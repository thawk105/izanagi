# T-2000 B-057 変異matrix

- 最終対象commit: `de8be5cce11c9d5bed689fc1bf417ba872c08501`
- spec SHA-256: `c8911ebe7052094a144105ea37673e5910bf97b04fe72dd74b9f777bf0c4291d`
- baseline: PASSED
- summary: KILLED=6, SURVIVED=0, TIMEOUT=0, PARSE_ERROR=0, MISMATCH=0

| ID | 結果 | exact failed node |
|---|---|---|
| M1 | KILLED | `test_t2000_classifier_m1_cache_hit_has_one_reason` |
| M2 | KILLED | `test_t2000_classifier_m2_stage_has_one_reason` |
| M3 | KILLED | `test_t2000_classifier_m3_non_file_git_attempt_has_one_reason` |
| M4 | KILLED | `test_t2000_identity_m4_dependency_mismatch_has_one_reason` |
| M5 | KILLED | `test_t2000_redaction_m5_secret_fixture_is_rejected` |
| M6 | KILLED | `test_t2000_classifier_m6_invalid_control_has_one_reason` |

各変異の失敗node集合は事前登録と完全一致した。変異後の診断文字列だけでなく、classifier受理集合、dependency identity、publish redactionの実効gateを検出対象とした。
