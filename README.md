# PPFCL-NIDS

Privacy-Preserving Federated Continual Learning Network Intrusion Detection System for Financial Networks.

Current checkpoint: CP3 split manifests complete. S1 assigns all 5,196,167 rows in CIC2017 and NF-UNSW to source-bound groups and roles; three external datasets remain sealed. See the [split protocol](docs/CP3-split-protocol-S1.md), [support results](reports/CP3-split-results.md), and [project status](docs/STATUS.md). Next is CP4: deterministic cleaning and training-only preprocessing with transformed-overlap checks. Architecture A0 remains provisional; no models or privacy guarantees exist yet.

This is a student research project using a financial-network deployment scenario. CIC-IDS2017 is a general IDS benchmark, not banking telemetry. The user already has the dataset; do not download it or additional datasets without an explicit later request.

Start with [comparative research](reports/CP0-comparative-review.md), [numerical literature evidence](reports/CP0-numerical-evidence.md), [Architecture A0](docs/architecture/A0.md), [experiment protocol M0.2](docs/experiment-plan-A0.md), and [project status](docs/STATUS.md). The [research registry](docs/registries/research.json) contains 54 sources with explicit reading depth; [project registries](docs/registries/project.json) contain 14 decisions, eight experiment families (two completed data experiments and six planned) and one provisional architecture. [Viva notes](docs/CP0-viva.md) explain the current choices. The original project brief is preserved in docs/project-brief.txt; [M0.1](docs/CP0-methodology.md) and [initial screening](reports/CP0-initial-evidence.md) remain as historical records.

All technology choices remain revisitable. Literature motivates candidates; controlled validation experiments select them. The final test set is reserved for final evaluation. Do not push the repository without an explicit request.
