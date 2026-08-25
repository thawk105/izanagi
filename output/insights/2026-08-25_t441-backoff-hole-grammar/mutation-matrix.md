# [T-441] 変異 matrix (最終走。main 取り込み後の tip `b78c8ba6` で実施)

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
| t441.m07 | negative | KILLED | 20 | 20 |
| t441.m08 | negative | KILLED | 7 | 7 |
| t441.m09 | negative | KILLED | 2 | 2 |
| t441.m10 | negative | KILLED | 2 | 2 |
| t441.p01 | positive | MISMATCH | 86 | 86 |
| t441.p02 | positive | KILLED | 7 | 7 |
| t441.p03 | positive | KILLED | 4 | 4 |

## MISMATCH 1 件は表記由来である

`t441.p01` の差分は 1 件で、期待側 `...::test_drive_iteration_checkpoint_survives_across_calls` に対し観測側は同じ test の `...@real-repo` 付きである。**同じ test が同じ理由で落ちている。**
収集前の実在検査は接尾辞なしの nodeid を要求し、失敗 node の抽出は xdist の group 接尾辞付きで
記録するため、group 実行される node はどちらの綴りでも完全一致にできない (両方を実走で確認した)。
詳細は failures 台帳の該当 F を参照。**実質 13/13 とする。**

## 取り込みで検出力が増えた

main の `6162fef4` (T-843) を取り込み、値域検査の正本を 1 つへ寄せた結果、
同じ変異が落とす node が増えた。取り込み前 → 後で `t441.m07` が 9 → 20 件、
`t441.m08` が 5 → 7 件、`t441.p01` が 69 → 86 件。main 側のテストも同じ正本を通るためである。
