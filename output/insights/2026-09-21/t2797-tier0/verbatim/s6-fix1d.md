実装済み・未実走です。本番コードの差分は 0、commit は作成していません。

1. 対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F6 | closed（実装・静的確認。probe は親が実施） | [test_b5_tier0.py:188](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py:188) |

2. 変更箇所

`orchestrator/tests/test_b5_tier0.py` の `insertion_case` のみ変更しました。`L.ident.ensure_resumable_attempts` を差し替え、`drive_iteration` 入口と `_run_one_iteration_resolved` 内の両呼出しを対象にしています。コメントも修正しました。

`campaign_id → cfg_hash → canonical_preimage` と `_b5_sidecar_payload` は HEAD blob 照合を呼ばないため、実物を維持しています。対象経路では追加の準備層差し替えは不要と判断しました。

3. 静的検査

- `git diff --check`：rc 0。
- `python3 -B - <<'PY' … PY`：`compile()` による構文確認と、HEAD に対する fixture 外の AST 一致確認。rc 0。
- 差分は所有 file のみ、7 行追加・1 行削除。検査項目・期待値・parameter は変更していません。

4. meta-test への影響

静的確認では以下への影響はありません。

- `test_ccbench_spawn_sites.py`：process・build sink・condition gate の本番呼出しは不変。
- `test_s8b_floor_campaign.py`：materializer 閉包と `--build` 字面は不変。
- `test_plain_runner_coverage.py`：自走入口は不変。
- `test_check_subprocess_bytecode_guard.py`：subprocess 起動の追加なし。
- `test_campaign.py`：certified-writer caller inventory は不変。
- `test_official_perf_closure.py`：本番走査対象は不変。

5. kill 先

全て `orchestrator/tests/test_b5_tier0.py::` 配下で、既存の legacy / v2 parameter を維持しています。

| 変異 | node 名 | 根拠 |
|---|---|---|
| M1〜M3 | `test_insertion_build_smoke_sidecar_submission_order` | 実挿入点の順序・`trace=False`・gateway に届く binary を検査 |
| M9・M10・M10b | `test_insertion_rejection_rc3_no_submission_wal_or_digest` | 実 driver・CLI を通し、拒否・rc 3・submission / WAL / digest 不在を検査 |
| M11 | `test_insertion_preparation_and_build_errors_propagate` | build の OSError と準備段例外の同一オブジェクト伝播を検査 |

その他の M は変更なし。kill の実測結果は未確認です。

6. 親の実走候補

上記 3 test の全 16 node と、`orchestrator/tests/test_b5_tier0.py` 全体。M0 および既登録の配線変異 probe を再実施してください。

## 総括

静的には、`p3_s4_loop.py` への意味のない comment 1 行追加だけでは、挿入点 test の判定は変わらない構成です。HEAD blob 照合へ入る identity 準備を fixture 内で外し、検査対象の機構は維持しました。M0 の SURVIVED 確認は親の probe に残しています。