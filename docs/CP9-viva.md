# CP9 viva notes

**What is federated here?** Five logical clients update a shared neural model locally for one epoch; a coordinator averages parameter states using training-row fractions. All computation is simulated sequentially on one laptop.

**Is it the original FedAvg optimizer?** The aggregation is sample-weighted FedAvg, but client updates use native Adam. The original algorithm used local SGD. There is no server optimizer, so this is not server-side FedAdam.

**Why reset moments in the controls?** All methods reset Adam each epoch/round to match the registered federated reset policy. Weight trajectories still differ. Fresh centralized controls account for this and the constant regularization coefficient.

**What does equal work mean?** Every sample is presented 20 times. Unequal client sizes and short batches produce different step counts, which are reported. It does not mean equal parallel wall time or identical optimization.

**How is local-only evaluated?** A validation row goes to its assigned client's model. The combined probability vector represents this routed system; it is not an ensemble.

**How are client and pooled F1 different?** Pooled F1 comes from the combined confusion matrix. Mean, weighted mean and minimum client F1 summarize separate confusion matrices and need not equal pooled F1.

**Does 1% pooled FPR protect every client?** No. One threshold is fitted on pooled validation and then applied unchanged to each client's rows; individual false-positive rates may exceed 1%.

**How is communication measured?** It is a calculated dense float32 tensor payload for uploads and downloads, not actual network traffic. Transport, serialization, cryptography and raw-data transfer are excluded.

**Does the simulator protect data?** No formal protection is claimed. The simulator accesses common matrices, preprocessing was centrally fitted, and updates can disclose information. DP, secure aggregation and deployment isolation are separate unimplemented gates.

**Can a method be selected now?** CP9 has one seed and reused validation. Its collaboration signal is an exploratory reporting rule; CP10 must preregister challengers and seed checks before a final FL decision.
