# CP4 preprocessing results

P1 / M0.4, 2026-09-09. Fitted preprocessing only; no classifier or detection score.

Five pipelines passed persisted-artifact verification. Their fit populations are exactly the permitted 100,000-representative samples. Recomputed medians, observed counts and maxima match saved parameters; model-ready vectors reproduce exactly from saved transformations. No pipeline merges distinct admitted S1 groups.

| Dataset | Ledger rows | Quality-invalid rows | Also S1-conflicted | Eligible rows | Peak sampled RSS (GiB) | Runtime (s) |
|---|---:|---:|---:|---:|---:|---:|
| cic-ids-2017 | 2,830,743 | 2,926 | 0 | 2,820,797 | 4.208 | 173.799 |
| ND-UNSW-NB15-v3 | 2,365,424 | 0 | 0 | 2,361,777 | 3.991 | 130.137 |

## cic-ids-2017

[Full counts and hashes](preprocessing/cic-ids-2017.json). Quality-invalid rows remain in the ledger; S1 memberships are unchanged.

| Class | Additional quality exclusions beyond S1 | Eligible rows |
|---|---:|---:|
| benign | 2,732 | 2,269,629 |
| bot | 0 | 1,966 |
| ddos | 19 | 128,002 |
| dos_goldeneye | 5 | 10,288 |
| dos_hulk | 159 | 225,690 |
| dos_slowhttptest | 0 | 5,499 |
| dos_slowloris | 0 | 5,795 |
| ftp_patator | 4 | 7,934 |
| heartbleed | 4 | 7 |
| infiltration | 1 | 35 |
| portscan | 0 | 157,877 |
| ssh_patator | 2 | 5,895 |
| web_attack_brute_force | 0 | 1,507 |
| web_attack_sql_injection | 0 | 21 |
| web_attack_xss | 0 | 652 |

| Pipeline | Fit rows | Output fields | Validation rows | Verified distinct groups |
|---|---:|---:|---:|---:|
| primary | 100,000 | 156 | 555,026 | 2,518,050 |
| stress | 100,000 | 156 | 403,597 | 2,518,050 |

| Pilot class | Primary | Stress | CL task 1 |
|---|---:|---:|---:|
| benign | 83,122 | 89,191 | N/A |
| bot | 83 | 0 | N/A |
| ddos | 5,066 | 0 | N/A |
| dos_goldeneye | 393 | 531 | N/A |
| dos_hulk | 6,974 | 9,154 | N/A |
| dos_slowhttptest | 193 | 256 | N/A |
| dos_slowloris | 234 | 297 | N/A |
| ftp_patator | 204 | 277 | N/A |
| heartbleed | 0 | 0 | N/A |
| infiltration | 3 | 3 | N/A |
| portscan | 3,498 | 0 | N/A |
| ssh_patator | 144 | 178 | N/A |
| web_attack_brute_force | 60 | 79 | N/A |
| web_attack_sql_injection | 1 | 1 | N/A |
| web_attack_xss | 25 | 33 | N/A |

Pilot sampling is label-independent. Missing or tiny minority classes restrict any multiclass experiment; no new seed or resampling was used to hide that limitation. Full eligible validation retains its observed prevalence.

## ND-UNSW-NB15-v3

[Full counts and hashes](preprocessing/ND-UNSW-NB15-v3.json). Quality-invalid rows remain in the ledger; S1 memberships are unchanged.

| Class | Additional quality exclusions beyond S1 | Eligible rows |
|---|---:|---:|
| analysis | 0 | 1,226 |
| backdoor | 0 | 4,377 |
| benign | 0 | 2,237,731 |
| dos | 0 | 5,932 |
| exploits | 0 | 42,370 |
| fuzzers | 0 | 33,221 |
| generic | 0 | 17,468 |
| reconnaissance | 0 | 16,928 |
| shellcode | 0 | 2,367 |
| worms | 0 | 157 |

| Pipeline | Fit rows | Output fields | Validation rows | Verified distinct groups |
|---|---:|---:|---:|---:|
| primary | 100,000 | 98 | 472,509 | 2,138,042 |
| stress | 100,000 | 98 | 82,067 | 2,138,042 |
| cl | 100,000 | 98 | 424,049 | 2,138,042 |

| Pilot class | Primary | Stress | CL task 1 |
|---|---:|---:|---:|
| analysis | 65 | 52 | 34 |
| backdoor | 194 | 227 | 3 |
| benign | 94,696 | 97,056 | 98456 |
| dos | 293 | 131 | 60 |
| exploits | 1,985 | 1,028 | 564 |
| fuzzers | 1,512 | 884 | 586 |
| generic | 331 | 129 | 56 |
| reconnaissance | 808 | 412 | 217 |
| shellcode | 106 | 78 | 21 |
| worms | 10 | 3 | 3 |

Pilot sampling is label-independent. Missing or tiny minority classes restrict any multiclass experiment; no new seed or resampling was used to hide that limitation. Full eligible validation retains its observed prevalence.

## Acceptance and remaining limits

Accept P1 for the non-private binary CPU baseline pilot in double precision. Preserve each pipeline namespace and exact fitting sample. The CL transform is fitted on task 1 only. Public/private reference/training rows never influence these development parameters; a future DP experiment needs a separately reviewed public or private preprocessing path.

No clipping, feature selection or constant removal was applied. Missing and unavailable-window indicators preserve distinctions during imputation. Numeric treatment of port/protocol codes is an explicit baseline limitation; alternative encodings require controlled comparison and renewed overlap checks. Float32 conversion is not validated by these binary64 checks.

All external ordered candidate names and dictionary bytes match after stripping dictionary-key whitespace, but the dictionaries contain ambiguous direction and IAT descriptions and omit IAT units. See [external schema check](preprocessing/external-schema-check.json). Zero-shot extraction equivalence and cross-domain transformed overlap remain unresolved; no external score was inspected.

Next: CP5 / EXP-003 installs and validates the CPU baseline stack, runs the bounded resource pilot on these exact training samples, and evaluates selection-only validation. Final-test prediction remains sealed.
