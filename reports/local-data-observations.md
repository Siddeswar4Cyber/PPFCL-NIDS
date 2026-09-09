# Local dataset inventory: header-level observations

2026-09-08. Path supplied by user: C:\Users\nimma\Downloads\Datasets.

Scope: directory/file inventory, byte sizes and raw first-line CSV headers only. This is not the full Dataset Audit Report. No rows were counted or cleaned; no labels/distributions were analyzed; no data were downloaded or modified. Machine-readable observations are in local-data-inventory.json.

| Folder | Main data files | Observed header structure |
|---|---|---|
| cic-ids-2017 | Eight day/session CSVs | 79 fields including Label; 78 distinct names after whitespace trimming |
| ND-UNSW-NB15-v3 | NF-UNSW-NB15-v3.csv | 55 fields: 53 non-label columns plus Label and Attack |
| NF-BoT-IoT-v3 | NF-BoT-IoT-v3.csv | Same 55 field names/order as other local NF files |
| NF-CIC-IDS-2018-v3 | NF-CICIDS2018-v3.csv | Same 55 field names/order |
| NF-ToN-IoT-v3 | NF-ToN-IoT-v3.csv | Same 55 field names/order |

The ND-UNSW folder spelling is preserved; the actual CSV name starts NF. Each NF directory also has NetFlow_v3_Features.csv. Three ZIP archives are present but their contents/provenance have not been validated. No PCAP appeared in the file inventory.

CIC observations: all eight headers include leading spaces in some names and two occurrences of Fwd Header Length. There are no explicit timestamp, source/destination IP or Flow ID fields in these headers; Destination Port is present. Filename-level day/session grouping is available. This limits defensible fine-grained temporal or host-disjoint splitting from these CSVs alone. The duplicate-name columns have not been compared by values and must not be silently merged.

NF observations: headers include FLOW_START_MILLISECONDS, FLOW_END_MILLISECONDS, IPV4_SRC_ADDR and IPV4_DST_ADDR. Their presence makes time/host grouping worth investigating; actual timestamp validity, sorting and session independence are unverified. These columns are metadata candidates, not automatically approved model features. Matching headers do not establish equal extractor configuration, label meaning, distribution or correct units.

[LITERATURE EVIDENCE] The original University of Queensland page describes NetFlow v3 datasets with 53 extended fields and links the temporal-analysis paper. [R024: UQ dataset documentation](https://staff.itee.uq.edu.au/marius/NIDS_datasets/), [R025: temporal-analysis paper](https://arxiv.org/abs/2503.04404).

[CURRENT DESIGN DECISION] Treat CICFlowMeter and NetFlow as distinct schema families. The NF datasets are derived versions, not the original UNSW/CIC/Ton CSV editions. A 2025/2026 re-extraction/publication does not make underlying older traffic newly collected.

[HYPOTHESIS] Use CIC-IDS2017 for benchmark/audit/model baselines and a bounded subset of existing NF v3 data for stronger temporal or external-domain tests if the audit supports it. This is an evidence-driven candidate change, not an approved final architecture. Compare scope/cost and do not pool all files indiscriminately.

Next validation: read feature dictionaries and provenance; full row/nonfinite/duplicate/label audit; inspect timestamp units/order; design independent groups and sealed test; compare possible tracks on development data only.
