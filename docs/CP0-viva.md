# CP0 defense notes

Current scope: research and provisional A0 only. No model has been trained.

**30 seconds.** I am building a research prototype for institutions that want to collaborate on intrusion detection without routinely pooling raw flow records. I will compare local, centralized and federated baselines, then test privacy and continual adaptation under controlled splits. The data are general IDS benchmarks, so the financial setting is a deployment scenario, not a claim about bank traffic.

**Why flows?** They summarize communication without requiring application payload. They can reveal traffic patterns, but they cannot prove the content of a SQL injection or whether a transaction is fraudulent.

**Why FL?** It changes where training data reside. It does not automatically hide the information in updates or prove collaboration improves detection; both require evaluation.

**Why MLP first?** It is a compact integration candidate for tabular inputs and per-example gradients. Classical models remain strong detection comparators. We have not established that an MLP is best.

**Why not automatically FedProx?** Its proximal penalty can help some heterogeneous settings and harm others. Our candidates share splits, model and documented tuning budgets before selection.

**What will DP protect?** If the mechanism passes review, the stated contribution of one curated training flow in the server-visible training transcript. It will not protect the whole institution, compromised raw storage or every flow from a person under a one-record guarantee.

**What do epsilon and delta mean?** They parameterize a bound on how the randomized output distribution changes when the protected dataset changes by one declared unit. A useful answer must also name adjacency, released outputs and lifetime composition. Smaller epsilon is generally a tighter bound under the same setting; values are not comparable without that context.

**Why not HE instead?** Encryption protects computation/data visibility under a cryptographic protocol; DP limits information about a record in released outputs. They address different surfaces and may be combined, at added cost. No HE implementation is claimed here.

**Why CL?** Later data may differ from earlier data. We need to measure both new-task learning and retention; a frozen model may retain its old behavior while failing to adapt.

**Why not automatically LwF?** A prior teacher can be inaccurate on shifted inputs. Replay and importance regularization are challengers; privacy compatibility is another test, not proof of detection superiority.

**How do you avoid leakage?** Lock group/time-aware manifests before fitting transforms, use only allowed development records for selection, record duplicate overlap and metadata limitations, and keep final/external performance out of tuning.

**What is the contribution?** The current intended contribution is controlled experimental evidence and a reproducible integration of known techniques. Prior FL+privacy+CL IDS work exists. Novel algorithms and successful results are not yet established.

**What could invalidate the study?** Bad label/provenance assumptions, correlated splits, arbitrary synthetic sequence construction, unaccounted private accesses, weak minority support or tuning after final-test exposure. These are explicit gates in A0, not problems to hide behind high accuracy.

**Two-minute extension.** Explain the two schema tracks, why NetFlow timestamps require audit, how a client performs local optimization before a protected update leaves, why aggregation is separate from privacy, and how the task score matrix measures forgetting. Finish with the current limitations: one-laptop simulation, no real financial telemetry, no measured winner and no established privacy guarantee yet.
