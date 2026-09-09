# CP7 host feasibility and client contracts

C1 / H1 / M0.7, 2026-09-10. Twelve client manifests are constructed and verified, covering five logical clients in each of four dataset/protocol namespaces and three allocation scenarios. Four fixed host-separation candidates were assessed and rejected for insufficient support. No classifier or FL model was trained, and final/external scores remain sealed.

## Host separation findings

| NF scope | Permitted development/validation rows | Endpoint addresses | Components | Components with attacks |
|---|---:|---:|---:|---:|
| primary | 1,417,626 | 42 | 4 | 1 |
| stress | 601,023 | 41 | 3 | 1 |

Every attack is in one 20-address component in each scope. A separate 20-address component contains only benign traffic. Components include both endpoint edges and any feature-group bridges. Retaining all permitted flows while separating endpoints therefore cannot give both training and validation attack examples. This conclusion is conditional on the observed development population and the endpoint-identity assumptions.

| NF scope | Component size in rows | Endpoint addresses | Benign rows | Attack rows |
|---|---:|---:|---:|---:|
| primary | 1,327,258 | 20 | 1,327,258 | 0 |
| primary | 90,350 | 20 | 15,923 | 74,427 |
| primary | 17 | 1 | 17 | 0 |
| primary | 1 | 1 | 1 | 0 |
| stress | 577,982 | 20 | 577,982 | 0 |
| stress | 23,032 | 20 | 207 | 22,825 |
| stress | 9 | 1 | 9 | 0 |

| NF scope / candidate | Retained training rows | Retained validation rows | Validation benign / attack | Rejection reason |
|---|---:|---:|---|---|
| primary / components | 945,117 | 0 | 0 / 0 | validation: fewer than 1000 rows; validation: fewer than 20 benign rows; validation: fewer than 20 attack rows |
| primary / endpoint_filter | 709,886 | 1,208 | 2 / 1206 | validation: fewer than 20 benign rows |
| stress / components | 518,956 | 0 | 0 / 0 | validation: fewer than 1000 rows; validation: fewer than 20 benign rows; validation: fewer than 20 attack rows |
| stress / endpoint_filter | 404,579 | 439 | 1 / 438 | validation: fewer than 1000 rows; validation: fewer than 20 benign rows |

The component-hash rule placed all components on the training side, leaving no retained validation. Independently of that draw, only one attack component prevents a no-discard two-class split. Endpoint filtering retains 1,208 primary validation rows (2 benign) and 439 stress rows (1 benign), below the registered support floors. No seed search or floor relaxation followed. These fixed rejections do not establish that every possible population-changing host subset is impossible.

Candidate ledgers retain all permitted rows with explicit exclusion reasons. Original training/validation roles are preserved; earlier validation never becomes training. No model score is produced for a rejected candidate. CIC host metadata is unavailable, so no CIC host-separation assertion is made.

## Five-client assignments

| Dataset / scope | Requested scenario | Actual method | Attempts | Training rows, clients 0–4 | Training attack-prevalence range | Eligible validation clients |
|---|---|---|---:|---|---|---:|
| cic-ids-2017 / primary | dirichlet_a0p1 | dirichlet_uniform10_fallback | 21 | 26,481 / 12,483 / 2,214 / 2,616 / 56,206 | 6.68%–37.50% | 5/5 |
| cic-ids-2017 / primary | dirichlet_a1 | pure_dirichlet | 1 | 41,745 / 17,200 / 6,990 / 17,779 / 16,286 | 6.07%–76.35% | 5/5 |
| cic-ids-2017 / primary | iid | uniform_iid | 1 | 19,978 / 20,244 / 20,002 / 19,854 / 19,922 | 17.03%–17.43% | 5/5 |
| cic-ids-2017 / stress | dirichlet_a0p1 | dirichlet_uniform10_fallback | 21 | 11,221 / 14,277 / 2,389 / 10,360 / 61,753 | 0.55%–82.86% | 5/5 |
| cic-ids-2017 / stress | dirichlet_a1 | pure_dirichlet | 1 | 8,493 / 7,317 / 22,261 / 44,992 / 16,937 | 1.78%–34.77% | 5/5 |
| cic-ids-2017 / stress | iid | uniform_iid | 1 | 19,947 / 19,986 / 20,003 / 19,872 / 20,192 | 10.67%–11.25% | 5/5 |
| ND-UNSW-NB15-v3 / primary | dirichlet_a0p1 | pure_dirichlet | 10 | 23,860 / 1,181 / 4,433 / 67,329 / 3,197 | 2.88%–71.13% | 5/5 |
| ND-UNSW-NB15-v3 / primary | dirichlet_a1 | pure_dirichlet | 1 | 17,872 / 23,402 / 12,603 / 26,155 / 19,968 | 1.94%–12.81% | 5/5 |
| ND-UNSW-NB15-v3 / primary | iid | uniform_iid | 1 | 20,087 / 20,072 / 19,920 / 19,852 / 20,069 | 5.06%–5.49% | 5/5 |
| ND-UNSW-NB15-v3 / stress | dirichlet_a0p1 | dirichlet_uniform10_fallback | 21 | 2,264 / 2,368 / 2,541 / 89,875 / 2,952 | 0.70%–32.96% | 5/5 |
| ND-UNSW-NB15-v3 / stress | dirichlet_a1 | pure_dirichlet | 2 | 36,595 / 1,144 / 6,125 / 43,235 / 12,901 | 1.24%–43.53% | 5/5 |
| ND-UNSW-NB15-v3 / stress | iid | uniform_iid | 1 | 20,004 / 19,919 / 20,130 / 19,965 / 19,982 | 2.86%–3.03% | 5/5 |

3 scenarios required the registered 10% uniform mixture after 20 unsuccessful pure Dirichlet draws. Across all scenarios, 70 rejected allocation attempts are preserved with their probability matrices and training support. NF primary alpha 0.1 accepted its tenth pure draw; NF stress alpha 1.0 accepted its second. Acceptance used training support only.

Every client has at least 1,000 training representatives and 20 examples of each binary class. Every validation client also meets the registered 20-per-binary-class eligibility floor, without validation-based retries. Rare canonical attack classes can still be absent in individual clients; full class counts are retained in each client report. Small alpha and a fallback do not guarantee a particular ordering of realized heterogeneity: use the measured distributions.

Each scenario partitions exactly the same 100,000 training representatives and the complete corresponding validation matrix. Duplicate feature groups have one owner; no group crosses training/validation or clients. Saved row indices preserve parent matrix order, so future model comparisons can read the same vectors without copying or reshuffling their identities. All scenario manifests are separate views of reused populations, not additional independent data.

## Interpretation and next step

C1 clients are synthetic partitions, not real institutions, host-disjoint populations or five datasets. Label-skew validation ownership is generated from the training-fitted label probabilities. The common preprocessing was fitted centrally on permitted development data. It supports controlled non-private simulations, with no distributed-preprocessing or differential-privacy guarantee. Private/public-reference/final/external client ownership and CL-specific contracts remain uncreated.

CP8 can verify neural-framework migration, input precision and optimization stability, then define central/local/FL comparisons on identical C1 assignments. This advances a scoped synthetic-client study; it does not repair independent-host generalization. Stronger claims would require a new approved data/split study. Current model choices and final evaluation remain provisional.

## Verification and provenance

All 26 tests pass. The verifier reconstructs allocation attempts from training only, independently computes hash-based ownership, checks exact parent rows and source roles, and rebuilds host components with graph traversal plus feature-group bridges. It also recomputes candidate-side/exclusion rules from the original NF source and verifies support and zero endpoint/group overlap.

H1 uses a 4-GB DuckDB memory limit and four threads; this is a configured limit, not measured process RSS. C1 per-scenario timings exclude loading/hashing parent matrices. No model training latency, communication cost or FL detection metric is claimed.

See [protocol](../docs/CP7-host-client-protocol-C1.md), [verification](cp7/verification.json), [host support and candidate bindings](cp7/host-feasibility.json), [test log](cp7-tests.log), [viva notes](../docs/CP7-viva.md), and [checkpoint verification](CP7-checkpoint-verification.md).
