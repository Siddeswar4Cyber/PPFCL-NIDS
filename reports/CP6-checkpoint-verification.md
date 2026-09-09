# CP6 checkpoint verification

2026-09-09. B2 / M0.6 is COMPLETE for its registered finite comparisons and diagnostics. EXP-003 remains RUNNING for unresolved split/generalization controls and final model selection.

| Check | Result |
|---|---|
| Preregistration | Protocol commit 6734173 precedes feature ranking and B2 scores |
| Training-only feature definitions | Rankings and category frequencies independently recomputed from each saved training matrix |
| Reduced-feature boundary | Eight dataset/protocol/reduction combinations rejected for cross-role vector merges; zero reduced-model scores |
| Valid comparison population | All candidates use unchanged CIC P2 / NF P1 rows, training representatives and validation order |
| New fits | 12 categorical-augmentation seed-17 fits and 24 selected-representation fits at seeds 29/43; all completed |
| Existing controls | 12 B1 trained-model seed-17 runs reused once; not counted as new replicates |
| Selection | Registered macro-F1 margin and AP guard reproduced; candidate report hashes remain bound to frozen selection |
| Model verification | Saved probability metrics, input/model/transform hashes and executed Git-source hashes pass |
| Diagnostics | Eight model permutation reports and two NF host-overlap scopes; saved probability/subgroup metrics reproduced |
| Resource ceilings | Every retained B2 worker below 600 seconds and 12 GiB sampled process-tree RSS |
| Integration tests | All 20 tests pass in 23.118 seconds |
| Evaluation boundary | No final/external model scores exposed; no private/public-reference performance evaluated |

The new fits total 87.970 fit seconds and 225.284 supervised seconds, with sampled maximum worker-tree RSS of 2.548 GiB. These totals exclude gate construction, diagnostics, verification and the historical B1 controls. Memory sampling is not a continuous exact peak. The categorical-augmentation comparison changes input width; all estimator hyperparameters are otherwise unchanged.

The unseen NF endpoint-pair subsets are benign-only. Their false-positive rates can be reported, but their attack recall/AP cannot be estimated. Fixed two-label macro-F1 in raw subgroup records follows B1's zero-division policy; it must not be treated as directly comparable two-class detection quality. Permutation interventions can make unrealistic feature combinations, and three model seeds do not provide population confidence intervals.

## Evidence and reproduction

- [Results and decisions](CP6-comparison-results.md)
- [Machine-readable verification](cp6/verification.json)
- [Three-seed summary and per-family recall](cp6/seed-summary.json)
- [Frozen representation selection](cp6/selection.json)
- [NF host overlap](cp6/diagnostics/NF-host-overlap.json)
- [Protocol](../docs/CP6-comparison-protocol-B2.md)
- [Test log](cp6-tests.log)
- [Metric verification log](cp6-verification.log)

From the project root with existing local artifacts:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe scripts\finalize_cp6.py
```

The finalizer checks saved outputs and refreshes derived report/registry entries without fitting models or exposing holdouts. `cp6_features.py`, `run_cp6.py` and `cp6_diagnostics.py` contain the registered execution stages. Feature/diagnostic outputs refuse overwrite. The runner can skip verified completed jobs, but rejects incomplete or changed existing jobs; a fresh study requires new versioned outputs. Retain original logs and artifacts when investigating any failure. Models, matrices, host masks and saved probabilities are local, Git-ignored artifacts; a source-only checkout is insufficient for score reproduction.

Git attributes preserve the exact bytes of B1 run reports and B2 JSON reports, because feature specifications, selection and verification bind their SHA-256 hashes. These files must not acquire automatic line-ending changes on checkout. The checkpoint validates staged bytes against the frozen bindings.

The next checkpoint assesses host-aware split feasibility and client design. Neural implementation migration, optimization stability, private preprocessing, FL/CL comparisons and final generalization remain outstanding.
