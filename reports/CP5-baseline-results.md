# CP5 CPU baseline pilot results

B1 / M0.5, 2026-09-09. These are selection-validation results, not final-test or external-domain scores. All 16 fixed-budget runs completed and their saved probabilities reproduce the recorded metrics. Each model trained on the exact 100,000 representatives for its namespace.

## Data amendment before the first model fit

P1's CIC float32 conversion merged 22,813 vectors and implicated 45,645 S1 groups. P2 conservatively excludes all 119,119 associated rows, preserves S1 roles, refits preprocessing, and passes both precision gates. All CIC candidates below use P2; NF uses P1. P1's earlier data counts and raw-dataset literature scores are not directly comparable with this population.

| CIC class | P2 precision-excluded rows |
|---|---:|
| benign | 118,995 |
| dos_goldeneye | 8 |
| dos_hulk | 93 |
| dos_slowloris | 23 |

## Validation comparisons

AP denotes average precision. Macro-F1, attack F1 and FPR below use threshold 0.5. Recall@1% uses a separately validation-calibrated threshold; its empirical FPR is at most 1%, not necessarily exactly 1%. No confidence interval or seed-averaged ranking is claimed.

### cic-ids-2017 / primary

Validation rows: 533,069. Attack prevalence: 19.4189%.

| Model | Macro-F1 | Attack F1 | AP | FPR | Recall@1% | Fit seconds | Model KiB | RSS GiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prior | 0.446232 | 0.000000 | 0.194189 | 0.000000 | 0.000000 | 0.003 | 0.4 | 1.162 |
| logistic | 0.873441 | 0.792467 | 0.915000 | 0.028888 | 0.544727 | 0.824 | 1.1 | 1.180 |
| extra_trees | 0.974765 | 0.958972 | 0.990832 | 0.000701 | 0.959282 | 2.501 | 1197.2 | 0.997 |
| mlp | 0.947913 | 0.915860 | 0.978456 | 0.017763 | 0.833060 | 2.859 | 374.1 | 1.308 |

Highest observed macro-F1 in this fixed pilot: extra_trees. This is a provisional ranking for this namespace only. Stress rows are the stress protocol's permitted validation population, not its sealed held-out Friday/final-time test.

### cic-ids-2017 / stress

Validation rows: 391,594. Attack prevalence: 11.6937%.

| Model | Macro-F1 | Attack F1 | AP | FPR | Recall@1% | Fit seconds | Model KiB | RSS GiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prior | 0.468950 | 0.000000 | 0.116937 | 0.000000 | 0.000000 | 0.003 | 0.4 | 0.937 |
| logistic | 0.914685 | 0.846956 | 0.948449 | 0.002157 | 0.796165 | 0.524 | 1.1 | 0.999 |
| extra_trees | 0.953149 | 0.916424 | 0.990922 | 0.000191 | 0.971654 | 2.652 | 939.7 | 0.936 |
| mlp | 0.956057 | 0.921712 | 0.986287 | 0.000928 | 0.947502 | 2.800 | 374.3 | 1.146 |

Highest observed macro-F1 in this fixed pilot: mlp. This is a provisional ranking for this namespace only. Stress rows are the stress protocol's permitted validation population, not its sealed held-out Friday/final-time test.

### ND-UNSW-NB15-v3 / primary

Validation rows: 472,509. Attack prevalence: 5.2439%.

| Model | Macro-F1 | Attack F1 | AP | FPR | Recall@1% | Fit seconds | Model KiB | RSS GiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prior | 0.486537 | 0.000000 | 0.052439 | 0.000000 | 0.000000 | 0.003 | 0.4 | 0.800 |
| logistic | 0.995222 | 0.990942 | 0.997221 | 0.000143 | 0.998426 | 0.181 | 1.0 | 0.815 |
| extra_trees | 0.999297 | 0.998669 | 0.999995 | 0.000094 | 1.000000 | 1.426 | 236.4 | 0.608 |
| mlp | 0.999031 | 0.998164 | 0.999354 | 0.000112 | 0.999516 | 2.402 | 261.1 | 0.847 |

Highest observed macro-F1 in this fixed pilot: extra_trees. This is a provisional ranking for this namespace only. Stress rows are the stress protocol's permitted validation population, not its sealed held-out Friday/final-time test.

### ND-UNSW-NB15-v3 / stress

Validation rows: 82,067. Attack prevalence: 9.3911%.

| Model | Macro-F1 | Attack F1 | AP | FPR | Recall@1% | Fit seconds | Model KiB | RSS GiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prior | 0.475366 | 0.000000 | 0.093911 | 0.000000 | 0.000000 | 0.003 | 0.4 | 0.402 |
| logistic | 0.993423 | 0.988069 | 0.998713 | 0.000148 | 0.999221 | 0.177 | 1.0 | 0.402 |
| extra_trees | 0.999463 | 0.999027 | 0.999996 | 0.000094 | 1.000000 | 1.503 | 198.5 | 0.372 |
| mlp | 0.999212 | 0.998573 | 0.999009 | 0.000148 | 0.999870 | 2.422 | 261.4 | 0.453 |

Highest observed macro-F1 in this fixed pilot: extra_trees. This is a provisional ranking for this namespace only. Stress rows are the stress protocol's permitted validation population, not its sealed held-out Friday/final-time test.

## Interpretation and next comparisons

The dummy baseline demonstrates why high accuracy under class imbalance is insufficient: it detects no attacks. Trained candidates improve substantially, but the very high NF validation scores require scrutiny of capture/host dependence and shortcut features. Input hashes, label-column exclusion and exact group separation pass; these checks do not prove independent real-world events or causal attack learning.

Retain the strongest classical candidates as baselines and the compact MLP as an integration candidate. No final detector, FL method, privacy budget or continual-learning method is selected. Numeric protocol/port encoding, feature ablations, training-only feature selection and repeat seeds remain EXP-003 work. Any feature reduction or dtype change requires a renewed overlap gate and a common population for compared methods.

Only one setting and seed 17 were tested per model. MLP uses the final bounded epoch, without automatic validation splitting or best-epoch selection. Convergence warnings and actual iterations are retained below. Near-perfect NF results are source-corpus evidence only; external data and final tests remain sealed.

## Convergence and cost details

| Run | Iterations/epochs | Warnings | Prediction seconds | Warm batch p50/p95 ms |
|---|---|---|---:|---|
| B1-cic-ids-2017-primary-prior-s17 | [] | none | 0.009 | 0.131 / 0.177 |
| B1-cic-ids-2017-primary-logistic-s17 | [76] | none | 0.066 | 0.428 / 0.612 |
| B1-cic-ids-2017-primary-extra_trees-s17 | [] | none | 0.655 | 13.240 / 13.812 |
| B1-cic-ids-2017-primary-mlp-s17 | 10 | ConvergenceWarning | 0.349 | 2.424 / 2.784 |
| B1-cic-ids-2017-stress-prior-s17 | [] | none | 0.006 | 0.136 / 0.171 |
| B1-cic-ids-2017-stress-logistic-s17 | [45] | none | 0.054 | 0.497 / 0.554 |
| B1-cic-ids-2017-stress-extra_trees-s17 | [] | none | 0.484 | 12.966 / 13.277 |
| B1-cic-ids-2017-stress-mlp-s17 | 10 | ConvergenceWarning | 0.261 | 2.309 / 2.681 |
| B1-ND-UNSW-NB15-v3-primary-prior-s17 | [] | none | 0.007 | 0.125 / 0.176 |
| B1-ND-UNSW-NB15-v3-primary-logistic-s17 | [20] | none | 0.042 | 0.253 / 0.370 |
| B1-ND-UNSW-NB15-v3-primary-extra_trees-s17 | [] | none | 0.414 | 12.785 / 12.928 |
| B1-ND-UNSW-NB15-v3-primary-mlp-s17 | 10 | ConvergenceWarning | 0.239 | 2.128 / 2.231 |
| B1-ND-UNSW-NB15-v3-stress-prior-s17 | [] | none | 0.001 | 0.139 / 0.175 |
| B1-ND-UNSW-NB15-v3-stress-logistic-s17 | [21] | none | 0.008 | 0.247 / 0.384 |
| B1-ND-UNSW-NB15-v3-stress-extra_trees-s17 | [] | none | 0.077 | 13.005 / 13.209 |
| B1-ND-UNSW-NB15-v3-stress-mlp-s17 | 10 | ConvergenceWarning | 0.046 | 2.097 / 2.419 |

Latencies are warmed 4,096-row prediction batches (seven repetitions), not per-flow end-to-end detection delay. Model bytes are compressed joblib artifacts. RSS is the sampled sum over the worker process tree, including the Windows launcher; it is not a GPU measurement.

The first tree worker exposed a NumPy-integer JSON serialization bug. The initial supervisor also sampled only the Windows launcher. Those attempts are retained under reports/baselines/initial-attempt and models/B1-initial-attempt, with actual worker RSS marked unavailable. After fixing serialization and process-tree monitoring, all configurations were rerun unchanged. Initial attempts are not independent confirmation seeds and are not pooled into the tables.

The source/configuration and P2 gate were preregistered in local commit 3d31e90 before the first model fit. Exact current code, data, transform, model and probability hashes are recorded per run. See [verification](baselines/verification.json) and [protocol](../docs/CP5-baseline-protocol-B1.md).
