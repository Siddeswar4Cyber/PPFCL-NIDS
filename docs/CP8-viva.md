# CP8 viva notes

**What did migration establish?** The saved selected MLPs can be represented in Torch with bounded CPU/CUDA prediction error and verified serialization. It does not establish identical learning trajectories.

**Why can matching Adam parameters still behave differently?** The implementations place epsilon on different sides of second-moment bias correction. N1 explicitly tests native Torch updates and treats fresh training as a controlled new experiment.

**What is the regularization objective?** Mean binary cross-entropy with logits plus half alpha times squared weights divided by the actual minibatch size. Biases are excluded; Adam weight_decay is zero to avoid double-counting.

**How is stability defined?** Three fixed seeds, sample macro-F1 SD <=0.01 and mean macro-F1/AP degradation <=0.002 against the same scope’s B2 MLP. These are practical preregistered gates, not statistical significance tests.

**Can improvements be credited to the new optimizer?** No. Framework, optimizer semantics and epoch budget change together against B2. Only the two N1 learning rates have paired initialization, shuffle streams and equal epoch budgets.

**Why keep Extra Trees?** Neural pilot eligibility does not prove it is the strongest detector. The classical reference remains part of final comparative evidence.

**What remains unproven?** Host-independent and institutional generalization, FL benefits, privacy accounting, continual-learning retention and held-out final performance. The financial setting remains a deployment scenario using general IDS benchmarks.

See reports/CP8-neural-results.md for measured numbers and the exact per-scope decisions. CP9 must define equal-data central/local/federated comparisons and budget/objective weights before scores.
