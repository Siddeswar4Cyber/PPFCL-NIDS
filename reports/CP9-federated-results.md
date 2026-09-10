# CP9 centralized, local-only and federated pilot

F1 / M0.9, 2026-09-10. CP9 is COMPLETE: 28 registered seed-17 run records, 76 final models and all 36 tests pass. Twelve federated systems complete 20 rounds each. Verification reconstructs all 240 aggregations and reproduces final validation predictions, work ledgers and metrics. This is an exploratory non-private simulation, not a final FL-method selection.

## What is compared

Four fresh centralized references each train on their existing 100,000 representatives. For each of the twelve C1 scenarios, five independent local models train on their own rows and one federated model averages five client updates per round. Validation rows in the local system are routed to their owner model; they are not ensembled. The centralized reference is reused across three ownership views in its namespace, without counting additional fits.

All methods use the same 64/32 model initializer and their own N1-selected learning rate. Every training row appears 20 times: 2,000,000 example presentations per method/scenario. Batch size is 256. Adam state resets every epoch/round in all methods. F1 uses a constant weight-only L2 coefficient 0.0001/256, including short minibatches; fresh central controls account for this change from N1. Equal exposure does not mean equal optimizer-step counts or trajectories.

Similar summed optimizer-step counts also do not imply similar global optimization: FedAvg averages separate client update sequences at each round, while the centralized reference applies every batch update serially to one model. The learning rates were inherited from centralized N1 tuning, not independently optimized for F1 federation. CP10 needs equal, registered method-specific tuning allowances before a final method ranking.

The federated variant is **FedAvg with client Adam**: full participation, one local epoch per round, n_k/N parameter averaging including biases, CPU float64 accumulation and one float32 cast. It has no server optimizer and is not server-side FedAdam. Every client receives the same round-start state; optimizer moments are not aggregated. The simulator accesses common matrices and is not a confidentiality boundary.

## Pooled and worst-client results at threshold 0.5

| Scope / requested scenario | Central pooled F1 | Local pooled F1 | FedAvg pooled F1 | Central worst-client F1 | Local worst-client F1 | FedAvg worst-client F1 |
|---|---:|---:|---:|---:|---:|---:|
| cic-ids-2017 / primary / iid | 0.977345 | 0.952758 | 0.960972 | 0.967533 | 0.923673 | 0.953231 |
| cic-ids-2017 / primary / dirichlet_a1 | 0.977345 | 0.961616 | 0.960825 | 0.960162 | 0.912243 | 0.928502 |
| cic-ids-2017 / primary / dirichlet_a0p1 | 0.977345 | 0.974051 | 0.922388 | 0.960874 | 0.920731 | 0.871952 |
| cic-ids-2017 / stress / iid | 0.984307 | 0.969630 | 0.974771 | 0.981289 | 0.957708 | 0.965707 |
| cic-ids-2017 / stress / dirichlet_a1 | 0.984307 | 0.973895 | 0.971204 | 0.925588 | 0.945558 | 0.915695 |
| cic-ids-2017 / stress / dirichlet_a0p1 | 0.984307 | 0.984938 | 0.937635 | 0.853709 | 0.862851 | 0.788103 |
| ND-UNSW-NB15-v3 / primary / iid | 0.999223 | 0.998114 | 0.998401 | 0.998551 | 0.997366 | 0.997635 |
| ND-UNSW-NB15-v3 / primary / dirichlet_a1 | 0.999223 | 0.998402 | 0.998412 | 0.998673 | 0.997692 | 0.997631 |
| ND-UNSW-NB15-v3 / primary / dirichlet_a0p1 | 0.999223 | 0.996637 | 0.998776 | 0.998491 | 0.972801 | 0.997741 |
| ND-UNSW-NB15-v3 / stress / iid | 0.998961 | 0.993132 | 0.993752 | 0.998583 | 0.989355 | 0.992514 |
| ND-UNSW-NB15-v3 / stress / dirichlet_a1 | 0.998961 | 0.975603 | 0.995607 | 0.997077 | 0.688836 | 0.984766 |
| ND-UNSW-NB15-v3 / stress / dirichlet_a0p1 | 0.998961 | 0.858611 | 0.969105 | 0.998099 | 0.540159 | 0.896687 |

| Scope / scenario | Actual C1 allocation | FedAvg − local pooled F1 | FedAvg − central pooled F1 | FedAvg − local worst F1 | Exploratory signal |
|---|---|---:|---:|---:|---|
| cic-ids-2017 / primary / iid | uniform_iid | +0.008215 | -0.016373 | +0.029558 | Yes |
| cic-ids-2017 / primary / dirichlet_a1 | pure_dirichlet | -0.000791 | -0.016521 | +0.016258 | No |
| cic-ids-2017 / primary / dirichlet_a0p1 | dirichlet_uniform10_fallback | -0.051663 | -0.054958 | -0.048779 | No |
| cic-ids-2017 / stress / iid | uniform_iid | +0.005141 | -0.009536 | +0.007999 | Yes |
| cic-ids-2017 / stress / dirichlet_a1 | pure_dirichlet | -0.002690 | -0.013103 | -0.029863 | No |
| cic-ids-2017 / stress / dirichlet_a0p1 | dirichlet_uniform10_fallback | -0.047303 | -0.046672 | -0.074748 | No |
| ND-UNSW-NB15-v3 / primary / iid | uniform_iid | +0.000288 | -0.000822 | +0.000269 | No |
| ND-UNSW-NB15-v3 / primary / dirichlet_a1 | pure_dirichlet | +0.000010 | -0.000811 | -0.000061 | No |
| ND-UNSW-NB15-v3 / primary / dirichlet_a0p1 | pure_dirichlet | +0.002138 | -0.000447 | +0.024940 | Yes |
| ND-UNSW-NB15-v3 / stress / iid | uniform_iid | +0.000619 | -0.005210 | +0.003158 | No |
| ND-UNSW-NB15-v3 / stress / dirichlet_a1 | pure_dirichlet | +0.020004 | -0.003355 | +0.295930 | Yes |
| ND-UNSW-NB15-v3 / stress / dirichlet_a0p1 | dirichlet_uniform10_fallback | +0.110494 | -0.029857 | +0.356528 | Yes |

5/12 scenarios meet the preregistered exploratory signal: pooled macro-F1 improves over routed-local by at least 0.002 and worst-client macro-F1 degrades by no more than 0.01. This flag is not a significance test or a final winner decision. Outcomes outside it remain valid results; no configuration was changed after scores.

The largest observed pooled gain over local-only is +0.110494 in ND-UNSW-NB15-v3/stress/dirichlet_a0p1. The largest decline is -0.051663 in cic-ids-2017/primary/dirichlet_a0p1. FedAvg is therefore not promoted as uniformly beneficial. Local-update drift under heterogeneous data is a hypothesis for a registered CP10 comparison, not an established causal explanation from these scenarios.

Local-only also maintains a separate parameter set for each client, while FedAvg serves one global model. Relative results therefore reflect client specialization as well as optimization. With label-skew simulated ownership, locally useful class priors can differ sharply; these outcomes should not be generalized to measured institutions or interpreted as a pure effect of model averaging.

The three uniform-mixture C1 fallbacks retain their actual labels. Label-aware simulated validation ownership and training-support-conditioned allocation limit interpretation. The twelve scenarios reuse four underlying validation populations; they are not twelve independent data samples. Single-seed differences do not establish robustness or population uncertainty.

## AP, false positives and client support

| Scope / scenario | Central AP | Local AP | FedAvg AP | FedAvg benign FPR at 0.5 | FedAvg recall at pooled calibrated threshold |
|---|---:|---:|---:|---:|---:|
| cic-ids-2017 / primary / iid | 0.990710 | 0.984882 | 0.988713 | 0.020147 | 0.928794 |
| cic-ids-2017 / primary / dirichlet_a1 | 0.990710 | 0.988141 | 0.985108 | 0.017739 | 0.904488 |
| cic-ids-2017 / primary / dirichlet_a0p1 | 0.990710 | 0.987363 | 0.983349 | 0.000584 | 0.921597 |
| cic-ids-2017 / stress / iid | 0.995524 | 0.989032 | 0.989577 | 0.004205 | 0.957198 |
| cic-ids-2017 / stress / dirichlet_a1 | 0.995524 | 0.991068 | 0.989747 | 0.004083 | 0.962548 |
| cic-ids-2017 / stress / dirichlet_a0p1 | 0.995524 | 0.995703 | 0.969287 | 0.000318 | 0.918588 |
| ND-UNSW-NB15-v3 / primary / iid | 0.999577 | 0.996629 | 0.997410 | 0.000112 | 0.997740 |
| ND-UNSW-NB15-v3 / primary / dirichlet_a1 | 0.999577 | 0.997039 | 0.997290 | 0.000109 | 0.997659 |
| ND-UNSW-NB15-v3 / primary / dirichlet_a0p1 | 0.999577 | 0.997395 | 0.999255 | 0.000132 | 0.999274 |
| ND-UNSW-NB15-v3 / stress / iid | 0.998931 | 0.993049 | 0.992176 | 0.000148 | 0.988841 |
| ND-UNSW-NB15-v3 / stress / dirichlet_a1 | 0.998931 | 0.992963 | 0.995870 | 0.000148 | 0.996107 |
| ND-UNSW-NB15-v3 / stress / dirichlet_a0p1 | 0.998931 | 0.964690 | 0.981420 | 0.000067 | 0.976126 |

The full comparison artifact includes binary/attack-family support, AP/ROC, confusion matrices, pooled metrics and per-client metrics at 0.5 and the common pooled validation-fitted <=1% benign-FPR threshold. A pooled FPR bound does not hold for every client. Client macro-F1 mean, row-weighted mean, minimum and population SD are separate from pooled macro-F1. All validation clients meet the C1 binary support floor; an absent canonical family has null recall.

## Work, runtime and calculated communication

| Scope / method / scenario | Optimizer steps | Fit seconds | Model payload upload / download bytes |
|---|---:|---:|---|
| cic-ids-2017 / primary / central / all | 7,820 | 30.555 | Not estimated |
| cic-ids-2017 / primary / local / iid | 7,880 | 29.790 | Not estimated |
| cic-ids-2017 / primary / fedavg / iid | 7,880 | 30.925 | 5,274,000 / 5,274,000 |
| cic-ids-2017 / primary / local / dirichlet_a1 | 7,880 | 29.487 | Not estimated |
| cic-ids-2017 / primary / fedavg / dirichlet_a1 | 7,880 | 29.973 | 5,274,000 / 5,274,000 |
| cic-ids-2017 / primary / local / dirichlet_a0p1 | 7,860 | 28.682 | Not estimated |
| cic-ids-2017 / primary / fedavg / dirichlet_a0p1 | 7,860 | 33.397 | 5,274,000 / 5,274,000 |
| cic-ids-2017 / stress / central / all | 7,820 | 33.683 | Not estimated |
| cic-ids-2017 / stress / local / iid | 7,860 | 23.834 | Not estimated |
| cic-ids-2017 / stress / fedavg / iid | 7,860 | 22.724 | 5,274,000 / 5,274,000 |
| cic-ids-2017 / stress / local / dirichlet_a1 | 7,860 | 25.228 | Not estimated |
| cic-ids-2017 / stress / fedavg / dirichlet_a1 | 7,860 | 23.301 | 5,274,000 / 5,274,000 |
| cic-ids-2017 / stress / local / dirichlet_a0p1 | 7,860 | 22.802 | Not estimated |
| cic-ids-2017 / stress / fedavg / dirichlet_a0p1 | 7,860 | 21.816 | 5,274,000 / 5,274,000 |
| ND-UNSW-NB15-v3 / primary / central / all | 7,820 | 23.605 | Not estimated |
| ND-UNSW-NB15-v3 / primary / local / iid | 7,860 | 25.570 | Not estimated |
| ND-UNSW-NB15-v3 / primary / fedavg / iid | 7,860 | 25.013 | 3,379,600 / 3,379,600 |
| ND-UNSW-NB15-v3 / primary / local / dirichlet_a1 | 7,860 | 25.677 | Not estimated |
| ND-UNSW-NB15-v3 / primary / fedavg / dirichlet_a1 | 7,860 | 24.234 | 3,379,600 / 3,379,600 |
| ND-UNSW-NB15-v3 / primary / local / dirichlet_a0p1 | 7,880 | 24.225 | Not estimated |
| ND-UNSW-NB15-v3 / primary / fedavg / dirichlet_a0p1 | 7,880 | 24.878 | 3,379,600 / 3,379,600 |
| ND-UNSW-NB15-v3 / stress / central / all | 7,820 | 23.617 | Not estimated |
| ND-UNSW-NB15-v3 / stress / local / iid | 7,860 | 26.720 | Not estimated |
| ND-UNSW-NB15-v3 / stress / fedavg / iid | 7,860 | 25.384 | 3,379,600 / 3,379,600 |
| ND-UNSW-NB15-v3 / stress / local / dirichlet_a1 | 7,840 | 25.418 | Not estimated |
| ND-UNSW-NB15-v3 / stress / fedavg / dirichlet_a1 | 7,840 | 23.447 | 3,379,600 / 3,379,600 |
| ND-UNSW-NB15-v3 / stress / local / dirichlet_a0p1 | 7,860 | 24.549 | Not estimated |
| ND-UNSW-NB15-v3 / stress / fedavg / dirichlet_a0p1 | 7,860 | 24.183 | 3,379,600 / 3,379,600 |

Total measured fitting time is 732.718 seconds; supervised model-worker time is 971.274 seconds. The four-hour EXP-004 family budget retains 13428.726 seconds for later model workers. Tests and final verification are additional overhead and are not included in this model-worker sum.

Maximum sampled worker-tree RSS is 2.772 GiB; maximum CUDA allocated/reserved memory is 0.138 / 0.156 GiB. Every worker stayed within the 600-second, 12-GiB process-tree and 4-GiB allocator limits. One worker/client update ran at a time. RSS is sampled every 0.5 seconds and excludes the supervisor; Torch allocator counters exclude some driver memory.

Payload counts represent 20 training rounds × five uploads/downloads × all float32 parameter bytes including biases. They are calculated dense-model payloads, not measured network traffic or latency. Serialization, transport, metadata, cryptography, optimizer state, raw-data transfer and any additional final-model deployment broadcast are excluded. Saving intermediate states locally supports audit and is not a privacy measure. No secure aggregation, DP or deployed cross-institution system is implemented.

## Verification, limitations and next checkpoint

Verification binds N1 selection and parent/C1/data/model/code artifacts; confirms exact ownership and example/step coverage; reconstructs shuffled global-row order hashes; checks identical client starts and round chaining; recomputes all weighted aggregations with NumPy; reloads every final model; and reproduces routed/global probabilities, metrics and operating points. The one-client fixture matches local training exactly, including reset-state behavior; unequal weights, invalid uploads and the common regularization gradient are tested.

Source-corpus validation and the financial deployment scenario remain distinct. NF endpoints overlap training almost entirely; H1 did not establish a host-separated binary challenge. C1 represents synthetic clients, including fallback-conditioned heterogeneity, and its shared preprocessing was fitted centrally on development data. Neither FL nor the present simulation supplies a formal privacy guarantee. No final/external model scores or CL training occurred.

CP10 should preregister bounded FL challengers and confirmation seeds, using these fixed central/local/FedAvg references and the remaining family budget. Do not declare a winning FL method from CP9 alone. Preserve all negative collaboration outcomes and inspect per-client regressions before selecting later configurations.

Evidence: [F1 protocol](../docs/CP9-federated-pilot-F1.md), [complete comparison](cp9/comparison.json), [verification](cp9/verification.json), [test log](cp9/tests.log), [checkpoint checks](CP9-checkpoint-verification.md), [viva notes](../docs/CP9-viva.md).
