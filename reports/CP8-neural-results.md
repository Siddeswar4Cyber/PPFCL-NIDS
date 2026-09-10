# CP8 neural migration and stability results

N1 / M0.8, 2026-09-10. CP8 is COMPLETE: four saved-model migration checks and all 24 registered fresh-training fits completed; all 32 tests and artifact/prediction verification pass. Eligibility is decided separately in each dataset/protocol namespace. This checkpoint establishes a tested neural implementation and bounded validation evidence, with no FL, privacy or CL result.

## Runtime and migration

PyTorch 2.10.0+cu128 runs with the bundled CUDA 12.8 runtime on the RTX 4050 Laptop GPU. The explicitly approved installation preserves all ten baseline dependency versions. CPU/GPU setup arithmetic passes; the environment inventory is pinned locally. [Setup evidence](CP8-runtime-setup.md).

| Scope | CPU maximum probability error | CUDA maximum probability error | Changed CUDA decisions at 0.5 | Save/load maximum error |
|---|---:|---:|---:|---:|
| cic-ids-2017 / primary | 9.4369e-16 | 1.06579e-06 | 0 | 0 |
| cic-ids-2017 / stress | 3.88578e-16 | 1.09045e-06 | 0 | 0 |
| ND-UNSW-NB15-v3 / primary | 2.22045e-16 | 3.24963e-07 | 0 | 0 |
| ND-UNSW-NB15-v3 / stress | 2.22045e-16 | 1.73684e-07 | 0 | 0 |

Each migration checks full corresponding validation against its saved B2-selected seed-17 MLP reference. CPU float64 errors are within 1e-12; CUDA float32 errors are within 1e-4 and changed-decision rates within 1e-4. The verifier reloads the saved Torch weights and reproduces every saved CPU/CUDA probability. These are representation checks, not new detection improvements.

The three-step float64 optimizer fixture independently reconstructs BCE, weight-only L2 gradients and native Adam updates, including a two-row final batch. Extreme-logit BCE remains finite. Native Torch Adam differs from scikit in epsilon placement; no training-trajectory equivalence is claimed.

## Fixed stability comparison

Every fit uses the unchanged 100,000 S1 training representatives, B2-selected representation and full validation in its own scope. CIC uses P2 and 172 augmented fields; NF uses P1 and 98 fields. Hidden widths stay 64/32, with a single binary logit. Both learning rates receive 20 epochs, batch size 256 and seeds 17/29/43. Initialization and epoch-order streams are paired across learning-rate candidates. Shared development preprocessing remains non-private.

| Scope | Learning rate | Macro-F1 mean ± sample SD | AP mean | N1 eligible |
|---|---:|---:|---:|---|
| cic-ids-2017 / primary | 0.001 | 0.968101 ± 0.005638 | 0.993316 | Yes |
| cic-ids-2017 / primary | 0.0003 | 0.962509 ± 0.004384 | 0.991119 | Yes |
| cic-ids-2017 / stress | 0.001 | 0.985157 ± 0.000415 | 0.995722 | Yes |
| cic-ids-2017 / stress | 0.0003 | 0.985425 ± 0.000176 | 0.996753 | Yes |
| ND-UNSW-NB15-v3 / primary | 0.001 | 0.999024 ± 0.000127 | 0.999702 | Yes |
| ND-UNSW-NB15-v3 / primary | 0.0003 | 0.998935 ± 0.000074 | 0.999206 | Yes |
| ND-UNSW-NB15-v3 / stress | 0.001 | 0.998805 ± 0.000799 | 0.999427 | Yes |
| ND-UNSW-NB15-v3 / stress | 0.0003 | 0.999188 ± 0.000090 | 0.998776 | Yes |

| Scope | Historical B2 MLP macro-F1 mean ± SD | Selected N1 candidate |
|---|---:|---|
| cic-ids-2017 / primary | 0.950916 ± 0.022140 | lr001 |
| cic-ids-2017 / stress | 0.979036 ± 0.010095 | lr0003 |
| ND-UNSW-NB15-v3 / primary | 0.999063 ± 0.000032 | lr001 |
| ND-UNSW-NB15-v3 / stress | 0.999248 ± 0.000062 | lr0003 |

4 of four namespaces have a candidate eligible for a later pilot. Eligibility requires three successful fits, sample SD <=0.01, and mean macro-F1/AP losses <=0.002 relative to that same namespace’s B2 selected MLP. Eligible candidates rank by mean macro-F1, mean AP, then lower learning rate. No additional candidates were introduced after scores. Any candidate that fails these gates remains reported, rather than being relabeled a failed execution.

The historical B2 comparison changes framework, optimizer semantics and epoch budget together; differences cannot be attributed solely to Adam or GPU use. Three seeds reuse the same training and validation populations. Sample SD is conditional model randomness, not a population confidence interval or proof of robustness. Cross-scope results cannot select an earlier temporal protocol’s settings.

The strongest B2 Extra Trees references remain in the detector comparison. A neural implementation that is eligible for FL experiments is not automatically the final best detector. NF host reuse and the unsupported H1 host-separated binary challenge remain limitations. Synthetic C1 clients must not be described as banks or independent hosts.

Each run records standard binary and attack-family metrics at 0.5, the validation-fitted <=1% FPR operating point, probabilities, initial/final weights, losses and artifact hashes. Calibrated validation scores are tuning results; the threshold has not been confirmed on a held-out final test.

## Resources and verification

The 24 fresh fits used 518.727 measured training seconds and 708.475 supervised worker seconds. Migration adds 27.482 supervised seconds. These totals exclude package download, prior preparation, tests and final verification.

Maximum sampled worker-tree RSS across all 28 workers was 2.918 GiB; maximum CUDA allocated/reserved memory was 0.137 / 0.152 GiB. Every worker stayed below the 600-second, 12-GiB process-tree and 4-GiB CUDA allocator limits. RSS sampling is every 0.5 seconds and excludes the supervising parent; CUDA counters cover the Torch allocator, not every driver allocation.

The verifier checks report/source/model/probability hashes, reloads and reproduces all 28 runs’ full validation predictions, recomputes reported metrics and operating points, separately checks macro-F1 with sklearn, and confirms registered initialization and pairing across candidates. It applies the fixed selection rule without accessing final/private/public-reference/external data.

Next: preregister CP9 central/local/FedAvg comparisons on identical C1 assignments, with explicit objective weighting and matched training budgets. Any scope without an eligible N1 candidate needs a separate recorded amendment before advancement. Model selection, FL, DP and CL remain provisional; final/external scores remain sealed.

Evidence: [N1 protocol](../docs/CP8-neural-migration-protocol-N1.md), [selection and seed values](cp8/selection.json), [verification](cp8/verification.json), [32-test log](cp8/runtime-tests.log), [optimizer tests](cp8/optimizer-tests.log), [checkpoint checks](CP8-checkpoint-verification.md), [viva notes](../docs/CP8-viva.md).
