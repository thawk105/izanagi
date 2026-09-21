## 実施

[make_mutation_spec.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2825-mutation/t2825-mutation/make_mutation_spec.py) のみ新規作成しました。標準 library のみ使用し、`git add` / `git commit` は未実行です。

probe / final、累積置換の一意性、適用後の JSON・count・canonical bytes を検証します。final の期待 node は外部 JSON から取得します。

## 生成結果

- `py_compile`、`--help`、probe、仮 node による final：すべて **rc=0**。
- final 引数不足・不正 mode：ともに **rc=2**。
- probe 再生成：bytes 一致。
- `old` 出現回数：P0 `[1]`、M1 `[1]`、M2 `[1,1]`、M3 `[1,1]`。
- 一時成果物・bytecode は一時ディレクトリごと削除済み。

| spec | SHA-256 |
|---|---|
| probe | `1015f7cf167db5693955a0e2a1b3b6ea9dc6a042680963933f29526b930bf1cb` |
| final（仮 node） | `6429930def2b647830441620935b3a7e5abc59a47a4df99bc4b0348a64c36b15` |

仮 node は裁定の予測値を使用しました。観測結果ではありません。

M3 は **3,265 件**削除（全体最小件数）、削除後 count は **23,340**、被覆率は **23,322 / 26,808 = 86.996419%** です。

- 先頭：`orchestrator/tests/test_acceptance_schedule_order.py::test_g7_controller_reads_ledger_only_for_enabled_loadgroup`
- 末尾：`orchestrator/tests/test_campaign.py::test_recovery_waits_for_external_exclusive_wal_lock`

見積りは 120 秒、両 timeout は 4,500 秒です。T2236 の 90 / 3,900 秒に余裕を加えました。harness は dispatch 時に準備・queue・walltime・後処理を合算し、spec timeout との大きい方を使用します（`tools/mutation_harness.py:1421`）。queue 待ちを含む実測値ではありません。

## 単一理由の静的確認

- **P0 / M1**：g7e は非負有限値の性質のみ（`test_update_acceptance_duration_ledger.py:319`）、g5 は key 被覆のみ（`test_acceptance_schedule_order.py:704`）。M1 の 0.12 exact pin は t1574（`test_update_acceptance_duration_ledger.py:349,358`）。
- **M2**：count を +1 するため g7e と conftest の count 検証を満たします（`orchestrator/tests/conftest.py:1598–1626`）。凍結 suite の集合検証が差を捉えます（`test_update_acceptance_duration_ledger.py:397–404`）。
- **M3**：凍結・`@real-repo` を維持します。**g6 は自身の台帳値を用いた順序も検証する**ため（`test_acceptance_schedule_order.py:838–852`）、その key（15.0）も保存しました。裁定の「先頭から削除」を調整し、同じ最小件数で条件を満たす最初の連続塊を採用しています。
- spec の未知 key はありません。受理 field 集合・空 node 条件・累積置換規則を source と照合しました（`tools/mutation_harness.py:544–629,1076–1094`）。診断情報は stdout に出します。

## 未実走

変異 harness・pytest・計算ノード runner は未実走です。親の dispatch で実測し、観測 node を渡して final を再生成してください。

## 総括

所有する生成器 1 file の実装と生成確認を完了しました。
M3 は最小 3,265 件の連続削除で被覆率 87% 以下になります。
g6 の追加依存を静的に発見し、その比較用 key を保存しました。
単一理由での KILLED / P0 の SURVIVED は、親による変異実走での確認が残ります。