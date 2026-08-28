# T-2000 B-057 変異matrix

- 最終対象commit: `cbaa49e6ab52b8f6bf3fa5665daf4b8465fce67a`
- spec SHA-256: `bab84aacf2eda90d38d7950c5b87a35d1ba9662e00d65341973a00bcf21170f6`
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
