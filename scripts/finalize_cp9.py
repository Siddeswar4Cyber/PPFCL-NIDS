"""Publish verified F1 pilot results without selecting a final FL method."""
from pathlib import Path
from audit_datasets import write_json
from preprocess_p1 import sha
from run_baseline_pilot import ROOT
from run_cp8 import read


def main():
    v=read(ROOT/'reports/cp9/verification.json')
    assert v['status']=='PASSED' and v['script_sha256']==sha(ROOT/'scripts/verify_cp9.py')
    assert sha(v['comparison']['path'])==v['comparison']['sha256']
    for b in v['report_bindings']: assert sha(b['path'])==b['sha256']
    comparisons=read(v['comparison']['path'])['comparisons']; runs=[read(b['path']) for b in v['report_bindings']]
    assert len(runs)==28 and len(comparisons)==12 and all(r['status']=='COMPLETED' for r in runs)
    signals=sum(c['exploratory_collaboration_signal'] for c in comparisons)
    worst_delta=min(comparisons,key=lambda c:c['fedavg_minus_local_macro_f1'])
    best_delta=max(comparisons,key=lambda c:c['fedavg_minus_local_macro_f1'])
    lines=['# CP9 centralized, local-only and federated pilot', '',
        'F1 / M0.9, 2026-09-10. CP9 is COMPLETE: 28 registered seed-17 run records, 76 final models and all 36 tests pass. Twelve federated systems complete 20 rounds each. Verification reconstructs all 240 aggregations and reproduces final validation predictions, work ledgers and metrics. This is an exploratory non-private simulation, not a final FL-method selection.', '',
        '## What is compared', '',
        'Four fresh centralized references each train on their existing 100,000 representatives. For each of the twelve C1 scenarios, five independent local models train on their own rows and one federated model averages five client updates per round. Validation rows in the local system are routed to their owner model; they are not ensembled. The centralized reference is reused across three ownership views in its namespace, without counting additional fits.', '',
        'All methods use the same 64/32 model initializer and their own N1-selected learning rate. Every training row appears 20 times: 2,000,000 example presentations per method/scenario. Batch size is 256. Adam state resets every epoch/round in all methods. F1 uses a constant weight-only L2 coefficient 0.0001/256, including short minibatches; fresh central controls account for this change from N1. Equal exposure does not mean equal optimizer-step counts or trajectories.', '',
        'Similar summed optimizer-step counts also do not imply similar global optimization: FedAvg averages separate client update sequences at each round, while the centralized reference applies every batch update serially to one model. The learning rates were inherited from centralized N1 tuning, not independently optimized for F1 federation. CP10 needs equal, registered method-specific tuning allowances before a final method ranking.', '',
        'The federated variant is **FedAvg with client Adam**: full participation, one local epoch per round, n_k/N parameter averaging including biases, CPU float64 accumulation and one float32 cast. It has no server optimizer and is not server-side FedAdam. Every client receives the same round-start state; optimizer moments are not aggregated. The simulator accesses common matrices and is not a confidentiality boundary.', '',
        '## Pooled and worst-client results at threshold 0.5', '',
        '| Scope / requested scenario | Central pooled F1 | Local pooled F1 | FedAvg pooled F1 | Central worst-client F1 | Local worst-client F1 | FedAvg worst-client F1 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for c in comparisons:
        values=[c[m]['metrics_05']['binary_macro_f1'] for m in ['central','local','fedavg']]
        worst=[c[m]['client_macro_f1']['minimum'] for m in ['central','local','fedavg']]
        lines.append(f'| {c["dataset"]} / {c["protocol"]} / {c["scenario"]} | '+' | '.join(f'{x:.6f}' for x in values+worst)+' |')
    lines+=['','| Scope / scenario | Actual C1 allocation | FedAvg − local pooled F1 | FedAvg − central pooled F1 | FedAvg − local worst F1 | Exploratory signal |',
        '|---|---|---:|---:|---:|---|']
    for c in comparisons:
        lines.append(f'| {c["dataset"]} / {c["protocol"]} / {c["scenario"]} | {c["actual_client_method"]} | {c["fedavg_minus_local_macro_f1"]:+.6f} | {c["fedavg_minus_central_macro_f1"]:+.6f} | {c["fedavg_minus_local_worst_client_macro_f1"]:+.6f} | {"Yes" if c["exploratory_collaboration_signal"] else "No"} |')
    lines+=['',f'{signals}/12 scenarios meet the preregistered exploratory signal: pooled macro-F1 improves over routed-local by at least 0.002 and worst-client macro-F1 degrades by no more than 0.01. This flag is not a significance test or a final winner decision. Outcomes outside it remain valid results; no configuration was changed after scores.', '',
        f'The largest observed pooled gain over local-only is {best_delta["fedavg_minus_local_macro_f1"]:+.6f} in {best_delta["dataset"]}/{best_delta["protocol"]}/{best_delta["scenario"]}. The largest decline is {worst_delta["fedavg_minus_local_macro_f1"]:+.6f} in {worst_delta["dataset"]}/{worst_delta["protocol"]}/{worst_delta["scenario"]}. FedAvg is therefore not promoted as uniformly beneficial. Local-update drift under heterogeneous data is a hypothesis for a registered CP10 comparison, not an established causal explanation from these scenarios.', '',
        'Local-only also maintains a separate parameter set for each client, while FedAvg serves one global model. Relative results therefore reflect client specialization as well as optimization. With label-skew simulated ownership, locally useful class priors can differ sharply; these outcomes should not be generalized to measured institutions or interpreted as a pure effect of model averaging.', '',
        'The three uniform-mixture C1 fallbacks retain their actual labels. Label-aware simulated validation ownership and training-support-conditioned allocation limit interpretation. The twelve scenarios reuse four underlying validation populations; they are not twelve independent data samples. Single-seed differences do not establish robustness or population uncertainty.', '',
        '## AP, false positives and client support', '',
        '| Scope / scenario | Central AP | Local AP | FedAvg AP | FedAvg benign FPR at 0.5 | FedAvg recall at pooled calibrated threshold |',
        '|---|---:|---:|---:|---:|---:|']
    for c in comparisons:
        aps=[c[m]['metrics_05']['average_precision'] for m in ['central','local','fedavg']]
        lines.append(f'| {c["dataset"]} / {c["protocol"]} / {c["scenario"]} | '+' | '.join(f'{x:.6f}' for x in aps)+
            f' | {c["fedavg"]["metrics_05"]["benign_fpr"]:.6f} | {c["fedavg"]["metrics_fpr01"]["attack_recall"]:.6f} |')
    lines+=['','The full comparison artifact includes binary/attack-family support, AP/ROC, confusion matrices, pooled metrics and per-client metrics at 0.5 and the common pooled validation-fitted <=1% benign-FPR threshold. A pooled FPR bound does not hold for every client. Client macro-F1 mean, row-weighted mean, minimum and population SD are separate from pooled macro-F1. All validation clients meet the C1 binary support floor; an absent canonical family has null recall.', '',
        '## Work, runtime and calculated communication', '',
        '| Scope / method / scenario | Optimizer steps | Fit seconds | Model payload upload / download bytes |',
        '|---|---:|---:|---|']
    for r in runs:
        comm=r['communication']; payload=f'{comm["upload_bytes"]:,} / {comm["download_bytes"]:,}' if r['method']=='fedavg' else 'Not estimated'
        lines.append(f'| {r["dataset"]} / {r["protocol"]} / {r["method"]} / {r["scenario"]} | {r["optimizer_steps"]:,} | {r["fit_seconds"]:.3f} | {payload} |')
    lines+=['',f'Total measured fitting time is {sum(r["fit_seconds"] for r in runs):.3f} seconds; supervised model-worker time is {v["supervised_model_worker_seconds"]:.3f} seconds. The four-hour EXP-004 family budget retains {v["four_hour_family_budget_remaining_seconds"]:.3f} seconds for later model workers. Tests and final verification are additional overhead and are not included in this model-worker sum.', '',
        f'Maximum sampled worker-tree RSS is {max(r["sampled_peak_process_rss_bytes"] for r in runs)/2**30:.3f} GiB; maximum CUDA allocated/reserved memory is {max(r["cuda_peak_allocated_bytes"] for r in runs)/2**30:.3f} / {max(r["cuda_peak_reserved_bytes"] for r in runs)/2**30:.3f} GiB. Every worker stayed within the 600-second, 12-GiB process-tree and 4-GiB allocator limits. One worker/client update ran at a time. RSS is sampled every 0.5 seconds and excludes the supervisor; Torch allocator counters exclude some driver memory.', '',
        'Payload counts represent 20 training rounds × five uploads/downloads × all float32 parameter bytes including biases. They are calculated dense-model payloads, not measured network traffic or latency. Serialization, transport, metadata, cryptography, optimizer state, raw-data transfer and any additional final-model deployment broadcast are excluded. Saving intermediate states locally supports audit and is not a privacy measure. No secure aggregation, DP or deployed cross-institution system is implemented.', '',
        '## Verification, limitations and next checkpoint', '',
        'Verification binds N1 selection and parent/C1/data/model/code artifacts; confirms exact ownership and example/step coverage; reconstructs shuffled global-row order hashes; checks identical client starts and round chaining; recomputes all weighted aggregations with NumPy; reloads every final model; and reproduces routed/global probabilities, metrics and operating points. The one-client fixture matches local training exactly, including reset-state behavior; unequal weights, invalid uploads and the common regularization gradient are tested.', '',
        'Source-corpus validation and the financial deployment scenario remain distinct. NF endpoints overlap training almost entirely; H1 did not establish a host-separated binary challenge. C1 represents synthetic clients, including fallback-conditioned heterogeneity, and its shared preprocessing was fitted centrally on development data. Neither FL nor the present simulation supplies a formal privacy guarantee. No final/external model scores or CL training occurred.', '',
        'CP10 should preregister bounded FL challengers and confirmation seeds, using these fixed central/local/FedAvg references and the remaining family budget. Do not declare a winning FL method from CP9 alone. Preserve all negative collaboration outcomes and inspect per-client regressions before selecting later configurations.', '',
        'Evidence: [F1 protocol](../docs/CP9-federated-pilot-F1.md), [complete comparison](cp9/comparison.json), [verification](cp9/verification.json), [test log](cp9/tests.log), [checkpoint checks](CP9-checkpoint-verification.md), [viva notes](../docs/CP9-viva.md).']
    (ROOT/'reports/CP9-federated-results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (ROOT/'reports/CP9-checkpoint-verification.md').write_text('''# CP9 checkpoint verification

F1 completed all 28 seed-17 runs: four centralized references, twelve five-model local systems and twelve global federated systems. All 36 tests pass; the targeted F1 tests were rerun after final helper additions.

- Parent artifacts, C1 row identity, training/validation ownership and source hashes are verified.
- Each method/scenario has 2,000,000 example presentations; per-client steps and full-coverage order hashes reproduce.
- All 240 federated rounds reconstruct with independent NumPy weighted sums; uploaded shapes/dtypes/finite values, shared starts and global chaining pass.
- Final models reproduce all saved global or owner-routed validation probabilities and metrics.
- Centralized ownership views reuse the same saved probabilities; no duplicate fit is counted.
- Initializer, objective coefficient, selected learning rates, optimizer reset policy and paired local/FL order streams match F1.
- Resource, dense tensor-payload and cumulative four-hour model-worker accounting pass.
- Single seed; no final winner, DP, secure aggregation, CL or final/external score.

The machine-readable verification and comparison bind all run reports. CP10 remains required for registered challengers and seed sensitivity.
''',encoding='utf-8')
    (ROOT/'docs/CP9-viva.md').write_text('''# CP9 viva notes

**What is federated here?** Five logical clients update a shared neural model locally for one epoch; a coordinator averages parameter states using training-row fractions. All computation is simulated sequentially on one laptop.

**Is it the original FedAvg optimizer?** The aggregation is sample-weighted FedAvg, but client updates use native Adam. The original algorithm used local SGD. There is no server optimizer, so this is not server-side FedAdam.

**Why reset moments in the controls?** All methods reset Adam each epoch/round to match the registered federated reset policy. Weight trajectories still differ. Fresh centralized controls account for this and the constant regularization coefficient.

**What does equal work mean?** Every sample is presented 20 times. Unequal client sizes and short batches produce different step counts, which are reported. It does not mean equal parallel wall time or identical optimization.

**How is local-only evaluated?** A validation row goes to its assigned client's model. The combined probability vector represents this routed system; it is not an ensemble.

**How are client and pooled F1 different?** Pooled F1 comes from the combined confusion matrix. Mean, weighted mean and minimum client F1 summarize separate confusion matrices and need not equal pooled F1.

**Does 1% pooled FPR protect every client?** No. One threshold is fitted on pooled validation and then applied unchanged to each client's rows; individual false-positive rates may exceed 1%.

**How is communication measured?** It is a calculated dense float32 tensor payload for uploads and downloads, not actual network traffic. Transport, serialization, cryptography and raw-data transfer are excluded.

**Does the simulator protect data?** No formal protection is claimed. The simulator accesses common matrices, preprocessing was centrally fitted, and updates can disclose information. DP, secure aggregation and deployment isolation are separate unimplemented gates.

**Can a method be selected now?** CP9 has one seed and reused validation. Its collaboration signal is an exploratory reporting rule; CP10 must preregister challengers and seed checks before a final FL decision.
''',encoding='utf-8')
    project_path=ROOT/'docs/registries/project.json'; project=read(project_path)
    for r in runs:
        entry=dict(r,date='2026-09-10',model='MLP 64/32, F1 fixed objective',hardware='RTX 4050 Laptop GPU; reports/cp8/runtime-installation.json',
            environment_versions=r['environment'])
        project['runs']=[old for old in project['runs'] if old['run_id']!=r['run_id']]+[entry]
    decisions=[('DEC-027','How are CP9 optimization/exposure controls made comparable?',
        'Use fresh F1 central/local references, fixed weight-only regularization and epoch/round-reset client Adam',
        'Identical objective/initializer and 20 presentations per row; report unequal steps explicitly'),
        ('DEC-028','What can the single-seed federated pilot establish?',
        f'Record {signals}/12 exploratory collaboration signals; keep FedAvg as a reference and defer final selection',
        'All results verified but one seed, reused validation and synthetic clients limit conclusions')]
    for did,question,choice,why in decisions:
        if not any(d['decision_id']==did for d in project['decisions']):
            project['decisions'].append({'decision_id':did,'question':question,'selected_option':choice,'why_selected':why,
                'candidate_alternatives':['Reuse N1 as an identical objective/optimizer control','Declare a final winner from one seed',choice],
                'evidence_considered':['docs/CP9-federated-pilot-F1.md','reports/CP9-federated-results.md','reports/cp9/comparison.json'],
                'experiments_used':['EXP-004'],'rejected_alternatives':['Claim private deployment','Hide poor client outcomes'],
                'why_rejected':'Unsupported by this non-private pilot','risks':['Single seed','Shared hosts','Label-aware ownership','Client drift','Validation reuse'],
                'trade_offs':['Controlled exposure still permits different update counts and trajectories'],
                'confidence':'High for reproduction; exploratory for comparative benefit','architecture_version':'A0',
                'revisit_condition':'Registered CP10 method/seed evidence or a new privacy/deployment protocol'})
    e4=next(e for e in project['experiments'] if e['experiment_id']=='EXP-004')
    e4.update(status='RUNNING',phase='F1_SEED17_PILOT_COMPLETE; METHOD_SELECTION_PENDING',date='2026-09-10',
        model='MLP 64/32; centralized, routed local-only and sample-weighted FedAvg with client Adam',
        result=f'28 F1 run records verified; {signals}/12 exploratory collaboration signals',
        interpretation='No final method decision or privacy guarantee; confirm with registered challengers and seeds',
        decision='Proceed to bounded CP10 within remaining cumulative family budget',
        metrics={'verified_client_manifests':12,'clients_per_manifest':5,'uniform_mixture_fallbacks':3,
                 'FL_model_runs':12,'central_model_runs':4,'local_system_runs':12,'local_final_models':60,'verified_aggregation_rounds':240,
                 'exploratory_collaboration_signals':signals},
        runtime={'F1_supervised_worker_seconds':v['supervised_model_worker_seconds'],'family_budget_remaining_seconds':v['four_hour_family_budget_remaining_seconds']})
    e4['artifacts']=list(dict.fromkeys(e4['artifacts']+['reports/CP9-federated-results.md','reports/cp9/comparison.json','reports/cp9/verification.json']))
    a=next(a for a in project['architectures'] if a['version']=='A0')
    a['components']=list(dict.fromkeys(a['components']+['F1 parameter-only weighted aggregation and non-private sequential-client simulator']))
    a['supporting_decisions']=list(dict.fromkeys(a['supporting_decisions']+['DEC-027','DEC-028']))
    a['status']='PROVISIONAL / DATA, CENTRAL AND CLIENT REFERENCES, NEURAL RUNTIME AND FEDERATED PILOT IMPLEMENTED'
    a['known_limitations']=list(dict.fromkeys(a['known_limitations']+['F1 has one seed and client Adam; no final FL selection','Simulation is not a privacy or network-isolation boundary']))
    project['progress'].update(checkpoint='CP9',status='COMPLETE',methodology_version='M0.9',current=[],blocked=[],
        next=['CP10: preregister FL challengers and confirmation seeds within the remaining EXP-004 budget'])
    project['progress']['completed']=list(dict.fromkeys(project['progress']['completed']+['F1 28 runs and 240 aggregations verified; single-seed collaboration outcomes recorded']))
    project['federated_pilot_result']={'verification_path':str(ROOT/'reports/cp9/verification.json'),
        'verification_sha256':sha(ROOT/'reports/cp9/verification.json'),'collaboration_signals':signals}
    write_json(project_path,project)
    research_path=ROOT/'docs/registries/research.json'; research=read(research_path)
    ref=next(s for s in research['sources'] if s['id']=='R006')
    ref['cp9_follow_up']='2026-09-10: author PDF objective section and Algorithm 1 re-read; F1 uses the weighted aggregation structure but changes local SGD to epoch-reset Adam; no new paper numerical result adopted.'
    write_json(research_path,research)
    for filename,paragraph in [('README.md',f'Current checkpoint: CP9 COMPLETE. F1 completes 28 seed-17 central/local/FedAvg run records; 36 tests and all 240 aggregation reconstructions pass. {signals}/12 scenarios meet the exploratory collaboration signal; final FL selection remains open. See [CP9 results](reports/CP9-federated-results.md), [verification](reports/CP9-checkpoint-verification.md), and [project status](docs/STATUS.md). Next: registered CP10 challengers and confirmation seeds. No DP, secure aggregation, CL or final/external model scores.'),
        ('docs/STATUS.md',f'Current checkpoint: CP9 COMPLETE. CP0 through CP8 remain complete. F1 verifies 28 seed-17 runs, 76 final models, 240 weighted aggregations and 36 tests. {signals}/12 scenarios meet the exploratory collaboration signal. EXP-004 remains open for method and seed comparisons. See [CP9 results](../reports/CP9-federated-results.md) and [verification](../reports/CP9-checkpoint-verification.md).')]:
        path=ROOT/filename; parts=path.read_text(encoding='utf-8').split('\n\n')
        i=next(i for i,x in enumerate(parts) if x.startswith('Current checkpoint:')); parts[i]=paragraph
        text='\n\n'.join(parts)
        if filename=='README.md': text=text.replace('contain 26 decisions','contain 28 decisions').replace('94 data/model run records','122 data/model run records')
        path.write_text(text,encoding='utf-8')
    status_path=ROOT/'docs/STATUS.md'; status=status_path.read_text(encoding='utf-8')
    status=status.replace('Methodology: M0.8 / N1 / S1','Methodology: M0.9 / F1 / N1 / S1')
    status=status.replace('data pipeline, centralized comparisons, logical-client ownership and tested Torch neural training implemented',
        'data pipeline, central/local references, client ownership, Torch training and a tested non-private federated pilot implemented')
    status=status.replace('DEC-024 through DEC-026 separate and resolve N1 migration correctness and pilot eligibility.',
        'DEC-024 through DEC-026 resolve N1 migration and pilot eligibility; DEC-027/DEC-028 record F1 controls and exploratory outcomes.')
    status=status.replace('EXP-004 has verified clients and a tested neural implementation, with zero FL model runs.',
        'F1 adds 28 run records, including 12 federated systems; EXP-004 remains open for challenger and seed comparisons.')
    old='Next action: CP9 preregisters matched centralized/local/FedAvg comparisons on identical C1 assignments, including objective weighting, optimizer-state handling and compute budgets.'
    new=(f'CP9 results: 28 seed-17 run records and all 240 federated aggregations verify; {signals}/12 scenarios meet the exploratory collaboration rule. '
         f'The four-hour model-worker budget has {v["four_hour_family_budget_remaining_seconds"]/3600:.3f} hours remaining. '
         'Results do not justify a uniformly beneficial or private federated system. See the CP9 report for pooled and worst-client comparisons.\n\n'
         'Next action: CP10 preregisters bounded FL challengers and confirmation seeds on C1, retaining F1 controls and cumulative family-budget accounting.')
    status=status.replace(old,new).replace('None for scoped CP9 non-private pilot preparation.','None for scoped CP10 non-private comparisons.')
    parts=status.split('\n\n')
    i=next(i for i,p in enumerate(parts) if p.startswith('Git milestone:'))
    parts[i]='Git milestone: Local branch codex/cp9-fedavg-pilot. F1 protocol and tested runner were committed in b367cf6 before all 28 workers. N1 source remains bound to de412e9 and C1/H1 to earlier checkpoint commits. Executed source, data, model, round and report hashes are verified; no push has been performed.'
    status_path.write_text('\n\n'.join(parts),encoding='utf-8')
    a_path=ROOT/'docs/architecture/A0.md'; architecture=a_path.read_text(encoding='utf-8')
    architecture=architecture.replace('Feature/model selection remains in progress, and FL/DP/CL algorithms remain unimplemented and unselected.',
        'Final feature/model/FL selection remains in progress. F1 implements a non-private federated pilot; DP and CL algorithms remain unimplemented.')
    note=(f'CP9 implementation note (2026-09-10): F1 completes 28 single-seed run records with matched example exposure and fresh central/local controls. '
          f'All 240 parameter averages and final predictions verify; {signals}/12 scenarios meet the exploratory collaboration signal. '
          'FedAvg with client Adam remains a comparison reference, not a final winner. Strong heterogeneity can produce pooled and client regressions; '
          'local-update drift is a CP10 hypothesis requiring controlled challengers and seed checks. The simulator, shared preprocessing and stored updates '
          'provide no DP, secure-aggregation or deployment-isolation guarantee. See [F1 evidence](../../reports/CP9-federated-results.md) and DEC-027/DEC-028.')
    marker='## Objective and boundary\n\n'
    if 'CP9 implementation note' not in architecture: architecture=architecture.replace(marker,marker+note+'\n\n')
    a_path.write_text(architecture,encoding='utf-8')
    print(f'CP9 complete: 28 runs, 240 verified aggregations, {signals}/12 exploratory signals',flush=True)


if __name__=='__main__': main()
