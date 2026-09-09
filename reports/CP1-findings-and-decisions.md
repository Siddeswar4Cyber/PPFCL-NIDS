# CP1–CP2 audit findings and next decisions

2026-09-09. This interpretation accompanies the machine-readable audit and [generated dataset report](CP1-dataset-audit.md). All five families are complete: 69,765,764 records across 12 CSVs with zero parser error events. Artifact verification found no row-count or column-count invariant errors. These are local data observations, not classifier results.

## Findings already verified

CIC-IDS2017 contains 2,830,743 parsed records in eight files. Exact parsed-string grouping finds 308,381 excess identical rows; 698 feature vectors have conflicting labels, involving 7,020 records. There are 34,208 feature vectors occurring across files. With no IP/time/flow identifiers, equal rows cannot prove the same underlying network event, but permitting equal predictor vectors across splits can still make the evaluation misleading.

The two Fwd Header Length columns agree on every row. They must retain distinct positional IDs during import; the subsequent feature manifest can explicitly exclude the redundant second position, c055. This leaves at most 77 non-label CIC features before other training-only feature decisions. It is not a selected final feature count.

CIC has 1,358 NaN cells and 4,376 positive-infinity cells. These are cell counts, not the number of affected rows. Infiltration has only 36 records, SQL Injection 21 and Heartbleed 11 before exclusions. No resampling can create additional independent minority observations. Support after any duplicate/conflict policy must be reported before deciding the multiclass protocol.

The Thursday web file is valid UTF-8 but contains 2,180 encoded replacement characters already in the source bytes. The raw labels distinguish Brute Force, Sql Injection and XSS despite the damaged separator. Preserve raw text and define a reviewed, explicit one-to-one canonical mapping; do not pretend to reconstruct the lost character.

NF-UNSW contains 2,365,424 parsed records, 14,815 excess identical rows and no conflicting full non-label vectors. Once IP/time fields are excluded, 642 predictor vectors have conflicting labels across 3,647 records. The latter is a different diagnostic and is not a reason to claim 225,997 duplicate network events.

Its source-to-destination byte-rate field has 63,425 blank and 59,068 infinite cells; the reverse byte-rate field has 122,493 infinite cells. Investigate zero-duration/measurement semantics and the union of affected rows before defining treatment. Do not replace these with zero simply to make a model accept the data.

NF-UNSW file order includes 335,443 backward timestamp steps. Interpreting the fields as Unix milliseconds yields January 22, January 23 and February 18, 2015. January 23 contains 39,778 benign records and no attacks. Therefore, three observed calendar days are not three equivalent supervised tasks. Timestamp-based sorting alone also does not remove capture/session dependence.

BoT-IoT has 16,933,808 records, of which only 51,989 are benign. Its extreme attack prevalence must be reported when interpreting precision, accuracy and transfer. No exact full-record duplicates were found. Missing and infinite byte-rate fields occur here too; complete details are in its JSON report.

NF-CIC-IDS2018 has 20,115,529 records and 628,474 excess identical rows. There are 440 conflicting full non-label feature groups. Removing IP/time metadata exposes 14,856 conflicting predictor groups involving 554,806 rows. No blank, NaN, infinity or nonnumeric predictor cells were found. FTP_COMMAND_RET_CODE is constant in this local file. There is one backward timestamp step, so even this nearly ordered file cannot be treated as strictly sorted without checking it.

NF-ToN-IoT has 27,520,260 records and 1,816,137 excess identical rows, with no conflicting full non-label feature groups. Removing IP/time metadata exposes 129,075 conflicting predictor groups involving 968,570 rows. No blank, NaN, infinity or nonnumeric predictor cells were found, and start timestamps have no backward steps. These checks do not establish event independence or trustworthy labels. Its observed attack classes change across the seven epoch days, which matters for temporal task support.

All four NetFlow files have consistent observed Label/Attack combinations: binary 0 accompanies Benign and binary 1 accompanies every attack token. None has invalid/nonpositive timestamps or end-before-start records under the audit's millisecond interpretation. Predictor conflicts remain distinct from duplicate network events; their impact must be evaluated after the feature contract is fixed.

The four NetFlow feature dictionaries are byte-identical. Three existing ZIP manifests match their three large extracted CSVs and all four local dictionary copies (15 checks, including repeated dictionary comparisons). Package metadata dates these bags to February 28, 2025. This supports consistency with those packages, not independent publisher authenticity or equivalence to every feature mentioned in a later revised paper. No UNSW archive was present among the three inspected ZIPs.

## Decisions for CP3, before any transform is fitted

| Issue | Current decision | Validation still required |
|---|---|---|
| Source integrity | Preserve originals and bind derived artifacts to complete source hashes | Recheck hashes on reuse; record every exclusion in a derived manifest |
| Identical CIC headers | Exclude redundant c055 from the candidate feature contract | Explicit positional mapping and matching transform schema |
| Labels | Preserve raw labels; define canonical IDs and binary mappings by dataset | Verify Label/Attack consistency, unknown tokens and per-family support |
| Identifiers and time | Retain for grouping/audit; exclude from the primary predictor set | Verify semantic feature intersection before external inference |
| Near-constant columns | Treat audit flags as diagnostics; no blanket global-data feature selection | Fit any learned selector on permitted training data; check rare-class impact |
| NaN/infinity/negative fields | Register feature-specific treatment and affected-row counts before modeling | Distinguish undefined rates, invalid durations and legitimate sentinel values |
| Exact duplicates | Keep equivalent feature groups on one side of a split; compare a declared deduplicated training policy if justified | Repeat equality/overlap checks after numeric normalization and feature exclusions |
| Conflicting labels | Investigate and disclose class support; no silent relabeling or deletion | Quantify support loss under a proposed quarantine policy before accepting it |
| Temporal tasks | Derive cutoffs from valid capture periods and supported labels | Chronological and group-boundary overlap assertions; separate synthetic task-order studies |
| External domains | Maintain the predeclared untouched external performance boundary | Audit semantics without using external model scores for selection |

The proposed NF predictor contract has at most 49 fields after excluding two IP and two timestamp fields from the 53 non-label columns. Common headers and identical dictionaries do not prove those fields have equal semantics in every capture. Ports/protocols remain candidates for a registered shortcut ablation.

## What this changes in A0

The audit supports A0's separation of schema families and its split/quality gates. It does not select a model, aggregator, privacy budget or CL method. A0 remains provisional. The simple plan to use three calendar days as three NF-UNSW tasks is unsupported; CP3 must define a better-supported task stream or explicitly report a synthetic sequence. The strongest immediate work is a valid dataset protocol, not model tuning.

## Scope and limitations

The original roadmap places repository/environment at CP1, dataset audit at CP2, splits at CP3 and fitted preprocessing at CP4. This work combines CP1 and CP2. No training/test manifest or cleaned dataset has been produced yet. Global audit diagnostics are outside the proposed private-training guarantee. No live deployment, banking telemetry, corrected PCAP labels or measured detection performance is claimed.
