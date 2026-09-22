# raw/ の可逆な最小正規化の記録 (DW-S07)

`git diff --check` の行末空白に抵触したため、可視文字を変えずに行末の空白だけを除いた。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 変更 | 復元法 |
|---|---|---|---|---|---|---|
| `apply-check-e9e477ca.txt` | `051061e5478dc6f7b3099c00a5697505d3a985d73b7ddc81e7326770fee2e76c` | 1715 | `895c23abb7f3deade9f4399fc6246a39edf367062c591f713f555fc462bb5145` | 1713 | 7 行目 (`broken-silo-lockskip-validation.patch`) と 11 行目 (`broken-silo-sort-nonswo.patch`) の行末の tab 各 1 byte を削除 (3 列目が空のため) | 両行の末尾に tab (`\t`) を 1 個ずつ戻す。原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-verifier-detection-design/apply-check-e9e477ca.txt` |

生成: job dir の `apply_check.py` (repo には入れていない) を 2026-09-22 09:25 JST に worktree で実行した stdout。
