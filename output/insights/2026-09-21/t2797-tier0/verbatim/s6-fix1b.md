F1 は**実装済み・未実走**です。テスト実行・commit・docs 編集は行っていません。

1. 対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F1 | closed（実走確認待ち） | [順序・binary 検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py:262)、[拒否検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py:281)、[例外伝播検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py:322) |

2. 変更範囲

`orchestrator/tests/test_b5_tier0.py` のみ、194 行追加。[fixture:150](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py:150) とテスト3関数、legacy/v2 合計16ケースです。追加ケースに skip 条件はありません。本番コード差分は0、既存テストの期待値は維持しています。

3. 静的検査

- `git diff --check`：rc 0。
- `python3 -B - <<'PY' … PY`：rc 0。構文確認、既存関数・クラスの AST 不変、変更ファイルが1本だけであることを確認しました。

4. meta-test への影響

静的確認では以下のとおりです。meta-test 自体は未実行です。

- `test_ccbench_spawn_sites.py`：本番の process/gateway 目録、build sink、condition gate 先行関係は不変。
- `test_s8b_floor_campaign.py`：新規 `--build` 字面・本番 materializer 変更なし。
- `test_plain_runner_coverage.py`：既存の自走入口を維持。
- `test_check_subprocess_bytecode_guard.py`：subprocess 起動点の追加なし。
- `test_campaign.py`、`test_official_perf_closure.py`：本番 caller inventory・perf 閉包は不変。
- growth hold 登録に追加 node はありません。test 間 import も追加していません。

5. 変異の再照準

以下は `orchestrator/tests/test_b5_tier0.py::` に続く node 名です。

| M | 新しい kill 先 | 到達根拠 |
|---|---|---|
| M1・M2 | `test_insertion_build_smoke_sidecar_submission_order` | 実 CLI→挿入点を通り、build→smoke→sidecar→submission→campaign の順序を検査 |
| M3 | 同上 | trace 別 executable、実 gateway の binary 引数、実行記録、build 1回・`trace=False` を照合 |
| M9・M10 | `test_insertion_rejection_rc3_no_submission_wal_or_digest` | 実 driver・CLI を通し、outcome、rc 3、submission/WAL/digest 非生成を検査 |
| M11 | `test_insertion_preparation_and_build_errors_propagate` | build の `OSError` と準備段の3例外型について、同じ例外の伝播・sidecar 非生成を検査 |

その他の M は変更なしです。**KILLED の実測判定・単一理由性の確認は未実施**です。

6. 親の実走候補

`tools/run_tests.py` 経由で、上記3 node（全 parameter）、`test_b5_tier0.py` 全体、および上記 meta-test 群を確認してください。live テストは従来どおり専用環境が必要です。

## 総括

F1 の通常走テストを追加しました。実挿入点・smoke・gateway・parser・bench lock・writer・driver・CLI は実物を通す構成です。受入と変異検査の実走は親に残っています。