実装済み・未実走です。

[対象テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2417-recovery-author/orchestrator/tests/test_ccbench_spawn_sites.py:932) の4つの pin を更新しました。

- trace sink: `<module>._certify_main._build_trace_binary` → 3910行
- 通常 sink: `<module>.main` → 4303行
- 台帳2箇所と既存期待集合2箇所を同じ値へ追従
- 競合マーカーを除去
- 分類、理由、期待値の意味、拒否挙動、テスト名は不変
- 他ファイル、既存のT-1998差分、fixtureには未接触
- 所有外caller、共有fixture、consumer testへの追加波及なし

静的確認結果:

- Python AST構文: OK
- driver内 `buildcache.build`: 上記2 sinkのみ
- テスト側4 pinとの一致: OK
- `git diff --check`: OK
- 競合マーカー残存: なし
- pytest、`run_tests.py`、build、qsub: 未実行

## 総括

| 状態 | 対象 | 結果 |
|---|---|---|
| closed | 競合4箇所 | 3910行と4303行へ正しく追従 |
| partial | 動的テスト | 親担当のため未実走 |
| regressed | 既存の受理・拒否分類 | 静的確認上なし |