"""Record verified N1 preparation, explicitly leaving framework/training gates open."""
import json
from pathlib import Path
from audit_datasets import write_json
from preprocess_p1 import sha
from run_baseline_pilot import ROOT


def read(path): return json.loads(Path(path).read_text())


def main():
    path = ROOT/'reports/cp8/preparation.json'; r = read(path)
    assert r['status'] == 'PREPARATION_PASSED_RUNTIME_PENDING' and r['exit_code'] == 0
    assert not r['checkpoint_complete'] and not r['torch_executed'] and r['new_model_fits'] == 0
    assert len(r['checks']) == 4 and r['resource_limit_stop'] is None
    for b in r['bindings'] + [b for c in r['checks'] for b in c['bindings']]:
        assert sha(b['path']) == b['sha256'], b['path']
    assert {(c['dataset'], c['protocol']) for c in r['checks']} == {
        (d, p) for d in ['cic-ids-2017', 'ND-UNSW-NB15-v3'] for p in ['primary', 'stress']}
    for c in r['checks']:
        assert c['status'] == 'PASSED' and c['max_abs_delta'] <= 1e-12
    test_path = ROOT/'reports/cp8-tests.log'; tests = test_path.read_text(encoding='utf-8')
    assert 'Ran 29 tests' in tests and tests.strip().endswith('OK')
    lines = ['# CP8 preparation: artifact checks pass; runtime pending', '',
             '2026-09-10. N1 / M0.8. CP8 remains IN PROGRESS. Four saved selected seed-17 MLPs pass independent NumPy reconstruction over all corresponding validation rows. PyTorch is not installed or executed, and no new model fit, FL run or private/CL result is recorded.', '',
             '| Dataset / scope | Inputs | Validation rows | Maximum probability difference | Changed decisions at 0.5 |',
             '|---|---:|---:|---:|---:|']
    for c in r['checks']:
        lines.append(f'| {c["dataset"]} / {c["protocol"]} | {c["width"]} | {c["rows"]:,} | {c["max_abs_delta"]:.6g} | {c["decision_disagreements_05"]} |')
    lines += ['', f'Total checked: {sum(c["rows"] for c in r["checks"]):,} predictions across separate, reused validation namespaces. These are not independent evaluation samples or fresh detection scores. Maximum error is below the preregistered 1e-12 tolerance in every scope. Artifact SHA bindings pass. All 29 existing and new tests pass; the three new tests exercise explicit affine/ReLU/sigmoid arithmetic, orientation/bias handling, a partial prediction batch and invalid inputs. They do not test Torch.', '',
              f'The preflight worker took {r["elapsed_seconds"]:.3f} seconds; supervised time was {r["supervised_wall_seconds"]:.3f} seconds. Peak sampled worker-tree RSS was {r["sampled_peak_process_rss_bytes"]/2**30:.3f} GiB (0.5-second sampling), below 12 GiB. No GPU allocation measurement exists.', '',
              '## Prepared implementation and experiment', '',
              'The prediction helper contains a lazy-import Torch converter that transposes weights into three Linear layers and returns logits. Its Torch path remains unexecuted. The committed protocol fixes CPU/CUDA prediction tolerances, save/load checks, native Adam gradient/update checks and a 24-fit stability budget: two learning rates, three seeds and four separate namespaces, each for 20 epochs. Training implementation and runtime validation are still outstanding. No best learning rate or neural stability claim is made.', '',
              'The native Adam formula places epsilon after second-moment bias correction, whereas the installed scikit implementation places epsilon before that correction. Consequently the protocol treats fresh Torch training as a new controlled experiment, not an exact continuation of the scikit optimizer. [PyTorch 2.10 Adam algorithm](https://docs.pytorch.org/docs/2.10/generated/torch.optim.Adam.html).', '',
              '## Blocking action and exact resumption', '',
              'Automatic approval review rejected the package installation before execution: it interpreted the original no-download instruction as requiring explicit later authorization for PyTorch. The requested action is to download torch==2.10.0 and its required dependencies from the official CUDA 12.8 package index and install them into this project’s .venv. This adds executable packages, uses download bandwidth and disk space, and modifies the project environment. No dataset or GPU driver download is proposed. No alternate installation was attempted.', '',
              'After explicit approval, use: `uv pip install --python .venv/Scripts/python.exe torch==2.10.0 --index-url https://download.pytorch.org/whl/cu128`. Capture exact resolved dependencies and verify CUDA on the actual RTX 4050 before executing N1. The [official wheel matrix](https://pytorch.org/get-started/previous-versions/) lists this Windows installation target; compatibility has not yet been established locally.', '',
              'Run CPU/CUDA migration and serialization checks, implement and test optimizer/gradient semantics, commit the training runner before new scores, execute the registered fits, independently recompute metrics, then update checkpoint and architecture decisions. CP9 FL pilots remain gated on that review.', '',
              'Evidence: [N1 protocol](../docs/CP8-neural-migration-protocol-N1.md), [machine-readable preparation](cp8/preparation.json), [preflight log](cp8/preparation.log), [test log](cp8-tests.log). Preregistration/code commit: '+r['git_commit']+'.']
    (ROOT/'reports/CP8-preparation-status.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    verification = {'status': 'PREPARATION_VERIFIED_RUNTIME_PENDING', 'checkpoint_complete': False,
                    'script_sha256': sha(__file__), 'preparation': {'path': str(path), 'sha256': sha(path)},
                    'test_log': {'path': str(test_path), 'sha256': sha(test_path)}, 'tests_passed': 29,
                    'numpy_prediction_gates_passed': 4, 'torch_gates_executed': 0, 'new_model_fits': 0}
    write_json(ROOT/'reports/cp8/preparation-verification.json', verification)
    project_path = ROOT/'docs/registries/project.json'; project = read(project_path)
    project['updated'] = '2026-09-10'
    project['progress'].update(checkpoint='CP8', status='IN_PROGRESS_AWAITING_PACKAGE_APPROVAL', methodology_version='M0.8',
        current=['N1 protocol and local prediction-layout preparation complete; CPU/CUDA migration and fresh training unexecuted'],
        next=['Approve pinned PyTorch package download', 'Verify N1 CPU/CUDA/optimizer gates and execute the fixed stability comparison',
              'Preregister comparable central/local/FL pilots on C1'],
        blocked=['Automatic approval review rejected PyTorch installation; explicit download authorization required'])
    completed = 'N1 four saved-model NumPy prediction-layout checks'
    if completed not in project['progress']['completed']: project['progress']['completed'].append(completed)
    project['neural_migration_preparation'] = verification
    e3 = next(e for e in project['experiments'] if e['experiment_id'] == 'EXP-003')
    e3['decision'] = 'N1 preparation passes; defer Torch and training conclusions until runtime gates and registered stability fits'
    e3['artifacts'] = list(dict.fromkeys(e3['artifacts']+['docs/CP8-neural-migration-protocol-N1.md', 'reports/CP8-preparation-status.md']))
    if not any(d['decision_id'] == 'DEC-024' for d in project['decisions']):
        project['decisions'].append({'decision_id': 'DEC-024', 'question': 'What constitutes a supported neural migration?',
            'candidate_alternatives': ['Assume optimizer equivalence from matching parameter names', 'Separate prediction equivalence and controlled fresh training'],
            'evidence_considered': ['docs/CP8-neural-migration-protocol-N1.md', 'reports/CP8-preparation-status.md', 'R061'],
            'experiments_used': ['EXP-003'], 'selected_option': 'Separate prediction/serialization gates and native-Adam stability trials',
            'why_selected': 'Scikit and Torch Adam epsilon placement differs; CIC seed sensitivity is unresolved',
            'rejected_alternatives': ['Treat NumPy reconstruction as a successful Torch migration'],
            'why_rejected': 'Torch has not executed locally', 'risks': ['Validation reuse', 'Three-seed uncertainty', 'Runtime compatibility pending'],
            'trade_offs': ['24 bounded fresh fits before FL pilot decisions'], 'confidence': 'Preparation verified; runtime and model conclusions pending',
            'architecture_version': 'A0', 'revisit_condition': 'Executed N1 gates and stability evidence'})
    write_json(project_path, project)
    research_path = ROOT/'docs/registries/research.json'; research = read(research_path)
    references = [('R060', 'PyTorch previous versions: 2.10.0 Windows wheel matrix', 'https://pytorch.org/get-started/previous-versions/',
                   'Official installation matrix lists CUDA 12.8 wheels for the pinned PyTorch 2.10.0 release.', 'Version 2.10.0 Windows wheel commands inspected'),
                  ('R061', 'PyTorch 2.10 Adam API and update algorithm', 'https://docs.pytorch.org/docs/2.10/generated/torch.optim.Adam.html',
                   'Adam adds epsilon after second-moment bias correction; implementation options affect execution.', 'Algorithm and optimizer parameter sections read')]
    for ident, title, url, conclusion, depth in references:
        if any(s['id'] == ident for s in research['sources']): continue
        item = {k: 'N/A' for k in research['sources'][-1]}
        item.update(id=ident, title=title, authors_organization='PyTorch contributors', year='Documentation accessed 2026',
            venue='Official versioned API / installation documentation', url_doi=url, problem='Neural runtime migration', model='PyTorch MLP / Adam',
            main_conclusion=conclusion, limitations='Local compatibility and numerical behavior require runtime tests; no detection result adopted',
            relevance_to_project='CP8 N1 migration and stability', evidence_category='LITERATURE EVIDENCE', accessed='2026-09-10',
            verification_depth=depth, follow_up='Install only after approval; execute N1 runtime gates', numeric_locator='No numerical detection result adopted')
        research['sources'].append(item)
    research['date'] = '2026-09-10'; write_json(research_path, research)
    print('Preparation verified and recorded; CP8 remains in progress', flush=True)


if __name__ == '__main__': main()
