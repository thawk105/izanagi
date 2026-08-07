結論は **NO-GO** です。critic の後置順そのものは実装されていますが、例外契約の拡大破壊と、変異事前登録・新設テストの検出力不足があります。以下は静的検査のみで、私は pytest を実走していません。

## real 所見

### R1 — must-fix: pending critic 全体が supervisor 回復境界の外へ出た

`_finish_trial` の `try/except` は `_run_workload` の呼び出しだけを囲み、正常系の helper 呼び出しはその外です（[p3_autonomous_workload_trial.py:1397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1397)、[同:1433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1433)）。

その helper には finalizer だけでなく、以下も含まれます。

- `require_admitted_campaign` と digest 構築（[同:1261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1261)）
- `providers["critic"]` の辞書参照（[同:1291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1291)）

たとえば注入 provider が planner/coder/auditor のみで critic を欠く入力は、旧実装では `_run_workload` 内の `KeyError` として `supervisor-error` partial report へ変換されました。新実装では finalization 後の `KeyError` がそのまま伝播し、formal trial なら outer handler が lifecycle を `indeterminate` にします（[同:2170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:2170)）。

S-01 が要求したのは finalizer 例外だけの非変換です。critic preparation/invocation infrastructure まで非変換にしたのは過剰です。

成果物影響: 同じ入力で `report.status=partial`、`cell.stop_reason=supervisor-error`、lifecycle `partial` だったものが、`report.json` なし・lifecycle `indeterminate` へ変わる。

照準先: admission finalizer だけを既存 `try` の外にし、その後の pending critic infrastructure 例外には従来どおり supervisor-error 回復境界を設ける。

### R2 — must-fix: M5 は kill されない

M5 は仕様自身が「新設 pin なし」と明記しています（[s4-erratum-v3.md:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-07_t244-p3-u8-critic-after-admission/s4-erratum-v3.md:93)）。現行 guard は [p3_autonomous_workload_trial.py:1467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1467) に一意にありますが、通常経路では helper が必ず key を pop するため、guard 削除だけでは既存入力の観測値が変わりません。

代替照準は、実 helper を呼んだ wrapper が消費済み pending を意図的に cell へ戻す fixture です。

- guard あり: report 構築前に指定例外
- guard 削除: completeness は未知の cell key を拒否しないため、private pending が report へ流入して publish される

成果物影響: `cells[*]._pending_critics` と、その中の `raw_variant`・harness outcome が `report.json` に混入し得る。

### R3 — must-fix: M2/M3 は指定 assert ではなく別 gate に殺される

M2 の代入削除では cell が `fixed-generation-budget` のまま、critic event だけ invalid になります。したがって `test_post_admission_invalid_critic_marks_cell_role_invalid` の assert（[test file:2084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2084)）へ到達せず、completeness の「fixed-budget に non-valid role」拒否（[autonomous_trial_completeness.py:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:771)）で赤になります。

M3 の harness 後勝ち mutant も、`converged` cell に invalid critic が残るため、優先順位 assert（[test file:2118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2118)）ではなく stopped-cell の non-valid role 拒否（[completeness:843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:843)）で赤になります。

また M3 は、harness stop の代入が `_run_workload`（[producer:1855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1855)）、critic invalid の代入が別 helper（[同:1303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1303)）に分かれ、変異位置も一意ではありません。

成果物影響: mutation evidence の `kill reason` が cell 値・優先順位 assert を参照する一方、実際は completeness の別 gate を参照し、単一理由性の証拠が偽になる。

照準先: helper を直接呼ぶ小さいテストで、M2 は初期 `fixed-generation-budget`、M3 は初期 `converged` を与え、completeness を介さず最終 `stop_reason` を検査する。

### R4 — must-fix: M4 は v5 後の配置では一意な mutation でない

v5 は二相処理を workload loop 内と fallback loop に分割しましたが、変異表について読み替えたのは M1 だけです（[s4-erratum-v5.md:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-07_t244-p3-u8-critic-after-admission/s4-erratum-v5.md:59)）。

現物には normal helper（[producer:1433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1433)）、fallback helper（[同:1442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1442)）、status（[同:1456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1456)）があります。

- status を normal helper 前へ移せば、対象テストは completeness の status projection で赤になる。
- status を fallback helper 前へ移すだけなら、normal invalid-critic 入力では既に stop reason が確定済みなので、対象テストは緑のまま。

成果物影響: M4 の位置・kill node の参照が一意でなく、事前登録した mutation coverage を成立したものとして記録できない。

照準先: M4 を具体的な AST 位置へ再定義し、status assignment が両 helper call より後にあることを構造的に pin する。

### R5 — must-fix: Layer 3 の実 finalizer と invalid build admission が未検査

順序テストは実 finalizer を完全に monkeypatch しています（[test file:2032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2032)）。docstring は限界を正直に書いていますが、実 `_finalize_build_cell_admission` の本体を削除してもこのテストは緑です。

さらに `test_post_admission_invalid_critic_marks_cell_role_invalid` は `do_build=False`（[同:2077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2077)）で、保持を検査しているのは `not-applicable` sentinel だけです。positive build admission を critic invalid 後に削除・巻き戻す mutant は検出しません。

成果物影響: real finalizer の no-op 化では critic の raw response/journal attempt が Layer 3 確定前に生成され、build-only rollback では positive `admission_decision` が report から消えるが、新設テストは緑になり得る。

照準先: real finalizer を残したまま `layer3_report.render` を fake にし、render 完了→critic の順序を観測する。invalid critic 側にも positive build admission の保持テストを足す。

### R6 — must-fix: multi-generation と direct pin は値を十分固定していない

多世代テストについて、現実装が止まる理由は狙いどおり順序不一致です。

- cap はテスト内で 2 に変更済み（[test file:2191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2191)）
- state-machine 前段は full/valid/continue として通る
- journal は `g1:PCA, g2:PCA, g1:critic, g2:critic`
- report は `g1:PCAcritic, g2:PCAcritic`
- 最初の停止点は `_check_attempt_sequence`（[completeness:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:857)）

したがって cap gate 等による false red ではありません。ただし assertion は generic な `"journal role attempts"` と critic call 数 2 だけです（[test file:2198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2198)）。pending を逆順に処理して `g2 critic → g1 critic` にしても、同じ例外文言・call 数で緑になります。

direct pin も pending の長さしか見ません（[同:2244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2244)）。`_pending_critics == [{}]` や余分な秘密 field を持つ record でも通ります。

成果物影響: `attempts.jsonl` の `(generation, role)` 順、および direct cell の `_pending_critics` key/value 集合が変わっても境界テストが緑になる。

照準先: journal の exact tuple 列、critic payload の generation 列 `[1, 2]`、pending record の exact 5 keys と既知値を検査する。

### R7 — must-fix（仕様または名乗り）: 復元 cell の「順序は壊れない」は誤り

v5 は supervisor-error 復元 cell が最後なので順序は壊れないとします（[s4-erratum-v5.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-07_t244-p3-u8-critic-after-admission/s4-erratum-v5.md:38)）。

しかし現物では先に `supervisor-error` event を append（[producer:1402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1402)）し、その後 fallback helper が pending critic event を append します（[同:1442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1442)）。completeness は terminal supervisor event が `run-finish` の直前であることを要求します（[completeness:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:552)）。

現在の cap=1 では「完了済み pending を持った後の supervisor error」は通常到達しませんが、cap-lift/monkeypatch 経路では実在します。

成果物影響: `supervisor-error → critic → run-finish` の journal は partial report を publish できず、formal lifecycle は partial でなく indeterminate になる。

## M1〜M5 判定

| Mutation | 位置一意性 | 指定 node の赤化理由 | 判定 |
|---|---|---|---|
| M1 | 一意。production critic call も1箇所 | fake finalizer と critic の order assert だけで赤 | **kill 成立** |
| M2 | 代入位置は一意 | cell assert 前に fixed-budget/non-valid completeness が拒否 | **kill するが理由誤記** |
| M3 | 二関数に分離され一意でない | priority assert 前に stopped/non-valid completeness が拒否 | **kill するが理由誤記・照準非一意** |
| M4 | v5 後は normal/fallback のどこより前かが曖昧 | 一解釈では completeness status gate、別解釈では対象 test が緑 | **事前登録不成立** |
| M5 | guard 自体は一意 | pin がなく通常入力では観測差なし | **kill されない** |

## 新設6テストの検出力

1. `test_build_cell_admission_precedes_critic_invocation`  
   M1 は殺す。ただし実 finalizer を bypass するため、Layer 3 実在保証は殺せない。

2. `test_post_admission_invalid_critic_marks_cell_role_invalid`  
   現実装の値は正しい。M2 は別 gate に殺され、positive build admission の保持は未検査。

3. `test_invalid_critic_overrides_harness_terminal_stop`  
   malformed critic に対する優先順位は固定するが、valid critic + terminal stop の正例がない。terminal を常に role-invalid にする過剰拒否 mutant を直接は殺さない。

4. `test_cell_admission_failure_is_not_converted_to_supervisor_error`  
   S-01 の対象 mutant は適切に殺す。fake finalizer が実際に呼ばれた回数を固定していない点だけは nit。

5. `test_multi_generation_deferred_critic_fails_closed`  
   現実装の停止理由は cap gate でなく狙った attempt 順序不一致。ただし exact 順序は未固定。

6. `test_direct_run_workload_defers_critic_to_finish_trial`  
   critic 0 回と role prefix は固定するが、5-field pending contract の内容・exact keys は未固定。

恒真 assert、実装からの期待値導出、時刻等の揮発値焼き込みは見つかりませんでした。

## v4 §3 の既存テスト改変

既存 expectation の変更は、許可された次の2箇所だけです。

- `test_run_workload_accepts_fresh_campaign_state`（現行 [test file:1775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:1775)）
- `test_run_workload_accepts_actual_fresh_campaign_layout`（現行 [同:1845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:1845)）

各1行の全-provider count が、v4 指定どおり planner/coder/auditor 各1回・critic 0回・pending 1件へ置換されています。削除行はこの2行だけで、他の既存期待値反転・緩和・skip・xfail・削除はありません。残りは helper 1個と新設6テストです。

## 禁止変更の確認

以下はすべて現物で不変です。

- `SCHEMA_VERSION = .../v3`、`REPORT_SCHEMA_VERSION = .../v2`、`MAX_APPROVED_GENERATIONS = 1`（[producer:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:143)）
- journal event 集合（[completeness:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:40)）
- `_ROLE_ORDER`（[同:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:52)）
- `_check_attempt_sequence`（[同:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:857)）
- critic payload 外側 key は common + `harness_result` + `critic_digest` のまま（[producer:1278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1278)）
- `autonomous_trial_completeness.py` は未変更
- 新定数・新 journal event なし
- `_run_workload` / `_finish_trial` の引数追加なし

## 所有外 consumer

静的に全走で赤を予測する既存 nodeid はありません。

- `test_claude_transport.py`: public 1世代 role orderは従来どおり P/C/A/critic（[test:1550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_claude_transport.py:1550)）。direct caller は generation 開始前 wall stop なので pending は空で、既存 assert は変わらない（[同:2085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_claude_transport.py:2085)）。
- `test_role_session_isolation.py`: public 1世代または手組み4-role report。`_finish_trial` signature も不変（[test:387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_role_session_isolation.py:387)）。
- `test_trial_registry.py`: report fixture は1世代 P/C/A/critic 順（[test:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_trial_registry.py:268)）。private pending は publish 前に消えるため shape 不変。
- `test_campaign.py`: `run_trial` を差し替えて CLI root だけを見る consumer（[test:4905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_campaign.py:4905)）。
- `test_p3_s4_loop.py`: production `make_critic_digest` call は依然1個で、`reflux` AST 式も一致（[test:1048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_s4_loop.py:1048)）。
- `test_p3_s4_loop_trigger_gating.py`: autonomous 依存は freshness helper のみで不変。
- `test_p3_s4_loop_sort.py`:変更対象 symbol の consumer なし。
- `s8c_preregistration_evidence.py`: cap=1 のため C11 は従来どおり `GENERATION_CAP_NOT_LIFTED` で先に止まる（[source:529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/s8c_preregistration_evidence.py:529)）。ただし将来 cap-lift 時は `_run_workload` 内の feedback consumer を要求するため再設計が必要。
- `trial_registry.py`: final report の workload/campaign/status を消費するだけで、通常1世代 shape は不変（[source:2333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/trial_registry.py:2333)）。R1 の error path は既存テストに pin されていない。

## 完了報告との照合

最終の [s5-impl-v5.md:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s5-impl-v5.md:1) の以下は実装と一致します。

- 5-key pending
- workload ごとの admission→critic
- schema/event/cap/signature/status式不変
- 変更量 `+117/-62` と `+289/-2`
- 新設6 nodeid
- U-8 全体は未完了

不一致・重大な未報告は次です。

- 「復元 cell も後処理し supervisor-error を保持」（[同:4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s5-impl-v5.md:4)）は、critic infrastructure 例外と terminal-event 順序について成立しない。
- consumer 波及報告は R1 の「partial report → reportなし」の契約変更を落としている。
- M2〜M5 の単一理由性・未 kill を報告していない。

## U-8 要求充足

現物の production critic invocation は [p3_autonomous_workload_trial.py:1289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1289) の1箇所だけです。その前に build は real finalizer（[同:1239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1239)）、no-build は `not-applicable` decision を確定します。

- normal cell: admission → pending critic
- harness terminal cell: admission → pending critic
- supervisor-error 復元 cell: admission → pending critic
- direct `_run_workload`: critic を呼ばず pending を返す
- finalizer failure: critic へ到達しない
- planner/coder/auditor invalid: pending がなく critic なし

したがって「8c 非認定 pilot の critic 呼び出しを cell の Layer 3 admission 確定後へ後置する」という限定要求は、現行実装では達成しています。admission 前に critic を呼ぶ分岐は見つかりません。

ledger seal、proof issuance、seal 後の proposal/raw 公開が未実装であり、U-8 全体が未完了という限定も正しいです。

## 疑い・nit

疑いとして残す実装所見はありません。未実走なので動的環境固有の失敗は判断していません。

nit は、finalizer failure test が fake finalizer の call count を固定していない点だけです。外部成果物の観測結果自体は十分固定するため must-fix には含めません。

## 総括

- **(a) NO-GO** — critic の後置自体は達成しているが、pending critic infrastructure 例外が supervisor 回復境界から漏れ、変異事前登録と新設テストにも未 kill・誤帰属・false-green 面がある。
- **(b) must-fix:** R1、R2、R3、R4、R5、R6、R7。
- **(c) 全走で赤くなると予測する nodeid:** なし。これは静的予測であり、私自身は全走していない。
- **(d) 仕様自体の誤り:** v5 が finalizer 非変換と pending critic 非変換を同じ境界へ束ねたこと、M3/M4 を v5 配置へ再登録しなかったこと、M5 に kill node がないこと、復元 cell の terminal-event 順序を「壊れない」としたこと。