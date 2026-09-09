# CP6 feature comparisons and seed sensitivity B2

2026-09-09. M0.6 extends B1. Goal: test whether representation choices improve the bounded detectors and investigate shortcuts before FL integration. Prerequisites are the verified S1 memberships, CIC P2 / NF P1 transforms and B1 artifacts. All B1 training and validation populations remain fixed; no final-test or external prediction is authorized.

## Registered comparisons

For each dataset and primary/stress namespace, compare LR, Extra Trees and MLP with their unchanged B1 settings on at most four feature representations at seed 17:

1. **full**: reuse the verified B1 run, without counting it as a new independent replicate.
2. **no_shortcut**: remove complete field groups, including missing/sentinel indicators. CIC removes Destination Port, both initial windows and minimum forward segment size. NF removes source/destination ports, PROTOCOL, L7_PROTO, MIN_TTL, MAX_TTL, both TCP window maxima and DNS_QUERY_ID. These are hypotheses about capture/service/host dependence; legitimate attack information may also be removed.
3. **top32**: rank raw-field groups by the maximum ANOVA F score over their numeric/missing/sentinel columns, using only the saved 100,000 training representatives and training labels. Nonfinite scores map to zero; ties use input field order. Retain 32 complete groups. Scores are a ranking heuristic, not significance tests on independent observations.
4. **categorical_augmented**: retain the entire original vector and append indicators for the 16 most frequent observed training values per nominal field (frequency descending, value ascending for ties). CIC uses Destination Port; NF uses both ports, PROTOCOL and L7_PROTO. All other/unseen values have zero appended indicators and retain their original numeric value/missing flag. This offers categorical paths while retaining numeric coding; it is not pure one-hot replacement.

Every reduced representation must have zero nonfinite vectors and zero merges of distinct admitted S1 groups in both float64 and float32, checked over all eligible representatives before fitting. Count cross-role merges as well. Reject an unsafe representation under S1, record why, and do not score it. Do not discard more rows or move groups just to obtain a feature comparison. Such reductions would require a separately registered split/population study. The augmented representation is injective because its unchanged original-vector prefix passes the existing gates; verify that prefix for exported training/validation inputs.

Use the same exact training rows and validation order, per-namespace transforms, seed, model hyperparameters, resource limits and metric definitions as B1. Models run sequentially with 600-second / 12-GiB sampled worker-tree limits and BLAS two threads. Save probabilities, model artifacts, warnings, cost and hashes. Maximum new exploration fits: 36 if every gate passes.

## Fixed sensitivity rule

After seed-17 comparisons, choose one representation per model/namespace for seeds 29 and 43. Starting from full, switch only to a valid candidate improving binary macro-F1 at threshold 0.5 by at least 0.002 absolute while losing no more than 0.002 average precision against full. Among eligible candidates choose highest macro-F1, then AP, then smaller width, then representation name. If none meets the margin, keep full. Record that confirmation is conditional on seed-17 representation selection and uses the same validation data; it is seed sensitivity, not fresh holdout confirmation. Keep training membership/transform fixed so seeds measure model randomness, not resampling uncertainty. Maximum additional fits: 24.

Report all three seeds, mean and sample standard deviation, per-family recall, FPR and cost. Do not derive population confidence intervals or significance claims from three seeds. Deterministic LR may return identical predictions for all seeds. Retain classical and neural integration candidates separately; no detector configuration is frozen for final evaluation in this checkpoint.

## Shortcut diagnostics

Use only the saved B1 full models and existing validation inputs. For Extra Trees and MLP, select up to 50,000 validation row indices uniformly without replacement with seed 17 and record their hash. Jointly permute complete related field groups with permutation seeds 17, 29 and 43: CIC service port, initial windows/minimum segment size, active/idle timing; NF ports/protocols, TTL/windows, DNS identifier. Record macro-F1/AP changes against the unchanged model on the exact same subset. No threshold recalibration on perturbed inputs. These interventions can create unrealistic combinations, and correlated unshuffled fields can hide dependence; they are sensitivity diagnostics, not causal importance or retrained ablation scores.

For NF, join the original audited source/destination IP metadata to the exact training and validation row identities. Record overlap for hosts seen in either direction and ordered endpoint pairs, plus B1 validation metrics by seen/unseen pair where support permits. Missing addresses are reported separately. No IP addresses become model inputs or appear in tracked reports. CIC's supplied CSV lacks host metadata, so do not invent a host-isolation claim. No host-only classifier or revised split is trained at B2.

## Success, stopping and evidence

Complete the four representation gates per namespace, all scientifically valid registered fits, the fixed seed sensitivity, and the shortcut diagnostics. Independently recompute saved prediction metrics and verify artifact/hash/membership consistency. Preserve failed and rejected attempts. Update experiment, decision, architecture and progress records before advancing. If gates reject reductions, report an unresolved split redesign requirement rather than treating rejection as evidence of poor detection.

Implementation references: [ANOVA F ranking](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.f_classif.html), [permutation importance](https://scikit-learn.org/stable/modules/permutation_importance.html), and [correlated-feature limitations](https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance_multicollinear.html). No additional package installation or GPU training is required.
