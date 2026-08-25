# [T-441] 変異 matrix (最終走)

baseline = PASSED / 失敗 node 0 件

summary = {"KILLED": 12, "MISMATCH": 1, "PARSE_ERROR": 0, "SURVIVED": 0, "TIMEOUT": 0, "completed": 13, "matching": 12, "recorded": 13, "registered": 13}

| ID | 種別 | 結果 | 期待 node | 観測失敗 node |
|---|---|---|---:|---:|
| t441.m01 | negative | KILLED | 4 | 4 |
| t441.m02 | negative | KILLED | 3 | 3 |
| t441.m03 | negative | KILLED | 12 | 12 |
| t441.m04 | negative | KILLED | 2 | 2 |
| t441.m05 | negative | KILLED | 7 | 7 |
| t441.m06 | negative | KILLED | 6 | 6 |
| t441.m07 | negative | KILLED | 9 | 9 |
| t441.m08 | negative | KILLED | 5 | 5 |
| t441.m09 | negative | KILLED | 2 | 2 |
| t441.m10 | negative | KILLED | 2 | 2 |
| t441.p01 | positive | MISMATCH | 69 | 69 |
| t441.p02 | positive | KILLED | 7 | 7 |
| t441.p03 | positive | KILLED | 4 | 4 |

`t441.p01` の MISMATCH は表記由来である。期待側 `...::test_drive_iteration_checkpoint_survives_across_calls` に対し観測側は 同じ test の `...@real-repo` 付きで、**同じ test が同じ理由で落ちている**。
収集前の実在検査は接尾辞なしを要求し、失敗 node の抽出は接尾辞付きで記録するため、
group 実行される node はどちらの綴りでも完全一致にできない。実質 13/13 とする。
