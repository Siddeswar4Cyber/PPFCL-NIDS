# PPFCL-NIDS

Privacy-Preserving Federated Continual Learning Network Intrusion Detection System for Financial Networks.

Current checkpoint: CP8 COMPLETE. All four Torch CPU/CUDA migration checks, 24 registered stability fits and 32 tests pass. 4/4 namespaces have an N1 candidate eligible for the next pilot. See [CP8 results](reports/CP8-neural-results.md), [verification](reports/CP8-checkpoint-verification.md), and [project status](docs/STATUS.md). Next is CP9: matched central/local/FedAvg comparisons on fixed C1 clients. Model/FL/privacy/CL choices remain provisional; final/external scores remain sealed.

Before any model fit, a float32 gate found CIC precision collisions. The P2 amendment excludes 119,119 associated rows for every CIC candidate and refits the transforms; both precision gates then pass. NF candidates retain P1. This population change must accompany reported scores; validation results do not establish deployment performance.

CP6 preserves those populations. Reduced-feature candidates fail renewed overlap gates; categorical augmentation remains valid. NF validation shares training endpoint pairs in over 99.95% of flows. Its small unseen-pair subsets contain only benign traffic, so unseen-pair attack detection remains unmeasured. The [CP5 pilot](reports/CP5-baseline-results.md) remains historical evidence.

CP7 finds all NF development attacks in one endpoint component. Both registered host-separation designs lack adequate two-class support. C1 therefore supports a synthetic-client study, with no independent-host or institutional claim. Three highly skewed scenarios use an explicitly labeled, preregistered uniform-mixture fallback.

This is a student research project using a financial-network deployment scenario. CIC-IDS2017 is a general IDS benchmark, not banking telemetry. The user already has the dataset; do not download it or additional datasets without an explicit later request.

Start with [comparative research](reports/CP0-comparative-review.md), [numerical literature evidence](reports/CP0-numerical-evidence.md), [Architecture A0](docs/architecture/A0.md), [experiment protocol M0.2](docs/experiment-plan-A0.md), and [project status](docs/STATUS.md). The [research registry](docs/registries/research.json) contains 61 sources with explicit reading depth; [project registries](docs/registries/project.json) contain 26 decisions, eight experiment families (two completed, two in progress and four planned), 94 data/model run records and one provisional architecture. [CP7 viva notes](docs/CP7-viva.md) explain the client contracts and their limits. The original project brief is preserved in docs/project-brief.txt; [M0.1](docs/CP0-methodology.md) and [initial screening](reports/CP0-initial-evidence.md) remain as historical records.

All technology choices remain revisitable. Literature motivates candidates; controlled validation experiments select them. The final test set is reserved for final evaluation. Do not push the repository without an explicit request.
