# CP7 checkpoint verification

2026-09-10. C1 / H1 / M0.7 COMPLETE. This is a data-contract checkpoint: no new detector, FL, privacy or continual-learning result is claimed.

| Check | Result |
|---|---|
| Preregistration | b7453f1 precedes client construction and host support inspection |
| Client source | cd4cb57, with executed source bytes verified against Git |
| Host source | 10c2210, with executed source bytes verified against Git |
| Client manifests | 12 completed; each has five clients, unchanged parent rows and group-consistent ownership |
| Training acceptance | At least 1,000 rows and 20 per binary class for every client; attempts reproduced using training only |
| Validation eligibility | All five clients meet the 20-per-binary-class floor in every scope; no validation-driven retries |
| Fallback disclosure | Three requested alpha-0.1 scopes use the registered 10% uniform mixture |
| Host feasibility | Four fixed candidates rejected for inadequate two-class support; all retained roles and endpoint/group separation verified |
| Independent reconstruction | Client ownership recomputed with a scalar hash/CDF implementation; host components rebuilt by graph traversal and source joins |
| Regression tests | 26 tests pass in 18.349 seconds |
| Seals | No final/external model scores; no private/public-reference ownership or scores generated |

The verifier compares each manifest's parent columns and row order exactly with the saved training/validation matrices. It reconstructs allocation attempts, checks source roles and representative flags, and checks duplicate/group ownership. Host verification reloads the audited source metadata, reconstructs component/group links and both candidate rules, and compares every candidate row and exclusion reason. Support counts and feasibility decisions are then recomputed.

The H1 population contains only quality-eligible development_train and validation rows in the respective protocol. The source CSV is read for metadata staging, but no other role is admitted to the candidate population. The fixed endpoint-filter results change the development population and remain rejected candidates, not a fresh test set. Endpoint addresses are not independently certified physical-device identities.

## Evidence and reproduction

- [Results](CP7-host-client-results.md)
- [Machine-readable verification](cp7/verification.json)
- [Host analysis and candidate bindings](cp7/host-feasibility.json)
- [Protocol](../docs/CP7-host-client-protocol-C1.md)
- [Construction log](cp7-client-construction.log)
- [Host log](cp7-host-feasibility.log)
- [Verification log](cp7-verification.log)
- [Test log](cp7-tests.log)

From the project root, with the existing local source and derived artifacts:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe scripts\verify_cp7.py
.venv\Scripts\python.exe scripts\finalize_cp7.py
```

Builders refuse existing outputs. Verification/report generation does not retrain models or revise ownership. The large manifests are local artifacts under `data/clients/C1` and `data/host-feasibility/H1`, excluded from Git; tracked reports bind their hashes. Exact bytes of bound CP7 JSON reports are preserved by Git attributes. A source-only checkout cannot reproduce data checks without the local parent artifacts.

Next: CP8 neural-framework migration and optimizer stability, followed by registered central/local/FL comparisons on identical C1 assignments. The study remains a non-private synthetic-client simulation until further evidence and privacy mechanisms exist.
