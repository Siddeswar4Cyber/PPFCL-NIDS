# Environment and audit defense notes

**What did we implement?** An isolated Python environment, a read-only disk-backed audit, small correctness fixtures, source fingerprints, archive consistency checks and structured output reports. We have not trained an intrusion detector.

**Why audit before splitting?** Identical flows in training and test can inflate scores. We also need to know whether the data contain enough examples of each family and whether timestamps can support the proposed task sequence.

**Why use positional column IDs?** CIC2017 has two columns named Fwd Header Length. A parser may silently rename or alias them. The audit kept both positions and verified their values are identical; a later feature manifest can drop the redundant position explicitly.

**Are these exact duplicates?** The main count uses exact parsed strings in all original fields. It is not a byte-for-byte line comparison, and it does not equate different numeric spellings. Removing metadata creates a different measure: separate events can share an identical predictor vector.

**What do conflicting labels mean?** Under the audited representation, some equal feature vectors have different labels. This may reflect lost context, measurement or label problems. We must inspect their class support before choosing a quarantine rule; simply deleting difficult examples could misrepresent performance.

**Why not remove all invalid values immediately?** The audit identifies them. The next protocol decides what their feature semantics mean and how exclusions affect minority support. Any learned imputation/scaling must subsequently fit permitted training data only.

**Why is valid UTF-8 insufficient?** CIC web-attack labels already contain the Unicode replacement character in the source bytes. Decoding those bytes correctly cannot recover the lost punctuation. An explicit raw-to-canonical label map preserves provenance.

**Why not call file order chronological?** NF-UNSW contains hundreds of thousands of backward timestamp steps in its physical row order. A time-based study needs verified timestamps and an explicit ordering/group policy.

**Does the ZIP match prove authenticity?** It establishes consistency with the manifest in that local package. It does not independently authenticate the publisher, validate attack labels or prove equivalence to a later paper revision.

**Why use DuckDB?** It can process the large local tables with bounded database memory and disk spill. The buffer-manager setting is not a hard limit on total process RAM; both are documented. Approximate cardinality is labeled separately from exact equality/group counts.

**What does a successful audit prove?** It establishes measured properties of these specific files under a recorded parser/version. It does not prove generalization, correct label semantics, privacy or production readiness. Those require later evidence.
