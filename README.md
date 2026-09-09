# PPFCL-NIDS

Privacy-Preserving Federated Continual Learning Network Intrusion Detection System for Financial Networks.

Current checkpoint: CP1 environment and CP2 dataset audit complete (69,765,764 rows across five families); provisional Architecture A0 remains unvalidated. See the [audit procedure](docs/CP1-environment-and-audit.md) and [audit report](reports/CP1-dataset-audit.md) for current artifacts. Next is CP3: label, feature, grouping and split manifests. No model training or established privacy guarantee exists.

This is a student research project using a financial-network deployment scenario. CIC-IDS2017 is a general IDS benchmark, not banking telemetry. The user already has the dataset; do not download it or additional datasets without an explicit later request.

Start with [comparative research](reports/CP0-comparative-review.md), [numerical literature evidence](reports/CP0-numerical-evidence.md), [Architecture A0](docs/architecture/A0.md), [experiment protocol M0.2](docs/experiment-plan-A0.md), and [project status](docs/STATUS.md). The [research registry](docs/registries/research.json) contains 54 sources with explicit reading depth; [project registries](docs/registries/project.json) contain 13 decisions, eight experiment families (one completed audit and seven planned) and one provisional architecture. [Viva notes](docs/CP0-viva.md) explain the current choices. The original project brief is preserved in docs/project-brief.txt; [M0.1](docs/CP0-methodology.md) and [initial screening](reports/CP0-initial-evidence.md) remain as historical records.

All technology choices remain revisitable. Literature motivates candidates; controlled validation experiments select them. The final test set is reserved for final evaluation. Do not push the repository without an explicit request.
