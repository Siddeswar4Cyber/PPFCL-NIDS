# CP0 comparative research and selection rationale

2026-09-08. Initial research gate for A0. This is a targeted primary-source review, not a systematic review or a claim to exhaust the literature. The research registry records verification depth and unknowns. Numerical excerpts and their experimental contexts live in [numerical evidence](CP0-numerical-evidence.md). No number in that report is our result.

## 1. Financial problem and observable threats

**LITERATURE EVIDENCE.** Financial institutions depend on available payment services, confidential customer information, credentials and interconnected providers. Sector incident reporting motivates collaboration, but it does not make benchmark traffic representative of banks. ENISA's European sample and the IMF's financial-stability analysis have different populations and denominators; neither supplies our expected attack rate. [ENISA finance report](https://www.enisa.europa.eu/sites/default/files/2025-02/Finance%20TL%202024_Final.pdf), [IMF analysis](https://www.imf.org/en/Blogs/Articles/2024/04/09/rising-cyber-threats-pose-serious-concerns-for-financial-stability).

**CURRENT DESIGN DECISION.** Simulate horizontal, cross-silo collaboration among logical institutions. This models institutions sharing feature definitions while retaining different records. It does not establish institutional representativeness, operational readiness or regulatory compliance. Different institution feature spaces would require an explicit vertical/transfer-learning problem, which A0 does not solve.

| Threat | Potential flow evidence | What the system still needs elsewhere |
|---|---|---|
| DDoS and scanning | Rates, fan-out if computed over genuine groups, flags, packet/byte asymmetry | Capacity context, service availability and attribution |
| Credential guessing and account takeover | Repeated connections and timing may indicate automation | Authentication results, identities, MFA and application sessions; a valid stolen login can look normal |
| Botnets, malware and ransomware | Beaconing, unusual destinations, transfer patterns, lateral scanning | Endpoint evidence and payload/application analysis; encryption or file damage is not a flow label |
| Lateral movement and insiders | Changed communication patterns and unusual internal access | Asset roles, authorization and host history; an allowed connection can be malicious |
| SQL injection, XSS and other web attacks | Some traffic patterns may correlate with an attack campaign | Request semantics and application/WAF logs; flow statistics cannot establish the injected content |
| Supply-chain compromise | Unusual provider communication or subsequent movement | Vendor provenance and software integrity |
| Fraud-related activity | Unusual network access can support an investigation | Transactions and business rules; detecting an attack flow is not detecting financial fraud |

This table is an engineering observability analysis, not a claim that each benchmark contains each threat. Collaboration requires common schemas, authenticated participants, versioned updates, accountable access, limited retention and measured alert workload. Pooling raw security logs can disclose internal topology, user activity and operational details; FL reduces routine raw-record transfer but introduces model/update disclosure.

The Indian RBI IT governance direction and the EBA DORA materials provide relevant examples of security governance, resilience and third-party accountability. Jurisdiction has not been selected, and this review does not establish current institution-specific obligations or compliance. [RBI direction issued November 2023](https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D12562%283%29.html), [EBA operational resilience](https://www.eba.europa.eu/regulation-and-policy/operational-resilience).

## 2. Detection method and deployment limits

Signature detection matches known indicators; anomaly detection estimates deviation from a reference distribution; behavior detection models patterns over observations. These overlap rather than forming mutually exclusive products. Host IDS sees endpoint activity; network IDS sees communications. Payload inspection offers application evidence but may be constrained by encryption and confidentiality. Flow summaries retain timing, size and transport behavior without reading application content, at the cost of lost semantics. [NIST SP 800-94](https://csrc.nist.gov/pubs/sp/800/94/final).

**CURRENT DESIGN DECISION.** Use existing labeled flow tables for offline supervised detection first. The interface will output a score and thresholded alert, with model/schema versions. This does not implement live flow extraction. Completed-flow features can require waiting for the flow to finish: prediction latency alone is not end-to-end detection latency. Encrypted traffic can still expose metadata, but changed encryption, applications or capture equipment can shift the distribution.

False positives must be measured as benign false-positive rate and alerts per unit traffic; precision changes with deployment prevalence. Report rare-family recall even for the binary detector. A high overall accuracy on mostly benign traffic is weak evidence. Unknown attacks are an explicit withheld-family evaluation, not an automatic consequence of anomaly scoring. Data drift means changed inputs; concept drift means changed predictive relationships. Malicious evasion, label poisoning and backdoors are separate from naturally occurring drift and remain outside A0's protection claims.

## 3. Dataset comparison and local strategy

**LITERATURE EVIDENCE.** Original dataset pages establish traffic-generation context and formats; they do not certify our local copies. The detailed local inventory contains only file metadata and headers. No local row totals, label frequencies, duplicates or timestamp validity have yet been computed.

| Dataset | Origin, labels and available modalities | Suitability and principal limitation |
|---|---|---|
| CIC-IDS2017 | 2017 controlled enterprise-style traffic; benign and scheduled attacks; original PCAP and labeled flow CSV offerings | Required baseline. Known flow/label construction problems warrant audit. Local eight CSVs have no timestamp/IP/Flow ID, so fine temporal or host-disjoint claims cannot be made from them |
| CSE-CIC-IDS2018 | 2018 controlled attack/benign scenarios, original captures and flow features | Useful larger related domain; shared collection methodology limits independence. Local copy is a NetFlow v3 re-extraction, not the original feature CSV |
| UNSW-NB15 | 2015 laboratory hybrid normal/attack generation; original capture, derived features and nine attack categories | Smaller local NetFlow candidate for pilots. Original and re-extracted counts/features must not be interchanged |
| CIC-DDoS2019 | 2019 DDoS-focused controlled traffic; capture and flow offerings | Relevant availability-threat benchmark and FL literature source; limited attack scope. Not among the five inspected local CSV families; no download planned |
| TON_IoT | IoT/IIoT testbed with network, operating-system and telemetry modalities | Network-only v3 offers domain-shift testing; do not concatenate other modalities by row. IoT environment differs from financial networks |
| CTU-13 | 2011 malware scenarios; labeled bidirectional flows and capture availability varying by traffic subset | Botnet transfer candidate. Background traffic is not interchangeable with confirmed benign; labels and feature extraction differ. No download planned |
| BoT-IoT | 2018 IoT testbed; benign and generated attack traffic | Already available in v3. Published extreme attack prevalence makes it a useful shift stress test, a poor stand-in for bank prevalence |
| NetFlow v3 family | Later common extraction of older benchmark captures, including timing fields | Shared headers enable investigation of common features; not proof of equal semantics, units, label quality or newer attack behavior |

Sources: [CIC2017](https://www.unb.ca/cic/datasets/ids-2017.html), [CIC2018](https://www.unb.ca/cic/datasets/ids-2018.html), [UNSW](https://research.unsw.edu.au/projects/unsw-nb15-dataset), [CICDDoS2019](https://www.unb.ca/cic/datasets/ddos-2019.html), [TON](https://research.unsw.edu.au/projects/toniot-datasets), [CTU13](https://www.stratosphereips.org/datasets-ctu13), [BoT-IoT](https://research.unsw.edu.au/projects/bot-iot-dataset), [NetFlow author site](https://staff.itee.uq.edu.au/marius/NIDS_datasets/), [CIC2017 troubleshooting](https://intrusion-detection.distrinet-research.be/WTMC2021/).

**CURRENT DESIGN DECISION.** Keep a CICFlowMeter baseline track and a separate NetFlow temporal/generalization track. Audit all five local datasets in chunks. Use NF-UNSW first for resource pilots, subject to label and time support. Reserve NF-CIC2018 for external testing; ToN/BoT are optional additional frozen external domains if resources allow. No pooling across the two schema families. No training on a declared external test domain.

The v3 paper's feature-count description differs from the inspected files; published totals also need reconciliation against local data. The local dictionary has repeated/misleading descriptions for some directional duration/IAT fields. Quarantine semantically unresolved fields from cross-domain inference until checked; do not silently alter data to match prose. [Temporal analysis paper](https://arxiv.org/html/2503.04404v3).

## 4. Model candidates

Parameter count is architecture dependent, not a property of the model name. With d inputs and c outputs, multinomial logistic regression has (d+1)c parameters; a two-hidden-layer MLP of widths h1,h2 has (d+1)h1+(h1+1)h2+(h2+1)c. A0's trial h1=64,h2=32 is a resource hypothesis. Tree node count/serialized bytes and SVM support vectors are more useful size measures than forcing them into neural parameter counts.

| Candidate | Fit to flow tables and cost | FL / DP / CL implications and A0 treatment |
|---|---|---|
| Logistic regression | Low-cost linear reference; scaling and interactions matter | Gradient averaging, per-example clipping and incremental updates are straightforward; retain as baseline |
| Random Forest | Nonlinear interactions, weak dependence on scaling; memory grows with nodes | Trees cannot be averaged as neural weights; use centralized/local benchmark, not fake FedAvg |
| Extra Trees | Strong randomized-tree alternative; controlled depth can limit memory | Same federation caveat; first tree pilot, retain RF as challenger if time permits |
| XGBoost | Boosted trees, nonlinear tabular reference; depth/round budget matters | Federated/private tree methods need separate protocols; benchmark only in A0 |
| LightGBM | Efficient boosting candidate, distinct tuning and sampling choices | Defer as redundant tree family unless XGBoost/runtime pilot warrants replacement |
| Linear/kernel SVM | Linear version is feasible reference; kernel training and support-vector inference can become expensive | Kernel model aggregation is not FedAvg. Kernel variant deferred beyond a small justified sample |
| MLP | No assumption that neighboring feature columns are spatial neighbors; modest dense layers | Primary neural integration candidate, not declared strongest detector; clean baseline for FL and per-example DP |
| 1D-CNN | Convolution assumes useful locality/weight sharing along its input | Conditional challenger only after a defensible feature ordering and permutation control; arbitrary CSV order is inadequate |
| LSTM / GRU | Can use histories if ordering and entity grouping are real | Require sequence construction, temporal split and privacy-unit reconsideration; no reshaping one row into a fictitious time series |
| CNN-LSTM | Adds convolution plus sequential state and substantial tuning | Defer until both component assumptions independently survive tests |
| Autoencoder variants | Useful benign-reference anomaly baseline; reconstruction error needs calibration | FL gradients possible; contaminated benign training, memorization and threshold drift are concerns; conditional unknown-attack study |
| Tabular transformer / residual tabular net | Interactions without simple feature locality; more configurations and memory | Possible neural challenger after MLP baseline; defer under deadline unless a clear gap remains |

Strong tree baselines are necessary: tabular benchmark research does not establish universal neural superiority. IDS feature-representation results also show how weighted F1 can conceal minority failure (N05). Modern tabular comparisons motivate representative alternatives, not a transfer of published rankings. [Tabular benchmark](https://arxiv.org/abs/2207.08815), [standard NetFlow features](https://arxiv.org/html/2101.11315v2), [XGBoost](https://arxiv.org/abs/1603.02754), [LightGBM](https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html), [tabular neural study](https://arxiv.org/abs/2106.11959), [ensemble documentation](https://scikit-learn.org/stable/modules/ensemble.html), [SVM documentation](https://scikit-learn.org/stable/modules/svm.html).

Kitsune provides an online autoencoder IDS reference, but its feature pipeline is not equivalent to feeding arbitrary benchmark rows into an autoencoder. Its result cannot stand in for our latency or unknown-attack detection. [Kitsune](https://arxiv.org/abs/1802.09089). No verified comparable IDS score or parameter count has been extracted for every neural candidate; these remain unverified rather than invented.

## 5. Federation comparison

Centralized learning pools records and supplies a research comparator. Local-only learning never collaborates. Distributed learning is the wider category of computation spread across workers, often under one data center's control. FL specifically keeps training data at clients while coordinating learning. Cross-device designs target many intermittently available devices; cross-silo collaboration is the closer institutional scenario. A0's logical clients run sequentially on one laptop: this tests algorithmic partitions, not independent organizations or real network latency.

Statistical heterogeneity includes label, feature and conditional distribution differences; systems heterogeneity includes speed, availability and local work. Partial participation changes who contributes per round. More local epochs can reduce communication but increase client drift. Unequal client sizes affect whether sample-weighted utility or equal-institution utility is optimized.

| Method | Mechanism and hypothesis | Cost/failure and decision |
|---|---|---|
| FedAvg | Sample-weighted average of compatible local models | Minimal common baseline; heterogeneity can degrade convergence |
| FedProx | Penalizes departure from the round's global model | Adds proximal strength tuning; can under-adapt. Core challenger, not default winner |
| FedAdam | Server adaptive first/second moments on aggregate updates | Extra server state and learning-rate tuning; core challenger |
| FedYogi | Changes adaptive second-moment evolution | Reserve if FedAdam is unstable; not a separate full grid by default |
| FedAdagrad | Accumulates squared server updates | Reserve comparison; shrinking effective steps can hinder later adaptation |
| SCAFFOLD | Uses client/server control variates to correct drift | Additional persistent state and communication; reserve if heterogeneity failure persists |
| FedNova | Normalizes effects of unequal local optimization work | Relevant when varying steps/epochs; defer if all clients have fixed work |
| Personalized FL / FedPer | Shared representation with local prediction head | May improve institution fit but weakens one-global-model comparison and raises unseen-client evaluation questions; reserve after measured global/local gap |

Sources: [FedAvg](https://proceedings.mlr.press/v54/mcmahan17a.html), [FedProx](https://arxiv.org/abs/1812.06127), [FedOpt](https://arxiv.org/abs/2003.00295), [SCAFFOLD](https://proceedings.mlr.press/v119/karimireddy20a.html), [FedNova](https://arxiv.org/abs/2007.07481), [FedPer](https://arxiv.org/abs/1912.00818).

N02 supplies a particularly relevant counterexample to assuming FedProx wins on IDS; N03 supplies a different adaptive-optimization result on images. Their different metrics, clients and tuning prevent a cross-paper league table. [Recent IDS comparison](https://arxiv.org/html/2509.17836v1). Our comparison holds model, initialization, sampled clients, data access budget and validation policy constant, while giving each method a documented tuning budget.

## 6. Privacy comparison and threat model

**CURRENT DESIGN DECISION.** Analyze honest clients, trusted local training processes, and an honest-but-curious coordinator that sees all transmitted messages. The proposed protected unit is one curated training flow record; it is not a person, account, host or institution. Repeated flows from a person may require group-level analysis with weaker protection. The laptop simulator itself can access all files; it supplies no process-isolation guarantee.

DP bounds how much a randomized release distribution can change between neighboring datasets. Epsilon and delta define this bound together with adjacency and the mechanism. Delta is not simply a universal probability that privacy is broken. A guarantee must state whose records, which outputs and what repeated accesses it covers. Model inversion and membership inference are empirical risks; a failed attack is not proof of privacy. [NIST SP 800-226](https://csrc.nist.gov/pubs/sp/800/226/final), [gradient leakage study](https://arxiv.org/abs/1906.08935).

| Mechanism | Protected surface / assumptions | Utility and cost; CL compatibility; A0 disposition |
|---|---|---|
| FL alone | Avoids routine raw-record upload; server sees updates | No formal privacy guarantee; low integration cost. Non-private baseline |
| Central DP | Trusted curator sanitizes a release | Noise/utility trade-off; does not protect updates already seen by that curator. Wrong boundary if coordinator is the adversary |
| Record-level DP-SGD inside each client | Clips per-record gradients and adds calibrated noise before any update leaves the trusted local process | Per-example gradient overhead; lifetime accounting required. Candidate for server-visible transcript privacy, subject to implementation review |
| Client-level DP | Adjacent datasets differ by an institution's contribution; typically clips/noises client updates | Different and stronger protected unit for institutional participation; few institutions can make utility difficult. Defer, do not relabel record-level DP |
| Local DP at each individual data owner | Each individual randomizes before an untrusted collector | Strong collector boundary, often high noise; a trusted bank running per-record DP-SGD is not this individual-local model |
| Secure aggregation | Coordinator obtains an aggregate under protocol thresholds and collusion/dropout assumptions | Hides individual updates but not aggregate/model inference; quantization and extra messages. Optional separate cryptographic extension |
| Homomorphic encryption | Computation over ciphertext, with selected key ownership/decryption policy | Ciphertext/arithmetic overhead; plaintext output still leaks. CL possible but expensive and protocol-specific; research comparison only |
| SMPC | Joint computation via secret shares under corruption-threshold assumptions | Interactive communication and multi-party engineering; output leakage remains. Research comparison only |
| TEE | Isolates computation assuming trusted hardware, attestation and implementation | Hardware availability, side channels and rollback matter; not statistical privacy. Research comparison only |
| Hybrid | Separately combines transport security, aggregation confidentiality and/or DP | Guarantees compose only with compatible trust and noise assumptions; more failure modes. No automatic sum of advertised protections |

Sources: [DP-SGD](https://arxiv.org/abs/1607.00133), [secure aggregation](https://acmccs.github.io/papers/p1175-bonawitzA.pdf), [POSEIDON](https://www.ndss-symposium.org/ndss-paper/poseidon-privacy-preserving-federated-neural-network-learning/), [ABY3](https://eprint.iacr.org/2018/403), [Slalom](https://arxiv.org/abs/1806.03287). N06 keeps their numerical overhead claims tied to original baselines; no universal multiplier is asserted.

Implementation feasibility references: [Opacus PrivacyEngine](https://opacus.ai/api/privacy_engine.html) and [Flower secure aggregation example](https://flower.ai/docs/examples/flower-secure-aggregation.html). Their availability does not prove our accounting, Windows compatibility or protocol security. Do not execute example dataset downloads.

**Privacy integration rule.** No release is labeled private until adjacency, sampling, clipping, noise, accountant and complete transcript have been checked. Server-side aggregation is post-processing only of already protected messages. Do not claim additional client-sampling amplification when participant identities are visible without a matching theorem. Metadata, exact data-dependent sample weights, private validation scores and non-private preprocessing statistics are releases too. A0 uses fixed public client weights in confirmatory privacy comparisons and avoids logging private counts or raw examples to the server.

For privacy-confirmatory runs, hyperparameters/transforms must be fixed from a disjoint public reference population or use an explicitly budgeted private procedure. A public benchmark permits development, but that does not justify an end-to-end private claim for a workflow that inspected its entire simulated private population. A0's proposed guarantee is conditional on curated inputs and public configuration; raw-data audit/curation is outside that boundary and must be disclosed. No epsilon resets across rounds/tasks or selective reporting of the best private run without accounting for its selection/release path.

Replay repeats protected records and changes sampling. EWC/SI importance state and non-private teachers can create additional dependencies on old records. A previous DP teacher may be used as post-processing, but current-record contributions to the combined distillation loss still need per-example clipping and accounting. No CL candidate inherits privacy merely by being wrapped in a DP optimizer.

In scope: formal record contribution protection against the observing coordinator if the gate passes; optional empirical membership attack; honest execution. Out of scope: malicious coordinator queries, compromised clients, poisoning/backdoors, traffic-analysis leakage, denial of service, raw endpoint compromise and person-level protection. TLS/authentication are future deployment requirements, not implemented by a local simulation.

## 7. Continual-learning alternatives

**CURRENT DESIGN DECISION.** Primary setting: sequential domain/time adaptation with fixed binary labels, and no task ID at inference. Add a separate withheld-attack/family analysis. Multiclass class-incremental experiments require a frozen label ontology and explicit head expansion; a binary detector encountering a new attack family is not automatically class-incremental learning. Task-incremental evaluation gives the learner task identity and is an easier, separate question. Online CL limits passes as data arrive; our finite task/round simulation is not automatically online. [Three scenarios](https://arxiv.org/abs/1904.07734).

| Method | Retention mechanism and requirements | Risk / A0 treatment |
|---|---|---|
| Frozen model | No adaptation; stable old weights | Essential drift reference; cannot learn new behavior |
| Naive fine-tuning | Train on current task only | Essential forgetting baseline |
| LwF | Match previous model outputs while fitting current labels | Teacher may be poor on shifted inputs; extra model/forward pass. Core challenger |
| EWC | Penalize changes to important previous parameters | Importance estimate may be poor; extra parameter state and estimation. Core challenger |
| SI | Accumulate importance along optimization trajectory | Requires correct local state through federated rounds; reserve |
| Experience replay / reservoir | Rehearse retained examples; reservoir controls stream inclusion | Strong simple baseline, but stores raw records and needs retention/access policy. Core non-private challenger |
| DER | Replay stored logits to preserve old outputs | Buffer adds logits and computation; reserve after ER |
| DER++ | Combine replay distillation with labeled replay loss | More tuning and storage; reserve after ER |
| GEM | Constrain updates using previous-task gradients | Multiple gradients and quadratic-program overhead; defer |
| A-GEM | Use an average replay-gradient constraint | Lower constraint overhead but extra gradient and retention; reserve if ER interference is clear |
| Generative replay | Learn a generator for old synthetic examples | Generator can forget or disclose training information; synthetic does not imply private. Defer |
| Parameter isolation | Preserve old parameters/columns and add capacity | Memory grows; task routing may violate unknown-task inference. Defer |

Sources: [LwF](https://arxiv.org/abs/1606.09282), [EWC](https://arxiv.org/abs/1612.00796), [SI](https://proceedings.mlr.press/v70/zenke17a.html), [DER/DER++ comparison](https://arxiv.org/html/2004.07211v2), [GEM](https://arxiv.org/abs/1706.08840), [A-GEM](https://arxiv.org/abs/1812.00420), [generative replay](https://arxiv.org/abs/1705.08690), [progressive networks](https://arxiv.org/abs/1606.04671).

N04 motivates rehearsal testing but reports image accuracy, not IDS forgetting or DP utility. Our retention comparison records task-by-task scores, new-task learning, backward transfer and memory bytes. Forward transfer requires pre-training evaluation against an untrained/common reference; it cannot be inferred from final accuracy. FL adds state-placement choices: keep buffers and importance estimates local, define absent-client return behavior, and never average private buffers or task identities into the global model.

## 8. Defensible gap, decision gates and coverage

The intersection review distinguishes what was actually verified from what a title suggests:

| Prior work | Verified intersection | Implication for our claim |
|---|---|---|
| R026, 2025 FL comparison | FL + IDS under unequal/non-IID clients | Comparing aggregators on IDS is already established |
| R020, 2021 cohort study | FL + DP + CL + IDS, with the source's particular curator/cohort setting | The full combination is prior art; our different boundary requires independent validation |
| R051, NeurIPS 2023 | Supervised binary CL + IDS; replay and minority-imbalance methods | Replay/imbalance research is established. Its synthetic task construction is not proof of natural chronological drift [paper](https://papers.nips.cc/paper_files/paper/2023/file/3755a02b1035fbadd5f93a022170e46f-Paper-Conference.pdf) |
| R052, 2024 IIoT study | Publisher abstract confirms federated continual representation learning for IDS | FL + CL for evolving attacks is established; DP, exact clients and split details remain unverified [publisher](https://doi.org/10.1016/j.engappai.2024.108826) |
| R053, 2026 domain-incremental study | Publisher excerpts compare regularization and replay across multiple IDS datasets and neural models | Even systematic CL component comparison is prior work; see N08 for qualified numeric context [publisher](https://doi.org/10.1016/j.asoc.2026.116022) |
| R054, August 2026 preprint | Abstract investigates transformer/replay IDS and buffer attacks | Buffer integrity is a relevant limitation. Its near-perfect accuracy claims are not adopted without split/attack-method review [preprint](https://arxiv.org/abs/2608.04602) |

R052/R053 direct full-page retrieval returned access errors; publisher search excerpts support the limited claims above. R054 remains abstract-level screening. R051's original PDF method/task sections were reviewed; exact reproduction remains separate. These findings strengthen the bounded capstone rationale while weakening broad novelty claims. No claim that these papers lack a mechanism is inferred merely because it is absent from an excerpt.

**LITERATURE EVIDENCE.** Integrated federated privacy and CL IDS work already exists; N01 records a direct example and its utility loss. [Chathoth et al.](https://arxiv.org/html/2101.09878v1). Therefore “first FL+DP+CL IDS” is not a defensible claim.

**HYPOTHESIS.** A useful contribution is a reproducible comparison of detection, minority performance, forgetting, privacy scope and resource cost under audited splits, followed by evidence-driven integration. The selected prior examples do not establish a universal optimum for our local data, threat boundary and laptop budget. This is an experimental and engineering contribution; no new algorithm or comprehensive absence-of-prior-art claim is established.

The eight research questions in M0.1 remain in force. A0 adds gates: (G1) provenance and valid split support; (G2) strong classical versus neural baseline; (G3) measured heterogeneous FL benefit; (G4) valid privacy mechanism and usable trade-off; (G5) retention versus new learning; (G6) interaction ablations and untouched external/final tests. A component survives only if its controlled evidence and engineering cost justify it. A weak integrated result is reportable; it is not a reason to tune on the final test.

| Required workstream | Initial research output | Remaining empirical or specialist work |
|---|---|---|
| Finance / NIDS | Sections 1-2, R001-R003/R047-R048 | Real institutional prevalence, deployment and jurisdiction not established |
| Datasets | Section 3, local inventory, N07 | Row audit, provenance reconciliation and split construction |
| Models | Section 4, N05 | Local parameter/node counts, runtime and controlled metrics |
| FL | Section 5, N02-N03 | Common-budget client experiments; selected-code review |
| Privacy | Section 6, N01/N06 | Mechanism/accountant proof boundary, tests and measured cost |
| CL | Section 7, N04 | Valid task support, score matrix and privacy integration |
| Integrated gap | Section 8 intersection matrix, N01/N08 | Ablations; external results; update recent literature before final submission |

The initial research gate is satisfied for issuing a **provisional** A0. Exact reproduction configurations and additional numeric results for deferred methods are not verified; they are not needed to declare a winner because no winner is declared. Implementation and final-design gates remain open.
