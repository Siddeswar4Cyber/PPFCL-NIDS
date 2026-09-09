# CP0 initial evidence and implications

Historical screening snapshot. The later [comparative review](CP0-comparative-review.md) and [numerical extractions](CP0-numerical-evidence.md) supersede its pending-work list. Provisional A0 is now issued; neither document contains our model results.

2026-09-08 | Initial source screening, not a completed literature review

No full dataset audit or model experiment has run. All numerical values below are literature evidence. Source abstracts and official pages were screened; detailed experimental tables still require extraction. The structured research registry records this distinction. A subsequent header-only local inventory is recorded separately in local-data-observations.md: the user already has four derived NetFlow v3 datasets as well as CIC-IDS2017. The external source descriptions below describe dataset families and must not be mistaken for the schemas of those derived local editions.

## Financial motivation

[LITERATURE EVIDENCE] ENISA's February 2025 finance-sector report analyzed 488 publicly reported incidents affecting European finance from January 2023 through June 2024. This is an observed report sample, not all incidents worldwide or a rate per institution. [R001: ENISA report](https://www.enisa.europa.eu/sites/default/files/2025-02/Finance%20TL%202024_Final.pdf).

[LITERATURE EVIDENCE] The IMF's April 2024 analysis reports that nearly one-fifth of incidents in its analysis affected financial firms and describes systemic pathways through confidence loss, disrupted critical services and interconnectedness. Do not equate this denominator with ENISA's sample. [R002: IMF analysis](https://www.imf.org/en/blogs/articles/2024/04/09/rising-cyber-threats-pose-serious-concerns-for-financial-stability).

[CURRENT DESIGN DECISION] Use this evidence to motivate collaborative detection and confidentiality requirements. Do not use benchmark F1 to calculate avoided fraud losses. A network-flow detector is one part of a defense system; finance-specific transactions, identity and endpoint evidence lie outside its input unless deliberately added.

## What telemetry can support

NIST's IDPS guide distinguishes network, host, wireless and network-behavior systems; it is foundational 2007 guidance, not a current product benchmark. [R003: NIST SP 800-94](https://csrc.nist.gov/pubs/sp/800/94/final).

The following is a technical assessment to test, rather than a promise of detection. A flow normally summarizes a network conversation through values such as packet sizes, duration and timing. Supervised flow classification and anomaly scoring are distinct approaches. A supervised label classifier does not acquire zero-day detection merely because its model is neural.

| Threat | Potential flow signal (hypothesis) | Evidence outside flow statistics / limitation |
|---|---|---|
| DDoS/DoS | Volume, rates, fan-in and timing | Low-rate application attacks can resemble legitimate traffic; completed-flow statistics add delay |
| Brute force/credential abuse | Repeated short sessions and periodic attempts | Success/failure and user identity need authentication/application logs; per-flow rows may miss cross-flow repetition |
| Botnet/malware | Beaconing, unusual peers or traffic asymmetry | Legitimate scheduled services can look similar; endpoint evidence needed to establish malware |
| Lateral movement | New internal connections and scanning | Requires an appropriate observation point and host/context metadata; isolated flow rows may be insufficient |
| SQL injection/XSS | Correlated request timing or response-size changes | Flow statistics cannot establish query/script semantics or prove exploit success; web/payload logs are needed |
| Ransomware | Scanning, propagation or exfiltration-related traffic | Local encryption may be invisible to a network-only detector |
| Account takeover/fraud | Unusual network usage in some cases | A valid-looking login or fraudulent transaction may have ordinary flow behavior |
| Insider/supply-chain activity | Changed destinations or transfer behavior | Authorized traffic may be malicious in intent; provenance and identity context matter |

[CURRENT DESIGN DECISION] Retain flow-based NIDS as the research focus because the available benchmark supports it. Validate observability and feature availability; do not claim complete attack coverage. Encrypted payloads constrain semantic inspection but do not remove every timing/size signal. Conversely, flow metadata is not inherently non-sensitive. The financial threat-to-telemetry map remains a research artifact under development.

## Dataset validity takes precedence over model choice

[LITERATURE EVIDENCE] CIC-IDS2017 was captured over five days, July 3-7, 2017; Monday contains benign traffic and attack schedules occupy the other days. Its official documentation describes CICFlowMeter features and general intrusion scenarios, not actual banks. [R004: original dataset documentation](https://www.unb.ca/cic/datasets/ids-2017.html).

[LITERATURE EVIDENCE] Engelen, Rimmer and Joosen document problems in flow construction, feature extraction and labeling; their supporting material explains how flow-direction handling can produce incorrect labels. These findings establish an audit requirement, not that every local edition has every reported defect. [R005: original research](https://intrusion-detection.distrinet-research.be/WTMC2021/), [supporting analysis](https://intrusion-detection.distrinet-research.be/WTMC2021/extended_doc.html).

[CURRENT DESIGN DECISION] Do not publish stock row/feature counts as our local counts. Preserve metadata for grouping, audit duplicate headers before normalization, and inspect attack support by day. Day holdout and unseen-class evaluation must be distinguished. Where CSV-only data cannot support a correction, disclose the limitation instead of inventing repaired ground truth.

External dataset screening is preliminary and no data have been downloaded:

| Dataset | Evidence seen | Possible role and unresolved issue |
|---|---|---|
| CSE-CIC-IDS2018 | Official page describes captured network traffic, machine logs and CICFlowMeter-V3 features | Related-family transfer; shared generator artifacts may limit independence; exact semantic schema audit required [R016](https://www.unb.ca/cic/datasets/ids-2018.html) |
| UNSW-NB15 | Original dataset page located | Independent generator/domain candidate; feature and label alignment still to extract [R017](https://research.unsw.edu.au/projects/unsw-nb15-dataset) |
| CIC-DDoS2019 | Official DDoS dataset and taxonomy page | Focused DDoS transfer rather than validation of every attack family [R018](https://www.unb.ca/cic/datasets/ddos-2019.html) |
| TON_IoT | Official page describes IoT/IIoT telemetry, OS data and network data including PCAP/Zeek | Use network modality if relevant; IoT domain is not banking and features differ [R019](https://research.unsw.edu.au/projects/toniot-datasets) |
| CTU-13 | Original laboratory overview describes 13 malware captures; Botnet, Normal and Background labels; Argus flows | Botnet-focused evaluation; Background is not verified benign; full PCAP availability differs by traffic category [R021](https://www.stratosphereips.org/datasets-overview) |

Do not align external features merely by spelling. Check measurement definitions, directions, units, timeouts and extraction versions. Full per-dataset year/generation/class/imbalance/artifact inventories, including newer candidates, remain pending.

## Federation: a baseline and several competing hypotheses

[LITERATURE EVIDENCE] FedAvg's original study reports 10-100 times fewer communication rounds than synchronized SGD in its evaluated settings. This is neither NIDS F1 nor a promised speedup on this project. [R006: McMahan et al., 2017](https://proceedings.mlr.press/v54/mcmahan17a.html).

FedProx addresses heterogeneous local optimization; SCAFFOLD corrects client drift with control variates; FedAdam/FedYogi/FedAdagrad apply adaptive server optimization. These provide distinct candidates, not a universal ranking. [R007: FedProx](https://arxiv.org/abs/1812.06127), [R008: SCAFFOLD](https://proceedings.mlr.press/v119/karimireddy20a.html), [R009: adaptive federated optimization](https://arxiv.org/abs/2003.00295).

[CURRENT DESIGN DECISION, provisional] Cross-silo horizontal FL is the first deployment hypothesis if a modest number of institutions share feature semantics while holding different records. Vertical FL would require complementary features about aligned entities; cross-device FL emphasizes much larger device populations. Client count and partition design await resources and data audit. FedAvg is a candidate control; FedNova and personalization still require primary-source extraction.

## Privacy choices protect different surfaces

[LITERATURE EVIDENCE] Deep Leakage from Gradients demonstrates reconstruction from shared gradients in image/text experiments. It invalidates a general claim that gradients are safe; it does not establish the success rate of reconstruction from our future multi-step NIDS updates. [R010: Zhu et al., 2019](https://arxiv.org/abs/1906.08935).

DP-SGD is grounded in randomized learning with privacy accounting; NIST's 2025 guidance highlights hazards when a mathematical guarantee is implemented. [R011: Abadi et al.](https://arxiv.org/abs/1607.00133), [R012: NIST SP 800-226](https://csrc.nist.gov/pubs/sp/800/226/final).

[LITERATURE EVIDENCE] Bonawitz et al. report secure-aggregation communication expansion of 1.73x for 2^10 users and 2^20-dimensional vectors, and 1.98x for 2^14 users and 2^24-dimensional vectors, using 16-bit input values. These large-population conditions do not predict overhead for a small cross-silo prototype. [R013: original CCS 2017 paper, abstract](https://acmccs.github.io/papers/p1175-bonawitzA.pdf).

The following is an initial mechanism taxonomy. Protocol-specific guarantees and measured costs require further research before selection.

| Mechanism | Intended protection | Remaining exposure / research gate |
|---|---|---|
| FL alone | Keeps training records at clients by design | Updates/models can leak; no automatic formal DP guarantee |
| Sample-level DP | Bounds dependence on one specified record | Does not imply institution/person-level protection; accounting and all releases matter |
| Client-level DP | Bounds dependence on an institution/client's entire contribution under defined adjacency | Utility feasibility with few institutions; weighting/sensitivity/cohort assumptions |
| Local vs central DP | Different placement of trust and randomization | Local/central is a trust distinction; sample/client is a separate adjacency distinction |
| Secure aggregation | Hides individual contributions while exposing an aggregate under protocol assumptions | Aggregate/model inference, small cohorts, collusion and repeated differencing |
| HE | Computation on encrypted values within a chosen scheme | Key holder/threshold trust, allowed output, numeric encoding and ciphertext cost; source extraction pending |
| SMPC | Joint computation with protocol-defined party/threshold security | Output leakage, collusion/dropout and communication assumptions; source extraction pending |
| TEE | Isolates computation inside a hardware trust boundary | Attestation, vendor/hardware trust, side channels and output leakage; source extraction pending |
| Hybrid | May cover complementary update and output exposures | Guarantees require joint analysis; combined costs must be measured |

Secure aggregation is a function that can be built using cryptographic techniques including MPC; these categories are not mutually exclusive product alternatives. No private operating point, encryption speed or accuracy loss has been measured here.

## Continual learning and models remain open

[LITERATURE EVIDENCE] LwF uses new-task data to preserve earlier behavior through distillation; DER combines rehearsal and distillation of past logits. Their original findings do not select a winner for federated flow data. [R014: LwF](https://arxiv.org/abs/1606.09282), [R015: DER](https://proceedings.neurips.cc/paper_files/paper/2020/hash/b704ea2c39778f07c617f6b7ce480e9e-Abstract.html). EWC constrains changes to important parameters and was demonstrated on MNIST and Atari tasks. [R022: EWC](https://arxiv.org/abs/1612.00796).

[HYPOTHESIS] Naive sequential fine-tuning, bounded local replay, a regularization method and a distillation method can form a useful representative comparison. Raw replay, teacher logits and importance estimates have distinct storage/privacy implications. Final candidate budgets await source extraction and hardware information.

[LITERATURE EVIDENCE] Grinsztajn et al. evaluated 45 tabular datasets and found strong tree-model performance in their medium-sized benchmark settings. This motivates retaining classical controls, not declaring a CIC-IDS2017 winner. [R023: original study](https://arxiv.org/abs/2207.08815).

[CURRENT DESIGN DECISION] Screen model families using comparable validation evidence. MLP is a practical neural candidate; CNN feature locality and recurrent temporal structure require justification. No model parameter count or inference time is known until configuration and hardware are specified.

## Existing integration constrains novelty

[LITERATURE EVIDENCE] Chathoth, Jagannatha and Lee's 2021 preprint studies federated intrusion detection with heterogeneous cohort privacy and proposes continual-learning-based DP methods. The abstract alone is enough to reject an unsupported claim that nobody has combined these ideas. Its datasets, method details and numeric results still need full-text review. [R020: original preprint](https://arxiv.org/abs/2101.09878).

[HYPOTHESIS] The project's potential contribution is a transparent evaluation of integrated trade-offs, leakage-aware validation and architecture revision in a financial-network simulation. Whether a more specific research gap exists remains unresolved.

## CP0 work still required

Detailed numeric extraction; recent integrated IDS comparisons; full model/FL/CL coverage; HE/SMPC/TEE original protocols and resource measurements; current jurisdiction-specific regulatory context; complete dataset comparison; resource envelope; finalized threat model; A0 block contracts and diagram. No CP0 completion or final architecture is claimed.
