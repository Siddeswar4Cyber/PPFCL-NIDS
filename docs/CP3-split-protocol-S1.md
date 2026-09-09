# CP3: split and feature protocol S1

2026-09-09. Methodology M0.3 supplements M0.2 at the data gate. No model has been fitted. Source-wide quality and label support were inspected before sealing. Memberships are generated for CIC2017 and NF-UNSW; the other three domains remain external source-level seals.

## Feature and label contracts

CIC uses 77 candidate predictors: retain source order, exclude Label and the second identical Fwd Header Length column (c055). NetFlow uses 49 candidate predictors after excluding Label, Attack, both IP addresses and both timestamps. This is an input contract, not an empirically selected feature set. Constant/near-constant removal and categorical encoding are training-only CP4 decisions. Ports and protocol fields are retained for a later declared shortcut ablation.

Each contract contains every exact raw label and its dataset-scoped canonical label. Lowercase ASCII alphanumeric tokens are joined by underscores, with uniqueness checked. Damaged CIC separators are mapped by exact raw-key lookup; no lost character is reconstructed. Benign maps to binary 0; other registered labels map to 1. NetFlow's supplied binary column must agree. Unknown labels stop processing. Labels across different datasets are not merged into a common multiclass taxonomy.

The grouping projection trims numeric strings, casts predictors to DOUBLE, maps nonfinite/uncastable/blank values to NULL and normalizes signed zero. Finite negative values remain distinguishable. Equality is checked on the actual ordered numeric vectors. Thus 1, 1.0 and 1e0 cannot cross roles as different strings. A SHA-256 digest of the JSON vector, prefixed S1|17|, identifies groups only after checking digest uniqueness across all distinct vectors. Exact source bytes and positional row IDs bind the result to the audit.

This projection is deterministic and does not estimate a statistic. It anticipates missing-value handling without fitting imputation. Any CP4 transform that changes equality requires another collision/overlap check; reducing features can merge groups. Existing S1 memberships must not silently be reused if a later transform creates cross-role equality.

## Roles and conflict policy

The first eight digest hex digits modulo 1000 assign each entire group: 0–99 public_reference, 100–499 development_train, 500–599 private_train, 600–799 validation, 800–999 sealed_test. These are expected group proportions, not guaranteed row proportions or stratification. No search across seeds to improve support is allowed. Report actual class/group support and narrow unsupported claims.

Groups with more than one canonical label are quarantined from all fitted/evaluated protocols. The report distinguishes binary conflicts from attack-subtype conflicts and quantifies loss by raw-class mapping. This conservative rule avoids treating inconsistent subtype labels as ground truth; it is assessed against minority support before this checkpoint is accepted. Quarantined rows remain in the source and membership ledger. Future robustness evaluation on these rows requires a separate preregistered endpoint, not silent relabeling.

Every group has one deterministic representative: the lowest (source_file, parsed_row). The planned training policy uses representatives only; validation/final evaluation retains all eligible rows and also reports a unique-vector sensitivity result. Natural source prevalence is therefore conditional on disclosed conflict exclusions. Neither a duplicate vector nor its representative proves an independent network event.

Development model selection uses development_train and validation. Public-reference groups are reserved for public privacy configuration; private_train groups are reserved for privacy-confirmatory fitting. These roles are globally disjoint across all S1 protocols. DP release/accounting and validation access still need review; disjointness alone is not a privacy guarantee. Clients will be assigned only inside eligible training roles later.

## Evaluation protocols

Primary: a group-disjoint within-corpus study for each schema family. It supports comparison under the observed capture mixture, not future-time or institution-independent claims. The sealed_test role is never a training, public-reference or validation role in any S1 protocol.

CIC Friday stress: only groups containing no Friday record may supply training/reference/validation. Only sealed groups touching Friday supply the stress test; all other groups are excluded from this stress protocol. A Friday group can include an identical earlier-day record, so this is a group-based Friday holdout, not a pure per-row day filter. Attack/day confounding and unseen attacks must be reported.

NF chronological stress: fix exact empirical 60th/80th percentile start timestamps before model scores. Training/reference groups must finish strictly before the first cutoff. Validation groups must start at/after the first and finish before the second. Test groups must start at/after the second. They must ALSO have the corresponding globally reserved primary role. Boundary-spanning and other ineligible groups are excluded. Resulting row proportions are not 60/20/20. The role restriction prevents a final-test row from entering another protocol's training. This is a conservative timestamp-ordered stress study; shared hosts/sessions still limit independence.

Each protocol has its own selection namespace. Chronological/Friday stress configurations and thresholds may use only that protocol's eligible development and validation populations, never parameters selected using later/Friday primary data. Baselines must be refitted for each protocol. No stress/final performance is inspected until the common finalization stage.

NF continual-learning tasks: use two observed capture periods, January 22–23 and February 18, 2015, under the local timestamp interpretation. The threshold is UTC epoch day 16484. A group whose start/end span this boundary is excluded from CL. Each period keeps the same public/development/private/validation/test group roles. Iterate training periods in order and evaluate on fixed same-period held-out groups. This measures retention/adaptation across two capture periods; within-task evaluation is not strictly future-only. Two tasks replace the provisional three-task cap because the audit's intermediate day contains only benign traffic. Do not claim three naturally comparable tasks. CIC CL tasks are not defined by S1.

The local NetFlow dictionary states milliseconds for flow start/end. The ranges align with the capture dates; Unix origin/timezone and real session identity are not independently certified. The [publisher dataset page](https://staff.itee.uq.edu.au/marius/NIDS_datasets/) confirms the NF-UNSW total but its displayed minority label counts differ from the local observed labels. Local source-bound counts govern S1; no relabeling to match the webpage is permitted.

## Artifacts and acceptance

Ignored local data/splits/S1/<family>/memberships.parquet stores every original parsed row's source_file, parsed_row, group, canonical/binary labels, role assignments, task, representative flag, group sizes and time diagnostics. No raw feature or IP payload is copied into this manifest. contract.json stores positional feature/label mappings and source hashes. Tracked reports/splits JSON files bind manifests and contracts to SHA-256 hashes and contain support/exclusion statistics. Existing output directories are immutable; regeneration requires a new version or explicit recovery from an incomplete attempt.

Required checks: source hashes match CP2; parsed count and row IDs cover each source exactly; labels are known; binary mappings agree; digest collisions are absent; each group has exactly one representative and one role per protocol; final-test roles never enter another protocol's training or selection; boundary exclusions hold; all binary roles/tasks have measurable support; loss of rare classes limits multiclass claims. Constructed fixtures cover numeric spellings, NULL/signed-zero equality, conflicting labels, cross-file groups, boundary crossing and input-order invariance. CP4 additionally verifies the fitted transformation pipeline.

External NF-CIC2018, NF-ToN and NF-BoT remain sealed as complete source-hash manifests. Their audit is already public project knowledge, but no performance feedback or externally fitted adapter enters selection. Identical headers do not yet establish shared units/extractor semantics. CP4 must verify the common contract before zero-shot inference; external multiclass transfer is not authorized by a matching label spelling.
