# CP6 feature comparison and shortcut results

B2 / M0.6, 2026-09-09. 36 new CPU fits completed and verified. Twelve B1 full-feature seed-17 runs supply existing controls; they are not new replicates. Final-test and external scores remain sealed.

## Representation gates

Removing fields changes equality groups. Both reduced candidates fail under the existing S1 split in every namespace; they receive no detector scores. No further rows were excluded, and no roles were reassigned. This rejects a comparison under S1, not the usefulness of those features or the possibility of a redesigned split.

| Dataset / protocol | Reduction | Float64 merged vectors | Float32 merged vectors | Float32 implicated groups | Cross-primary-role vectors |
|---|---|---:|---:|---:|---:|
| cic-ids-2017 / primary | no_shortcut | 25,821 | 25,919 | 505,045 | 22,249 |
| cic-ids-2017 / primary | top32 | 26,126 | 34,809 | 74,301 | 26,534 |
| cic-ids-2017 / stress | no_shortcut | 25,821 | 25,919 | 505,045 | 22,249 |
| cic-ids-2017 / stress | top32 | 26,082 | 34,765 | 74,213 | 26,499 |
| ND-UNSW-NB15-v3 / primary | no_shortcut | 105,556 | 105,556 | 1,207,744 | 90,677 |
| ND-UNSW-NB15-v3 / primary | top32 | 62,292 | 62,292 | 645,765 | 53,068 |
| ND-UNSW-NB15-v3 / stress | no_shortcut | 105,556 | 105,556 | 1,207,744 | 90,677 |
| ND-UNSW-NB15-v3 / stress | top32 | 62,293 | 62,293 | 645,768 | 53,068 |

Full vectors and their categorical augmentation pass. Categories and ANOVA rankings are fitted only on the existing training representatives. Augmentation retains numeric coding and adds common-value indicators; it is not pure categorical replacement.

## Seed-17 representation comparison

| Dataset / protocol | Model | Full macro-F1 | Augmented macro-F1 | Full AP | Augmented AP | Chosen for seed sensitivity |
|---|---|---:|---:|---:|---:|---|
| cic-ids-2017 / primary | logistic | 0.873441 | 0.924994 | 0.915000 | 0.955262 | categorical_augmented |
| cic-ids-2017 / primary | extra_trees | 0.974765 | 0.983111 | 0.990832 | 0.998505 | categorical_augmented |
| cic-ids-2017 / primary | mlp | 0.947913 | 0.965785 | 0.978456 | 0.993051 | categorical_augmented |
| cic-ids-2017 / stress | logistic | 0.914685 | 0.971572 | 0.948449 | 0.991051 | categorical_augmented |
| cic-ids-2017 / stress | extra_trees | 0.953149 | 0.972980 | 0.990922 | 0.999074 | categorical_augmented |
| cic-ids-2017 / stress | mlp | 0.956057 | 0.985265 | 0.986287 | 0.997047 | categorical_augmented |
| ND-UNSW-NB15-v3 / primary | logistic | 0.995222 | 0.997741 | 0.997221 | 0.997435 | categorical_augmented |
| ND-UNSW-NB15-v3 / primary | extra_trees | 0.999297 | 0.999542 | 0.999995 | 0.999997 | full |
| ND-UNSW-NB15-v3 / primary | mlp | 0.999031 | 0.999245 | 0.999354 | 0.999814 | full |
| ND-UNSW-NB15-v3 / stress | logistic | 0.993423 | 0.997018 | 0.998713 | 0.998388 | categorical_augmented |
| ND-UNSW-NB15-v3 / stress | extra_trees | 0.999463 | 0.999392 | 0.999996 | 0.999997 | full |
| ND-UNSW-NB15-v3 / stress | mlp | 0.999212 | 0.998997 | 0.999009 | 0.999490 | full |

The fixed rule requires at least 0.002 absolute macro-F1 improvement and at most 0.002 AP loss against full. Otherwise full is retained. Selection uses validation and seed 17, so subsequent seeds do not create independent model-selection evidence.

## Three-seed sensitivity

| Dataset / protocol | Model / representation | Macro-F1 seeds 17, 29, 43 | Mean ± sample SD | Mean AP | Mean FPR | Mean recall at ≤1% validation FPR | Mean fit seconds |
|---|---|---|---:|---:|---:|---:|---:|
| cic-ids-2017 / primary | logistic / categorical_augmented | 0.924994, 0.924994, 0.924994 | 0.924994 ± 0.000000 | 0.955262 | 0.028879 | 0.706635 | 1.112 |
| cic-ids-2017 / primary | extra_trees / categorical_augmented | 0.983111, 0.982385, 0.982613 | 0.982703 ± 0.000372 | 0.998491 | 0.000347 | 0.997768 | 1.582 |
| cic-ids-2017 / primary | mlp / categorical_augmented | 0.965785, 0.925472, 0.961491 | 0.950916 ± 0.022140 | 0.991528 | 0.012431 | 0.932912 | 6.791 |
| cic-ids-2017 / stress | logistic / categorical_augmented | 0.971572, 0.971572, 0.971572 | 0.971572 ± 0.000000 | 0.991051 | 0.006053 | 0.974231 | 0.408 |
| cic-ids-2017 / stress | extra_trees / categorical_augmented | 0.972980, 0.973634, 0.972985 | 0.973200 ± 0.000376 | 0.998825 | 0.000080 | 0.999767 | 1.379 |
| cic-ids-2017 / stress | mlp / categorical_augmented | 0.985265, 0.967389, 0.984454 | 0.979036 ± 0.010095 | 0.996742 | 0.002739 | 0.987531 | 6.427 |
| ND-UNSW-NB15-v3 / primary | logistic / categorical_augmented | 0.997741, 0.997741, 0.997741 | 0.997741 ± 0.000000 | 0.997435 | 0.000183 | 0.998789 | 0.275 |
| ND-UNSW-NB15-v3 / primary | extra_trees / full | 0.999297, 0.999319, 0.999457 | 0.999358 ± 0.000087 | 0.999995 | 0.000077 | 1.000000 | 0.823 |
| ND-UNSW-NB15-v3 / primary | mlp / full | 0.999031, 0.999095, 0.999063 | 0.999063 ± 0.000032 | 0.999358 | 0.000109 | 0.999543 | 3.914 |
| ND-UNSW-NB15-v3 / stress | logistic / categorical_augmented | 0.997018, 0.997018, 0.997018 | 0.997018 ± 0.000000 | 0.998388 | 0.000161 | 0.999221 | 0.242 |
| ND-UNSW-NB15-v3 / stress | extra_trees / full | 0.999463, 0.999320, 0.999463 | 0.999415 ± 0.000083 | 0.999996 | 0.000117 | 1.000000 | 0.844 |
| ND-UNSW-NB15-v3 / stress | mlp / full | 0.999212, 0.999320, 0.999212 | 0.999248 ± 0.000062 | 0.998829 | 0.000148 | 0.999870 | 3.704 |

Training membership is fixed across seeds. This measures estimator randomness conditional on the data and selected representation; it does not measure population uncertainty. LR is effectively deterministic here. Bounded MLP convergence warnings remain in the run records. Family supports and all per-family recalls are retained in [seed summary](cp6/seed-summary.json).

CIC primary MLP macro-F1 varies from 0.925472 to 0.965785 (sample SD 0.022140), whereas augmented Extra Trees stays between 0.982385 and 0.983111. The MLP remains an integration candidate, with optimizer/threshold stability still to investigate; its seed-17 encoding gain is not a guaranteed improvement across random initializations.

## Endpoint overlap

| NF protocol | Training hosts | Validation rows | Both hosts seen in training | Ordered pair seen in training | Unseen-pair rows |
|---|---:|---:|---:|---:|---:|
| primary | 40 | 472,509 | 472,506 | 472,296 (99.9549%) | 213 |
| stress | 40 | 82,067 | 82,066 | 82,042 (99.9695%) | 25 |

| NF protocol | B1 Extra Trees subgroup | Rows | Benign / attack support | False positives | Benign FPR |
|---|---|---:|---|---:|---:|
| primary | seen_ordered_pair | 472,296 | 447518 / 24778 | 27 | 0.000060 |
| primary | unseen_ordered_pair | 213 | 213 / 0 | 15 | 0.070423 |
| stress | seen_ordered_pair | 82,042 | 74335 / 7707 | 0 | 0.000000 |
| stress | unseen_ordered_pair | 25 | 25 / 0 | 7 | 0.280000 |

Nearly all NF validation flows reuse training endpoint pairs. Every unseen-pair validation row is benign: attack recall and AP cannot be estimated there. The B1 tree produces 15/213 (7.04%) false positives on primary unseen pairs and 7/25 (28%) on stress unseen pairs. These small, differently composed subsets do not prove causal host memorization. Raw subgroup macro-F1 retains the fixed two-label zero-division policy and must not be compared directly with two-class macro-F1. No independently held-out-host estimate is established. CIC host metadata is unavailable. Metadata never enters the detector vector.

## Grouped permutation sensitivity

Each comparison uses the same fixed 50,000-row validation subset, B1 model and threshold 0.5. Positive drops mean worse performance after joint shuffling. Mean drops below summarize three permutations, not three independently trained models.

| Dataset / protocol | B1 model | Shuffled group | Mean macro-F1 drop | Mean AP drop |
|---|---|---|---:|---:|
| cic-ids-2017 / primary | extra_trees | active_idle | 0.001567 | 0.003716 |
| cic-ids-2017 / primary | extra_trees | service | 0.004215 | 0.005879 |
| cic-ids-2017 / primary | extra_trees | window_segment | 0.105246 | 0.054928 |
| cic-ids-2017 / primary | mlp | active_idle | 0.025228 | 0.034761 |
| cic-ids-2017 / primary | mlp | service | 0.042029 | 0.075843 |
| cic-ids-2017 / primary | mlp | window_segment | 0.285082 | 0.487115 |
| cic-ids-2017 / stress | extra_trees | active_idle | 0.005616 | 0.013032 |
| cic-ids-2017 / stress | extra_trees | service | 0.003707 | 0.012829 |
| cic-ids-2017 / stress | extra_trees | window_segment | 0.041324 | 0.059950 |
| cic-ids-2017 / stress | mlp | active_idle | 0.058337 | 0.048558 |
| cic-ids-2017 / stress | mlp | service | 0.085412 | 0.189047 |
| cic-ids-2017 / stress | mlp | window_segment | 0.189236 | 0.421001 |
| ND-UNSW-NB15-v3 / primary | extra_trees | dns_identifier | -0.000066 | 0.000001 |
| ND-UNSW-NB15-v3 / primary | extra_trees | service | 0.000199 | 0.000013 |
| ND-UNSW-NB15-v3 / primary | extra_trees | ttl_window | 0.453204 | 0.619659 |
| ND-UNSW-NB15-v3 / primary | mlp | dns_identifier | 0.000000 | -0.000390 |
| ND-UNSW-NB15-v3 / primary | mlp | service | 0.000133 | 0.001254 |
| ND-UNSW-NB15-v3 / primary | mlp | ttl_window | 0.453510 | 0.852383 |
| ND-UNSW-NB15-v3 / stress | extra_trees | dns_identifier | 0.000000 | 0.000005 |
| ND-UNSW-NB15-v3 / stress | extra_trees | service | 0.000194 | 0.000036 |
| ND-UNSW-NB15-v3 / stress | extra_trees | ttl_window | 0.479216 | 0.587099 |
| ND-UNSW-NB15-v3 / stress | mlp | dns_identifier | 0.000000 | -0.000007 |
| ND-UNSW-NB15-v3 / stress | mlp | service | -0.000019 | 0.001002 |
| ND-UNSW-NB15-v3 / stress | mlp | ttl_window | 0.425951 | 0.745120 |

Jointly shuffling NF TTL/window fields reduces macro-F1 by about 0.426 to 0.479 across these model/protocol combinations. CIC window/segment shuffling produces drops from about 0.041 to 0.285. This identifies strong fitted-model dependence for investigation.

Shuffling may create unrealistic feature combinations; unshuffled correlated fields may also mask dependence. These are model sensitivity measurements, not causal explanations or reduced-feature retraining results. See the [registered protocol](../docs/CP6-comparison-protocol-B2.md) for the exact groups and interpretation references.

## Decision and next work

Retain Extra Trees as the classical reference and the compact MLP as the neural integration candidate. The per-namespace representation choices above are development choices, not a final detector freeze. EXP-003 remains open because reduced-feature comparisons require split redesign and NF host independence is not established.

CP7 must assess host-aware split feasibility and realistic client assignment before stronger generalization claims or FL comparisons. Do not use the sealed final or external results to repair these development choices. An eventual neural framework migration also needs prediction/precision and training equivalence checks before FL/DP integration.

All 36 new runs stayed within worker limits. Their fit time totals 87.970 seconds; supervised time totals 225.284 seconds; sampled maximum worker-tree RSS is 2.548 GiB. Gate preparation, diagnostics and verification are additional work. Warmed batch latency and artifact sizes are in per-run records; none is end-to-end flow latency.

Saved probabilities reproduce model, permutation and host-subgroup metrics. The full 20-test suite passes. See [verification](cp6/verification.json), [test log](cp6-tests.log), [seed summary](cp6/seed-summary.json), and [viva notes](../docs/CP6-viva.md).
