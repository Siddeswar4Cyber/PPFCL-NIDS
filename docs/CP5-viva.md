# CP5 viva notes

**What is implemented?** A reproducible centralized binary-classification pilot: prior dummy, logistic regression, Extra Trees and a compact MLP. Two datasets each have primary and stress protocols, giving 16 retained runs. Each model sees the same 100,000 training representatives within its protocol. Federation, differential privacy and continual learning are still later experiments.

**Why amend preprocessing before fitting?** Extra Trees converts inputs to float32. Different float64 feature groups can become identical at that precision. The full pre-score CIC gate found 22,813 merged vectors involving 45,645 S1 groups. P2 excludes every implicated group for all CIC candidates, including 119,119 rows, then refits the permitted preprocessing samples. Both float64 and float32 gates pass afterward. This is a conservative population change, not a universal correction of CIC-IDS2017. NF passes without that amendment.

**Does excluding groups across reserved roles use the test set for selection?** The eligibility gate inspects feature equality across roles before scoring, preserving the existing S1 assignments. It does not use held-out prediction metrics. Nevertheless, this is a dataset-wide feature-aware partition protocol, not a purely training-only data audit; disclose that distinction. Final-test and external model scores remain sealed.

**Why report macro-F1 and average precision?** Accuracy can reward predicting benign on imbalanced traffic. The dummy detects no attacks. Binary macro-F1 gives equal weight to benign and attack F1; average precision summarizes the precision-recall curve and has class prevalence as the constant-score reference. Per-family binary recall describes attack detection, not multiclass attribution.

**What does recall at 1% FPR mean?** The threshold is calibrated on benign validation scores to permit at most floor(0.01 times the benign count) false positives. Ties are handled conservatively. Its recall is also measured on that validation set; this is an operating-point comparison, not an unbiased final-test estimate or a production false-alarm guarantee.

**Which model won?** No final model is selected. Extra Trees has the highest observed primary-validation macro-F1 for both datasets. MLP slightly leads CIC stress-validation macro-F1, while Extra Trees leads its AP and calibrated recall. Different metrics and implementation costs can favor different candidates. Only one configuration and seed 17 were run per candidate; repeat-seed and feature/encoding comparisons remain necessary.

**Are near-perfect NF scores proof of deployment quality?** No. Hash checks, label exclusion and exact group separation passed, but related flows, capture artifacts or host behavior can remain shared. CP6 must investigate shortcuts and representation choices. Neither source-corpus validation nor the financial deployment scenario establishes performance on actual banking traffic.

**Did the MLP converge?** It completed its fixed 10-epoch budget and emitted a convergence warning. Its final epoch is used without internal validation splitting or best-epoch selection. This is bounded feasibility evidence. The scikit-learn implementation also needs separately verified migration before FL/DP training.

**What failed and how was it handled?** The first tree run could not serialize a NumPy integer in its report. Initial memory monitoring sampled the Windows launcher instead of the whole worker process tree. Both issues were fixed; all configurations were rerun unchanged. Original attempts remain preserved and are not counted as confirmation seeds.

**What can be claimed now?** The local CPU can run the bounded candidates, saved validation probabilities reproduce their metrics, and all 16 tests pass. No privacy, forgetting, federation, final generalization or novel-algorithm claim is established. See the [results](../reports/CP5-baseline-results.md) and [verification](../reports/CP5-checkpoint-verification.md).
