# Project status

Updated: 2026-09-09.

Current checkpoint: CP5 CPU baseline pilot COMPLETE. CP0 through CP4 remain complete. EXP-003 continues into CP6 for controlled feature/model comparisons and repeat seeds; completing the bounded pilot does not complete detector selection.

Architecture: A0, data pipeline and centralized baselines implemented; model/FL/DP/CL choices PROVISIONAL. Methodology: M0.5 / S1 / CIC P2 / NF P1 / B1. DEC-016 records the pre-score precision amendment and DEC-017 keeps final selection open.

Completed: Seven research workstreams, 56-source registry (54 initial sources plus two implementation references) with explicit reading depth, numerical literature comparison, financial-threat observability matrix, A0 component contracts, experiment budgets and selection gates. The isolated audit environment uses Python 3.13.13, DuckDB 1.5.5 and psutil 7.2.2. EXP-001 audited all 69,765,764 rows across 12 CSVs in five dataset families. Four constructed integration tests passed; artifact invariants and all 15 local archive-manifest comparisons passed. Raw source files were not modified.

Latest findings: CIC2017 has 308,381 excess identical rows, 698 conflicting feature groups, identical duplicate header columns, nonfinite cells and damaged web-label separators already present in source bytes. NF-UNSW, NF-CIC2018 and NF-ToN contain 14,815, 628,474 and 1,816,137 excess identical rows respectively; BoT has none. Removing IP/time fields reveals conflicting predictor vectors in every NetFlow family. NF-UNSW includes a benign-only day; file order is not generally temporal order. See [audit report](../reports/CP1-dataset-audit.md) and [interpretation](../reports/CP1-findings-and-decisions.md).

Validation evidence: [verification.json](../reports/audit/verification.json), per-family source hashes and statistics, [run.json](../reports/audit/run.json), [environment](../reports/audit/environment.json), and tests/test_audit.py. The last resumed invocation took 4,219.984 seconds and peaked at 6,030,651,392 bytes of process RSS. Earlier attempts are additional work; BoT's 43.483 seconds cover its resumed completion segment only. No total runtime across all interruptions is claimed.

Experiment state: EXP-001 and EXP-002 COMPLETED; EXP-003 RUNNING; EXP-004 through EXP-008 PLANNED. Sixteen fixed-configuration B1 model runs are complete, alongside RUN-002-P1. There are no final-test detection results or established privacy guarantees. All generated matrices, model files and saved validation predictions remain local and ignored by Git.

CP3 results: 5,196,167 row memberships cover CIC2017 and NF-UNSW. The accepted conflict policy quarantines 7,020 and 3,647 rows respectively. Group-role overlap, source/hash binding, row coverage, stress boundaries and binary support pass. Both NF capture periods support the two-task CL design; 242,973 rows spanning those periods are excluded from CL only. CIC Heartbleed, Infiltration and SQL Injection have limited independent class support. See [split results](../reports/CP3-split-results.md) and [S1 protocol](CP3-split-protocol-S1.md).

CP4 results: 2,926 CIC rows are additionally quality-ineligible because of negative timing/size/count values; no NF-UNSW rows receive that exclusion. The cleaned eligible populations are 2,820,797 and 2,361,777 rows. Five pipelines each fit exactly 100,000 permitted development representatives. Output widths are 156 CIC / 98 NF fields, including explicit missing/sentinel indicators. Persisted hashes, sampling scopes, recomputed parameters and exported vectors pass; no admitted S1 groups merge. NF CL fitting uses task 1 only. Eleven integration tests pass. See [P1 results](../reports/CP4-preprocessing-results.md).

CP5 results: All 16 retained runs completed and saved probabilities reproduce every reported metric. The full suite passes 16 tests. Before the first model fit, float32 conversion merged CIC feature vectors; P2 excludes all 119,119 rows in the 45,645 implicated S1 groups for every CIC candidate and refits preprocessing. The resulting 2,701,678 eligible CIC rows pass float64 and float32 equality gates. NF P1 passes unchanged. This precision-based exclusion changes the evaluated population. See [B1 results](../reports/CP5-baseline-results.md), [verification](../reports/CP5-checkpoint-verification.md), and [viva notes](CP5-viva.md).

The primary-validation Extra Trees macro-F1 values are 0.974765 (CIC) and 0.999297 (NF). These are fixed-budget seed-17 results, not confirmed winners or deployment estimates. MLP has the highest CIC stress-validation macro-F1, while Extra Trees has higher AP and calibrated recall there. NF's near-perfect results require capture/host shortcut investigations. Each fit used 100,000 permitted representatives; sampled peak worker-tree RSS stayed below 1.31 GiB. Initial reporting/monitoring failures and their unchanged-configuration reruns are preserved.

Next action: CP6 / EXP-003 investigates shortcut dependence and controlled feature/encoding comparisons, then confirms retained configurations across seeds 17, 29 and 43. Any changed feature representation requires renewed group-overlap checks and a common comparison population. Client partitioning and FL comparisons follow that evidence. Privacy-confirmatory preprocessing needs a separately reviewed public/private mechanism; existing development transforms are not approved for that claim. Final-test and external scores stay sealed.

Open decisions: NetFlow 57-versus-53-feature provenance discrepancy; external field semantics and any new transform-induced duplicates; minority support; realistic temporal tasks and client grouping; training budgets; private sampling/release accounting; final candidate winners and thresholds. Shared headers and matching local archives do not prove publisher authenticity or equivalent extraction semantics.

User context: local data at C:\Users\nimma\Downloads\Datasets; deadline September 20, assumed 2026; no special report format. Reported i7-13650HX and RTX 4050 Laptop GPU with 6 GB VRAM were detected. psutil measured about 31.7 GiB RAM, differing from the earlier reported 23.7 GB. Training-framework CUDA support is not yet tested.

Blocked: None for CP6 development comparisons. Privacy-confirmatory training requires mechanism/accounting review; final evaluation requires a selection freeze. External model scores must remain outside selection.

Deferred: Optional model/FL/CL alternatives, HE/SMPC/TEE, secure aggregation pending feasibility, and final report/slides pending measured evidence. No datasets were downloaded and no repository push is authorized.

Rejected: Blind cross-schema concatenation, a first-ever FL+DP+CL claim, a fixed untested winning stack, banking-telemetry claims and FL-alone privacy guarantees. No model candidate is empirically rejected.

Risks: Attack/day confounding, missing CIC grouping metadata, ambiguous feature semantics, rare-class support, synthetic-client realism, replay/privacy incompatibility, runtime and domain shift. Implementation-specific privacy proof/accountant review and a literature refresh remain pending.

Git milestone: Local branch codex/cp5-baseline-pilot. Configuration and the precision amendment were preregistered in 3d31e90 before the first model fit. Completed-run provenance is recorded in the local checkpoint history and run registry. No push has been performed.
