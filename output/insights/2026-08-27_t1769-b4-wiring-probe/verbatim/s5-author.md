## 実装したもの

- [p3_b4_wiring_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1769-b4-wiring-probe/orchestrator/campaign/p3_b4_wiring_probe.py:1)
  - 3-seed 静的逆閉包・conditional edge 解析: 71, 618, 689, 781 行
  - audit/profile interdiction と identity seal: 266, 471 行
  - 発行 workspace、fixture schema、`record_diff_reject` 束縛: 891, 968, 1005 行
  - zero-argument `_make_probe_view()`: 1044 行
  - 4 検査と trigger site projection: 1109–1246 行
  - 観測由来 hook evidence、exact schema、sidecar-first publish: 1257, 1293, 1350 行
  - 実 CLI `main(argv)`: 1439 行
- [test_p3_b4_wiring_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1769-b4-wiring-probe/orchestrator/tests/test_p3_b4_wiring_probe.py:1)
  - clean env・`-I -B` child runner: 24–55 行
  - 3 seed、静的 edge、fail-closed resolver: 127–240 行
  - 実 producer 9 本と実 `main()` 負例: 253, 299 行
  - fixture/root/audit/swap/publish 負例: 345–540 行
  - 3 driver 正例と evidence/schema 検査: 544 行

既存 driver の runtime 受理・拒否挙動と campaign identity は変更していません。repository-wide gate の走査対象だけが新規2ファイル分増えます。

## 実走した検査

正式 pytest は **0 nodeid 実走**です。次の runner 要求はいずれも `qstat -Q: Unknown user-id`、child 未起動、rc=16 でした。

- `orchestrator/tests/test_p3_b4_wiring_probe.py`
- 指定された内容走査 meta-test 12ファイル一式（A6 の2件を含む）

したがって、これらを closed/緑とは扱いません。

nodeid 外の diagnostic では以下を実行し成功しましたが、受入緑には算入しません。

- 実 `main()` の base/sort/trigger 正例
- 実 `main()` → 実 `pipeline.evaluate` の遮断と evidence 0 件
- 実 producer 9 本の body 前遮断
- protected WAL、ambient temp、symlink、module/code swap、exec/import、failure publish の負例
- 内容走査 checker相当の静的 diagnostic
- `python3 tools/check_subprocess_bytecode_guard.py --repo ...`: exit 0
- `python3 tools/check_codex_agents.py`: exit 0
- `python3 tools/check_docs.py`: exit 0（事前指定した docs finding も発生せず）

runner が作った dispatch 診断物は削除済みで、`output/` に本作業の成果物は残していません。

## must-fix 8 項目の対応表

|項目|状態|根拠|
|---|---|---|
|1 / A2|partial|観測由来 hook booleanと実 `main()` 負例を実装・diagnostic 済み。pytest 未実走|
|2 / A3|partial|anchor・`save_loop_state`・`project_whiteboard` の3 seed。完全性非主張も evidence 化。pytest 未実走|
|3 / B4|partial|`record_diff_reject` は非遮断、exact issued layout に束縛。protected root 負例あり|
|4 / B1|partial|`admission_reads` に overlay path/hash/classification。protected-read ledger 0をschemaで強制|
|5 / B8|partial|base/trigger の逐語 guard、sort 無条件、trigger site-projected cfgを記録|
|6 / B5/B3/B2/B9/B7/B11|partial|module/code seal、ambient root拒否、型生成fixture、raw ID削除、import副作用/thread census、zero-argument viewを実装。pytest未実走|
|7 / A6|partial|child runnerはclean env・`-I -B`。指定meta-testはrunner infrastructureにより未実走|
|8 / source制約|closed|両新規sourceを実走査し、禁止文字列なし、禁止factory callなしを確認|

よって全体状態は **実装済み・正式受入未実走のため未完了** です。

## 変異 M-01〜M-15 の単一理由性

実変異matrixは親の段6待ちです。以下は実装構造とdiagnosticによる確認です。

|ID|判定|単一理由|
|---|---|---|
|M-01|確認できた|実 `main()` のprofile装着だけが期待例外を発生|
|M-02|確認できた|false観測をそのままfalse evidenceへ写す独立test|
|M-03|確認できた|anchor seedだけが `pipeline.evaluate` を導入|
|M-04|確認できた|`save_loop_state` seedと実体entry負例|
|M-05|確認できた|`project_whiteboard` seedと実体entry負例|
|M-06|確認できた|audit未装着の直接束縛testで他層と分離|
|M-07|確認できた|非literal `getattr` の静的resolverだけが拒否|
|M-08|確認できた|off loader call ledgerの件数だけを固定|
|M-09|確認できた|off/green byte比較を独立fieldで固定|
|M-10|確認できた|preimage分離だけを検査しraw IDを不使用|
|M-11|確認できた|audit未装着でambient workspace検査を直接発火|
|M-12|確認できた|publish前seal再検証へ直接swapを入力|
|M-13|確認できた|追加性能fieldはfixture禁止field検査だけが拒否|
|M-14|確認できた|failed check後、publish前に停止し0件|
|M-15|確認できた|sortの`conditional_edges == []`だけを固定|

ただしpytestと実変異matrixが未実走なので、親は登録を外さず段6で実測する必要があります。

## 波及可能性

- 所有外caller: 現時点で新CLIの既存callerなし。既存driver/APIは無変更。
- 共有fixture: 既存test fixtureは流用せず、private型生成fixtureのみ。public admission、deny-only overlay、現行policy/activationを読みます。
- 自動consumer:
  - `test_p3_exploration_namespace.py`
  - `test_p3_build_authority_cli.py`
  - `test_s8b_floor_campaign.py`
  - `test_s8b_oracle_manifest_contract.py`
  - `test_s1_known_axes_freeze.py`
  - `test_campaign_import_invariant.py`
  - `test_campaign.py`
  - `test_s8b_floor_stats.py`
  - `test_s8b_ratified_freeze.py`
  - `test_frozen_artifacts.py`
  - `test_ccbench_spawn_sites.py`
  - `test_check_subprocess_bytecode_guard.py`
- `docs/`、既存test、`output/`、既存production fileは未編集です。
- commit/add/stash/branch操作は行っていません。

## 総括

- 許可された新規2ファイルだけを作成しました。
- must-fixの実装面はすべて反映済みです。
- 3 driver正例と主要負例は一時root diagnosticで発火確認済みです。
- 正式pytestはqueue認証不能でchild未起動のため未実走です。
- 作業ツリーには新規2ファイルだけが残っています。
- commitは作成していません。