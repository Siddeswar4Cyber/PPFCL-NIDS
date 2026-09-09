"""Summarize verified CP7 data contracts without creating model results."""
import json
import sys
from pathlib import Path
import duckdb
import numpy as np
import pyarrow as pa
from audit_datasets import write_json
from preprocess_p1 import sha
from run_baseline_pilot import ROOT


def read(path): return json.loads(Path(path).read_text())


def main():
    verification=read(ROOT/'reports/cp7/verification.json'); assert verification['status']=='PASSED'
    assert verification['verification_script_sha256']==sha(ROOT/'scripts/verify_cp7.py')
    for binding in verification['report_bindings']: assert sha(binding['path'])==binding['sha256']
    clients=[read(p) for p in sorted((ROOT/'reports/cp7/clients').glob('*.json'))]; host=read(ROOT/'reports/cp7/host-feasibility.json')
    assert len(clients)==12 and all(c['status']=='COMPLETED' for c in clients) and host['status']=='COMPLETED'
    assert len(verification['client_checks'])==12 and len(verification['host_checks'])==4
    tests=(ROOT/'reports/cp7-tests.log').read_text(encoding='utf-8'); assert 'Ran 26 tests' in tests and tests.strip().endswith('OK')
    lines=['# CP7 host feasibility and client contracts','',
        'C1 / H1 / M0.7, 2026-09-10. Twelve client manifests are constructed and verified, covering five logical clients in each of four dataset/protocol namespaces and three allocation scenarios. Four fixed host-separation candidates were assessed and rejected for insufficient support. No classifier or FL model was trained, and final/external scores remain sealed.','',
        '## Host separation findings','',
        '| NF scope | Permitted development/validation rows | Endpoint addresses | Components | Components with attacks |','|---|---:|---:|---:|---:|']
    for h in host['protocols']: lines.append(f"| {h['protocol']} | {h['permitted_rows']:,} | {h['endpoint_count']} | {len(h['components'])} | {h['attack_containing_components']} |")
    lines+=['','Every attack is in one 20-address component in each scope. A separate 20-address component contains only benign traffic. Components include both endpoint edges and any feature-group bridges. Retaining all permitted flows while separating endpoints therefore cannot give both training and validation attack examples. This conclusion is conditional on the observed development population and the endpoint-identity assumptions.','',
        '| NF scope | Component size in rows | Endpoint addresses | Benign rows | Attack rows |','|---|---:|---:|---:|---:|']
    for h in host['protocols']:
        for c in h['components']: lines.append(f"| {h['protocol']} | {c['rows']:,} | {c['endpoints']} | {c['benign']:,} | {c['attack']:,} |")
    lines+=['','| NF scope / candidate | Retained training rows | Retained validation rows | Validation benign / attack | Rejection reason |','|---|---:|---:|---|---|']
    for h in host['protocols']:
        for c in h['candidates']:
            support={s['partition']:s for s in c['support']}; tr=support.get('train',{}); val=support.get('validation',{})
            lines.append(f"| {h['protocol']} / {c['method']} | {tr.get('rows',0):,} | {val.get('rows',0):,} | {val.get('benign',0)} / {val.get('attack',0)} | {'; '.join(c['reasons'])} |")
    lines+=['','The component-hash rule placed all components on the training side, leaving no retained validation. Independently of that draw, only one attack component prevents a no-discard two-class split. Endpoint filtering retains 1,208 primary validation rows (2 benign) and 439 stress rows (1 benign), below the registered support floors. No seed search or floor relaxation followed. These fixed rejections do not establish that every possible population-changing host subset is impossible.','',
        'Candidate ledgers retain all permitted rows with explicit exclusion reasons. Original training/validation roles are preserved; earlier validation never becomes training. No model score is produced for a rejected candidate. CIC host metadata is unavailable, so no CIC host-separation assertion is made.','',
        '## Five-client assignments','',
        '| Dataset / scope | Requested scenario | Actual method | Attempts | Training rows, clients 0–4 | Training attack-prevalence range | Eligible validation clients |','|---|---|---|---:|---|---|---:|']
    for r in clients:
        train=[s for s in r['support'] if s['partition']=='train']; val=[s for s in r['support'] if s['partition']=='validation']
        rows=' / '.join(f"{s['rows']:,}" for s in train); low=min(s['attack_prevalence'] for s in train); high=max(s['attack_prevalence'] for s in train)
        lines.append(f"| {r['dataset']} / {r['protocol']} | {r['requested_scenario']} | {r['actual_method']} | {len(r['attempts'])} | {rows} | {low:.2%}–{high:.2%} | {sum(s['balanced_evaluation_eligible'] for s in val)}/5 |")
    fallback=[r for r in clients if r['actual_method']=='dirichlet_uniform10_fallback']
    failed=sum(sum(not a['accepted'] for a in r['attempts']) for r in clients)
    lines+=['',f'{len(fallback)} scenarios required the registered 10% uniform mixture after 20 unsuccessful pure Dirichlet draws. Across all scenarios, {failed} rejected allocation attempts are preserved with their probability matrices and training support. NF primary alpha 0.1 accepted its tenth pure draw; NF stress alpha 1.0 accepted its second. Acceptance used training support only.','',
        'Every client has at least 1,000 training representatives and 20 examples of each binary class. Every validation client also meets the registered 20-per-binary-class eligibility floor, without validation-based retries. Rare canonical attack classes can still be absent in individual clients; full class counts are retained in each client report. Small alpha and a fallback do not guarantee a particular ordering of realized heterogeneity: use the measured distributions.','',
        'Each scenario partitions exactly the same 100,000 training representatives and the complete corresponding validation matrix. Duplicate feature groups have one owner; no group crosses training/validation or clients. Saved row indices preserve parent matrix order, so future model comparisons can read the same vectors without copying or reshuffling their identities. All scenario manifests are separate views of reused populations, not additional independent data.','',
        '## Interpretation and next step','',
        'C1 clients are synthetic partitions, not real institutions, host-disjoint populations or five datasets. Label-skew validation ownership is generated from the training-fitted label probabilities. The common preprocessing was fitted centrally on permitted development data. It supports controlled non-private simulations, with no distributed-preprocessing or differential-privacy guarantee. Private/public-reference/final/external client ownership and CL-specific contracts remain uncreated.','',
        'CP8 can verify neural-framework migration, input precision and optimization stability, then define central/local/FL comparisons on identical C1 assignments. This advances a scoped synthetic-client study; it does not repair independent-host generalization. Stronger claims would require a new approved data/split study. Current model choices and final evaluation remain provisional.','',
        '## Verification and provenance','',
        'All 26 tests pass. The verifier reconstructs allocation attempts from training only, independently computes hash-based ownership, checks exact parent rows and source roles, and rebuilds host components with graph traversal plus feature-group bridges. It also recomputes candidate-side/exclusion rules from the original NF source and verifies support and zero endpoint/group overlap.','',
        'H1 uses a 4-GB DuckDB memory limit and four threads; this is a configured limit, not measured process RSS. C1 per-scenario timings exclude loading/hashing parent matrices. No model training latency, communication cost or FL detection metric is claimed.','',
        'See [protocol](../docs/CP7-host-client-protocol-C1.md), [verification](cp7/verification.json), [host support and candidate bindings](cp7/host-feasibility.json), [test log](cp7-tests.log), [viva notes](../docs/CP7-viva.md), and [checkpoint verification](CP7-checkpoint-verification.md).']
    (ROOT/'reports/CP7-host-client-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    environment={'python':sys.version.split()[0],'numpy':np.__version__,'pyarrow':pa.__version__,'duckdb':duckdb.__version__}
    project_path=ROOT/'docs/registries/project.json'; project=read(project_path)
    entries=[]
    for r in clients:
        entries.append({**r,'date':'2026-09-10','architecture_version':'A0','model':'None; assignment preparation','hardware':'reports/audit/environment.json',
            'environment_versions':environment,'privacy_configuration':'Non-private development; centrally fitted preprocessing','cl_configuration':'No task-specific allocation',
            'result':'Client contract verified; no FL/model score','interpretation':'Synthetic group ownership with training-support-conditioned allocation'})
    entries.append({**host,'date':'2026-09-10','architecture_version':'A0','model':'None; host feasibility analysis','hardware':'reports/audit/environment.json',
        'environment_versions':environment,'result':'Four fixed candidates rejected for support; independent-host binary evaluation unestablished'})
    for entry in entries: project['runs']=[r for r in project['runs'] if r['run_id']!=entry['run_id']]+[entry]
    e3=next(e for e in project['experiments'] if e['experiment_id']=='EXP-003')
    e3.update(result='B1/B2 model comparisons and H1 host feasibility complete; no supported host-disjoint binary challenge under registered rules',
        decision='Proceed only with explicit S1 synthetic-client scope; revisit neural stability at CP8',
        interpretation='Source-corpus validation evidence; all NF attacks share one endpoint component; final detector freeze remains open')
    e3['artifacts']=list(dict.fromkeys(e3['artifacts']+['reports/CP7-host-client-results.md','reports/cp7/host-feasibility.json']))
    e4=next(e for e in project['experiments'] if e['experiment_id']=='EXP-004')
    e4.update(date='2026-09-10',status='RUNNING',phase='CLIENT_CONTRACTS_COMPLETE; MODEL_TRIALS_NOT_STARTED',
        dataset_version='Source-bound CIC P2 / NF P1 development samples',split_version='S1 / C1',preprocessing_version='CIC P2 / NF P1; B2 representation options',
        feature_set='Unchanged parent vectors; C1 supplies only ownership indices',client_configuration='Five clients; IID, alpha 1.0, alpha 0.1 with explicitly labeled uniform-mixture fallbacks',
        model='Pending verified neural migration: centralized/local references and FL candidates',hardware='reports/audit/environment.json',environment_versions=environment,
        metrics={'verified_client_manifests':12,'clients_per_manifest':5,'uniform_mixture_fallbacks':len(fallback),'rejected_allocation_attempts':failed,'FL_model_runs':0},
        artifacts=['reports/CP7-host-client-results.md','reports/cp7/clients','reports/cp7/verification.json'],logs=['reports/cp7-client-construction.log','reports/cp7-verification.log'],
        git_commit=clients[0]['git_commit'],runtime={'scenario_assignment_seconds':sum(c['elapsed_seconds'] for c in clients),'parent_io_additional':True},memory_usage='Not sampled; H1 DuckDB configured at 4GB',
        result='C1 assignments verified; no FL results exist',interpretation='Preparation only; shared hosts and centrally fitted development preprocessing limit claims',
        decision='Advance to CP8 migration/stability before comparable central/local/FL training',architecture_impact='Logical client ownership implemented; aggregation/training remain unimplemented')
    decisions=[('DEC-021','Can the registered H1 candidates support two-class host separation?','Reject all four fixed candidates; retain explicit host-generalization limitation','All attacks occupy one component; filtered validation lacks benign support'),
        ('DEC-022','How are supported five-client partitions defined?','Freeze 12 C1 manifests; label three uniform-mixture fallbacks explicitly','Training-only acceptance and deterministic group ownership pass'),
        ('DEC-023','Can work proceed after H1 rejection?','Proceed with non-private synthetic-client comparisons only; no institutional or independent-host claim','S1/C1 controls support a narrower simulation; neural migration and privacy accounting remain separate gates')]
    for did,question,choice,why in decisions:
        if not any(d['decision_id']==did for d in project['decisions']):
            project['decisions'].append({'decision_id':did,'question':question,'selected_option':choice,'why_selected':why,
                'candidate_alternatives':['Ignore support/identity limits',choice],'evidence_considered':['docs/CP7-host-client-protocol-C1.md','reports/CP7-host-client-results.md'],
                'experiments_used':['EXP-003','EXP-004'],'rejected_alternatives':['Claim real institutions or supported independent-host evaluation'],'why_rejected':'Unsupported by source metadata and support',
                'risks':['Address identity assumptions','Conditional allocation and label-aware evaluation','Rare-class support','Shared centralized development preprocessing'],
                'trade_offs':['Narrower generalization scope; explicit fallback heterogeneity'],'confidence':'High for verified manifests and support; limited for external generalization',
                'architecture_version':'A0','revisit_condition':'Approved new split/data or subsequent migration/FL evidence'})
    failures=[]
    for hr in host['protocols']:
        for candidate in hr['candidates']:
            failures.append({'experiment_id':'EXP-003','what_failed':f'H1 {hr["protocol"]}/{candidate["method"]} support gate','error':'; '.join(candidate['reasons']),
                'suspected_cause':'Attack concentration and fixed host partition support','investigation':'reports/cp7/host-feasibility.json',
                'fix':'Do not score candidate; retain a scoped synthetic-client study','scientifically_invalid':True,'rerun_required':False})
    for r in clients:
        rejected=[a['attempt'] for a in r['attempts'] if not a['accepted']]
        if rejected: failures.append({'experiment_id':'EXP-004','what_failed':r['run_id']+' raw allocation attempts','error':'Per-client training support below registered floors',
            'suspected_cause':'Stochastic label/quantity skew','investigation':f'reports/cp7/clients/{r["dataset"]}-{r["protocol"]}-{r["requested_scenario"]}.json',
            'rejected_attempts':rejected,'fix':r['actual_method']+' accepted using training data only','scientifically_invalid':False,'rerun_required':False})
    for f in failures:
        if f not in project['failures']: project['failures'].append(f)
    a=next(a for a in project['architectures'] if a['version']=='A0')
    a['supporting_experiments']=list(dict.fromkeys(a['supporting_experiments']+['EXP-004']))
    a['supporting_decisions']=list(dict.fromkeys(a['supporting_decisions']+['DEC-021','DEC-022','DEC-023']))
    a['components']=list(dict.fromkeys(a['components']+['C1 synthetic client ownership on fixed development matrices']))
    a['known_limitations']=list(dict.fromkeys(a['known_limitations']+['H1 fixed candidates fail binary support; all NF attacks in one component',
        'Three C1 alpha-0.1 scopes use a registered uniform mixture; allocations conditioned on training support',
        'Shared development preprocessing; no private or CL-specific client contract']))
    a['status']='PROVISIONAL / DATA, CENTRALIZED COMPARISONS AND CLIENT OWNERSHIP IMPLEMENTED'
    project['progress'].update(checkpoint='CP7',status='COMPLETE',current=[],next=['CP8: verify neural framework migration, precision and optimizer stability','Preregister comparable central/local/FL pilots on fixed C1 manifests'],
        needs_validation=['Neural migration and optimizer stability','FL method comparison on C1','Private preprocessing, allocation and DP accounting','CL-specific clients/tasks and forgetting comparisons','Final/external evaluation after freeze'])
    project['progress']['completed']=list(dict.fromkeys(project['progress']['completed']+['H1 host feasibility with explicit support rejections','Twelve verified C1 logical-client manifests']))
    write_json(project_path,project)
    print('CP7 records complete: 12 client manifests, 4 host candidate rejections, no model training',flush=True)


if __name__=='__main__': main()
