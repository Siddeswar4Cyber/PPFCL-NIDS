"""Frozen F2 candidate selection, exact F1 reuse and confirmation schedule."""
import argparse
from pathlib import Path
from audit_datasets import write_json
from preprocess_p1 import sha
from run_baseline_pilot import ROOT,DATASETS,PROTOCOLS
from run_cp8 import read,binding
from run_cp9 import ident as f1_ident
from run_cp10 import FEDERATED,supervise
from build_clients_c1 import SCENARIOS

SEEDS=[17,29,43]


def resolve(dataset,protocol,method,scenario,seed,candidate):
    if seed==17 and candidate==1 and method in ['central','local','fedavg']:
        path=ROOT/'reports/cp9/runs'/f'{f1_ident(dataset,protocol,method,scenario)}.json'
        v=read(ROOT/'reports/cp9/verification.json'); assert v['status']=='PASSED'
        b=next(b for b in v['report_bindings'] if Path(b['path']).resolve()==path.resolve())
        assert sha(path)==b['sha256']; r=read(path)
        assert r['status']=='COMPLETED' and r['exit_code']==0
        for item in r['source_bindings']+[r['initial_weights'],r['validation_predictions']]+r['final_models']:
            assert sha(item['path'])==item['sha256']
        print('F1 exact reuse: '+r['run_id'],flush=True)
    else: path=supervise(dataset,protocol,method,scenario,seed,candidate)
    return {'dataset':dataset,'protocol':protocol,'method':method,'scenario':scenario,'seed':seed,'candidate':candidate,
            'reused_f1':str(path.parent.parent.name)=='cp9','run':binding(path)}


def choose(entries):
    scored=[]
    for entry in entries:
        assert sha(entry['run']['path'])==entry['run']['sha256']
        r=read(entry['run']['path']); e=r['evaluation']
        scored.append(dict(entry,pooled_f1=e['metrics_05']['binary_macro_f1'],ap=e['metrics_05']['average_precision'],
            worst_f1=e['client_macro_f1']['minimum']))
    best=max(c['pooled_f1'] for c in scored)
    eligible=[c for c in scored if c['pooled_f1']>=best-.002]
    best_ap=max(c['ap'] for c in eligible)
    eligible=[c for c in eligible if c['ap']>=best_ap-.002]
    chosen=max(eligible,key=lambda c:(c['worst_f1'],c['pooled_f1'],c['ap'],-c['candidate']))
    return {'dataset':chosen['dataset'],'protocol':chosen['protocol'],'method':chosen['method'],
            'selected_candidate':chosen['candidate'],'candidates':scored}


def tuning():
    path=ROOT/'reports/cp10/tuning-selection.json'
    if path.exists():
        saved=read(path); assert saved['status']=='FROZEN'
        assert saved['driver_sha256']==sha(__file__) and sha(saved['protocol']['path'])==saved['protocol']['sha256']
        for s in saved['scopes']: assert choose(s['candidates'])==s
        return saved
    scopes=[]
    for d in DATASETS:
        for p in PROTOCOLS:
            for m in FEDERATED:
                scopes.append(choose([resolve(d,p,m,'dirichlet_a1',17,c) for c in range(3)]))
    result={'version':'F2','status':'FROZEN','driver_sha256':sha(__file__),
            'protocol':binding(ROOT/'docs/CP10-federated-comparison-F2.md'),'scopes':scopes}
    write_json(path,result); return result


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['tune','all']); args=parser.parse_args()
    selection=tuning()
    if args.action=='tune': return
    path=ROOT/'reports/cp10/cell-manifest.json'
    if path.exists(): raise RuntimeError('Preserve existing manifest')
    cells=[]; controls=[]
    for d in DATASETS:
        for p in PROTOCOLS:
            for seed in SEEDS:
                controls.append(resolve(d,p,'central','all',seed,1))
                for scenario in SCENARIOS:
                    controls.append(resolve(d,p,'local',scenario,seed,1))
                    for m in FEDERATED:
                        c=next(s['selected_candidate'] for s in selection['scopes'] if (s['dataset'],s['protocol'],s['method'])==(d,p,m))
                        cells.append(resolve(d,p,m,scenario,seed,c))
    assert len(cells)==108 and len(controls)==48
    write_json(path,{'version':'F2','status':'COMPLETED','driver_sha256':sha(__file__),
        'selection':binding(ROOT/'reports/cp10/tuning-selection.json'),'cells':cells,'controls':controls})
    print('F2 complete: 108 method cells + 48 control systems, with exact reuse recorded',flush=True)


if __name__=='__main__': main()
