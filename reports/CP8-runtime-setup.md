# CP8 runtime installed; migration checks next

2026-09-10. The user explicitly approved the package download and subsequently sent continue, authorizing CP8 continuation. PyTorch 2.10.0+cu128 and its required dependencies are installed in the project virtual environment. The previously rejected installation is resolved. The project is saved at this setup checkpoint; CP8 remains incomplete.

- Python: 3.13.13.
- PyTorch wheel CUDA runtime: 12.8.
- GPU: NVIDIA GeForce RTX 4050 Laptop GPU; 5.997 GiB reported device memory.
- Driver query: NVIDIA GeForce RTX 4050 Laptop GPU, 581.86, 6141 MiB.
- CPU float64 and CUDA float32 matrix multiplication and autograd checks both pass with zero error against a fixed NumPy arithmetic fixture.
- The original ten baseline dependency versions are unchanged.

The smoke check uses deterministic algorithms, disables TF32, limits CPU threads to two and caps the CUDA allocator at 4 GiB. Peak allocated/reserved GPU memory for this tiny fixture was 67,112,448 / 69,206,016 bytes. These measurements describe setup verification only; they do not estimate project training resources. No dataset was opened and no project model was trained.

The package inventory is saved in [requirements-neural-lock.txt](../requirements-neural-lock.txt). The CUDA-specific install specification is [requirements-torch.txt](../requirements-torch.txt); use the official CUDA index for the Torch build rather than assuming it is on the default package index. The full inventory records versions, not wheel-content hashes or a portable cross-platform environment.

The earlier [preparation report](CP8-preparation-status.md) is historical and retains the original blocked state. Current machine-readable setup evidence is [runtime-installation.json](cp8/runtime-installation.json). The NumPy artifact checks remain valid; successful installation does not establish saved-model Torch migration or optimizer correctness.

Next, under the user's continuation instruction: execute the preregistered N1 CPU/CUDA migration and serialization checks, implement and verify native-Adam gradient/update checks, then run the bounded 24-fit stability comparison. Save decisions before advancing to CP9 central/local/federated pilots. No new scope or candidate budget is authorized by this setup check.
