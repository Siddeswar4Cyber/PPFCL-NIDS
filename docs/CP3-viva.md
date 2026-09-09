# CP3 viva notes

**Why group after numeric parsing?** Strings such as 1, 1.0 and 1e0 represent the same predictor value. Keeping them on different sides of a split could make leakage checks pass falsely. Grouping also excludes IP/time predictors, so metadata cannot hide equal model inputs.

**Why preserve every row in a membership file?** It gives an auditable exclusion ledger tied to source hashes and positional row IDs. A quarantined row is never silently deleted or relabeled. The representative flag permits deduplicated training without losing the original evaluation population.

**Why separate development and private training?** Non-private candidate selection on one curated population must not be presented as privacy protection for that same selection process. S1 reserves disjoint public-reference, development and private groups. The eventual DP claim remains conditional on curation and the reviewed release mechanism.

**Why only two NF tasks?** The observed data have two capture periods; the intermediate day is entirely benign. S1 groups January 22–23 as the first period and February 18 as the second. Both have attack/benign support in every role. Groups spanning periods are excluded from this CL endpoint.

**Is the primary test chronological?** No. It is a group-disjoint capture-mixture test. The separately registered temporal stress test enforces start/end boundaries as well as the global role seal. Fixed same-period evaluation in CL measures retention/adaptation and is not a future-only test.

**Why not stratify until all rare classes look balanced?** Repeated seed selection would tailor the split to a preferred support pattern. One hash rule is fixed before models. Heartbleed, Infiltration and SQL Injection remain limited and are reported accordingly. Synthetic resampling cannot manufacture independent evidence.

**Do matching hashes prove independent flows?** No. Hash uniqueness is checked over actual distinct projected vectors and binds artifacts to their bytes. Neither vector inequality nor a hash proves host/session independence. Metadata limitations and later transformed collisions remain explicit gates.

**What is next?** CP4 implements deterministic treatment, training-only imputation/encoding/scaling, and checks transformed overlap. Only after that gate can the baseline pilot run. S1 does not establish detection accuracy, privacy protection or financial-network deployment validity.
