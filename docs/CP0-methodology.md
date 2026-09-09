# CP0: research and methodology

Version M0.1 | 2026-09-08 | Initial protocol, incomplete research

Historical protocol. The initial research gate subsequently closed with the comparative review and provisional A0 on the same date. Current additions/overrides are in [M0.2 experiment protocol](experiment-plan-A0.md), [A0](architecture/A0.md), and [status](STATUS.md). Statements below about unfinished initial screening describe the earlier state.

## Objective and contribution boundary

[CURRENT DESIGN DECISION] Investigate whether institutions represented by simulated clients can collaboratively learn a flow-based intrusion detector while keeping raw telemetry local, limiting specified information leakage, and adapting to changing traffic without unacceptable loss of previous detection capability. Compare detection, privacy, retention, generalization, communication, and resource costs under controlled conditions.

The financial setting motivates confidentiality and collaborative defense; it does not make CIC-IDS2017 representative of banks. Centralized experiments use the public benchmark as a research reference and are separate from the proposed decentralized deployment. A centralized model is a useful reference, not a mathematical upper bound.

[HYPOTHESIS] A defensible contribution may be a reproducible comparison of integrated FL, privacy, and CL under leakage-aware splits and heterogeneous clients. Algorithmic novelty is unestablished. Prior integrated work already exists (R020). A gap statement requires detailed related-work comparison, including negative evidence and recent work.

## Evidence discipline

Use the user's five categories: LITERATURE EVIDENCE; OUR EXPERIMENTAL RESULT; CURRENT DESIGN DECISION; HYPOTHESIS; PLANNED / NOT IMPLEMENTED. A repository observation is an observation, not an ML result. An abstract reviewed is not a complete paper review. Missing numeric values are UNVERIFIED, never zero. N/A means the field does not apply. Keep original and superseding records.

## Assumptions to validate

| Assumption | How to establish it | Consequence if false |
|---|---|---|
| Downloaded files are the intended CIC-IDS2017 edition | Local path, archive/provenance, hashes, raw headers, per-file counts | Revise schema and dataset claims |
| Timestamps, hosts or session identifiers survive in the local edition | Inspect actual headers and parser samples | Weaken temporal/host-disjoint claims; assess available PCAP |
| Labels are usable for intended tasks | Published schedule, class support, artifact/label audit | Revise tasks or document exclusions before scoring |
| Shared feature semantics across clients | Feature definitions, units, extractor versions | Harmonize or reconsider horizontal FL |
| Available hardware supports repeated comparisons | CPU/RAM/GPU and pilot cost measurements | Reduce candidates, not evaluation integrity |
| Labels become available after deployment | Explicit delayed-label simulation | Do not claim autonomous learning from unlabeled new attacks |
| Local retention is permitted | State retention and deletion assumptions for replay | Include rehearsal-free candidates |
| The server may observe individual updates | Threat and protocol review | Locate privacy protection before that observation |
| Client identity corresponds to a research abstraction | Document partition generation | Never call synthetic clients real banks |
| Financial jurisdiction and institutional rules are known | User context and current official sources | Keep legal discussion contextual; no compliance claim |

User update: Local data root is C:\Users\nimma\Downloads\Datasets. A header-only inventory found CIC-IDS2017 plus four NF v3 datasets; the CIC headers lack fine-grained timestamps/IPs, while NF headers contain them. See reports/local-data-observations.md. Deadline is September 20 (assume 2026); resource and calendar constraints are in docs/deadline-plan.md. These resolve the path/hardware questions, but not provenance, timestamp validity, row quality or compute feasibility.

No fixed feature count, client count, model, epsilon, or architecture is justified yet.

## Adaptive process and decision gates

Research -> problem/threat definition -> candidates -> A0 -> preregistered validation experiment -> result and uncertainty -> accept/reject/inconclusive -> decision record -> architecture update -> integration -> re-evaluation -> final validation.

At every checkpoint: define goal, prerequisites, implementation scope, measurements and success criteria; implement only after prerequisites; validate; record experiment and failure history; record decision; update architecture and status. Passing a checkpoint requires its evidence, not elapsed time. Reopen an earlier choice when integration reverses rankings or violates the agreed resource/privacy envelope.

## Research questions

| ID | Question | Controlled evidence needed |
|---|---|---|
| RQ1 | Which feature/model combination provides the best detection and generalization trade-off? | Shared development splits; macro-F1, minority/per-class F1, worst-domain score, latency and memory |
| RQ2 | When does collaboration improve on independent local models, and which FL method handles heterogeneity best? | Centralized, local-only and FL; IID, label/quantity/domain skew; client distributions and communication |
| RQ3 | Which privacy mechanism matches the specified adversary and protected unit within resource limits? | Threat-to-mechanism mapping, formal assumptions, implementation verification and cost |
| RQ4 | How does privacy strength affect detection, especially rare attacks and weak clients? | Matched non-private controls; accountant-verified operating points; utility/overhead curves |
| RQ5 | Does sequential updating cause forgetting, and which CL candidate improves retention and new-task learning? | Frozen and naive sequential baselines; full task evaluation matrix; memory/time costs |
| RQ6 | What are the separate costs and benefits of federation, privacy and CL? | Centralized; local-only; FL; FL+privacy; FL+CL; FL+privacy+CL |
| RQ7 | How well does the selected system transfer to held-out clients, time periods and feasible external domains? | Preregistered unseen-domain protocols; fixed labels and semantic feature mapping |
| RQ8 | Do privacy, FL and CL interactions change the preferred component choices? | Matched integration ablations and limited alternate-component checks |

## Initial threat model: questions and provisional scope

The following are research questions, not assertions that the prototype already protects these assets.

1. Protected unit: one flow, session, person/device, or entire institution? One person's many correlated flows do not receive person-level protection from a single-flow guarantee.
2. Adversary: honest-but-curious coordinator, malicious coordinator, external observer, other clients, or collusion? What data, models and auxiliary knowledge can each access?
3. Outputs: individual updates, sums, model checkpoints, teacher logits, preprocessing statistics, label counts, metrics, participation and final models? The guarantee must cover the actual release transcript.
4. Trust boundary: who sees unnoised quantities; who adds and verifies noise; who holds keys; what minimum cohort and collusion/dropout assumptions apply?
5. Retention: can clients store historical flows, replay labels/logits, Fisher estimates or teacher models, and for how long?
6. Integrity: are poisoning, backdoors and adaptive malicious training in scope? Confidentiality controls do not establish robustness.
7. Lifetime: how do privacy losses compose across local steps, rounds, repeated tuning, sequential tasks, replay and model releases?
8. Deployment: is evaluation a single-machine simulation or independently isolated clients? File separation is not a verified security boundary against the machine owner.

[CURRENT DESIGN DECISION, provisional] Start analysis with honest clients and an honest-but-curious coordinator; assess leakage from outputs and updates. Analyze authenticated encrypted transport as a separate control. Consider a malicious server/collusion as extension scenarios before choosing a cryptographic protocol. Compromised endpoints, poisoning/backdoor resistance, denial-of-service tolerance and hardware side-channel defense are outside the initial implementation scope unless explicitly added by a decision record. This does not mean these threats are unimportant or prevented.

DP evaluation must specify adjacency and trust, not just report epsilon. Per-example DP-SGD at an institution can protect records before update transmission under its assumptions; this is not automatically client-level local DP for the entire institution. Central noise added by a coordinator does not conceal previously observed raw updates from that coordinator. Secure aggregation hides individual contributions under protocol assumptions, but the aggregate and resulting model remain observable. Review repeated differencing and small-cohort risks.

## Literature research plan

This is a structured literature review, not yet an exhaustive systematic review. Search original author/publisher pages, proceedings, official dataset sites, NIST, IMF, ENISA and relevant regulators. Use reviews only to discover primary work. Record search date/query, eligibility, exclusion reasons and reading depth. Check developments through 2026-09-08; distinguish foundational papers from recent results and preprints from peer-reviewed work.

| Workstream | Required coverage | Output before closing CP0 |
|---|---|---|
| Financial threat context | Ransomware, credentials/account takeover, DDoS, botnets/malware, lateral movement, web attacks, insiders, suppliers and fraud-related anomalies; confidentiality and information-sharing constraints | Threat/telemetry map; scoped statistics with geography, period and denominator; jurisdiction-specific official context |
| IDS foundations | Signature/anomaly/behavioral methods; host/network placement; payload/flow visibility; encryption; false positives; drift, imbalance, unknown attacks, adversarial limits | Detection requirements and observability limitations |
| FL | Centralized/local/distributed; cross-device/cross-silo; horizontal/vertical/transfer; FedAvg, FedProx, FedAdam/Yogi/Adagrad, SCAFFOLD, FedNova and justified personalization | Algorithm matrix with objectives, assumptions, experimental setup, convergence, quality and communication |
| Privacy | FL alone, local/central DP, sample/client adjacency, DP-SGD, secure aggregation, HE, SMPC, TEE and hybrids | Protection/assumption/utility/cost matrix; numerical extraction with setup; lifecycle accounting plan |
| CL | Data/concept drift; task/class/domain/online settings; naive fine-tuning, LwF, EWC, SI, experience/reservoir replay, DER/DER++, GEM/A-GEM, generative replay and isolation | Setting definition; retention/new-task/memory/privacy matrix |
| Datasets | CIC-IDS2017, CSE-CIC-IDS2018, UNSW-NB15, CIC-DDoS2019, TON_IoT, CTU-13 and justified newer options | Generation, year, attacks, benign data, PCAP/schema, labels, artifacts, leakage and suitability table |
| Models | Logistic Regression, RF, Extra Trees, XGBoost, LightGBM, feasible SVM; MLP, 1D-CNN, LSTM/GRU/CNN-LSTM, autoencoders and justified tabular/transformer methods | Representative shortlist; parameter/inference/training costs and FL/DP/CL compatibility |
| Existing integrations | FL+IDS, DP+FL+IDS, CL+IDS, FL+CL+IDS and full intersections | Claim-by-claim related-work matrix and conservative gap statement |

For numeric extraction record source table/page, dataset version, task, split, preprocessing, features, model, clients, partition, participation, seeds, metrics, privacy unit/accountant and hardware. Preserve units and whether an improvement is relative percent or percentage points. An abstract-level improvement is an author-reported claim pending table verification. Do not rank incompatible studies by accuracy.

CP0 stopping rule: every required workstream has credible source coverage; every shortlisted algorithm has its original method and a relevant empirical context; known competing integrated work is assessed; unverified values remain explicit; threat/split/metric/resource plans and A0 are coherent. Additional papers should resolve a decision or limitation, not merely inflate the reference count. These conditions are not yet met.

## Evaluation protocol M0.1 (planned, not implemented)

**Audit before assumptions.** Preserve files read-only. Record bytes/hashes, parser/encoding, original and normalized headers, duplicate headers, row counts, malformed rows, missing/nonfinite cells, class-by-file/day counts, inferred types, constant/near-constant features, identifiers and exact duplicates. Inspect raw headers before a dataframe parser silently renames duplicates. Retain metadata in restricted split/audit artifacts even if excluded from model inputs.

**Separation before fitting.** Establish training, development/selection and sealed final test membership before learned cleaning, imputation, scaling, feature selection or tuning. Basic schema/integrity inspection is permitted before sealing; no label-conditioned feature selection from test data. Group dependent sessions, duplicates and relevant time blocks where metadata permits. Use a declared embargo if flows/windows overlap boundaries. Predeclare a deterministic duplicate/conflicting-label policy. Record unavoidable dependencies and how missing metadata limits claims.

**Distinct evaluation questions.** A day holdout may exclude entire attack classes because of the scripted schedule. Separate known-class generalization, unseen-attack detection and class-incremental adaptation. Do not train Monday-only multiclass supervision and describe Tuesday attacks as ordinary known-class testing. Use group-disjoint known-class partitions only if sufficient independent support exists; otherwise narrow that claim. Random row splits cannot establish temporal or cross-institution generalization. No target-test fitting during external validation.

**Operational prediction task.** Consider binary alerting as a primary operational endpoint and multiclass attack-family attribution as a complementary endpoint. This is provisional, pending support audit. A closed-set classifier is not automatically an unknown-attack detector. Novelty detection and delayed-label retraining require separate protocols. Do not construct temporal sequences by reshaping an arbitrary feature vector.

**Preprocessing and privacy.** Fit training transformations only. Specify whether scalers and feature-selection statistics are local, based on public reference data, or securely aggregated. A centrally fitted scaler on pooled institution records violates a strict decentralized training claim unless it is an explicitly separate public-benchmark oracle. Data-dependent preprocessing, private validation, class weighting and sampling may need privacy analysis; an accountant for optimizer steps alone is not an end-to-end guarantee.

**Fair comparisons.** First retain a constant/prior classifier, representative classical models and a compact MLP; evaluate 1D-CNN if its feature locality is defensible. Candidate list is not final selection. Neural weight averaging does not directly apply to independently trained tree structures. Compare statistical quality against strong tree baselines, and choose a federatable family with its engineering trade-offs explicit. Predeclare bounded tuning budgets; record time as well as trial count. Use matched development partitions, seeds, information availability and stopping criteria. Centralized joint retraining with future-task data is an oracle reference, not a deployable continual competitor.

**Federation.** Partition only after split constraints are specified; preserve client assignment across comparable methods. Test an IID control plus label skew, quantity skew and justified domain skew. Dirichlet label allocation alone does not reproduce real banking heterogeneity. Save alpha, client count, client sizes, seeds, minimum-support rules and failed allocation attempts. Distinguish non-IID effects from partial participation/system-speed effects.

**Privacy.** If DP survives the threat review, use a validated framework with compatible modules and a correct sampling/accounting setup. Record adjacency, clipping norm, noise multiplier, sampling, total steps, epsilon, delta and accountant version per client/lifetime. Do not reset the privacy ledger after an FL round or CL task. Choosing delta requires a justified protected population and application, not a universal default. Replay changes sampling probabilities and dependence: do not reuse a fresh-batch accountant without analysis. Teacher/Fisher/logit computation on raw data is not automatically DP post-processing. An empirical attack that fails does not prove privacy; formal guarantees and attack measurements serve different purposes.

**Continual setting.** Start by evaluating frozen and naive sequential controls. A fixed-label domain-incremental experiment and a class-incremental new-family experiment answer different questions. No inference-time task identity unless explicitly labeled task-incremental. Maintain separate development and final evaluation panels at each stage; tuning uses development panels. Real label delay, changing clients and automatic drift detection are additional assumptions to assess, not completed capabilities.

**Metrics.** Preserve macro-F1, per-class precision/recall/F1 and support, worst-client/domain performance, minority-class results, confusion matrices, PR-AUC, FPR/FNR and secondary weighted-F1/accuracy. Define a fixed label universe and absent-class policy for each protocol; provide support-aware scores where useful without hiding unsupported classes. A single-class test slice has undefined discrimination metrics in some cases: report N/A, not fabricated AUC. Select alert thresholds on development data. Report expected false-alert volume only with explicit traffic volume/prevalence assumptions.

Let R[t,j] be the specified macro-F1 on evaluation task j after training stage t. Report the full matrix. For T tasks, use BWT = mean over j<T of (R[T,j]-R[j,j]); forgetting = mean over j<T of (max over k=j..T-1 R[k,j]-R[T,j]). Keep signs, including beneficial transfer; label any nonnegative-clamped variant separately. Forward transfer requires a defined pretraining/reference baseline and is omitted when not meaningful.

**Uncertainty and efficiency.** Aim for at least three seeds for key comparisons if feasible; report all runs and mean/SD. Choose additional runs based on a predeclared ambiguity/resource rule. Confidence intervals must respect grouping by independent domains/sessions; millions of correlated flows are not millions of independent replications. Measure end-to-end training, preprocessing, peak RAM/VRAM, inference batch size/device, and p50/p95 latency. Completed-flow feature availability adds detection delay beyond model inference. Count upload/download, auxiliary optimizer state, masks/keys and protocol retries; simulation byte estimates must be labeled estimates.

**Selection and stopping.** Use raw quality/cost/privacy metrics and a Pareto comparison; introduce a composite score only with predeclared weights. Establish practical effect margins and resource limits after initial development baselines, before confirmatory selection. Stop a family at its budget or when remaining candidates cannot answer an unresolved research question. Inconclusive results remain inconclusive. Final-test feedback must not reopen tuning on that same test; revisions require a new confirmatory evaluation plan or an explicit exploratory label.

## Full checkpoint roadmap

| CP | Goal and prerequisite | Required evidence / exit artifact |
|---|---|---|
| 0 | Research, questions, threats, methodology | Completed coverage matrix, conservative gap, protocol, provisional A0 with block contracts |
| 1 | Repository and environment after CP0 | Modular structure, reproducible environment, hardware inventory, version capture |
| 2 | Audit actual local dataset after path resolution | Dataset Audit Report, manifest/hashes, schema, label/quality statistics |
| 3 | Specify labels, groups and splits using audit | Versioned train/development/sealed-test manifest; overlap and support checks |
| 4 | Deterministic cleaning and training-only preprocessing | Quarantine ledger, preprocessing artifacts, leakage checks |
| 5 | Baseline and metric framework | Prior/logistic/tree/MLP pilot; metric sanity checks; feasible resource budget |
| 6 | Feature comparison across representative families | Feature comparison and selection record; no universal fixed feature count |
| 7 | Fair model comparison; revisit feature interaction | Detection, stability and cost table; provisional model decision |
| 8 | Client design and local-only baselines | Saved IID/non-IID partitions, support checks, per-client results |
| 9 | FedAvg research baseline | Verified aggregation, centralized/local/FL comparison |
| 10 | Shortlisted FL comparisons | Quality/convergence/client variance/bytes; FL decision |
| 11 | Privacy threat and mechanism comparison | Coverage, assumptions, DP/crypto/TEE feasibility and cost evidence |
| 12 | Implement chosen privacy candidates | Mechanism correctness, accountant or protocol checks, explicit guarantee |
| 13 | Privacy/utility optimization | Operating-point curves and privacy decision; revisit model if needed |
| 14 | CL setting, frozen and naive sequential baselines | Task streams, label assumptions, measured forgetting matrix |
| 15 | CL candidate comparisons | Retention/new-task/memory/time/privacy results and decision |
| 16 | Integrate selected components | Six core configurations with matched information and resources |
| 17 | Reopen choices and optimize integration | Regression investigations and alternate-component evidence |
| 18 | Ablations | Each claimed component benefit tied to a controlled comparison |
| 19 | Generalization on development domains | Held-out client/time plans; external schema feasibility if authorized |
| 20 | Freeze candidate and run untouched final evaluation | Seed results, intervals/limits, authoritative results and claim-evidence table; final architecture only if gates pass |
| 21 | Report/paper and reproducibility package | Verified methods/results, references, limitations, rerun instructions |
| 22 | Presentation, demonstration and defense | Accurate slides, 30/60/120-second explanations, viva answers tied to evidence |

Before A0 is issued, each block must specify input, operation, output, artifacts, trust, failures and alternatives. Diagrams must separate clients/server and training/inference, locate privacy before relevant disclosure, locate CL state at its real owner, and never show raw data moving to the production aggregator. No A0 diagram is issued in this initial protocol.

## Tracking and future repository layout

Research records contain the complete source schema in docs/registries/research.json, with verification depth and numeric extraction notes. Project records in docs/registries/project.json define full schemas for experiments, decisions, architecture, failures and claims. Use DATA/PREP/FEAT/MODEL/FL/PRIV/CL/INT/GEN/ABL/EFF IDs and statuses PLANNED, RUNNING, COMPLETED, FAILED, REJECTED, SUPERSEDED. Research tasks use separate RES IDs.

Each decision links source IDs and experiment IDs, alternatives, risks, confidence and revisit criteria. Each architecture links the decisions that changed it. Progress uses completed/current/next/blocked/deferred/rejected/needs-research/needs-validation. Keep a single authoritative final-results table, empty until actual results exist.

Proposed later structure: src/, scripts/, configs/, tests/, data/{raw,interim,processed,splits}/, artifacts/, experiments/, reports/, docs/. Do not mix raw data or model binaries with source. Preserve original data outside tracked code; document its local location. Suggested CP0 branch: codex/cp0-research-methodology; suggested commit purpose: establish research protocol and evidence registries. No branch/commit/push is claimed as completed here.

## First research task

RES-001: Map financial threats to observable network-flow evidence and define the threat boundary. Deliver a threat/telemetry matrix, source-qualified financial evidence, flow-visibility limitations and privacy questions. Continue with dataset validity and prior integrated work before proposing A0. This task has begun; full numerical paper extraction and all CP0 workstreams remain open.
