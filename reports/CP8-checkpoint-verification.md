# CP8 checkpoint verification

- Runtime: pinned Torch CUDA build installed after explicit authorization; CPU/GPU arithmetic and autograd pass; baseline dependency versions preserved.
- Tests: 32 pass, including independent three-step native-Adam and partial-batch gradient checks.
- Migration: 4/4 full-validation CPU/CUDA/serialization gates pass; saved weights reproduce probabilities.
- Stability: 24/24 preregistered fits complete; 20 epochs each; no score-based budget extension.
- Reproduction: source/data/model hashes verified; saved predictions and metrics reproduced; initialization checked against the registered stream and across candidates.
- Selection: N1 practical eligibility thresholds applied independently per scope; full candidate/seed values preserved.
- Limits: all workers within registered wall time, sampled process-tree RSS and Torch allocator bounds.
- Scope: no final/external scores, private guarantee, CL training or FL run. Eligibility for a pilot is not a deployment claim.

Machine-readable evidence is in reports/cp8/verification.json and reports/cp8/selection.json. CP8 is complete as an executed bounded experiment, even where a candidate fails a scientific eligibility rule.
