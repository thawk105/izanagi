## 足した node

計 37 件を追加しました。

- `test_t1998_stock_inline_pair.py`: 30 件
- `test_t1998_launcher_contract.py`: 7 件

## placeholder の根拠

現行 ledger の以下の既存 entry などで使われている `0.0` に合わせました。

`test_campaign_import_invariant.py::test_real_campaign_package_uses_relative_sibling_imports`

先例 commit `c2596a2c2` の未実測時の扱いとも一致します。

## nodeid_count の更新

`19521` から `19558` へ更新しました。JSON 内の実 entry 数も 19,558 件です。

## 総括

[acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/tests/acceptance_duration_ledger.json) のみ変更しました。JSON 構文、37 node の完全一致、全 placeholder 値、末尾改行、差分形式を確認済みです。禁止事項に従い、テスト、build、benchmark、qsub、git add、commit は実行していません。