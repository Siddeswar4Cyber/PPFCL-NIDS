import sys
import unittest
from pathlib import Path
import duckdb
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_split_manifests import relations, summarize, numeric_projection


class SplitTests(unittest.TestCase):
    def connection(self):
        con=duckdb.connect()
        self.addCleanup(con.close)
        con.execute('CREATE TABLE n(source_file INT,parsed_row BIGINT,x DOUBLE[],label VARCHAR,binary_label INT,start_ms DOUBLE,end_ms DOUBLE,friday BOOLEAN)')
        return con

    def test_normalized_missing_and_signed_zero_equivalence(self):
        con=self.connection()
        values=con.execute("SELECT "+numeric_projection('v')+" FROM (VALUES ('1'),('1.0'),('1e0'),('-0'),('0'),('Infinity'),('NaN'),(''),('text')) t(v)").fetchall()
        self.assertEqual(values,[(1.0,)]*3+[(0.0,)]*2+[(None,)]*4)

    def test_conflicts_are_quarantined_and_cross_file_groups_stay_together(self):
        con=self.connection()
        con.executemany('INSERT INTO n VALUES (?,?,?,?,?,?,?,?)',[
            (0,1,[1,None],'benign',0,None,None,False),(1,1,[1,None],'attack',1,None,None,True),
            (0,2,[2],'attack_a',1,None,None,False),(0,3,[2],'attack_b',1,None,None,False),
            (0,4,[3],'benign',0,None,None,False),(1,2,[3],'benign',0,None,None,True)])
        relations(con,True); result=summarize(con)
        self.assertEqual(result['rows'],6); self.assertEqual(result['groups'],3)
        self.assertEqual(con.execute("SELECT count(*) FROM membership WHERE primary_role='quarantine_conflict'").fetchone()[0],4)
        self.assertEqual(con.execute("SELECT count(*) FROM membership WHERE group_id IN (SELECT group_id FROM g WHERE friday) AND stress_role IN ('development_train','private_train','public_reference','validation')").fetchone()[0],0)

    def test_time_boundary_exclusion_seal_and_determinism(self):
        def build(reverse):
            con=self.connection(); period=16484*86400000
            rows=[(0,i,[i],'benign' if i%2 else 'attack',i%2,period-100+i,period-99+i,False) for i in range(1,1001)]
            rows += [(1,1,[1],'benign',1,period+100,period+101,False)]
            con.executemany('INSERT INTO n VALUES (?,?,?,?,?,?,?,?)',list(reversed(rows)) if reverse else rows)
            relations(con,False,[period+300,period+600]); summarize(con)
            self.assertEqual(con.execute('SELECT DISTINCT task_role FROM membership WHERE group_id=(SELECT group_id FROM membership WHERE source_file=1)').fetchone()[0],'excluded_task_boundary')
            bad=con.execute(f"SELECT count(*) FROM membership WHERE (stress_role IN ('development_train','private_train','public_reference') AND end_ms>={period+300}) OR (stress_role='validation' AND (start_ms<{period+300} OR end_ms>={period+600})) OR (stress_role='sealed_test' AND start_ms<{period+600})").fetchone()[0]
            self.assertEqual(bad,0)
            return con.execute('SELECT source_file,parsed_row,group_id,primary_role,stress_role,task_role,representative FROM membership ORDER BY source_file,parsed_row').fetchall()
        self.assertEqual(build(False),build(True))


if __name__=='__main__':
    unittest.main()
