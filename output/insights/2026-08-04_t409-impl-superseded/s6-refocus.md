現 worktree は依頼時点から進んでおり、実装は既に `48ec948`、記録は `b3ec6e0` に commit 済みでした。現在の `git diff HEAD` は superseded README のみです。このため、実装差分 `6e22c5b..48ec948` と現在の未 commit 差分を監査対象にしました。pytest は実行していません。

## 対応表

| ID | 判定 | 実装確認 |
|---|---|---|
| R1-1 | closed | ledger は path-only、raw Mapping は拒否。consumer が全 record を再検査する。 |
| R1-2 | closed | record hash ごとの source/provenance と `src_token` を照合し、証拠なしは `SOURCE_UNAVAILABLE`。 |
| R1-3 | **partial** | 指摘された `#if BACKOFF_TRIGGER_GATING && 0` は拒否するが、marker 外側の条件分岐を検査しない。[source_digest.py:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/source_digest.py:245)。成果物影響: receipt が安全な hole を指す一方、binary・性能値・certified 選択は外側の別枝を実行できる。 |
| R1-4 | closed | S8A configure 直前・build 直後に全 `SourceEvidence` を exact 再照合。 |
| R1-5 | closed | receipt 発行時に fresh `resolve_evidence()` と入力全体を比較。 |
| R1-6 | closed | artifact admission が campaign lock の grammar 宣言を topology validator へ渡す。 |
| R1-7 | closed | abort は active attempt 必須、receiptless reason は共有 closed enum。 |
| R1-8 | closed | 親裁定どおり refuted。matched name は閉じた定数集合。 |
| R1-9 | closed | 実 binary inspector → sanitized exception → notes/WAL/log を通す canary node がある。 |
| R1-10 | **partial** | P1–P9 node はあるが quarantine の opt-in がなく、build 側も `_verify_ccbench_commit` で実 gate より前に停止する。[test_buildcache_v2.py:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_buildcache_v2.py:164)、[test_buildcache_v2.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_buildcache_v2.py:186)、[buildcache.py:965](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/buildcache.py:965)。成果物影響: 現 diff での過剰拒否例は構成できず、全層正例という証拠だけが欠けるため nit。 |
| R2-1 | closed | R1-6 と同じ。real v2 trigger 正例も存在。 |
| R2-2 | closed | R1-1/R1-2 と同じ。campaign-wide source 一括代用は不可。 |
| R2-3 | closed | oracle lock に policy/grammar が入り、report は診断付き共有 admitted view の record のみ読む。 |
| R2-4 | closed | Layer3 API・render・CLI が ledger path を伝播し、decision receipt に SHA を残す。 |
| R2-5 | closed | v4 schema は classification 別 `oneOf`。historical proof は非 null・非空必須。 |
| R2-6 | closed | R1-7 と同じ。unknown/missing reason 負例あり。 |
| R2-7 | closed | pinned 5 内の2 producerが recognizer source SHAを literal/live 比較する。 |
| G-1 | closed | `test_campaign.py` に `pytest` import がある。 |
| G-2 | closed | `system_gate`/`ident_all` のみ full trigger evidence。sort/backoff は従来の token-only 経路。trigger cell を非-trigger に落とす ratified input は構成できなかった。 |
| G-3 | **partial** | autonomous/S1 は明示束縛するが、S8A sweep の非-stock materialization は束縛しない。[s8a_trigger_sweep.py:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_sweep.py:262)、[s8a_trigger_sweep.py:336](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_sweep.py:336)。成果物影響: v2 trigger receipt を持つ WAL が grammar-unbound lock になり、sweep の replay/admitted view が拒否される。 |
| G-4 | **partial** | opt-in API と直接 M13 node はあるが、S8A sweep の2経路が引数を渡さない。[s8a_trigger_sweep.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_sweep.py:421)、[s8a_trigger_sweep.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_sweep.py:443)。成果物影響: invalid generator output が quarantine reject でなく後段 prebuild abort となり、sweep provenance の outcome/reason と M13 の実経路帰属が変わる。 |
| G-5 | closed | fixture が現実の `genome=` を渡し、fresh evidence 等値条件は緩和していない。 |
| G-6 | closed | trigger 7-key/non-trigger 5-key fixture が driver/report/ratified freeze で追随。 |
| H-1 | closed | diagnostic API は invalid frame を diagnostics に分離し、返す record は同じ shared topology validation を通す。[artifact_admission.py:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:452)、[artifact_admission.py:689](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:689)、[artifact_admission.py:780](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:780)。admitted projection 外の record 採用は構成できなかった。 |
| H-2 | closed | immutable Mapping/tuple を JSON dict/list に戻して T-080 と execution receipt を検証。 |
| H-3 | closed | axis 名だけでは未束縛、明示 materialization で束縛、競合値は拒否、の3点を pin。 |

## 新規所見

### FOCUS-1 — marker 外側の compiler branch を偽装できる

- file:line: [source_digest.py:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/source_digest.py:245)–[source_digest.py:303](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/source_digest.py:303)
- 攻撃シナリオ: exact marker/frame 全体を `#if BACKOFF_TRIGGER_GATING && 0` の死枝に置き、marker 後の outer `#else` に実挙動を置く。extractor は marker 内の safe hole を PASS にするが compiler は outer else を選ぶ。
- 成果物影響: safe implementation SHA の receipt で、別挙動の binary・cache・性能値・certified 選択を発行できる。
- 判定: **must-fix**。marker 前後の immutable enclosing frame、または template 基準との差分を build authority で検証する必要がある。

### FOCUS-2 — S8A sweep の materialization identity が未束縛

- file:line: [s8a_trigger_sweep.py:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_sweep.py:262)、[s8a_trigger_sweep.py:336](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_sweep.py:336)
- 攻撃シナリオ: `names` に非-stock候補を含めて実 trigger implementation を materialize する。source/build receipt は v2 になるが campaign lock に grammar version がない。
- 成果物影響: sweep WAL は生成されても replay・artifact admission・report の受理集合から除外される。
- 判定: **must-fix**。stock-only と非-stock実体化 run の campaign identity を分ける必要がある。

### FOCUS-3 — G-4 opt-in が S8A sweep で不発

- file:line: [s8a_trigger_sweep.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_sweep.py:421)、[s8a_trigger_sweep.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8a_trigger_sweep.py:443)
- 攻撃シナリオ: generator が文法外 predicate を返しても generic quarantine は通過する。後段 actual-source gate が certification を mask して拒否するため、M13 node の成功から実 caller の発火を推論できない。
- 成果物影響: sweep provenance の `quarantine-reject` が `aborted`/driver failure に変わり、拒否理由と変異帰属が壊れる。
- 判定: **must-fix**。なお同ファイルは段4 B-5 の「編集回避」に含まれており、親が scope 整合を明示する必要がある。

### FOCUS-4 — P1–P9 は全層正例になっていない

- file:line: [test_buildcache_v2.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_buildcache_v2.py:147)
- 攻撃シナリオ: quarantine opt-in を過剰拒否へ変異しても、この node は既定 `False` なので緑のまま。
- 成果物影響: 現 diffで実際の過剰拒否は構成できなかった。
- 判定: **nit**（DW-G05）。`enforce_trigger_gate_language=True` と build側 actual-source recheck 到達を追加すべき。

## 変異 KILL node 監査

| 変異 | 最終 node | 監査 |
|---|---|---|
| M1 | `test_reject_corpus_is_fail_closed` | OK。public checker 直接。 |
| M2 | なし | **不足**。bare `!` node がない。さらに scanner が `!` token を作っても parser が拒否するため診断コード変化だけで、DW-M03 上の KILL ではない。 |
| M3 | `test_a2_5_whitespace_and_punctuator_failures_have_exact_codes` | OK。`: :` 等で受理拡大へ直接到達。 |
| M4 | `test_longest_match_accepts_every_multi_character_punctuator` | OK。 |
| M5 | failure-order 2 node | **diagnostic sensitivity のみ**。判定順交換後も入力は拒否され、受理集合は変わらない。KILL credit 不可。 |
| M6 | `test_token_count_boundaries_511_512_513` | **diagnostic sensitivity のみ**。513-token fixture は余分な `;` を持ち、off-by-one 後も parser が拒否する。 |
| M7 | `test_parenthesis_depth_boundaries_63_64_65` | OK。65深度が受理へ反転。 |
| M8 | `test_semantic_rejections_are_unset_not_true` | OK。非 kUnset 式の受理拡大。 |
| M9 | `test_handwritten_mixed_precedence_truth_tables` | OK。独立 handwritten oracle。 |
| M10 | `test_m10_issue_trigger_receipt_rejects_invalid_actual_source` | OK。receipt 発行境界へ直接到達。 |
| M11 | `test_m11_trigger_receipt_requires_exact_type_not_subclass` | OK。exact-type 単独。 |
| M12 | `test_m12_trigger_cache_hit_rereads_actual_source_without_leak` | OK。crafted cache-hit、prefilter 非経由。 |
| M13 | `test_public_quarantine_trigger_language_reject_is_prewrite_and_no_touch` | node 自体は OK。opt-in 後の正しい帰属。ただし実 S8A caller は opt-in しないため実経路代表性なし。 |
| M14 | `test_three_legacy_campaigns_are_denied` | OK。ledger 無し legacy fixture を直接拒否。 |
| M15 | `test_m15_reinspection_ledger_never_records_rejected_as_passed` | OK。ledger producer 直接。 |
| M16 | `test_m16_receiptless_build_done_is_forbidden` / `...commit...` | OK。 |
| M17 | `test_v4_trigger_claim_boundaries_are_required_and_fixed` | OK。schemaから field を削る変異へ直接到達。 |
| M18 | `test_current_sources_render_byte_exact_and_native_is_empty`、`test_review_ledger_independently_pins...` | OK。adapter/source SHA drift を byte parity/ledger が拒否。 |
| P1–P9 | `test_p1_p9_raw_and_indented_reach_quarantine_receipt_and_build_boundary` | **partial**。18ケースは存在するが opt-in と実 build source gate を踏まない。 |
| M12+M13 | 専用 node なし | **不足**。両独立 node を同時に走らせれば二理由で赤になるだけで、mask 用の単一路ではない。単一理由性を満たさない。 |

mask 上の結論は、M13 が下流 source gate に mask される問題が実 S8A callerで残っています。M2/M5/M6 は変異自体が equivalent/diagnostic-only であり、KILLED と記録してはいけません。

## 攻撃したが構成できなかった面

- H-1 の invalid frame は diagnostics にしか入らず、record projection へ昇格しない。oracle も admitted view の records のみ採用する。
- S1 の `system_gate`/`ident_all` を sort/backoff token-only 分岐へ落とす ratified freeze inputは構成できなかった。
- raw/self-hashed ledger、単一 campaign-wide source、record集合差し替えによる legacy admission は再現不能。
- S8A direct materializer の configure前/build後 swap、receipt発行前の Options/source swap、cache-hit swapはいずれも閉じている。
- receiptless build_done/commit、unknown abort reason、fresh v2 trigger artifact の自己拒否は構成できなかった。
- Layer3 historical proof 欠落、claim-boundary 欠落、oracle receipt/grammar-lock迂回は構成できなかった。

## 総括

- 対応表集計: **closed 22 / partial 4 / regressed 0**。
- 残 must-fix: **3件**（outer compiler frame、S8A materialization identity、S8A opt-in漏れ）。
- nit: P1–P9 全層性と、M2/M5/M6・M12+M13 の変異証拠再設計。
- H-1 の authority/diagnostic 境界そのものは closed。
- 親は新規3負例を追加後、S8A stock-only/non-stock identity と quarantine outcome を実測すること。
- mutation harness は M2/M5/M6 を再照準し、M12+M13 を単一路化してから再走すること。
- P1–P9 は opt-in と build actual-source gate の到達を確認すること。
- 裁定済み一回限り C++ differential も未確認事項として残る。
- 本レビューでは pytest を実行していない。親提示の 1285 passed / 12 skipped / 0 failed を前提値としてのみ扱った。