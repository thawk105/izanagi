**NO-GO。must-fix は 3 件です。** 本番の Tier0・driver・report は概ね裁定どおりですが、必須の挿入点検査が通常走で skip され、既存回帰 2 件と自走検査 1 件が赤です。以下は静的レビューであり、変異の KILLED は未確認です。

表中の `T` / `D` / `R` は、それぞれ `test_b5_tier0.py` / `test_b5_generator_contrast.py` / `test_b5_generator_contrast_report.py` を指します。

**所見**

1. **must-fix — 必須の挿入点検査を任意の live 実行に依存させている。**
   対象: [test_b5_tier0.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/tests/test_b5_tier0.py:119)、同 :147、:199、:218。

   根拠: `_live_args` は receipt 未指定で `pytest.skip(...)`。4 関数、parameter 展開後 5 node がこの条件に依存する。裁定 §3.4 の「実挿入点での順序」「perf binary」「拒否時 rc 3・digest 非生成・submission なし」が通常走で検査されない。driver の合成 sidecar 検査では、子が実際に submission をいつ書くかは検査できない。

   **成果物への影響:** Tier0 前の submission、trace binary 使用、拒否後の digest 経路への流入を含む実装を、通常受入が排除できない。

   推奨: 順序・拒否・例外伝播は通常走可能な挿入点 fixture にする。実 gateway/parser は現在の executable fixture を再利用する。実 build/cache/verify の確認は §3.5 の親の生死確認へ分離する。**所有 7 file 内で閉じる。** 単に skip を fail に変え、通常受入へ専用 receipt を必須化する修正は勧めない。

   なお **M11 は完全な穴ではない**。:271 の通常 AST 検査が捕捉型を完全一致で確認するため、指定された `except Exception` 変異は静的には落ちる構造になっている。

2. **must-fix — 既存 B-5 seam 2 件の fixture 追従が未完了。**
   対象: [test_p3_s4_loop.py:10362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/tests/test_p3_s4_loop.py:10362)、[p3_s4_loop.py:2374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/p3_s4_loop.py:2374)。

   根拠: 共通 fixture の checkout は `_mk_template_dir` の偽 source directory。新しい `_b5_tier0_build_inputs` が `source_digest.resolve_evidence` を実行するため、`run_campaign` の観測点に届く前に git rc=128 で落ちる。f1 が両件を実証している。

   **成果物への影響:** machine proposal の authority・submission binding と、duplicate 時の復元拒否／digest 非生成を検査する既存受入が成立しない。

   推奨: **所有外 `test_p3_s4_loop.py` の共通 fixture 1 箇所**で、新たに前置された evidence/admission/build/smoke の準備を提供する。両 test 本体の期待値は維持する。所見 1 の通常 fixture と共通化できるが、test 間 import のためだけの汎用基盤は不要。本番に「偽 checkout なら Tier0 を飛ばす」分岐を加えてはならない。

3. **must-fix — 新規 test file に自走入口がない。**
   対象: [test_b5_tier0.py:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/tests/test_b5_tier0.py:297)。

   根拠: ファイル末尾まで `_run` / `__main__` がなく、f1 の `test_every_test_file_is_self_runnable_or_allowlisted` が当該 file のみを列挙して失敗している。

   **成果物への影響:** 素の runner では Tier0 検査を 0 件実行して終了でき、既存の受入条件にも違反する。

   推奨: 隣接する D/R と同じ `pytest.main([__file__, "-q"])` の自走入口を追加する。**所有 7 file 内で閉じる。** allowlist 追加は不要。

4. **should — Tier0 前の certified-writer 認可呼出しは削除候補。**
   対象: [p3_s4_loop.py:2368](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/p3_s4_loop.py:2368)。

   根拠: `require_certified_writer_authorization(...)` の戻り値は未使用。Tier0 は certified 出力を書かず、後続 pipeline の既存認可呼出しは残っている。裁定 §3.1 の build/admission・診断 smoke・sidecar のどれにも、この追加呼出しは指定されていない。

   **成果物への影響:** 有効な認可入力での A/B・certified 集合は変えず、認可不一致時の停止位置を submission より前へ移し、その場合の B 計上を変える追加 gate になっている。

   推奨: この追加呼出しを削除候補とする。既存の site 判定・build admission・pipeline 認可は維持する。残すなら、診断 smoke 前にもこの既存認可を要求する根拠を示す必要がある。**所有内。**

5. **should — capability の ReviewReceipt 対応は現行 B-5 に不要。**
   対象: [p3_s4_loop.py:2015](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/p3_s4_loop.py:2015)。

   根拠: B-5 CLI の machine 経路は `_machine_proposal_capability_resolver` の `GeneratorReceipt` / `None`、LLM 経路は resolver なし。追加 helper は pipeline の汎用 `ReviewReceipt` 分岐まで複製している。

   **成果物への影響:** 現行 B-5 CLI の成果物は変えず、内部 helper が受理する capability の集合だけを広げる。

   推奨: `GeneratorReceipt` と `None`、および不正型の拒否は残し、ReviewReceipt の import・分岐・引数を削減候補とする。admission 導出自体は裁定必須なので削らない。**所有内。**

**追加要素を削った場合の照合**

| 要素 | 判定・削除で失う要件 |
|---|---|
| 契約定数、search/score 共通適用 | 維持。§3.1 の単一定義・score を含む契約、§3.2 header |
| evidence/admission 導出を build の `try` 外へ置く | 維持。§3.1 の準備失敗と候補 build 失敗の分離 |
| capability の GeneratorReceipt / None | 維持。§3.1 の pipeline と同じ capability。machine / LLM の両経路に必要 |
| capability の ReviewReceipt | 削除候補。所見 5 |
| v2 / legacy build 分岐、cache・dependency・grammar 引数 | 維持。§3.1 が明示的に両経路と同じ入力を要求 |
| `trace=False`、perf 1 本だけ | 維持。§3.1。trace build は投入後に残す裁定 |
| build 捕捉型の限定 | 維持。§3.1、§3.3 の候補失敗と分類不能の区別 |
| gateway、固定 flags、parser、32 秒 timeout、bench lock | 維持。§3.1・§3.4 |
| `tier0.json`、判定後・submission 前の書込み | 維持。§3.1、事前登録 §3.1 の A/B 境界 |
| `rejected-tier0` return、早期 return 集合、CLI rc 3 | 維持。§3.1 の submission/WAL/digest 非生成 |
| certified-writer 追加呼出し | 削除候補。所見 4 |
| report の共通構成比較 2 key | 維持。§3.3 が指定した最小変更。新 gate の一般化ではない |
| spawn 目録 1 行 | 維持。§3.1 の既存目録を弱めず gateway client を登録する要求 |

driver の各追加分岐も、次のとおり裁定に直接対応している。

| `classify_slot` の追加要素 | 削除で失う §3.2 の要件 |
|---|---|
| submission の有無によらず sidecar を読む | 投入後の Tier0 通過証拠の確認 |
| stock に sidecar があれば拒否 | stock slot の契約 |
| JSON object / schema の確認 | 壊れた証拠の拒否 |
| slot / campaign / genome の一致 | 別 slot の証拠の拒否 |
| contract 全体の一致 | 共通 Tier0 契約との照合 |
| status/reason の組の確認 | valid passed/rejected の区別 |
| rejected＋未投入 → candidate | A のみ・retry なし |
| rejected＋投入済み → missing | B 保持・系列停止 |
| passed＋投入済み → 従来分類 | Tier0 を certification の代わりにしない |
| passed＋未投入 → 未解決 | Tier0 通過だけで B を増やさない |
| 投入済み＋証拠欠落 → missing | 証拠欠落時の B 保持・停止 |
| `{status, reason, sidecar_sha256}` 射影 | 数値を event に流さず、sidecar への参照を残す |

この検証群は裁定に明記されており、仮想リスク向けとして一括削除する根拠はない。`result["outcome"]` を読込み前に missing にする処理も、JSON 読込み例外時の分類に効いている。

**新規 test の各 node の必要性**

| T の node | 判定 |
|---|---|
| `test_smoke_exact_argv_and_parser` | 維持。§3.4 固定 argv・実 gateway/parser、M4。ただし FLAGS 除去・一時 cwd/log の寿命までの assert は gateway 自身の検査と重複する削除候補 |
| `…rejects_nonzero_or_invalid_output[nonzero]` | 維持。rc 条件、M5 |
| 同 `[empty]` | 維持。出力解析不能 |
| 同 `[zero-commit]` | 維持。commit > 0、M6 |
| 同 `[invalid-counter]` | 維持。既存 integer parser の利用 |
| 同 `[zero-throughput]` | 維持。正 throughput |
| 同 `[infinite-throughput]` | 維持。有限 throughput |
| 同 `[nan-throughput]` | 維持。有限 throughput |
| `test_smoke_parser_fallback` | 維持。独自 parser ではなく既存 parser の判定を使う正例 |
| `test_smoke_timeout` | 維持。bounded timeout、M7 |
| `test_smoke_uses_bench_lock` | 維持。§3.1 の lock、M8 |
| `test_live_insertion_build_smoke_sidecar_submission_order` | 検査内容は必須。live 専用という構成を置換。§3.4、M1～M3 |
| `test_live_rejection_rc3_no_submission_wal_or_digest` | 検査内容は必須。通常走へ移す。§3.4、M9/M10 |
| `test_live_preparation_and_build_io_errors_propagate[_b5_tier0_build_inputs]` | 内容は必要。準備失敗を候補拒否にしない確認を通常走へ |
| 同 `[build_v2]` | 内容は必要。I/O 例外伝播を通常走へ。M11 |
| `test_live_pipeline_reuses_perf_cache_and_keeps_verify` | §3.5 の親の生死確認として維持可能。通常の変異 kill 先には不要 |
| `test_build_exception_boundary_and_preparation_order` | 現状は M11 の通常 kill 先なので削除不可。動的検査を整えた後は AST 形状の重複固定を削減可能 |
| `test_non_b5_stock_and_dry_run_do_not_reach_tier0` | §3.1 の不変条件に必要。ただし AST 検査が証明する範囲に限る |

専用環境変数 2 本は、上記の通常検査には不要。親の実 build 生死確認を test として残す場合には fixture 入力として用途があるため、**生死確認まで削除する提案ではない**。

| D の新規 node | 削除で失うもの／削減候補 |
|---|---|
| `test_tier0_rejection_consumes_A_only_without_retry[random]` | §3.4 の random 30 件全拒否、A のみ、retry なし。必須 |
| 同 `[sweep-matched]` | 同じ拒否処理の追加回帰。random と既存 grid 検査を残すなら削減候補 |
| `test_retry_then_tier0_reject_retains_B` | 前 attempt の B 保持。必須 |
| `test_score_tier0_reject_stops_without_fallback` | score 拒否時の停止。必須 |
| `test_submitted_requires_valid_passed_tier0` の missing/json/list/schema/b5_slot/campaign_id/genome/contract/rejected/status | 各々 §3.2 の欠落・破損・identity・契約・判定不正に対応。維持 |
| `test_missing_tier0_stops_series_with_B_retained` | classifier 単体では確認できない系列停止。維持 |
| `test_stock_with_tier0_is_unclassified` | stock の明示契約。維持 |
| `test_tier0_rejected_evidence_without_submission` の build-error/smoke-failed/smoke-timeout | 3 つの登録済み拒否理由の分類。維持 |
| `test_passed_without_submission_is_unresolved` | 通過と投入を区別。維持 |
| `test_tier0_pass_does_not_replace_anomaly_gate` | §3.4 の anomaly 負例。維持 |
| `test_smoke_numbers_never_enter_events_inputs_or_endpoint` | §3.4 の数値非流出。維持 |
| `test_llm_tier0_rejection_preserves_expected_inputs` | §3.4 の LLM 入力不変。維持 |
| `test_header_declares_shared_tier0_contract` | §3.2 header、M17。維持 |

| R の新規 node | 判定 |
|---|---|
| `test_tier0_contract_mismatch_rejected[status]` | status key の比較を固定。維持 |
| 同 `[contract]` | 契約欠落の混在拒否。維持 |
| 同 `[timeout]` | 契約内部の値の差を拒否。維持 |
| 同 `[applies_to]` | 同じ dict 比較の追加例。timeout を残すなら削減候補 |
| `test_tier0_and_historical_ledger_reading_preserve_AB` | §3.3 の旧台帳互換・A/B 不変。維持 |
| `test_tier0_rejection_report_does_not_recover_B` | producer から report までの A/B 照合。維持 |

**M1～M17 と通常走の対応**

| 変異 | 静的に確認できた状態 |
|---|---|
| M1 | 主たる動的順序検査は skip。AST が削除形によって落ちても、実挿入点の動的保証にはならない |
| M2・M3 | 主たる kill 先が live 順序検査。通常走の穴 |
| M4～M8 | 通常 smoke test に到達する構成 |
| M9・M10 | 子の submission/digest を見る kill 先が live 拒否検査。driver の合成拒否 fixture では代替不可 |
| M11 | live は skip するが、通常 AST 検査が指定の捕捉型拡大を検出する構成 |
| M12・M13 | 通常 D の A-only/retry 検査 |
| M14 | 通常 D の証拠欠落・B 保持・停止検査 |
| M15 | 通常 D の compact 射影・数値非流出検査 |
| M16 | 通常 R の契約混在検査 |
| M17 | 通常 D の header 検査 |

したがって「M1～M3・M9～M11 が全部無検査」ではなく、**特に M2/M3/M9/M10 の通常動的検査欠落が明確**。また、候補 build の `RuntimeError` / `SubprocessError` が実際に `build-error` sidecar と rc 3 へ至る正しい拒否経路は、捕捉型の AST 検査や合成 sidecar だけでは確認できない。

**f1 の赤 3 件の帰属**

| 失敗 | 本差分への帰属と根拠 |
|---|---|
| `test_machine_no_authority_guard_and_sidecar_before_campaign` | **帰属する。** 新設 :2374 → :2018 の evidence 解決で停止し、既存の campaign 境界検査へ届かない |
| `test_b5_duplicate_skip_returns_failure_without_restore` | **帰属する。** 同じ fixture・同じ新設経路で停止し、duplicate outcome を生成する stub へ届かない |
| `test_every_test_file_is_self_runnable_or_allowlisted` | **帰属する。** offender は新規 `test_b5_tier0.py`。自走入口の追加漏れ |

前二者は「本番 source 検証が誤っている」証拠ではなく、必要な本番変更に伴う fixture 追従漏れである。f1 の **3 failed / 4,747 passed / 20 skipped** は受入完了を示さない。

**T-2632 との衝突**

`drive_iteration` の変更は [p3_s4_loop.py:3018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/p3_s4_loop.py:3018) の集合へ outcome を 1 個加えるだけで、`save_loop_state` 自体は変更していない。この変更幅は妥当であり、衝突回避目的の関数再編は不要。

所有外 test の追従も共通 fixture 1 箇所に寄せ、T-2632 の test 本体変更と分離できる。なお裁定 §3.1 の「T-2632 land 後の provenance outcome 値域との照合」は、今回の差分・f1 だけでは完了を確認できない。

## 総括

**NO-GO。must-fix 3 件：**

1. 必須の挿入点・拒否検査を通常走で実行可能にする。
2. 所有外の既存 seam fixture を追従させる。
3. 新規 test file に自走入口を追加する。

report・driver の追加検証は裁定に対応しており維持が妥当。削減は追加認可呼出し、未使用 capability 対応、重複する test assert／parameter に絞れる。
