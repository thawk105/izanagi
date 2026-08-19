[severity: nit] [docs/provenance/audit.md:15] 裁定値の family 8809B ではなく実差分は 8869B（`check_docs.py` の上限9000Bは通過）→ `PR-A02` を60B縮約するか、裁定値と byte assertion を更新する。

[severity: nit] [orchestrator/tests/test_check_ai_provenance.py:794] 空リポジトリ、policy commit＝HEAD、複数 side branch の authoritative 経路を直接検査するテストがない → 各境界を単一理由のテストとして追加する。

consumer、既存シグネチャ、`--message-file` 経路に回帰所見はありません。DW-M01 は12項目すべて対応テストを確認済み。CAB 3 seed 以上は `test_ancestry_pickaxe_mask_matches_per_commit_oracle` でカバーされています。

## 総括

blocker / must-fix はありません。