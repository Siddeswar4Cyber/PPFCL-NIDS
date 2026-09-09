# CP7 host feasibility H1 and client contracts C1

2026-09-10. M0.7 extends B2. Determine which host-separation claims the metadata supports and create reproducible logical-client assignments before FL comparisons. Prerequisites are verified S1 roles, CIC P2 / NF P1, the fixed 100,000-row training samples and B2 evidence. No classifier is trained at this checkpoint.

## H1 development-only feasibility

CIC CSVs lack host metadata; record that limitation. For NF, join audited source/destination IP metadata to all quality-eligible rows whose primary or stress role is development_train or validation, in separate namespaces. Verify source hashes, parsed-row identities and labels. No final/private/public-reference rows enter the feasibility population, and no earlier validation row becomes training data.

Form undirected endpoint components: every flow joins its endpoints. Also join components touched by the same S1 feature group. Splitting these components is necessary to retain every permitted flow while separating both endpoints and feature groups. Report component/class support, largest-component fraction and the number of components containing attacks. Fewer than two attack-containing components rules out a two-sided binary challenge without discarding flows from this population. Endpoint addresses are not certified physical hosts or institutions; NAT, reuse and special addresses limit interpretation.

Assess two fixed candidate development subsets, with no scores or changes to S1:

- **components**: hash `H1|17|component|` plus newline-joined sorted component addresses with SHA-256. First eight hex digits modulo 1000 below 800 designate the training side; others designate validation. Retain original development_train rows only on the training side and original validation rows only on the validation side.
- **endpoint_filter**: hash each address using `H1|17|host|` and the same threshold. Retain a feature group only if every permitted row has both endpoints on one identical side. Exclude entire cross-side/mixed-side groups. Retain only original roles matching that side. This changes the development population; it is not a fresh untouched test.

Feasibility requires at least 1,000 rows and 20 benign plus 20 attack rows on each side, zero shared endpoints/groups and preserved original roles. These are support floors, not power calculations. Missing endpoints make their entire group ineligible. Publish retained/excluded support and reasons. Use only seed 17; do not search for better support. Persist candidate membership including exclusion reasons. Rejection of a fixed filtered candidate does not prove every possible filtered split impossible. Reduced-feature split redesign remains separate.

## C1 logical-client assignment

Keep each B1/B2 dataset/protocol namespace separate. Assign its exact saved training and validation rows to five clients under uniform IID, Dirichlet alpha 1.0 and Dirichlet alpha 0.1 scenarios. Do not pool schemas or protocols. No private/public-reference/final/external ownership or scores are generated.

Assignments operate on S1 groups; duplicate validation rows inherit group ownership. For each scenario, derive a uniform value from SHA-256 of `C1|17|dataset|protocol|scenario|group_id` (first 13 hex digits divided by 16**13). IID uses equal probabilities. Label skew draws a five-client Dirichlet vector for each label present in training, in lexical label order. Seed NumPy's generator with the first 16 hex digits of the scope tag's SHA-256. Assign by cumulative probabilities and the group uniform value. Validation labels absent from training use uniform probabilities. Validation never determines probability fitting or acceptance.

Each client requires at least 1,000 training representatives and 20 rows of each binary class. Try at most 20 successive Dirichlet draws, recording every attempt's training support. If all fail, assess exactly one registered fallback: mix the twentieth matrix with 10% uniform mass (0.9*p + 0.1/5). Name the actual method as a uniform-mixture fallback, not an accepted pure Dirichlet draw. If that fails, mark the scenario infeasible without relaxing floors. IID has one attempt and no fallback.

Assign validation with the accepted training-derived probabilities and group hash. This is label-aware simulated evaluation ownership, not measured institutions or host separation. Report per-client row/group counts, binary/canonical support, attack prevalence and training fraction. A validation client is eligible for balanced per-client comparison only with at least 20 rows of each binary class. Never resample on validation support; keep all rows for pooled evaluation.

Client manifests index unchanged matrices, without copying vectors. Their shared preprocessing was fitted centrally on permitted development training before ownership assignment. C1 is for non-private simulation and establishes no distributed-preprocessing or DP guarantee. CL/task-specific and privacy-confirmatory contracts require later scopes.

## Acceptance and next work

Verify parent/source hashes, exact row coverage/order, group ownership, zero train/validation group overlap, labels/roles, training floors and deterministic reconstruction. Record failed attempts and host limits; update experiment, run, decision, architecture and progress records and viva notes. Use bounded DuckDB staging (4 GB, four threads), one construction job at a time and no dependency installation. CP8 reviews neural-framework migration and optimizer stability before central/local/FL pilots on identical C1 assignments. Synthetic clients must never be described as banks or independent-host evidence.
