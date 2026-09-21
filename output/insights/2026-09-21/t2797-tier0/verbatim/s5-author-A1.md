**実装済み・未実走です。** 所有 7 file のみ変更しました。テスト・変異走・commit・docs 編集は行っていません。

**1. 着手前の現行挙動**

- (a) 候補経路は検疫・condition gate・`campaign_options` 組立て後、`run_campaign` 前に `pipeline-submitted.json` を書いていました。投入前拒否は `_b5_proposal_rejected` → `rejected-preprocess` → B-5 早期 return／CLI rc 3 です。
- (b) 投入後の build 例外は pipeline が `build-error` で abort、driver が候補起因の `build-failed` に分類し、B を消費していました。
- (c) `_header` は `tier0_status="not-implemented"` でした。
- (d) HEAD は `36fb14a3d131d516dc57b02ec69f56c711927c2e`。T-2632 未 land の前提で、`save_loop_state` と provenance 関数は変更していません。

**2. 変更した file と箇所**

リンク先の行番号は現在の作業木です。

| File | 変更 |
|---|---|
| [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/p3_s4_loop.py:1992) | 契約定数、build 入力 helper、smoke helper。`_run_one_iteration_resolved` :2365 に Tier0、`drive_iteration` :3018 と CLI :3677 に拒否分岐 |
| [b5_generator_contrast.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/b5_generator_contrast.py:298) | `classify_slot` の証拠照合・compact summary、`_header` の実装済み契約、docstring |
| [b5_generator_contrast_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/b5_generator_contrast_report.py:468) | 共通構成比較へ Tier0 の 2 key を追加 |
| [test_b5_generator_contrast.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_generator_contrast.py:126) | sidecar fixture、既存 header assert、:933 以降の分類・予算・非流出検査 |
| [test_b5_generator_contrast_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_generator_contrast_report.py:78) | 新契約 fixture を分離、:716 以降に契約差・旧台帳互換・A/B 検査 |
| [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_ccbench_spawn_sites.py:42) | bounded client を 1 行追加 |
| [test_b5_tier0.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py:1) | 新規。実 gateway／parser／lock の fixture executable 検査と、親用の実 build 検査 |

**3. 静的検査**

以下はすべて rc 0 でした。

```bash
python3 -B -c 'import sys; from pathlib import Path; [compile(Path(p).read_text(), p, "exec") for p in sys.argv[1:]]' orchestrator/campaign/{p3_s4_loop,b5_generator_contrast,b5_generator_contrast_report}.py orchestrator/tests/{test_b5_generator_contrast,test_b5_generator_contrast_report,test_ccbench_spawn_sites,test_b5_tier0}.py
git diff --check
```

別途 `python3 -B` の AST 検査で次を確認しました。

- build 呼出し 2 分岐とも `trace=False`、admission/context/evidence を明示。condition gate が先行。
- certified writer 呼出しは従来どおり 2 件、bounded gateway の追加は 1 件。
- 許可された挿入と outcome 分岐変更を取り除くと、`p3_s4_loop.py` の既存関数 AST はすべて HEAD と一致。

**4. meta-test への影響**

| 検査面 | 静的確認・対応 |
|---|---|
| `test_ccbench_spawn_sites.py` の各目録 | 直接 subprocess 起動追加なし。検出器が追跡する直接 import で `run_once` を呼び、client 1 件を登録 |
| build sink／condition gate 先行 | build は gate と同じ関数内。無条件 helper へ隠していない |
| `test_s8b_floor_campaign.py` materializer 閉包 | 新しい `"--build"` 字面なし。両 build 呼出しに必須 3 引数あり |
| `test_p3_build_authority_cli.py` | coder authority の発行・登録追加なし |
| `test_campaign.py` writer inventory | `run_campaign` の呼出し数・既存引数を維持 |
| `test_official_perf_closure.py` | 新しい tracked call／perf 判定分岐なし。smoke は固定 `use_perf=False` |
| lock codec／contract loader 閉包 | 新 production module なし。使用 module は既登録。変更した loader の blob hash は変わる |
| `test_p3_s4_loop*.py` | 下記の既存 seam 2 件に fixture 追従が必要 |
| `test_b5_contrast_launch.py` | argv・予算定数・launcher 契約を変更していない |
| `conftest.py` | live 検査は実 site を使用。通常の output-root 環境が消去されるため、専用環境変数から設定 |

既存 meta-test 本体は実行していません。

**5. M1〜M17 の検査対応**

略号は `T=test_b5_tier0.py`、`D=test_b5_generator_contrast.py`、`R=test_b5_generator_contrast_report.py`。すべて `orchestrator/tests/` 配下です。**KILLED の確認は未実施**です。

| 変異 | 落とすはずの node／到達根拠 |
|---|---|
| M1 | `T::test_live_insertion_build_smoke_sidecar_submission_order` — 実挿入点の呼出し列 |
| M2 | 同上 — submission 書込み入口で Tier0 完成を確認 |
| M3 | 同上 — 実 BuildResult の trace 属性と smoke に渡る binary を照合 |
| M4 | `T::test_smoke_exact_argv_and_parser` — executable が実 argv を保存 |
| M5 | `T::test_smoke_rejects_nonzero_or_invalid_output[nonzero]` — 正常形式の出力＋rc 7 |
| M6 | 同 `[zero-commit]` — 正 throughput＋commit 0 |
| M7 | `T::test_smoke_timeout` — 実 subprocess timeout。省略時は正常終了する fixture |
| M8 | `T::test_smoke_uses_bench_lock` — 別 process の実 flock |
| M9 | `T::test_live_rejection_rc3_no_submission_wal_or_digest` — 実 CLI の timeout 拒否 |
| M10 | 同上 — 実 `drive_iteration` を通り digest 非生成を確認 |
| M11 | `T::test_live_preparation_and_build_io_errors_propagate[build_v2]` — 実挿入点の build 入口で実 file-open エラーを注入。広い捕捉なら失敗 |
| M12 | `D::test_tier0_rejection_consumes_A_only_without_retry` — 実 classifier／系列計数 |
| M13 | 同上 — 物理 attempt 数・retry event 数を固定 |
| M14 | `D::test_missing_tier0_stops_series_with_B_retained` — submission 済み証拠を欠落させ、B 保持・停止を確認 |
| M15 | `D::test_smoke_numbers_never_enter_events_inputs_or_endpoint` — event、handshake、current_perf、endpoint を検査 |
| M16 | `R::test_tier0_contract_mismatch_rejected` — 実 report に status／契約差を入力 |
| M17 | `D::test_header_declares_shared_tier0_contract` — 実 `_header` |

**6. 所有外への波及**

- `test_p3_s4_loop.py` の次の 2 件は、新しい実 evidence/build 経路を通せない既存 fixture のため、親での追従が必要です。編集していません。
  - `test_machine_no_authority_guard_and_sidecar_before_campaign`
  - `test_b5_duplicate_skip_returns_failure_without_restore`
- 共有 `_write_attempt` は候補 submission に passed sidecar を付けるよう更新しました。これを使う `FakeRunner` と report の consumer test に波及します。既存の分類期待値は緩和していません。
- 非 B-5・stock・dry-run は AST と既存回帰検査で確認する構成です。今回、それらの動的検証は行っていません。
- T-2632 land 後の provenance outcome 値域との照合は親に残ります。

**7. 親の実走候補**

まず変更した 4 test file と、上記 meta-test／seam test を `tools/run_tests.py` 経由で確認してください。

`T::test_live_*` は scratch submit-tree と通常の実行認可に加え、次が必要です。

- `IZANAGI_B5_TIER0_TEST_RECEIPT`
- `IZANAGI_B5_TIER0_TEST_OUTPUT_ROOT` — 許可された scratch 出力 root

receipt 未指定では live node は **skip** します。挿入点検査と合わせて、`T::test_live_pipeline_reuses_perf_cache_and_keeps_verify` が実 cache hit・binary hash 一致・verify／bench 継続の確認対象です。

## 総括

**実装済み・未実走。** 構文・差分・変更範囲の静的確認は通過しました。親での実走、M1〜M17 の変異確認、所有外 seam 2 件の追従、T-2632 との照合が残っています。