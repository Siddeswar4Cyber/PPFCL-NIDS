# CP4 checkpoint verification

2026-09-09. P1 / M0.4 accepted for the bounded non-private CPU baseline pilot.

Implemented deterministic cleaning ledgers for all 5,196,167 CIC/NF-UNSW rows, five permitted-sample fitted transforms, exact fit-population manifests, and model-ready training/validation files. Each fitting sample contains 100,000 eligible development representatives. The NF CL transform fits task 1 only. Final/private/reference populations never determine these development parameters.

The build verifies source/S1 hashes, rederived group identities, source-row coverage and constant cleaned representation within each S1 group. Each pipeline checks all admitted representative vectors for finite values, correct shape, exact observed-value round trips and no merging of distinct S1 groups. These checks pass in float64.

The persisted verifier independently reopens saved files, checks hashes, verifies exact permitted sampling/role membership, recomputes medians/maxima/observed counts, verifies the smallest qualifying power-of-two divisor, reproduces every exported training/validation vector and checks row/label coverage. All five pipelines pass. Evidence: [verification JSON](preprocessing/verification.json), preprocess-verification-P1.log and [result tables](CP4-preprocessing-results.md).

All eleven fixtures pass: four new preprocessing tests plus the seven existing audit/split tests. The new tests cover contamination by forbidden roles/future tasks, negative/sentinel policies, all-missing fallback, missing-value distinction, out-of-fitting-range values and JSON transform reproduction. Test output is in preprocess-tests-P1.log. The small synthetic fixture labels were also aligned with the declared benign/attack binary convention.

The additional quality rule excludes 2,926 CIC rows, including four Heartbleed rows, beyond the existing S1 conflicts. No NF rows receive an additional negative-value exclusion. All protocol/task roles retain both binary classes. Pilot minority support is recorded; zero Heartbleed training examples preclude a known-class Heartbleed claim for this pilot.

Four dictionary byte hashes and three external ordered predictor contracts match after explicit key-whitespace normalization. Ambiguous direction descriptions, unspecified IAT units and unavailable historical extractor configurations remain unresolved. These checks do not authorize a zero-shot equivalence claim or any external score-based selection.

RUN-002-P1 and DEC-015 record this outcome. A0's data/preprocessing components are implemented; all detector, FL, privacy and CL method winners remain unselected. Float32/GPU conversion, privacy-specific preprocessing, external transformed overlap and learned feature changes each require later gates. No classifier score, threshold or final-test prediction is produced here. Raw data stay unchanged and local data artifacts stay outside Git.
