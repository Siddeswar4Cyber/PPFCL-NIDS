# CP5 baseline pilot B1

2026-09-09. M0.5 extends M0.4 before the first model score. This checkpoint implements a metric/model framework and bounded feasibility comparisons; it does not complete EXP-003's feature/model selection or confirmation seeds.

## Precision amendment P2

The pre-score tree-input gate found 22,813 CIC vectors merging after float32 conversion, involving 45,645 S1 groups; 16,892 merged vectors crossed primary roles. Both primary and stress P1 transforms have this issue. NF-UNSW passes. Scikit-learn Extra Trees converts input to float32, so its input boundary cannot be assumed identical to P1's float64 boundary.

P2 excludes the union of every implicated CIC S1 group, including same-role collisions, from every candidate's eligible population. It preserves all source rows and S1 role assignments in a ledger, with a precision-exclusion flag. It refits each permitted 100,000-representative pilot sample and its medians/scales, then rechecks binary64 and float32 equality on every admitted representative. Training starts only if both gates pass. No model performance influenced these exclusions. All CIC candidates use P2; all NF candidates use P1. Comparisons across different populations must be labeled, and P1 remains historical.

## Fixed pilot configurations

Four independent namespaces: CIC primary, CIC Friday stress, NF primary, NF chronological stress. Each uses its own preprocessing and exactly its saved 100,000 training representatives, plus all eligible validation rows. No final, external, private-training or public-reference performance is evaluated.

| Candidate | Fixed pilot configuration |
|---|---|
| Prior dummy | Training class-prior probabilities; default threshold predicts benign |
| Logistic regression | L2 via l1_ratio=0, C=1, lbfgs, max_iter=500, tol=1e-4, no class weights |
| Extra Trees | 64 trees, max_depth=20, max_leaf_nodes=4096, min_samples_leaf=2, max_features=sqrt, no bootstrap or class weights, four jobs |
| MLP | (64,32), ReLU, Adam, learning_rate_init=0.001, alpha=0.0001, batch_size=256, 10 epochs maximum, no automatic validation split/early stopping or batch normalization |

Seed 17 only. BLAS is limited to two threads, with one model-training worker at a time. Every worker has a 600-second total wall-time limit and a sampled 12-GiB process-RSS ceiling; the supervisor stops only its own worker on a violation. Record actual iterations, loss curve, convergence warnings, parameters, training time, prediction time, sampled RSS, artifact bytes and warmed batch latency. Bounded iteration/epoch termination is not a convergence certificate.

No hyperparameter search, feature selection, resampling or confirmation seed is performed at B1. The MLP is a CPU feasibility implementation in scikit-learn, not the eventual FL/DP training implementation. Its weights/state need a separately verified migration before integration.

## Metrics and selection boundary

Report threshold 0.5 accuracy, attack precision/recall/F1, binary macro-F1, benign FPR and confusion counts. PR-AUC is explicitly average precision (step-weighted precision-recall summary), not trapezoidal PR area. Report ROC-AUC, validation prevalence, and binary attack recall by canonical attack family; absent-family recall is null rather than zero. Per-family recall does not imply multiclass attribution.

Preregister the validation operating target as benign FPR ≤1%. Sort benign validation scores descending; set the threshold immediately above the (floor(0.01*N_benign)+1)-th score. This handles ties conservatively and yields at most the permitted count of validation false positives. An above-one threshold is allowed as an explicit no-alert operating point. This is validation calibration, not a guaranteed deployment FPR or an unbiased test estimate. No threshold selection uses final-test predictions.

All validation predictions are saved locally for reproducibility. Recompute metrics from those saved probabilities, verify their input hashes and bounds, and check model save/load prediction consistency. Classifier inputs contain only the named vector column. No row/group IDs or labels are predictors. Models from different namespaces are fitted and calibrated independently; a better primary result does not authorize transferring its selected settings into the stress namespace.

Use validation results to identify feasible candidates and data/metric failures. Any preliminary ranking is single-seed, fixed-budget evidence. EXP-003 remains in progress for controlled feature/encoding/model comparisons and repeat seeds; final model selection and test exposure are later gates. A0's detector and integration candidates may diverge.

References: [Extra Trees](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesClassifier.html), [MLPClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html), and [average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html). Installed versions are pinned in requirements-baseline.txt; local behavior and artifact checks govern the run.
