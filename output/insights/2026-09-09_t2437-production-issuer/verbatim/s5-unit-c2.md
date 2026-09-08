## 前の子の作業の監査結果

[loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-unit-c/orchestrator/campaign/loop.py:368) には次が実装済みでした。

- keyword-only の `result_evidence_context`
- durable write 前の context、単一 genome、balanced 非併用、evidence root 包含検査
- identity-skip、identity-error、terminal-skip、per-result の4発行点
- issuer 例外の上位伝播
- 実 verifier を使う正例と各負例

監査で確認した食い違いは以下です。

- originless の eval-exception で既存 abort frame を省略する回帰があった。
- capability の `campaign_id` 欠落を空文字へ変換する fail-open があった。
- 正例は `verifier_runner` を使っておらず、実 verifier を維持している。
- ただし「stub は trace 生成だけ」という説明には限定が必要。正例は additionally:
  - tmp output root 用に `_has_git_ancestor` を差し替える。
  - 実 `_authorize_measurement` の結果へ実 `build_receipt()` を載せる fixture wrapper を使う。
  - verifier-to-resolver 鎖の stub は `trace_runner` だけ。

空 attempt ID は単位 B の `_ordered_attempt_materials()` が `ResultEvidenceIssuanceRefused` にするため、黙って通らないことを実装から確認しました。

## 直した 2 件

1. [loop.py:829](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-unit-c/orchestrator/campaign/loop.py:829)

   eval-exception の `wal.log(..., STAGE_ABORT, ...)` を従来どおり無条件へ戻しました。originless で trigger-binding、build-start、既存 abort、eval-exception abort の順と payload key 集合を固定する非回帰テストも追加しました。

2. [loop.py:330](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-unit-c/orchestrator/campaign/loop.py:330)

   `origin_capability.campaign_id` の属性欠落、空文字、非文字列を `ResultEvidenceError` で拒否するよう修正しました。[負例](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-unit-c/orchestrator/tests/test_reflux_campaign_issuer.py:796)で3形を検査しています。

## 実走した検査

新規ファイル全7 nodeを直接実行しました。

`PYTHONPATH=. python3 orchestrator/tests/test_reflux_campaign_issuer.py -rf`

結果: **4 passed / 3 failed、5.05秒**。

pass:

- `test_context_shape_rejects_multiple_genomes_and_balanced_before_writes`
- `test_context_exact_type_and_root_binding_precede_campaign_writes`
- `test_issuance_rejects_invalid_origin_capability_campaign_id`
- `test_signature_keeps_context_keyword_only_after_verify_fanout_hosts`

未完了の3 node:

- `test_real_run_campaign_issues_rejected_record_and_originless_is_inert`
- `test_identity_error_terminal_is_explicitly_refused`
- `test_originless_eval_exception_after_terminal_preserves_legacy_abort`

3件とも assertion 前の `contract-loader-drift: ... orchestrator/campaign/loop.py`。未 commit の enforcement source closure による既知の赤であり、実装回帰かどうかは commit 後の再走が必要です。

既存 WAL/abort node:

- `test_wal_append_replay` — pass、0.16秒
- `test_attempt_topology_accepts_abort_then_retry` — pass、0.28秒
- `test_wal_abort_is_terminal_not_adopted` — pass、0.05秒
- `test_loop_isolates_identity_error` — output-root の `/tmp/.git` 境界で assertion 前に停止
- `test_loop_identity_error_is_retryable_after_repair` — 同上
- `test_loop_identity_skip_is_visible_when_stock_id_terminal` — 同上
- `test_loop_does_not_append_abort_after_wal_io_error` — 同上

関連検査:

- 単位 B の実 issuer/resolver と receipt 不在拒否: **2 passed、1.39秒**
- caller inventory、authorization 順序、closed verifier mode の meta-test: **3 passed、28.63秒**
- `py_compile`: pass
- `git diff --check`: pass

なお `test_campaign.py` の直接 runner は nodeid 指定を絞り込まず全体を走らせ、全403件で 333 pass / 67 error / 3 skip でした。fixture 引数欠落、sandbox output-root、Pegasus heavy-run guard、既知 drift が混在するため受入結果には数えていません。

## 正例が通した実 callee の列

今回の未 commit 実走では `run_campaign()` → `ensure_resumable_wal()` → contract-loader 検査で停止したため、以下の完全な鎖は未実走です。

コード上の正例配線:

`run_campaign` → 実 `pipeline.evaluate` → 実 `_execute_verification_repetition` → 実 `verify_trace_dir` → WAL → 実 `issue_campaign_result_evidence` → 実 `produce_ordered_wal_projection` → 実 `derive_physical_result` → 実 `assemble_result_evidence_record` → create-only writer → 実 `resolve_result_evidence`

stub:

- trace ファイル生成用 `trace_runner`
- fixture 前提としての tmp-root admission と mode-none receipt wrapper

`verifier_runner`、deriver、assembler、issuer、WAL、resolver は stub していません。

## 現行の受理・拒否挙動 (scope 前後)

- originless: issuer は no-op。新しい evidence file は置かず、eval-exception abort の stage と payload key は従来どおり。
- context あり: exact context、単一 genome、balanced 非併用、実在 evidence root と layout 包含を durable write 前に要求。
- identity-error: terminal は作るが typed rejected 証拠がないため明示拒否。
- identity-skip / terminal-skip:
  - COMMIT は typed 結果不要の accepted として導出可能。
  - ABORT は typed 結果なしなら拒否。
- per-result:
  - local verifier の typed rejected は発行可能。
  - accepted は typed 値なしで発行可能。
  - remote fan-out rejected、eval-exception、空または非一意 attempt は拒否。
- execution receipt 不在、衝突、issuer 異常は握り潰さず `run_campaign()` 外へ伝播し、summary を返さない。

## 所有外 caller・共有 fixture・consumer test への波及 (静的列挙)

既定引数のまま影響を受けない production caller:

`p2_2.py`、`backoff_sweep.py`、`backoff_extended_sweep.py`、`backoff_repro.py`、`sanity_silo.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`p3_kickoff.py`、`p3_s4_red.py`、`p3_s4_loop.py`、`p3_s4_loop_sort.py`、`p3_s4_loop_trigger_gating.py`、`demo.py`、`b10_backoff_shape_sweep.py`、`paper_story_a1_paired.py`、`paper_story_a2_certification.py`。

共有 fixture/consumer:

- `test_campaign.py` の certified-writer authority と `ratified_enforcement_source`
- `r9_dense_cycle4`
- `reflux_origin_fixture_builder.py`
- `test_reflux_result_evidence.py`
- `test_pipeline_verify_result_retention.py`
- `test_verifier.py`
- `test_reflux_formal_consumer.py`

所有外ファイルや既存テスト期待値は変更していません。

## 受入所要台帳へ登録すべき nodeid と実測所要

新規7 nodeすべてが登録対象です。

- `test_context_shape_rejects_multiple_genomes_and_balanced_before_writes` — 0.01秒、pass
- `test_context_exact_type_and_root_binding_precede_campaign_writes` — 0.005秒未満、pass
- `test_issuance_rejects_invalid_origin_capability_campaign_id` — 0.005秒未満、pass
- `test_signature_keeps_context_keyword_only_after_verify_fanout_hosts` — 0.005秒未満、pass
- `test_real_run_campaign_issues_rejected_record_and_originless_is_inert` — 0.18秒で既知 drift 停止
- `test_identity_error_terminal_is_explicitly_refused` — 0.07秒で既知 drift 停止
- `test_originless_eval_exception_after_terminal_preserves_legacy_abort` — 0.07秒で既知 drift 停止

後3件は受入所要として有効な完走値ではありません。親で commit 後に再計測して登録が必要です。

## 契約の問題

無し。

## 総括

親指摘の2件は修正済みです。所有 path 以外は変更せず、commit、docs編集、push、ブランチ操作はしていません。

ただし中心正例、identity-error、originless WAL 非回帰の3 nodeは既知の contract-loader drift で未完走です。したがって現時点の申告は「実装済み・commit 後の実走待ち」であり、closed ではありません。