# CP5 checkpoint verification

2026-09-09. Status: COMPLETE for the B1 CPU feasibility pilot. EXP-003 remains RUNNING for feature/model selection and confirmation. Configuration and P2 preprocessing were preregistered in local commit `3d31e90` before the first model fit.

| Check | Evidence and result |
|---|---|
| CIC precision amendment | P1 float32 gate failed; P2 excludes 45,645 implicated groups / 119,119 rows, then both equality gates pass |
| P2 input integrity | Original roles, labels and clean feature values preserved; fit membership, recomputed parameters and exported vectors verified |
| Candidate comparison populations | Exactly 100,000 permitted training representatives per namespace; all four models share its transform and validation population |
| Completed runs | 16: four models times two datasets times two protocols |
| Reproduction from saved outputs | All recorded metric dictionaries reproduced from saved validation probabilities; input/model/transform hashes verified |
| Operating threshold | Every calibrated validation confusion matrix satisfies its integer 1% benign-FPR budget |
| Resource budgets | All retained workers below 600 seconds and 12 GiB sampled process-tree RSS |
| Integration tests | All 16 passed in 19.923 seconds, including five baseline tests |
| Evaluation boundary | No final-test or external predictions produced by B1; private-training/public-reference performance not evaluated |

The retained workers total 20.285 fit seconds and 67.429 supervised seconds. Preparation, verification and the preserved initial attempts are additional time; these numbers are not total checkpoint elapsed time. Memory figures are sampled process-tree RSS, not an exact continuous peak. Prediction latency measures warmed 4,096-row batches, not end-to-end flow processing.

The initial reporting and launcher-only RSS failures are retained under `baselines/initial-attempt`. Retained runs were rerun with unchanged scientific settings after the infrastructure fixes. All initial attempts are excluded from reported tables and confirmation counts. Run records bind the executed script bytes; their completed-checkpoint Git field points to the later local source/results commit, while the earlier configuration preregistration remains separately identified.

## Evidence

- [Results and interpretation](CP5-baseline-results.md)
- [B1 protocol](../docs/CP5-baseline-protocol-B1.md)
- [Saved-metric verification](baselines/verification.json)
- [P2 preprocessing verification](preprocessing/P2-verification.json)
- [CIC P2 population and fit report](preprocessing/cic-ids-2017-P2.json)
- [Full test log](baseline-tests-B1.log)
- [Training console](baseline-console-B1.log)
- [Verification console](baseline-verification-B1.log)
- [Dependency versions](../requirements-baseline.txt)

## Reproduction commands

From the project root, with the existing local artifacts:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe scripts\verify_cic_p2.py
.venv\Scripts\python.exe scripts\finalize_cp5.py
```

The final command verifies saved probabilities and refreshes the results and registry; it does not retrain models. The training entry point is `scripts/run_baseline_pilot.py`; it refuses to overwrite existing reports. Preserve completed artifacts and establish a new versioned experiment before deliberately retraining. Raw data, matrices and models are local artifacts excluded from Git, so a source-only checkout cannot reproduce scores without them.

## Limits and next checkpoint

Only one seed and setting per model were tested. CIC P2 changes the population from P1; every comparison here uses a common population within its namespace. Stress-validation results do not expose the sealed Friday/final-time test. Numeric nominal encodings, capture/host dependence, rare attack support and changing-feature overlap remain unresolved. CP6 addresses those controls and repeat seeds before final selection and FL integration. Existing development preprocessing provides no differential-privacy guarantee.
