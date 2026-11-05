# Issue #4 offline failed-count re-verification

This post-result correction favors the corrected method by construction (Rule E5).

Baseline: `results/law1/method_a_rescored.jsonl`. Labels unchanged: `results/law1/dataset_v2.jsonl`.

Failure-word quotes compare only with failed counts; all other quotes use total or passed.

| Split | Metric | Old | New |
|---|---|---|---|
| all | tp | 73 | 73 |
| all | fp | 3 | 4 |
| all | fn | 5 | 5 |
| all | tn | 21 | 20 |
| all | f1 | 0.948051948051948 | 0.9419354838709677 |
| all | accuracy | 0.9215686274509803 | 0.9117647058823529 |
| all | error_verdicts | 0 | 0 |
| all | missing | 0 | 0 |
| calibration | tp | 20 | 20 |
| calibration | fp | 2 | 2 |
| calibration | fn | 1 | 1 |
| calibration | tn | 5 | 5 |
| calibration | f1 | 0.9302325581395349 | 0.9302325581395349 |
| calibration | accuracy | 0.8928571428571429 | 0.8928571428571429 |
| calibration | error_verdicts | 0 | 0 |
| calibration | missing | 0 | 0 |
| test | tp | 53 | 53 |
| test | fp | 1 | 2 |
| test | fn | 4 | 4 |
| test | tn | 16 | 15 |
| test | f1 | 0.954954954954955 | 0.9464285714285715 |
| test | accuracy | 0.9324324324324325 | 0.918918918918919 |
| test | error_verdicts | 0 | 0 |
| test | missing | 0 | 0 |

Coverage: {"claim_results_changed": 42, "counted_failure_quotes": 44, "counted_tests_ran": 603, "extraction_error_samples": 0, "other_claim_results_retained": 5357, "row_verdicts_changed": 1, "rows": 102, "sample_verdicts_changed": 8, "samples": 510, "stored_claims": 6080, "tests_ran_reverified": 723, "unique_traces": 44}

The host-only test selection below excludes the smoke test, whose load_evidence call reconstructs the seed case. This script does not invoke that loader.

Command: `python -B scripts/law1_reverify_failed_counts.py --output <NEW.json>`.
Test command: `python -B -m pytest --disable-plugin-autoload --noconftest -p no:cacheprovider law1/test_verify.py -q -k 'not load_evidence_on_the_committed_smoke_run'`.

All input SHA-256 values were checked before and after parsing. JSON includes old/new claim changes, per-row aggregates, corrected rows, and input hashes.

Gaps: Other claim results retained, not reverified. Methods B/C and consensus not recomputed. Dry-run extraction outputs excluded; coverage is the 102-row published Method A corpus. No suspect commands, code, hidden tests, model calls, or fresh grading executed.
