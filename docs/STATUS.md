# Project status

Updated: 2026-09-09.

Current checkpoint: CP3 labels, feature contracts, groups and split manifests COMPLETE. CP1 environment and CP2 audit remain complete. CP0 initial research is complete for provisional A0. The combined environment/audit milestone retains the roadmap: CP3 splits and task manifests, CP4 fitted preprocessing, CP5 baselines.

Architecture: A0, PROVISIONAL / NOT IMPLEMENTED. Methodology: M0.3 / split version S1. Data evidence adds DEC-013 and DEC-014; it does not select a model, FL aggregator, privacy mechanism or continual-learning method.

Completed: Seven research workstreams, 54-source registry with explicit reading depth, numerical literature comparison, financial-threat observability matrix, A0 component contracts, experiment budgets and selection gates. The isolated audit environment uses Python 3.13.13, DuckDB 1.5.5 and psutil 7.2.2. EXP-001 audited all 69,765,764 rows across 12 CSVs in five dataset families. Four constructed integration tests passed; artifact invariants and all 15 local archive-manifest comparisons passed. Raw source files were not modified.

Latest findings: CIC2017 has 308,381 excess identical rows, 698 conflicting feature groups, identical duplicate header columns, nonfinite cells and damaged web-label separators already present in source bytes. NF-UNSW, NF-CIC2018 and NF-ToN contain 14,815, 628,474 and 1,816,137 excess identical rows respectively; BoT has none. Removing IP/time fields reveals conflicting predictor vectors in every NetFlow family. NF-UNSW includes a benign-only day; file order is not generally temporal order. See [audit report](../reports/CP1-dataset-audit.md) and [interpretation](../reports/CP1-findings-and-decisions.md).

Validation evidence: [verification.json](../reports/audit/verification.json), per-family source hashes and statistics, [run.json](../reports/audit/run.json), [environment](../reports/audit/environment.json), and tests/test_audit.py. The last resumed invocation took 4,219.984 seconds and peaked at 6,030,651,392 bytes of process RSS. Earlier attempts are additional work; BoT's 43.483 seconds cover its resumed completion segment only. No total runtime across all interruptions is claimed.

Experiment state: EXP-001 and EXP-002 COMPLETED; EXP-003 through EXP-008 PLANNED. Zero completed model experiments, final detection results or established privacy guarantees. S1 split manifests exist; no cleaned dataset or fitted preprocessing exists yet.

CP3 results: 5,196,167 row memberships cover CIC2017 and NF-UNSW. The accepted conflict policy quarantines 7,020 and 3,647 rows respectively. Group-role overlap, source/hash binding, row coverage, stress boundaries and binary support pass. Both NF capture periods support the two-task CL design; 242,973 rows spanning those periods are excluded from CL only. CIC Heartbleed, Infiltration and SQL Injection have limited independent class support. See [split results](../reports/CP3-split-results.md) and [S1 protocol](CP3-split-protocol-S1.md).

Next action: CP4 implements deterministic cleaning and training-only imputation/encoding/scaling, verifies semantic feature use, and rechecks equality after every proposed feature transform. Any new cross-role collision requires an explicit protocol amendment before fitting models. CP5 / EXP-003 begins only after those checks. Selection namespaces for primary and stress protocols remain separate.

Open decisions: NetFlow 57-versus-53-feature provenance discrepancy; field semantics and normalized duplicates; minority support; realistic temporal tasks and client grouping; training budgets; private sampling/release accounting; final candidate winners and thresholds. Shared headers and matching local archives do not prove publisher authenticity or equivalent extraction semantics.

User context: local data at C:\Users\nimma\Downloads\Datasets; deadline September 20, assumed 2026; no special report format. Reported i7-13650HX and RTX 4050 Laptop GPU with 6 GB VRAM were detected. psutil measured about 31.7 GiB RAM, differing from the earlier reported 23.7 GB. Training-framework CUDA support is not yet tested.

Blocked: None for CP4 work. Privacy-confirmatory training requires mechanism/accounting review; final evaluation requires a selection freeze. External model scores must remain outside selection.

Deferred: Optional model/FL/CL alternatives, HE/SMPC/TEE, secure aggregation pending feasibility, and final report/slides pending measured evidence. No datasets were downloaded and no repository push is authorized.

Rejected: Blind cross-schema concatenation, a first-ever FL+DP+CL claim, a fixed untested winning stack, banking-telemetry claims and FL-alone privacy guarantees. No model candidate is empirically rejected.

Risks: Attack/day confounding, missing CIC grouping metadata, ambiguous feature semantics, rare-class support, synthetic-client realism, replay/privacy incompatibility, runtime and domain shift. Implementation-specific privacy proof/accountant review and a literature refresh remain pending.

Git milestone: Local branch codex/cp3-split-manifests; this checkpoint is recorded in its local commit history. No push has been performed.
