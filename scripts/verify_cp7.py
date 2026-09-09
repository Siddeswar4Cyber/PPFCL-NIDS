"""Rebuild C1 allocations and independently check H1 memberships from source."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
import duckdb
import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq
from audit_datasets import lit,write_json,load_file,fetch_dict
from preprocess_p1 import sha
from run_baseline_pilot import ROOT,DATASETS,PROTOCOLS,bundle
from build_clients_c1 import SCENARIOS,META,choose,metadata,describe


def read(path): return json.loads(Path(path).read_text())


def verify_commit(report,script):
    assert report['script_sha256']==sha(ROOT/'scripts'/script)
    blob=subprocess.check_output(['git','show',report['git_commit']+':scripts/'+script],cwd=ROOT)
    assert hashlib.sha256(blob).hexdigest()==report['script_sha256']


def independent_owners(groups,labels,tag,probabilities):
    result=[]
    for group,label in zip(groups,labels):
        u=int(hashlib.sha256((tag+'|'+group).encode()).hexdigest()[:13],16)/16**13
        cumulative=0.0; selected=4
        for i,p in enumerate(probabilities.get(label,[.2]*5)):
            cumulative+=p
            if u<cumulative or i==4: selected=i; break
        result.append(selected)
    return np.asarray(result,dtype=np.int8)


def graph_components(nodes,edges):
    adjacency={node:set() for node in nodes}
    for a,b in edges: adjacency[a].add(b); adjacency[b].add(a)
    unseen=set(nodes); groups=[]
    while unseen:
        start=min(unseen); stack=[start]; visited=set()
        while stack:
            a=stack.pop()
            if a in visited: continue
            visited.add(a); stack.extend(adjacency[a]-visited)
        unseen-=visited; groups.append(sorted(visited))
    return groups


def main():
    checks=[]; hosts_checked=[]; bindings=[]
    with tempfile.TemporaryDirectory(prefix='ppfcl-cp7-verify-') as temp:
        con=duckdb.connect(str(Path(temp)/'verify.duckdb')); con.execute("SET memory_limit='4GB'"); con.execute('SET threads=4'); con.execute('SET preserve_insertion_order=true')
        try:
            for dataset in DATASETS:
                pre=read(ROOT/'reports/preprocessing'/('cic-ids-2017-P2.json' if dataset.startswith('cic') else dataset+'.json'))
                assert sha(pre['cleaned']['path'])==pre['cleaned']['sha256']
                con.execute(f"CREATE OR REPLACE VIEW cleaned AS SELECT * FROM read_parquet({lit(pre['cleaned']['path'])})")
                for protocol in PROTOCOLS:
                    _,pipe,_=bundle(dataset,protocol); parents={p:metadata(pipe['artifacts'][p]) for p in ['train','validation']}
                    tr=parents['train']; universe=sorted(set(read(ROOT/'reports/splits/contracts'/f'{dataset}.json')['raw_to_canonical_label'].values()))
                    for scenario,alpha in SCENARIOS.items():
                        path=ROOT/'reports/cp7/clients'/f'{dataset}-{protocol}-{scenario}.json'; r=read(path); verify_commit(r,'build_clients_c1.py')
                        assert r['parent_artifacts']==pipe['artifacts'] and r['transform_sha256']==pipe['transform_sha256'] and not r['validation_used_for_acceptance']
                        _,p,attempts=choose(tr['group_id'].to_numpy(),tr['label'].to_numpy(),tr['binary_label'].to_numpy(),r['scope_tag'],alpha)
                        assert attempts==r['attempts'] and p==r['probabilities']
                        if p is None:
                            assert r['status']=='INFEASIBLE'; checks.append({'run_id':r['run_id'],'status':'VERIFIED_INFEASIBLE'}); continue
                        assert r['status']=='COMPLETED' and sha(r['artifact']['path'])==r['artifact']['sha256']
                        table=pq.read_table(r['artifact']['path']); assert len(table)==sum(len(t) for t in parents.values()) and 'vector' not in table.column_names
                        expected_support=[]
                        for partition,parent in parents.items():
                            subset=table.filter(pc.equal(table['partition'],partition))
                            assert subset.select(META).equals(parent)
                            assert np.array_equal(subset['row_index'].to_numpy(),np.arange(len(parent)))
                            owners=independent_owners(parent['group_id'].to_numpy(),parent['label'].to_numpy(),r['scope_tag'],p)
                            assert np.array_equal(owners,subset['client_id'].to_numpy())
                            expected_support+=describe(parent,owners,universe,partition)
                        assert expected_support==r['support']
                        con.execute(f"CREATE OR REPLACE VIEW membership AS SELECT * FROM read_parquet({lit(r['artifact']['path'])})")
                        assert con.execute('SELECT count(*) FROM (SELECT group_id FROM membership GROUP BY group_id HAVING count(DISTINCT client_id)>1 OR count(DISTINCT partition)>1)').fetchone()[0]==0
                        bad=con.execute(f'''SELECT count(*) FROM membership m LEFT JOIN cleaned c USING(source_file,parsed_row)
                            WHERE c.group_id IS NULL OR NOT c.quality_eligible OR c.group_id<>m.group_id OR c.label<>m.label OR
                            (m.partition='train' AND (c.{protocol}_role<>'development_train' OR NOT c.representative)) OR
                            (m.partition='validation' AND c.{protocol}_role<>'validation')''').fetchone()[0]
                        assert bad==0
                        checks.append({'run_id':r['run_id'],'status':'PASSED','rows':len(table),'exact_parent_rows':True,'independent_hash_assignment':True,
                            'training_only_attempts_reproduced':True,'group_role_ownership':True,'source_commit_verified':True})
                        bindings.append({'path':str(path),'sha256':sha(path)})
                    print(f'C1 verification: {dataset}/{protocol}',flush=True)
            hpath=ROOT/'reports/cp7/host-feasibility.json'; h=read(hpath); assert h['status']=='COMPLETED'; verify_commit(h,'host_feasibility_h1.py')
            contract=read(ROOT/'reports/splits/contracts/ND-UNSW-NB15-v3.json'); source=contract['source_files'][0]
            assert sha(source['path'])==h['source_sha256'] and sha(h['cleaned']['path'])==h['cleaned']['sha256']
            info=load_file(con,Path(source['path']),source,contract['columns'],0,False); assert info['error_events']==0
            for hr in h['protocols']:
                protocol=hr['protocol']; con.execute('DROP TABLE IF EXISTS dev')
                con.execute(f'''CREATE TABLE dev AS SELECT *,bool_or(src IS NULL OR dst IS NULL) OVER(PARTITION BY group_id) AS group_missing
                    FROM (SELECT c.source_file,c.parsed_row,c.group_id,c.label,c.binary_label,c.{protocol}_role AS original_role,
                    nullif(trim(r.c002),'') AS src,nullif(trim(r.c004),'') AS dst FROM read_parquet({lit(h['cleaned']['path'])}) c
                    JOIN raw r USING(source_file,parsed_row) WHERE c.quality_eligible AND c.{protocol}_role IN ('development_train','validation'))''')
                edges=con.execute('SELECT DISTINCT src,dst FROM dev WHERE NOT group_missing').fetchall(); nodes={x for pair in edges for x in pair}
                groups=graph_components(nodes,edges); initial={host:g[0] for g in groups for host in g}
                con.execute('DROP TABLE IF EXISTS initial_map'); con.execute('CREATE TABLE initial_map(host VARCHAR,root VARCHAR)'); con.executemany('INSERT INTO initial_map VALUES (?,?)',list(initial.items()))
                bridges=con.execute('''SELECT list(DISTINCT i.root ORDER BY i.root) FROM dev d JOIN initial_map i ON d.src=i.host WHERE NOT group_missing
                    GROUP BY group_id HAVING count(DISTINCT i.root)>1''').fetchall()
                augmented_edges=edges+[(row[0][0],other) for row in bridges for other in row[0][1:]]
                groups=graph_components(nodes,augmented_edges); mapping=[]
                for group in groups:
                    digest=hashlib.sha256(('H1|17|component|'+'\n'.join(group)).encode()).hexdigest()
                    cs='train' if int(digest[:8],16)%1000<800 else 'validation'
                    for host in group:
                        hs='train' if int(hashlib.sha256(('H1|17|host|'+host).encode()).hexdigest()[:8],16)%1000<800 else 'validation'
                        mapping.append((host,digest,cs,hs))
                con.execute('DROP TABLE IF EXISTS host_map'); con.execute('CREATE TABLE host_map(host VARCHAR,component_id VARCHAR,cs VARCHAR,hs VARCHAR)'); con.executemany('INSERT INTO host_map VALUES (?,?,?,?)',mapping)
                actual=fetch_dict(con,'''SELECT m.component_id,count(*) AS rows,count(DISTINCT d.group_id) AS groups,count_if(d.binary_label=0) AS benign,count_if(d.binary_label=1) AS attack
                    FROM dev d JOIN host_map m ON d.src=m.host WHERE NOT group_missing GROUP BY m.component_id ORDER BY rows DESC,m.component_id''')
                for c in actual: c['endpoints']=sum(m[1]==c['component_id'] for m in mapping)
                assert actual==hr['components'] and len(nodes)==hr['endpoint_count'] and len(bridges)==hr['feature_groups_bridging_initial_components']
                for candidate in hr['candidates']:
                    assert sha(candidate['artifact']['path'])==candidate['artifact']['sha256']
                    con.execute(f"CREATE OR REPLACE VIEW candidate AS SELECT * FROM read_parquet({lit(candidate['artifact']['path'])})")
                    assert con.execute('SELECT count(*) FROM candidate').fetchone()[0]==con.execute('SELECT count(*) FROM dev').fetchone()[0]==hr['permitted_rows']
                    assert con.execute('SELECT count(DISTINCT (source_file,parsed_row)) FROM candidate').fetchone()[0]==hr['permitted_rows']
                    con.execute('DROP TABLE IF EXISTS expected_sides')
                    if candidate['method']=='components':
                        con.execute("CREATE TABLE expected_sides AS SELECT d.*,m.component_id,CASE WHEN group_missing THEN 'excluded_missing_endpoint' ELSE m.cs END AS expected_side FROM dev d LEFT JOIN host_map m ON d.src=m.host")
                    else:
                        con.execute('''CREATE TABLE expected_sides AS WITH side_rows AS
                            (SELECT d.*,s.component_id,CASE WHEN s.hs=t.hs THEN s.hs ELSE 'cross' END AS row_side FROM dev d
                            LEFT JOIN host_map s ON d.src=s.host LEFT JOIN host_map t ON d.dst=t.host),
                            group_sides AS (SELECT group_id,CASE WHEN bool_or(group_missing) THEN 'excluded_missing_endpoint'
                            WHEN min(row_side)=max(row_side) AND min(row_side)<>'cross' THEN min(row_side) ELSE 'excluded_cross_or_mixed_group' END AS expected_side
                            FROM side_rows GROUP BY group_id) SELECT r.*,g.expected_side FROM side_rows r JOIN group_sides g USING(group_id)''')
                    bad=con.execute('''SELECT count(*) FROM candidate c FULL JOIN expected_sides e USING(source_file,parsed_row)
                        WHERE c.group_id IS DISTINCT FROM e.group_id OR c.label IS DISTINCT FROM e.label OR c.binary_label IS DISTINCT FROM e.binary_label
                        OR c.original_role IS DISTINCT FROM e.original_role OR c.component_id IS DISTINCT FROM e.component_id OR c.candidate_side IS DISTINCT FROM e.expected_side
                        OR c.partition IS DISTINCT FROM CASE WHEN e.expected_side LIKE 'excluded_%' THEN e.expected_side
                        WHEN (e.original_role='development_train' AND e.expected_side='train') OR (e.original_role='validation' AND e.expected_side='validation') THEN e.expected_side ELSE 'excluded_role_side_mismatch' END''').fetchone()[0]
                    assert bad==0
                    actual_support=fetch_dict(con,'SELECT partition,count(*) AS rows,count(DISTINCT group_id) AS groups,count_if(binary_label=0) AS benign,count_if(binary_label=1) AS attack FROM candidate GROUP BY partition ORDER BY partition')
                    assert actual_support==candidate['support']
                    qualifying=all(any(s['partition']==p and s['rows']>=1000 and s['benign']>=20 and s['attack']>=20 for s in actual_support) for p in ['train','validation'])
                    assert qualifying==(candidate['status']=='FEASIBLE_DEVELOPMENT_SUBSET')
                    shared=con.execute('''SELECT count(*) FROM (SELECT host FROM
                        (SELECT e.src AS host,c.partition FROM candidate c JOIN dev e USING(source_file,parsed_row) WHERE c.partition IN ('train','validation')
                        UNION ALL SELECT e.dst,c.partition FROM candidate c JOIN dev e USING(source_file,parsed_row) WHERE c.partition IN ('train','validation'))
                        GROUP BY host HAVING count(DISTINCT partition)>1)''').fetchone()[0]
                    assert shared==0 and con.execute("SELECT count(*) FROM (SELECT group_id FROM candidate WHERE partition IN ('train','validation') GROUP BY group_id HAVING count(DISTINCT partition)>1)").fetchone()[0]==0
                    hosts_checked.append({'protocol':protocol,'method':candidate['method'],'status':'PASSED','source_reconstruction':True,'endpoint_and_group_separation':True,'support_decision_verified':True})
                print(f'H1 verification: {protocol}',flush=True)
            bindings.append({'path':str(hpath),'sha256':sha(hpath)})
        finally: con.close()
    write_json(ROOT/'reports/cp7/verification.json',{'status':'PASSED','client_checks':checks,'host_checks':hosts_checked,'report_bindings':bindings,
        'source_and_parent_hashes_verified':True,'final_test_model_scores_exposed':False,'verification_script_sha256':sha(__file__)})
    print('CP7 verification PASSED',flush=True)


if __name__=='__main__': main()
