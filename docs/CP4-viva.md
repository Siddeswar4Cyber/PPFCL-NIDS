# CP4 viva notes

**What was fitted?** Exact per-column medians and maximum-absolute scaling divisors on a deterministic sample of 100,000 permitted training representatives. No classifier, threshold, feature selector or privacy mechanism was fitted.

**Why add missing indicators to every column?** A field can be complete during fitting and missing later. A fixed output schema handles that case and distinguishes observed median-valued data from imputed data. Initial-window -1 observations also have a separate sentinel indicator.

**Why powers of two for scaling?** Scaling bounds the fitting sample without clipping held-out values. Power-of-two division is particularly suitable for preserving normal binary floating-point values. P1 additionally checks exact round trips and all admitted transformed groups. This is a correctness-oriented baseline choice, not evidence of best prediction accuracy.

**What happened to negative values?** Initial-window -1 values have an explicit unavailable-observation policy. Other negative counts, timings or sizes make the group quality-ineligible. CIC loses 2,926 additional rows under this rule. The source and ledger remain unchanged, and the excluded population is disclosed rather than silently repaired.

**Can preprocessing leak future information?** Yes. The NF continual-learning artifact fits on the first task only and stays frozen. Stress studies fit their own earlier/non-Friday training populations. Tests change forbidden-role and future-task values and verify that fitted parameters do not change.

**Is this private preprocessing?** No. These are non-private development artifacts. The eventual DP experiment needs separately reviewed public-reference preprocessing or a valid private estimator and full release accounting. The fact that private_train rows were excluded from these fits is a boundary check, not a privacy theorem.

**Why are protocol codes still numeric?** P1 preserves the extractor's numeric representation as an initial baseline with an acknowledged nominal-distance limitation. Alternative encoding and shortcut ablations must be compared under the same experimental budget and undergo new overlap checks.

**Can the same files go directly into a GPU model?** Not yet. P1 verifies float64 vectors. Conversion to float32 may merge distinguishable values and needs its own precision/overlap check, alongside training-framework compatibility.

**What about rare classes?** A fixed 100,000-group pilot may contain no Heartbleed observations and very few examples of other rare attacks. P1 records exact pilot class support. Binary detection is the primary initial task; absence from training must be disclosed in per-family or multiclass interpretation.

**Are external datasets semantically identical?** The 49 ordered candidate names and four dictionary files match, but some descriptions contradict their names or omit units. Historical extractor equivalence is unverified. No external score is used for selection, and cross-domain transformed overlap remains a separate gate.
