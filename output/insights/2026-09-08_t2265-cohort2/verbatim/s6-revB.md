## 所見 1: 既存 cohort 1 と legacy の診断走行は統合後に成果物を生成できない

- 所見: terminal 無効の既存 2 trace literal も producer が raw v3 を出す一方、parser は raw v3 に terminal 1 件を必須とするため、既存走行は最初の run で拒否される。
- 根拠: producer は terminal 値に関係なく `patch-audit/new/include/backoff.hh:217` で `IZANAGI_BACKOFF_TRACE v=3`、同 `:258-262` で `flushes` 付き summary を出す。.pbs は既存 2 literal に `TRACE_EXTIME=3`、terminal 値 0 を割り当てる (`tools/pegasus/probes/t2187_adaptive_const_probe.pbs:162-170`)。parser は `tools/pegasus/probes/t2187_adaptive_const_probe.py:1285-1298` で raw v3 に末尾 terminal と `flushes=1` を必須化する。統合 test も terminal 無しの `flushes=0` を parser へ渡す (`orchestrator/tests/test_dynamic_backoff_transitions.py:1771-1779`) ため、非実走ながらコード上は必ず赤になる。これは unit B の「cohort 1 保持」報告 (`s5-unitB.md:13-19`) と矛盾する。
- 実害: legacy 3-cell と cohort 1 3-cell の新規診断 job は最終 JSON を書けず、既存受理集合が縮む。
- 提案: `BACKOFF_TRACE_TERMINAL_US == 0` の build は従来の raw v2 書式と 3-key summary を出し、非 0 の build だけ raw v3 を出すよう patch C を最小修正する。

## 所見 2: terminal 非閉鎖という事前登録済み outcome が parser で消される

- 所見: cohort 2 で terminal が生成されなかった run を解析器は `inconclusive` にする設計だが、unit B parser と plot がその成果物を先に拒否するため、この裁定経路は実在しない。
- 根拠: 凍結事前登録は commit 停止を含む terminal 非閉鎖を `inconclusive` と定める (`docs/backoff-counterfactual-cohort2-preregistration.md:300-303`)。解析器も terminal 0 件を許し (`orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:195-218`)、`terminal_not_closed` を返す (`:455-482`)。対して parser は terminal 位置を必ず `[len(events)-1]` と要求する (`tools/pegasus/probes/t2187_adaptive_const_probe.py:1285-1306`)。plot も同じくちょうど 1 件を要求する (`tools/plotting/plot_dynamic_backoff.py:747-771`)。親契約自身も「ちょうど 1 件」 (`impl-contract.md:45-51`) と「terminal 非閉鎖を inconclusive」 (`:90-91`) を同時に置いている。
- 実害: outcome に依存する非閉鎖が解析上の `inconclusive` ではなく job 失敗または不完全 journal になり、受理集合と主判定理由が事前登録から変わる。
- 提案: raw v3 parser と schema v4 plot を terminal 0 または 1 件に合わせ、0 件では `flushes=0`, `updates=retained=len(events)`, `dropped=0` を要求する。凍結事前登録は変更せず、矛盾する実装契約側を訂正する。

## 所見 3: cohort 2 plot の公開 CLI は本 wave の成果物だけでは起動できない

- 所見: plot は cohort 2 schema を読めるが、同一 identity かつ extime 6 の旧 7-cell performance artifact を 6 または 7 本要求し、本 wave の 12 診断 job と 49 認証 jobからはその入力集合が得られない。
- 根拠: `load_inputs` は performance JSON を 6 または 7 本必須とする (`tools/plotting/plot_dynamic_backoff.py:1235-1253`)、全入力 identity の逐語一致も要求する (`:1267-1269`)。performance 側は旧 `CELLS` の rotation だけを受理する (`:442-496`)。CLI も performance 引数を 1 本以上必須とし、常に 3 図を作る (`:1781-1797`)。正例 test は production 成果物ではなく、fixture の performance 7 本を extime 6 に書き換えている (`orchestrator/tests/test_plot_dynamic_backoff.py:372-388`)。親の投入集合は 12 診断 job と 49 認証 jobだけである (`s4-ruling.md:140-151`)。
- 実害: cohort 2 JSON が生成されても、追加の scope 外 performance 計測なしには新設 plot 経路を利用できない。
- 提案: R5 を残すなら schema v4 に限る診断-only CLI 経路へ最小分離する。分離しないなら cohort 2 plot 対応を本 wave の完了主張から外す。この選択は親 scope の裁定が必要。

## 所見 4: producer と consumer の逐語書式は terminal 完走時には一致する

- 所見: terminal が 1 件生成され、通常 event が 65,535 件以下なら、C++、unit B parser、unit C 解析器の field 名、順序、trigger 対応、summary 算術は一致する。
- 根拠: producer の順序は `seq tsc window_us window_commits trigger backoff_before backoff_after gradient_sign step_us ceiling_us ceiling_changed parity_branch recommended_delta_sign assigned_invert inversion_realized both_actions_feasible terminal_flush` (`patch-audit/new/include/backoff.hh:217-256`)、parser regex も同順 (`tools/pegasus/probes/t2187_adaptive_const_probe.py:1073-1090`)。summary は双方とも `updates retained dropped flushes` (`backoff.hh:258-262`, parser `:1094-1099`)。整数 trigger `3` は `"terminal"` へ写像される (`probe.py:1092,1194`)。解析器が要求する `terminal_flush`, `"terminal"`, `assigned_invert=-1`, `recommended_delta_sign=0`, `inversion_realized=0`, `both_actions_feasible=0` は parser の正規化出力と一致する (`backoff_counterfactual_cohort2_analysis.py:136-177`)。
- 実害: 上記条件の適格 run では producer-consumer の文字ずれによる値の変化はない。
- 提案: この逐語部分は維持し、所見 1 と 2 の「terminal 0 件」の分岐だけ直す。

## 所見 5: ring 容量到達時は `seq` と summary の契約が壊れるが fail-closed になる

- 所見: 通常 event 数を `n` とすると `n <= 65535` では `seq=0..n` と `len(events)=updates+flushes` が成立するが、`n >= 65536` では terminal が最古 event を上書きして成立しない。
- 根拠: 通常 event は `seq=updates` 後に `updates` を増やす (`patch-audit/new/include/backoff.hh:569-595`)。terminal も `seq=updates` だが、`retained==65536` なら `retained` を 1 減らして `dropped` を増やす (`:628-654`)。従って `n=65536` では出力は `seq=1..65536`、summary は `updates=65536 retained=65535 dropped=1 flushes=1`、出力長は 65536 で `updates+flushes=65537` となる。parser は 0 始まり連続性と `dropped=0` を要求し (`probe.py:1278-1306`)、解析器も同じく拒否する (`backoff_counterfactual_cohort2_analysis.py:207-218`)。
- 実害: 容量超過時は値を誤受理せず成果物全体が拒否されるが、producer 層だけでは仕様式を満たさない。
- 提案: 事前登録の既観測 event 数は 555 から 671 件 (`docs/backoff-counterfactual-cohort2-preregistration.md:61`) なので、仮想的な容量対策 gate は追加しない。親の実測で 65,536 に接近した場合だけ scope を再裁定する。

## 所見 6: consumer 参照監査ではコード追随は概ね入ったが、結合 test と利用文書が取り残されている

- 所見: 指定どおり `orchestrator/tests/` と `tools/` を module 名で全検索した結果、実コードの registry/default 追随は入っているが、A-B 結合 test は赤のままで、plot 利用文書は v4 を記載していない。
- 根拠: 検出した参照は次のとおり。

  - `condition_meaning_gate`: `condition_gate_test_support.py:7`, `test_backoff_extended_sweep.py:134`, `test_backoff_profile_pegasus.py:714`, `test_backoff_sweep.py:117`, `test_ccbench_spawn_sites.py:22`, `test_condition_meaning_gate.py:17`, `test_mocc_proof_surface.py:17`, `test_p3_s4_loop.py:7336`, `test_paper_story_a1_paired.py:4134`, `test_paper_story_a2_certification.py:256`, `test_pegasus_calibration_workload.py:126`, `test_s1_direct_comparison.py:30`, `test_s5_permutation_coverage.py:95`, `test_screening_driver.py:19`, `test_t2228_driver_gate_liveness_probe.py:9`, `test_t316_sandbox_probe.py:141`; tools 側は `certify_calibration.sh:381`, `t139_positive_control_probe.sh:185`, `t139_r4_env_probe.sh:259`, `t1683_rr5_cost_probe.py:9`, `t2228_driver_gate_liveness_probe.py:45`, `t316_sandbox_backend_probe.py:36`, `run_ss2pl_lock_study.py:34`。
  - `screening_driver`: `test_backoff_requested_us.py:882`, `test_campaign.py:5364`, `test_condition_meaning_gate.py:18`, `test_official_perf_closure.py:74`, `test_p2_2_site_aware.py:23`, `test_screening_driver.py:20`, `test_t1416_backoff_compiler_binding.py:241`。
  - `plot_dynamic_backoff`: `test_plot_dynamic_backoff.py:18` と `tools/plotting/README.md:189`。
  - `t2187_adaptive_const_probe`: `test_ccbench_spawn_sites.py:923`, `test_dynamic_backoff_transitions.py:1772`, `test_hooks.py:3064`, `test_plot_dynamic_backoff.py:17`, `test_t2187_adaptive_const_probe.py:22`, `.pbs:7`、運用登録 `tools/pegasus/admission_registry.json:190-200`。
  - cohort 2 解析器の直接 consumer は `test_backoff_counterfactual_cohort2_analysis.py:16` だけで、production caller は無い。

  registry と screening default はそれぞれ `condition_meaning_gate.py:124-128` と `screening_driver.py:62` で追随済みであり、動的 inventory consumer に追加漏れは見つからない。一方、結合 test は所見 1 の理由で赤となり、README は schema v2/v3 しか案内していない (`tools/plotting/README.md:189-195`)。
- 実害: condition gate の受理集合は保たれるが、統合破損を test 全体が示し、利用者は v4 の実行条件を文書から再現できない。
- 提案: 所見 1 と 2 の修正後に既存の実 parser 結合 test を通る形へ直し、plot を残す場合だけ `tools/plotting/README.md` を v4 と実際の入力形へ追随させる。

## 所見 7: spawn site pin は統合後の実物と一致する

- 所見: `test_ccbench_spawn_sites.py` の 2 本の pin と理由文は、統合後 driver の実際の build call と certification cell 数に一致する。
- 根拠: 実物の `buildcache.build` は certification 内の `tools/pegasus/probes/t2187_adaptive_const_probe.py:3375` と main 内の `:3749` の 2 本だけで、pin は `test_ccbench_spawn_sites.py:923-945` および exact ledger `:2687-2695` に同じ値を持つ。理由文の `exact 4 cell` は `CERT_CELLS` の tuned、dynamic、cohort2-p1、cohort2-p2 の 4 要素 (`probe.py:302-307`) と一致する。
- 実害: 行番号 drift による meta-test の偽赤または未登録 sink はない。
- 提案: 修正不要。

## 所見 8: PBS から driver への cohort 2 引数経路と既存 certification 経路は実在する

- 所見: PBS は cohort 2 の exact cell、extime 6、terminal 5,000,000 us を driver へ渡し、cohort 1 と certification へ非 0 terminal 値を漏らさないが、診断成果物は所見 1 と 2 で停止する。
- 根拠: exact plus literal は `.pbs:22`、cohort 別 extime と terminal 選択は `:162-180`、driver への `--cells`, `--extime`, `--backoff-trace-terminal-us` は `:430-444`。driver は同じ閉じた表を再検査する (`probe.py:3045-3088`)。genome へ terminal define を追加するのは値が非 0 の場合だけ (`:723-724`)。certification branch は terminal 引数を渡さず (`.pbs:447-473`)、旧 2 cell は extime 3 のまま (`:182-200`, `probe.py:337-342`)。`PBS_O_WORKDIR` は canonical root、tracked-clean、exact HEAD を要求する (`.pbs:43-57`) ため、親裁定どおり detached tree で `cd -P` 後に qsub すれば満たせる。
- 実害: cohort 2 の build/run 引数自体は正しい。既存 certification の受理集合にも静的な破損はないが、既存診断走行だけは完走できない。
- 提案: PBS と certification 表は維持し、parser/schema 分岐だけ修正する。実際の qsub、build、certification の通過は親実測まで未確認とする。

## 所見 9: test の変異帰属には重複と fixture 依存がある

- 所見: 新設 test は主要行を覆うが、同じ 1 行変異で複数 node が同時に赤になる冗長群があり、一部 node は production を変えず共有 fixture だけでも赤にできる。
- 根拠: 主要な 1 行変異と赤になる node 集合は次のとおり。

  - `backoff.hh:294` の除算比較を乗算へ戻すと `test_count_window_cap_comparison_is_overflow_safe`。
  - `backoff.hh:129-130` の terminal static assert を外すと `test_terminal_deadline_static_assert_rejects_out_of_domain_values` の 2 case。
  - `backoff.hh:168` の trace 境界から terminal state を外すと既存 `test_trace_preprocesses_out_of_trace_zero_builds` と新設 `test_terminal_instrumentation_preprocesses_completely_out_of_trace_zero`。
  - `backoff.hh:602-603` の guard を削除または `return false` にすると `test_terminal_is_recorded_once_and_remains_the_last_event`, `test_terminal_does_not_update_backoff_advance_lcg_or_assign`, `test_terminal_recorded_guard_precedes_all_terminal_eligibility_checks` の 3 node。
  - `backoff.hh:438-440` の recommendation を gradient の alias にすると `test_trace_v3_records_parity_recommendation_not_gradient_alias` と既存 `test_policy_two_lcg_advances_on_every_update`。
  - 解析器 `:455` の `events[1:]` を `events` にすると `test_seq_zero_is_excluded_before_pairing_under_cohort2` と `test_terminal_flush_is_following_only_and_does_not_consume_lcg`。
  - 解析器 `:486` で terminal following を落とすと `test_terminal_flush_is_following_only_and_does_not_consume_lcg` と `test_final_normal_assignment_changes_estimate_through_terminal_following_window`。
  - 解析器 `:231-234` で terminal でも LCG を進めると `test_assignment_lcg_accepts_exact_positive_sequence_and_rejects_one_bit_flip` と `test_terminal_flush_is_following_only_and_does_not_consume_lcg`。
  - B の certification 表 `probe.py:302-351` を壊すと既存 `test_public_certification_accepts_each_exact_cell_and_rejects_widening` と新設 `test_cohort2_certification_is_exact_and_policy2_uses_default_seed`。
  - cohort 2 trace 表 `probe.py:3051-3088` または PBS `:162-180` を壊すと `test_backoff_trace_contract_accepts_only_three_exact_cell_literals`, `test_pbs_dynamic_output_and_plus_transport_are_fail_closed`, `test_two_layer_trace_literals_are_byte_identical` の重複群。
  - registry `condition_meaning_gate.py:124-128` を削ると `test_counterfactual_specs_are_exact`, `test_define_inventory_includes_counterfactual_defaults`, `test_screening_condition_requests_cover_exact_define_specs`, `test_patch_define_inventory_matches_condition_gate_registry`。
  - pure behavior ではない node は `test_module_claim_names_the_exact_38_define_supply_domain` で、docstring `condition_meaning_gate.py:12-15` だけを変えて赤にできる。`test_analysis_preregistration_file_is_bound_to_literal_cohort2_sha` も凍結入力 bytes だけで赤になるが、これは意図した束縛 test。
  - shared fixture だけで赤にできる具体例は、`POLICY_DRIVER_SOURCE` の `results[0].local_commit_counts_=55` を 54 にする変異 (`test_dynamic_backoff_transitions.py:647`) で、上記 terminal runtime 2 node が production patch 無変更のまま赤になる。`test_trace_v3_records_parity_recommendation_not_gradient_alias` も fixture の `force_gradient(..., 0, ...)` (`:695-696`) を変えるだけで赤になる。

  また、C の artifact test は独自 `_row` fixture を組み立てる (`test_backoff_counterfactual_cohort2_analysis.py:130-165`) ため、unit B の実 parser 出力を C へ渡す正の結合 node は存在しない。
- 実害: 赤の本数を独立な保護数として数えると過大評価になり、A-B-C 間の実 artifact drift は synthetic fixture 群が緑でも残る。
- 提案: gate を増設せず、既存 `test_emitter_stdout_parses_with_the_real_parser` を修正後の正例として成立させ、その出力を既存 C validator まで渡す 1 本の結合確認へ拡張する。重複 node は削除必須ではないが、段 5 報告の変異帰属を独立保証として数えない。

## 所見 10: 実ファイルの unit 間重複編集はないが Unit D は親の所有裁定に存在しない

- 所見: A、B、C、D の実際の変更ファイルは相互重複しない一方、段 4 の正式な所有表は 3 unit だけで、Unit D の 4 ファイルは未宣言 ownership で統合されている。
- 根拠: integrated.diff の 15 ファイルは A の patch、README、transition test、B の probe、PBS、2 test、C の解析器、解析 test、plot、plot test、D の condition gate、screening driver、2 test に一意に分割できる。各 s5 報告の所有宣言とも重複しない (`s5-unitA.md:3-17`, `s5-unitB.md:3-11`, `s5-unitC.md:1-20`, `s5-unitD.md:1-7`)。しかし正式な R7 は Unit AからCの 3 unit しか列挙しない (`s4-ruling.md:112-120`)。
- 実害: Unit D が他 unit の file を侵してはいないが、親が確定した所有境界だけを基準にすれば 4 ファイルすべてが無権限変更扱いになる。
- 提案: code を戻すのではなく、段 7 で Unit D の 4-file ownership を明示的に追認する。これは親の裁定記録の修正であり、production scope の拡張ではない。

## 所見 11: 現物から誤りと判定できる親裁定は 3 点ある

- 所見: 「1 秒の余裕で terminal が必ず入る」、「3 unit 所有」、「cohort 2 plot がこの wave の成果物で利用可能」という親判断は現物と一致しない。
- 根拠: terminal handler は 5 秒経過だけでなく count 差 10,000 以上も要求する (`backoff.hh:604-609`) ため、R3 の「terminal が必ず run 内に入る」 (`s4-ruling.md:79-80`) は commit 停止時に偽である。3 unit 所有は所見 10 のとおり。plot の入力不足は所見 3 のとおり。加えて impl-contract の「既存 cohort 1 を壊さない」 (`impl-contract.md:25`) は所見 1 の実装により未達である。
- 実害: 親裁定をそのまま完了条件に使うと、非閉鎖 outcome の欠落、既存走行の破損、実行不能な plot を見逃す。
- 提案: 段 7 では上の 3 点だけを訂正し、統計的裁定や scope 外の一般化には広げない。

## 総括

- 着地前に必ず直すべき所見 (優先順): 1. terminal 無効時の raw v2 互換復元、2. terminal 非閉鎖を parser から解析器まで通す修正、3. cohort 2 plot を診断-only で実在化するか scope 外へ戻す裁定、4. Unit D ownership の追認。
- producer と consumer が噛み合わない箇所: terminal 無効または非閉鎖の raw v3 `terminal_flush=0` / `flushes=0` を unit B parser が拒否し、unit C 解析器は terminal 0 件を受理する一方で plot は拒否する。
- 判定不能・情報不足で結論できなかった点: pytest、実 build、qsub、12 診断 job、49 certification job は未実走であり、全 run の terminal 閉鎖、実 event 数、Pegasus 上の最終通過は親実測まで判定不能。