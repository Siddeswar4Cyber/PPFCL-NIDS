# CP8 preparation: artifact checks pass; runtime pending

2026-09-10. N1 / M0.8. CP8 remains IN PROGRESS. Four saved selected seed-17 MLPs pass independent NumPy reconstruction over all corresponding validation rows. PyTorch is not installed or executed, and no new model fit, FL run or private/CL result is recorded.

| Dataset / scope | Inputs | Validation rows | Maximum probability difference | Changed decisions at 0.5 |
|---|---:|---:|---:|---:|
| cic-ids-2017 / primary | 172 | 533,069 | 2.1684e-18 | 0 |
| cic-ids-2017 / stress | 172 | 391,594 | 9.69352e-26 | 0 |
| ND-UNSW-NB15-v3 / primary | 98 | 472,509 | 3.59989e-21 | 0 |
| ND-UNSW-NB15-v3 / stress | 98 | 82,067 | 1.18585e-20 | 0 |

Total checked: 1,479,239 predictions across separate, reused validation namespaces. These are not independent evaluation samples or fresh detection scores. Maximum error is below the preregistered 1e-12 tolerance in every scope. Artifact SHA bindings pass. All 29 existing and new tests pass; the three new tests exercise explicit affine/ReLU/sigmoid arithmetic, orientation/bias handling, a partial prediction batch and invalid inputs. They do not test Torch.

The preflight worker took 7.692 seconds; supervised time was 9.181 seconds. Peak sampled worker-tree RSS was 2.263 GiB (0.5-second sampling), below 12 GiB. No GPU allocation measurement exists.

## Prepared implementation and experiment

The prediction helper contains a lazy-import Torch converter that transposes weights into three Linear layers and returns logits. Its Torch path remains unexecuted. The committed protocol fixes CPU/CUDA prediction tolerances, save/load checks, native Adam gradient/update checks and a 24-fit stability budget: two learning rates, three seeds and four separate namespaces, each for 20 epochs. Training implementation and runtime validation are still outstanding. No best learning rate or neural stability claim is made.

The native Adam formula places epsilon after second-moment bias correction, whereas the installed scikit implementation places epsilon before that correction. Consequently the protocol treats fresh Torch training as a new controlled experiment, not an exact continuation of the scikit optimizer. [PyTorch 2.10 Adam algorithm](https://docs.pytorch.org/docs/2.10/generated/torch.optim.Adam.html).

## Blocking action and exact resumption

Automatic approval review rejected the package installation before execution: it interpreted the original no-download instruction as requiring explicit later authorization for PyTorch. The requested action is to download torch==2.10.0 and its required dependencies from the official CUDA 12.8 package index and install them into this project’s .venv. This adds executable packages, uses download bandwidth and disk space, and modifies the project environment. No dataset or GPU driver download is proposed. No alternate installation was attempted.

After explicit approval, use: `uv pip install --python .venv/Scripts/python.exe torch==2.10.0 --index-url https://download.pytorch.org/whl/cu128`. Capture exact resolved dependencies and verify CUDA on the actual RTX 4050 before executing N1. The [official wheel matrix](https://pytorch.org/get-started/previous-versions/) lists this Windows installation target; compatibility has not yet been established locally.

Run CPU/CUDA migration and serialization checks, implement and test optimizer/gradient semantics, commit the training runner before new scores, execute the registered fits, independently recompute metrics, then update checkpoint and architecture decisions. CP9 FL pilots remain gated on that review.

Evidence: [N1 protocol](../docs/CP8-neural-migration-protocol-N1.md), [machine-readable preparation](cp8/preparation.json), [preflight log](cp8/preparation.log), [test log](cp8-tests.log). Preregistration/code commit: d574237712d190faebdbc6f4fbbadefecbbe7f2c.
