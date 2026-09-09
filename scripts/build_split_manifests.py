"""S1: source-bound memberships; no fitted transform or model. See CP3 protocol."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import tempfile
import time
from pathlib import Path
import duckdb
from audit_datasets import fingerprint, header_info, load_file, lit, fetch_dict, write_json

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'S1'
ROLES = ['public_reference', 'development_train', 'private_train', 'validation', 'sealed_test']


def numeric_projection(column):
    v = f'try_cast(trim({column}) AS DOUBLE)'
    return f'CASE WHEN isfinite({v}) THEN CASE WHEN {v}=0 THEN 0.0 ELSE {v} END END'


def contract(audit):
    columns = header_info(Path(audit['files'][0]['path']), audit['files'][0]['encoding'])
    cic = audit['dataset'] == 'cic-ids-2017'
    features = [c for c in columns if c['role'] == 'candidate_feature' and not (cic and c['id'] == 'c055')]
    labels = sorted({r['c078' if cic else 'c054'] for r in audit['label_counts']})
    mapping = {label: re.sub('[^a-z0-9]+', '_', label.lower()).strip('_') for label in labels}
    assert len(set(mapping.values())) == len(mapping)
    return {'version': VERSION, 'dataset': audit['dataset'], 'columns': columns,
            'predictors': features, 'raw_to_canonical_label': mapping,
            'canonicalization': 'Lowercase ASCII alphanumeric tokens joined by underscore; exact raw-key lookup, no fuzzy matching. Labels remain dataset-scoped.',
            'group_projection': 'Ordered DOUBLE predictors; trim strings; nonfinite/uncastable/blank -> NULL; signed zero -> 0. Negative finite values retained.',
            'projection_limit': 'No imputation or scaling fitted. CP4 must recheck collisions after any additional transformation.',
            'source_files': audit['files']}


def relations(con, cic, cuts=None):
    """Input n: source_file, parsed_row, x DOUBLE[], label, binary_label, start_ms, end_ms, friday."""
    con.execute('''CREATE TABLE groups AS SELECT x, count(*) AS n, count(DISTINCT label) AS labels,
        count(DISTINCT binary_label) AS binary_labels, min(start_ms) AS start_min, max(end_ms) AS end_max,
        bool_or(friday) AS friday, min(struct_pack(f:=source_file,r:=parsed_row)) AS representative
        FROM n GROUP BY x''')
    # Group equality is verified on actual vectors. Hash is an identifier only after collision check.
    con.execute("ALTER TABLE groups ADD COLUMN group_id VARCHAR")
    con.execute("UPDATE groups SET group_id=sha256('S1|17|' || to_json(x))")
    assert con.execute('SELECT count(*)=count(DISTINCT group_id) FROM groups').fetchone()[0], 'SHA-256 collision'
    con.execute("ALTER TABLE groups ADD COLUMN bucket INTEGER")
    con.execute("UPDATE groups SET bucket=('0x' || substr(group_id,1,8))::UBIGINT % 1000")
    con.execute('''CREATE TABLE g AS SELECT *, CASE WHEN labels>1 THEN 'quarantine_conflict'
        WHEN bucket<100 THEN 'public_reference' WHEN bucket<500 THEN 'development_train'
        WHEN bucket<600 THEN 'private_train' WHEN bucket<800 THEN 'validation'
        ELSE 'sealed_test' END AS role FROM groups''')
    if cic:
        task = 'NULL::INTEGER'
        stress = "CASE WHEN g.role='quarantine_conflict' THEN g.role WHEN g.friday AND g.role='sealed_test' THEN 'sealed_test' WHEN NOT g.friday AND g.role<>'sealed_test' THEN g.role ELSE 'excluded_stress' END"
        task_role = "'not_defined'"
    else:
        c60, c80 = cuts
        # Epoch threshold separates the two observed capture periods, not arbitrary three calendar days.
        period = 16484 * 86400000
        task = f'CASE WHEN g.end_max<{period} THEN 1 WHEN g.start_min>={period} THEN 2 ELSE NULL END'
        task_role = f"CASE WHEN g.role='quarantine_conflict' THEN g.role WHEN ({task}) IS NULL THEN 'excluded_task_boundary' ELSE g.role END"
        stress = f"""CASE WHEN g.role='quarantine_conflict' THEN g.role
            WHEN g.end_max<{c60} AND g.role IN ('public_reference','development_train','private_train') THEN g.role
            WHEN g.start_min>={c60} AND g.end_max<{c80} AND g.role='validation' THEN g.role
            WHEN g.start_min>={c80} AND g.role='sealed_test' THEN g.role ELSE 'excluded_stress' END"""
    con.execute(f'''CREATE TABLE membership AS SELECT n.source_file,n.parsed_row,g.group_id,n.label,n.binary_label,
        g.role AS primary_role, {stress} AS stress_role, {task} AS task_id, {task_role} AS task_role,
        n.source_file=g.representative.f AND n.parsed_row=g.representative.r AS representative,
        g.n AS group_rows, g.labels AS group_labels, g.binary_labels AS group_binary_labels,
        n.start_ms,n.end_ms FROM n JOIN g ON n.x IS NOT DISTINCT FROM g.x''')


def summarize(con):
    rows = con.execute('SELECT count(*) FROM membership').fetchone()[0]
    assert rows == con.execute('SELECT count(*) FROM n').fetchone()[0]
    assert rows == con.execute('SELECT count(DISTINCT (source_file,parsed_row)) FROM membership').fetchone()[0]
    bad = con.execute('''SELECT count(*) FROM (SELECT group_id FROM membership GROUP BY group_id
        HAVING count(DISTINCT primary_role)>1 OR count(DISTINCT stress_role)>1 OR count(DISTINCT task_role)>1
        OR sum(representative::INT)<>1)''').fetchone()[0]
    assert bad == 0, 'Group overlap or representative failure'
    assert con.execute("SELECT count(*) FROM membership WHERE primary_role='sealed_test' AND (stress_role IN ('public_reference','development_train','private_train','validation') OR task_role IN ('public_reference','development_train','private_train','validation'))").fetchone()[0] == 0
    support = {}
    for role in ['primary_role','stress_role','task_role']:
        support[role] = fetch_dict(con, f'''SELECT {role} AS role, {"task_id," if role=='task_role' else ''} label,binary_label,
            count(*) AS rows,count(DISTINCT group_id) AS groups,sum(representative::INT) AS representatives
            FROM membership GROUP BY ALL ORDER BY ALL''')
    quarantine = fetch_dict(con, '''SELECT label,binary_label,count(*) AS rows,count(DISTINCT group_id) AS groups,
        count(*) FILTER (WHERE group_binary_labels>1) AS binary_conflict_rows
        FROM membership WHERE primary_role='quarantine_conflict' GROUP BY ALL ORDER BY label''')
    return {'rows':rows, 'groups':con.execute('SELECT count(*) FROM g').fetchone()[0],
            'support':support, 'quarantine_by_label':quarantine,
            'assertions':{'row_coverage':True,'unique_row_ids':True,'no_group_role_overlap':True,
                          'one_representative_per_group':True,'hash_collision_check':True,'global_sealed_role_preserved':True}}


def run_family(audit, output):
    name = audit['dataset']; cic = name == 'cic-ids-2017'; began = time.perf_counter()
    destination = output / name
    if destination.exists():
        raise RuntimeError(f'Refusing to overwrite immutable output: {destination}')
    c = contract(audit)
    for f in c['source_files']:
        print(f'{name}: verify {Path(f["path"]).name}', flush=True)
        assert fingerprint(Path(f['path']))['sha256'] == f['sha256'], 'Source changed since audit'
    destination.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='ppfcl-splits-') as temp:
        con = duckdb.connect(str(Path(temp)/'work.duckdb'))
        try:
            con.execute("SET memory_limit='4GB'"); con.execute('SET threads=8')
            con.execute('SET preserve_insertion_order=true')
            for i,f in enumerate(c['source_files']):
                print(f'{name}: stage {Path(f["path"]).name}', flush=True)
                parsing = load_file(con, Path(f['path']), f, c['columns'], f['source_file'], i>0)
                assert parsing['error_events']==0
            assert con.execute('SELECT count(*) FROM raw').fetchone()[0] == audit['rows']
            cases = 'CASE ' + ('c078' if cic else 'c054') + ' ' + ' '.join(f'WHEN {lit(k)} THEN {lit(v)}' for k,v in c['raw_to_canonical_label'].items()) + ' END'
            values = []
            for f in c['predictors']:
                values.append(numeric_projection(f['id']))
            names = {f['name']:f['id'] for f in c['columns']}
            start = 'NULL::DOUBLE' if cic else f"try_cast({names['FLOW_START_MILLISECONDS']} AS DOUBLE)"
            end = 'NULL::DOUBLE' if cic else f"try_cast({names['FLOW_END_MILLISECONDS']} AS DOUBLE)"
            friday_files=[str(f['source_file']) for f in c['source_files'] if Path(f['path']).name.startswith('Friday_')]
            friday = f"source_file IN ({','.join(friday_files)})" if cic else 'false'
            print(f'{name}: normalize for grouping', flush=True)
            con.execute(f'''CREATE TABLE n AS SELECT source_file,parsed_row,[{','.join(values)}] AS x,
                {cases} AS label, CASE WHEN {('c078' if cic else 'c054')} IN ('BENIGN','Benign') THEN 0 ELSE 1 END AS binary_label,
                {start} AS start_ms,{end} AS end_ms,{friday} AS friday FROM raw''')
            assert con.execute('SELECT count(*) FROM n WHERE label IS NULL').fetchone()[0]==0
            if not cic:
                assert con.execute('SELECT count(*) FROM raw JOIN n USING(source_file,parsed_row) WHERE try_cast(c053 AS INT) IS DISTINCT FROM binary_label').fetchone()[0]==0
                assert con.execute('SELECT count(*) FROM n WHERE start_ms IS NULL OR end_ms IS NULL OR NOT isfinite(start_ms) OR NOT isfinite(end_ms) OR start_ms<=0 OR end_ms<start_ms').fetchone()[0]==0
            cuts = None if cic else list(con.execute('SELECT quantile_disc(start_ms, [0.6,0.8]) FROM n').fetchone()[0])
            con.execute('DROP TABLE raw')
            print(f'{name}: exact normalized groups and memberships', flush=True)
            relations(con,cic,cuts)
            result=summarize(con)
            target=destination/'memberships.parquet'
            con.execute(f"COPY (SELECT * FROM membership ORDER BY source_file,parsed_row) TO {lit(str(target))} (FORMAT PARQUET, COMPRESSION ZSTD)")
            assert con.execute(f'SELECT count(*) FROM read_parquet({lit(str(target))})').fetchone()[0]==audit['rows']
            c['stress_cutoffs_ms']=cuts
            write_json(destination/'contract.json',c)
            result.update(dataset=name,version=VERSION,status='COMPLETED',elapsed_seconds=time.perf_counter()-began,
                manifest_path=str(target.resolve()),manifest_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                contract_sha256=hashlib.sha256((destination/'contract.json').read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),stress_cutoffs_ms=cuts)
            write_json(ROOT/'reports/splits'/f'{name}.json',result)
            print(f'{name}: COMPLETED {result["rows"]:,} rows, {result["groups"]:,} groups',flush=True)
        finally:
            con.close()


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--family',action='append'); args=parser.parse_args()
    for name in args.family or ['cic-ids-2017','ND-UNSW-NB15-v3']:
        a=json.loads((ROOT/'reports/audit'/f'{name}.json').read_text())
        assert a['status']=='COMPLETED'
        run_family(a,ROOT/'data/splits'/VERSION)


if __name__=='__main__':
    main()
