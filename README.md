# PPFCL-NIDS

Privacy-Preserving Federated Continual Learning Network Intrusion Detection System for Financial Networks.

Current checkpoint: CP5 CPU baseline pilot complete. Sixteen runs compare a prior dummy, logistic regression, Extra Trees and a compact MLP on two datasets and their primary/stress validation protocols. Saved predictions reproduce every reported metric; all 16 tests pass. See the [B1 protocol](docs/CP5-baseline-protocol-B1.md), [results](reports/CP5-baseline-results.md), [verification](reports/CP5-checkpoint-verification.md), and [project status](docs/STATUS.md). Next is CP6: shortcut checks, controlled feature/encoding comparisons and repeat seeds. Model/FL/privacy/CL choices remain provisional, and final-test scores remain sealed.

Before any model fit, a float32 gate found CIC precision collisions. The P2 amendment excludes 119,119 associated rows for every CIC candidate and refits the transforms; both precision gates then pass. NF candidates retain P1. These changed populations and single-seed validation results do not establish deployment performance.

This is a student research project using a financial-network deployment scenario. CIC-IDS2017 is a general IDS benchmark, not banking telemetry. The user already has the dataset; do not download it or additional datasets without an explicit later request.

Start with [comparative research](reports/CP0-comparative-review.md), [numerical literature evidence](reports/CP0-numerical-evidence.md), [Architecture A0](docs/architecture/A0.md), [experiment protocol M0.2](docs/experiment-plan-A0.md), and [project status](docs/STATUS.md). The [research registry](docs/registries/research.json) contains 56 sources with explicit reading depth; [project registries](docs/registries/project.json) contain 17 decisions, eight experiment families (two completed, one in progress and five planned), 17 follow-up/pilot run records and one provisional architecture. [CP5 viva notes](docs/CP5-viva.md) explain the pilot and its limits. The original project brief is preserved in docs/project-brief.txt; [M0.1](docs/CP0-methodology.md) and [initial screening](reports/CP0-initial-evidence.md) remain as historical records.

All technology choices remain revisitable. Literature motivates candidates; controlled validation experiments select them. The final test set is reserved for final evaluation. Do not push the repository without an explicit request.
