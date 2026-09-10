# CP9 central/local/FedAvg pilot F1

M0.9, 2026-09-10. Preregistered before F1 model scores. Question: under the fixed C1 ownership contracts, how does sample-weighted model averaging compare with centralized and local-only references at equal training-example exposure? This checkpoint is an exploratory seed-17 pilot, not a final FL-method selection or replication of a paper's numerical results.

## Scope and prerequisites

Use the four existing CIC/NF primary/stress namespaces independently, each with its N1-selected representation and learning rate. Require N1 verification and frozen selection, unchanged S1/P2/P1 transforms and exact parent training/validation matrices, plus CP7's independently verified C1 manifests. Twelve scenarios are the Cartesian product of four namespaces and IID/Dirichlet alpha 1/Dirichlet alpha 0.1. Preserve actual C1 method labels, including three uniform-mixture fallbacks. No source-population edits, new preprocessing, private/public-reference/CL/final/external scores or downloads.

## Controlled objective and optimizer amendment

Initialize every model from the N1 NumPy RandomState(17) 64/32 binary MLP initializer. Reuse N1's selected learning rate for its own scope (0.001 primary, 0.0003 stress), without tuning it again. Float32 CUDA, deterministic algorithms, TF32 disabled, batch size 256. Fix the common objective to mean BCEWithLogits plus (0.5 * 0.0001 / 256) times squared Linear weights; exclude biases. Unlike N1, the regularizer denominator stays 256 even for a short minibatch, preventing client-dependent regularization from the size of the final batch. This is an explicit F1 amendment; train fresh centralized references and do not treat N1 runs as identical controls.

Use native Adam with N1's betas/epsilon, zero weight_decay, foreach=False and fused=False. Reset Adam moments and step counter at the start of every epoch/round for all three methods. Centralized resets every global epoch; local-only resets every local epoch; federated clients reset every round. Weights persist except when federated clients receive the current global state. There is no server optimizer. This variant is **FedAvg with client Adam**, distinct from the original paper's local SGD and from server-side FedAdam. No trajectory equivalence to centralized training is claimed.

The canonical FedAvg reference uses data-size objective/aggregation weights and repeated local updates followed by model averaging; Algorithm 1 and the objective section were consulted in the [author paper](https://proceedings.mlr.press/v54/mcmahan17a/mcmahan17a.pdf). F1's optimizer, small client count and benchmark setting are our simulation choices.

## Runs, budgets and isolation

- Centralized: four runs, one per namespace, 20 epochs on all 100,000 representatives. Reuse each run's probabilities to evaluate its three C1 ownership views; do not count these views as new fits.
- Local-only: twelve runs, one per C1 scenario; train five independent models, each for 20 epochs on its own rows. Initialize all five identically. Route each validation row to its owner model, with no ensemble or cross-client training.
- FedAvg with client Adam: twelve runs; 20 rounds, full participation, one complete epoch per client per round. Every client starts from the same round-start global state, never the previous client's update. Aggregate all parameters, including biases, with fixed n_k/100000 training-count weights. Accumulate in CPU float64 in client-ID order, cast once to float32; do not aggregate Adam state.

This is 28 run records and 76 final trained models (4 centralized, 60 local-only, 12 global federated). The 1,200 federated client epochs are intermediate updates, not independent final models. Each method/scenario uses 2,000,000 total training-example presentations. Unequal client sizes mean unequal local steps; report per-client and total steps. A 400-step epoch cap is sufficient for every saved client and the centralized 100,000-row sample; assert this before fitting and fail rather than truncate rows. No dropped batches, oversampling, class weighting, early stopping or adaptive round count.

Shuffle each epoch with a fresh NumPy default_rng seeded by the first 16 hex SHA-256 digits of `F1|17|dataset|protocol|scenario|round|client`, with rounds 1..20 and clients 0..4. Centralized uses scenario `all`, client -1. Local and federated clients therefore have identical row orders at corresponding epochs/rounds. Save order hashes, counts and steps. Reuse unchanged row indices from C1. One training worker and one client update execute at a time. The simulator can access the common matrices; this is not an operating-system isolation or data-confidentiality claim. The aggregation function accepts only parameter states and training counts.

Resource limits: 600 seconds and 12 GiB sampled process-tree RSS per worker; 4 GiB Torch CUDA allocator, two CPU threads. The EXP-004 four-hour model-worker budget is cumulative across F1 and later FL pilots; reserve a full worker allowance before launching a run, sum measured supervised worker time, and stop with an explicit incomplete status if budget is exhausted. No unregistered expansion to additional seeds/methods in CP9.

## Measurements and retained evidence

Score only final epoch/round models on the full existing validation matrix. Report pooled standard B1 binary/AP/ROC and attack-family metrics at 0.5 and at the pooled validation-fitted <=1% benign-FPR threshold. Apply that common threshold to each client's rows and report their metrics/support. A pooled 1% FPR does not guarantee 1% in every client. Report unweighted mean, validation-row-weighted mean, minimum and population SD of client macro-F1; distinguish these from pooled macro-F1. Every existing validation client meets C1's binary support floor, but rare canonical classes can be absent.

Retain final probabilities/models, initializer, loss/work/order ledgers, model/data/code hashes and all 20 federated round-start, uploaded and aggregated states. Independently reconstruct every weighted aggregation and verify round chaining, identical starts, parameter shapes/dtypes, finite updates, exact row coverage/order and paired local/FL streams. A one-client integration fixture must match the local reference under the same schedule. Add unequal-weight arithmetic, invalid-upload and common-objective gradient tests. Verify no client mutates the input global state.

Communication is a calculated dense tensor-payload estimate: five float32 model downloads and five uploads per round, 20 rounds, including biases. Report directions separately and parameter count. It excludes serialization/protocol/cryptography, optimizer states and initial data transfer. No real network latency, secure aggregation or privacy guarantee is measured. Central/local communication is not estimated as a deployment quantity.

## Interpretation and completion gate

Compare federated minus centralized and federated minus routed-local metrics within each exact scenario. Mark an exploratory collaboration signal only if pooled macro-F1 improves on local-only by >=0.002 and worst-client macro-F1 degrades by <=0.01. These are reporting flags, not a winning-method decision or significance test. Publish all other outcomes without changing configurations; one seed cannot establish stability. No final FL selection until CP10's registered challengers and multi-seed comparisons.

CP9 completes when the 28 runs are executed or explicitly failed, verification and resource/work/communication accounting are recorded, and registries, architecture status, limitations and viva notes are updated. FL benefits may be absent; that is a valid experimental result. CP10 should address measured weaknesses with a bounded preregistered comparison, preserving the F1 references and four-hour family budget.
