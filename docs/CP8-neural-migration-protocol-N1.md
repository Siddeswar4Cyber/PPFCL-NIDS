# CP8 neural migration and stability N1

M0.8, 2026-09-10. Status: preregistered preparation; runtime execution requires approval of the PyTorch package download. CP8 is not complete until migration and fresh-training gates have been executed and reviewed.

## Question and fixed scope

Can the compact MLP be represented faithfully in PyTorch, and can a bounded fresh-training comparison reduce the observed CIC seed sensitivity before non-private FL pilots? Prediction equivalence is separate from training-trajectory equivalence and from detection quality.

Use the four existing dataset/protocol namespaces independently: CIC primary/stress with P2 and B2 categorical augmentation (172 inputs), NF primary/stress with P1 and full features (98 inputs). Preserve S1 populations, the exact 100,000 training representatives and full validation matrices. The B2 selection artifact determines the saved seed-17 reference. No new preprocessing, feature selection, population exclusions, client ownership, private/public-reference, CL or final/external evaluation is permitted here. C1 remains unchanged.

## Preparation and prediction gates

Bind the selection, source run, model, saved probabilities, feature definition and parent transforms by SHA-256. Validate the source model is a binary ReLU MLP with hidden widths 64 and 32, one sigmoid output and classes [0, 1]. Reconstruct its affine/ReLU/affine/ReLU/sigmoid calculation independently in NumPy in batches of 4,096. Across every validation row, require finite probabilities and maximum absolute difference <= 1e-12 from the saved predictions. Report threshold-0.5 decision disagreements separately. This preparation checks weight layout and artifact identity; it cannot establish PyTorch or CUDA correctness.

After explicit package-download approval, install only torch==2.10.0 from the official CUDA 12.8 wheel index into the existing project virtual environment. Capture the resolved dependency lock, Python/Torch/CUDA/driver versions and device identity. The official previous-versions installation matrix lists this pinned Windows build; it is a reproducibility choice, not a claim to use the latest release.

Copy scikit weights transposed into three torch.nn.Linear layers and copy biases unchanged. CPU float64 inference must agree with the saved probabilities within 1e-12 over full validation. A weights-only save/load must reproduce CPU predictions within 1e-12. CUDA float32 inference uses the already approved P1/P2 input precision, no mixed precision, TF32 disabled, deterministic algorithms and CUBLAS_WORKSPACE_CONFIG=:4096:8. Require maximum absolute probability error <= 1e-4 and threshold-0.5 disagreement rate <= 1e-4 relative to the saved reference. Report actual errors, changed decisions and their distances to threshold. A failed gate is retained and investigated; do not silently relax tolerances or fall back to a different runtime.

## Training semantics and bounded stability experiment

The scikit Adam implementation uses lr*sqrt(1-beta2**t)/(1-beta1**t), with epsilon added to the uncorrected second-moment square root. Standard PyTorch Adam adds epsilon to the bias-corrected denominator. Scikit also divides the alpha weight penalty by the actual minibatch size. Equal parameter names therefore do not guarantee equal updates. N1 fresh training deliberately uses native PyTorch Adam and makes no scikit trajectory-equivalence claim. Before scored training, independently verify BCE-with-logits gradients, weight-only L2 gradients and the first three native Adam steps on a small fixed float64 fixture; include a short final minibatch. Runtime tests remain required, not satisfied by NumPy preparation.

Architecture stays input -> 64 ReLU -> 32 ReLU -> 1 logit. Fresh training uses float32 CUDA, batch size 256, unweighted BCEWithLogitsLoss mean plus 0.5*0.0001/actual_batch_rows times the sum of squared Linear weights (biases excluded); Adam betas=(0.9,0.999), eps=1e-8, weight_decay=0, foreach=False, fused=False. Initialize weights and biases using a separate NumPy RandomState(seed), drawing each layer's (fan_in,fan_out) weights then bias uniformly within +/-sqrt(6/(fan_in+fan_out)), then transpose. Shuffle each epoch with a separate NumPy default_rng(seed) stream; paired candidates share initialization and batch orders. No class weighting, resampling, dropout, clipping, scheduler or validation early stopping.

Compare exactly two candidates per namespace: learning rate 0.001 for 20 epochs and 0.0003 for 20 epochs, each at seeds 17, 29 and 43 (24 fresh fits total). Save epoch training loss but score only the final epoch on full validation. Report the standard B1/B2 metrics at 0.5 and the validation-fitted <=1% FPR operating point, along with fit time, process-tree RSS and CUDA allocated/reserved peaks. Compare against the existing three-seed B2 selected-MLP summaries as historical references, explicitly acknowledging that framework, optimizer semantics and epoch budget change together.

A candidate is eligible for a future pilot if all three fits and numerical gates pass, macro-F1 sample SD <= 0.01, and mean macro-F1 and mean AP each lose at most 0.002 against its same-namespace B2 selected MLP. Rank eligible candidates by mean macro-F1, then mean AP, then lower learning rate. If neither qualifies, report stability/quality unresolved; do not add a third candidate without a new registered amendment. These are practical engineering gates, not statistical significance tests. Reused validation and three seeds do not provide independent confirmation or population confidence intervals.

One worker at a time, at most 600 seconds and 12 GiB sampled worker-tree RSS each, two BLAS/Torch CPU threads, CUDA allocator limit 4 GiB. No GPU driver/toolkit installation. Log all failures and preserve outputs. Before training, commit the implemented runner and runtime tests; bind their hashes to each result. This document freezes the candidate budget before new scores, but does not imply that the training runner already exists.

## Acceptance, interpretation and next checkpoint

CP8 requires artifact reconstruction, CPU/CUDA migration, save/load, optimizer checks, resource measurements, 24 completed or explicitly failed planned fits, verified metrics and a recorded eligibility decision in each namespace. Then preregister CP9 comparable central/local/FL budgets on C1. No FL, DP or CL result follows from successful migration alone.

Sources: [official pinned wheel matrix](https://pytorch.org/get-started/previous-versions/) (installation section consulted), and the installed scikit-learn 1.9.0 source files `_multilayer_perceptron.py` and `_stochastic_optimizers.py` (loss, gradient, initialization and Adam update inspected). Source inspection is not a numerical cross-framework test.
