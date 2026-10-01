## 総括

**条件付き GO。** U-A〜U-C の実装経路は具体化できる。ただし、現行 pin C と仕様 digest 未登録のままでは、本番の gen-opt 候補を certified と確定できない。U-D は fixture を使った配線の生死確認とし、その結果を本評価と区別して記録する。

## (P) への賛否

- **P1 — 条件付き賛成。** driver の明示 `True` と、genome の `SILO_ORDER_VARIANT=1` による pipeline 側の強制を併用する。強制値は caller の `False` で上書きできない形にする。flag の build define は [model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/model.py:141) と [骨格 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/patches/silo-lock-order-variant.patch:255) に実在する。
- **P2 — 賛成。** 消費側で `cc-model-result/1` を先に閉じて定義し、md_19 に同じ形を要求する。既存の反例 schema は [schema.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/tools/cc_model_checker/schema.py:35)。
- **P3 — 賛成。** 期待 digest を結果 file から読まず、軸側の登録値と照合する。未登録なら fixture を明示注入した試験以外は build 前に拒否する。
- **P4 — 賛成。** 全順列を扱う仕様一つに軸単位の digest 一つを対応させる。ただし結果には探索済み場面集合と各場面の完了を要求する。[段 A 候補 §5.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md:239)。
- **P5 — 賛成。** 今回の「1 周」は名前つき対照を proposal として投入すれば成立する。新 LLM role は不要。`--emit-coder-input` は将来の role に渡せる閉じた出力として実装する。
- **P6 — 賛成。** 並べ替え件数の計数 build は今回の certified 判定条件ではない。段 A の効果評価には別途必要。
- **P7 — 賛成。** D5 の判定述語は維持し、証拠の取得時点を build snapshot に束縛する。`MEANING_VERSION = 2` は据え置く。ただし snapshot 束縛の回帰試験を必須にする。[D2321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/docs/decisions.md:74602)、[model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/verifier/model.py:11)。
- **P8 — 賛成。** pin C には U1 の gate emitter がなく、U1 を未追跡差分として重ねる経路は [source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/source_digest.py:97) の許可集合にも収まらない。U-D の patched checkout は起動器で扱い、pipeline の要求伝播は試験で検証する。

## U-A 計画

1. [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/verifier/core.py:616) の `verify_trace_dir_with_capability` に keyword-only `require_gate_witness: bool = False` を追加する。既存どおり `_bound_proof_source_snapshot` を先に実行し、その戻り値で `verify_trace_dir(..., require_gate_witness=require_gate_witness, _proof_source_snapshot=...)` を呼ぶ。`True` の型も厳密に検査する。capability の構築・receipt・結果投影は変更しない。[core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/verifier/core.py:630)。
2. [model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/verifier/model.py:185) の `CompiledProtocolSourceSnapshot` に、要求時だけ埋める gate 証拠を追加する。`include/ycsb.hh`、`cc/silo/transaction.cc`、`cc/silo/ycsb_silo.cc` の正規化 text と、引用 include が同じ header に解決したかの capture 時の事実を保持する。通常 capture は従来の三 field のままにし、[source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/source_digest.py:129) の通常 serialize は従来の v1 JSON **bytes と同一**にする。gate 証拠ありの場合だけ別 schema または閉じた追加 field を serialize/deserialize し、未知 field・欠落・型違いを拒否する。
3. capture の実点は [source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/source_digest.py:2413) の `resolve_evidence` と [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/pipeline.py:1924) の再 capture の**両方**で揃える。片方だけを拡張すると `source_evidence != current_evidence` または `_bind_runtime_verification` の一致検査で落ちる。要求を決めてから source identity を解決し、build 前の同じ source 状態を二度比較する。[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/pipeline.py:1905)。
4. [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/verifier/core.py:43) の disk 版 `_gate_d5(ccbench_root)` は standalone CLI 用に残す。snapshot が渡された要求つき判定では、snapshot text と capture 済み include 解決事実だけを使う `_gate_d5_snapshot` を呼ぶ。[core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/verifier/core.py:281) の D5 分岐で disk へ戻らないことを、capture 後に source file を改変・削除する試験で固定する。
5. [loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/loop.py:522) → `pipeline.evaluate` [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/pipeline.py:3068) → `_prepare_evaluation_core` → local と child の `_execute_verification_repetition` [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/pipeline.py:626) へ keyword を運ぶ。実効値は `明示要求 or (genome.protocol == "silo" and genome.flags["SILO_ORDER_VARIANT"] != 0)` とし、既存 caller では keyword 自体を送らない分岐を保つ。fan-out task [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/pipeline.py:887) と [verify_fanout_worker.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/verify_fanout_worker.py:29) に要求を閉じて伝播し、旧 task bytes は要求なしで維持する。
6. D442 の四 file は **`core.py` と `model.py` を変更、`dsg.py` と `parse.py` は変更不要**。既存の [test_verifier.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_verifier.py:2923)、[test_verifier_gate_witness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_verifier_gate_witness.py:250)、[test_t1286_commit_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_t1286_commit_receipt.py:236) は無変更で緑を目標にする。新試験で要求なしの `result_to_dict`・`result_to_dict_v3`・`verify_payload`・receipt digest・snapshot JSON を既存 fixture の byte 列と比較する。`test_campaign.py` の capability mock が新 keyword を受けられない箇所だけ、互換分岐を確認して必要なら fixture を更新する。

## U-B 計画

新 module `orchestrator/campaign/silo_lock_order_model_gate.py` に、閉じた `cc-model-result/1` を置く。必須 field は `schema`、`axis`、`specification_digest`、`checker_identity`、`scenarios`。`checker_identity` は checker 名・版・実装 digest の閉じた組、各 scenario は `scenario_id`、`complete`、`stop_reason`、`counterexamples` とする。`complete=True` は `stop_reason=null`、偽なら列挙された停止理由が必須。反例配列の各要素は [schema.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/tools/cc_model_checker/schema.py:81) の `validate_counterexample(..., vocabulary=...)` を通し、`specification_digest` と `scenario_id` も外側と一致させる。重複 JSON key、余分な field、場面 ID の重複を拒否する。

期待 digest と必須場面 ID 集合は [axis_silo_lock_order.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/axis_silo_lock_order.py:4) の隣に登録する。登録集合は [段 A 候補 §5.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md:265) の L1、L2、L3 を明示的な ID として固定する。欠落・digest 不一致・未完了・反例ありはすべて build 前に拒否し、別々の理由コードを返す。md_19 はこの結果を生成できるが、その着地までは本番 digest を空のままにして全候補を拒否する。fixture digest の注入は試験と U-D 起動器に限定し、履歴に `model_evidence_kind="fixture"` を刻む。[共通 checker の設計メモ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/output/insights/2026-09-29/gen-opt-model-checker/README.md:177)。

反例の schema 通過だけでは真偽は確定しない。md_19 の replay 可能な結果には replay 成功の閉じた証拠を要求する設計を合わせ、実物が未着地の間は fixture の構造試験以上を主張しない。[正しさ関門 §4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/output/insights/2026-09-29/gen-opt-correctness-gate/README.md:255)。

## U-C 計画

新 sibling `orchestrator/campaign/p3_s4_loop_lock_order.py` は `from . import p3_s4_loop_policy as P` とし、P の `_unique_pairs`、`_perf_identity`、計測契約・reason code 化など汎用部品を再利用する。[p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/p3_s4_loop_policy.py:128) の `load_proposal_file` は axis が異なるので再利用しない。`default_cfg` の spec・search tag・`BASE` も方策軸専用なので新定義にする。[p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/p3_s4_loop_policy.py:164)。

関数の順は `load_lock_order_proposal`（重複 key 禁止、閉じた `coder`/`auditor`、axis は `silo-lock-order-policy`）→ `run_one_iteration`（`patchharness.applied`、[order_gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/silo_lock_order_gate.py:23) を `write=False` で検査）→ `require_model_result` → 合格時だけ `order_gate(write=True)` と `run_campaign(..., require_gate_witness=True)` → `_result_history` → `_append_history` とする。小モデル拒否時も `lock_order_history.jsonl` に一行書き、build と trace は起動しない。`drive_iteration` は既存の停止・iteration 状態部品を再利用するが、方策用の history や critic 投影はコピーしない。[p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/p3_s4_loop_policy.py:460)。

history 行は `schema`、`iteration`、`axis`、`proposal_digest`、`variant_id`、`outcome`、`reject_code`、`model_specification_digest`、`model_evidence_kind`、`model_scenario_ids`、`counterexamples`、`verifier_digest`、`measurement_campaign_id` の閉じた形にする。反例は validate 済みの dataclass からのみ投影し、自由文の `message`・`justification`・例外本文を載せない。key 名は [policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/codex_roles/policy.py:176) と manifest の禁止 token に照合する。`make_lock_order_coder_input` / `--emit-coder-input` は軸仕様、baseline、閉じた `self_history` を出し、反例の field を再検証してから含める。

新試験は `test_silo_lock_order_model_gate.py`、`test_p3_s4_loop_lock_order.py`、`test_verifier_capability_gate_witness.py`、`test_pipeline_gate_witness.py`。主な赤試験は gate 前 build、モデル未登録・欠落・未完了・自己申告 digest、反例の余分な field、flag 由来の要求強制、local・fan-out への伝播、要求なし bytes 一致とする。

## U-D 計画

repo 外起動器は node-local checkout で pin C から U1 bundle `dcb9a41f3` を取り込み、`u1-final/patches/fix-silo-intra-txn-values.patch`、次に [骨格 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/patches/silo-lock-order-variant.patch:1) を適用する。各段で git status と patch 適用結果を記録する。名前つき `version_desc` は [axis_silo_lock_order.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/axis_silo_lock_order.py:15) から取り、driver の intake → `order_gate` → fixture を明示した小モデル関門を通す。合格後に hole を書き、`TRACE=1`、`SILO_ORDER_VARIANT=1` で trace build と二つの workload を走らせる。

判定は新しい `verify_trace_dir_with_capability(..., require_gate_witness=True)` を使う。起動器は build 前に gate 証拠を含む snapshot を capture し、同一 checkout に対する `SourceEvidence` と `BuildAdmission` を正規 API で作って渡す。これらを正規に導出できない場合は capability を捏造せず、構造化した admission 拒否を history に記録する。pin C 固定の pipeline ではこの patched source を本番 source identity として受理できないため、U-D の成功は **fixture 付き配線確認**として扱う。pin 前進と md_19 着地後に本番の certified 判定を取り直す。

直列条件は名前つき対照 **1 種 × workload 2 種 = 2 run**、trace build は共通の 1 回。先例の md_14 は「build＋2 workload＋判定」で **117〜130 秒／条件一式**、md_13 は **81 秒／一式**なので、起動・fixture 関門込みで約 **2〜3 分の 1 job**を見込む。再試行を含めても 2 node 時間未満に収め、実 Elapse を記録する。

## inventory 追記一覧

- [test_p3_exploration_namespace.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_p3_exploration_namespace.py:538): discovery の名前 tuple に `p3_s4_loop_lock_order` を追加し、[DriverContract](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_p3_exploration_namespace.py:231) に CLI authority、generator ID、argv factory、AST/runtime call 件数、campaign ID 導出を実装形に合わせて一件追加。
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_campaign.py:5509): certified-writer の semantic inventory に新 driver の `campaign.loop.run_campaign` **1 site**、[同 file](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_campaign.py:5598) の raw AST 件数にも **1** を追加。
- [test_p3_build_authority_cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_p3_build_authority_cli.py:71): 新 driver の `main` を coder build authority site に一件追加。
- [test_official_perf_closure.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_official_perf_closure.py:67): `run_campaign` を呼ぶ新 driver を閉包へ追加。
- [orchestrator/tests/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/README.md:122): 新 test ごとに自走 harness を付けるか pytest 専用 allowlist に追加し、[test_plain_runner_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_plain_runner_coverage.py:60) で確認。
- [acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/acceptance_duration_ledger.json): 新 test nodeid の実測値を追記。生成は [update_acceptance_duration_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/tools/update_acceptance_duration_ledger.py:248) に従う。

## 変異候補

| 変異 | 赤になるべき test |
|---|---|
| driver の `require_gate_witness=True` を落とす | `test_p3_s4_loop_lock_order.py` の campaign 呼出し spy |
| genome flag による pipeline 強制を削る | `test_pipeline_gate_witness.py` の flag=1・明示要求なし |
| local または fan-out の片経路で要求を落とす | `test_pipeline_gate_witness.py` の各経路 |
| snapshot D5 を disk 読みに戻す | `test_verifier_capability_gate_witness.py` の capture 後改変 |
| モデル結果の欠落を受理する | `test_silo_lock_order_model_gate.py` の欠落拒否 |
| 結果 file の digest を期待値として自己採用する | 同 test の別 digest 結果 |
| `complete=False` または場面欠落を受理する | 同 test の未完了・必須場面欠落 |
| 反例の余分な field や自由文を history に通す | 同 test の schema 拒否と `test_p3_s4_loop_lock_order.py` の history 投影 |

## 未確認・リスク

- これは静的点検による計画であり、build・test・計測は実行していない。既存 fixture を無変更で全件緑にできるかは実装後の確認事項。
- U-D で patched checkout から正規の `BuildAdmission` を導出する具体的な provenance は、起動器の実装時に確定する。導出不能なら capability の certified は報告できない。
- snapshot に gate 証拠を追加すると D442 の閉包 bytes が変わり、既存 lock の E1 drift が生じる。[gate-verifier の記録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/output/insights/2026-09-30/gen-opt-gate-verifier/README.md:173) の扱いに従って通知・再判定対象を整理する。