# CP1 environment and audit procedure

Date: 2026-09-09. This combined milestone covers CP1 (repository/environment) and CP2 (dataset audit) in the original roadmap, through EXP-001. Splits are CP3 and fitted preprocessing is CP4. A0's model/FL/privacy/CL candidates are unchanged.

## Environment

The project uses an isolated `.venv` with the existing CPython 3.13.13 interpreter. Audit dependencies are pinned in `requirements-audit.txt`: DuckDB 1.5.5 and psutil 7.2.2. No training stack or CUDA-enabled tensor library has been installed yet. Detecting the NVIDIA driver does not prove a training framework can use CUDA.

Measured inventory and process costs are saved in `reports/audit/environment.json` and `run.json`. Hardware discovery uses psutil and nvidia-smi; Windows CIM queries were unavailable in the sandbox. The initial uv cache was also outside the writable workspace, so setup uses a project-local cache. Installing dependencies required permitted network escalation; dataset downloads were never attempted.

From PowerShell in the project root:

```powershell
uv --cache-dir .cache/uv venv .venv --python 'C:\Users\nimma\AppData\Local\Programs\Python\Python313\python.exe' --no-python-downloads
uv --cache-dir .cache/uv pip install --python .venv\Scripts\python.exe -r requirements-audit.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -u scripts\audit_datasets.py --root 'C:\Users\nimma\Downloads\Datasets'
.venv\Scripts\python.exe scripts\check_archive_provenance.py --root 'C:\Users\nimma\Downloads\Datasets'
```

These are reproduction commands, not instructions to recreate an existing environment unnecessarily. The audit can restrict execution with `--family` (repeatable). Default memory limit is 4 GB for DuckDB's buffer manager, four compute threads, one dataset family at a time. Process RSS can exceed that buffer limit and is measured separately. Staging/spill files use a uniquely owned OS temporary directory, removed after the connection closes; sources are opened read-only. Interruption can leave a temporary directory whose removal must be restricted to that exact task-owned path.

## What the audit measures

Each source receives a complete SHA-256 byte hash and full-stream UTF-8 validation. Non-UTF-8 files use lossless Latin-1 decoding for inspection; this preserves bytes but does not assert that the labels use correct Unicode typography. The parser keeps positional IDs (`c000`, etc.) so duplicate header names cannot silently alias features. Labels and metadata are classified explicitly. Blank strings remain distinguishable from literal nonnumeric tokens.

DuckDB stages the parsed fields as strings. It records malformed-row diagnostics rather than coercing them into valid observations. Per-file results include blank/NaN/positive-infinity/negative-infinity counts, nonnumeric tokens, finite minima/maxima, negative values, integral-versus-real evidence, exact lexical constants and approximate string cardinality. Nonnumeric content in IP addresses and labels is expected, not automatically a data error.

Near-constant screening proposes a most frequent value using a streaming approximate algorithm over all rows, then counts that candidate's population frequency exactly. A verified candidate above 99.9% establishes a near-constant field. A missing flag is not proof no other value reaches the threshold. Cardinality estimates are never described as exact uniqueness counts.

Duplicate/conflict grouping operates on actual parsed field values, with no digest-based equality shortcut. It reports extra identical rows, repeated feature vectors, conflicting-label groups and vectors occurring across files. The main grouping includes all non-label fields. A separate NetFlow analysis removes IP/time metadata to expose predictor collisions; those are not necessarily duplicate network events. No source rows are deleted. Whitespace/numeric-spelling equivalence is not applied to this exact-string grouping, so later normalization requires another overlap check.

Timestamp checks report ranges, invalid/nonpositive times, end-before-start records, backward steps in file order and per-epoch-day label support. A valid timestamp range does not establish host/session-independent splits or chronological realism. Epoch-day grouping assumes milliseconds only for diagnostic interpretation, pending provenance validation. Physical-line counts are a separate byte-level diagnostic; quoted multiline records or blank lines can differ from parsed-record counts.

Local archive checks compare existing extracted files with SHA-1 manifests stored in three existing ZIPs, without extracting them. A match establishes local archive consistency, not publisher authenticity. File names/headers alone do not resolve a publication-version discrepancy.

## Correctness gates

Audit-1.3 adds continuation from a fully profiled staging database after source-hash, cached-row-count and schema checks. Its interruption/recovery fixture passes alongside the original three tests. The execution process ended again during an earlier background attempt; saved completed stages were reused rather than reported as a finished dataset. A resumed family's reported elapsed seconds cover only its completion invocation; earlier completed phase timings remain separately recorded. The latest source snapshot is preserved in `reports/audit/attempts/audit-1.3.py`.

The first complete family used audit-1.0. A 100,000-row diagnostic showed the main statistics query taking 8.41 seconds with filtered counts and 2.13 seconds using `count_if`; these timings were collected during other audit activity, so they are indicative, not a rigorous speedup benchmark. Audit-1.1 substitutes null-safe equivalent counts and passes the same fixtures. It completed CIC2017. A later task interruption ended that foreground invocation while loading the next family. Audit-1.2 adds progress persistence and resumes through a hidden helper with eight threads, rechecking full hashes before reusing completed family reports. It does not change the statistic definitions. RAM observations and runtimes must be interpreted per invocation; interrupted work is recorded separately.

Small constructed fixtures test malformed records, blank/NaN/infinite/nonnumeric values, duplicate headers, exact duplicates with conflicting labels, cross-file duplicates, reversed timestamps and file-order regressions. Fixtures also verify source bytes remain unchanged. The initial `nullstr=[]` parser option failed against the installed version; it was replaced with explicit `force_not_null` columns before any real audit ran.

Output JSON is written atomically after stages; a failed family is labeled FAILED, with its error, and must not be treated as complete. Full rows/metrics are not placed in terminal logs. Dataset-label distributions and aggregate diagnostics are public-benchmark audit observations, outside the proposed private-training guarantee.

Implementation references: [DuckDB CSV options](https://duckdb.org/docs/current/data/csv/overview), [rejected-row diagnostics](https://duckdb.org/docs/current/data/csv/reading_faulty_csv_files), and [memory tuning](https://duckdb.org/docs/current/guides/performance/how_to_tune_workloads). The implementation is validated against installed behavior rather than assuming documentation defaults.

## Next gate

Use the completed report to choose exclusions and split/group rules before fitting preprocessing. Conflicting labels, timestamp anomalies or lack of minority support may require changing the experiment protocol. CP1 does not select a model or establish a privacy guarantee.
