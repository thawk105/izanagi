## 総括

- 変更前は登録済み 3 node が全走で無条件 skip、その他は受理され、不正 registry row は validator が拒否していました。
- 変更後は hold による skip が 0 件になり、validator の拒否条件は変更していません。
- B1、B2、B3 を許可された 3 file だけに実装しました。
- `poll_interval_s=1` は暫定値で、段 6 の親実測待ちです。
- `git add`、commit、pytest 実走は行っていません。

## 変更した file と行

- [flaky_test_holds.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-b/orchestrator/tests/flaky_test_holds.py:200): registry を空化。
- [test_flaky_test_holds_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-b/orchestrator/tests/test_flaky_test_holds_contract.py:287): live empty registry 契約。
- 同 file 887-927: synthetic 1-row summary と新 digest。
- 同 file 970-1005: live empty summary の `0/0/0` 契約。
- [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-b/orchestrator/tests/test_pegasus_dispatch_compute.py:5394): 1 個目の thread scenario。
- 同 file 5462-5495: hold#1 scenario。

## B1 の実装

`_FLAKY_TEST_HOLD_ROWS = ()` とし、3 行すべて撤去しました。

`FlakyTestHold`、validator、digest、公開 API は未変更です。静的 import では次を確認しました。

- rows: `()`
- mapping: `{}`
- node IDs: `frozenset()`
- digest: `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`

## B2 の実装 (pin 閉包の自力再列挙の結果を含む)

live registry 非空依存を再検索し、指定された次の 3 test に閉じることを確認しました。

1. live hold#1 を逐語 pin していた testを、空 rows、空 mapping、node-set 不変条件、動的 digest、empty digest を検査する testへ変更。
2. 非空 summary testを `_synthetic_valid_hold()` 1 行だけに変更。期待 count は `1/1/1`、digest は `eec86ac747160fb628a341d2c6737a30e5578f847f16f7e04340e599bd192623`。
3. live summary testを空 registry の `0/0/0` と empty digest に変更。

残る registry 参照は synthetic injection、空 mapping、一般的な `len` または集合積で、live 非空性には依存しません。validator の negative control は削除・緩和していません。

## B3 の実装 (poll ループ通過の静的確認を含む)

両方の `DC.dispatch(...)` に、同 file の既存の短間隔慣行に合わせて `poll_interval_s=1` を追加しました。

- `join(10)` scenario: permission failure 後の cleanup qstat、qdel 後の post-qstat retry で poll seam を通ります。
- `join(60)` scenario: default `_Scheduler` の `QUE -> RUN -> DONE` で通常 poll seam を通ります。
- どちらにも既定の 5 秒間隔や sleep 回数を固定する assertion はありません。

join は hang 回収 watchdog であり latency 合否予算ではないこと、親の母集合が計算ノードでの同 file 単独走 3 回で受入全走と同一 regime ではないこと、注入前の床が 10.015 秒だったことをコメントへ記載しました。

`results`、qsub 回数、`_orphan_hold_present`、`submission-disabled.json` の assertion はすべて維持しています。

## 実走したか (nodeid と範囲、または「実装済み・未実走」)

実装済み・未実走です。実走した nodeid はありません。緑は主張しません。

非 pytest の静的確認として以下のみ実施しました。

- `git diff --check`
- 変更 3 file の AST parse
- registry の import-time 空 mapping、node set、digest 導出
- 変更 file が許可された 3 fileだけであることの `git status`

## 制約 meta-test の洗い出し結果

- `acceptance_duration_ledger.json` には B3 の 2 nodeidが残っています。hold#1 の `10.0` 秒は注入後に古くなるため、親の段 6 実測後の更新候補です。
- hold#2、hold#3 の duration entry は残っており、テスト自体を削除していないため維持が妥当です。
- 改名した 2 contract testの旧 nodeid は、変更前から ledger に登録されていませんでした。ledger は非網羅・fail-softで、追加を強制する meta-testはありません。
- ledger にはさらに古い `test_registry_is_two_exact_nodes_with_reintroduction_anchors` が既存 stale keyとして残っています。本変更起因ではなく、所有外なので未編集です。
- `test_check_docs.py` は registry file の存在と一般運用文言だけを検査し、live nodeidや件数を pinしていません。
- その他の test inventory、node一覧、skip分類に新 nodeid登録を要求する箇所は見つかりませんでした。

## 所有外への波及可能性

- `orchestrator/tests/conftest.py`: hold match、skip、stale-node確認、終了 summary が空 registryを消費します。変更不要です。
- `tools/mutation_harness.py`: 空 `FLAKY_TEST_HOLD_NODE_IDS` を受理し、交差集合が空になります。
- `tools/run_tests.py` と task-run receipt群: genericな passed/skipped件数のみ変化し、schema変更はありません。
- duration scheduling: hold#1 の既存 10 秒見積もりは段 6 実測後に見直しが必要です。
- B3 は production dispatcher、共有 `_Scheduler` fixture、dispatch signatureを変更していません。

## 期待赤の finding 集合

実装子 A が未 land の状態で想定する赤は次の 4 nodeです。

- `test_s8b_oracle_driver.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes`
- `test_real_repo_serialization.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes`
- `test_s8b_floor_campaign.py::test_real_output_snapshot_excludes_git_ignored_real_output_changes`
- `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary`

最後の nodeは hold#2 撤去により受入へ戻りますが、A の snapshot helper 修理前です。この集合以外の赤は回帰として扱う必要があります。

## 未完・未確認

- pytest、焦点走、受入全走は未実走です。
- `poll_interval_s=1` 注入後の実所要と watchdog倍率は親の段 6 実測待ちです。
- 実装子 A を先に統合し、その後に本変更を重ねる必要があります。
- docs、duration ledger、phase完了処理は所有外のため変更していません。
- commit、stageは行っていません。