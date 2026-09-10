"""Publish only verified N1 evidence and the predeclared eligibility decisions."""
import json
from pathlib import Path
from audit_datasets import write_json
from preprocess_p1 import sha
from run_baseline_pilot import ROOT


def read(path): return json.loads(Path(path).read_text())


def main():
    v = read(ROOT/'reports/cp8/verification.json')
    assert v['status'] == 'PASSED' and v['script_sha256'] == sha(ROOT/'scripts/verify_cp8.py')
    assert sha(v['selection']['path']) == v['selection']['sha256']
    for b in v['report_bindings']: assert sha(b['path']) == b['sha256']
    s = read(v['selection']['path']); runs = [read(b['path']) for b in v['report_bindings']]
    migrations = [r for r in runs if r['stage'] == 'migration']; training = [r for r in runs if r['stage'] == 'train']
    assert len(migrations) == 4 and len(training) == 24 and all(r['status'] == 'COMPLETED' for r in runs)
    eligible = [scope for scope in s['scopes'] if scope['selected_candidate'] is not None]
    lines = ['# CP8 neural migration and stability results', '',
        'N1 / M0.8, 2026-09-10. CP8 is COMPLETE: four saved-model migration checks and all 24 registered fresh-training fits completed; all 32 tests and artifact/prediction verification pass. Eligibility is decided separately in each dataset/protocol namespace. This checkpoint establishes a tested neural implementation and bounded validation evidence, with no FL, privacy or CL result.', '',
        '## Runtime and migration', '',
        'PyTorch 2.10.0+cu128 runs with the bundled CUDA 12.8 runtime on the RTX 4050 Laptop GPU. The explicitly approved installation preserves all ten baseline dependency versions. CPU/GPU setup arithmetic passes; the environment inventory is pinned locally. [Setup evidence](CP8-runtime-setup.md).', '',
        '| Scope | CPU maximum probability error | CUDA maximum probability error | Changed CUDA decisions at 0.5 | Save/load maximum error |',
        '|---|---:|---:|---:|---:|']
    for r in migrations:
        lines.append(f'| {r["dataset"]} / {r["protocol"]} | {r["cpu_max_abs_delta"]:.6g} | {r["cuda_max_abs_delta"]:.6g} | {r["cuda_decision_disagreements"]} | {r["roundtrip_max_abs_delta"]:.6g} |')
    lines += ['', 'Each migration checks full corresponding validation against its saved B2-selected seed-17 MLP reference. CPU float64 errors are within 1e-12; CUDA float32 errors are within 1e-4 and changed-decision rates within 1e-4. The verifier reloads the saved Torch weights and reproduces every saved CPU/CUDA probability. These are representation checks, not new detection improvements.', '',
        'The three-step float64 optimizer fixture independently reconstructs BCE, weight-only L2 gradients and native Adam updates, including a two-row final batch. Extreme-logit BCE remains finite. Native Torch Adam differs from scikit in epsilon placement; no training-trajectory equivalence is claimed.', '',
        '## Fixed stability comparison', '',
        'Every fit uses the unchanged 100,000 S1 training representatives, B2-selected representation and full validation in its own scope. CIC uses P2 and 172 augmented fields; NF uses P1 and 98 fields. Hidden widths stay 64/32, with a single binary logit. Both learning rates receive 20 epochs, batch size 256 and seeds 17/29/43. Initialization and epoch-order streams are paired across learning-rate candidates. Shared development preprocessing remains non-private.', '',
        '| Scope | Learning rate | Macro-F1 mean ± sample SD | AP mean | N1 eligible |',
        '|---|---:|---:|---:|---|']
    for scope in s['scopes']:
        for c in scope['candidates']:
            lines.append(f'| {scope["dataset"]} / {scope["protocol"]} | {c["learning_rate"]:g} | {c["macro_f1_mean"]:.6f} ± {c["macro_f1_sample_sd"]:.6f} | {c["average_precision_mean"]:.6f} | {"Yes" if c["eligible"] else "No"} |')
    lines += ['', '| Scope | Historical B2 MLP macro-F1 mean ± SD | Selected N1 candidate |', '|---|---:|---|']
    for scope in s['scopes']:
        lines.append(f'| {scope["dataset"]} / {scope["protocol"]} | {scope["historical_b2_mlp_macro_f1_mean"]:.6f} ± {scope["historical_b2_mlp_macro_f1_sample_sd"]:.6f} | {scope["selected_candidate"] or "None: stability/quality unresolved"} |')
    lines += ['', f'{len(eligible)} of four namespaces have a candidate eligible for a later pilot. Eligibility requires three successful fits, sample SD <=0.01, and mean macro-F1/AP losses <=0.002 relative to that same namespace’s B2 selected MLP. Eligible candidates rank by mean macro-F1, mean AP, then lower learning rate. No additional candidates were introduced after scores. Any candidate that fails these gates remains reported, rather than being relabeled a failed execution.', '',
        'The historical B2 comparison changes framework, optimizer semantics and epoch budget together; differences cannot be attributed solely to Adam or GPU use. Three seeds reuse the same training and validation populations. Sample SD is conditional model randomness, not a population confidence interval or proof of robustness. Cross-scope results cannot select an earlier temporal protocol’s settings.', '',
        'The strongest B2 Extra Trees references remain in the detector comparison. A neural implementation that is eligible for FL experiments is not automatically the final best detector. NF host reuse and the unsupported H1 host-separated binary challenge remain limitations. Synthetic C1 clients must not be described as banks or independent hosts.', '',
        'Each run records standard binary and attack-family metrics at 0.5, the validation-fitted <=1% FPR operating point, probabilities, initial/final weights, losses and artifact hashes. Calibrated validation scores are tuning results; the threshold has not been confirmed on a held-out final test.', '',
        '## Resources and verification', '',
        f'The 24 fresh fits used {sum(r["fit_seconds"] for r in training):.3f} measured training seconds and {sum(r["supervised_wall_seconds"] for r in training):.3f} supervised worker seconds. Migration adds {sum(r["supervised_wall_seconds"] for r in migrations):.3f} supervised seconds. These totals exclude package download, prior preparation, tests and final verification.', '',
        f'Maximum sampled worker-tree RSS across all 28 workers was {max(r["sampled_peak_process_rss_bytes"] for r in runs)/2**30:.3f} GiB; maximum CUDA allocated/reserved memory was {max(r["cuda_peak_allocated_bytes"] for r in runs)/2**30:.3f} / {max(r["cuda_peak_reserved_bytes"] for r in runs)/2**30:.3f} GiB. Every worker stayed below the 600-second, 12-GiB process-tree and 4-GiB CUDA allocator limits. RSS sampling is every 0.5 seconds and excludes the supervising parent; CUDA counters cover the Torch allocator, not every driver allocation.', '',
        'The verifier checks report/source/model/probability hashes, reloads and reproduces all 28 runs’ full validation predictions, recomputes reported metrics and operating points, separately checks macro-F1 with sklearn, and confirms registered initialization and pairing across candidates. It applies the fixed selection rule without accessing final/private/public-reference/external data.', '',
        'Next: preregister CP9 central/local/FedAvg comparisons on identical C1 assignments, with explicit objective weighting and matched training budgets. Any scope without an eligible N1 candidate needs a separate recorded amendment before advancement. Model selection, FL, DP and CL remain provisional; final/external scores remain sealed.', '',
        'Evidence: [N1 protocol](../docs/CP8-neural-migration-protocol-N1.md), [selection and seed values](cp8/selection.json), [verification](cp8/verification.json), [32-test log](cp8/runtime-tests.log), [optimizer tests](cp8/optimizer-tests.log), [checkpoint checks](CP8-checkpoint-verification.md), [viva notes](../docs/CP8-viva.md).']
    (ROOT/'reports/CP8-neural-results.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    (ROOT/'reports/CP8-checkpoint-verification.md').write_text('''# CP8 checkpoint verification

- Runtime: pinned Torch CUDA build installed after explicit authorization; CPU/GPU arithmetic and autograd pass; baseline dependency versions preserved.
- Tests: 32 pass, including independent three-step native-Adam and partial-batch gradient checks.
- Migration: 4/4 full-validation CPU/CUDA/serialization gates pass; saved weights reproduce probabilities.
- Stability: 24/24 preregistered fits complete; 20 epochs each; no score-based budget extension.
- Reproduction: source/data/model hashes verified; saved predictions and metrics reproduced; initialization checked against the registered stream and across candidates.
- Selection: N1 practical eligibility thresholds applied independently per scope; full candidate/seed values preserved.
- Limits: all workers within registered wall time, sampled process-tree RSS and Torch allocator bounds.
- Scope: no final/external scores, private guarantee, CL training or FL run. Eligibility for a pilot is not a deployment claim.

Machine-readable evidence is in reports/cp8/verification.json and reports/cp8/selection.json. CP8 is complete as an executed bounded experiment, even where a candidate fails a scientific eligibility rule.
''', encoding='utf-8')
    (ROOT/'docs/CP8-viva.md').write_text('''# CP8 viva notes

**What did migration establish?** The saved selected MLPs can be represented in Torch with bounded CPU/CUDA prediction error and verified serialization. It does not establish identical learning trajectories.

**Why can matching Adam parameters still behave differently?** The implementations place epsilon on different sides of second-moment bias correction. N1 explicitly tests native Torch updates and treats fresh training as a controlled new experiment.

**What is the regularization objective?** Mean binary cross-entropy with logits plus half alpha times squared weights divided by the actual minibatch size. Biases are excluded; Adam weight_decay is zero to avoid double-counting.

**How is stability defined?** Three fixed seeds, sample macro-F1 SD <=0.01 and mean macro-F1/AP degradation <=0.002 against the same scope’s B2 MLP. These are practical preregistered gates, not statistical significance tests.

**Can improvements be credited to the new optimizer?** No. Framework, optimizer semantics and epoch budget change together against B2. Only the two N1 learning rates have paired initialization, shuffle streams and equal epoch budgets.

**Why keep Extra Trees?** Neural pilot eligibility does not prove it is the strongest detector. The classical reference remains part of final comparative evidence.

**What remains unproven?** Host-independent and institutional generalization, FL benefits, privacy accounting, continual-learning retention and held-out final performance. The financial setting remains a deployment scenario using general IDS benchmarks.

See reports/CP8-neural-results.md for measured numbers and the exact per-scope decisions. CP9 must define equal-data central/local/federated comparisons and budget/objective weights before scores.
''', encoding='utf-8')
    project_path = ROOT/'docs/registries/project.json'; project = read(project_path)
    for r in runs:
        entry = dict(r, date='2026-09-10', hardware='RTX 4050 Laptop GPU; reports/cp8/runtime-installation.json',
                     model='MLP 64/32 binary logits' if r['stage'] == 'train' else 'Saved MLP prediction migration',
                     environment_versions=r['environment'])
        project['runs'] = [old for old in project['runs'] if old['run_id'] != r['run_id']]+[entry]
    decisions = [('DEC-025','Does the Torch implementation meet N1 numerical gates?',
                  'Accept tested N1 prediction and native-Adam implementation for non-private development',
                  'Four migration gates and independent optimizer/loss/gradient tests pass'),
                 ('DEC-026','Which N1 candidates qualify for the next pilot?',
                  '; '.join(f'{x["dataset"]}/{x["protocol"]}: {x["selected_candidate"] or "unresolved"}' for x in s['scopes']),
                  'Apply preregistered SD/quality floors then mean macro-F1/AP/lower-LR ranking separately per namespace')]
    for did, question, choice, why in decisions:
        if not any(d['decision_id'] == did for d in project['decisions']):
            project['decisions'].append({'decision_id': did, 'question': question, 'selected_option': choice, 'why_selected': why,
                'candidate_alternatives': ['Assume migration from package installation alone', 'Extend tuning after seeing scores', choice],
                'evidence_considered': ['docs/CP8-neural-migration-protocol-N1.md','reports/CP8-neural-results.md','reports/cp8/selection.json'],
                'experiments_used': ['EXP-003'], 'rejected_alternatives': ['Unverified optimizer equivalence','Post-score candidate additions'],
                'why_rejected': 'No supporting controlled evidence or preregistration',
                'risks': ['Validation reuse','Three-seed uncertainty','NF host overlap','Historical framework/budget confounding'],
                'trade_offs': ['Neural pilot readiness does not establish best detector or deployment quality'],
                'confidence': 'High for reproduction; conditional for validation ranking', 'architecture_version': 'A0',
                'revisit_condition': 'Registered C1 FL evidence, new approved amendment or final evaluation'})
    e3 = next(e for e in project['experiments'] if e['experiment_id'] == 'EXP-003')
    e3.update(result='N1 four migration gates and 24 stability fits verified; per-scope pilot eligibility recorded',
              decision=decisions[1][2], interpretation='Bounded reused-validation evidence; final detector and held-out evaluation remain open')
    e3['artifacts'] = list(dict.fromkeys(e3['artifacts']+['reports/CP8-neural-results.md','reports/cp8/selection.json','reports/cp8/verification.json']))
    e4 = next(e for e in project['experiments'] if e['experiment_id'] == 'EXP-004')
    e4.update(phase='CLIENT_CONTRACTS_AND_NEURAL_IMPLEMENTATION_READY; FL_TRIALS_NOT_STARTED',
              decision='Preregister matched central/local/FedAvg budgets for N1-eligible scopes on C1')
    a = next(a for a in project['architectures'] if a['version'] == 'A0')
    a['components'] = list(dict.fromkeys(a['components']+['N1 verified Torch MLP and native-Adam development runner']))
    a['supporting_decisions'] = list(dict.fromkeys(a['supporting_decisions']+['DEC-024','DEC-025','DEC-026']))
    a['status'] = 'PROVISIONAL / DATA, CENTRALIZED COMPARISONS, CLIENT OWNERSHIP AND NEURAL RUNTIME IMPLEMENTED'
    project['progress'].update(checkpoint='CP8', status='COMPLETE', current=[], blocked=[], methodology_version='M0.8',
        next=['CP9: preregister comparable central/local/FedAvg pilots on fixed C1 manifests for eligible N1 scopes'],
        needs_validation=['FL method comparison on C1','Private preprocessing, allocation and DP accounting',
                          'CL-specific clients/tasks and forgetting comparisons','Final detector choice and final/external evaluation after freeze'])
    project['progress']['completed'] = list(dict.fromkeys(project['progress']['completed']+['N1 four Torch migration gates and 24 native-Adam stability fits verified']))
    project['neural_migration_result'] = {'verification_path': str(ROOT/'reports/cp8/verification.json'),
        'verification_sha256': sha(ROOT/'reports/cp8/verification.json'), 'eligible_scopes': len(eligible)}
    write_json(project_path, project)
    for filename, text in [('README.md', f'Current checkpoint: CP8 COMPLETE. All four Torch CPU/CUDA migration checks, 24 registered stability fits and 32 tests pass. {len(eligible)}/4 namespaces have an N1 candidate eligible for the next pilot. See [CP8 results](reports/CP8-neural-results.md), [verification](reports/CP8-checkpoint-verification.md), and [project status](docs/STATUS.md). Next is CP9: matched central/local/FedAvg comparisons on fixed C1 clients. Model/FL/privacy/CL choices remain provisional; final/external scores remain sealed.'),
                           ('docs/STATUS.md', f'Current checkpoint: CP8 COMPLETE. CP0 through CP7 remain complete. N1 verifies four Torch CPU/CUDA migration gates and 24 fresh stability fits; all 32 tests pass. {len(eligible)}/4 namespaces have eligible pilot candidates. The approved PyTorch installation and subsequent continuation are complete. See [CP8 results](../reports/CP8-neural-results.md) and [verification](../reports/CP8-checkpoint-verification.md). EXP-003 remains open for final detector choice; EXP-004 has no FL trials yet.')]:
        path = ROOT/filename; paragraphs = path.read_text(encoding='utf-8').split('\n\n')
        i = next(i for i,p in enumerate(paragraphs) if p.startswith('Current checkpoint:'))
        paragraphs[i] = text; new = '\n\n'.join(paragraphs)
        if filename == 'README.md': new = new.replace('contain 24 decisions','contain 26 decisions').replace('66 data/model run records','94 data/model run records')
        path.write_text(new, encoding='utf-8')
    print('CP8 complete: 4 migrations, 24 fresh fits; eligible scopes:', len(eligible), flush=True)


if __name__ == '__main__': main()
