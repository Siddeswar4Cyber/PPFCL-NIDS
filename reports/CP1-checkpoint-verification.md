# CP1–CP2 checkpoint verification

2026-09-09. Environment and dataset audit complete; this is not model evaluation.

Goal: establish a reproducible local audit and identify data-quality constraints before splits or preprocessing fits. Prerequisites were the existing downloaded files, CP0 methodology and the source inventory. Success required every family to complete, explicit source hashes and parser diagnostics, internally consistent counts, tested audit logic, and recorded decisions.

All five families completed: 69,765,764 records across 12 CSVs, with zero parser error events. Source-file/profile counts, label totals and mutually exclusive per-column quality categories reconcile. All 15 comparisons against three local archive manifests match. See [machine-readable verification](audit/verification.json), [completed runner](audit/run.json), [audit report](CP1-dataset-audit.md) and [decisions](CP1-findings-and-decisions.md).

Four integration fixtures pass, including malformed/quoted/Latin-1 input, nonfinite values, duplicate headers, conflicting labels, cross-file equality, timestamp reversals and interrupted-stage recovery. The fixtures verify unchanged source bytes. Execution output is retained in audit-tests.log. Finalization and report scripts compile. Registry required-field and unique-ID checks pass; Markdown relative links resolve. The current audit script SHA-256 matches the completed runner's recorded source hash.

EXP-001 is COMPLETED; EXP-002 through EXP-008 remain PLANNED. DEC-013 registers the audit-derived quality/split gate. Architecture A0 remains provisional, with no empirically chosen model, privacy budget or CL method. Historical partial attempts and parser failures remain recorded rather than being counted as completed runs.

The last resumed invocation took 4,219.984 seconds, with sampled peak process RSS of 6,030,651,392 bytes. Earlier attempts incurred additional work. BoT's reported 43.483 seconds cover its completion segment only, and no aggregate runtime across interruptions is available. DuckDB's 4 GB buffer limit is not a process-RSS ceiling.

Limitations: exact parsed-string equality does not collapse numeric spellings; predictor collisions are not necessarily duplicate events; missing grouping metadata limits independence claims; matching archives do not establish publisher authenticity. No cleaned data, split manifests, model results or privacy guarantees are produced here.

Gate outcome: CP1 and CP2 complete. Next is CP3 / EXP-002: explicit label/feature contracts, proposed exclusions with minority-support counts, grouping and temporal/task manifests, followed by overlap validation before any fit. Raw datasets were not modified or downloaded. The milestone is recorded locally on codex/cp1-dataset-audit; no push is performed.
