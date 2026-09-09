# Research search and access notes

Date: 2026-09-08. Scope: targeted primary-source review for provisional A0, with foundational methods and recent IDS intersections. Inclusion: original method papers, official dataset/framework pages, primary public-sector reports, and directly relevant recent experiments. Exclusion from evidence: unsourced summaries, promotional claims, incomparable metrics presented as rankings, and search hits whose relevant content could not be verified. A deferred source is not evidence that its method is ineffective.

Earlier discovery covered financial cyber threats, NIST privacy/IDS guidance, the named FL and CL algorithms, tabular models, cryptographic protocols, dataset provenance and NetFlow v3. Exact earlier query strings were not preserved in a machine-readable log; the registry retains the resulting primary URLs, access date and reading depth. This is a reproducibility limitation. No PRISMA flow/counts or exhaustive-search claim is made.

Exact late-stage queries retained:

| Query | Purpose / disposition |
|---|---|
| `"federated" "continual" "intrusion detection" arxiv 2024 2025 2026` | Recent intersection check; promoted R052 and investigated newer work |
| `"continual learning" "intrusion detection" catastrophic forgetting replay arxiv` | IDS-specific CL context; promoted R051, R053, R054 |
| `"Continual learning for adaptive IoT network intrusion detection via domain-incremental learning methods" authors` | Metadata/source follow-up; publisher excerpts available, author list not independently verified from primary content |
| `"Federated continual representation learning" authors` | Metadata follow-up; primary author list remained unverified |

R001-R050 arose from the earlier targeted search/full-text follow-ups; R051-R054 were added in the final intersection check. Their late addition changes the contribution rationale, not the algorithm shortlist. Additional hits (SOUL, CITADEL, quantum CL, TAMR, CO-DEFEND and others) were not promoted to selection evidence: they address further supervision/architecture/protocol questions beyond the current finite pilot. Their results were not imported. They can be revisited if those questions become central.

Access limitations: direct ScienceDirect pages for R052/R053 returned 403 errors, although the search tool exposed publisher abstract/method excerpts. R054 is abstract-reviewed only. A screenshot request for R051's PDF table page failed with a cache error; no new table-cell result from that failed rendering was added. The N08 abstract range is explicitly weaker evidence than a fully checked result table.

Future searches should append exact queries, date, source versions, exclusions and retrieval failures before final report preparation. Never silently upgrade abstract screening to full-paper verification.
