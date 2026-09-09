"""Check local external contracts/dictionaries without reading model scores."""
import csv
import hashlib
import json
from pathlib import Path
from audit_datasets import write_json

ROOT=Path(__file__).resolve().parents[1]


def main():
    nf=json.loads((ROOT/'reports/splits/contracts/ND-UNSW-NB15-v3.json').read_text())
    names=[c['name'] for c in nf['predictors']]
    out={'status':'ORDERED_SCHEMA_MATCH_SEMANTICS_CONDITIONAL','source_training_contract':'reports/splits/contracts/ND-UNSW-NB15-v3.json','predictors':len(names),'domains':[],
         'allow_external_model_selection':False,'dictionary_key_rule':'Strip leading/trailing whitespace; require unique resulting keys; preserve original dictionary bytes.',
         'initial_check_failure':'Eight IAT names had trailing spaces in dictionary keys; exact untrimmed lookup failed before any modeling.',
         'semantic_issues':['DURATION_IN and DURATION_OUT have identical direction descriptions','Reverse IAT MAX/AVG/STDDEV descriptions say Minimum','IAT units are not stated','Exact historical extractor binaries/configurations unavailable'],
         'limitation':'Matching keys and dictionary hashes do not resolve these semantic issues; cross-domain transformed overlap and extractor-equivalence review remain required before transfer claims.'}
    for path in sorted((ROOT/'reports/splits/external').glob('*.json')):
        c=json.loads(path.read_text()); dictionary=Path(c['source_files'][0]['path']).parent/'NetFlow_v3_Features.csv'
        with dictionary.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
        descriptions={r['Feature'].strip():r['Description'] for r in rows}
        assert len(descriptions)==len(rows) and all(n in descriptions for n in names)
        assert [x['name'] for x in c['predictors']]==names
        out['domains'].append({'dataset':c['dataset'],'ordered_predictors_match':True,'dictionary_sha256':hashlib.sha256(dictionary.read_bytes()).hexdigest(),'descriptions':{n:descriptions[n] for n in names},'performance_access':'SEALED'})
    dictionary=Path(nf['source_files'][0]['path']).parent/'NetFlow_v3_Features.csv'
    expected=hashlib.sha256(dictionary.read_bytes()).hexdigest()
    assert len(out['domains'])==3 and all(d['dictionary_sha256']==expected for d in out['domains'])
    write_json(ROOT/'reports/preprocessing/external-schema-check.json',out)
    print('Ordered schemas/dictionaries match; documented semantic limitations remain.')


if __name__=='__main__': main()
