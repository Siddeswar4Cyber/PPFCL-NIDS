# CP3 checkpoint verification

2026-09-09. S1 / M0.3 accepted for CP4 preprocessing work.

Implemented exact label mappings, positional candidate-feature contracts, normalized predictor grouping, conflict ledgers, global public/development/private/validation/final roles, CIC Friday stress memberships, NF chronological stress memberships, and two NF capture-period tasks. All 5,196,167 source rows in the two development families have local Parquet memberships. The other three datasets have source-level external seals.

The independent verifier reopens the persisted Parquet files and checks hashes, source metadata, source-row coverage, unique positional IDs, group-role separation, representatives, global final-test separation, stress boundaries and binary support. All checks pass. Each group has one deterministic representative. Both classes occur in every accepted role for primary/stress protocols and both NF tasks. See [verification JSON](splits/verification.json) and [support results](CP3-split-results.md).

Three split fixtures pass, covering numeric spellings, missing/signed-zero equivalence, label conflicts, cross-file grouping, time-boundary exclusion, final-role preservation and input-order invariance. The four existing audit fixtures also pass. Seven-test output is preserved in split-tests-S1.log. The initial use of a reserved SQL column name failed at the fixture stage and was corrected before any source data was processed.

The conservative policy quarantines 7,020 CIC rows and 3,647 NF-UNSW rows. Another 242,973 NF rows are excluded from the CL endpoint because their predictor group spans capture periods; primary memberships are retained. This is an evaluation choice, not proof of erroneous source labels or duplicate network events. Rare CIC class support remains inadequate for strong multiclass claims, particularly Heartbleed.

EXP-002 and DEC-014 record the accepted data protocol. A0 now has implemented audit/membership contracts; all model, FL, privacy and CL algorithm choices remain provisional. M0.3 explicitly replaces the provisional three NF tasks with two supported capture periods. Primary and stress protocols must retain separate selection namespaces.

Remaining CP4 gates: deterministic feature treatment, train-only imputation/encoding/scaling, renewed equality checks after transformations, external semantic compatibility, and explicit fitted-artifact contracts. Host/session independence remains unproven. No detector, private-training mechanism, client partition or final performance score is produced here. Raw sources remain unchanged; row-level manifests are ignored by Git, with source/output hashes and small contracts tracked locally.
