実装済み・未実走です。所有 2 ファイルのみ変更し、テスト・commit は実行していません。

**1. 変更前の挙動**

- `drive_iteration` は評価・whiteboard 射影後、checkpoint を保存していました。base provenance report はありませんでした。
- capture は proposal 検証完了後に更新されますが、document は含まず、CLI では `--agent-inputs` 指定時だけ渡していました。

**2. 変更箇所**

- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/campaign/p3_s4_loop.py:1523)
  - `_provenance_path`／validator／loader／writer／merge／attempt 抽出を追加。
  - 破損退避、未処理退避ファイルによる再起動停止、exclusive tmp → file fsync → replace → directory fsync を実装。
  - `_append_provenance_entry:1610` に P4 の限定、`_wal_attempt_provenance:1629` に参照点の定義を記載。
  - `load_proposal_file:2900` に検証済み document の capture。
  - `drive_iteration:2967` に評価・B-4 認可前の読取検証、`:3063` に checkpoint 前の公開。
  - `main:3691` 以降で常時 capture、canonical hash 計算・引渡し。
- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_s4_loop.py:7134)
  - provenance テスト 19 関数と、module 単位の binding fixture を追加。
  - 既存 loader stub 3 箇所を capture 契約へ追従。既存 assertion は維持。
  - `test_pair_candidate_has_one_provenance_entry` は作成していません。

**3. 静的検査**

| コマンド・検査 | rc |
|---|---:|
| `PYTHONPYCACHEPREFIX=/tmp/t2632-unit-a-pycache python3 -m py_compile orchestrator/campaign/p3_s4_loop.py orchestrator/tests/test_p3_s4_loop.py` | 0 |
| `git diff --check` | 0 |
| `python3 -` による AST 呼出数・射影隔離検査 | 0 |
| `python3 -` による HEAD との import／射影関数 AST 比較 | 0 |

テスト本体の import・実行、pytest collection、変異実行はしていません。

**4. meta-test の静的点検**

| 対象 | 影響・更新判断 |
|---|---|
| `test_p3_exploration_namespace.py` DriverContract | layout 呼出し 11、run_campaign 呼出し 2。既存値と一致、更新不要 |
| `test_campaign.py` certified-writer 目録 | certified producer 呼出し追加なし。更新不要 |
| `test_p3_b4_wiring_probe.py` static 数・inventory | import 宣言不変。新しい生成 producer／seed なし。更新不要の見込み |
| `test_official_perf_closure.py` | perf 実行面・guard 追加なし。更新不要 |
| `_assert_agent_input_ast_isolated` | root と直接参照先を静的点検。隔離維持 |
| `test_agent_loader_capture_only_after_validation` | `capture == {}` を維持。更新不要 |
| `test_p3_build_authority_cli.py` authority AST 目録 | issuer／登録 CLI 面の追加なし |
| `test_ccbench_spawn_sites.py` | process launch 追加なし |
| `test_campaign_import_invariant.py` | import 宣言不変 |
| `test_real_repo_serialization.py`／`conftest.py` | 既存 node の改名なし。新 binding fixture と drive fixture は `real_repo_fixture_lock` を使用 |
| lock／artifact admission の closure 検査 | **ソース bytes が変わるため影響あり**。検査・fixture hash は緩和していません |

所有外の目録更新が必要と確定した箇所はありません。ただし、これは実走結果ではありません。

**5. 所有外への波及**

- sort／trigger は独自 `drive_iteration` のまま。base report の書込みを展開していません。
- `b5_generator_contrast` の loader 呼出しは戻り値不変。起動した base CLI では report が追加されます。
- pair CLI の loader stub は所有ファイル内で修正済み。stock 非書込みは実 stock 関数を通す別テストで扱います。
- `test_p3_b4_closed_critic.py` の直接 drive 呼出しは引数省略可能で、hash は null。
- caller／layer3 consumer が読む checkpoint の 5 field は不変。
- `campaign_lock_test_support.py` 等の共有 fixture は未変更。新規 v2 fixture は記録 HEAD binding を module 単位で取得します。
- 未 commit bytes による contract-loader／B-4 projection drift は残ります。親で commit 後の焦点走と E1 probe により区別してください。

**6. 親の焦点走候補**

以下は追加した完全な関数 nodeid です。parametrize の各ケースも対象です。

```text
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_records_each_outcome
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_rejects_same_variant_use_distinct_attempts
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_duplicate_reuses_selected_attempt
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_keeps_all_attempt_records
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_preserves_whiteboard_projection
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_precedes_checkpoint
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_failure_keeps_checkpoint
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_merge_is_idempotent
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_corrupt_report_stops
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_publish_failure_preserves_old_report
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_skips_stock_and_entry_stop
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_records_b5_early_returns
orchestrator/tests/test_p3_s4_loop.py::test_direct_drive_provenance_hash_defaults_to_null
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_inputs_do_not_read_report
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_invalid_entry_is_quarantined
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_rejects_missing_or_conflicting_start
orchestrator/tests/test_p3_s4_loop.py::test_main_provenance_hash_without_agent_inputs
orchestrator/tests/test_p3_s4_loop.py::test_main_provenance_hash_uses_loaded_document
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_hash_excludes_receipt_key
```

加えて既存 capture、agent live、pair CLI、B-5、および上記 meta-test の回帰確認が必要です。

**7. S1〜S14・E1 の自己点検**

行番号は `p3_s4_loop.py` です。変異は未実行です。

| ID | 実装後の位置・変異点 | 拒否層の重なり |
|---|---|---|
| S1 | `drive_iteration:3063` 公開呼出し削除 | 他の公開義務検査なし。entry assertion が検出点 |
| S2 | 同、`:3069` checkpoint を公開前へ | 順序 spy／失敗時 checkpoint assertion |
| S3 | `_wal_attempt_provenance:1682` refs 抽出の ID 条件削除 | start 一意性検査を独立させ、別 attempt 混入は refs 比較で検出 |
| S4 | 同 `:1655` commit ID を最新 start ID に置換 | fixture の両 ID は異なる。後者にも有効な start がある |
| S5 | 同 `:1684` record 全体を payload に置換 | hash 形式は通る。全 record digest 比較で検出 |
| S6 | 同 `:1680` record 列を stage 単位へ圧縮 | 複数 verify record の比較で検出 |
| S7 | `_append_provenance_entry:1620` 既存 entries を破棄 | schema は通る。他 iteration 保持の assertion |
| S8 | `_load_provenance:1580` 破損時 raise を空辞書へ | **後段 loader と重複あり**。単なる例外を KILL 根拠にせず、評価未呼出し assertion へ照準 |
| S9 | `_write_provenance:1597` file fsync 削除 | 注入は regular file の fsync のみ。directory fsync は別扱い |
| S10 | `main:3710` capture の raw bytes hash に置換 | 有効な 64 hex なので後段型検査は通る。canonical hash 比較で検出 |
| S11 | `main:3691/3703` capture を条件付きに戻す | document 欠落で停止し得る。hash 配管欠落として扱い、hash アルゴリズム検出とは区別 |
| S12 | `drive_iteration:3063` に非 B-5 条件を追加 | B-5 entry assertion が検出点 |
| S13 | `drive_iteration:2967` 評価前 loader を削除 | **後段 merge loader と重複あり**。評価・認可未呼出し assertion が必要 |
| S14 | `make_critic_digest:1166` 内で report 内容を文字列へ連結 | report 不在でも読める注入に限定。出力 bytes 比較で検出 |
| E1 | `_wal_attempt_provenance:1684` canonical bytes の直接 SHA-256 に置換 | 意味上等価。SURVIVED は未確認。drift probe が必要 |

## 総括

所有 2 ファイルへの実装と静的検査を完了しました。**実装済み・未実走**で、commit はありません。P4 は checkpoint 未確定の保証に限定し、S8／S13 の後段拒否との重なりも明記しました。