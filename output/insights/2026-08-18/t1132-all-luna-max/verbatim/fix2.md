## 総括

- 指定テストのみ修正。slug の出現集合を動的に取得し、各 slug を別名へ一対一置換。
- `assert changed_line != line` を追加し、無変更の恒真化を防止。
- 新 commit を `snapshot_authority` で読み、元と同じ v1/v2 文法であることを検証。
- `check_docs`、`check_codex_agents`、AST parse、diff check は成功。対象 consumer に slug 個数の決め打ちは残っていない。他所の添字は固定 schema/lane 検査。
- pytest は指示どおり未実走。コミット・docs・production code の変更なし。