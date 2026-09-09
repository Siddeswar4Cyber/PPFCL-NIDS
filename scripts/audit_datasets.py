"""Read-only source audit. Disk-backed staging; no data cleaning or model fitting."""
from __future__ import annotations

import argparse
import codecs
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import psutil

VERSION = "audit-1.3"
LABELS = {"Label", "Attack"}
METADATA = {"FLOW_START_MILLISECONDS", "FLOW_END_MILLISECONDS", "IPV4_SRC_ADDR", "IPV4_DST_ADDR", "Flow ID", "Source IP", "Destination IP", "Timestamp"}


def lit(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def fingerprint(path: Path) -> dict:
    """Full byte hash and UTF-8 validation; Latin-1 is lossless fallback, not a repair."""
    before = path.stat()
    sha = hashlib.sha256()
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    utf8 = True
    physical_lf = 0
    last = b""
    with path.open("rb") as handle:
        while block := handle.read(8 * 1024 * 1024):
            sha.update(block)
            physical_lf += block.count(b"\n")
            last = block[-1:]
            if utf8:
                try:
                    decoder.decode(block)
                except UnicodeDecodeError:
                    utf8 = False
    if utf8:
        try:
            decoder.decode(b"", final=True)
        except UnicodeDecodeError:
            utf8 = False
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError(f"Source changed while hashing: {path}")
    return {"path": str(path.resolve()), "bytes": before.st_size, "mtime_ns": before.st_mtime_ns,
            "sha256": sha.hexdigest(), "encoding": "utf-8" if utf8 else "latin-1",
            "physical_lines": physical_lf + int(bool(last) and last != b"\n")}


def header_info(path: Path, encoding: str) -> list[dict]:
    with path.open(encoding="utf-8-sig" if encoding == "utf-8" else encoding, newline="") as handle:
        names = next(csv.reader(handle, strict=True))
    return [{"position": i, "id": f"c{i:03d}", "raw_name": name, "name": name.strip(),
             "role": "label" if name.strip() in LABELS else "metadata" if name.strip() in METADATA else "candidate_feature"}
            for i, name in enumerate(names)]


def fetch_dict(con, query: str) -> list[dict]:
    cur = con.execute(query)
    names = [x[0] for x in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def load_file(con, path: Path, info: dict, columns: list[dict], file_id: int, append: bool) -> dict:
    colspec = "{" + ",".join(f"{lit(c['id'])}:'VARCHAR'" for c in columns) + "}"
    # Preserve blanks as strings. All columns forced to VARCHAR so cast issues are audited, not skipped.
    options = (f"columns={colspec}, header=true, auto_detect=false, delim=',', quote='\"', escape='\"', "
               f"force_not_null=[{','.join(lit(c['id']) for c in columns)}], strict_mode=true, store_rejects=true, rejects_limit=0, "
               f"rejects_table='rejects_{file_id}', rejects_scan='scans_{file_id}', "
               f"encoding={lit(info['encoding'])}, parallel=false")
    query = f"SELECT {file_id}::INTEGER AS source_file, row_number() OVER ()::BIGINT AS parsed_row, * FROM read_csv({lit(str(path))}, {options})"
    con.execute(("INSERT INTO raw " if append else "CREATE TABLE raw AS ") + query)
    rejected = con.execute(f"SELECT count(*), count(DISTINCT line) FROM rejects_{file_id}").fetchone()
    kinds = fetch_dict(con, f"SELECT error_type, count(*) AS errors FROM rejects_{file_id} GROUP BY error_type")
    # Diagnostics exclude full traffic records. Exact line locations retained for later investigation.
    locations = fetch_dict(con, f"SELECT line, column_idx, error_type FROM rejects_{file_id} ORDER BY line LIMIT 100")
    return {"error_events": rejected[0], "rejected_physical_line_locations": rejected[1], "error_types": kinds, "first_100_locations": locations}


def profile(con, columns: list[dict]) -> tuple[list[dict], list[dict]]:
    expressions = []
    converted = []
    for col in columns:
        c = col["id"]
        converted += [f"trim({c}) AS {c}", f"try_cast(trim({c}) AS DOUBLE) AS n_{c}"]
    con.execute("CREATE VIEW numeric_view AS SELECT source_file, parsed_row, " + ",".join(converted) + " FROM raw")
    # Single scan across all columns; approximate cardinality is labeled, never called exact.
    for col in columns:
        c, n = col["id"], "n_" + col["id"]
        e = {
            "blank": f"coalesce(count_if({c} IS NULL OR {c}=''),0)",
            "nan": f"coalesce(count_if(isnan({n})),0)",
            "positive_infinity": f"coalesce(count_if({n}='Infinity'::DOUBLE),0)",
            "negative_infinity": f"coalesce(count_if({n}='-Infinity'::DOUBLE),0)",
            "non_numeric_nonblank": f"coalesce(count_if({n} IS NULL AND {c} IS NOT NULL AND {c}<>''),0)",
            "finite": f"coalesce(count_if(isfinite({n})),0)",
            "negative_finite": f"coalesce(count_if(isfinite({n}) AND {n}<0),0)",
            "non_integral_finite": f"coalesce(count_if(isfinite({n}) AND {n}<>trunc({n})),0)",
            "min_finite": f"min({n}) FILTER (WHERE isfinite({n}))",
            "max_finite": f"max({n}) FILTER (WHERE isfinite({n}))",
            "approx_distinct_strings": f"approx_count_distinct({c})",
            "lexical_min": f"min({c})", "lexical_max": f"max({c})",
        }
        expressions += [f"{v} AS {c}_{k}" for k, v in e.items()]
    rows = fetch_dict(con, "SELECT source_file,count(*) AS rows," + ",".join(expressions) + " FROM numeric_view GROUP BY source_file ORDER BY source_file")
    outputs = []
    for row in rows:
        fields = []
        for col in columns:
            c = col["id"]
            values = {k[len(c)+1:]: v for k, v in row.items() if k.startswith(c + "_")}
            values["constant_string"] = values["lexical_min"] == values["lexical_max"] and row["rows"] > 0
            values["inferred_type"] = ("numeric_integer_valued" if values["non_integral_finite"] == 0 else "numeric_real") if values["finite"] and values["non_numeric_nonblank"] == 0 else "string_or_mixed"
            fields.append({**col, **values})
        outputs.append({"source_file": row["source_file"], "rows": row["rows"], "columns": fields})
    # Top candidates estimated from entire population; their frequencies then counted exactly.
    candidates = con.execute("SELECT " + ",".join(f"approx_top_k({c['id']},1)[1]" for c in columns) + " FROM numeric_view").fetchone()
    counts = con.execute("SELECT " + ",".join(f"coalesce(count_if({c['id']} IS NOT DISTINCT FROM {lit(v) if v is not None else 'NULL'}),0)" for c, v in zip(columns, candidates)) + ", count(*) FROM numeric_view").fetchone()
    dominant = [{"id": c["id"], "name": c["name"], "candidate_value": v, "exact_candidate_count": count, "fraction": count/counts[-1] if counts[-1] else None, "near_constant_at_99_9_percent": bool(counts[-1] and count/counts[-1] >= .999)} for c, v, count in zip(columns, candidates, counts[:-1])]
    return outputs, dominant


def duplicate_summary(con, columns: list[dict], exclude_metadata: bool = False) -> dict:
    features = [c['id'] for c in columns if c['role'] != 'label' and not (exclude_metadata and c['role'] == 'metadata')]
    labels = [c['id'] for c in columns if c['role'] == 'label']
    label_expr = "row(" + ",".join(labels) + ")" if len(labels)>1 else labels[0]
    # Group actual field values, not hashes: no digest collision can invent a duplicate.
    grouped = f"SELECT count(*) AS n, count(DISTINCT {label_expr}) AS labels, count(DISTINCT source_file) AS files FROM raw GROUP BY " + ",".join(features)
    return fetch_dict(con, f"SELECT count(*) AS distinct_feature_vectors, coalesce(sum(n-1),0) AS repeated_feature_rows, coalesce(sum(n-labels),0) AS duplicate_row_excess, count(*) FILTER(WHERE labels>1) AS conflicting_feature_groups, coalesce(sum(n) FILTER(WHERE labels>1),0) AS rows_in_conflicting_groups, count(*) FILTER(WHERE files>1) AS cross_file_feature_groups FROM ({grouped})")[0]


def temporal_profile(con, columns: list[dict]) -> dict | None:
    mapping = {c['name']: c['id'] for c in columns}
    if 'FLOW_START_MILLISECONDS' not in mapping:
        return None
    s, e = 'n_' + mapping['FLOW_START_MILLISECONDS'], 'n_' + mapping['FLOW_END_MILLISECONDS']
    summary = fetch_dict(con, f"SELECT min({s}) FILTER(WHERE isfinite({s})) AS start_min_ms, max({s}) FILTER(WHERE isfinite({s})) AS start_max_ms, count(*) FILTER(WHERE {e}<{s}) AS end_before_start, count(*) FILTER(WHERE {s}<=0 OR {e}<=0) AS nonpositive_time, count(*) FILTER(WHERE NOT isfinite({s}) OR NOT isfinite({e}) OR {s} IS NULL OR {e} IS NULL) AS invalid_time FROM numeric_view")[0]
    summary['backward_steps_in_file_order'] = con.execute(f"SELECT count(*) FROM (SELECT {s} AS s,lag({s}) OVER(PARTITION BY source_file ORDER BY parsed_row) AS prev FROM numeric_view) WHERE s<prev").fetchone()[0]
    # Group by epoch day without inventing timezone interpretation of original captures.
    attack = mapping.get('Attack', mapping['Label'])
    summary['epoch_day_label_counts'] = fetch_dict(con, f"SELECT floor({s}/86400000)::BIGINT AS epoch_day,{attack} AS label,count(*) AS rows FROM numeric_view WHERE isfinite({s}) GROUP BY ALL ORDER BY 1,2")
    return summary


def audit_family(paths: list[Path], out: Path, memory: str = '4GB', threads: int = 4) -> dict:
    started = time.perf_counter()
    result = {'audit_version': VERSION, 'status': 'RUNNING', 'dataset': paths[0].parent.name, 'files': [], 'stage_timings': {}}
    workspace = Path(tempfile.mkdtemp(prefix='ppfcl-audit-'))
    result['staging_directory']=str(workspace)
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write_json(out,result)
    con = duckdb.connect(str(workspace/'audit.duckdb'))
    con.execute(f"SET memory_limit={lit(memory)}")
    con.execute(f"SET threads={threads}")
    con.execute(f"SET temp_directory={lit(str(workspace/'spill'))}")
    con.execute("SET max_temp_directory_size='120GB'")
    try:
        columns = None
        for i, path in enumerate(paths):
            print(f"{result['dataset']}: hash/load {path.name}", flush=True)
            info = fingerprint(path)
            cols = header_info(path, info['encoding'])
            if columns is not None and [c['raw_name'] for c in cols] != [c['raw_name'] for c in columns]:
                raise ValueError('Within-family headers differ; pooling audit refused')
            columns = cols
            info['source_file'] = i
            info['parsing'] = load_file(con, path, info, columns, i, i>0)
            result['files'].append(info)
            write_json(out, result)
        assert columns
        result['header_fields'] = len(columns)
        result['duplicate_trimmed_headers'] = {k:v for k,v in Counter(c['name'] for c in columns).items() if v>1}
        print(f"{result['dataset']}: column statistics", flush=True)
        stage_start=time.perf_counter()
        result['file_profiles'], result['dominant_values'] = profile(con, columns)
        result['stage_timings']['profile_seconds']=time.perf_counter()-stage_start
        labelcols = [c['id'] for c in columns if c['role']=='label']
        result['label_counts'] = fetch_dict(con, 'SELECT source_file,' + ','.join(labelcols) + ',count(*) AS rows FROM raw GROUP BY ALL ORDER BY ALL')
        result['label_columns'] = [c for c in columns if c['role']=='label']
        result['rows'] = sum(p['rows'] for p in result['file_profiles'])
        result['duplicate_header_value_checks'] = []
        for name in result['duplicate_trimmed_headers']:
            ids = [c['id'] for c in columns if c['name']==name]
            for c in ids[1:]:
                count = con.execute(f"SELECT count(*) FROM raw WHERE {ids[0]} IS DISTINCT FROM {c}").fetchone()[0]
                result['duplicate_header_value_checks'].append({'name':name,'columns':[ids[0],c],'unequal_rows':count})
        write_json(out, result)
        print(f"{result['dataset']}: exact duplicate/conflict grouping", flush=True)
        stage_start=time.perf_counter()
        result['duplicates_all_nonlabel_fields'] = duplicate_summary(con, columns)
        result['stage_timings']['exact_grouping_seconds']=time.perf_counter()-stage_start
        write_json(out, result)
        if any(c['role']=='metadata' for c in columns):
            print(f"{result['dataset']}: predictor-only collisions", flush=True)
            stage_start=time.perf_counter()
            result['duplicates_excluding_identifiers_and_time'] = duplicate_summary(con, columns, True)
            result['stage_timings']['predictor_grouping_seconds']=time.perf_counter()-stage_start
            write_json(out,result)
        print(f"{result['dataset']}: temporal checks", flush=True)
        result['temporal'] = temporal_profile(con, columns)
        for info in result['files']:
            st = Path(info['path']).stat()
            if (st.st_size,st.st_mtime_ns)!=(info['bytes'],info['mtime_ns']):
                raise RuntimeError('Source changed during audit')
        result['status']='COMPLETED'
    except Exception as exc:
        result['status']='FAILED'
        result['error']=f'{type(exc).__name__}: {exc}'
        raise
    finally:
        result['elapsed_seconds']=round(time.perf_counter()-started,3)
        result['staging_directory']=str(workspace)
        con.close()
        # Delete only this script's freshly created temporary workspace, verified under OS temp.
        import shutil
        temp_root = Path(tempfile.gettempdir()).resolve()
        if workspace.resolve().parent == temp_root and workspace.name.startswith('ppfcl-audit-'):
            shutil.rmtree(workspace)
        write_json(out,result)
    return result


def resume_family(paths: list[Path], out: Path, previous: dict, memory: str, threads: int) -> dict:
    """Resume only fully loaded, already profiled staging after validating source hashes."""
    workspace=Path(previous['staging_directory']).resolve()
    temp_root=Path(tempfile.gettempdir()).resolve()
    if workspace.parent!=temp_root or not workspace.name.startswith('ppfcl-audit-') or workspace.is_symlink():
        raise ValueError('Refuse staging directory outside owned temporary namespace')
    actual={str(p.resolve()):fingerprint(p)['sha256'] for p in paths}
    if actual!={f['path']:f['sha256'] for f in previous['files']}:
        raise ValueError('Sources changed; partial audit cannot be resumed')
    result=previous.copy()
    result['prior_partial_audit_version']=previous['audit_version']
    result['audit_version']=VERSION
    result['resumed_partial']=True
    result['elapsed_scope']='Completion invocation only; earlier stage timings remain in stage_timings; total wall time unavailable across interruption.'
    result['status']='RUNNING'
    result.pop('error',None)
    result['completion_script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    columns=header_info(paths[0],previous['files'][0]['encoding'])
    started=time.perf_counter()
    con=duckdb.connect(str(workspace/'audit.duckdb'))
    con.execute(f'SET memory_limit={lit(memory)}');con.execute(f'SET threads={threads}')
    con.execute(f"SET temp_directory={lit(str(workspace/'spill'))}")
    con.execute("SET max_temp_directory_size='120GB'")
    try:
        if con.execute('SELECT count(*) FROM raw').fetchone()[0]!=result['rows']:
            raise ValueError('Cached row count differs from completed profile')
        expected=['source_file','parsed_row']+[c['id'] for c in columns]
        if [r[0] for r in con.execute('DESCRIBE raw').fetchall()]!=expected:
            raise ValueError('Cached schema differs from source header')
        write_json(out,result)
        if 'duplicates_all_nonlabel_fields' not in result:
            print(f"{result['dataset']}: resume exact grouping",flush=True)
            t=time.perf_counter();result['duplicates_all_nonlabel_fields']=duplicate_summary(con,columns)
            result['stage_timings']['exact_grouping_seconds']=time.perf_counter()-t
            write_json(out,result)
        if any(c['role']=='metadata' for c in columns) and 'duplicates_excluding_identifiers_and_time' not in result:
            print(f"{result['dataset']}: resume predictor-only collisions",flush=True)
            t=time.perf_counter();result['duplicates_excluding_identifiers_and_time']=duplicate_summary(con,columns,True)
            result['stage_timings']['predictor_grouping_seconds']=time.perf_counter()-t
            write_json(out,result)
        if 'temporal' not in result:
            print(f"{result['dataset']}: resume temporal checks",flush=True)
            result['temporal']=temporal_profile(con,columns)
        for f in result['files']:
            st=Path(f['path']).stat()
            if (st.st_size,st.st_mtime_ns)!=(f['bytes'],f['mtime_ns']):
                raise ValueError('Source changed during completion')
        result['status']='COMPLETED'
    except Exception as exc:
        result['status']='FAILED';result['error']=f'{type(exc).__name__}: {exc}'
        raise
    finally:
        result['elapsed_seconds']=round(time.perf_counter()-started,3)
        con.close()
        if result['status']=='COMPLETED':
            import shutil
            shutil.rmtree(workspace)
        write_json(out,result)
    return result


def environment() -> dict:
    return {'recorded_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'executable':sys.executable,
            'platform':platform.platform(),'processor_identifier':os.environ.get('PROCESSOR_IDENTIFIER'),
            'cpu_physical':psutil.cpu_count(logical=False),'cpu_logical':psutil.cpu_count(),
            'ram':psutil.virtual_memory()._asdict(),'disk':__import__('shutil').disk_usage('.')._asdict(),
            'packages':{'duckdb':duckdb.__version__,'psutil':psutil.__version__},
            'nvidia_smi':subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],capture_output=True,text=True).stdout.strip()}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('reports/audit'))
    parser.add_argument('--family',action='append')
    parser.add_argument('--memory',default='4GB')
    parser.add_argument('--threads',type=int,default=4)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    write_json(args.output/'environment.json',environment())
    groups={}
    for file in sorted(args.root.rglob('*.csv')):
        if file.name=='NetFlow_v3_Features.csv':
            continue
        if args.family and file.parent.name not in args.family:
            continue
        groups.setdefault(file.parent.name,[]).append(file)
    if not groups:
        raise SystemExit('No dataset CSVs found')
    peak=[0]
    stop=threading.Event()
    def monitor():
        process=psutil.Process()
        ticks=0
        while not stop.wait(.5):
            peak[0]=max(peak[0],process.memory_info().rss)
            ticks+=1
            if ticks%20==0:
                write_json(args.output/'heartbeat.json',{'pid':os.getpid(),'recorded_utc':datetime.now(timezone.utc).isoformat(),'rss_bytes':process.memory_info().rss,'peak_rss_bytes':peak[0]})
    thread=threading.Thread(target=monitor,daemon=True);thread.start()
    start=time.perf_counter()
    summaries=[]
    try:
        for family,paths in sorted(groups.items(),key=lambda item:sum(p.stat().st_size for p in item[1])):
            existing=args.output/(family+'.json')
            if args.resume and existing.exists():
                prior=json.loads(existing.read_text())
                if prior.get('status')=='COMPLETED' and prior.get('audit_version') in {'audit-1.0','audit-1.1','audit-1.2','audit-1.3'}:
                    actual={str(p.resolve()):fingerprint(p)['sha256'] for p in paths}
                    recorded={f['path']:f['sha256'] for f in prior['files']}
                    if actual==recorded:
                        print(f'{family}: reuse completed audit after full hash verification',flush=True)
                        summaries.append(prior)
                        continue
                if prior.get('status')!='COMPLETED' and 'file_profiles' in prior and Path(prior.get('staging_directory','__missing__'),'audit.duckdb').is_file():
                    summaries.append(resume_family(paths,existing,prior,args.memory,args.threads))
                    continue
            summaries.append(audit_family(paths,args.output/(family+'.json'),args.memory,args.threads))
    finally:
        stop.set();thread.join()
        write_json(args.output/'run.json',{'audit_version':VERSION,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'arguments':{k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},'elapsed_seconds':time.perf_counter()-start,'peak_process_rss_bytes':peak[0],'completed_families':[r['dataset'] for r in summaries],'total_rows_completed':sum(r.get('rows',0) for r in summaries),'all_requested_families_completed':len(summaries)==len(groups)})


if __name__=='__main__':
    main()
