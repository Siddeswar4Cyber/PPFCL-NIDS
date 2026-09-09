# CP1 local dataset audit

Generated UTC: 2026-09-09T04:35:02.143122+00:00. Audit observations, not detection-model results.

Sources were inspected without cleaning or fitting preprocessing. Exact-string duplicates use parsed field equality; they do not collapse different numeric spellings. Numeric diagnostics use trimmed values. Approximate cardinalities and dominant-value candidate selection are explicitly labeled in the JSON.

| Dataset | Status | Parsed rows | Parse error events | Exact duplicate excess | Conflicting feature groups |
|---|---|---:|---:|---:|---:|
| cic-ids-2017 | COMPLETED | 2,830,743 | 0 | 308,381 | 698 |
| ND-UNSW-NB15-v3 | COMPLETED | 2,365,424 | 0 | 14,815 | 0 |
| NF-BoT-IoT-v3 | COMPLETED | 16,933,808 | 0 | 0 | 0 |
| NF-CIC-IDS-2018-v3 | COMPLETED | 20,115,529 | 0 | 628,474 | 440 |
| NF-ToN-IoT-v3 | COMPLETED | 27,520,260 | 0 | 1,816,137 | 0 |

## cic-ids-2017

Authoritative JSON: [details](audit/cic-ids-2017.json). Status: COMPLETED. Runtime: 209.249 seconds. Full completed family invocation.

### Files and class support

| File | Parsed rows | Physical lines including header | Encoding |
|---|---:|---:|---|
| Friday_DDos.csv | 225,745 | 225,746 | utf-8 |
| Friday_Morning.csv | 191,033 | 191,034 | utf-8 |
| Friday_PortScan.csv | 286,467 | 286,468 | utf-8 |
| Monday.csv | 529,918 | 529,919 | utf-8 |
| Thursday_Infiltration.csv | 288,602 | 288,603 | utf-8 |
| Thursday_Web.csv | 170,366 | 170,367 | utf-8 |
| Tuesday.csv | 445,909 | 445,910 | utf-8 |
| Wednesday.csv | 692,703 | 692,704 | utf-8 |

| Raw label combination | Rows |
|---|---:|
| BENIGN | 2,273,097 |
| DoS Hulk | 231,073 |
| PortScan | 158,930 |
| DDoS | 128,027 |
| DoS GoldenEye | 10,293 |
| FTP-Patator | 7,938 |
| SSH-Patator | 5,897 |
| DoS slowloris | 5,796 |
| DoS Slowhttptest | 5,499 |
| Bot | 1,966 |
| Web Attack � Brute Force | 1,507 |
| Web Attack � XSS | 652 |
| Infiltration | 36 |
| Web Attack � Sql Injection | 21 |
| Heartbleed | 11 |

### Quality and feature implications

Cell counts (different problems can occur in the same row): blank=0, nan=1,358, positive_infinity=4,376, negative_infinity=0, nonnumeric_feature_cells=0.

Repeated trimmed headers: {'Fwd Header Length': 2}.

Duplicate-header value checks: [{'name': 'Fwd Header Length', 'columns': ['c034', 'c055'], 'unequal_rows': 0}].

Features with negative finite values (investigate semantic meaning; do not automatically clip): {'Flow Duration': 115, 'Flow Bytes/s': 85, 'Flow Packets/s': 115, 'Flow IAT Mean': 115, 'Flow IAT Max': 115, 'Flow IAT Min': 2891, 'Fwd IAT Min': 17, 'Init_Win_bytes_forward': 1001189, 'Init_Win_bytes_backward': 1441552, 'Fwd Header Length': 70, 'Bwd Header Length': 22, 'min_seg_size_forward': 35}.

Exact within-file constant columns and source-file IDs: {'Bwd PSH Flags': [0, 1, 2, 3, 4, 5, 6, 7], 'Fwd URG Flags': [0, 1, 2, 3, 5, 6, 7], 'Bwd URG Flags': [0, 1, 2, 3, 4, 5, 6, 7], 'CWE Flag Count': [0, 1, 2, 3, 5, 6, 7], 'Fwd Avg Bytes/Bulk': [0, 1, 2, 3, 4, 5, 6, 7], 'Fwd Avg Packets/Bulk': [0, 1, 2, 3, 4, 5, 6, 7], 'Fwd Avg Bulk Rate': [0, 1, 2, 3, 4, 5, 6, 7], 'Bwd Avg Bytes/Bulk': [0, 1, 2, 3, 4, 5, 6, 7], 'Bwd Avg Packets/Bulk': [0, 1, 2, 3, 4, 5, 6, 7], 'Bwd Avg Bulk Rate': [0, 1, 2, 3, 4, 5, 6, 7], 'Label': [3]}.

Verified dominant candidates occupying at least 99.9% of the family: Bwd PSH Flags (100.0000%); Fwd URG Flags (99.9889%); Bwd URG Flags (100.0000%); RST Flag Count (99.9758%); CWE Flag Count (99.9889%); ECE Flag Count (99.9757%); Fwd Avg Bytes/Bulk (100.0000%); Fwd Avg Packets/Bulk (100.0000%); Fwd Avg Bulk Rate (100.0000%); Bwd Avg Bytes/Bulk (100.0000%); Bwd Avg Packets/Bulk (100.0000%); Bwd Avg Bulk Rate (100.0000%).

No supported timestamp columns: fine chronological and host/session-disjoint guarantees cannot be established from these CSVs alone.

## ND-UNSW-NB15-v3

Authoritative JSON: [details](audit/ND-UNSW-NB15-v3.json). Status: COMPLETED. Runtime: 422.532 seconds. Full completed family invocation.

### Files and class support

| File | Parsed rows | Physical lines including header | Encoding |
|---|---:|---:|---|
| NF-UNSW-NB15-v3.csv | 2,365,424 | 2,365,425 | utf-8 |

| Raw label combination | Rows |
|---|---:|
| 0 / Benign | 2,237,731 |
| 1 / Exploits | 42,748 |
| 1 / Fuzzers | 33,816 |
| 1 / Generic | 19,651 |
| 1 / Reconnaissance | 17,074 |
| 1 / DoS | 5,980 |
| 1 / Backdoor | 4,659 |
| 1 / Shellcode | 2,381 |
| 1 / Analysis | 1,226 |
| 1 / Worms | 158 |

### Quality and feature implications

Cell counts (different problems can occur in the same row): blank=63,425, nan=0, positive_infinity=181,561, negative_infinity=0, nonnumeric_feature_cells=0.

Repeated trimmed headers: {}.

Duplicate-header value checks: [].

Features with negative finite values (investigate semantic meaning; do not automatically clip): {}.

Exact within-file constant columns and source-file IDs: {}.

Verified dominant candidates occupying at least 99.9% of the family: SRC_TO_DST_IAT_MIN (99.9385%); DST_TO_SRC_IAT_MIN (99.9906%).

After excluding identifiers/time, predictor collisions: {'distinct_feature_vectors': 2138684, 'repeated_feature_rows': 226740, 'duplicate_row_excess': 225997, 'conflicting_feature_groups': 642, 'rows_in_conflicting_groups': 3647, 'cross_file_feature_groups': 0}. These may be separate events with identical summaries and must not be called raw duplicate flows.

### Time diagnostics

- start_min_ms: 1421927376907.0
- start_max_ms: 1424262564927.0
- end_before_start: 0
- nonpositive_time: 0
- invalid_time: 0
- backward_steps_in_file_order: 335,443
- start_min_ms, interpreted as Unix milliseconds: 2015-01-22T11:49:36.907000+00:00
- start_max_ms, interpreted as Unix milliseconds: 2015-02-18T12:29:24.927000+00:00

Epoch-day/label support is retained in JSON. Calendar conversion is diagnostic; capture provenance and chronology must be reviewed before a temporal split.

## NF-BoT-IoT-v3

Authoritative JSON: [details](audit/NF-BoT-IoT-v3.json). Status: COMPLETED. Runtime: 43.483 seconds. Completion invocation only; earlier stage timings remain in stage_timings; total wall time unavailable across interruption.

### Files and class support

| File | Parsed rows | Physical lines including header | Encoding |
|---|---:|---:|---|
| NF-BoT-IoT-v3.csv | 16,933,808 | 16,933,809 | utf-8 |

| Raw label combination | Rows |
|---|---:|
| 1 / DoS | 8,034,190 |
| 1 / DDoS | 7,150,882 |
| 1 / Reconnaissance | 1,695,132 |
| 0 / Benign | 51,989 |
| 1 / Theft | 1,615 |

### Quality and feature implications

Cell counts (different problems can occur in the same row): blank=387,350, nan=0, positive_infinity=1,716,860, negative_infinity=0, nonnumeric_feature_cells=0.

Repeated trimmed headers: {}.

Duplicate-header value checks: [].

Features with negative finite values (investigate semantic meaning; do not automatically clip): {}.

Exact within-file constant columns and source-file IDs: {}.

Verified dominant candidates occupying at least 99.9% of the family: RETRANSMITTED_IN_BYTES (99.9422%); RETRANSMITTED_IN_PKTS (99.9422%); RETRANSMITTED_OUT_BYTES (99.9377%); RETRANSMITTED_OUT_PKTS (99.9377%); ICMP_TYPE (99.9361%); ICMP_IPV4_TYPE (99.9361%); DNS_QUERY_ID (99.9590%); DNS_QUERY_TYPE (99.9590%); DNS_TTL_ANSWER (99.9857%); FTP_COMMAND_RET_CODE (99.9977%).

After excluding identifiers/time, predictor collisions: {'distinct_feature_vectors': 16687490, 'repeated_feature_rows': 246318, 'duplicate_row_excess': 201424, 'conflicting_feature_groups': 44894, 'rows_in_conflicting_groups': 164051, 'cross_file_feature_groups': 0}. These may be separate events with identical summaries and must not be called raw duplicate flows.

### Time diagnostics

- start_min_ms: 1526344031665.0
- start_max_ms: 1529381833932.0
- end_before_start: 0
- nonpositive_time: 0
- invalid_time: 0
- backward_steps_in_file_order: 40,736
- start_min_ms, interpreted as Unix milliseconds: 2018-05-15T00:27:11.665000+00:00
- start_max_ms, interpreted as Unix milliseconds: 2018-06-19T04:17:13.932000+00:00

Epoch-day/label support is retained in JSON. Calendar conversion is diagnostic; capture provenance and chronology must be reviewed before a temporal split.

## NF-CIC-IDS-2018-v3

Authoritative JSON: [details](audit/NF-CIC-IDS-2018-v3.json). Status: COMPLETED. Runtime: 1486.263 seconds. Full completed family invocation.

### Files and class support

| File | Parsed rows | Physical lines including header | Encoding |
|---|---:|---:|---|
| NF-CICIDS2018-v3.csv | 20,115,529 | 20,115,530 | utf-8 |

| Raw label combination | Rows |
|---|---:|
| 0 / Benign | 17,514,626 |
| 1 / DDOS_attack-HOIC | 1,032,311 |
| 1 / FTP-BruteForce | 386,720 |
| 1 / DDoS_attacks-LOIC-HTTP | 288,589 |
| 1 / Bot | 207,703 |
| 1 / SSH-Bruteforce | 188,474 |
| 1 / Infilteration | 188,152 |
| 1 / DoS_attacks-SlowHTTPTest | 105,550 |
| 1 / DoS_attacks-Hulk | 100,076 |
| 1 / DoS_attacks-GoldenEye | 61,300 |
| 1 / DoS_attacks-Slowloris | 36,040 |
| 1 / DDOS_attack-LOIC-UDP | 3,450 |
| 1 / Brute_Force_-Web | 1,618 |
| 1 / Brute_Force_-XSS | 480 |
| 1 / SQL_Injection | 440 |

### Quality and feature implications

Cell counts (different problems can occur in the same row): blank=0, nan=0, positive_infinity=0, negative_infinity=0, nonnumeric_feature_cells=0.

Repeated trimmed headers: {}.

Duplicate-header value checks: [].

Features with negative finite values (investigate semantic meaning; do not automatically clip): {}.

Exact within-file constant columns and source-file IDs: {'FTP_COMMAND_RET_CODE': [0]}.

Verified dominant candidates occupying at least 99.9% of the family: FTP_COMMAND_RET_CODE (100.0000%).

After excluding identifiers/time, predictor collisions: {'distinct_feature_vectors': 17454518, 'repeated_feature_rows': 2661011, 'duplicate_row_excess': 2646080, 'conflicting_feature_groups': 14856, 'rows_in_conflicting_groups': 554806, 'cross_file_feature_groups': 0}. These may be separate events with identical summaries and must not be called raw duplicate flows.

### Time diagnostics

- start_min_ms: 1518611287705.0
- start_max_ms: 1520021065524.0
- end_before_start: 0
- nonpositive_time: 0
- invalid_time: 0
- backward_steps_in_file_order: 1
- start_min_ms, interpreted as Unix milliseconds: 2018-02-14T12:28:07.705000+00:00
- start_max_ms, interpreted as Unix milliseconds: 2018-03-02T20:04:25.524000+00:00

Epoch-day/label support is retained in JSON. Calendar conversion is diagnostic; capture provenance and chronology must be reviewed before a temporal split.

## NF-ToN-IoT-v3

Authoritative JSON: [details](audit/NF-ToN-IoT-v3.json). Status: COMPLETED. Runtime: 2680.909 seconds. Full completed family invocation.

### Files and class support

| File | Parsed rows | Physical lines including header | Encoding |
|---|---:|---:|---|
| NF-ToN-IoT-v3.csv | 27,520,260 | 27,520,261 | utf-8 |

| Raw label combination | Rows |
|---|---:|
| 0 / Benign | 16,792,214 |
| 1 / ddos | 4,141,256 |
| 1 / xss | 2,834,435 |
| 1 / password | 1,594,777 |
| 1 / scanning | 1,358,977 |
| 1 / injection | 381,777 |
| 1 / dos | 203,456 |
| 1 / Backdoor | 203,384 |
| 1 / mitm | 6,013 |
| 1 / ransomware | 3,971 |

### Quality and feature implications

Cell counts (different problems can occur in the same row): blank=0, nan=0, positive_infinity=0, negative_infinity=0, nonnumeric_feature_cells=0.

Repeated trimmed headers: {}.

Duplicate-header value checks: [].

Features with negative finite values (investigate semantic meaning; do not automatically clip): {}.

Exact within-file constant columns and source-file IDs: {}.

Verified dominant candidates occupying at least 99.9% of the family: none found (see JSON for stage status).

After excluding identifiers/time, predictor collisions: {'distinct_feature_vectors': 14729992, 'repeated_feature_rows': 12790268, 'duplicate_row_excess': 12660567, 'conflicting_feature_groups': 129075, 'rows_in_conflicting_groups': 968570, 'cross_file_feature_groups': 0}. These may be separate events with identical summaries and must not be called raw duplicate flows.

### Time diagnostics

- start_min_ms: 1556028590618.0
- start_max_ms: 1556549155177.0
- end_before_start: 0
- nonpositive_time: 0
- invalid_time: 0
- backward_steps_in_file_order: 0
- start_min_ms, interpreted as Unix milliseconds: 2019-04-23T14:09:50.618000+00:00
- start_max_ms, interpreted as Unix milliseconds: 2019-04-29T14:45:55.177000+00:00

Epoch-day/label support is retained in JSON. Calendar conversion is diagnostic; capture provenance and chronology must be reviewed before a temporal split.

## Gate for the next checkpoint

Use this audit to register deterministic cleaning/exclusion rules and split manifests before model fitting. Keep duplicate groups together, investigate contradictory labels, verify feature semantics and time support, and do not use final-test performance to choose rules. No source data have been repaired by this audit.

Limits: no PCAP relabeling; no proof of extraction semantics from a matching header; no cross-dataset full-row duplicate join; no host/session independence certificate; no numeric-normalized duplicate equivalence; no train/test split created. Near-constant screening can miss a dominant value if its approximate candidate is wrong.
