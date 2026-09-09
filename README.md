# PPFCL-NIDS

Privacy-Preserving Federated Continual Learning Network Intrusion Detection System for Financial Networks.

Current checkpoint: CP6 feature comparisons and shortcut diagnostics complete. B2 adds 36 verified CPU fits and three-seed sensitivity for 12 model/protocol combinations. All 20 tests pass. See the [B2 protocol](docs/CP6-comparison-protocol-B2.md), [results](reports/CP6-comparison-results.md), [verification](reports/CP6-checkpoint-verification.md), and [project status](docs/STATUS.md). Next is CP7: host-aware split feasibility and client assignment. Model/FL/privacy/CL choices remain provisional, and final-test scores remain sealed.

Before any model fit, a float32 gate found CIC precision collisions. The P2 amendment excludes 119,119 associated rows for every CIC candidate and refits the transforms; both precision gates then pass. NF candidates retain P1. This population change must accompany reported scores; validation results do not establish deployment performance.

CP6 preserves those populations. Reduced-feature candidates fail renewed overlap gates; categorical augmentation remains valid. NF validation shares training endpoint pairs in over 99.95% of flows. Its small unseen-pair subsets contain only benign traffic, so unseen-pair attack detection remains unmeasured. The [CP5 pilot](reports/CP5-baseline-results.md) remains historical evidence.

This is a student research project using a financial-network deployment scenario. CIC-IDS2017 is a general IDS benchmark, not banking telemetry. The user already has the dataset; do not download it or additional datasets without an explicit later request.

Start with [comparative research](reports/CP0-comparative-review.md), [numerical literature evidence](reports/CP0-numerical-evidence.md), [Architecture A0](docs/architecture/A0.md), [experiment protocol M0.2](docs/experiment-plan-A0.md), and [project status](docs/STATUS.md). The [research registry](docs/registries/research.json) contains 59 sources with explicit reading depth; [project registries](docs/registries/project.json) contain 20 decisions, eight experiment families (two completed, one in progress and five planned), 53 follow-up/pilot run records and one provisional architecture. [CP6 viva notes](docs/CP6-viva.md) explain the comparisons and their limits. The original project brief is preserved in docs/project-brief.txt; [M0.1](docs/CP0-methodology.md) and [initial screening](reports/CP0-initial-evidence.md) remain as historical records.

All technology choices remain revisitable. Literature motivates candidates; controlled validation experiments select them. The final test set is reserved for final evaluation. Do not push the repository without an explicit request.
