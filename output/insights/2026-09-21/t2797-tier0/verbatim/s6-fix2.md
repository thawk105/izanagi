実装済み・未実走です。指定の2ファイルだけを変更し、commit は作成していません。

### 1. 所見への対応

| 所見 | 状態 | 根拠 |
|---|---|---|
| F2 | closed（実装、未実走） | `test_p3_s4_loop.py:10856` の共通 fixture だけに Tier0 準備・両 build API・smoke の通過差し替えを追加 |
| F7 | closed（実装、未実走） | `p3_s4_loop.py:1519` の outcome 追加、`test_p3_s4_loop.py:7487` のケース追加 |

### 2. 変更箇所と静的確認

- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/p3_s4_loop.py:1519)：本番変更は `"rejected-tier0"` 1語だけ。
- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_p3_s4_loop.py:7487)：parametrize に1ケース追加。同ファイル10856行の `_b5_candidate_fixture` に通過差し替えを集約。

Tier0 拒否は本番2601行で `variant=None` を返します。`_wal_attempt_provenance` の既存分岐は `wal.read_records` より前に `build_attempt_id=None, wal_refs=[]` を返します。他の provenance 関数は変更していません。

fixture 利用側の候補前処理拒否は proposal loader、文字列 preflight 拒否は Tier0 より前で終了するため、追加した差し替えに到達しません。両 seam test を含む既存テスト本体・期待値は不変です。

`test_b5_tier0.py` の挿入点も静的に到達可能です。新規 layout では `_load_provenance` が `{}` を返し、実物の loader が capture を埋め、実物の `drive_iteration` が `initial_proposal_sha256` を受け取ります。既存の `ensure_resumable_attempts` 差し替えは両呼出しに有効です。同ファイルは未変更です。

### 3. 静的検査

- `python3 - <<'PY' … PY`：メモリ上の構文コンパイル、HEAD との AST 差分限定確認、参照ファイルのバイト一致確認。**rc=0**
- `git diff --check`：**rc=0**
- `git status --short`：変更は指定2ファイルだけ。

### 4. meta-test への影響

静的に以下を照合しました。

| meta-test | 影響 |
|---|---|
| `test_ccbench_spawn_sites.py` | 本番の spawn・build sink・condition gate の呼出しと順序は不変 |
| `test_s8b_floor_campaign.py` | materializer 閉包対象の本番 build 呼出し・`"--build"` 字面は不変 |
| `test_plain_runner_coverage.py` | ファイル集合・自走入口は不変 |
| `test_check_subprocess_bytecode_guard.py` | subprocess 起動の追加なし |
| `test_campaign.py` | certified-writer caller は不変。fixture は検査対象外 |
| `test_official_perf_closure.py` | 本番 perf 条件・呼出し集合は不変 |

### 5. M18 の kill 先

`orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_records_b5_early_returns[rejected-tier0]`

実物の provenance 公開時に outcome 検証を通るため、M18 では `ValueError` となる見込みです。

併せて `orchestrator/tests/test_b5_tier0.py::test_insertion_rejection_rc3_no_submission_wal_or_digest` の全6ケースも、実物の Tier0 拒否から同検証へ到達します。その他の変異は変更していません。変異実走は未実施です。

### 6. 親の実走候補

- `orchestrator/tests/test_p3_s4_loop.py` 全体：F2 の2件、fixture 利用側の拒否ケース、既存 provenance ケースを含む。
- `orchestrator/tests/test_b5_tier0.py`：通常挿入点・拒否・例外伝播。
- 上記 meta-test 6ファイル。
- M18 を適用した上記 kill 先。

## 総括

F2・F7 の修正と静的確認を完了しました。テスト・変異 probe は指示どおり未実走で、実走による閉鎖確認は親に残ります。