# CP0 numerical literature evidence

2026-09-08. All values are LITERATURE EVIDENCE, not our experiments. These are selected table extractions, not cross-paper rankings. Where uncertainty or hardware was not extracted it is explicitly unresolved. Registry records point here to avoid duplicate authoritative result tables.

## N01 — Integrated privacy and CL for IDS (R020)

Chathoth et al., CSE-CIC-IDS2018; 80/20 split, two non-IID cohorts, 10,000 simulated clients, 5% participation. Each client has benign and two attack labels. Network: 79 inputs, hidden 79/128, nine outputs; Adagrad 0.1, batch 10. Cohort epsilon 6/8, delta 1e-5; sensitivity/noise settings 1; moments accountant.

| Configuration | Macro-F1 | Weighted-F1 | Micro-F1 |
|---|---:|---:|---:|
| Non-private | 0.77 | 0.94 | 0.95 |
| DP | 0.38 | 0.74 | 0.81 |
| DP-R, rho=0.25 | 0.49 | 0.85 | 0.88 |
| DP-SI | 0.46 | 0.85 | 0.87 |

Locator: IV-B, Table II. Its cohort withdrawal/privacy scheduling differs from new-attack learning. Trusted-curator placement differs from our proposed untrusted coordinator. Split independence, complete privacy proof and runtime are not established by this extraction. Do not inherit the source's claim that non-private performance is a guaranteed upper bound. [Paper](https://arxiv.org/html/2101.09878v1).

## N02 — Recent controlled IDS FL comparison (R026)

Doriguzzi-Corin et al., 2025 preprint: CIC-DDoS2019 binary MLP, 13 clients, one attack type per client and unequal volumes. Six clients selected per round for these methods; Kubernetes testbed; ten experiments. Common round counts follow FLAD's stopping decision.

| Method | Mean client F1 | Reported duration, minutes | Reported network overhead, MB |
|---|---:|---:|---:|
| FedAvg | 0.897 | 8.27 | 34.59 |
| FedProx | 0.815 | 8.88 | 34.59 |
| SCAFFOLD | 0.893 | 8.71 | 60.25 |

Locator: Tables 4, 6, 7 and sections 5-6. Network figure uses the paper's per-client averaging convention; not total consortium bytes. Mean client binary F1 is not multiclass macro-F1. Standard deviation across attack/client scores is not seed uncertainty. Hyperparameters, aggregation choices and FLAD-dependent round allocation constrain transferability. No DP/CL result here. [Paper](https://arxiv.org/html/2509.17836v1).

## N03 — Adaptive server optimization (R009)

Reddi et al.: CIFAR-100 with 500 training clients. Table 1 reports last-100-round mean validation accuracy: FedAvg 44.7%, FedAdagrad 47.9%, FedAdam 52.5%, FedYogi 52.4%, FedAvgM 52.4%. This is an image experiment, not IDS F1. Table 2 gives the client count. The paper uses test data as validation for several tasks; we do not adopt that evaluation practice. Detailed partition/hardware and wall time must be extracted for reproduction, not inferred from rounds. [Paper](https://arxiv.org/html/2003.00295v5).

## N04 — Continual method comparison (R015)

Buzzega et al., Table 2: Sequential CIFAR-10, five two-class tasks, ResNet18, 50 epochs/task, SGD, ten runs. Class-incremental final average accuracy, buffer 500 for replay methods:

| Method | Accuracy percent |
|---|---:|
| Naive SGD, no buffer | 19.62 +/- 0.05 |
| Online EWC, no buffer | 19.49 +/- 0.12 |
| SI, no buffer | 19.48 +/- 0.17 |
| LwF, no buffer | 19.61 +/- 0.05 |
| ER | 57.74 +/- 0.27 |
| DER | 70.51 +/- 1.67 |
| DER++ | 72.70 +/- 1.36 |

Task order was fixed; validation used 10% of training. This is neither flow data nor DP. Do not equate equal example-buffer size with equal memory bytes when logits/models differ. The result motivates rehearsal comparisons, not a universal winner. [Paper](https://arxiv.org/html/2004.07211v2).

## N05 — Feature representation and hidden minority failure (R040)

Sarhan et al., Extra Trees; five 70/30 splits, min-max preprocessing, removal of identifiers and selected TTL fields. Table 8: NF-UNSW-NB15-v2 binary F1 0.97, accuracy 99.73%, prediction time 5.92 microseconds. Table 9: multiclass weighted F1 0.99, but Analysis F1 0.17, Backdoor 0.18, DoS 0.36. Hardware/provenance and preprocessing fitting order require caution; these are v2 results, not local v3 scores. Strong aggregate metrics can coexist with poor minority detection. [Paper](https://arxiv.org/html/2101.11315v2).

## N06 — Cryptography and trusted hardware (R013, R035-R037)

| Source and mechanism | Verified numeric evidence | Boundary |
|---|---|---|
| Bonawitz secure aggregation | 1.73x communication expansion at 2^10 users and 2^20 dimensions; 1.98x at 2^14 users and 2^24 dimensions; 16-bit inputs | Abstract; not a small-client overhead forecast [paper](https://acmccs.github.io/papers/p1175-bonawitzA.pdf) |
| POSEIDON multiparty HE | Three-layer MNIST network, 784 features, 60,000 samples, ten parties: training under two hours | Author-reported abstract result; passive adversary, up to N-1 colluding parties under protocol assumptions; hardware detail not extracted [paper](https://www.ndss-symposium.org/ndss-paper/poseidon-privacy-preserving-federated-neural-network-learning/) |
| ABY3 mixed 3PC | Up to four orders of magnitude faster than prior secure-computation work | Not faster than plaintext training; abstract maximum, no transferable NIDS latency [paper](https://eprint.iacr.org/2018/403) |
| Slalom TEE/GPU | 6-20x throughput for verifiable inference, 4-11x for verifiable private inference | Compared with enclave execution in its setup; VGG16/MobileNet/ResNet; not FL training overhead [paper](https://arxiv.org/abs/1806.03287) |

No credible universal ciphertext expansion, F1 penalty or runtime multiplier exists across these different tasks and schemes. Missing capstone figures stay unmeasured.

## N07 — NetFlow v3 scale and provenance (R025)

Luay et al., Table 2, reports NF3-UNSW-NB15 2,365,424 flows; NF3-CSE-CIC-IDS2018 20,115,529; NF3-ToN-IoT 27,520,260; NF3-BoT-IoT 16,933,808. Attack proportions: 5.40%, 12.93%, 38.98%, 99.7%, respectively. These are published counts, not local audit results. The source describes nProbe conversion preserving PCAP timestamps and says 57 extracted features; local files contain 53 non-label fields. Version/provenance reconciliation is required. A newer extraction does not imply newer underlying traffic. [Paper, sections III-IV](https://arxiv.org/html/2503.04404v3).

## N08 — Recent IDS-specific CL comparison (R053)

The 2026 Applied Soft Computing publisher excerpt reports replay final macro-F1 0.92–0.98 and average forgetting below 0.05 across UQ-IoT-IDS-2021, Kitsune and CIC-IDS2017. Setting: nine synthetic attack-family stages, fixed binary labels, MLP/LSTM/Transformer; five-seed headline results. The excerpt describes RTX 4080 SUPER/i9-14900K hardware, not our laptop. These are abstract ranges, not individually verified Table 7 cells. Direct full-page access failed; missing formulas, exact seeds and leakage checks remain unresolved. This is stronger domain relevance than N04, but does not establish DP/FL performance or a transferable winner. [Publisher abstract and method excerpts](https://doi.org/10.1016/j.asoc.2026.116022).

## Numeric integrity rules (all sections)

Each excerpt is sufficient to motivate a candidate or caution; none predicts our final scores. Experiment registries remain empty of completed runs. No rounded chart value is treated as exact. Future results must distinguish percentage points from relative percent, binary from multiclass F1, per-client from pooled metrics, and repeated seeds from heterogeneous test domains.
