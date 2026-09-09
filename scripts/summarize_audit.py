"""Produce a human-readable audit report from authoritative JSON, including partial state."""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def number(value):
    return f'{value:,}' if isinstance(value,int) else str(value)


def safe(value):
    return str(value).replace('|','/').replace('\n',' ').replace('\r',' ')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,default=Path('reports/audit'))
    parser.add_argument('--output',type=Path,default=Path('reports/CP1-dataset-audit.md'))
    args=parser.parse_args()
    datasets=[]
    for path in sorted(args.input.glob('*.json')):
        data=json.loads(path.read_text(encoding='utf-8'))
        if 'dataset' in data:
            datasets.append((path,data))
    lines=['# CP1 local dataset audit','',f'Generated UTC: {datetime.now(timezone.utc).isoformat()}. Audit observations, not detection-model results.','',
           'Sources were inspected without cleaning or fitting preprocessing. Exact-string duplicates use parsed field equality; they do not collapse different numeric spellings. Numeric diagnostics use trimmed values. Approximate cardinalities and dominant-value candidate selection are explicitly labeled in the JSON.','',
           '| Dataset | Status | Parsed rows | Parse error events | Exact duplicate excess | Conflicting feature groups |',
           '|---|---|---:|---:|---:|---:|']
    for _,d in datasets:
        duplicates=d.get('duplicates_all_nonlabel_fields',{})
        lines.append('| '+' | '.join(safe(number(x)) for x in [d['dataset'],d['status'],d.get('rows','pending'),sum(f['parsing']['error_events'] for f in d['files']),duplicates.get('duplicate_row_excess','pending'),duplicates.get('conflicting_feature_groups','pending')])+' |')
    for path,d in datasets:
        lines += ['',f"## {d['dataset']}",'',f"Authoritative JSON: [details](audit/{path.name}). Status: {d['status']}. Runtime: {d.get('elapsed_seconds','pending')} seconds. {d.get('elapsed_scope','Full completed family invocation.')}"]
        if d.get('error'):
            lines += ['', '**Run error:** '+safe(d['error'])]
        lines += ['', '### Files and class support','', '| File | Parsed rows | Physical lines including header | Encoding |','|---|---:|---:|---|']
        for file in d['files']:
            prof=next((p for p in d.get('file_profiles',[]) if p['source_file']==file['source_file']),{})
            lines.append(f"| {safe(Path(file['path']).name)} | {number(prof.get('rows','pending'))} | {number(file['physical_lines'])} | {file['encoding']} |")
        labels=Counter()
        label_ids=[c['id'] for c in d.get('label_columns',[])]
        for row in d.get('label_counts',[]):
            labels[' / '.join(str(row[k]) for k in label_ids)]+=row['rows']
        lines += ['', '| Raw label combination | Rows |','|---|---:|']
        lines += [f'| {safe(label)} | {count:,} |' for label,count in labels.most_common()]
        counts=Counter()
        constants={}
        negative={}
        for file in d.get('file_profiles',[]):
            for col in file['columns']:
                for metric in ['blank','nan','positive_infinity','negative_infinity']:
                    counts[metric]+=col[metric]
                if col['role']=='candidate_feature':
                    counts['nonnumeric_feature_cells']+=col['non_numeric_nonblank']
                    if col['negative_finite']:
                        negative[col['name']]=negative.get(col['name'],0)+col['negative_finite']
                if col['constant_string']:
                    constants.setdefault(col['name'],[]).append(file['source_file'])
        lines += ['', '### Quality and feature implications','',
                  'Cell counts (different problems can occur in the same row): '+', '.join(f'{k}={v:,}' for k,v in counts.items())+'.',
                  '', 'Repeated trimmed headers: '+safe(d.get('duplicate_trimmed_headers',{}))+'.',
                  '', 'Duplicate-header value checks: '+safe(d.get('duplicate_header_value_checks',[]))+'.',
                  '', 'Features with negative finite values (investigate semantic meaning; do not automatically clip): '+safe(negative)+'.',
                  '', 'Exact within-file constant columns and source-file IDs: '+safe(constants)+'.']
        near=[f"{x['name']} ({x['fraction']:.4%})" for x in d.get('dominant_values',[]) if x['near_constant_at_99_9_percent']]
        lines += ['', 'Verified dominant candidates occupying at least 99.9% of the family: '+('; '.join(near) if near else 'none found (see JSON for stage status)')+'.']
        if 'duplicates_excluding_identifiers_and_time' in d:
            lines += ['', 'After excluding identifiers/time, predictor collisions: '+safe(d['duplicates_excluding_identifiers_and_time'])+'. These may be separate events with identical summaries and must not be called raw duplicate flows.']
        temporal=d.get('temporal')
        if temporal:
            lines += ['', '### Time diagnostics','']
            for key,value in temporal.items():
                if key=='epoch_day_label_counts':
                    continue
                lines.append(f'- {key}: {number(value)}')
            for key in ['start_min_ms','start_max_ms']:
                try:
                    date=datetime.fromtimestamp(temporal[key]/1000,tz=timezone.utc).isoformat()
                    lines.append(f'- {key}, interpreted as Unix milliseconds: {date}')
                except (OverflowError,ValueError,TypeError,OSError):
                    lines.append(f'- {key}: not convertible to a supported UTC date')
            lines += ['', 'Epoch-day/label support is retained in JSON. Calendar conversion is diagnostic; capture provenance and chronology must be reviewed before a temporal split.']
        elif d['status']=='COMPLETED':
            lines += ['', 'No supported timestamp columns: fine chronological and host/session-disjoint guarantees cannot be established from these CSVs alone.']
    lines += ['', '## Gate for the next checkpoint','',
              'Use this audit to register deterministic cleaning/exclusion rules and split manifests before model fitting. Keep duplicate groups together, investigate contradictory labels, verify feature semantics and time support, and do not use final-test performance to choose rules. No source data have been repaired by this audit.','',
              'Limits: no PCAP relabeling; no proof of extraction semantics from a matching header; no cross-dataset full-row duplicate join; no host/session independence certificate; no numeric-normalized duplicate equivalence; no train/test split created. Near-constant screening can miss a dominant value if its approximate candidate is wrong.','']
    args.output.write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    main()
