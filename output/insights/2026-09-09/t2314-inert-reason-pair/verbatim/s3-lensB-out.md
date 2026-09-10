## 所見

- **B-01 / [s2-plan-out.md:144](/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s2-plan-out.md:144)、[acceptance_duration_ledger.json:20046](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/acceptance_duration_ledger.json:20046) / 受入台帳更新がプランから完全に欠落 / 重大度: 高**  
  提案された parametrized node 4 件と単独 node 1 件、計 5 nodeid は現台帳に存在しない。実装時には実測 duration を次の key で add-only 追加し、`nodeid_count` を `20042 → 20047` にする必要がある。

  - `...::test_s6_accepts_each_exact_inert_condition_gate_pair[identity]`
  - `...::test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]`
  - `...::test_s6_rejects_crossed_inert_condition_gate_pair[identical_reason__root_location_comparison]`
  - `...::test_s6_rejects_crossed_inert_condition_gate_pair[root_location_reason__identity_comparison]`
  - `...::test_s6_rejects_requested_default_preprocess_difference`

  updater は既存 entry bytes を維持する add-only 契約であり、duration は成功した JUnit から得る設計である（[update_acceptance_duration_ledger.py:362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/update_acceptance_duration_ledger.py:362)）。値の推測・合成は不可。

- **B-02 / [s2-plan-out.md:105](/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s2-plan-out.md:105)、[condition_meaning_gate.py:941](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:941) / 第 3 reason fixture の決定的な引数が未記載 / 重大度: 中**  
  `requested_value=5, default_value=-1` は inert ではないため、既存 helper と同じ `stock_comparison=True` を流用すると `request-contract-invalid` で evaluator 前段から落ちる。`requested-default-preprocess-different` の genuine admitted family にするには、この helper は明示的に `stock_comparison=False` でなければならない。デフォルト値に任せれば現状は false だが、プランはこの層を固定していない。

- **B-03 / [s2-plan-out.md:156](/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s2-plan-out.md:156)、[t316_sandbox_backend_probe.py:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:358) / 交叉負例は seam だけでは pair membership 到達を証明しない / 重大度: 中**  
  通常経路では両交叉とも gate admission が先に拒否する。comparison だけを交換すれば vocabulary 契約（[condition_meaning_gate.py:3702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:3702)）、evidence 全体を交換すれば missing/unexpected schema（同 [3571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:3571)）で落ちる。  
  replay seam 版では、patched admission が既存 `observed` を返すだけでなく、交叉 family から再生成した receipt summary を渡さなければならない。そうしないと pair membership より前の `receipt_summary == ...`（[t316_sandbox_backend_probe.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:365)）で恒真に拒否される。プランはこの前提を明記していない。

- **B-04 / [s2-plan-out.md:98](/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/codex-artifacts/t2314-inert-reason-pair/s2-plan-out.md:98)、[test_condition_meaning_gate.py:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_condition_meaning_gate.py:646) / 2 組目の正例そのものには欠陥なし / 重大度: なし**  
  提案 fixture は production evaluator を実行する。追加した `__FILE__` は dependency closure 内の code-owned header として root-dependent path に入る（[condition_meaning_gate.py:2106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:2106)）。evaluator は `root_diff_source_roots`、replacement count、`root_diff_has_residual` を発行し（同 [2646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:2646)）、CMake argv は `(cmake, "-S", source_root, ...)` になる（同 [1663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:1663)）。`_issue_arm_record` が integrity 検査後に issuer capability を付与する（同 [1043](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py:1043)）。したがって `_arm_record` 偽造正例ではない。

## 波及一覧

識別子の exact grep では、`orchestrator/tests/` 内で `_condition_gate_family_valid` と `_condition_gate_receipt_summary` の直接参照は 0 件、単独 token `condition_gates` の参照は `test_t316_sandbox_probe.py` のみだった。

- [test_t316_sandbox_probe.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:185) `_condition_gate_receipts`、[同:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:211) `_good_s6`  
  supply entry に scalar `comparison` を双方へ追加すれば通る。

- [同:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:833) `test_stage_judges_reject_injected_bad_observations`  
  更新済み `_good_s6` を使うため通る。

- [同:839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:839) `test_s6_injected_success_without_condition_records_is_not_go`  
  key 欠落を試す負例なので通る。

- [同:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:848) `test_s6_unissued_condition_records_cannot_replace_live_family`  
  issuer capability 拒否は変わらず、通る。

- [同:869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:869) `test_s6_receipt_summary_must_match_live_condition_conclusions`  
  terminal status 改変による summary mismatch は維持され、通る。

- [同:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:877) `test_s6_rejects_legacy_stock_identity_vocabulary`  
  gate の vocabulary 拒否なので通る。

- [同:944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:944) `test_injected_observer_flows_through_judge_and_overall`  
  `_good_stages → _good_s6` 経由で新形を受け、通る。

- [同:958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:958)、[同:986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:986)、[同:1000](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1000)、[同:1014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1014)  
  いずれも `_good_stages` の推移的 consumer。新 field を解釈せず、通る。

- [同:1130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1130) `test_r3_1_coverage_does_not_overclaim`  
  line 1143 の equality は producer/test helper を同時更新すれば通る。line 1146–1149 は `"evidence"` mapping の不在だけを検査するため、scalar `comparison` と両立する。

- [同:1168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1168)、[同:1178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1178)、[同:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1189)、[同:1217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py:1217)  
  `_good_stages` の推移的 consumer。すべて通る。

- [test_official_perf_closure.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_official_perf_closure.py:88)  
  production path の reviewed allowlist。今回の変更は tracked perf call を増やさないため通る。

- [test_hooks.py:3071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_hooks.py:3071)、[同:3336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_hooks.py:3336)  
  path の `dispatch-required` classification を固定するだけで、source bytes は固定していない。通る。

Receipt schema は上げなくてよいと判定する。`SCHEMA_VERSION` は現行 v1（[probe:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:39)）だが、既発行の v1 receipt 2 本には `condition_gates` 自体がなく、現行コードにも既発行 receipt の reader や閉じた key schema がない。policy schema は別系統（[policy:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/policies/t316_sandbox_backend_v1.json:2)）。さらに各 receipt は production bytes の SHA-256 と commit を保持しており、同じ v1 内の意味差は execution binding で識別できる。

## 親 brief への反証

- **「pin 閉包は空」一般化は誤り。** なお、この文言自体は射影された [s1-brief.md](/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s1-brief.md) には存在しない。事実としては PBS 側が production Python を `BOUND_PATHS` に含め、HEAD blob と live SHA-256 を比較する（[t316_sandbox_backend_probe.pbs:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54)、同 [71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:71)）。Python 自身も `_BOUND_RELATIVE_PATHS` と runtime hash を持つ（[probe:2277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:2277)）。literal SHA grep 0 件でも、`HEAD:path` を key にした実行時 pin は存在する。ただし commit 後は自動的に新 blob へ束縛されるため、PBS の co-edit は不要。

- **path/class pin も存在する。** official-perf allowlist、hooks の admission classification、`admission_registry.json` が production path を固定する。いずれも内容変更では壊れないが、「pin はない」という説明には使えない。`test_t316_sandbox_probe.py` には `xdist_group` marker はなく、role 名 pin も見つからなかった。一方、`driver_id` は exact semantic identity として [probe:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py:367) に固定される。

- **「worklog の 1 行で t316 到達可能性を実測」は過大。** 引用箇所は A-5 の `backoff_sweep` 経路が root-location-only になった記録である（[worklog:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/docs/archive/worklog-phase3-0907-1291-1292.md:31)）。t316 自身の実測ではない。既発行 t316 receipt 2 本は v1 だが `condition_gates` を持たず、この経路を立証しない。gate unit test は constructibility、worklog は別 driver の実環境到達を示すに留まる。

- **「編集面は 2 file」は誤り。** 新規 nodeid 5 件の受入台帳更新を含めれば、少なくとも production、test、既存 ledger の 3 file である。

## 裁定パッケージ候補

- **厳密な receipt schema versioning。** 現コードは v1 を additive/open shape として運用しており今回の版上げは不要と判断できるが、「v1 は exact closed shape」とするなら、既存 v1 receipt が `condition_gates` を持たない時点から別問題になる。今回の局所変更では扱わない。
- **t316 実経路の root-location-only 到達実測。** A-5 からの一般化を閉じるには、変更後 commit を束縛した計算ノード probe が必要。本 wave の実装・静的 test scope 外。

## 総括

2 組目の正例 fixture は production evaluator・完全 evidence・issuer capability を通る本物で、プランの核心は成立する。  
主な欠落は新規 5 nodeid の acceptance duration ledger と、第 3 reason helper の `stock_comparison=False` 明記である。  
交叉負例は admission seam に加え、交叉 family と一致する receipt を渡さなければ probe 述語へ到達しない。  
既存 consumer、policy、hooks、official-perf test に期待値変更は不要で、receipt schema の版上げも現コード上は不要。