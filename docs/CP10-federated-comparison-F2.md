# CP10 federated comparison F2

M0.10, 2026-09-10. Preregister before any F2 scores. Continue EXP-004 on the four separate CIC/NF primary/stress namespaces. F1 remains immutable. This is a bounded development comparison of three optimizer variants, not a final-test result or privacy claim.

## Fixed data and work

Reuse verified C1 assignments, including actual fallback labels, P1/P2 matrices, N1 representations and namespace-specific base learning rates. No data, preprocessing, label, round-count or architecture search. Twenty rounds, full participation, one complete client epoch, batch 256, 400-step cap with failure rather than truncation. Same F1 constant weight-only L2 and epoch-reset native client Adam. Initialization uses NumPy RandomState(model_seed). Shuffle tag is `F1|model_seed|dataset|protocol|scenario|round|client`; thus seed 17 is exactly F1-compatible. Model seeds 17,29,43 do not change C1 ownership. Every system exposes each training row 20 times. Central controls reset Adam each epoch; local controls reset each client epoch.

## Methods and finite tuning budget

Each method receives exactly three candidate settings on Dirichlet alpha 1, seed 17, independently in each namespace:

| Method | Three candidate values | Other settings |
|---|---|---|
| FedAvg with client Adam | client LR multiplier 0.3, 1, 3 | base LR from same-scope N1 |
| FedProx with client Adam | mu 0.001, 0.01, 0.1 | client LR = base |
| Server FedAdam with client Adam | server LR 0.001, 0.01, 0.1 | client LR = base; beta1 .9, beta2 .99, tau .001 |

FedProx adds `mu/2 * sum_all_parameters((w - round_start)^2)` to the F1 local objective, including biases; the anchor is immutable throughout the local epoch. Its structure follows [Li et al., Definition 2](https://arxiv.org/pdf/1812.06127). We fix complete work rather than claiming tolerance to measured stragglers or the paper's convergence conditions.

Server FedAdam forms the F1 float64 weighted upload average, cast to float32. Delta is that average minus round-start, evaluated in CPU float64. Persist float64 moments: m starts at zero, v at tau squared; m = .9*m + .1*delta, v = .99*v + .01*delta squared, global = float32(start + server_lr*m/(sqrt(v)+tau)). No bias correction or moment reset. All parameters participate. This follows the server recurrence in [Reddi et al., Algorithm 2](https://arxiv.org/pdf/2003.00295); our client Adam, precision, fixed epoch and weighting choices are explicit variants, not a replication of the paper's SGD experiment or theory. Moments remain server-side and are not transmitted.

There are 36 candidate cells, including four reused exact F1 base-FedAvg cells and 32 new fits. Configuration selection is mechanical: retain candidates within 0.002 pooled macro-F1 of the best candidate; among these retain AP within 0.002 of their best AP; then choose maximum worst-client macro-F1, followed by pooled F1, AP and lower candidate index. All comparisons use threshold 0.5. Persist the selection and source-report hashes before confirmation fits. This rule explicitly trades up to 0.002 pooled F1 for client performance. It is identical for all methods, although the searched parameter dimensions differ.

## Confirmation and reuse

Evaluate every method's selected configuration on all three C1 scenarios and all three model seeds: 108 cells. Reuse the twelve alpha-1 seed-17 selected candidates, and reuse any other exact base-FedAvg seed-17 F1 cells. Train fresh central and routed-local controls at seeds 29 and 43 (8 central + 24 local systems); reuse the 16 F1 seed-17 controls. Controls retain their base LR and are references, not equally tuned contenders. At most 160 new F2 workers: 32 tuning, 96 remaining method cells and 32 controls. Reuse is referenced explicitly and never counted as a new fit.

The same validation populations underlie all ownership views; alpha-1 tuning and other scenario views are not independent data holdouts. Seed-17 confirmation includes tuning observations. Report both all-three-seed summaries and fresh-seed 29/43 sensitivity separately. Population uncertainty, host generalization and final-test claims remain unavailable.

## Method decision fixed before scores

Within each namespace, compare each challenger against tuned FedAvg on the nine paired scenario/seed cells. A challenger qualifies only if mean pooled macro-F1 gain is at least 0.002, mean AP loss is no greater than 0.002, no paired worst-client F1 loss exceeds 0.01, and each scenario's three-seed mean pooled F1 gain is nonnegative. Apply the same four gates separately to the six fresh-seed cells as well. If neither qualifies retain tuned FedAvg as the development reference. If both qualify select higher nine-cell mean pooled F1, then mean worst-client F1, then FedProx on an exact tie. No averaging across datasets or primary/stress for selection. This conservative practical-margin rule is not a significance test or proof of optimality. Final detector choice against classical/central baselines remains open.

## Accounting and verification

EXP-004 has a cumulative 14,400-second supervised model-worker limit, including F1's 971.2741855 seconds. Reserve 600 seconds before each worker. Worker caps: 600 seconds, sampled process-tree RSS 12 GiB, Torch CUDA allocator 4 GiB, two CPU threads, one worker/client update at a time. Preserve failed records and stop instead of silently expanding budget or overwriting. Tests and independent artifact verification are separately reported overhead. No new downloads, private/CL/final/external scores or remote publication.

Save initial/final models and probabilities, all round starts/uploads/weighted averages/final server states, and FedAdam moments before/after every round. Bind source/data/configuration/report hashes. Independently reconstruct every average and adaptive recurrence with NumPy; check update sign, moment persistence, finite values, shape, dtype, all round/work chains and full row coverage. Reproduce all saved final probabilities, pooled/per-client metrics and FPR thresholds. Test proximal gradients including biases, zero-mu F1 parity, non-mutation and seed-17 order compatibility, and multi-round server Adam arithmetic. Retain F1's calculated dense upload/download payload formula, excluding protocol/crypto/real network timing and final deployment broadcast. Update registries, architecture limitations, results and viva; commit locally. CP10 completes only after the registered cells are resolved and verification passes, or is explicitly incomplete if a required run fails or the budget ends.
