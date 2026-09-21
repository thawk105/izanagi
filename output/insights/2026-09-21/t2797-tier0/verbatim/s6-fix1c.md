**実装済み・未実走**です。テスト実行・commit・docs 編集はしていません。

1. 対応表

| 対象 | 状態 | 根拠 |
|---|---|---|
| legacy 8 ケース | partial（修正済み、実走待ち） | [insertion_case:173](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py:173) |

2. 変更箇所

`orchestrator/tests/test_b5_tier0.py` の `insertion_case` だけを変更しました。

- 両分岐で v2 側と同じ Pegasus contract を使用。
- fixture 内の site 対応表も更新し、`drive_iteration` の env_tag 整合検証を維持。
- legacy の site は `OTHER` を維持。receipt 指定もないため、`campaign_options` に `env_contract` が入らず、実物の `buildcache.build` 分岐を選びます（`p3_s4_loop.py:2350,2395`）。

本番コード差分0。既存期待値・parameter・検査対象機構は変更していません。

なお、f2 ログの `legacy-preparation-io` は activation 検証で失敗しています（ログ:105）。`source_digest` の rc 128 は対象外の seam 2 件です。修正後は準備差し替え（本番呼出し:2368）へ進む構成ですが、到達の実測は未確認です。

3. 静的検査

- `git diff --check`：rc 0。
- `python3 -B - <<'PY' … PY`：rc 0。構文、fixture 外の AST 不変、変更ファイルが指定1本のみであることを確認。

4. meta-test への影響

静的確認では、以下の対象に変更はありません。meta-test 自体は未実行です。

- `test_ccbench_spawn_sites.py`：process 目録、build sink、condition gate 先行関係。
- `test_s8b_floor_campaign.py`：`--build` 字面と materializer 閉包。
- `test_plain_runner_coverage.py`：自走入口。
- `test_check_subprocess_bytecode_guard.py`：subprocess 起動点。
- `test_campaign.py`／`test_official_perf_closure.py`：certified-writer caller 目録と本番 perf 閉包。

5. 変異の kill 先

以下は `orchestrator/tests/test_b5_tier0.py::` に続く node 名です。前 fix の割当を維持します。

| 変異 | node | 検査 |
|---|---|---|
| M1・M2・M3 | `test_insertion_build_smoke_sidecar_submission_order` | 実挿入点の順序、build 回数・trace、gateway の binary |
| M9・M10 | `test_insertion_rejection_rc3_no_submission_wal_or_digest` | 実 driver／CLI の早期 return、rc 3、非生成 |
| M11 | `test_insertion_preparation_and_build_errors_propagate` | 準備・build 例外の伝播と sidecar 非生成 |

その他の M は変更なし。KILLED の実測判定は未実施です。

6. 親の実走候補

`tools/run_tests.py` 経由で上記3 node の全 parameter（legacy/v2 合計16ケース）、続いて `test_b5_tier0.py` 全体を確認してください。

## 総括

準備層の contract 選択と site 対応表のみを修正しました。legacy 8 ケースの検査内容は維持しており、完了判定には親の焦点走が必要です。