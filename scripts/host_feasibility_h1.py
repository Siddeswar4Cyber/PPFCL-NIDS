"""H1 endpoint/group components and fixed development-subset feasibility."""
import hashlib
import ipaddress
import json
import subprocess
import tempfile
import time
from pathlib import Path
import duckdb
from audit_datasets import lit,write_json,load_file,fetch_dict
from preprocess_p1 import sha
from run_baseline_pilot import ROOT,PROTOCOLS


class UnionFind:
    def __init__(self,items): self.parent={x:x for x in items}
    def find(self,x):
        while self.parent[x]!=x:
            self.parent[x]=self.parent[self.parent[x]]; x=self.parent[x]
        return x
    def union(self,a,b):
        a,b=self.find(a),self.find(b)
        if a!=b: self.parent[max(a,b)]=min(a,b)


def side(prefix,value):
    return 'train' if int(hashlib.sha256((prefix+value).encode()).hexdigest()[:8],16)%1000<800 else 'validation'


def component_map(addresses,edges,group_links=()):
    uf=UnionFind(addresses)
    for a,b in edges: uf.union(a,b)
    for group in group_links:
        for other in group[1:]: uf.union(group[0],other)
    members={}
    for address in sorted(addresses): members.setdefault(uf.find(address),[]).append(address)
    result={}
    for hosts in members.values():
        payload='\n'.join(hosts); digest=hashlib.sha256(('H1|17|component|'+payload).encode()).hexdigest()
        for host in hosts: result[host]=(digest,side('H1|17|component|',payload))
    return result


def support_acceptance(support,shared_hosts,shared_groups,role_violations):
    reasons=[]
    for partition in ['train','validation']:
        s=next((s for s in support if s['partition']==partition),{'rows':0,'benign':0,'attack':0})
        if s['rows']<1000: reasons.append(f'{partition}: fewer than 1000 rows')
        if s['benign']<20: reasons.append(f'{partition}: fewer than 20 benign rows')
        if s['attack']<20: reasons.append(f'{partition}: fewer than 20 attack rows')
    if shared_hosts: reasons.append('Endpoint overlap')
    if shared_groups: reasons.append('S1 group overlap')
    if role_violations: reasons.append('Original role violation')
    return reasons


def candidate(con,protocol,method,mapping):
    con.execute('DROP TABLE IF EXISTS candidate')
    if method=='components':
        expr="CASE WHEN d.group_missing THEN 'excluded_missing_endpoint' ELSE m.component_side END"
        joins='LEFT JOIN host_map m ON d.src=m.host'
    else:
        con.execute('DROP TABLE IF EXISTS group_sides')
        con.execute('''CREATE TABLE group_sides AS SELECT group_id,
            CASE WHEN bool_or(group_missing) THEN 'excluded_missing_endpoint'
            WHEN count(DISTINCT row_side)=1 AND min(row_side)<>'cross' THEN min(row_side)
            ELSE 'excluded_cross_or_mixed_group' END AS group_side
            FROM (SELECT d.*,CASE WHEN s.endpoint_side=t.endpoint_side THEN s.endpoint_side ELSE 'cross' END AS row_side
            FROM dev d LEFT JOIN host_map s ON s.host=d.src LEFT JOIN host_map t ON t.host=d.dst) GROUP BY group_id''')
        expr='g.group_side'; joins='JOIN group_sides g USING(group_id) LEFT JOIN host_map m ON d.src=m.host'
    con.execute(f'''CREATE TABLE candidate AS SELECT *,CASE WHEN candidate_side LIKE 'excluded_%' THEN candidate_side
        WHEN (original_role='development_train' AND candidate_side='train') OR (original_role='validation' AND candidate_side='validation') THEN candidate_side
        ELSE 'excluded_role_side_mismatch' END AS partition
        FROM (SELECT d.source_file,d.parsed_row,d.group_id,d.label,d.binary_label,d.original_role,m.component_id,{expr} AS candidate_side FROM dev d {joins})''')
    support=fetch_dict(con,"SELECT partition,count(*) AS rows,count(DISTINCT group_id) AS groups,count_if(binary_label=0) AS benign,count_if(binary_label=1) AS attack FROM candidate GROUP BY partition ORDER BY partition")
    bylabel=fetch_dict(con,'SELECT partition,label,count(*) AS rows,count(DISTINCT group_id) AS groups FROM candidate GROUP BY ALL ORDER BY ALL')
    shared_hosts=con.execute('''SELECT count(*) FROM (SELECT host FROM
        (SELECT d.src AS host,c.partition FROM dev d JOIN candidate c USING(source_file,parsed_row) WHERE c.partition IN ('train','validation')
        UNION SELECT d.dst,c.partition FROM dev d JOIN candidate c USING(source_file,parsed_row) WHERE c.partition IN ('train','validation'))
        GROUP BY host HAVING count(DISTINCT partition)>1)''').fetchone()[0]
    shared_groups=con.execute("SELECT count(*) FROM (SELECT group_id FROM candidate WHERE partition IN ('train','validation') GROUP BY group_id HAVING count(DISTINCT partition)>1)").fetchone()[0]
    bad=con.execute("SELECT count(*) FROM candidate WHERE (partition='train' AND original_role<>'development_train') OR (partition='validation' AND original_role<>'validation')").fetchone()[0]
    reasons=support_acceptance(support,shared_hosts,shared_groups,bad)
    path=ROOT/'data/host-feasibility/H1/ND-UNSW-NB15-v3'/protocol/(method+'.parquet'); path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): raise RuntimeError(f'Refusing overwrite {path}')
    con.execute(f'COPY (SELECT * FROM candidate ORDER BY source_file,parsed_row) TO {lit(str(path))} (FORMAT PARQUET, COMPRESSION ZSTD)')
    return {'method':method,'status':'FEASIBLE_DEVELOPMENT_SUBSET' if not reasons else 'INFEASIBLE_UNDER_FIXED_RULE','reasons':reasons,
        'support':support,'canonical_support':bylabel,'shared_endpoints':shared_hosts,'shared_groups':shared_groups,'original_role_violations':bad,
        'artifact':{'path':str(path),'sha256':sha(path),'rows':sum(s['rows'] for s in support)},'model_scored':False}


def main():
    began=time.perf_counter(); dataset='ND-UNSW-NB15-v3'; output=ROOT/'reports/cp7/host-feasibility.json'
    if output.exists(): raise RuntimeError('H1 report already exists')
    contract=json.loads((ROOT/'reports/splits/contracts'/f'{dataset}.json').read_text()); source=contract['source_files'][0]
    pre=json.loads((ROOT/'reports/preprocessing'/f'{dataset}.json').read_text()); cleaned=pre['cleaned']
    assert sha(source['path'])==source['sha256'] and sha(cleaned['path'])==cleaned['sha256']
    report={'version':'H1','run_id':'H1-NF-host-feasibility','experiment_id':'EXP-003','status':'RUNNING','source_sha256':source['sha256'],
        'cleaned':cleaned,'script_sha256':sha(__file__),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'CIC_host_status':'UNAVAILABLE: supplied CSV has no endpoint metadata','protocols':[],
        'final_private_public_external_population_used':False,'model_scored':False,'memory_limit':'4GB','threads':4}
    write_json(output,report)
    try:
        with tempfile.TemporaryDirectory(prefix='ppfcl-h1-') as temp:
            con=duckdb.connect(str(Path(temp)/'work.duckdb'))
            try:
                con.execute("SET memory_limit='4GB'"); con.execute('SET threads=4'); con.execute('SET preserve_insertion_order=true')
                parse=load_file(con,Path(source['path']),source,contract['columns'],0,False); assert parse['error_events']==0
                for protocol in PROTOCOLS:
                    print(f'H1/{protocol}: development graph',flush=True)
                    con.execute('DROP TABLE IF EXISTS dev')
                    con.execute(f'''CREATE TABLE dev AS SELECT *,bool_or(src IS NULL OR dst IS NULL) OVER(PARTITION BY group_id) AS group_missing
                        FROM (SELECT c.source_file,c.parsed_row,c.group_id,c.label,c.binary_label,c.{protocol}_role AS original_role,
                        nullif(trim(r.c002),'') AS src,nullif(trim(r.c004),'') AS dst,try_cast(r.c053 AS INTEGER) AS original_label
                        FROM read_parquet({lit(cleaned['path'])}) c JOIN raw r USING(source_file,parsed_row)
                        WHERE c.quality_eligible AND c.{protocol}_role IN ('development_train','validation'))''')
                    expected=con.execute(f"SELECT count(*) FROM read_parquet({lit(cleaned['path'])}) WHERE quality_eligible AND {protocol}_role IN ('development_train','validation')").fetchone()[0]
                    assert con.execute('SELECT count(*) FROM dev').fetchone()[0]==expected
                    assert con.execute('SELECT count(*) FROM dev WHERE binary_label IS DISTINCT FROM original_label').fetchone()[0]==0
                    edges=con.execute('SELECT DISTINCT src,dst FROM dev WHERE NOT group_missing ORDER BY src,dst').fetchall()
                    addresses=sorted({a for pair in edges for a in pair})
                    for address in addresses: assert str(ipaddress.ip_address(address))==address,'Noncanonical endpoint requires review'
                    initial=component_map(addresses,edges)
                    # Use one address as representative for each initial component, so feature-group bridges can be unioned.
                    representatives={}
                    for address,(component,_) in initial.items(): representatives.setdefault(component,address)
                    con.execute('DROP TABLE IF EXISTS initial_map'); con.execute('CREATE TABLE initial_map(host VARCHAR,component_host VARCHAR)')
                    con.executemany('INSERT INTO initial_map VALUES (?,?)',[(h,representatives[c[0]]) for h,c in initial.items()])
                    links=[row[0] for row in con.execute('''SELECT list(DISTINCT m.component_host ORDER BY m.component_host) FROM dev d JOIN initial_map m ON d.src=m.host
                        WHERE NOT group_missing GROUP BY group_id HAVING count(DISTINCT m.component_host)>1''').fetchall()]
                    mapping=component_map(addresses,edges,links)
                    con.execute('DROP TABLE IF EXISTS host_map'); con.execute('CREATE TABLE host_map(host VARCHAR,component_id VARCHAR,component_side VARCHAR,endpoint_side VARCHAR)')
                    con.executemany('INSERT INTO host_map VALUES (?,?,?,?)',[(host,*mapping[host],side('H1|17|host|',host)) for host in addresses])
                    components=fetch_dict(con,'''SELECT m.component_id,count(*) AS rows,count(DISTINCT d.group_id) AS groups,
                        count_if(d.binary_label=0) AS benign,count_if(d.binary_label=1) AS attack
                        FROM dev d JOIN host_map m ON d.src=m.host WHERE NOT d.group_missing GROUP BY m.component_id ORDER BY rows DESC,m.component_id''')
                    for c in components: c['endpoints']=sum(v[0]==c['component_id'] for v in mapping.values())
                    current={'protocol':protocol,'permitted_rows':expected,'permitted_support':fetch_dict(con,'SELECT original_role,label,count(*) AS rows,count(DISTINCT group_id) AS groups FROM dev GROUP BY ALL ORDER BY ALL'),
                        'missing_endpoint_group_rows':con.execute('SELECT count(*) FROM dev WHERE group_missing').fetchone()[0],
                        'endpoint_count':len(addresses),'initial_endpoint_components':len(set(v[0] for v in initial.values())),
                        'feature_groups_bridging_initial_components':len(links),'components':components,
                        'attack_containing_components':sum(c['attack']>0 for c in components),
                        'no_discard_two_sided_attack_support_possible':sum(c['attack']>0 for c in components)>=2,
                        'address_flags':{'unspecified':sum(ipaddress.ip_address(a).is_unspecified for a in addresses),'multicast':sum(ipaddress.ip_address(a).is_multicast for a in addresses)},
                        'candidates':[candidate(con,protocol,method,mapping) for method in ['components','endpoint_filter']]}
                    report['protocols'].append(current); write_json(output,report)
                    print(f'H1/{protocol}: {len(components)} components; '+', '.join(c['method']+'='+c['status'] for c in current['candidates']),flush=True)
            finally: con.close()
        report['status']='COMPLETED'
    except Exception as exc:
        report.update(status='FAILED',error=repr(exc)); raise
    finally:
        report['elapsed_seconds']=time.perf_counter()-began; write_json(output,report)


if __name__=='__main__': main()
