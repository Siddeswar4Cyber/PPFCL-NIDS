# Resource and deadline envelope

The more specific [A0 experiment protocol](experiment-plan-A0.md) now governs trial limits and calendar targets. This earlier envelope is retained for decision history.

2026-09-08. User reports submission on September 20; assume 2026. Approximately 12 days remain. User hardware: i7-13650HX, 23.7 GB RAM, RTX 4050 Laptop GPU with 6 GB VRAM; Intel UHD is also present. No special report format is required. These are user-reported specifications, not benchmark results.

[PLANNED / NOT IMPLEMENTED] Calendar targets below are provisional and do not override checkpoint gates. Persist negative results and explicit unfinished scope. Do not claim completion because the date has arrived.

| Dates | Priority and relevant checkpoints | Deliverable |
|---|---|---|
| Sep 8-9 | CP0 literature, actual dataset edition implications, scope/threat/split protocol | Research matrices, candidate shortlist, A0 only after research gate |
| Sep 9-10 | CP1-4 environment, data audit, split and preprocessing | Audited manifest and reproducible leakage-safe pipeline |
| Sep 10-12 | CP5-10 model/feature/local/FL comparisons | Representative model and FL selection with budgets |
| Sep 12-14 | CP11-15 privacy and CL | Valid privacy path, utility curve, naive and CL retention comparison |
| Sep 14-16 | CP16-18 integration and ablations | Matched six-configuration comparison; investigate regressions |
| Sep 16-17 | CP19-20 generalization and untouched evaluation | Final evidence table and limitations; no further test-driven tuning |
| Sep 18-20 | CP21-22 report, demo and viva; correction buffer | Verified deliverables and reproducibility package |

Candidate implementation envelope, subject to literature and measured pilot cost:

- Models: Logistic Regression, one strong tree ensemble/boosting model and compact MLP initially. Add 1D-CNN only if its assumptions and cost justify it. Research the wider model list regardless.
- FL: FedAvg and one or two justified alternatives; a small, explicitly synthetic cross-silo client population. Pilot approximately five clients sequentially on one GPU if feasible; count is provisional. Include IID plus a defined non-IID condition before expanding severity.
- Privacy: research DP/secure aggregation/HE/SMPC/TEE broadly; implement the threat-matched minimum correctly. DP and secure aggregation are candidate complements. If cryptography cannot be implemented and verified, record it as not implemented and narrow the protection claim; a masked-update mock is not secure aggregation.
- CL: frozen/naive controls, bounded replay if allowed, and one justified rehearsal-free method; expand to DER++ only if budget and accounting support it. Limit initial stream to a few defensible tasks with adequate support.
- Integration: six core configurations, focused ablations, key multi-seed comparisons. Include at least one meaningful domain/time holdout if data support it; select external tracks before model selection and seal final target data.
- Data/compute: the large NF CSVs call for chunked, disk-backed processing. Avoid loading all datasets/copies into 23.7 GB RAM. Benchmark CPU trees and GPU neural models separately; avoid several concurrent GPU trainers within 6 GB VRAM. A stratified/group-preserving development pilot may estimate cost, but final samples and population claims must be documented.

Stopping rule: after cost pilots, predeclare time/trial/seed budgets. Reduce optional candidate breadth before reducing leakage checks, formal privacy correctness, negative-result retention or final-test discipline. A sound limited study is the target; no fabricated performance or unsupported production readiness.
