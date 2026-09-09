"""Diagnostic timing of the audit's individual SQL stages on a bounded prefix."""
import importlib.util
import json
import time
import sys
from pathlib import Path
import duckdb

module_path=(Path(__file__).parents[1]/'reports/audit/attempts/audit-1.0.py') if '--baseline' in sys.argv else Path(__file__).with_name('audit_datasets.py')
spec=importlib.util.spec_from_file_location('audit',module_path)
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
source=Path(r'C:\Users\nimma\Downloads\Datasets\ND-UNSW-NB15-v3\NF-UNSW-NB15-v3.csv')
columns=audit.header_info(source,'utf-8')
con=duckdb.connect();con.execute("SET threads=2");con.execute("SET memory_limit='1GB'")
names='['+','.join(audit.lit(c['id']) for c in columns)+']'
con.execute(f"CREATE TABLE raw AS SELECT 0 AS source_file,row_number() OVER() AS parsed_row,* FROM read_csv({audit.lit(str(source))},all_varchar=true,names={names},header=true,parallel=false) LIMIT 100000")
timings=[]
class Timed:
    def execute(self,query):
        if '--materialize' in sys.argv and query.startswith('CREATE VIEW numeric_view'):
            query=query.replace('CREATE VIEW numeric_view','CREATE TABLE numeric_view',1)
        if '--count-if' in sys.argv:
            token='count(*) FILTER (WHERE '
            while token in query:
                start=query.index(token); end=start+len(token); level=1; stop=end
                while level:
                    if query[stop]=='(': level+=1
                    if query[stop]==')': level-=1
                    stop+=1
                query=query[:start]+'coalesce(count_if('+query[end:stop-1]+'),0)'+query[stop:]
        start=time.perf_counter();res=con.execute(query)
        row={'sql_prefix':query[:100],'elapsed_seconds':time.perf_counter()-start}
        timings.append(row);print(json.dumps(row),flush=True)
        return res
audit.profile(Timed(),columns)
Path('reports/audit/profile-benchmark'+('-materialized' if '--materialize' in sys.argv else '')+('-count-if' if '--count-if' in sys.argv else '')+'.json').write_text(json.dumps({'scope':'First 100000 NF-UNSW rows; speed diagnostic, not representative statistics','threads':2,'timings':timings},indent=2))
