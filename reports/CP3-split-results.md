# CP3 split and support results

S1 / M0.3, 2026-09-09. No model scores were computed. Source-wide quality and label counts were inspected before sealing.

Memberships and contracts were independently reopened and hash-checked. Source-row coverage, unique row IDs, group-role separation, one representative per group, sealed roles and stress boundaries pass. Both binary classes are present in every accepted training/reference/validation/test role and in both NF task periods.

| Dataset | Source rows | Normalized groups | Quarantined rows | Quarantined groups |
|---|---:|---:|---:|---:|
| cic-ids-2017 | 2,830,743 | 2,521,664 | 7,020 | 698 |
| ND-UNSW-NB15-v3 | 2,365,424 | 2,138,684 | 3,647 | 642 |

## cic-ids-2017

Runtime: 88.886 seconds for its full manifest invocation. See [machine-readable support](splits/cic-ids-2017.json).

| Primary role | Rows | Groups / training representatives |
|---|---:|---:|
| development_train | 1,132,190 | 1,007,679 |
| private_train | 295,154 | 252,785 |
| public_reference | 278,882 | 251,276 |
| sealed_test | 561,845 | 505,150 |
| validation | 555,652 | 504,076 |

| Canonical class | Quarantined rows | Development groups | Validation groups | Final groups | ≥5 groups in each? |
|---|---:|---:|---:|---:|---|
| benign | 736 | 837,800 | 418,847 | 419,969 | yes |
| bot | 0 | 755 | 414 | 372 | yes |
| ddos | 6 | 50,944 | 25,524 | 25,886 | yes |
| dos_goldeneye | 0 | 4,102 | 2,024 | 2,139 | yes |
| dos_hulk | 5,224 | 69,346 | 34,692 | 34,311 | yes |
| dos_slowhttptest | 0 | 2,109 | 1,031 | 1,061 | yes |
| dos_slowloris | 1 | 2,165 | 1,086 | 1,092 | yes |
| ftp_patator | 0 | 2,400 | 1,217 | 1,161 | yes |
| heartbleed | 0 | 3 | 3 | 1 | no |
| infiltration | 0 | 17 | 6 | 4 | no |
| portscan | 1,053 | 35,942 | 18,136 | 18,060 | yes |
| ssh_patator | 0 | 1,248 | 661 | 658 | yes |
| web_attack_brute_force | 0 | 569 | 309 | 297 | yes |
| web_attack_sql_injection | 0 | 9 | 4 | 5 | no |
| web_attack_xss | 0 | 270 | 122 | 134 | yes |

The five-group threshold is a pre-fit support diagnostic, not a statistical guarantee. No resampling or seed search repairs insufficient independent observations. Binary comparison is primary; multiclass/per-family conclusions must disclose these limitations. Quarantining attack-subtype conflicts also removes some binary-consistent rows.

| Stress role | Rows | Groups |
|---|---:|---:|
| development_train | 826,112 | 762,274 |
| private_train | 214,124 | 190,800 |
| public_reference | 200,358 | 189,817 |
| sealed_test | 152,395 | 123,464 |
| validation | 404,114 | 381,083 |

## ND-UNSW-NB15-v3

Runtime: 67.725 seconds for its full manifest invocation. See [machine-readable support](splits/ND-UNSW-NB15-v3.json).

| Primary role | Rows | Groups / training representatives |
|---|---:|---:|
| development_train | 945,117 | 855,764 |
| private_train | 234,386 | 212,257 |
| public_reference | 237,012 | 214,571 |
| sealed_test | 472,753 | 427,289 |
| validation | 472,509 | 428,161 |

| Canonical class | Quarantined rows | Development groups | Validation groups | Final groups | ≥5 groups in each? |
|---|---:|---:|---:|---:|---|
| analysis | 0 | 485 | 228 | 251 | yes |
| backdoor | 282 | 1,685 | 889 | 872 | yes |
| benign | 0 | 810,506 | 405,263 | 404,581 | yes |
| dos | 48 | 2,405 | 1,167 | 1,205 | yes |
| exploits | 378 | 16,864 | 8,641 | 8,528 | yes |
| fuzzers | 595 | 13,162 | 6,475 | 6,524 | yes |
| generic | 2,183 | 3,046 | 1,551 | 1,485 | yes |
| reconnaissance | 146 | 6,650 | 3,418 | 3,315 | yes |
| shellcode | 14 | 895 | 493 | 504 | yes |
| worms | 1 | 66 | 36 | 24 | yes |

The five-group threshold is a pre-fit support diagnostic, not a statistical guarantee. No resampling or seed search repairs insufficient independent observations. Binary comparison is primary; multiclass/per-family conclusions must disclose these limitations. Quarantining attack-subtype conflicts also removes some binary-consistent rows.

| Stress role | Rows | Groups |
|---|---:|---:|
| development_train | 518,956 | 503,581 |
| private_train | 129,271 | 125,367 |
| public_reference | 129,796 | 125,980 |
| sealed_test | 81,952 | 81,555 |
| validation | 82,067 | 81,655 |

242,973 rows are excluded specifically from CL because their predictor group spans the two capture periods. They retain their original primary role for the separate within-corpus study. Exclusions by class remain in the support JSON.

Chronological stress cutoffs (Unix-millisecond interpretation): [1424229622862.0, 1424246259998.0]. Role filtering and exclusion of groups spanning boundaries intentionally change the nominal proportions.

| Capture task | Primary role | Benign rows | Attack rows |
|---|---|---:|---:|
| 1 | development_train | 404,068 | 6,246 |
| 1 | private_train | 100,746 | 1,451 |
| 1 | public_reference | 101,195 | 1,525 |
| 1 | sealed_test | 201,261 | 2,982 |
| 1 | validation | 201,586 | 3,065 |
| 2 | development_train | 398,838 | 38,770 |
| 2 | private_train | 98,962 | 9,724 |
| 2 | public_reference | 99,957 | 9,926 |
| 2 | sealed_test | 199,529 | 19,575 |
| 2 | validation | 199,686 | 19,712 |

## Accepted scope and remaining gates

Accept S1 for binary baseline preparation, with disclosed conservative conflict exclusions. Both NF capture periods support the binary CL design; three natural tasks are not claimed. Multiclass support and Friday/temporal stress are separate, qualified endpoints. Models and thresholds must be selected within their own protocol namespace.

The three external datasets have immutable source-hash seals in reports/splits/external. No external performance has been observed. Shared extraction semantics, host/session dependence, any additional preprocessing collisions, training-only imputation/encoding, and privacy release/accounting remain CP4 or later gates.

No learned transform, model, client assignment or privacy guarantee is produced at CP3. Row-level Parquet manifests stay under ignored data/splits/S1; tracked contracts and reports contain their hashes. Raw sources are unchanged.
