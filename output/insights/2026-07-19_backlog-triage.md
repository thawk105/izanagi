# 未消化タスク棚卸し — ユーザー裁定パッケージ

---
authority: none
default_effect: no-state-change
as_of_commit: 80343a2
canonical_state: "docs/worklog.md 末尾 + docs/phase3.md"
---

本文書は裁定資料であり、ユーザーが承認するまで何も発効しない。裁定後の状態反映は
`docs/phase3.md` 見送り台帳と `docs/worklog.md` へ行い、本文書は書き換えない
（凍結スナップショット）。

出自: 標準ループ（codex 敵対相談 3 本 22 所見 → 掃引 6 単位 → 本表）と、敵対レビュー
R1〜R3（計 20 所見、親裁定で全件 real・本版へ反映済み）を経た。相談逐語は
`output/insights/2026-07-19_backlog-triage-consultations.md`、レビュー逐語は R1〜R3 の凍結成果物を正本とする。

## 裁定要求の要約

裁定対象は **59 行**。節別内訳は A 11 / B 6 / C 15 / D 13 / E 7 / F 4 / G 3。AI 推奨別内訳は
昇格候補 10 / 条件付き保留候補 47 / 廃棄候補 0 / 正本の完了記録だけ更新 2。全行の
`ユーザー裁定` は **未裁定** であり、事実状態や AI 推奨は裁定そのものではない。

AI 推奨（非拘束）の選択肢は次の 4 つ。

- **昇格候補**: 現行承認 scope の blocker、または行に定義した trigger が既に真。
- **条件付き保留候補**: 価値は生存しているが独立 action の trigger は現在 false / unknown。基礎不足の
  predicate が true でも既存 live carrier が運ぶ場合は、独立 action predicate を分けて明記する。
- **廃棄候補**: active consumer がなく、superseded / refuted / 重複の一次証拠がある。
- **正本の完了記録だけ更新**: 実体上の完了が確認でき、追加実装でなく正本の terminal 記録だけが残る。

本体は「独立に採否を裁定できる最小単位」を一行とする。横長表で証拠が潰れるのを避けるため、
各行を同じ列名の縦持ちレコードで表示する。`source_occurrences` は掃引間の同一・包含・関連検出を
保存し、同一項目は一行へ統合した。

**キー境界**: `B-xxx` は本監査のローカルキーであり、正式な `T-*` ID はユーザー裁定後の生存項目にのみ
C（backlog-guard-mechanism）で付与する。B→T の対応表は C 実装時に作る。

### 掃引間の明白な矛盾・精密化

- X3-24 は §5-(viii) を未消化と直接分離する一方、X6-96 は §5 追認群を一括して done と要約する。
  個別完了述語を持つ X3-24 を採り、B-005 の不確実性欄に矛盾を保存した。
- X3-69 は「新 workflow ごとの lint 実行」を continued、X6-105 は checker 実装を done とする。
  実装と継続運用は別 child なので、B-043 を部分吸収とした。
- X2-49 は処分記録なしを unresolved とするが、現時点の worktree と directory は不在。B-038 は
  過去処分の裏取り不能と現在の前提消滅を併記する。
- X4 の balanced driver docstring は「既定で write-heavy + balanced」と書くが、実装既定は
  write-heavy のみ。B-011 の反証欄に保存した。
- X6-94 は execution/run-contract 親を広く partial とするが、X3-52 は reps 束縛を done、X3-53 は
  extime 束縛だけを unresolved と直接分離する。B-004 は extime child に限定した。
- X6-15 の useful IPC 分離 done は sweet-spot の spin 希釈を指し、X4 の over-throttle 原因未分離とは
  対象域が異なる。B-012 は矛盾でなく scope 差として保存した。

## 棚卸し表本体

## A. 正しさ・防壁系

### B-001 — EVOLVE hole 内コメントの機械拒否

- **出所逐語 + file:line**: 「hole 内コメント = auditor への injection 経路（real・反証不能・機械 reject 推奨）」
  (`docs/archive/worklog-phase3-0702-0713.md:1905-1907,1975-1976`)；「hole 内コメント (`//`) が
  検疫を素通りし、coder … → auditor への prompt injection 直送経路」「対策推奨度『高』」
  (`output/insights/2026-07-12_strategy-review-headline-axis.md:33,36`)。
- `source_occurrences`: **X1B-51 = X6-41**。
- **事実状態**: **未消化** — `_DIRECTIVE_RE` / `_MARKER_RE` は指令と BEGIN/END だけを拒否し、
  コメント通過を `orchestrator/tests/test_diff_quarantine.py:430-437` が正例として固定する
  (`orchestrator/campaign/diff_quarantine.py:44-53,375-387`)。
- **反証・不確実性**: 一般コメント全拒否は正当な説明コメントも拒むため、拒否対象を hole 内に限定する
  parser 境界が必要。ただし「現在も通る」という核心に反証はない。
- **AI 推奨（非拘束）**: **昇格候補** — 既知の prompt-injection 経路が現に開いており、正しさ防壁の
  trigger は既に真。
- **代替案**: コメントを機械拒否せず、auditor 入力からコメントを構造的に除去し、その除去を positive
  control で固定する。
- **発火条件述語**: `P_comment_injection := hole_comment_is_accepted ∧ auditor_input_preserves_that_comment`。
  観測対象は `diff_quarantine.py` の受理規則、正例テスト、auditor 入力射影；現在 **true**
  （コメント受理を正例固定し、除去契約もない）。
- **反映先**: `docs/phase3.md` の diff-quarantine / 残存リスク節と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-002 — trigger-loop runbook の verify abort>0 確認

- **出所逐語 + file:line**: 「F 段 runbook に abort>0 確認が無い」「持ち越し: … runbook abort>0 2 行」
  (`docs/archive/worklog-phase3-0702-0713.md:1907,1975-1976`)；「runbook §0 に項目 7 … §1(f) に
  verify abort>0 確認の計 2 行追記」
  (`output/insights/2026-07-12_strategy-review-headline-axis.md:34,36`)。
- `source_occurrences`: **X1B-52 = X6-42**。
- **事実状態**: **未消化** — 現行 runbook の実走前 gate は 6 項目で、§1(f) に verify abort>0 がない
  (`docs/phase3-s8a-trigger-runbook.md:14-31,78-92`)。
- **反証・不確実性**: `docs/phase3.md:184,413` の一般 S2/sort 規定は存在するが、この runbook の
  空振り認証を閉じる完了述語とは別。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 防壁価値は生存するが、完了済み 8a の runbook を
  現在再利用する active consumer は確認できない。
- **代替案**: runbook 固有追記でなく、全 verify campaign 共通の abort>0 preflight へ昇格する。
- **発火条件述語**: `P_runbook := trigger_loop_runbook_selected_for_new_run ∧ abort_positive_gate_absent`。
  観測対象は実走事前登録と runbook gate；現在 **false**；次の trigger-loop 再利用承認時に再評価。
- **真時 action**: runbook の preflight と verify 後確認へ abort>0 gate を各 1 行追加し、abort=0 の
  negative control が実際に失敗することを固定する。
- **失効条件**: trigger-loop runbook を恒久廃止する、または同等の共通 abort>0 preflight が全 consumer を
  機械的に覆う。
- **反映先**: 保留なら `docs/phase3.md` 見送り台帳、昇格なら同 runbook の対応節と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-003 — oracle report の bench-failed abort reason 検査

- **出所逐語 + file:line**: 「oracle report の bench-failed 分岐は abort reason 非検査」
  (`docs/worklog.md:184-185`)。
- `source_occurrences`: **X3-45**。
- **事実状態**: **未消化** — `orchestrator/campaign/s8b_oracle_report.py:449-453` は abort 件数と
  verify pass を見るが reason を検査しない。binary-mismatch / verify-inconclusive は
  `:458-475` で reason を検査する。
- **反証・不確実性**: 正規 driver の `_outcome_for` が reason を制限するため正規経路だけなら間接防壁はある。
  ただし report は独立 artifact verifier であり、独立検証面の欠落は残る。
- **AI 推奨（非拘束）**: **昇格候補** — 現行 s8b oracle / launch-certificate scope の artifact verifier
  に非対称な検査穴があり、blocker 条件が真。
- **代替案**: report 単体で reason を閉表検査せず、driver が署名した正規化 outcome object のみを受理する。
- **発火条件述語**: `P_bench_reason := bench_failed_report_is_accepted_without_closed_abort_reason_check`。
  観測対象は `s8b_oracle_report.py` の `bench-failed` 分岐と binary-mismatch / verify-inconclusive 分岐；
  現在 **true**（前者だけ reason 非検査）。
- **反映先**: `docs/phase3.md` の s8b v2 verifier / oracle 完了条件と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-004 — extime の run-contract 束縛

- **出所逐語 + file:line**: 「reps・extime の束縛 = experiment_numbers 裁定後」
  (`docs/worklog.md:488-490`)。
- `source_occurrences`: **X3-53**；**X6-94 の未完 child**（reps は X3-52 で完了）。
- **事実状態**: **未消化** — `orchestrator/campaign/s8b_floor_contract.py:185` と
  `s8b_oracle_manifest.py:354-361` は extime を任意の正整数として受理し、裁定値へ束縛しない。
- **反証・不確実性**: protocol bytes の実凍結が結果的に値を固定する余地はあるが、validator 自身の
  完了述語を満たさない。X6-94 の「reps も未完」は X3-52 の直接証拠と矛盾するため採らない。
- **AI 推奨（非拘束）**: **昇格候補** — protocol JSON 凍結と実 oracle が現行承認 scope にあり、
  実験数値の未束縛は launch certificate の blocker。
- **代替案**: code 定数へ直接 pin せず、承認 freeze の extime と manifest の一致を validator で検査する。
- **発火条件述語**: `P_extime := approved_protocol_freeze_is_live ∧ validator_accepts_extime_other_than_frozen_value`。
  観測対象は承認 protocol/freeze と `s8b_floor_contract.py` / `s8b_oracle_manifest.py` の validator；
  現在 **true**（任意の正整数を受理）。
- **反映先**: `docs/phase3.md` の protocol JSON / run-contract 完了条件と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-005 — §5-(viii) 残存限界の最終承認

- **出所逐語 + file:line**: 「**(viii) 限界受け入れは floor 実測直前に持ち越し**」
  (`docs/worklog.md:646`)。
- `source_occurrences`: **X3-24**；X6-96 は §5 追認群を一括 done とする競合要約。
- **事実状態**: **未消化** — 後続 `docs/worklog.md:677,736-755` と `docs/phase3.md:66-70` に
  最終承認 step がない。certificate 前削除、ignored 領域、内容 TOCTOU 等の限界自体は既存 insight に残る。
- **反証・不確実性**: floor 実測列を暗黙 carrier と読む余地はある。X6-96 の一括 done と明白に衝突するが、
  個別 child と完了述語を直接追った X3-24 を優先した。
- **AI 推奨（非拘束）**: **昇格候補** — floor 実測は現行 scope の直近工程で、承認を黙って飛ばす条件が
  既に成立しうる。
- **代替案**: 個別承認を追加せず、既承認 §5 のどの条項が (viii) を包含したかをユーザーが明示追認する。
- **発火条件述語**: `P_viii := floor_measurement_is_live_next_stage ∧ explicit_section5_viii_acceptance_absent`。
  観測対象は `docs/phase3.md:66-70` の live floor 工程、§5 裁定記録、worklog の持ち越し；現在 **true**。
- **反映先**: `docs/phase3.md` の floor 実測直前 gate と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-006 — critic digest への unstable / CV 伝搬

- **出所逐語 + file:line**: 「digest への unstable 伝搬」
  (`docs/archive/worklog-phase3-0702-0713.md:132-134`)。
- `source_occurrences`: **X1A-52**。
- **事実状態**: **未消化** — `GenomeLI` は unstable / CV を持たず、`load_workload()` は
  leading indicators のみを射影する (`orchestrator/critic/digest.py:38-44,192-217`)。
- **反証・不確実性**: downstream critic が現行 headline の採否に使われる時だけ情報欠落が実害化する。
  元約束の具体的 consumer は現在明示されない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 測定不安定性を次の探索判断へ返す価値は生存するが、
  critic loop の active 再走は未確認。
- **代替案**: digest schema を増やさず、unstable を fitness / admission で terminal 扱いし critic へ渡さない。
- **発火条件述語**: `P_digest := critic_loop_approved ∧ workload_stability_affects_next_proposal ∧
  digest_lacks_stability_fields`。観測対象は loop 事前登録と digest schema；現在 **false**；次 loop 凍結時。
- **真時 action**: unstable/CV を digest schema と critic 入力へ対称に配線し、欠落・unstable の fixture で
  次提案への伝搬を検証する。
- **失効条件**: critic loop を廃止する、または unstable workload を digest 到達前に terminal reject する
  契約が全経路を覆う。
- **反映先**: `docs/phase3.md` 見送り台帳または critic loop 完了条件と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-007 — Gate1 √2 閾値意味論

- **出所逐語 + file:line**: 「Gate1 √2 の閾値意味論（Phase 3 設計判断）」
  (`docs/archive/worklog-phase3-0702-0713.md:132-134`)。
- `source_occurrences`: **X1A-53**（X1A-41 は docstring 化だけを done と判定）。
- **事実状態**: **未消化** — `compare()` は `abs(rel) <= noise_cv` のままで、docstring も設計判断を
  保留とする (`orchestrator/calibrator/stability.py:233-243,275`)。
- **反証・不確実性**: cf62e81 の注記を判断完了と読む余地はあるが、閾値採否・棄却の決定証拠はない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 候補比較の統計意味論には価値があるが、当該 Gate1 を
  load-bearing にする新比較は未確認。
- **代替案**: √2 補正を入れず、現行閾値を保守的設計として明示裁定する。
- **発火条件述語**: `P_gate1 := gate1_compare_used_for_certifying_claim ∧ sqrt2_semantics_unratified`。
  観測対象は比較 protocol と `stability.py`；現在 **false**；次の比較 protocol 凍結時。
- **真時 action**: √2 補正を採用するか現閾値を保守的定数として維持するかを裁定し、選択した意味論の
  境界値テストと protocol 記録を追加する。
- **失効条件**: Gate1 compare を certification claim から除外する、または同じ意味論を持つ後継 gate が
  本行を supersede する。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は calibration / comparison 契約節、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-008 — fresh background session での guard_agent 再検証

- **出所逐語 + file:line**: 「次回新規 bg セッションで guard_agent 再検証」
  (`docs/worklog.md:576-577,612`)。
- `source_occurrences`: **X3-61**。
- **事実状態**: **未消化** — version drift と background surface の配送欠落が未分離
  (`hooks/README.md:142-148`)。
- **反証・不確実性**: 2.1.212 headless 対照では拒否が発火しており、全 surface の一般故障ではない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 再検証価値は高いが、predicate は新規 background
  job 型 session の発生待ち。
- **代替案**: background surface を使わず foreground 運用に固定し、再検証自体を不要化する。
- **発火条件述語**: `P_guard_retest := new_background_job_session_started`。観測対象は daemon version、
  `Agent` PreToolUse 配送、model 無し spawn の拒否；現在 **false**；次の該当 session 冒頭で再評価。
- **真時 action**: version を記録した fresh background job session で model 欠落 Agent を 1 回 probe し、
  hook 配送・拒否・spawn 有無を対照付きで記録する。
- **失効条件**: background job surface を利用禁止または廃止し、model 欠落 Agent が構造的に到達不能になる。
- **反映先**: `docs/phase3.md` 見送り台帳、結果は `hooks/README.md` の live 発火限界と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-009 — guard_agent 防衛候補の裁定

- **出所逐語 + file:line**: 「guard_agent 防衛候補の裁定」 (`docs/worklog.md:572-573`)。
- `source_occurrences`: **X3-62**（B-008 から split）。
- **事実状態**: **未消化** — Agent 全拒否、子モデル強制、foreground 化の候補だけが
  `hooks/README.md:149-152` に残り、裁定記録がない。
- **反証・不確実性**: B-008 が拒否成功なら version drift であり、追加防衛は不要になる。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 価値は B-008 の再度素通り時にだけ発生する。
- **代替案**: 機械防衛を増やさず、surface 利用禁止を運用契約にする。
- **発火条件述語**: `P_guard_defense := P_guard_retest ∧ model_omitted_agent_spawn_allowed`。
  観測対象は B-008 の対照結果；現在 **false**；B-008 完了時に再評価。
- **真時 action**: Agent 全拒否・子モデル強制・foreground 固定の保証差と副作用を提示し、ユーザーが
  選んだ防衛を E2E negative control 付きで実装する。
- **失効条件**: B-008 が拒否成功を示す、または当該 background surface を恒久利用禁止にする。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は `hooks/README.md` と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-010 — fairness allowlist 反転

- **出所逐語 + file:line**: 「allowlist 字句検査への反転は中推奨」「auditor ギャラリーへの
  『間接 thid_（アドレス系）』型追記」
  (`output/insights/2026-07-12_strategy-review-headline-axis.md:32,36`)。
- `source_occurrences`: **X6-43 の split child 1/2**；X1A-91 は同じ fairness 機械観測ギャップの関連検出
  (`docs/archive/worklog-phase3-0702-0713.md:1130-1136,1154-1157`)。
- **split 関係**: 元複合 B-010 を安定キー B-010（本 child）と B-058（間接 `thid_` gallery）へ分割。
- **事実状態**: **未消化** — D42 条件 4（auditor 型13〜15）は承認・実装済み
  (`docs/decisions.md:1352`; `.claude/agents/auditor.md:58`)。その後続提案である fairness 字句検査の
  allowlist 反転だけが未裁定・未実装である。
- **反証・不確実性**: proposed_tests 一般には phase carrier があるが、allowlist 反転を直接包含するか不明。
- **AI 推奨（非拘束）**: **条件付き保留候補** — sort-strategy が headline 候補でない現状では trigger 偽。
- **代替案**: 字句 allowlist を増やさず、per-key / per-thread commit 分布の動的 fairness gate だけを置く。
- **発火条件述語**: `P_fair_allowlist := sort_strategy_variant_is_headline_candidate ∧
  fairness_lexical_policy_is_not_allowlist`。観測対象は凍結候補集合と auditor fairness 字句規則；現在 **false**；
  headline 候補凍結時。
- **真時 action**: fairness 字句規則を exact allowlist へ反転し、未知語・既知良性語・既知迂回語の
  positive/negative control を追加する。
- **失効条件**: sort-strategy を候補空間から恒久除外する、または字句検査を不要にする同等以上の動的
  fairness gate が全候補を覆う。
- **反映先**: `docs/phase3.md` の fairness 残存リスク / 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-058 — 間接 thid_ gallery 追記

- **出所逐語 + file:line**: 「allowlist 字句検査への反転は中推奨」「auditor ギャラリーへの
  『間接 thid_（アドレス系）』型追記」
  (`output/insights/2026-07-12_strategy-review-headline-axis.md:32,36`)。
- `source_occurrences`: **X6-43 の split child 2/2**；X1A-91 は関連検出。
- **split_from**: **B-010（元複合行）**。既存 B キーを変えず、分離 child を末尾キー B-058 とした。
- **事実状態**: **未消化** — D42 条件 4（auditor 型13〜15）は承認・実装済みだが、後続提案の
  間接 `thid_`（アドレス系）gallery 追記は未裁定・未実装。
- **反証・不確実性**: 現 gallery の既存型が一部を間接的に捕える可能性はあるが、当該型の named fixture と
  回帰証拠はない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — sort-strategy が headline 候補でない現状では trigger 偽。
- **代替案**: gallery を増やさず、per-key / per-thread commit 分布の動的 fairness gate で検出する。
- **発火条件述語**: `P_indirect_thid_gallery := sort_strategy_variant_is_headline_candidate ∧
  indirect_address_based_thid_fixture_absent`。観測対象は凍結候補集合、auditor gallery と回帰 fixture；
  現在 **false**；headline 候補凍結時。
- **真時 action**: 間接 `thid_`（アドレス系）の最小 adversarial fixture を gallery へ追加し、現 auditor が
  その型を実際に拒否する回帰を固定する。
- **失効条件**: sort-strategy を恒久除外する、または同じ間接型を識別する別の named regression が本行を
  明示 supersede する。
- **反映先**: `docs/phase3.md` の fairness 残存リスク / 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

## B. 見送り台帳 6 行

### B-011 — balanced での backoff profile 対照

- **出所逐語 + file:line**: 「balanced での backoff profile 対照 … write-heavy の [P0] は閉じたが
  balanced の対照 profile は未取得」 (`docs/phase3.md:391`)。
- `source_occurrences`: **X3-71**；**X4 §1**。
- **事実状態**: **未消化** — balanced / rr50 / 0,2,5,10,25,50,100µs の driver はあるが committed
  JSON/MD はなく、driver は歴史 pin `dff0f1e` を参照し現 pin は `d706650`
  (`orchestrator/campaign/backoff_profile.py:40,46,49,173,224`; `pin.py:26`; `p2_2.py:36`)。
- **反証・不確実性**: docstring `backoff_profile.py:20` は既定で balanced も走ると書くが、実装既定
  `:224` は write-heavy のみで明白に不一致。off-repo 実走は不明だが committed 成果物条件には影響しない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 現行 Fig.2 の機序 profile は write-heavy のみで trigger 偽。
- **代替案**: balanced の一般化主張を行わず、write-heavy 限定を明記して台帳行を廃棄裁定する。
- **発火条件述語**: `P_bal := ("balanced" ∈ frozen_mechanism_profile_workloads) ∧
  (qualifying_rr50_artifact = absent)`。観測対象は凍結図・レポートと `output/env/*/profile/`；現在 **false**；
  backoff 機序図または「+38%/+11% 両方」の説明凍結直前。
- **真時 action**: 現 pin へ更新した driver で balanced/rr50/全 7 点を実走し、下記完了証拠を持つ
  committed JSON/MD を生成する。
- **失効条件**: frozen mechanism claim を write-heavy 限定に確定し、balanced への一般化を明示的に捨てる。
- **完了証拠**: 現 pin、balanced、rr50、全 7 点、env/thread/records/workload/pin/binary identity、TRACE=0、
  `BACKOFF_NOINLINE` inert 性を直接束縛した committed JSON/MD。
- **反映先**: `docs/phase3.md` 見送り台帳の balanced 行と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-012 — over-throttle 有用 IPC 低下の機序分離

- **出所逐語 + file:line**: 「over-throttle 有用 IPC 低下の機序分離 … MLP 低下 vs cache 余熱の
  どちらかは未分離」 (`docs/phase3.md:392`)。
- `source_occurrences`: **X3-72**；**X4 §2**；X6-15 は sweet-spot の別 scope。
- **事実状態**: **部分吸収** — sweet-spot 0–10µs の total IPC 低下は spin 希釈、有用 IPC はほぼ一定。
  25–100µs の有用 IPC 低下は観測済みだが MLP / cache 余熱を識別していない
  (`output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:172,184,188`)。
- **反証・不確実性**: 効果の存在は反証されないが、単一 48-thread 断面と event multiplex のため幅は soft。
  X6-15 の done は sweet-spot だけであり本行を完了させない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 現行文書は原因を断定せず、因果帰属 consumer がない。
- **代替案**: 原因を「未分離」と固定し、追加計測を行わず廃棄裁定する。
- **発火条件述語**: `P_over := active_report_or_consumer emits causal_attribution ∈ {MLP,
  cache-warmth}`。観測対象は層3機序仮説、backoff 図・論文 prose、critic/selector 入力；現在 **false**；
  mechanism v3 または出版用因果説明の凍結時。
- **真時 action**: MLP と cache-warmth の反対予測を事前登録し、warm/cold factorial と必要な perf event を
  同一 pin/env で測って因果帰属を判定する。
- **失効条件**: active report/consumer が原因を「未分離」と明示して因果帰属を行わない、または
  over-throttle claim 自体を除外する。
- **完了証拠**: MLP / cache の反対予測、outstanding-miss・L3/memory-stall・LLC loads/misses・useful MPKI、
  warm/cold factorial、同一 pin/env、TRACE=0、ランダム順・反復・事前固定判定を持つ committed raw/summary。
- **反映先**: `docs/phase3.md` 見送り台帳の over-throttle 行と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-013 — mocc trace-hook / verifier 第2 protocol

- **出所逐語 + file:line**: 「mocc trace-hook … visible reads の trace 検証 + verifier 2nd エンジン化。
  S1 発火時に吸収するのが自然」 (`docs/phase3.md:393`)。
- `source_occurrences`: **X3-73**；**X4 §3**。
- **事実状態**: **未消化** — MOCC source に trace hook がなく、探索空間も Silo のみ
  (`external/ccbench/cc/mocc/transaction.cc:1,1074`; `orchestrator/campaign/genome.py:87`)。
- **反証・不確実性**: universal `CCBENCH_TRACE` 定義はあるが、MOCC source hook がなければ出力しない。
  「S1 発火時」は一次起源でなく後続 phase 分類による発火条件の追加。
- **AI 推奨（非拘束）**: **条件付き保留候補** — cross-protocol / visible-invisible 比較は現在未承認。
- **代替案**: verifier 第2 protocol を MOCC でなく、hook 実装が小さい別 protocol で実証する。
- **発火条件述語**: `P_S1 := old_headline2_revived ∨ phase7_cross_protocol_started`；
  `P_mocc := (P_S1 ∧ "mocc" ∈ frozen_protocol_set) ∨
  visible_invisible_correctness_ablation_approved`。観測対象は承認 protocol 集合、事前登録、`SPACES`；
  現在はいずれも **false**；protocol 集合凍結時。
- **真時 action**: MOCC の visible/invisible read path へ trace hook を配線し、第2 verifier protocol を
  下記 integrity/TRACE 契約まで実証する。
- **失効条件**: MOCC を frozen protocol 集合から恒久除外し、visible/invisible correctness ablation も
  不採用と裁定する。
- **完了証拠**: visible/invisible read path 被覆、commit 数一致、orphan/duplicate/missing txid=0、実 MOCC trace
  certified、TRACE=0 symbol=0 を pin/workload/diff/binary hash とともに committed 化。
- **反映先**: `docs/phase3.md` 見送り台帳の mocc 行と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-014 — ermia cross-check の再定義

- **出所逐語 + file:line**: 「ermia cross-check … si 赤 / ermia 緑の同一エンジン ablation」
  (`docs/phase3.md:394`)。
- `source_occurrences`: **X3-74**；**X4 §4**。
- **事実状態**: **前提消滅/要再定義** — 旧前提の shifted `ssn_commit()` は実在するが YCSB live path は
  `commit()` → `ssn_parallel_commit()` を通り、version へ未 shift の cstamp を保存する
  (`external/ccbench/include/ycsb.hh:161`; `ermia/transaction.cc:503,553,594,602,751,765,905`)。
- **反証・不確実性**: 外部 consumer が `ssn_commit()` を直接呼ぶ場合は別だが、現 CCBench YCSB の
  call path ではない。台帳の「S1 発火時」は原出所逐語でなく後続分類。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 旧仕様のままは実行不能だが、SI/ERMIA cross-check の
  研究価値は protocol 集合に両者が入る場合だけ生存。
- **代替案**: ERMIA を候補から外し、reachable call graph が既知の protocol へ置換する。
- **発火条件述語**: `P_ermia := {"si","ermia"} ⊆ frozen_crosscheck_protocols`。観測対象は
  cross-protocol 事前登録；現在 **false**；旧 headline 2 復活または段7 protocol 集合凍結時。
- **真時 action**: 現 pin の reachable call graph から ERMIA decoder/spec を再定義し、SI 赤 / ERMIA 緑の
  同一 workload cross-check を下記完了証拠まで実行する。
- **失効条件**: SI または ERMIA の一方を frozen cross-check protocol 集合から外す、または
  cross-protocol cross-check 自体を廃棄裁定する。
- **完了証拠**: reachable helper call graph、txid/cstamp/worker、initial/inflight/committed 遷移、TID flag と
  Version cstamp の別 decoder、全 read/write/delete 規則、version ID 一意性を現 pin に束縛し、同一 workload で
  SI 赤 / ERMIA 緑、commit 数一致、integrity 0、TRACE=0 symbol=0 を示す committed 設計・成果物。
- **反映先**: `docs/phase3.md` 見送り台帳の ermia 行を「前提消滅・要再定義」へ更新し、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-015 — calibration 下限 K 感度

- **出所逐語 + file:line**: 「(任意) thread 数を変えた再 calibration / 下限基準 K の感度。」
  (`docs/archive/worklog-phase1-2.md:226`)；現台帳複合行 (`docs/phase3.md:395`)。
- `source_occurrences`: **X3-75**；**X1B-12 の split child**；**X4 §5a**。
- **split 関係**: 原文の slash 区切り複合項目を B-015（下限基準 K）と B-016（thread 数変更）へ分割した
  child 1/2。両 child に原文逐語を保存する。
- **事実状態**: **未消化** — 実装・成果物は K=4 単値で、CLI に K sweep がない
  (`orchestrator/calibrator/analyze.py:19`; `orchestrator/calibrator/cli.py:100`)。
- **反証・不確実性**: 既存系列から一部 K を post-hoc 再計算できるが、感度表はない。Pegasus の選定 N は
  1M、`lower_bound_selected=true`、`l3_multiple=4.0` である。
- **AI 推奨（非拘束）**: **昇格候補** — protocol 凍結が目前で K=4 の N が claim に入り、trigger は真。
- **代替案**: K=4 を設計定数として明示承認し、感度主張を行わない。
- **発火条件述語**: `P_K := approved_protocol_or_freeze_references_N(lower_bound_selected=true,
  l3_multiple=4.0) ∧ qualifying_K_sensitivity_table_absent`。観測対象は Pegasus
  `calibration-753f535a8d024727.json:1603`、承認済み protocol/freeze と K 感度表；現在 **true**
  （`docs/worklog.md:725`、感度表 absent）。
- **完了証拠**: 固定 env/pin/protocol/workload/thread、事前登録 K 集合ごとの採用 N、LLC miss、maxrss/L3、
  下限充足、結論変化を持つ committed JSON/MD。端点張り付き時は sweep 範囲を拡張。
- **反映先**: `docs/phase3.md` 見送り台帳の calibration 複合行を本 child へ分割し、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-016 — thread 数変更時の再 calibration

- **出所逐語 + file:line**: 「(任意) thread 数を変えた再 calibration / 下限基準 K の感度。」
  (`docs/archive/worklog-phase1-2.md:226`)；現台帳複合行 (`docs/phase3.md:395`)。
- `source_occurrences`: **X3-76**；**X1B-12 の split child**；**X4 §5b**。
- **split 関係**: 原文の slash 区切り複合項目を B-015（下限基準 K）と B-016（thread 数変更）へ分割した
  child 2/2。両 child に原文逐語を保存する。
- **事実状態**: **部分吸収** — Pegasus の 48-thread calibration は bootstrap で、
  `scale_sensitivity=not-measured`、between-run floor 未取得のため、下記 `qualifying_calibration` を満たさない
  (`output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1577,1636`)。
- **反証・不確実性**: between-run floor 取得は `docs/phase3.md:66-70` の floor 実測工程が live carrier として
  既に運んでいる。したがって不足は real だが、別 backlog action を今すぐ重複起票する根拠にはしない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — `P_thread(48)` は真だが既存 live carrier の完了待ち。
  本行の裁定は **floor 実測完了後に再評価**する。
- **代替案**: 性能比較 thread を 48 に固定し、変更を禁止する契約へ置換する。
- **発火条件述語**: `P_thread(T) := T ∈ approved_performance_threads ∧
  qualifying_calibration(env,pin,protocol,workload,T) = absent`。観測対象は `PerfConfig.threads` と committed
  calibration/floor；T=48 は現在 **true**（bootstrap のみ、between-run floor absent）。別行動の述語
  `P_thread_separate := P_thread(48) ∧ live_floor_carrier_absent` は現在 **false**；floor 実測完了時に再評価。
- **真時 action**: floor 実測 carrier 完了後も `P_thread(48)` が真なら、48-thread の records sweep・採用 N・
  within/between floor を満たす再 calibration を独立実行する。
- **失効条件**: live floor carrier が下記 `qualifying_calibration` を満たす成果物を生成する、または
  48-thread を approved performance thread 集合から外す。
- **完了証拠**: 各 live T の records sweep、採用 N、LLC miss/maxrss、within/between floor、thread/NUMA binding、
  TRACE=0 を含む `calibration_t<T>_*` JSON/MD。scale sensitivity 単点は数えない。
- **反映先**: `docs/phase3.md` 見送り台帳の calibration 複合行を本 child へ分割し、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

## C. 研究・計測系

### B-017 — Threats to Validity の集約

- **出所逐語 + file:line**: 「外的妥当性 (Threats to Validity) の集約が無い」
  (`docs/archive/worklog-phase3-0702-0713.md:241-242,285-286,349-350,407-408,524-527`)。
- `source_occurrences`: **X1A-63**。
- **事実状態**: **未消化** — 限界記述は paper-story、phase3-main-experiment、監査 JSON に散在するが、
  要求された集約成果物と完了 commit はない。
- **反証・不確実性**: 分散記述を十分とみなす選択肢はあるが、一次要求は集約であり直接完了証拠ではない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 外的妥当性の価値は生存するが、論文・対外 report の
  claim set 凍結はまだ確認されない。
- **代替案**: 専用文書を作らず、既存 paper-story の限界節を唯一の索引として全記述へリンクする。
- **発火条件述語**: `P_ttv := external_claim_set_about_to_be_frozen ∧ consolidated_threats_index_absent`。
  観測対象は論文 / 対外 report の claim set と限界索引；現在 **false**；最初の外部共有・投稿用凍結時。
- **真時 action**: 散在する限界を claim ごとの根拠ポインタ付き索引へ集約し、claim set と一緒に凍結する。
- **失効条件**: 対外 claim を行わないと裁定する、または既存 paper-story 限界節を唯一の十分な索引として承認する。
- **反映先**: `docs/phase3.md` 見送り台帳、昇格時は paper-story の限界節、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-018 — backoff +38%/+11% の別 boot 再現

- **出所逐語 + file:line**: 「+38%/+11% の別 boot 再現」
  (`docs/archive/worklog-phase3-0702-0713.md:524-525`)；「残: 別 boot」
  (`output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:78-80`)。
- `source_occurrences`: **X1A-68 = X6-13**。
- **事実状態**: **未消化** — `orchestrator/campaign/backoff_repro.py:12` は「別 boot ではない」と明記し、
  同 headline の別 boot 成果物はない。
- **反証・不確実性**: 同一 boot 内の cross-run 再現は存在するが、別 boot という完了述語を満たさない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 出版用再現性補強の価値はあるが、当該 headline を外部主張へ
  採用する trigger は未確認。
- **代替案**: 主張を「同一 boot / 当該環境」に限定し、別 boot 一般化を明示的に捨てる。
- **発火条件述語**: `P_boot := backoff_38_11_claim_selected_for_external_report ∧
  qualifying_separate_boot_artifact_absent`。観測対象は claim set と boot-id 付き成果物；現在 **false**；
  claim 凍結直前。
- **真時 action**: 同一 pin/protocol の別 boot で事前登録した反復を実行し、boot identity 付き成果物と
  +38%/+11% の再現判定を commit する。
- **失効条件**: claim を同一 boot / 当該環境限定に固定する、または当該 headline を外部 report から外す。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は backoff case-study の再現性節、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-019 — critic 軸提案の再現率測定

- **出所逐語 + file:line**: 「critic 軸提案の再現率測定 (replay、新規計測ゼロ)」
  (`docs/archive/worklog-phase3-0702-0713.md:524-525`)。
- `source_occurrences`: **X1A-69**。
- **事実状態**: **未消化** — 同一入力への複数独立呼びと再現率 report がなく、単発観測だけが散在する。
- **反証・不確実性**: replay は性能計測ゼロでも model nondeterminism と model/version drift の影響を受ける。
- **AI 推奨（非拘束）**: **条件付き保留候補** — critic の再現性を主張・利用する active consumer が未確認。
- **代替案**: 再現率を測らず、全提案を exploratory と表示して人間 gate を維持する。
- **発火条件述語**: `P_critic_repro := critic_proposal_reproducibility_used_as_claim_or_gate ∧
  replay_report_absent`。観測対象は凍結入力、model/version、独立出力集合；現在 **false**；critic 再利用設計時。
- **真時 action**: 同一凍結入力を独立 replay し、model/version と軸一致規則を固定した再現率 report を作る。
- **失効条件**: critic 出力を exploratory のみに限定し、再現性を claim・自動 gate のどちらにも使わない。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は critic 評価契約、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-020 — backoff 再現の rounds≥3

- **出所逐語 + file:line**: 「rounds≥3」
  (`output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:78-80`)。
- `source_occurrences`: **X6-14**。
- **事実状態**: **未消化** — `orchestrator/calibrator/stability.py:251-252` に将来必要と残るだけで、
  対応する実測成果物がない。
- **反証・不確実性**: rounds の定義と別 boot の独立性は別問題であり、B-018 を完了しても本行は自動完了しない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 再現性 claim を強める場合だけ価値が発火する。
- **代替案**: 現行反復数の範囲に主張を限定し、rounds≥3 を要求しない。
- **発火条件述語**: `P_round3 := cross_round_reproducibility_claim_selected ∧ qualifying_rounds < 3`。
  観測対象は事前登録 round 数と boot/run identity；現在 **false**；再現性 protocol 凍結時。
- **真時 action**: round 独立性と boot/run identity を事前登録し、qualifying round を 3 以上まで実測する。
- **失効条件**: cross-round 再現性を claim しない、または現行反復範囲だけへ主張を明示限定する。
- **反映先**: `docs/phase3.md` 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-021 — stock 第2・3位 base 上の fix5/fix10 一般性

- **出所逐語 + file:line**: 「stock 第2・3位 base 上でも fix5/fix10 が no-backoff を超えるか」
  (`output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:89`)。
- `source_occurrences`: **X6-18**（backoff 残件 P1）。
- **事実状態**: **未消化** — base 一般性専用 driver/report と裁定記録がない。
- **反証・不確実性**: 元 base 上の改善は real でも、別 base への移植性を保証しない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — base 一般性を外部主張に含める trigger は現在偽。
- **代替案**: 主張を単一 stock base に限定する。
- **発火条件述語**: `P_base := claim_requires_backoff_improvement_across_stock_bases ∧
  second_third_base_artifacts_absent`。観測対象は claim scope と base identity；現在 **false**；主張凍結時。
- **真時 action**: stock 第2・3位 base を事前固定し、fix5/fix10 と no-backoff の同条件比較成果物を作る。
- **失効条件**: claim を単一 stock base に限定する、または base 一般性の主張を削除する。
- **反映先**: `docs/phase3.md` 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-022 — backoff 動作点 thread/skew/records 拡張

- **出所逐語 + file:line**: 「動作点 (thread/skew/records) を広げて述語付き主張へ」
  (`output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:92`)。
- `source_occurrences`: **X6-19**（backoff 残件 P2-1）。
- **事実状態**: **未消化** — 後続 S1/8a/8b は別比較契約で、backoff の効く範囲を直接満たす成果物ではない。
- **反証・不確実性**: 類似する複数動作点実験はあるため、完全な「未計測」ではなく完了述語の不一致。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 単一点限定を超える主張を採る場合のみ必要。
- **代替案**: thread/skew/records を逐語で scope 限定し、一般化を行わない。
- **発火条件述語**: `P_operating := backoff_claim_quantifies_operating_region ∧
  registered_region_sweep_absent`。観測対象は claim predicate と sweep grid；現在 **false**；claim 凍結時。
- **真時 action**: thread/skew/records の範囲と判定述語を事前登録し、registered grid を同一契約で sweep する。
- **失効条件**: claim を既存の単一点へ逐語限定し、動作領域を定量化しない。
- **反映先**: `docs/phase3.md` 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-023 — backoff ピーク位置 fix2/3/5/7 reps≥15

- **出所逐語 + file:line**: 「ピーク位置確定 (fix2/3/5/7 を reps≥15)」
  (`output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:92-93`)。
- `source_occurrences`: **X6-20**（backoff 残件 P2-2）。
- **事実状態**: **未消化** — 該当 variant × reps の成果物・commit がなく、後続 S1 は異なる比較契約。
- **反証・不確実性**: coarse sweep からピーク候補は見えるが、指定反復数による確定ではない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 正確なピーク位置を claim に使う場合だけ必要。
- **代替案**: sweet-spot を区間で報告し、単一ピークを確定しない。
- **発火条件述語**: `P_peak := claim_names_backoff_peak ∧ qualifying_fix2_3_5_7_reps15_absent`。
  観測対象は claim と committed run matrix；現在 **false**；図表・prose 凍結時。
- **真時 action**: fix2/3/5/7 を各 reps≥15 で測り、事前固定した比較規則でピーク位置を確定する。
- **失効条件**: sweet-spot を区間でのみ報告し、単一ピークを claim しない。
- **反映先**: `docs/phase3.md` 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-024 — 待ち方と待ち量の直交化（SMT 分離）

- **出所逐語 + file:line**: 「待ち方 vs 待ち量の直交化 (physical-core ピンで SMT 副作用分離)」
  (`output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:93`)。
- `source_occurrences`: **X6-21**（backoff 残件 P2-3）。
- **事実状態**: **未消化** — pinning は存在するが、待ち方/量 × SMT の直交 ablation はない。
- **反証・不確実性**: physical-core pin だけでは待ち方と量の因果分離にならない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — SMT を機序説明へ使う consumer が現在ない。
- **代替案**: SMT 副作用を未分離の限界として明記する。
- **発火条件述語**: `P_smt := active_claim_attributes_effect_to_wait_shape_or_amount ∧
  orthogonal_smt_ablation_absent`。観測対象は機序 prose と pinning/ablation matrix；現在 **false**；因果説明凍結時。
- **真時 action**: wait shape × wait amount × SMT/pinning の直交 ablation を事前登録し、同一環境で実測する。
- **失効条件**: SMT 影響を未分離の限界として固定し、wait shape/amount への因果帰属を行わない。
- **反映先**: `docs/phase3.md` 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-025 — backoff rmw=1 一点測定

- **出所逐語 + file:line**: 「[P3] rmw=1 で 1 点」
  (`output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:94`)。
- `source_occurrences`: **X6-22**（backoff 残件 P3）。
- **事実状態**: **未消化** — backoff 成果は rmw=false のままで、該当一点の run/report がない。
- **反証・不確実性**: 一点追加は一般性を証明せず、blind-write 限定帰属の境界確認にしかならない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — blind-write 限定の scope を外す場合だけ価値が発火。
- **代替案**: rmw=false 限定を明記して追加点を取らない。
- **発火条件述語**: `P_rmw := backoff_claim_scope_includes_rmw_true ∧ qualifying_rmw1_point_absent`。
  観測対象は claim scope と committed run；現在 **false**；claim scope 改訂時。
- **真時 action**: 現 headline と同じ env/pin/thread/skew/records で rmw=1 の事前登録一点を測る。
- **失効条件**: claim scope を rmw=false / blind-write に限定し続ける。
- **反映先**: `docs/phase3.md` 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-026 — calibration maxrss 固定オーバヘッド控除

- **出所逐語 + file:line**: 「より厳密な下限が要るなら (a) 固定オーバヘッドを差し引く」
  (`output/insights/2026-06-18_calibration-no-cache-miss-saturation.md:58-60`)。
- `source_occurrences`: **X6-01**。
- **事実状態**: **未消化** — `orchestrator/calibrator/analyze.py:124-149` は生の maxrss を使い控除しない。
- **反証・不確実性**: source 自身は現方式を実用上十分とするため、無条件要件ではない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — より厳密な下限が必要な場合だけ価値が生存。
- **代替案**: 現方式の保守性と固定オーバヘッド未控除を限界として明記する。
- **発火条件述語**: **X5 派生案・未裁定**として
  `P_overhead_X5 := fixed_overhead_bytes / maxrss_at_selected_N ≥ 0.05 ∧
  subtracting_fixed_overhead_changes_selected_N`。5% 閾値は source 由来でなく裁定対象。観測対象は同一 binary の
  zero-record/最小実行 baseline、選定 N の maxrss と控除後再計算；現在 **unknown**（baseline 未取得）。
- **真時 action**: 固定オーバヘッド baseline を同一 env/binary で測り、控除前後の採用 N を再計算して
  protocol へ採否を記録する。
- **失効条件**: raw maxrss を意図的に保守的な正本値として承認する、または控除後も全承認 K で採用 N が不変。
- **反映先**: `docs/phase3.md` 見送り台帳または calibration 前提節、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-027 — calibration sweep の 1m 未満拡張

- **出所逐語 + file:line**: 「(b) スイープを 1m 未満に延ばす」
  (`output/insights/2026-06-18_calibration-no-cache-miss-saturation.md:58-60`)。
- `source_occurrences`: **X6-02**。
- **事実状態**: **未消化** — `orchestrator/calibrator/cli.py:112` の既定開始点は 1,000,000 records。
- **反証・不確実性**: source は現方式を実用上十分とし、通常は追加 sweep のコストを正当化しない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — K 感度などで下限左打切りが生じた場合だけ必要。
- **代替案**: 1m を測定下限として結果を censored 表示する。
- **発火条件述語**: `P_sub1m := approved_K_sensitivity_table_reports_left_boundary_censoring ∧
  min(measured_records)=1_000_000`。観測対象は承認済み K/N 感度表、records grid と
  `lower_bound_selected`；現在 **false**（K 感度表が未承認・未作成）；B-015 完了時に再評価。
- **真時 action**: 事前登録した等比 grid を 1,000,000 records 未満へ延長し、censoring が解けるまで測る。
- **失効条件**: 承認 K 集合の全てで左端 censoring がない、または 1m を制度上の最小 N として明示承認する。
- **反映先**: `docs/phase3.md` 見送り台帳または calibration protocol、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-028 — range predicate の P record

- **出所逐語 + file:line**: 「範囲境界 (lo, hi) または next-key を R とは別の `P` レコードで記録」
  (`output/insights/2026-06-18_phantom-predicate-out-of-scope.md:37-45`)。
- `source_occurrences`: **X6-03**（predicate 対応 parent の child 1/2）。
- **事実状態**: **未消化** — verifier trace schema / parser に P record がない。
- **反証・不確実性**: 現行 point-key workload では predicate record は不要。S1 の protocol 移植だけでは発火しない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — range/predicate workload 採用時だけ correctness blocker になる。
- **代替案**: range workload を verifier の certified scope から明示除外する。
- **発火条件述語**: `P_pred_record := range_or_predicate_workload_approved ∧ trace_schema_has_no_P_record`。
  観測対象は workload schema と trace parser；現在 **false**；range workload の事前登録時。
- **真時 action**: P record の境界/next-key schema、parser と trace producer を実装し、点 read と混同しない
  positive/negative control を追加する。
- **失効条件**: range/predicate workload を certified scope から恒久除外する。
- **反映先**: `docs/phase3.md` 見送り台帳、発火時は verifier trace schema、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-029 — predicate anti-dependency 検出

- **出所逐語 + file:line**: 「verifier 側に predicate anti-dependency (述語 rw) の検出を足す」
  (`output/insights/2026-06-18_phantom-predicate-out-of-scope.md:40-45`)。
- `source_occurrences`: **X6-04**（predicate 対応 parent の child 2/2）。
- **事実状態**: **未消化** — `orchestrator/verifier/dsg.py` は key/version の rw・wr・ww だけを扱う。
- **反証・不確実性**: B-028 の P record がなければ本検出は入力を持たず、単独実装できない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — range/predicate workload 採用時だけ correctness blocker。
- **代替案**: range workload を certified scope から除外し続ける。
- **発火条件述語**: `P_pred_edge := P_pred_record ∧ predicate_rw_detection_absent`。観測対象は P record
  schema と DSG edge types；現在 **false**；B-028 の発火・設計凍結時。
- **真時 action**: P record から predicate rw anti-dependency を構成し、phantom の正例と非 phantom の負例で
  DSG/verifier を固定する。
- **失効条件**: range/predicate workload を certified scope から除外する、または B-028 を不採用と裁定する。
- **反映先**: `docs/phase3.md` 見送り台帳、発火時は verifier DSG 契約、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-030 — axis-proposer 用の既存軸台帳

- **出所逐語 + file:line**: 「既存軸台帳の未材料化…発火条件 = 軸数が増えて手動再構成が非自明になったら
  独立成果物化」 (`docs/archive/worklog-phase3-0702-0713.md:1550-1552`)。
- `source_occurrences`: **X1B-19**。
- **事実状態**: **未消化** — S-1 `known_axes_freeze.json` は性能比較点の freeze で、axis-proposer の
  hole / 探索範囲を人間照合する台帳の直接証拠ではない。
- **反証・不確実性**: 軸名・構成の一部は machine-readable なので、目的を粗く取れば done とも読める。
  CA-3 の直接完了述語基準では unrelated。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 軸数増加と手動照合困難化がまだ定量確認されない。
- **代替案**: 独立台帳を作らず、既存 freeze と axis-onboarding 文書を索引で接続する。
- **発火条件述語**: **predicate 未定義 — 裁定で定義を求める**。入力文書集合、再構成対象の axis/hole 集合、
  review 手順と失敗判定が未定義で、現状は真偽評価不能。観測対象候補は freeze、axis-onboarding と
  proposer 入力だが、**現在値は unknown**。
- **真時 action**: まず裁定で入力集合・期待 axis/hole・照合手順・失敗条件を固定し、その述語が真なら
  machine-readable ledger を作る。
- **失効条件**: axis-proposer を廃止する、または定義済みの再構成試験を既存 freeze/index が常に満たす。
- **反映先**: `docs/phase3.md` 見送り台帳、発火時は axis-onboarding の機械可読 companion、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-031 — 共有相手決定時の review snapshot

- **出所逐語 + file:line**: 「共有相手が決まった時点で、相談したい問いから review snapshot の収録範囲を切る」
  (`docs/archive/worklog-phase3-0714-0716.md:257`)。
- `source_occurrences`: **X2-45**。
- **事実状態**: **未消化** — 共有相手決定、snapshot 作成、不要裁定の証拠がなく、repo 外の trigger 成立も不明。
- **反証・不確実性**: trigger が成立していない正当な deferred と、carrier がない黙落ちの両解釈がある。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 相手と問いが決まる前の snapshot は過不足を固定する。
- **代替案**: repository snapshot を作らず、共有時に既存 commit / artifact の allowlist だけを渡す。
- **発火条件述語**: `P_share := external_research_partner_identified ∧ review_question_set_frozen ∧
  curated_snapshot_absent`。観測対象は外部共有判断と収録 allowlist；現在 **不明のため false 扱い**；共有承認時。
- **真時 action**: 凍結した問いから必要 artifact/commit の allowlist を作り、最小 review snapshot を生成する。
- **失効条件**: 外部共有を取りやめる、または repository snapshot ではなく既存 commit allowlist だけを渡すと裁定する。
- **反映先**: `docs/phase3.md` 見送り台帳、外部共有時の結果は `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

## D. プロセス・文書系

### B-032 — CLAUDE.md 作業手順 5 への provenance pointer 配線

- **出所逐語 + file:line**: 「作業の進め方 5 への配線 1 行 (provenance ポインタ方式 + workflow 要旨返し)
  は未承認のまま持ち越し」 (`docs/archive/worklog-phase3-0702-0713.md:2121-2122`)。
- `source_occurrences`: **X1B-73 の split child 1/2**。
- **split 関係**: 元複合 B-032 を安定キー B-032（本 child）と B-059（workflow 要旨返し規律）へ分割。
- **事実状態**: **部分吸収** — `docs/failures.md:122-129` の F13 と driver hash ledger に実質の一部があるが、
  約束された provenance pointer の `CLAUDE.md` 1 行はない。
- **反証・不確実性**: 実目的達成を重く見れば完了とも読めるが、文書配線の直接完了述語は未達。
- **AI 推奨（非拘束）**: **条件付き保留候補** — provenance pointer を hot path の標準導線に戻す場合だけ発火。
- **代替案**: `CLAUDE.md` を増やさず、F13 と driver 契約を唯一の正本として明示裁定する。
- **発火条件述語**: `P_clause5_provenance := approved_hot_path_requires_provenance_pointer ∧
  current_clause5_lacks_pointer`。観測対象は provenance/driver 契約と `CLAUDE.md` 作業の進め方 5；
  現在 **false**（hot-path 配線は未承認）；導線改訂時。
- **真時 action**: `CLAUDE.md` 作業手順 5 に F13/driver provenance 正本への 1 行 pointer を追加し、
  内容を重複再掲しない。
- **失効条件**: F13 と driver 契約だけを唯一の十分な正本として承認する、または当該 workflow 導線を廃止する。
- **反映先**: 保留状態は `docs/phase3.md` 見送り台帳、採用時は `CLAUDE.md` 作業の進め方 5 と
  `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-059 — workflow 要旨返し規律

- **出所逐語 + file:line**: 「作業の進め方 5 への配線 1 行 (provenance ポインタ方式 + workflow 要旨返し)
  は未承認のまま持ち越し」 (`docs/archive/worklog-phase3-0702-0713.md:2121-2122`)。
- `source_occurrences`: **X1B-73 の split child 2/2**。
- **split_from**: **B-032（元複合行）**。既存 B キーを変えず、分離 child を末尾キー B-059 とした。
- **事実状態**: **部分吸収** — F13 と driver hash ledger は provenance を運ぶが、workflow が context 境界で
  要旨を返す standing rule の直接完了証拠はない。
- **反証・不確実性**: workflow を標準導線で使わない場合、要旨返し規律は不要。個別 workflow の出力 schema が
  既に同等要旨を持つ可能性はある。
- **AI 推奨（非拘束）**: **条件付き保留候補** — workflow 要旨を context 境界の標準入力にする場合だけ発火。
- **代替案**: standing rule を置かず、各 workflow schema が必要な digest を個別に定義する。
- **発火条件述語**: `P_workflow_summary := workflow_output_used_across_context_boundary ∧
  required_summary_schema_absent`。観測対象は workflow 呼出契約、返却 schema と consumer 入力；現在 **false**；
  新 workflow の標準導線承認時。
- **真時 action**: 返すべき結果・不確実性・証拠 pointer の最小 summary schema を定め、consumer が生ログでなく
  要旨だけを受け取る回帰を追加する。
- **失効条件**: workflow 利用を廃止する、または全 workflow が個別 schema で同等の要旨契約を満たす。
- **反映先**: 保留状態は `docs/phase3.md` 見送り台帳、採用時は workflow 運用正本と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-033 — fan-out 3 本以上の multi-agent 規則

- **出所逐語 + file:line**: 「多エージェント実行は fan-out 実在時 (3 本以上) のみ」
  (`docs/archive/worklog-phase3-0702-0713.md:608-609`)。
- `source_occurrences`: **X1A-83**。
- **事実状態**: **未消化** — task-class gate は小さい class 1 で子を起動しないが、「3 本以上」は規約化されていない。
- **反証・不確実性**: 2 本でも独立 latency を短縮する場合があり、固定 3 閾値の一般妥当性は未実証。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 現行 gate が既に小作業を抑制し、追加固定閾値の必要性は未発火。
- **代替案**: 数値閾値を置かず、「独立で並列利益がある具体 subtask のみ」とする現行規律を維持。
- **発火条件述語**: **X5 派生案・未裁定**として
  `P_fanout_X5 := comparable_multi_agent_task_runs(n≥5, independent_tasks<3) ∧
  median(agent_startup_s + merge_s + rework_s) > median(parallel_wall_time_saved_s)`。観測対象は同種 task-run の
  task graph と実測時間；現在 **unknown**（比較可能な n≥5 台帳なし）。
- **真時 action**: 3 本未満を禁止する規則を pilot し、同種 task の lead time・finding・手戻りが悪化しないことを
  前後比較してから規約化する。
- **失効条件**: n≥5 の比較で並列節約が調整コスト以上、または現行「独立利益」gate が同じ無駄を防ぐと確認する。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は `CLAUDE.md` サブエージェント節、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-034 — ultracode 常時オンの見直し

- **出所逐語 + file:line**: 「ultracode 常時オンの見直し (監査・探索セッション限定オンにする提案は
  提示済み・未決着)」 (`docs/archive/worklog-phase3-0702-0713.md:608-609`)。
- `source_occurrences`: **X1A-82**。
- **事実状態**: **未消化** — 明示裁定がなく、後続利用実績は「常時オン維持」の直接決定ではない。
- **反証・不確実性**: 利用継続を暗黙棄却と読む余地はあるが、done 証拠基準では人間裁定を確認できない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 常時オンのコスト・便益が現在の model/surface で未計測。
- **代替案**: 現行を維持し、個別 session が必要時だけ明示 override する。
- **発火条件述語**: `P_ultra := ultracode_default_causes_rate_or_cost_constraint ∨
  audit_quality_diff_is_measured`。観測対象は利用率、rate limit、finding 実効密度；現在 **未観測=false**；
  model 経済監査時。
- **真時 action**: 同種 session の常時オン/限定オンを比較し、rate/cost と real finding 密度を併記して default を裁定する。
- **失効条件**: ultracode 機能が廃止される、または現 default 維持を計測不要として明示裁定する。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は該当 model 運用正本、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-035 — D39 決定 1 の wording 訂正

- **出所逐語 + file:line**: 「anchor finding = D39 決定1 の wording 訂正の可否」
  (`docs/archive/worklog-phase3-0702-0713.md:818-819,834-835,903-904`)。
- `source_occurrences`: **X1A-85**。
- **事実状態**: **未消化** — D39 は現在も `head_text=base_text` に「検証は弱まらない」と記す
  (`docs/decisions.md:1066-1077`)。
- **反証・不確実性**: 歴史的 decision の原文保存を優先するなら訂正でなく追記が適切。
- **AI 推奨（非拘束）**: **昇格候補** — load-bearing な設計説明の不正確な wording が現存し、trigger は真。
- **代替案**: 原文を変えず、直後に日付付き erratum を追記する。
- **発火条件述語**: `P_D39_wording := D39_says_validation_is_not_weakened ∧
  head_text_equals_base_text_reduces_independent_validation`。観測対象は D39 決定 1 と現行比較契約；
  現在 **true**（不正確な wording が正本に残る）。
- **反映先**: `docs/decisions.md` D39 の erratum と `docs/worklog.md` 末尾；状態は `docs/phase3.md` 見送り台帳。
- **ユーザー裁定**: **未裁定**

### B-036 — Codex runtime の nested tool exact allowlist

- **出所逐語 + file:line**: 「全 nested tool surface の exact allowlist と許可外 event 負例が揃うまで
  runtime blocked を維持」 (`docs/archive/worklog-phase3-0714-0716.md:185,202,219`)。
- `source_occurrences`: **X2-40**。
- **事実状態**: **未消化** — `.codex/agents/README.md:12-19` は native 0 / static 13 / runtime blocked 13、
  `docs/decisions.md:2213-2219` は再開条件未充足を列挙する。
- **反証・不確実性**: policy 文書は現状を安全に保持するため、task carrier がなくても runtime が誤って再開する
  状態ではない。platform/tool surface 所有の blocker を repo 側だけで解けない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — runtime 再開を望む時だけ実装価値が発火し、現在は blocked 維持が安全。
- **代替案**: native profile を恒久廃止し、static adapter だけを維持する。
- **発火条件述語**: `P_codex_runtime := user_approves_native_runtime_reactivation ∧
  (exact_tool_allowlist_absent ∨ denied_event_e2e_absent)`。観測対象は selector、全 tool surface、spawn/allow/deny E2E；
  現在 **false**；再開提案時。
- **真時 action**: selector と継承 surface を列挙した exact allowlist を実装し、許可・拒否 tool event と spawn の
  E2E negative control を通す。
- **失効条件**: native Codex runtime を恒久廃止し、static adapter だけを正式な実行面にする。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は `.codex/agents/README.md` と関連 decision、
  `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-037 — Codex hook adapter と parity test

- **出所逐語 + file:line**: 「既存 2 判定核への adapter + parity test まで保留」
  (`docs/archive/worklog-phase3-0714-0716.md:126-127`)。
- `source_occurrences`: **X2-41**。
- **事実状態**: **未消化** — Codex hook adapter/parity test は未実装で、Codex では hook 発火を主張しない状態
  (`docs/decisions.md:2081-2085`; `AGENTS.md:18-20`)。
- **反証・不確実性**: decision 自体が安全な保留理由を保持しており、黙って安全性を失ってはいない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 安全な tool-input 契約が得られるまで trigger 偽。
- **代替案**: Codex hook 配線を恒久対象外とし、manual boundary と runtime blocked を正式化する。
- **発火条件述語**: `P_codex_hook := stable_codex_tool_input_contract_available ∧
  adapter_parity_tests_absent`。観測対象は apply_patch/tool payload schema と Claude/Codex parity corpus；現在 **false**；
  tool contract 再分類時。
- **真時 action**: 既存判定核への Codex payload adapter を作り、Claude/Codex の同値 allow/deny corpus と
  path 欠落 negative control を parity test に固定する。
- **失効条件**: Codex hook 配線を恒久対象外と裁定する、または native/runtime write 面を廃止する。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は `hooks/README.md` / AGENTS adapter 節、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-038 — locked strategy-review-freeze worktree 残骸

- **出所逐語 + file:line**: 「気づき (スコープ外・処分は人間判断):
  `.claude/worktrees/strategy-review-freeze` が locked のまま残存」
  (`docs/archive/worklog-phase3-0714-0716.md:348-349`)。
- `source_occurrences`: **X2-49**。
- **事実状態**: **裏取り不能** — 処分の file:line/commit はない一方、基準時の `git worktree list` と filesystem
  では対象が既に不在。過去処分は裏取り不能、現在の作業前提は消滅している。
- **反証・不確実性**: X2 は直接証拠基準から unresolved とした。別 clone / metadata に残る可能性は排除できない。
- **AI 推奨（非拘束）**: **正本の完了記録だけ更新** — 現 checkout では除去という目的状態にあり、追加削除対象がない。
- **代替案**: 人間の処分証言がない限り保留し、同名 worktree 再出現時だけ再調査する。
- **発火条件述語**: `P_worktree_terminal := named_worktree_absent_from_git_worktree_list ∧
  named_path_absent_from_filesystem`。観測対象は基準時の `git worktree list` と filesystem；現在 **true**。
- **反映先**: `docs/phase3.md` 見送り台帳に「現物不在・処分証拠なし」を terminal 記録し、
  `docs/worklog.md` 末尾へ裁定結果。
- **ユーザー裁定**: **未裁定**

### B-039 — 07-12 (6) の無名「ほか should-fix」

- **出所逐語 + file:line**: 「07-12 (6) 持ち越し裁定」
  (`docs/archive/worklog-phase3-0714-0716.md:36`)。参照元は「provenance 恒久修正ほか should-fix の着手順」
  (`docs/archive/worklog-phase3-0702-0713.md:1948-1950`)。
- `source_occurrences`: **X2-13**。
- **事実状態**: **裏取り不能** — provenance union は 80b21de で完了したが、「ほか」の対象集合を後続資料から
  復元できない。
- **反証・不確実性**: 「ほか」は単なる prose で実 child がなかった可能性と、未列挙 child が落ちた可能性が同程度。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 一次証拠なしで廃棄基準を満たさず、識別可能になった時だけ裁定できる。
- **代替案**: 対象不能を理由に廃棄し、同型 finding が再発したら新規行で扱う。
- **発火条件述語**: `P_unnamed := primary_source_recovers_a_named_should_fix_child_not_covered_by_X2_08_12`。
  観測対象は当時の review 原文・凍結成果物；現在 **false/復元不能**；新一次資料発見時。
- **真時 action**: 復元した named child を既存 B 行と突合し、重複でなければ独立裁定行として証拠付きで起票する。
- **失効条件**: ユーザーが無名 placeholder に実 child はなかったと裁定する、または一次資料の恒久消失を理由に
  terminal reject する。
- **反映先**: `docs/phase3.md` 見送り台帳に「裏取り不能」と裁定を記録し、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-040 — S6 盲検で入力構成への言及禁止

- **出所逐語 + file:line**: 「将来の盲検設計は提案側に『入力構成への言及禁止』を足すべき」
  (`docs/archive/worklog-phase3-0702-0713.md:2207-2209`)；同旨
  (`output/insights/2026-07-13_s6-report-language.md:41`;
  `output/insights/2026-07-13_s6-rounds-content-analysis.md:175`)。
- `source_occurrences`: **X1B-75 = X6-47**。
- **事実状態**: **未消化** — `.claude/agents/axis-proposer.md:53-61` は入力構成を説明するが、出力での言及禁止を
  規定しない。8b は blind でなく swapped 対照を採用したため未発火。
- **反証・不確実性**: 実 S6 採点 reason に由来変更の形跡はなく、過去結果の実害は限定的。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 次の blind 設計でだけ価値が発火。
- **代替案**: 入力構成言及を許し、由来推定可能性を既知限界として採点に影響させない規則を固定する。
- **発火条件述語**: `P_blind := new_blind_proposal_design_approved ∧
  proposal_prompt_lacks_input_configuration_mention_ban`。観測対象は提案 prompt と匿名化設計；現在 **false**；
  次の blind prompt 凍結前。
- **真時 action**: proposer prompt に入力構成への言及禁止を追加し、由来を漏らす出力が拒否される fixture を固定する。
- **失効条件**: blind proposal design を採用しない、または入力構成を開示する非盲検設計へ明示変更する。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は該当 proposer prompt / 実験事前登録、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-041 — S6 c1「軸」定義の明文化

- **出所逐語 + file:line**: 「c1 の『軸』定義 (作用点基準 vs 政策集合基準) の明文化を将来の採点基準設計の
  教訓として」 (`docs/archive/worklog-phase3-0702-0713.md:2235-2236`)。
- `source_occurrences`: **X1B-76**。
- **事実状態**: **未消化** — `output/s6-rounds/audit-sheet.md:743` に教訓は残るが、採点基準正本へ明文化されていない。
- **反証・不確実性**: 将来の rubric が c1 を再利用しなければ実害はない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — c1 / 同型 rubric の再利用時だけ定義差が load-bearing。
- **代替案**: c1 を再利用せず、新 rubric で別名・別定義を事前登録する。
- **発火条件述語**: `P_axis_definition := scoring_rubric_reuses_c1_or_axis_term ∧
  action_point_vs_policy_set_semantics_unfixed`。観測対象は rubric と用語定義；現在 **false**；採点基準凍結前。
- **真時 action**: action-point 基準か policy-set 基準かを rubric 冒頭で一意に定義し、境界例を採点 fixture にする。
- **失効条件**: c1/「軸」を再利用せず、曖昧性のない別名・別定義で新 rubric を作る。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は該当 scoring rubric、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-042 — Phase 1〜2 failures 4 件の回収

- **出所逐語 + file:line**: 「Phase 1〜2 分 4 件は未回収と明記」
  (`docs/archive/worklog-phase3-0702-0713.md:2113-2116`)。
- `source_occurrences`: **X1B-74**。
- **事実状態**: **未消化** — `docs/failures.md:284-287` は「必要になったとき grep で回収」と明示し、
  terminal disposition はない。
- **反証・不確実性**: failures 台帳を live carrier と認めれば正当な deferred で、黙落ち確度は low。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 一次記録が保持され、今すぐの回収価値は未発火。
- **代替案**: 4 件を恒久 history-only と明記して回収義務を廃棄する。
- **発火条件述語**: `P_failure_recovery := new_review_opened ∧
  (review_scope_explicitly_includes_phase1_or_2 ∨ reviewed_diff_touches_any_archived_failure_path) ∧
  four_entries_not_indexed`。観測対象は review scope、diff path、4 件の archive source と failures 索引；
  現在 **false**（該当 review 未開始）。
- **真時 action**: 4 件を現行 failure tag/index へ source pointer 付きで回収し、新 review の threat model に含める。
- **失効条件**: 4 件を history-only と裁定する、または全 4 件が後継 failure entry に明示 supersede される。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は `docs/failures.md` の索引、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-043 — 新 workflow 起動前の model lint 継続規則

- **出所逐語 + file:line**: 「新 workflow script は起動前に
  `python3 tools/check_workflow_models.py` で自己検査」 (`docs/worklog.md:781`)；checker 実装推奨
  (`output/insights/2026-07-19_agent-model-economy-audit.md:21-26`)。
- `source_occurrences`: **X3-69**；**X6-105**（実装 child のみ done）。
- **事実状態**: **部分吸収** — checker は存在する (`tools/check_workflow_models.py:13-14`) が、継続規則は
  terminal 化できず live carrier がない。`hooks/README.md:119` は standalone lint・hook 未配線とする。
- **反証・不確実性**: X6-105 の done と X3-69 の continued は、実装と毎回実行を分ければ矛盾しない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 新 workflow script が追加・変更される時だけ実行義務が発火。
- **代替案**: standing rule を廃止し、CI の静的検査対象ファイル集合へ checker を組み込む。
- **発火条件述語**: `P_workflow_lint := workflow_script_added_or_changed ∧
  model_lint_not_run_on_candidate`。観測対象は workflow diff と checker rc；現在 **false**；該当 diff の起動前。
- **真時 action**: candidate workflow 起動前に checker を実行し、対象 script・rc・model 明示結果を review 証拠へ残す。
- **失効条件**: workflow script 面を廃止する、または checker が同じ候補 diff を必須 CI gate として完全に覆う。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は workflow 運用正本 / `hooks/README.md`、
  `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

## E. 外部・環境系

X3 が原子化した「任意後始末 4 child」は、他マシン clone 1 件（X3-56）と GitHub / remote 整合 3 件
（X3-57〜59）の合計であり、GitHub-only 4 件 + clone 1 件ではない。入力レポートに存在しない第 5 child は
捏造せず、この 4 行を逐語どおり保持する。

端末判定済みの `external/ccbench` テスト残骸復旧（X2-57）は、`docs/archive/worklog-phase3-0714-0716.md:625-628`
で submodule clean まで確認されているため、指示どおり本体行から除外した。証拠は付録の X2-57 に保存する。

### B-044 — 資金提供元回答の送付判断

- **出所逐語 + file:line**: 「本協議側は回答の送付判断…が持ち越し」
  (`docs/archive/worklog-phase3-0702-0713.md:1674-1676`)。
- `source_occurrences`: **X1B-31**（funder parent の child 1/2）。
- **事実状態**: **裏取り不能** — repository 内に送付・棄却・引継ぎがなく、repository 外での送付有無は不明。
- **反証・不確実性**: 外部会話で完了済みの可能性があるため、未送付を事実認定できない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 送付対象と窓口がなお有効な場合だけ価値が生存。
- **代替案**: 時機を失したとして廃棄し、新しい照会が来た場合に回答を作り直す。
- **発火条件述語**: `P_funder_send := funder_reply_still_expected ∧ approved_reply_exists ∧
  delivery_not_confirmed`。観測対象は外部 correspondence と承認済み文面；現在 **不明のため false 扱い**；
  次の funder 連絡確認時。
- **真時 action**: 承認済み文面の現行性を確認して送付可否をユーザーへ提示し、送付または見送りの存在だけを記録する。
- **失効条件**: 窓口・照会が終了する、既に送付済みと確認する、またはユーザーが時機失効で廃棄裁定する。
- **反映先**: 保留状態は `docs/phase3.md` 見送り台帳、外部結果は秘密を載せず `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-045 — ソルバ・量子質問への回答作成

- **出所逐語 + file:line**: 「質問 2 (ソルバ・量子の妥当性) への回答作成が持ち越し」
  (`docs/archive/worklog-phase3-0702-0713.md:1674-1676`)。
- `source_occurrences`: **X1B-32**（funder parent の child 2/2）。
- **事実状態**: **裏取り不能** — 回答作成・棄却・引継ぎの repository 証拠がなく、related-work の
  「ソルバ」は別文脈。
- **反証・不確実性**: 外部で既に回答した可能性と、質問自体が失効した可能性を repo から分離できない。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 質問が現在も open の場合だけ作成価値が発火。
- **代替案**: 旧質問を廃棄し、再照会時に現行設計を基準に新規回答する。
- **発火条件述語**: `P_funder_q2 := solver_quantum_question_still_open ∧ current_answer_absent`。
  観測対象は外部 correspondence と回答文面；現在 **不明のため false 扱い**；次の照会確認時。
- **真時 action**: 現行設計と related work を基準に回答案を作り、ユーザー承認後の送付判断へ渡す。
- **失効条件**: 質問が close/撤回済み、回答済み、または再照会時に新規回答へ置換すると裁定する。
- **反映先**: `docs/phase3.md` 見送り台帳と、外部結果の存在だけを `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-046 — 他マシン clone の reset / reclone

- **出所逐語 + file:line**: 「他マシン clone (Pegasus 等) の fetch + reset または clone し直し」
  (`docs/worklog.md:229`)。
- `source_occurrences`: **X3-56**（履歴書換え後始末 parent の child 1/4）。
- **事実状態**: **裏取り不能** — repo 外の clone 状態と完了証拠を観測できない。
- **反証・不確実性**: 対象 clone が既に削除・更新済み、または存在しない可能性がある。
- **AI 推奨（非拘束）**: **条件付き保留候補** — stale clone が再利用される時だけ必要。
- **代替案**: 対象 clone を廃棄し、必要時に fresh clone のみ許可する。
- **発火条件述語**: `P_clone := target_clone_exists ∧ contains_pre_rewrite_history ∧
  target_clone_will_be_used`。観測対象は各 clone の HEAD / remote / object history；現在 **不明のため false 扱い**；
  対象マシンでの次回利用前。
- **真時 action**: 対象 clone を明示し、fresh clone または fetch+hard reset のどちらかで新履歴へ揃え、HEAD/remote を確認する。
- **失効条件**: 対象 clone が存在しない・廃棄済み、または今後利用しないと裁定する。
- **反映先**: `docs/phase3.md` 見送り台帳と、機密を含まない完了事実を `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-047 — GitHub PR 本文の session URL 監査

- **出所逐語 + file:line**: 「GitHub PR 本文のセッション URL 確認」 (`docs/worklog.md:229-230`)。
- `source_occurrences`: **X3-57**（履歴書換え後始末 parent の child 2/4）。
- **事実状態**: **裏取り不能** — GitHub 側の確認結果がなく、repo 内 trailer 除去は PR 本文とは別面。
- **反証・不確実性**: 対象 PR がない、本文に URL がない、または既に修正済みの可能性がある。
- **AI 推奨（非拘束）**: **条件付き保留候補** — GitHub 接続可能かつ対象 PR が存在する時だけ価値が発火。
- **代替案**: 過去 PR は触らず、今後の PR template / review で session URL 禁止だけを固定する。
- **発火条件述語**: `P_pr_url := github_access_available ∧ historical_PRs_exist ∧
  session_URL_audit_not_recorded`。観測対象は PR 本文集合；現在 **不明のため false 扱い**；次の GitHub 管理作業時。
- **真時 action**: 対象 PR 本文を URL 値を転載せず監査し、該当数と除去/無処置の結果だけを記録する。
- **失効条件**: 対象 PR が存在しない、監査済みと確認する、または過去 PR を不変とする裁定を行う。
- **反映先**: `docs/phase3.md` 見送り台帳と、URL を転載しない集約結果を `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-048 — GitHub refs/pull の Support GC

- **出所逐語 + file:line**: 「GitHub 側 refs/pull 残存の完全消去は Support へ GC 依頼」
  (`docs/worklog.md:230-231`)。
- `source_occurrences`: **X3-58**（履歴書換え後始末 parent の child 3/4）。
- **事実状態**: **裏取り不能** — Support 依頼・GC 完了・refs 残存の外部証拠がない。
- **反証・不確実性**: 完全消去を要求しないなら不要。Support が refs の物理 GC を保証できない可能性もある。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 「到達不能」ではなく「完全消去」を必要とする場合だけ発火。
- **代替案**: force-push 後の通常到達不能化を受容し、完全 GC は要求しない。
- **発火条件述語**: `P_support_gc := user_requires_physical_removal ∧ github_refs_pull_retains_old_objects ∧
  support_request_not_completed`。観測対象は GitHub refs / support response；現在 **不明のため false 扱い**；
  完全消去要件の裁定時。
- **真時 action**: 秘密や URL を記録せず GitHub Support へ GC 可否を問い合わせ、保証範囲と完了結果を集約する。
- **失効条件**: 通常到達不能化を十分と裁定する、残存 object がないと確認する、または provider が物理 GC を保証しない。
- **反映先**: `docs/phase3.md` 見送り台帳と、問い合わせ ID を載せず結果だけを `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-049 — fetch --prune 後の tracking ref 最終整合

- **出所逐語 + file:line**: 「次回の実 `git fetch --prune` で tracking ref の最終整合を確認」
  (`docs/worklog.md:230-231`)。
- `source_occurrences`: **X3-59**（履歴書換え後始末 parent の child 4/4）。
- **事実状態**: **未消化** — 実行結果がなく、現 local main の ahead 状態は fetch/prune 完了述語ではない。
- **反証・不確実性**: 後続 fetch が記録されず実行済みの可能性はある。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 次のネットワーク接続 fetch まで評価不能。
- **代替案**: tracking ref を削除して再作成し、旧整合確認を不要化する。
- **発火条件述語**: `P_prune := real_git_fetch_prune_about_to_run ∧ final_tracking_ref_check_absent`。
  観測対象は fetch 結果、remote-tracking refs、origin/main ancestry；現在 **false**；次の実 fetch 直後。
- **真時 action**: 実 `fetch --prune` 後に tracking refs と origin/main ancestry を確認し、旧 ref 不在を記録する。
- **失効条件**: 対象 remote/tracking ref を廃止する、または後続の記録済み fetch/prune が同じ整合を証明する。
- **反映先**: `docs/phase3.md` 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-050 — user settings の model=fable→opus

- **出所逐語 + file:line**: 「ユーザー: ~/.claude/settings.json の手動変更 (model: \"opus\" /
  effortLevel: \"high\")」 (`docs/worklog.md:779`)；「既定 opus/high … を推奨」「手動変更をユーザーへ引き渡し」
  (`output/insights/2026-07-19_agent-model-economy-audit.md:27-32`)。
- `source_occurrences`: **X3-67 = X6-106**（effort child X6-107 は done）。
- **事実状態**: **未消化** — 2026-07-19 の `~/.claude/settings.json` 直接観測では
  `model=claude-fable-5`、`effortLevel=high`。
- **反証・不確実性**: repo 外設定は時点後に変更された可能性があり、本スナップショットから現在値を保証しない。
  X3 は読み取り対象外として blocked(user)、X6 は現物確認して unresolved とした。
- **AI 推奨（非拘束）**: **昇格候補** — as-of 時点で明示依頼した model child が未実施で trigger は真。
- **代替案**: fable 既定を意図的に維持すると裁定し、opus は監査・統合時の個別指定だけにする。
- **発火条件述語**: `P_settings := observed_model != "opus" ∨ observed_effortLevel != "high"`。
  観測対象は `~/.claude/settings.json`、観測日 **2026-07-19**；現在 **true**
  （`model=claude-fable-5`, `effortLevel=high`）。
- **反映先**: repo 外設定そのものはユーザー管理。裁定結果の存在だけを `docs/worklog.md` 末尾、状態を
  `docs/phase3.md` 見送り台帳へ反映。
- **ユーザー裁定**: **未裁定**

## F. 既知 flake・テスト衛生

### B-051 — protocol_builder repo-tree snapshot の xdist flake

- **出所逐語 + file:line**: 「`test_s8b_protocol_builder` の repo-tree snapshot テストが xdist 並列下で
  4 走中 1 flake (git status --porcelain 前後比較が untracked 出入りに脆弱)」
  (`docs/worklog.md:812-815,821-824`)；実走 `1957 passed / 1 failed` と 4 走中 3 green
  (`output/insights/2026-07-19_test-suite-hygiene-survey.md:159`)。
- `source_occurrences`: **survey flake**（X6 は本項を明示除外）；worklog (5) 次の一手。
- **事実状態**: **未消化** — 4 走中 1 回観測され、単発再現はしない。対象は
  `orchestrator/tests/test_s8b_protocol_builder.py:256,266`。
- **観測済み flake**: 868017 は 1 green、868018 は 1 failure、868019 内に連続 2 green
  （4 走中 3 green）。
- **原因仮説**: 別 worker の untracked 出入りを `git status --porcelain` が同時観測する競合。有力だが
  causal attribution は未確定で、本 wave の製品 diff から独立。
- **保証契約**: SUT 実行前後で **実 repo tree が不変**。tracked だけでなく untracked repo-root 漏出も検出する。
- **修正候補と保証差**: 直列化 marker と隔離 worktree は保証を維持するが速度を失う。tracked-only 比較は
  保証を弱めるため、採るなら tracked / untracked の repo-root 漏出を実際に赤くする別 positive control が必須。
- **反証・不確実性**: flake が単発で、同時 worker のどの path が干渉したかは未記録。直列化だけで消えることも未証明。
- **AI 推奨（非拘束）**: **昇格候補** — xdist が既定で有効で観測済み flake があり、trigger は真。
- **代替案**: テストを xdist group で直列化；または使い捨て隔離 worktree で同じ full-tree 保証を維持する。
- **発火条件述語**: `P_snapshot_flake := xdist_is_default ∧ failures_in_same_wave_full_runs ≥ 1`。
  観測対象は 868017/868018/868019 の 4 走と failing node ID；現在 **true**（failure=1）。
- **acceptance（対称）**: 直列化 / 隔離案は、同一 xdist 条件の反復が green かつ意図的 tracked・untracked
  漏出が双方 red なら受理。tracked-only 案は、同じ二種漏出を別 positive control が red にし、元 SUT の
  tracked 変更も red、通常反復 green の全条件を満たす場合だけ受理。どの案も速度差を同じ runner で併記する。
- **反映先**: `docs/phase3.md` 見送り台帳または test-hygiene 完了条件、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-052 — s1 freeze 系テストの submodule 読取 isolation

- **出所逐語 + file:line**: 「s1 freeze 系テストの submodule 読取 isolation」
  (`docs/worklog.md:739-740,755`)。
- `source_occurrences`: **X3-65**（test-isolation parent の child 1/2）。
- **事実状態**: **未消化** — xdist の patch 窓を読む競合への専用隔離完了証拠がない。
- **反証・不確実性**: patchharness index.lock retry は導入済みだが、読取 isolation とは別。観測 failure が
  本 child 単独に起因する証拠はない。
- **AI 推奨（非拘束）**: **昇格候補** — 並列テストが既定で実 submodule を読む現在、競合 predicate は真。
- **代替案**: s1 freeze 系だけ xdist 直列 group に置き、実 submodule 読取を維持する。
- **発火条件述語**: `P_s1_read_isolation := xdist_is_default ∧ s1_freeze_tests_read_real_submodule ∧
  read_isolation_absent`。観測対象は xdist 設定、s1 freeze test の path 解決と isolation fixture；現在 **true**。
- **反映先**: `docs/phase3.md` の test isolation / 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-053 — patch 適用を tmp worktree へ隔離

- **出所逐語 + file:line**: 「テストの patch 適用を tmp worktree へ隔離する恒久対策」
  (`docs/worklog.md:739-740,755`)。
- `source_occurrences`: **X3-66**（test-isolation parent の child 2/2）。
- **事実状態**: **未消化** — test-hygiene の重複統合・assert 強化や index.lock retry は、実 submodule から
  tmp worktree への隔離を実装していない。
- **反証・不確実性**: 隔離 worktree は full-tree 保証を保ちやすい一方、作成コストと cleanup flake を増やしうる。
- **AI 推奨（非拘束）**: **昇格候補** — xdist と実 submodule patch の同居が現行既定で、競合 trigger は真。
- **代替案**: patch 適用テストを直列化し、tmp worktree の複雑性を増やさない。
- **発火条件述語**: `P_patch_isolation := xdist_is_default ∧ tests_patch_real_submodule ∧
  tmp_worktree_isolation_absent`。観測対象は patch test の書込先、xdist 設定と tmp worktree fixture；現在 **true**。
- **反映先**: `docs/phase3.md` の test isolation / 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-054 — writable 環境で全走 3 連続 rc=0

- **出所逐語 + file:line**: 「Git 管理領域を書き込める環境で `python3 tools/run_tests.py` を3回連続実行し、
  rc=0を確認する」 (`docs/worklog.md:699-705`)。
- `source_occurrences`: **X3-63**。
- **事実状態**: **完了** — commit `6b9c818` は `HEAD` の祖先で、その時点の親環境で全走 3 連続
  rc=0・各 1899 passed が実証・記録済み
  (`output/insights/2026-07-18_env-contract-pegasus-consultations.md:1207` 付近)。
- **反証・不確実性**: 後発スナップショットの xdist flake は過去の受入証拠を未完了へ巻き戻さない。
  後発 flake は B-051 の独立課題である。
- **AI 推奨（非拘束）**: **正本の完了記録だけ更新** — 追加の 3 連続全走は不要。
- **代替案**: 受入時点と後発 flake を別 epoch として明示し、B-051 だけを継続する。
- **発火条件述語**: `P_three_green_done := is_ancestor(6b9c818, HEAD) ∧
  recorded_consecutive_full_suite_green_runs ≥ 3`。観測対象は Git ancestry と consultations の 3 実走記録；
  現在 **true**（3 走とも rc=0、各 1899 passed）。
- **反映先**: `docs/phase3.md` の test acceptance / 見送り台帳と `docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

## G. テスト調査由来の発火条件付き施策

### B-055 — survey #6 ratified_verify git fixture 共有化

- **出所逐語 + file:line**: 「ratified_verify の git fixture 共有化」「スイート全走が `3` 分を超えた場合にのみ発火」
  (`output/insights/2026-07-19_test-suite-hygiene-survey.md:127`)。
- `source_occurrences`: **survey #6**；X6-108 は 9 施策の集約検出。
- **事実状態**: **未消化** — fixture 共有化は未実施。現行 full suite は 3 分を大幅に下回る実績で、source の trigger は偽。
- **反証・不確実性**: 全体時間だけでは ratified_verify fixture が律速とは言えない。共有化は state leakage を増やしうる。
- **AI 推奨（非拘束）**: **条件付き保留候補** — source の条件どおり、現状は抽象化コストを正当化しない。
- **代替案**: fixture を共有せず、遅い個別 setup だけを profile して局所 cache 化する。
- **発火条件述語**: 原述語を逐語保存した `P6_source := full_suite_duration_s > 180`。観測対象は同一 runner/env の
  full-suite 全走時間；現在 **false**（観測済み全走は 180 秒未満）。別案として **X5 派生案・未裁定**の
  `P_fixture_X5 := median(full_suite_duration_s, same_runner_env, n≥3) > 180 ∧
  ratified_verify_fixture_time_s / full_suite_duration_s ≥ 0.20` を置く。20% は数値化した対案で現在 **unknown**
  （fixture profile 未取得）。
- **真時 action**: `P6_source` が真ならまず fixture 時間比を profile し、共有化を選ぶ場合は state leakage の
  negative control と分離 teardown を付けて実装する。
- **失効条件**: full suite が承認済み同一環境で継続して 180 秒以下、fixture を共有不能と裁定する、または
  ratified_verify test 群を廃止する。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は test fixture 契約、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-056 — survey #7 coverage 観測（X5 派生）

- **出所逐語 + file:line**: 「coverage と差分 mutation の衛生監査」「coverage は観測値に留め…達成率 gate にはしない」
  (`output/insights/2026-07-19_test-suite-hygiene-survey.md:128`)。
- `source_occurrences`: **survey #7**；X6-108 は集約検出。**X5 による派生案・未裁定**（元 #7 を coverage と
  差分 mutation に二分した child 1/2）。
- **事実状態**: **未消化** — coverage 観測の標準イベント・artifact は未定義。達成率 gate 禁止だけが source 契約。
- **反証・不確実性**: coverage は assertion 実効性や拒否経路を測らず、単独 KPI は gaming を招く。
- **AI 推奨（非拘束）**: **条件付き保留候補** — 次の hygiene wave / safety gate 変更の診断値としてのみ使う。
- **代替案**: coverage を取らず、node-ID 差分と targeted negative control だけを維持する。
- **発火条件述語**: `P_coverage := new_test_hygiene_wave_started ∨ safety_gate_changed`。観測対象は対象 diff の
  line/branch coverage（説明変数のみ、閾値なし）；現在 **false**；該当 wave の baseline / final checkpoint。
- **真時 action**: baseline/final の line/branch coverage を観測値として保存し、達成率 gate や採否 KPI には使わない。
- **失効条件**: hygiene wave/safety gate 変更を行わない、または coverage を診断にも使わないと裁定する。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は test-hygiene 調査契約、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

### B-057 — survey #7 差分 mutation 標準化（X5 派生）

- **出所逐語 + file:line**: 「coverage と差分 mutation の衛生監査」「差分 mutation は弱テストを疑う監査手段として
  標準化候補にする。達成率 gate にはしない」
  (`output/insights/2026-07-19_test-suite-hygiene-survey.md:128`)。
- `source_occurrences`: **survey #7**；X6-108 は集約検出。**X5 による派生案・未裁定**（元 #7 の child 2/2）。
- **事実状態**: **部分吸収** — 今回 wave は事前登録 mutant matrix を実施した
  (`output/insights/2026-07-19_test-suite-hygiene-survey.md:139-159`) が、差分 mutation の汎用標準は未定義。
- **反証・不確実性**: operator 選定が恣意的なら「殺せる mutant だけ選ぶ」自己証明になる。全変更への常設は高コスト。
- **AI 推奨（非拘束）**: **条件付き保留候補** — validator / 拒否 gate 変更または escaped defect 時だけ発火。
- **代替案**: 標準化せず、各 high-risk wave が threat model に基づく negative control を個別事前登録する。
- **発火条件述語**: `P_diffmut := validator_or_rejection_gate_changed ∨ escaped_defect_observed`。観測対象は対象 diff、
  事前登録 operator、予算、第一失敗アサート、復元後 green；現在 **false**；該当変更の review 前。
- **真時 action**: threat model から mutant/operator と予算を事前登録し、第一失敗 assert と復元後 green を記録する。
- **失効条件**: validator/rejection gate の変更を撤回する、escaped defect が別の mandatory negative control で
  恒久回帰化される、または差分 mutation を不採用と裁定する。
- **反映先**: `docs/phase3.md` 見送り台帳、採用時は test-hygiene / review 契約、`docs/worklog.md` 末尾。
- **ユーザー裁定**: **未裁定**

## 付録 A — 消化済みの証明

### A.1 統計サマリ

原掃引レポートの状態判定表は X1a / X1b / X2 / X3 / X6 の **462 原子項目**。敵対レビュー R1 が
母集団漏れ 5 項目を発見したため、本版の訂正後母集団は **467 原子項目（462 + 追補 5）**である。
X4 は見送り台帳 5 source entry を 6 裁定行へ分割する裏取りであり、467 には重複加算しない。
この網羅は R1 の層化抜き取り検査済みだが、全 source の再全数監査による保証ではない。

| 掃引 | 担当エントリ数 | 原子項目数 | done | continued | blocked | deferred | rejected | superseded | partial | unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| X1a | 34 | 105 | 84 | 1 | 3 | 1 | 7 | 4 | 0 | 5 |
| X1b | 44 | 86 | 63 | 2 | 0 | 5 | 6 | 1 | 2 | 7 |
| X2 | 42 | 85 | 59 | 7 | 1 | 10 | 1 | 5 | 0 | 2 |
| X3 | 30 | 76 | 43 | 10 | 1 | 13 | 1 | 2 | 2 | 4 |
| X6（R1 訂正反映） | 59 | 110 | 70 | 5 | 1 | 10 | 6 | 6 | 2 | 10 |
| レビュー追補 | 2 | 5 | 4 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| **合計** | **211** | **467** | **323** | **25** | **6** | **40** | **21** | **18** | **6** | **28** |

X6 の訂正は X6-96 を done から partial(children) へ移したもの。X2 の複合親 partial 3 件は原子内訳へ
重複計上されず、上表では 0。X4 の裏取り結果は balanced=未消化、
over-throttle=部分吸収、mocc=未消化、ermia=前提消滅・要再定義、calibration K=未消化、
thread 再較正=部分吸収。

### A.2 状態判定表の逐語収録

以下の 5 表は入力レポートの `## 状態判定表` をそのまま収録し、原掃引 462 原子項目の terminal / live
判定証拠を保存する。レビューで判明した訂正は原文行の直後へ `⚠ 訂正` として追記し、母集団漏れ 5 項目は
A.4 に追補する（訂正後総数 467）。X4 は表を持たないため、その事実状態・証拠・完了証拠・発火述語を
A.3 にレポート逐語で収録する。

<!-- APPENDIX_STATE_TABLES -->


#### X1a_report.md

## 状態判定表 (全原子項目)
| id | 項目要約 | 出所 file:line | 状態 | 根拠 (file:line/commit) | 対応関係 | live carrier |
|---|---|---|---|---|---|---|
| X1A-01 | CLAUDE.md 現在地更新 | docs/archive/worklog-phase3-0702-0713.md:33-35 | done | 608a72b; 同:122-123 | same | なし (terminal) |
| X1A-02 | H3 hooks 実体化・最小化・配線 | 同:36,136-137,166-167,190-192,283-284,345-348,404-406 | done | a97c0f3; docs/phase3.md:167 | merged-from | phase3 完了群 |
| X1A-03 | C1 drift 恒久対応 | 同:37,84-85,241 | done | 065593a; 同:115-117 | merged-from | phase3 完了群 |
| X1A-04 | TRACE 別ビルド分離の実挙動検査 | 同:29-31,42-44 | done | 同:51-60,97 | same | なし |
| X1A-05 | verifier DSG/G2 偽陰性検査 | 同:29-31,42-44 | done | 36a1193; 同:52-54,106-109 | same | なし |
| X1A-06 | source_digest/EVOLVE-BLOCK 裏取り | 同:29-31,42-44 | done | 同:55-58,110-114 | same | なし |
| X1A-07 | fitness/admission/median 数値検査 | 同:29-31,42-44 | done | cf62e81; 同:65-69,118-119 | same | なし |
| X1A-08 | roadmap §6 D16 追随 | 同:73-75 | done | d16f7dc; 同:100-102 | split-into child | なし |
| X1A-09 | roadmap §8 7x7→10 protocol | 同:73-75 | done | d16f7dc; 同:100-102 | split-into child | なし |
| X1A-10 | phase2 テスト数更新 | 同:73-75 | done | d16f7dc; 同:100-102 | split-into child | なし |
| X1A-11 | decisions patch 名更新 | 同:73-75 | done | d16f7dc; 同:100-102 | split-into child | なし |
| X1A-12 | agent-architecture critic 注記 | 同:73-75 | done | d16f7dc; 同:100-102 | split-into child | なし |
| X1A-13 | patches README broken-silo 手順 | 同:73-75 | done | d16f7dc; 同:100-102 | split-into child | なし |
| X1A-14 | guided.py docstring 更新 | 同:76-77 | done | 8e06a37; 同:100-102 | split-into child | なし |
| X1A-15 | genome.py 行参照を記号化 | 同:76-77 | done | 8e06a37; 同:100-102 | split-into child | なし |
| X1A-16 | calibrator CLI 出力名更新 | 同:76-77 | done | 8e06a37; 同:100-102 | split-into child | なし |
| X1A-17 | buildcache doc 補記 | 同:76-77 | done | 8e06a37; 同:100-102 | split-into child | なし |
| X1A-18 | fixtures README 凡例 | 同:76-77 | done | 8e06a37; 同:100-102 | split-into child | なし |
| X1A-19 | orchestrator README 実構成化 | 同:76-77 | done | 8e06a37; 同:100-102 | split-into child | なし |
| X1A-20 | agent spec python→python3 | 同:78 | done | a1661d2; 同:100-102 | split-into child | なし |
| X1A-21 | critic.md digest 引数修正 | 同:78 | done | a1661d2; 同:100-102 | split-into child | なし |
| X1A-22 | 書き込み隔離文言の honest 化 | 同:78 | done | a1661d2; 同:100-102 | split-into child | なし |
| X1A-23 | return 疑似 skip 可視化 | 同:79 | done | d96264f; 同:103-104 | split-into child | なし |
| X1A-24 | test_critic/test_guided の例外枝 | 同:79 | done | d96264f; 同:103-104 | split-into child | なし |
| X1A-25 | tests/README 新設 | 同:79 | done | d96264f; 同:103-104 | split-into child | なし |
| X1A-26 | clocks_per_us fallback 記録 | 同:80 | done | 4d1f25f; 同:105 | split-into child | なし |
| X1A-27 | max_records 16m 統一 | 同:80 | done | 4d1f25f; 同:105 | split-into child | なし |
| X1A-28 | txid 欠番検出 | 同:81 | done | 36a1193; 同:106-109 | split-into child | なし |
| X1A-29 | W 行版照合 | 同:81 | done | 36a1193; 同:106-109 | split-into child | なし |
| X1A-30 | key 正規化検査 | 同:81 | done | 36a1193; 同:106-109 | split-into child | なし |
| X1A-31 | genesis 番兵検査 | 同:81 | done | 36a1193; 同:106-109 | split-into child | なし |
| X1A-32 | D25 retryable を last_terminal 化 | 同:82 | done | 02b08eb; 同:110-112 | split-into child | なし |
| X1A-33 | CV=None admission guard | 同:82 | done | 9cde781; 同:110-114 | split-into child | なし |
| X1A-34 | Rejection に variant/src_token | 同:82 | done | ec5aaaf; 同:110-114 | split-into child | なし |
| X1A-35 | records assert→例外 | 同:82-83 | done | 9cde781; 同:110-114 | split-into child | なし |
| X1A-36 | calibrator CLI binary TRACE 検査 | 同:82-83 | done | 9cde781; 同:110-114 | split-into child | なし |
| X1A-37 | nm 失敗を fails-closed | 同:82-83 | done | 9cde781; 同:110-114 | split-into child | なし |
| X1A-38 | p2_2 calibration JSON 照合 | 同:84-85 | done | 065593a; 同:115-117 | split-into child | なし |
| X1A-39 | rep 失敗 notes 永続化 | 同:86 | done | cf62e81; 同:118-119 | same | なし |
| X1A-40 | prob_superiority tie 校正 | 同:87 | done | cf62e81,39c44cc; 同:118-119,144-155 | same | なし |
| X1A-41 | Gate1 √2 docstring 化 | 同:87 | done | cf62e81; stability.py:233-243 | same | なし |
| X1A-42 | dead import 削除 | 同:88 | done | f8f423a; 同:120-121 | split-into child | なし |
| X1A-43 | env_scope_dir 集約 | 同:88 | done | f8f423a; 同:120-121 | split-into child | なし |
| X1A-44 | audit/worklog 最終同期 | 同:90 | done | 同:97,123 | same | なし |
| X1A-45 | 全テスト緑確認 | 同:90 | done | 同:97-98 | same | なし |
| X1A-46 | submodule dirty を clean に戻す | 同:92,125-126 | done | d6bc750; 同:162-164 | merged-from | なし |
| X1A-47 | backoff #ifndef/#error guard | 同:92-93,125-126 | done | 4f7bb3c; 同:156-159 | merged-from | なし |
| X1A-48 | patches フォーマット統一 | 同:125-127 | done | 92e1cd8; 同:160-161 | same | なし |
| X1A-49 | P2-5 指標を a に再校正 | 同:127-130 | done | 39c44cc/D29; 同:144-155 | same | なし |
| X1A-50 | trx 尾部欠落検出 | 同:132-134 | continued | docs/phase3.md:185,424-427 | same | phase3 S1/残存リスク |
| X1A-51 | infra 起因 build-error だけ retryable 化 | 同:132-134 | rejected(reason) | D37: docs/decisions.md:928-933; model.py:100-105 は build-error を terminal と明示 | same | なし |
| X1A-52 | digest へ unstable/cv 伝搬 | 同:132-134 | unresolved | digest.py:38-44,192-217 | same | なし |
| X1A-53 | Gate1 √2 閾値意味論決定 | 同:132-134 | unresolved | stability.py:239-243,275 | same | なし |
| X1A-54 | docs変更とhooks実装をcommit | 同:237-240 | done | 441a50b,f9fa80a,a97c0f3 | split-into child | なし |
| X1A-55 | 観測者効果 diff-of-diffs 実体化 | 同:190-192,239-240,345-348,404-406 | done | 14d64e6; 同:509-515 | merged-from | phase3 完了群 |
| X1A-56 | verify abort 数を WAL 記録 | 同:345-348 | done | 9301a8c; docs/phase3.md:163 | split-into child | phase3 kickoff完了 |
| X1A-57 | apply/revert harness | 同:345-348 | done | 62a0db9; docs/phase3.md:164 | split-into child | phase3 kickoff完了 |
| X1A-58 | build後digest再照合 | 同:345-348 | done | b059a70; docs/phase3.md:165 | split-into child | phase3 kickoff完了 |
| X1A-59 | #include 死角の最小閉塞 | 同:345-348 | done | e0b9b22; docs/phase3.md:166 | split-into child | phase3 kickoff完了 |
| X1A-60 | no-op variant の stock cache-hit | 同:453-457 | done | 4c167b5; docs/phase3.md:156-169 | split-into child | phase3 kickoff完了 |
| X1A-61 | 純 timing variant の全配線1周 | 同:453-457 | done | 4c167b5; 同:568-590 | split-into child | phase3 kickoff完了 |
| X1A-62 | WAL proof chain の実体定義 | 同:241-242,285-286,349-350,407-408,458-459 | done | docs/phase3.md:367-379; layer3 renderer 15d9e7c | merged-from | phase3 層3契約 |
| ⚠ 訂正 (R1) | X1A-62 の `15d9e7c` は解決不能な stale hash。done は維持し、到達可能な根拠を `d6085a9`（実装）/ `2230edf`（最小実レポート）/ `4204013`（v2 拡大）へ訂正 | — | done | `d6085a9`, `2230edf`, `4204013` | レビュー訂正注記 | phase3 層3契約 |
| X1A-63 | Threats to Validity 集約 | 同:241-242,285-286,349-350,407-408,524-527 | unresolved | 専用成果物・commitなし | merged-from | なし |
| X1A-64 | coder loop 停止条件予約 | 同:241-242,285-286,349-350,458-459 | done | D39: docs/decisions.md:1079-1086 | merged-from | なし |
| X1A-65 | fitness 採否方針予約 | 同:241-242,285-286,349-350,458-459 | done | phase3-main-experiment.md:57-67 | merged-from | なし |
| X1A-66 | 再試行方針予約 | 同:241-242,285-286,349-350,458-459 | done | phase3-main-experiment.md:353-355 | merged-from | なし |
| X1A-67 | S2 前倒し | 同:521-525 | done | 9606c66/D36; docs/phase3.md:198-201 | same | phase3 完了段1 |
| X1A-68 | +38%/+11% 別boot再現 | 同:524-525 | unresolved | 元 insight:37-42,79-99 に「残」 | split-into child | なし |
| X1A-69 | critic 軸提案の再現率測定 | 同:524-525 | unresolved | 成果物・commitなし | split-into child | なし |
| X1A-70 | paper-story の日付抜き改名 | 同:560-561 | superseded(by) | ff3268f は日付別 snapshot を `docs/paper-story/` に集約 | superseded | なし |
| X1A-71 | S4 load_rejections consumer | 同:592-595,633-635 | done | ce872f3..21bd67e/D37 | same | phase3 完了段2 |
| X1A-72 | auditor 実体化 | 同:665-667,700-703 | done | bd17b3e..0e7e1f0/D38 | same | phase3 完了段3 |
| X1A-73 | diff quarantine 実装 | 同:701-702,715-718,760-766 | done | 6359aa5; 同:770-798 | same | phase3 完了段4 |
| X1A-74 | coder リーク制御 | 同:715-718,735-737 | done | D39/06e4847; docs/phase3.md:428-437 | same | phase3 残存リスクに部分保証 |
| X1A-75 | planner-v4 定義・起動 | 同:724,760-765 | done | 54f5ae8,06e4847 | merged-from | phase3 完了段4 |
| X1A-76 | mutation-red 汎用gate | 同:701-702,718,817-819 | done | 744f51b/D39; docs/phase3.md:463-466 | merged-from | phase3 残存リスク |
| X1A-77 | 実LLM複数iteration loop | 同:724,830-832,898-901 | done | d862da3/8a3911b; 同:1010-1013 | merged-from | phase3 完了段4 |
| X1A-78 | lock経路編集面拡張 | 同:1018-1019,1054-1056 | done | 0ead69b; 同:1081-1085 | same | phase3 完了段5 |
| X1A-79 | git worktree隔離 | 同:1054-1056,1087 | done | 28e8f93/D40 | same | phase3 完了段5 |
| X1A-80 | sort-strategy 起動 | 同:1054-1056,1087,1114 | done | ba37bf6,5cc693b | merged-from | phase3 完了段5 |
| X1A-81 | 旧段6主実験・delta_pct live化 | 同:830-832,898-901 | superseded(by) | D52縮小後S'不成立、07-14戦略改訂; docs/phase3.md:23-29 | superseded | なし |
| X1A-82 | ultracode 常時オン見直し | 同:608-609 | blocked(human) | 未決着の直接記録のみ | same | なし |
| X1A-83 | fan-out 3本以上規則 | 同:608-609 | blocked(human) | 未決着の直接記録のみ | split-into child | なし |
| X1A-84 | submodule 028f34d/d706650 push | 同:698,721,768,800,834,903,1182 | done | 同:1186-1188 | merged-from | なし |
| X1A-85 | D39決定1 wording訂正 | 同:818-819,834-835,903-904 | blocked(human) | docs/decisions.md:1066-1077 は未訂正 | merged-from | なし |
| X1A-86 | wiring campaign dir git clean | 同:893-896,903-904,954 | superseded(by) | d862da3で正規追跡対象としてcommit; 同:982-985 | superseded | なし |
| X1A-87 | 未コミットCLAUDE.md差分判断 | 同:972-976 | done | a14c133; 同:1015-1016 | same | なし |
| X1A-88 | 凍結apply 24件 | 同:930-933 | done | d399771; 同:949-950 | same | なし |
| X1A-89 | token severity軸への確度混入修正 | 同:918-920,932-933 | done | 2206e6d; 同:960-966 | split-into child | なし |
| X1A-90 | token 確度三値の揺れ修正 | 同:918-920,932-933 | done | 2206e6d; 同:960-966 | split-into child | なし |
| X1A-91 | fairness機械観測点 | 同:1130-1136,1154-1157 | deferred(trigger) | docs/phase3.md:468-475 | same | phase3 残存リスク |
| X1A-92 | CCBENCH_SORT_VARIANT flag | 同:1135-1136 | done | 5cc693b/D42; 同:1147-1156 | split-into child | phase3 完了段5 |
| X1A-93 | sort template patch | 同:1135-1136 | done | 5cc693b; 同:1149-1151 | split-into child | phase3 完了段5 |
| X1A-94 | permutation保存assert | 同:1135-1136 | done | d706650/5cc693b; 同:1147-1150 | split-into child | phase3 完了段5 |
| X1A-95 | ASan/UBSan positive control | 同:1135-1136 | done | 5cc693b/D42; 同:1151-1154 | split-into child | phase3 完了段5 |
| X1A-96 | sort兄弟driver | 同:1156-1157,1180-1181 | done | c944a1f/D43; 同:1209-1211 | same | phase3 完了段5 |
| X1A-97 | sort variant 1本をcoder loop評価 | 同:1180-1181 | done | c6e7fba; 同:1217-1261 | same | phase3 完了段5 |
| X1A-98 | D40/D41/D42変更のcommit承認 | 同:1112-1115,1139-1140,1182 | done | 28e8f93,ba37bf6,5cc693b; 同:1186-1188 | merged-from | なし |
| X1A-99 | competing-tenant retryable化 | 同:661-662 | rejected(reason) | model.py:100-105 は実競合をterminalとする | same | なし |
| X1A-100 | abort率の機械帯 | 同:661-662 | rejected(reason) | D37: docs/decisions.md:935-941,959-961 | same | なし |
| X1A-101 | reason-only第3アーム | 同:661-662 | superseded(by) | 旧段6/S'実験が不成立後に戦略改訂; phase3.md:23-29 | same | なし |
| X1A-102 | Shinka novelty bonus | 同:854-856 | rejected(reason) | 同行で「着手はしない (規律5、基質が先)」 | split-into child | なし |
| X1A-103 | Shinka全書換えsplice | 同:854-856 | rejected(reason) | 同上 | split-into child | なし |
| X1A-104 | Shinka段4中立上乗せ4件 | 同:854-856 | rejected(reason) | 同上 | split-into child | なし |
| X1A-105 | auditorへ直接Write付与 | 同:701-702,713-718 | rejected(reason) | D39: docs/decisions.md:1116-1125 | same | phase3にread-only裁定 |

#### X1b_report.md

## 状態判定表 (全原子項目)

表中 `W` = `docs/archive/worklog-phase3-0702-0713.md`。

| id | 項目要約 | 出所 file:line | 状態 | 根拠 (file:line/commit) | 対応関係 | live carrier |
|---|---|---|---|---|---|---|
| X1B-01 | 非SWO comparatorの機械的property test | W:1195-1196,1387-1389 | deferred(trigger) | `docs/phase3.md:228-233` | merged-from | phase3 |
| X1B-02 | sort軸 実LLM iteration 1 | W:1213-1215 | done | `c6e7fba`; W:1217-1261 | same | なし |
| X1B-03 | sort iteration 2でcritic召喚 | W:1257,1263-1264 | rejected(reason) | W:1454-1458; `7dea693` | split-into | なし |
| X1B-04 | critic後の逆方向判定 | W:1263-1264 | rejected(reason) | W:1454-1458 | split-into | なし |
| X1B-05 | sort軸の次proposal | W:1263-1264 | rejected(reason) | W:1454-1458 | split-into | なし |
| X1B-06 | sort機械sweep先行実測 | W:1286-1287,1299-1302 | done | `c8194da`,`ffa383f`; `docs/phase3.md:278-283` | merged-from | なし |
| X1B-07 | planner-v4のRead遮断 | W:1286-1287,1299-1301 | done | `b8c422b`; W:1305-1320 | merged-from | なし |
| X1B-08 | coder入力例の文書地雷除去 | W:1286-1287,1299-1301 | done | `b8c422b`; W:1307-1316 | split-into | なし |
| X1B-09 | 軸提案のループ内化 | W:1286-1287 | done | `docs/phase3.md:305-312`; `d485a48` | same | なし |
| X1B-10 | workload次元の導入 | W:1286-1287 | continued | `docs/phase3.md:327-335` | same | phase3 |
| X1B-11 | 同等性基準の事前定義 | W:1286-1287 | done | W:1294-1297; `95b6a70` | same | なし |
| X1B-12 | protocol別calibration | W:1370-1371,1430-1432ほか | partial(children) | `docs/phase3.md:263-272,395` | merged-from | phase3見送り台帳 |
| X1B-13 | related-work欠落埋め | W:1370,1394-1396 | done | W:1398-1427; `docs/phase3.md:284-290` | merged-from | なし |
| X1B-14 | Polyjuice/NeurCC実測比較 | W:1411-1418,1430-1432 | rejected(reason) | W:1434-1443; `bc79604` | same | phase3に再判断trigger |
| X1B-15 | 回転速度の主張を8c後に評価 | W:1445-1447 | deferred(trigger) | `docs/phase3.md:28,351-355` | same | phase3 |
| X1B-16 | 軸オンボーディング手順のテンプレ化 | W:1467-1468 | done | `27f6345`; W:1470-1490 | same | なし |
| X1B-17 | axis-proposer設計 | W:1491-1493 | done | `5ecca35`; W:1495-1518 | same | なし |
| X1B-18 | axis-proposer実体化 | W:1520-1524,1534-1535 | done | `46d24c9`; W:1537-1549 | merged-from | なし |
| X1B-19 | 既存軸台帳の独立成果物化 | W:1550-1552 | unresolved | 専用成果物・裁定なし。S-1 freezeはunrelated | unrelated | なし |
| X1B-20 | axis-proposer n=1実証 | W:1535,1561-1565 | done | `62be4f6`; W:1567-1589 | merged-from | なし |
| X1B-21 | 既開通領域への偏りを次回n増加時も観測 | W:1574-1578 | continued | `docs/phase3.md:322-323` | same | phase3 |
| X1B-22 | n=1提案3件の人間採否 | W:1591-1597 | done | W:1599-1606 | same | なし |
| X1B-23 | 採用軸の段階B独立再導出・レビュー | W:1596-1597,1608-1611 | done | `a274063`; W:1613-1631 | merged-from | なし |
| X1B-24 | SOURCE_RELの実コード裏取り | W:1609-1611 | done | W:1615-1629 | split-into | なし |
| X1B-25 | trigger-gating骨格patch | W:1633-1636,1651-1653 | done | `4bced5c..cbcbe1d`; W:1678-1688 | merged-from | なし |
| X1B-26 | identity実証 | W:1633-1636 | done | `4bced5c..cbcbe1d` | split-into | なし |
| X1B-27 | 要因記録positive control | W:1633-1636 | done | `4bced5c..cbcbe1d`; D49 | split-into | なし |
| X1B-28 | 軸定数ブロック | W:1633-1636 | done | `4bced5c..cbcbe1d` | split-into | なし |
| X1B-29 | 偵察firewall | W:1651-1653 | done | `4bced5c..cbcbe1d`; D49 | split-into | なし |
| X1B-30 | auditorギャラリー型16追記 | W:1635-1636 | done | W:1638-1645 | same | なし |
| X1B-31 | 資金提供元回答の送付判断 | W:1674-1676 | unresolved | 後続記録・carrierなし | split-into | なし |
| X1B-32 | ソルバ・量子質問への回答作成 | W:1674-1676 | unresolved | 後続記録・carrierなし | split-into | なし |
| X1B-33 | ftruncate-xor insightの完了訂正 | W:1670-1672 | done | `docs/archive/worklog-phase3-0714-0716.md:410-415`; `docs/phase3.md:396-398` | same | なし |
| X1B-34 | p2_2動作点での要因頻度実測 | W:1699-1701 | done | `8c97b6a`; `docs/decisions.md:1841-1844` | split-into | なし |
| X1B-35 | read-heavy floor較正 | W:1699-1701 | done | `540b797`; `docs/decisions.md:1844-1846` | split-into | なし |
| X1B-36 | adaptive Backoff連成の凍結 | W:1699-1701 | done | `docs/decisions.md:1845-1846` | split-into | なし |
| X1B-37 | 恒等gate対照 | W:1699-1701 | done | `docs/decisions.md:1847-1849` | split-into | なし |
| X1B-38 | D生死判定後のE段着手判断 | W:1702,1788-1794 | done | W:1839-1841; `b539b33..064af01` | merged-from | なし |
| X1B-39 | roadmap修正6点 | W:1717-1719 | done | W:1721-1727 | same | なし |
| X1B-40 | token-management-strategyのarchive移動判断 | W:1746-1747 | rejected(reason) | W:1767「据え置き決着済み」 | same | なし |
| X1B-41 | CLAUDE.md圧縮 | W:1747-1749 | done | W:1754-1767; `ea76de4` | split-into | なし |
| X1B-42 | auditor.md圧縮 | W:1748-1749 | done | W:1754-1767 | split-into | なし |
| X1B-43 | 同居benchを今後の計測で監視 | W:1785-1786 | done | `docs/phase3-s8a-trigger-runbook.md:22-24`; 後続実運用 `docs/archive/worklog-phase3-0714-0716.md:692-694` | same | なし |
| X1B-44 | abort WAL payloadへ例外要約 | W:1788-1790 | done | `84ccab7`; W:1820-1824 | same | なし |
| X1B-45 | E段ロール・loop driver実体化 | W:1792-1794 | done | `b539b33..064af01` | same | なし |
| X1B-46 | E段provenance記録義務の実装先確定 | W:1808-1818 | done | `064af01`; W:1837-1850 | same | なし |
| X1B-47 | coder定義草案の承認・配置 | W:1855-1861 | done | W:1863-1868 | same | なし |
| X1B-48 | F段iteration 1 E2E | W:1867-1872 | done | `d485a48`; W:1916-1934 | same | なし |
| X1B-49 | extra-sourceを毎iteration再指定する回避策 | W:1912-1913,1935-1937 | superseded(by X1B-50) | W:2130-2132 | same | なし |
| X1B-50 | provenance path後勝ちunion恒久修正 | W:1935-1937,1975-1976 | done | `80b21de`; W:2127-2132 | merged-from | なし |
| X1B-51 | hole内コメントの機械reject | W:1905-1907,1975-1976 | unresolved | `diff_quarantine.py:44-53`; `test_diff_quarantine.py:430-437` が現在もpassを固定 | merged-from | なし |
| X1B-52 | F段runbookのabort>0確認2行 | W:1907,1975-1976 | unresolved | `docs/phase3-s8a-trigger-runbook.md:14-31,78-92` に不在 | merged-from | なし |
| X1B-53 | headline 3択の人間裁定 | W:1910-1914 | done | W:1959-1962; D52 | same | なし |
| X1B-54 | 動作点再ホストかクローズかの裁定 | W:1948-1950,1981-1982 | done | `docs/archive/worklog-phase3-0714-0716.md:80-81`; `docs/phase3.md:318-321` | merged-from | なし |
| X1B-55 | auditor proposed_tests採否 | W:1938-1950,1981-1982 | deferred(trigger) | `docs/phase3.md:320-321` | merged-from | phase3 |
| X1B-56 | 独立再命名canary | W:1978-1980 | done | `623aab9`; W:1984-1999 | same | なし |
| X1B-57 | canary一致判定の人間追認 | W:2001-2003 | done | `5d8ee4f`; W:2035-2040 | same | なし |
| X1B-58 | S2/C4/C5のn・成功閾値確定 | W:1979-1980,2006-2008 | done | W:2010-2025 | merged-from | なし |
| X1B-59 | C5空diagnostics契約 | W:2031-2033 | done | W:2071-2073,2082-2083; `391fda4` | split-into | なし |
| X1B-60 | 射影入力の凍結 | W:2031-2033 | done | W:2066-2069; `54c4051` | split-into | なし |
| X1B-61 | C4抽出列の実行・凍結 | W:2031-2033 | done | W:2076-2077,2153-2164; `54c4051` | split-into | なし |
| X1B-62 | 由来盲検採点の運用実装 | W:2031-2033 | done | W:2076-2077,2162-2164; `54c4051` | split-into | なし |
| X1B-63 | axis-proposer契約追記の承認 | W:2071-2077 | done | W:2082-2083 | split-into | なし |
| X1B-64 | master seedの人間確定 | W:2071-2077,2094-2101 | done | W:2153-2155 | merged-from | なし |
| X1B-65 | 60ラウンド実走承認 | W:2071-2077,2094-2101 | done | W:2150-2155 | merged-from | なし |
| X1B-66 | 採点prompt・匿名化規則の凍結 | W:2076-2077,2100-2102 | done | W:2085-2093; `54c4051` | split-into | なし |
| X1B-67 | 60ラウンド提案実走 | W:2076-2077,2100-2102 | done | W:2148-2164; `54c4051` | split-into | なし |
| X1B-68 | 混合順採点 | W:2076-2077,2100-2102 | done | W:2162-2164; `54c4051` | split-into | なし |
| X1B-69 | tally・名目p集計 | W:2076-2077,2100-2102 | done | W:2162-2164; `54c4051` | split-into | なし |
| X1B-70 | 採点reason人間監査 | W:2101-2102,2171-2184 | done | W:2222-2234 | merged-from | なし |
| X1B-71 | 60ラウンド探索的内容分析 | W:2175-2182 | done | `fcf9ab3`; W:2188-2212 | same | なし |
| X1B-72 | S-2/S-3報告文言確定 | W:2183-2184,2215-2216,2241 | done | `82c42d2`; W:2245-2258 | merged-from | なし |
| X1B-73 | CLAUDE作業手順5へのprovenance/要旨規律配線 | W:2121-2122 | partial(children) | `docs/failures.md:122-129` に実質一部、CLAUDE.mdへの約束された1行は不在 | same | なし |
| X1B-74 | Phase 1〜2 failures 4件の回収 | W:2113-2116 | deferred(trigger) | `docs/failures.md:284-287` | same | なし（許可carrier外のfailures台帳には残存） |
| X1B-75 | 将来の盲検設計で入力構成への言及禁止 | W:2207-2209 | unresolved | 後続正本・agent定義に実装なし | same | なし |
| X1B-76 | c1「軸」の作用点/政策集合定義を明文化 | W:2235-2236 | unresolved | `output/s6-rounds/audit-sheet.md:743` は教訓記録のみ | same | なし |
| X1B-77 | S-1サンプル設計4点確定 | W:2259-2263,2271-2273 | done | `cbf32d3`,`1fe126e`; `docs/phase3.md:242-243` | merged-from | なし |
| X1B-78 | S-1直接比較driver実装 | W:2259-2263,2271-2273 | done | `7b0983b`; `docs/phase3.md:244-245` | merged-from | なし |
| X1B-79 | 既知軸基準点の機械freeze | W:2259-2263,2271-2273 | done | `80b3010`,`15fcc08`; `docs/phase3.md:244-245` | merged-from | なし |
| X1B-80 | 検証相(seed×N/長extime)実装 | W:2259-2263,2271-2273 | done | `docs/phase3.md:246-247`; `docs/archive/worklog-phase3-0714-0716.md:603-624` | merged-from | なし |
| X1B-81 | 対象別between-run floor再実測 | W:2262-2263,2273 | done | `docs/phase3.md:248-249` | split-into | なし |
| X1B-82 | sort read-heavy欠測補充 | W:2262-2263,2273 | done | `docs/phase3.md:248-249` | split-into | なし |
| X1B-83 | S-1直接比較本走 | W:2271-2273 | done | `694c32d`; `docs/phase3.md:250-255` | same | なし |
| X1B-84 | 07-13成果のorigin push | W:2265-2268 | done | `docs/archive/worklog-phase3-0714-0716.md:728`; 対象commit群は現 `origin/main` のancestor | same | なし |
| X1B-85 | ランダム変異生成器・生成分布 | W:1336-1338 | deferred(trigger) | `docs/decisions.md:1576-1578`; `docs/phase3.md:263-270` | same | phase3 |
| X1B-86 | docs/phaseディレクトリ化 | W:1381-1384 | rejected(reason) | 同行にコスト理由と再考triggerを直接記録 | same | なし |

#### X2_report.md

## 状態判定表 (全原子項目)
| id | 項目要約 | 出所 file:line | 状態 | 根拠 (file:line/commit) | 対応関係 | live carrier |
|---|---|---|---|---|---|---|
| X2-01 | S-1 を安価に完走 | archive:26-28,34-36 | done | archive:678-687; commit 694c32d | split-into（提言5点） | なし（terminal） |
| X2-02 | LLM vs machine 分離実証を中心価値から外す | archive:26-28,34-36 | done | archive:71-74 | split-into（提言5点） | なし |
| X2-03 | 8b・層3へ投資を移す | archive:26-28,34-36 | done | archive:73-83; phase3.md:27-29 | split-into（提言5点） | なし |
| X2-04 | roadmap/物語を再構成 | archive:26-28,34-36 | done | archive:65-86 | split-into（提言5点） | なし |
| X2-05 | 手続き固定費の運用上限を導入 | archive:26-28,34-36 | done | archive:84-86 | split-into（提言5点） | なし |
| X2-06 | origin へ push | archive:31,58 ほか各「push は人間判断」 | done | docs/worklog.md:225-228（2026-07-17 force-push 完了） | merged-from | なし |
| X2-07 | 8a 軸を高競合へ再ホストするか現動作点を閉じる | archive:31,36（参照元 0702-0713:1948-1954） | superseded(by 低競合クローズ＋8b前向き設計) | phase3.md:318-321 | split-into（07-12(6)持ち越し） | なし |
| X2-08 | 自由形述語の fail-safe 意味検査を採否 | archive:31,36（参照元 0702-0713:1938-1950） | deferred(trigger 軸再利用) | phase3.md:320-321 | split-into（auditor proposed_tests） | phase3.md:320-321 |
| X2-09 | stock-equivalence 観察器を採否 | 同上 | deferred(trigger 軸再利用) | phase3.md:320-321 | split-into | phase3.md:320-321 |
| X2-10 | 骨格改竄 red を採否 | 同上 | deferred(trigger 軸再利用) | phase3.md:320-321 | split-into | phase3.md:320-321 |
| X2-11 | 禁止識別子 red を採否 | 同上 | deferred(trigger 軸再利用) | phase3.md:320-321 | split-into | phase3.md:320-321 |
| X2-12 | `extra_sources` を iteration 間で union 保持 | archive:31,36（参照元 0702-0713:1935-1937） | done | commit 80b21de; test `test_provenance_header_unions_extra_sources_across_rewrites` | split-into | なし |
| X2-13 | 07-12(6) の「ほか should-fix」着手順を裁定 | archive:31,36 | unresolved | 後続全 worklog/phase/decisions/handoff/git log に対象集合・処分なし | split-into | なし |
| X2-14 | S-1 サンプル設計4点を確定・承認 | archive:91,134,353-354,381-384 | done | archive:363-374,480-488; commits cbf32d3,1fe126e | merged-from | なし |
| X2-15 | S-1 直接比較 driver を実装 | archive:91,134,381-384,491-493 | done | archive:526-543,611-617; commit 7b0983b | merged-from | なし |
| X2-16 | 既知軸基準点を machine-readable freeze | archive:91,134,363-378 | done | archive:363-378; commit 80b3010 | merged-from | なし |
| X2-17 | 検証相・統計・校正機構を実装 | archive:91,134,381-384,491-493 | done | archive:500-569,611-624; commits 5c70182,8750433,8a8399b | merged-from | なし |
| X2-18 | sort read-heavy 欠測を補充 | archive:93,135-136,654-656 | done | phase3.md:248-252 | merged-from | なし |
| X2-19 | 対象別 floor を再実測 | archive:93,136,654-656 | done | phase3.md:248-249 | merged-from | なし |
| X2-20 | S-1 本走・report を完了 | archive:93,136,637,654-656 | done | archive:678-687; phase3.md:250-252; commit 694c32d | merged-from | なし |
| X2-21 | Holm 族4判定と S' 文言を確定 | archive:684,708-710 | done | archive:720-724; commit e5dfa84 | same | なし |
| X2-22 | 8b 前向き設計・holdout/全件報告を発効 | archive:92,135,708-711 | done | archive:725-729; commit 72b294e | merged-from | なし |
| X2-23 | descriptor 射影＋二段検証 gate | archive:731-735 | done | archive:754-756; commit 6a975a1 | split-into（8b実装段階） | なし |
| X2-24 | selector 役・入力 builder を実装 | archive:732-735,775-777,789-791 | done | archive:794-813; commits 1357461,2f8eda5 | split-into（実装＋実測親） | なし |
| X2-25 | oracle 評価 driver/report/judge を実装 | archive:734-735,775-778,789-791 | done | archive:794-813; commits b6ab942,31f20fb,1e9f740 | split-into（実装＋実測親） | なし |
| X2-26 | oracle を実測・完走 | archive:777-778,791,823-827 | continued | phase3.md:66-70 | split-into（親は partial(children): X2-24/X2-25 done, X2-26 continued） | phase3.md:66-70 |
| X2-27 | 層3 schema＋最小 renderer/E2E | archive:92,135,676-687 | done | archive:686-687; phase3.md:359-360; commits d6085a9,2230edf | merged-from | なし |
| X2-28 | 層3 renderer を sweep campaign へ拡大 | archive:708-712,731-736 | done | archive:757-761; phase3.md:360-363; commit 4204013 | split-into（複合親） | なし |
| X2-29 | 層3の機序仮説層原料を配線 | archive:708-712,731-736 | deferred(trigger 次のloop再走/v3) | archive:761-762; phase3.md:364-370 | split-into（親は partial(children): X2-28 done, X2-29 deferred） | phase3.md:359-370 |
| X2-30 | 8c セッション非依存駆動を必要性確認後に判断 | archive:75-76,93,136 | deferred(trigger 8b＋層3 1 cycle後も運営が律速) | phase3.md:28-29,351-357 | merged-from | phase3.md:28-29,351-357 |
| X2-31 | cross-protocol/b2 移植を8b・層3後に再判断 | archive:75-76 | deferred(trigger 8b＋層3後) | phase3.md:28-29,76 | same | phase3.md:28-29 |
| X2-32 | bench-first pipeline を実装 | archive:60-62,435-437 | done | archive:442-451; commits 67c699b..0115290 | split-into（bench-first完了条件） | なし |
| X2-33 | bench-first consumer 監査・修正 | archive:61-62,435-437 | done | archive:446-451; commits 0a7304c,0a1374b,d3b7249 | split-into | なし |
| X2-34 | bench-first testsを完備 | archive:61-62,435-437 | done | archive:446-451; commits f585e30,8323386 | split-into | なし |
| X2-35 | bench-first positive control を実発火 | archive:61-62,435-437 | done | archive:452-453; phase3.md:32-34 | split-into | なし |
| X2-36 | bench-first 初回 ablation | archive:474-475,494-495 | continued | phase3.md:34,344-347 | split-into（複合親） | phase3.md:32-36,344-347 |
| X2-37 | Best-of-∞ 型逐次停止を別設計・別裁定 | archive:400-402,405-407,422,433,438 | deferred(trigger 別設計・裁定) | phase3.md:35-36,347-350 | merged-from | phase3.md:35-36,347-350 |
| X2-38 | native profiles を dormant/blocked 化 | archive:149-151 | done | archive:154-166; commits f72886e,b398b85 | same | なし |
| X2-39 | checker body policy/YAML/runtime controlsを修理 | archive:151 | done | archive:188-216; commit c9e2118 | split-into | なし |
| X2-40 | nested tool exact allowlist＋許可外 event 負例 | archive:185,202,219 | blocked(owner=Codex platform/tool surface) | decisions.md:2213-2219; `.codex/agents/README.md:12-19` | merged-from | なし（現行状態文書は指定 carrier 外） |
| X2-41 | Codex hook adapter＋parity test | archive:126-127 | deferred(trigger 安全なtool-input契約) | decisions.md:2081-2085 | same | なし |
| X2-42 | Codex adapter 差分を独立レビュー・commit | archive:168-170,183-186 | done | archive:188-216; commits f72886e,c9e2118 | merged-from | なし |
| X2-43 | 全12 roleを static adapterへ移植 | archive:172-181 | done | archive:205-216; commit f72886e | same | なし |
| X2-44 | CLAUDE.md を追加スリム化 | archive:238-239 | done | archive:260-267; decisions.md:2239; D57 commit | same | なし |
| X2-45 | 共有相手決定時に review snapshot 範囲を切る | archive:256-257 | deferred(trigger 共有相手決定) | 後続 carrier/成果物なし | same | なし |
| X2-46 | task-class gate を実装 | archive:286-287 | done | archive:289-304; commits 3a913e0,3bf7262 | split-into（三段導線） | なし |
| X2-47 | phase3 hot path を分離 | archive:287,306-308,326-328 | done | archive:330-342; commit 9e8daae | split-into | なし |
| X2-48 | archive到達性lint＋history-only化 | archive:287,306-308,326-328 | done | archive:330-345; commit d855a68 | split-into | なし |
| X2-49 | locked `strategy-review-freeze` worktreeを処分判断 | archive:348-349 | unresolved | 後続 terminal 記録なし。現時点では worktree/dir 不在 | same | なし |
| X2-50 | S-1 known-axes freezeを再凍結 | archive:461-467,470-473 | done | archive:480-489; commit 15fcc08 | same（measurement freezeとは unrelated） | なし |
| X2-51 | pin literal 4 driverを修正 | archive:474-475,494-495 | rejected(reason 再走予定なしの歴史的driverは保持) | archive:620-624; commit 8aa579e | split-into（親は partial: ablation=X2-36 continued, pin=X2-51 rejected） | なし |
| X2-52 | measurement freeze generator を実装 | archive:498-514 | done | archive:611-614; commit 55d0d55 | same（known-axes再凍結とは unrelated） | なし |
| X2-53 | measurement freeze 実体を生成・commit | archive:521-523,545-547,574-576,598-600,634-635 | done | archive:678-687; commit 4b9d86e | merged-from | なし |
| X2-54 | 層別統計を実装 | archive:491-493 | done | archive:611-617; commit 5c70182 | same | なし |
| X2-55 | extime 校正 driver を実装 | archive:491-493 | done | archive:611-614; commit 8750433 | same | なし |
| X2-56 | extime 校正を実走し値を凍結 | archive:634-636,654-655 | done | archive:678-687; commit aa1bf50 | same | なし |
| X2-57 | external/ccbench のテスト残骸を正規復旧 | archive:574-575,598-600 | done | archive:625-628 | merged-from | なし |
| X2-58 | B1/A/B2a/B2bを統合監査・commit | archive:521-523,545-548,574-576,598-601 | done | archive:603-632; commits ddea4bd..48be6c4 | merged-from | なし |
| X2-59 | S-1 4 roleを `--dry-run` 照合 | archive:545-547,598-600,637 | done | archive:678-679（前夜の次の一手1〜3を完遂） | merged-from | なし |
| X2-60 | ftruncate-xor還元状態をPR #116 merge済みへ訂正 | archive:410-423 | done | archive:412-415; phase3.md:396-398 | same | なし |
| X2-61 | verbal-diff還流を将来敵対レビュー | archive:400-402 | superseded(by v3機序原料の構造化配線設計) | phase3.md:364-373 | superseded | なし |
| X2-62 | `nearest-read-ratio-v1` 束縛規則を承認 | archive:749-753,772-775 | done | archive:781-787 | same | なし |
| X2-63 | holdout freeze を生成・verify | archive:773-775 | done | archive:783-786; commit 911f6bc | same | なし |
| X2-64 | 二波監査全文を凍結 | archive:814-815,823-829 | superseded(by 消失記録＋再構成) | archive:901-929; phase3.md:71-75; commit d1543f4 | superseded | なし |
| X2-65 | §9 全8項をユーザー承認・発効 | archive:804-808,823-825,894-895,934-947 | done | archive:1000-1014; phase3.md:43-45 | merged-from | なし |
| X2-66 | floor/budget 実測envを確定 | archive:894-898,939-964 | done | archive:1000-1013; docs/worklog.md:619-626 | merged-from | なし |
| X2-67 | floor protocol案を作成・裁定 | archive:1016-1020,1044-1047 | done | docs/worklog.md:33-69,332-454; phase3.md:49-54 | merged-from | なし |
| X2-68 | strict v2 verifier 本体を実装 | archive:934-938,965-968,993-997,1016-1019,1048 | done | docs/worklog.md:434-513; commits fad6f0a..23fa0db | merged-from | なし |
| X2-69 | trusted prediction runnerを実装 | archive:936-938,965-968,993-997,1017-1019 | done | archive:1029-1033; commit ff5f61c | merged-from | なし |
| X2-70 | R6 resume拒否を強化 | archive:936-938,953-968,993-997,1017-1019 | done | archive:1029-1037; commit ff5f61c | merged-from | なし |
| X2-71 | F3 pgrepのpath依存を修正 | archive:983-986,993-997,1017-1019 | done | archive:1029-1033; commit ff5f61c | merged-from | なし |
| X2-72 | R5 truth table・結合judgeを実装 | archive:936-938,993-997,1008-1010,1017-1019 | done | archive:1029-1033; commit ff5f61c | merged-from | なし |
| X2-73 | A3-3単一block/A3-4 status・rcを裁定・実装 | archive:926-929,934-938,965-968,993-997 | done | archive:1008-1010,1029-1038 | merged-from | なし |
| X2-74 | protocol JSONを実凍結 | archive:1020,1044-1047 | continued | phase3.md:66-68; docs/worklog.md:751-754 | split-into（wave2後続） | phase3.md:66-68 |
| X2-75 | selector予測を封印・6セル実実行 | archive:824-825,965-969,1020,1044-1047 | continued | phase3.md:66-68; docs/worklog.md:751-754 | merged-from | phase3.md:66-68 |
| X2-76 | floor/budgetを再実測 | archive:826-827,939-964,1020,1044-1047 | continued | phase3.md:66-70; docs/worklog.md:751-755 | merged-from | phase3.md:66-70 |
| X2-77 | holdout freeze v2を再凍結 | archive:826-827,936-938,965-969,1020,1044-1048 | continued | phase3.md:69-70 | merged-from | phase3.md:69-70 |
| X2-78 | Pegasus専用 env-tag/env_contractを設計・登録 | archive:842-843,869-871,896-898 | done | phase3.md:61-65; docs/worklog.md:708-733; commits 950757e..0b4f67c | split-into（Pegasus正式利用親） | なし |
| X2-79 | Pegasusで再calibration | archive:842-843,869-871 | done | docs/worklog.md:722-731（attempt 10 accepted, CV 1.17%） | split-into | なし |
| X2-80 | Pegasusのbetween-run noise floorを取得 | archive:842-843,869-871 | continued | docs/worklog.md:732-738; phase3.md:66-70 | split-into | phase3.md:66-70 |
| X2-81 | roadmap §5をenv-tag中心へ改訂 | archive:860-863,869-871 | done | archive:873-888; commit 00624d4 | split-into（Pegasus条件項目） | なし |
| X2-82 | 旧実走runbookの単独性gateを共有環境対応へ置換 | archive:862-867,869-871 | done | archive:873-888; commits b1be5e0,92fe5ca | split-into | なし |
| X2-83 | `worktree-s8b-ruling-prep`をmainへ取り込む | archive:991-998,1021,1049 | done | commit ff5f61c は現行 main 80343a2 の祖先 | merged-from | なし |
| X2-84 | 各時点のcommit/push判断を人間へ引き渡す | archive:93,136,169,184,202,219,270,307,327,352,385,408,423,438,476,496,524,548,577,601,638,657,674,713,737,779,792,829,899,941,998,1021,1049 | superseded(by 後続の最新push判断) | docs/worklog.md:225-231で一度完了。以後の新規push判断は末尾(5)へ更新され、ユーザー指定により本掃引対象外 | merged-from/superseded | なし |
| X2-85 | Codex委譲でmodel/reasoningを毎回明示 | archive:700-705 | superseded(by 機械化されたmodel/effort規約) | docs/worklog.md:516-520; decisions.md:D61（2325-2345） | superseded | なし |

#### X3_report.md

## 状態判定表 (全原子項目)

| id | 項目要約 | 出所 file:line | 状態 | 根拠 (file:line/commit) | 対応関係 | live carrier |
|---|---|---|---|---|---|---|
| X3-01 | F1 裁定 | `docs/worklog.md:67` | done | `3d96f57`; `docs/worklog.md:337-344` | same | なし |
| X3-02 | F2 裁定 | `:67,350-351` | done | `b7b38da`; `:356-363` | merged-from | なし |
| X3-03 | F3 裁定 | `:67,350` | done | `b7b38da`; `:356-363` | merged-from | なし |
| X3-04 | F4 裁定 | `:67,350` | done | `cdb16c0`; `:364-367` | merged-from | なし |
| X3-05 | F5 裁定 | `:67,350,372` | done | `05244bf`; `:377-382` | merged-from | なし |
| X3-06 | F6 裁定 | `:67,350,372,386,429` | done | `bfa0f08`; `:434-447` | merged-from | なし |
| X3-07 | F7 裁定 | `:67,350,372,386,429` | done | `bfa0f08`; `:434-447` | merged-from | なし |
| X3-08 | n_sessions=8 確定 | `:46-47,67` | done | `s8b_approved.py:27-30`; `3d96f57` | split-into | なし |
| X3-09 | reps=5 確定 | `:46-47,67` | done | `s8b_approved.py:27-30`; `3d96f57` | split-into | なし |
| X3-10 | 2 block + 1800s gap | `:43,46-47,68` | rejected(reason) | F1 裁定で廃止、`docs/worklog.md:342-344` | same | なし |
| X3-11 | wired floor 3% | `:46-47,67` | done | F1 維持、`:342-344`; `s8b_approved.py:31-35` | split-into | なし |
| X3-12 | scale ±10% | `:46-47,67` | done | `s8b_approved.py:31-33`; consumer `d7ac2d7` | split-into | なし |
| X3-13 | retry 通算 2 | `:46-47,67` | done | `s8b_approved.py:27-30`; `b87bb1e` | split-into | なし |
| X3-14 | master_seed 確定 | `:372,387,429,453,510` | done | `f49cfef`; `docs/worklog.md:619-621` | merged-from | なし |
| X3-15 | env_tag=pegasus 確定 | `:67,326,350,372,387,429,453,510` | done | `f49cfef`; `:622-626` | merged-from | なし |
| X3-16 | B-1 NaN strict 化裁定 | `:302-306,326-330,350,372,386,429` | done | `bfa0f08`, `8d3642e` | merged-from | なし |
| X3-17 | B-2 probe 自 PID 限定裁定 | `:176-178,197,326-327,350,372,386,429` | done | `bfa0f08`, `babef37` | merged-from | なし |
| X3-18 | retry を round 末尾へ読み替える追認 | `:416-419,429` | done | `bfa0f08`; `:436-447` | same | なし |
| X3-19 | settle timeout 非該当の追認 | `:416-419,429` | done | `bfa0f08`; `:436-447` | same | なし |
| X3-20 | strict-v2 §5 (i)〜(vii) 裁定 | `:480-487,510,572,606-608` | done | `fc12788`; `:639-645` | merged-from | なし |
| X3-21 | §5-(ix) 裁定 | `:562-565,572-575,607-608` | done | `4521b72`; `:582-600` | merged-from | なし |
| X3-22 | §8.5 裁定 | `:600,606-608` | done | `fc12788`; `:643-645` | same | なし |
| X3-23 | §10.2 追認 5 項 | `:677,682-683,736` | done | `25bbbe7`; `:743-749` | merged-from | なし |
| X3-24 | §5-(viii) 残存限界の最終承認 | `:646` | deferred(trigger=floor 実測直前) | terminal 証拠なし | split-into | なし |
| X3-25 | protocol JSON 実凍結 | `:68,352-353,430,453,511,574,653,685,737,752` | continued | `docs/phase3.md:66-68` | merged-from | `phase3:66-68` |
| X3-26 | selector 予測封印 | `:68,430,453,511-513,574-575,653-654,685-686,737-738,752` | continued | `docs/phase3.md:66-68` | merged-from | `phase3:66-68` |
| X3-27 | floor 実測 | 同上 | continued | `docs/phase3.md:66-70` | merged-from | `phase3:66-70` |
| X3-28 | holdout freeze v2 再凍結 | `:69,107-121,198` | continued | `docs/phase3.md:69-70` | merged-from | `phase3:69-70` |
| X3-29 | strict v2 verifier 本体 | `:69,179-183,328-330,430-431,451-452` | done | `d0c947a`; `docs/phase3.md:54-57` | merged-from | なし |
| X3-30 | v2 候補生成 | `:513,575,654,686` | continued | `docs/phase3.md:66-68` | merged-from | `phase3:66-68` |
| X3-31 | 候補のユーザー承認 | `:513,575,654,686` | continued | `docs/phase3.md:66-68` | split-into | `phase3:66-68` |
| X3-32 | active pointer 発行 | `:513` | continued | `docs/phase3.md:66-68` | split-into | `phase3:66-68` |
| X3-33 | oracle 実走 | `:513,575,654,686` | continued | `docs/phase3.md:66-68` | merged-from | `phase3:66-68` |
| X3-34 | oracle 側 binary hash 照合 | `:70-71,179-183,328-330` | done | `a87c107`; `s8b_floor_campaign.py:1623-1629` | merged-from | なし |
| X3-35 | probe fail-open 是正・共有切替 | `:70-71,179-183,328-330` | done | `e419c55`, `babef37` | merged-from | なし |
| X3-36 | manifest per-pair 追随 | `:70-71,179-183,328-330` | done | `8d3642e` | merged-from | なし |
| X3-37 | materialization 共通抽出 | `:70-71,179-183` | done | `50e65be`, `d4cbf91` | same | なし |
| X3-38 | bench_max_rounds=1 束縛 | `:179-180,328-330` | done | `8d3642e`; `s8b_oracle_manifest.py:358-361` | same | なし |
| X3-39 | G5'/ExecutionEnvironmentContract | `:179-180,328-330,373` | done | `28ccb07`, `26a9ad6`; `docs/phase3.md:61-64` | merged-from | なし |
| X3-40 | binding 検証 issue-code 統合 | `:181-183,296-313,328-330` | done | `d4cbf91`; `docs/phase3.md:58-60` | merged-from | なし |
| X3-41 | closed-source bundle/source closure pin | `:181-185,296-306,328-330` | done | `de23695`, `d4cbf91` | merged-from | なし |
| X3-42 | trace-disabled build 共有の追加抽出 | `:181-183,307-309` | superseded(by=既存 buildcache primitive + 結線テスト再評価) | `docs/worklog.md:307-309` | superseded | なし |
| X3-43 | 8b descriptor stale 引用の修正 | `:86-89,107-121` | continued | freeze v2 と同枠、`docs/phase3.md:69-70` | merged-from | `phase3:69-70` |
| X3-44 | official 拒否を core API にも適用 | `:86-88` | done | `b87bb1e`; `docs/worklog.md:404-408` | same | なし |
| X3-45 | oracle report の bench-failed abort reason 検査 | `:184-185` | unresolved | `s8b_oracle_report.py:449-453` に欠落 | same | なし |
| X3-46 | probe reason の stage 別写像 | `:184-185` | done | `s8b_oracle_driver.py:410-434` | same | なし |
| X3-47 | 実行 byte の直前再照合 | `:184-185` | done | `s8b_floor_campaign.py:1623-1629`; `a87c107` | same | なし |
| X3-48 | scale gate consumer | `:420-423,430-431` | done | `d7ac2d7` | same | なし |
| X3-49 | G12 enforcement/attestation/cache namespace | `:420-423,489-490,631-632,652,684` | done | `26a9ad6`; `docs/phase3.md:61-64` | merged-from | なし |
| X3-50 | C2-2 launch certificate 発行結線 | `:488-492,511-513` | done | `1eb1ed1`; `docs/worklog.md:553-565` | same | なし |
| X3-51 | launch certificate lineage verifier | `:488-492,511-513,562-575` | done | `d4cbf91`; `docs/phase3.md:58-60` | merged-from | なし |
| X3-52 | reps の run-contract 束縛 | `:488-490` | done | `s8b_approved.py:27-30`; `s8b_floor_contract.py:166-170` | split-into | なし |
| X3-53 | extime の run-contract 束縛 | `:488-490` | unresolved | `s8b_floor_contract.py:185`; `s8b_oracle_manifest.py:354-357` | split-into | なし |
| X3-54 | 各作業 branch の push/PR/merge | `:98,118-119,153-154,195-196,242,266,281,325,354,375,389,432,455,514,537,578,613,632,655,687,706,741,756,780,800` | superseded(by=統合済み local main の最終 push) | merge `9d0ae8d,1d33979,3bd3de0,240d1cc,80343a2`; 最終 live 項目 `docs/worklog.md:823` は除外対象 | merged-from/superseded | `worklog:823`（除外対象） |
| X3-55 | Claude-Session force-push とローカル後始末 | `:210-228` | done | `docs/worklog.md:217-228`; `b24836a` | same | なし |
| X3-56 | 他マシン clone の reset/reclone | `:229` | deferred(trigger=対象 clone 利用時) | terminal 証拠なし | split-into | なし |
| X3-57 | GitHub PR 本文 URL 監査 | `:229-230` | deferred(trigger=GitHub 接続可能時) | terminal 証拠なし | split-into | なし |
| X3-58 | refs/pull の Support GC | `:230-231` | deferred(trigger=完全消去を要求する場合) | terminal 証拠なし | split-into | なし |
| X3-59 | fetch --prune 最終整合確認 | `:230-231` | deferred(trigger=次回実 fetch) | terminal 証拠なし | split-into | なし |
| X3-60 | guard_agent 初回 live 発火確認 | `:534-536` | partial(children=X3-61,X3-62) | 不発を確認、`b6fd37f`; `docs/worklog.md:547-552` | split-into | なし |
| X3-61 | fresh bg session で guard_agent 再検証 | `:576-577,612` | deferred(trigger=新規 bg session) | `hooks/README.md:147-148` | same | なし |
| X3-62 | guard_agent 機械防衛案の裁定 | `:572-573` | deferred(trigger=X3-61 で再度素通り) | `hooks/README.md:149-152` | split-into | なし |
| X3-63 | writable 環境で全走 3 連続 rc=0 | `:699-705` | partial(children=2連続 green、1 flake) | `test-suite-hygiene-survey.md:159` | same | なし |
| ⚠ 訂正 (R2) | X3-63 は `6b9c818` が HEAD 祖先で、受入時点に 3 連続全走 rc=0・各 1899 passed の記録があるため完了。後発 flake は B-051 の独立課題 | — | done | `6b9c818`; `2026-07-18_env-contract-pegasus-consultations.md:1207` 付近 | レビュー訂正注記 | なし |
| X3-64 | patchharness 修正の commit | `:706` | done | `6b9c818` | split-into | なし |
| X3-65 | s1 freeze テストの submodule 読取隔離 | `:739-740,755` | unresolved | 後続 terminal 証拠なし | split-into | なし |
| X3-66 | patch 適用を tmp worktree へ隔離 | `:739-740,755` | unresolved | 後続 terminal 証拠なし | split-into | なし |
| X3-67 | repo 外 Claude 既定 model/effort 手動変更 | `:765-767,779` | blocked(owner=ユーザー) | repo 外・実施証拠なし | same | なし |
| X3-68 | model-economy branch の統合 | `:780` | done | merge `3bd3de0` | same | なし |
| X3-69 | workflow script 起動前 model lint | `:781` | continued | checker 実在 `tools/check_workflow_models.py:13-14`; hook 未配線 `hooks/README.md:119` | same | なし |
| X3-70 | test-runner-autoscale branch 統合 | `:800` | done | merge `240d1cc` | same | なし |
| X3-71 | balanced backoff profile 対照 | `docs/archive/worklog-phase1-2.md:898-901` | deferred(trigger=対照 profile が必要な研究判断) | `docs/phase3.md:391` | same | `phase3:391` |
| X3-72 | over-throttle 有用 IPC 機序分離 | `archive/worklog-phase1-2.md:900-901` | deferred(trigger=MLP/cache 識別実験を行う判断) | `docs/phase3.md:392` | same | `phase3:392` |
| X3-73 | mocc trace-hook | `archive/worklog-phase1-2.md:276-282` | deferred(trigger=S1/cross-protocol 再開) | `docs/phase3.md:393` | same | `phase3:393` |
| X3-74 | ermia trace-hook/cross-check | `archive/worklog-phase1-2.md:157-160` | deferred(trigger=S1/cross-protocol 再開・版写像再定義) | `docs/phase3.md:394` | same | `phase3:394` |
| X3-75 | calibration 下限 K 感度 | `archive/worklog-phase1-2.md:220-226` | deferred(trigger=下限 K の再検討) | `docs/phase3.md:395` | split-into | `phase3:395` |
| X3-76 | thread 数変更時の再 calibration | `archive/worklog-phase1-2.md:220-226` | deferred(trigger=測定 thread/protocol 変更) | `docs/phase3.md:268,395` | split-into | `phase3:268,395` |

#### X6_report.md

## 状態判定表 (全原子項目)

| id | 項目要約 | 出所 file:line | 状態 | 根拠 (file:line/commit) | 対応関係 | live carrier |
|---|---|---|---|---|---|---|
| X6-01 | maxrss 固定オーバヘッド控除 | calibration…:58-60 | deferred(trigger: 厳密下限が必要) | `calibrator/analyze.py:124-149` 未実装 | split-into | なし |
| X6-02 | 1m 未満へ sweep 拡張 | calibration…:58-60 | deferred(trigger: 厳密下限が必要) | `calibrator/cli.py:112` | split-into | なし |
| X6-03 | predicate P record | phantom…:37-45 | deferred(trigger: range workload) | trace/parser に P 無し | split-into | なし |
| X6-04 | predicate anti-dependency | phantom…:40-45 | deferred(trigger: range workload) | `verifier/dsg.py` に述語辺無し | split-into | なし |
| X6-05 | WAL ftruncate XOR 上流修正 | wal-ftruncate…:39-50 | done | PR #116 / `2574412`; `docs/phase3.md:394-399` | same | 不要 |
| X6-06 | invisible reads は rr100 anchor＋全曲線報告 | invisible…:67-80 | done | 同 insight:67-80、phase1 訂正済み | same | 不要 |
| X6-07 | oze を uniform で測る | oze…:40-45 | superseded(D32 の対象選定) | `docs/phase3.md:291-299` | split-into | phase3:291-299 |
| X6-08 | oze skew 病理を明示フラグ化 | oze…:40-45 | superseded(D32 の対象選定) | `docs/decisions.md:702-715` | split-into | phase3:291-299 |
| X6-09 | ADD_ANALYSIS ODR/segfault 修正 | backoff-add-analysis…:81-96 | done | PR #118 / `50c7946` | same | 不要 |
| X6-10 | settle timeout を pipeline admission reject に | orphan…:57-60 | superseded(直接 competitor probe) | `e419c55`; `loop.py:74-91` | superseded | phase3 見送り台帳の計測硬化 |
| X6-11 | timeout 後の孤児 cleanup | orphan…:64-66 | done | pipeline subprocess timeout・probe、`e419c55` | same | 運用規律 |
| X6-12 | BACK_OFF/WAL/no-wait の探索推奨 | critic…:39-45 | done | P2-5/P2-4 実走、D27/D28 | merged-from | 不要 |
| X6-13 | backoff 別 boot 再現 | p2-case…:78-80 | unresolved | `backoff_repro.py:12`; 完了証拠なし | split-into | なし |
| X6-14 | backoff rounds≥3 | p2-case…:78-80 | unresolved | `stability.py:251-252`; 完了証拠なし | split-into | なし |
| X6-15 | useful IPC 分離 | p2-case…:81-83 | done | 同 insight:164-177; D20 | same | 不要 |
| X6-16 | static variant perf-config trace＋broken-silo | p2-case…:85-87 | done | `docs/phase2.md:173-175`; S2/D36 | same | 不要 |
| X6-17 | adaptive Backoff_ 収束値実測 | p2-case…:88 | done | 同 insight:108-159 | same | 不要 |
| X6-18 | 第2・3位 base で fix5/fix10 | p2-case…:89 | unresolved | 後続成果物・裁定なし | same | なし |
| X6-19 | thread/skew/records 拡張 | p2-case…:92 | unresolved | 完了述語を満たす成果物なし | split-into | なし |
| X6-20 | fix2/3/5/7 reps≥15 | p2-case…:92-93 | unresolved | 該当 report/commit なし | split-into | なし |
| X6-21 | physical-core pin で SMT 分離 | p2-case…:93 | unresolved | 該当 ablation なし | split-into | なし |
| X6-22 | rmw=1 一点測定 | p2-case…:94 | unresolved | 該当 run/report なし | same | なし |
| X6-23 | no-wait-zero の上流還元 | no-wait…:77-83 | rejected(out-of-scope/任意) | 同 insight の還元判断 | same | 不要 |
| X6-24 | cicada/oze へ探索空間拡大 | p2-5…:78-79 | deferred(trigger: 8b＋S1) | `docs/phase3.md:291-299` | same | phase3:291-299 |
| X6-25 | critic uncertainty と早期停止抑制 | p2-5…:79 | continued | critic 設計/D28、再利用時適用 | same | phase3 の loop 設計 |
| X6-26 | identity-error retryable 化 | loop-src-token…:39-47 | done | D25; `loop.py:74-91` | same | 不要 |
| X6-27 | configure 最終 -D digest | evolve-review…:29-32 | deferred(trigger: cicada/oze) | `docs/phase3.md:422-423`; D23 | same | phase3:422-423 |
| X6-28 | H3 方針 A/B/C の裁定 | hooks-round2…:27-35 | done | D30/D33/D34 | same | 不要 |
| X6-29 | H3 13 real の処置 | hooks-review…:91-101 | done | `6507c87` ほか D30-D34 | merged-from | 不要 |
| X6-30 | kickoff blocking real 群 | kickoff-review…:15-45 | done | Phase3 kickoff 完了、D35-D37 | merged-from | 不要 |
| X6-31 | auditor n=1 の実運用観察 | s3-auditor…:29-31 | done | `docs/phase3.md:305-313` | same | 不要 |
| X6-32 | sort iteration 2 継続 | sort-preliminary…:57-66 | superseded(8a を本筋化) | phase3:305-312 | superseded | 不要 |
| X6-33 | 8a Stage B 必須前提 | stage-b-sheet…:14-20 | done | D48-D50、phase3:305-312 | merged-from | 不要 |
| X6-34 | roadmap stale 6点修正 | roadmap-audit…:52 | done | 同行の「6点すべて反映済み」 | merged-from | 不要 |
| X6-35 | 8a 軸の生死裁定 | recon…:113-116 | done | ユーザー進行、phase3:305-312 | same | 不要 |
| X6-36 | build-error payload に例外要約 | recon…:152-155 | done | `pipeline.py:156-164,461-465`; test_campaign:1151 | same | 不要 |
| X6-37 | headline を系レベルへ再構成 | strategy…:25 | done | D52、S' 実験・最終報告 | same | 不要 |
| X6-38 | coder-v4 定義承認・配置 | coder-draft:1 | done | runbook:16-18、8a 完走 | same | 不要 |
| X6-39 | Stage E review 修正群 | design-review:20-47 | done | 8a E/F 完走、phase3:305-312 | merged-from | 不要 |
| X6-40 | provenance extra-source union | strategy…:31,36 | done | `80b21de`; archive worklog:2125-2132 | split-into | 不要 |
| X6-41 | EVOLVE hole コメント機械拒否 | strategy…:33,36 | unresolved | `diff_quarantine.py:375-387`; test:430-437 | split-into | なし（triage handoff は audit seed） |
| X6-42 | trigger runbook abort>0 二行 | strategy…:34,36 | unresolved | runbook:14-31,78-92 に不存在 | split-into | なし |
| X6-43 | allowlist 反転＋間接 thid gallery | strategy…:32,36 | deferred(trigger: ユーザー裁定) | D42条件4未裁定、decisions:1951 | merged-from | なし |
| ⚠ 訂正 (R2/R3) | D42 条件4（auditor 型13〜15）は承認・実装済み。未裁定なのは後続の allowlist 反転と間接 thid gallery で、B-010/B-058 へ分割 | — | deferred(trigger) | `docs/decisions.md:1352`; `.claude/agents/auditor.md:58` | レビュー訂正注記 | B-010 / B-058 |
| X6-44 | 8c 非侵襲 daemon | strategy…:46,50 | deferred(trigger: 運営律速再発) | `docs/phase3.md:351-355` | same | phase3:351-355 |
| X6-45 | workload 次元を入力化する 8b | strategy…:45,50 | continued | `docs/phase3.md:327-343` | same | phase3:327-343 |
| X6-46 | S6 n決定残タスク | s6-n…:48,60 | done | phase3:250-261 | merged-from | 不要 |
| X6-47 | blind prompt の入力構成言及禁止 | s6-report…:41 | deferred(trigger: 次の blind 設計) | 後続 prompt/carrier なし | merged-from | なし |
| X6-48 | S6 round 実走 gate | round-design…:275 | done | phase3:250-261 | same | 不要 |
| X6-49 | Holm 表・報告文言確定 | s6-report…:59-68 | done | phase3:254-261 | same | 不要 |
| X6-50 | bench-first screening 実装 | bench-first…:171-273 | done | `9a0a0cc`; phase3:344-345 | same | 不要 |
| X6-51 | S1 直接比較 | overall-strategy…:40-80 | done | phase3:250-255 | same | 不要 |
| X6-52 | layer3 fact renderer | layer3-design…:20-90 | done | `15d9e7c`, `24202e2`; phase3:360-379 | split-into | 不要 |
| ⚠ 訂正 (R1) | X6-52 の `15d9e7c` / `24202e2` は解決不能な stale hash。done は維持し、到達可能な根拠を `d6085a9`（実装）/ `2230edf`（最小実レポート）/ `4204013`（v2 拡大）へ訂正 | — | done | `d6085a9`, `2230edf`, `4204013` | レビュー訂正注記 | 不要 |
| X6-53 | layer3 mechanism hypothesis v3 | layer3-design…:90-140 | deferred(trigger: 次 loop 再走) | phase3:365-379 | split-into | phase3:365-379 |
| X6-54 | floor protocol F1 | floor-package:34-134 | done | `3d96f57`, `b87bb1e` | same | 不要 |
| X6-55 | floor protocol F2 | floor-package:135-204 | done | `b7b38da`, `b87bb1e` | same | 不要 |
| X6-56 | floor budget F3 | floor-package:205-264 | continued | F3裁定済み、数値は protocol/floor 段 | same | phase3:48-67 |
| X6-57 | env・順序 F4 | floor-package:265-315 | done | `cdb16c0`, `28ccb07` | same | 不要 |
| X6-58 | freeze schema F5 | floor-package:316-378 | done | strict-v2 commits | same | 不要 |
| X6-59 | approval binding F6 | floor-package:379-438 | done | `bfa0f08`, `fad6f0a` | same | 不要 |
| X6-60 | v2 verifier semantics F7 | floor-package:439-497 | done | `bfa0f08`, `de23695` | same | 不要 |
| X6-61 | median-of-medians 裁定 | ruling-package:26-80 | done | floor protocol 裁定群 | same | 不要 |
| X6-62 | resume/crash policy | ruling-package:81-142 | done | F2/F6/F7・launch cert | same | 不要 |
| X6-63 | execution topology | ruling-package:143-188 | done | strict-v2 Lane RV/M/O | same | 不要 |
| X6-64 | status/rc 契約 | ruling-package:189-243 | done | strict-v2 tests | same | 不要 |
| X6-65 | R5 truth table | ruling-package:244-290 | done | `de23695`, `d7ac2d7` | same | 不要 |
| X6-66 | floor env 選択 | ruling-package:291-349 | done | env_tag Pegasus、`f49cfef`, `26a9ad6` | same | 不要 |
| X6-67 | selector leak-control package | selector-leak…:20-180 | done | selector freeze/strict-v2 Lane J/O | merged-from | 不要 |
| X6-68 | A3-1/A3-2 window・test | third-wave:91-95 | done | `d96a9f0` | merged-from | 不要 |
| X6-69 | A3-3/A3-4 topology・rc | third-wave:95-96 | done | ruling 3/4、strict-v2 | merged-from | 不要 |
| X6-70 | A3-5 optional strengthening | third-wave:97 | superseded(strict-v2 matrix) | `23fa0db` | superseded | 不要 |
| X6-71 | A3-6 verified single object | third-wave:98 | done | `a87c107`, `d4cbf91` | same | 不要 |
| X6-72 | 二波監査 F/G finding 群 | two-wave:80-91 | done | 記載 commits + strict-v2 | merged-from | 不要 |
| X6-73 | clarity P-19 | clarity…:44-63 | done | `05ea74c`; file:47 | same | 不要 |
| X6-74 | clarity P-118 | clarity…:67-86 | done | `05ea74c`; file:70 | same | 不要 |
| X6-75 | clarity P-209 | clarity…:90-109 | done | `05ea74c`; file:93 | same | 不要 |
| X6-76 | clarity P-100 | clarity…:190-220 | done | 再起草版適用、file:11 | same | 不要 |
| X6-77 | clarity C-32 | clarity…:113-140 | done | `fe9620d`; file:116 | same | 不要 |
| X6-78 | clarity C-139 | clarity…:144-169 | done | `fe9620d`; file:147 | same | 不要 |
| X6-79 | clarity C-150 | clarity…:173-200 | done | `fe9620d`; file:176 | same | 不要 |
| X6-80 | clarity P-155 | clarity…:250-280 | done | `05ea74c`; file:11 | same | 不要 |
| X6-81 | clarity P-3 | clarity…:19-40 | rejected(軸ずれ) | file:22 | same | 不要 |
| X6-82 | clarity P-89 | clarity…:280-310 | rejected(利益不足) | file:11 | same | 不要 |
| X6-83 | clarity P-93 | clarity…:310-340 | rejected(利益不足) | file:11 | same | 不要 |
| X6-84 | repo refinement consultation 群 | repo-refinement…:366-390 | done | `23c736d` | merged-from | 不要 |
| X6-85 | fsync/tmpfs speedup＋容量防壁 | fsync-review:58-64 | done | `d9183fd`; D60 | merged-from | 不要 |
| X6-86 | v2 prereq wave1 | prereqs-consultations:416-477 | done | `82af986`〜`3522ce9` | merged-from | 不要 |
| X6-87 | prereq wave2 Lane A | wave2:601-611 | done | `6a102d5`, `95afc88` | merged-from | 不要 |
| X6-88 | prereq wave2 Lane B 統合 | wave2:621-629 | superseded(strict-v2 Lane M/J) | `8d3642e`, `2ee5d07` | superseded | 不要 |
| X6-89 | prereq wave2 Lane C | wave2:649-654 | rejected(F7先取り) | file:650 | same | 不要 |
| X6-90 | floor wave3 S/C/E | floor-wave3:63-80 | done | `28ccb07`, `b87bb1e` | merged-from | 不要 |
| X6-91 | floor wave3 Lane M | floor-wave3:71,104 | done | 後続 `8d3642e` | same | 不要 |
| X6-92 | strict-v2 C1 trust/history 群 | strict-v2:508-514 | done | `fad6f0a`, `de23695`, `23fa0db` | merged-from | 不要 |
| X6-93 | strict-v2 C2 closure/cert 群 | strict-v2:515-524 | done | `1eb1ed1`, `d4cbf91` | merged-from | 不要 |
| X6-94 | strict-v2 C3 execution/run-contract 群 | strict-v2:525-535 | partial(children) | 機構は実装、reps/extime/floor実測は未完 (`phase3.md:66-67`) | split-into | phase3:48-67 |
| X6-95 | strict-v2 C4 builder/probe/docs 群 | strict-v2:536-546 | done | `babef37`, `2ee5d07`, `23fa0db` | merged-from | 不要 |
| X6-96 | strict-v2 §5 追認事項 | strict-v2:593-612 | done | worklog 2026-07-19 (2):743-749; `25bbbe7` | same | 不要 |
| ⚠ 訂正 (R1) | §5 追認は (i)〜(vii)=done、(viii)=B-005 のとおり未消化。`25bbbe7` は §10.2 の別成果物で §5-(viii) を完了しない | — | partial(children) | (i)〜(vii): done / (viii): unresolved (B-005) | レビュー訂正注記 | B-005 |
| X6-97 | guard_agent review 8項 | guard-review:49-54,98-103 | done | `e45db19` | merged-from | 不要 |
| X6-98 | C22 §5-(ix)-1〜10 | c22:543-572 | done | `4521b72`, `1eb1ed1` | merged-from | 不要 |
| X6-99 | C22 validator 本丸 | c22:1471-1539 | done | `d4cbf91` | merged-from | 不要 |
| X6-100 | C22 §10.2 追認5項 | c22:1478-1539,2564 | done | worklog:743-749; `25bbbe7` | merged-from | 不要 |
| X6-101 | Pegasus env contract 登録 | env-contract:822-860 | done | `950757e`〜`26a9ad6`; accepted certification | merged-from | 不要 |
| X6-102 | protocol JSON 実凍結 | env-contract:1017 | continued | `docs/phase3.md:66-67` | same | phase3:66-67 |
| X6-103 | Pegasus floor 実測 | env-contract:1017 | continued | `docs/phase3.md:66-67` | same | phase3:66-67 |
| X6-104 | verifier model/effort 再ピン | economy-audit:10-20 | done | `7f77ecb`; D61 | same | 不要 |
| X6-105 | workflow model lint | economy-audit:21-26 | done | `tools/check_workflow_models.py`; `7f77ecb` | same | 運用規律 |
| X6-106 | user settings model=fable→opus | economy-audit:27-32 | unresolved | 現物は fable のまま | split-into | なし |
| X6-107 | user settings effort=xhigh→high | economy-audit:27-32 | done | 現物 `effortLevel=high` | split-into | 不要 |
| X6-108 | test hygiene 採用施策群 | survey:120-128 | done | `5073116` | merged-from | 不要 |
| X6-109 | hygiene #1/#2/#3/#9 非強化 | survey:120-128 | rejected(契約どおり/強化不要) | worklog:804-810; `5073116` | merged-from | 不要 |
| X6-110 | CCBench protocols 表の上流 PR | ccbench-protocols…:6,29-31 | blocked(user) | Izanagi側は anatomy で是正、上流判断待ち | same | `docs/ccbench-anatomy.md:61` |

<!-- APPENDIX_STATE_TABLES_END -->


### A.3 X4 見送り台帳裏取り（レポート逐語）

~~~~text
=== X4 REPORT START ===

調査基準は superproject HEAD `80343a2cc1f...`、CCBench gitlink `d706650cdb31...`。処置判断は行っていない。

## 1. balanced backoff 対照

- 事実状態: **未消化**。balanced 座標と sweep 実装はあるが、取得済み成果物はない。さらに現 driver は現 pin ではなく歴史 pin `dff0f1e` を参照するため、「現 pin で取得可能」まで完成していない。
- 証拠:
  - 台帳は未取得を明記: [phase3.md:391](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:391)、[notes-2026-07-10.md:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/paper-story/notes-2026-07-10.md:7)。
  - driver は `balanced/rratio=50` と `{2,5,10,25,50,100}`、および none=0 を実装: [backoff_profile.py:46](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:46)、[backoff_profile.py:49](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:49)、[backoff_profile.py:173](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:173)。
  - 既定実行は write-heavy のみ: [backoff_profile.py:224](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:224)。
  - driver の build は trace-disabled: [backoff_profile.py:130](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:130)。
  - 現 pin は `d706650`: [pin.py:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pin.py:26)。一方 driver が import する `p2_2.CCBENCH_COMMIT` は `dff0f1e`: [backoff_profile.py:40](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:40)、[p2_2.py:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/p2_2.py:36)。
  - HEAD の committed `profile/` は rr5 の JSON/MD だけ。実体も write-heavy/rr5/48-thread/1M: [rr5 JSON:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.json:2)、[rr5 JSON:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.json:7)。`git ls-files` に rr50 JSON/MD は 0 件。
- 反証・不確実性:
  - docstring の「既定で write-heavy + balanced」[backoff_profile.py:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:20) は実際の既定選択と不一致。
  - off-repo の実走有無は不明だが、基準が「committed JSON/MD」なので取得済み判定には影響しない。
- 完了と数える証拠の定義:
  - 現 pin `d706650cdb31...`、`balanced`、`rratio=50`、0/2/5/10/25/50/100µs 全点を含む committed JSON/MD。
  - `env_tag`、threads、records、workload、pin、binary identity、`TRACE=0`、`BACKOFF_NOINLINE` とその inert 性を成果物に直接束縛する。
- 条件付き carrier とする場合の発火条件述語案:
  - `P_bal := ("balanced" ∈ frozen_mechanism_profile_workloads) ∧ (qualifying_rr50_artifact = absent)`。
  - 現在値: **false**。現行 Fig.2 の機序 profile は write-heavy のみで、balanced は条件付き必要性として記述されている。
  - 観測対象: 凍結された図・レポートの workload 集合、`output/env/*/profile/`。
  - 再評価点: backoff 機序図または「+38%/+11% 両方」の説明を凍結する直前。

## 2. over-throttle IPC 機序分離

- 事実状態: **部分吸収**。
  - 完了部分: sweet-spot 0–10µs の total IPC 低下は spin 希釈。有用 IPC はほぼ一定。
  - 観測済み部分: 25–100µs で有用 IPC 自体が低下。
  - 未完部分: その原因が MLP 低下か、cache 余熱喪失かの識別。
- 証拠:
  - Phase 2 の「機序的に閉じた」は sweet-spot を対象にしている: [phase2.md:106](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase2.md:106)、[phase2.md:109](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase2.md:109)。
  - sweet-spot の有用 IPC 一定・spin 希釈: [synthesis.md:172](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:172)。
  - over-throttle は「有用 IPC 低下」の観測まで: [synthesis.md:184](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:184)。単一 48-thread 断面で、幅は soft: [synthesis.md:188](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-06-22_p2-case-study-backoff-synthesis.md:188)。
  - profile driver の HW event は cycles/instructions のみ: [backoff_profile.py:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:47)、[backoff_profile.py:117](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_profile.py:117)。
  - over-throttle driver は spin/abort/tps/派生 eff_tps のみ: [backoff_overthrottle.py:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_overthrottle.py:63)、[backoff_overthrottle.py:69](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/backoff_overthrottle.py:69)。
- 反証・不確実性:
  - 「over-throttle 効果が real」は反証されない。ただし同じ useful IPC 系列から原因を再解釈しても二仮説の分離にはならない。
  - event multiplex と単一 thread 断面により、低下幅の精密値には留保がある。
- 完了と数える証拠の定義:
  - 実走前に次の反対予測を固定する。
    - `H_MLP`: useful phase の平均 outstanding miss/MLP が backoff 増加で低下し、memory-stall が増える。LLC MPKI を条件付けた後の warm/cold 介入効果は小さい。
    - `H_cache`: backoff 増加で LLC miss/MPKI が増え、warm 制御が useful IPC 低下を明確に緩和する。outstanding miss 能力の低下は必須でない。
  - 必須観測: outstanding-miss proxy、L3/memory-stall 系、LLC loads/misses、useful-instruction 正規化 MPKI、既存 spin/useful IPC。
  - warm/cold を明示的に操作した factorial 対照、同一 pin/env/thread/records/workload、trace-disabled、順序ランダム化、反復、事前固定した符号・interaction 判定を持つ committed raw/summary。
- 発火条件述語案:
  - `P_over := active_report_or_consumer emits causal_attribution ∈ {MLP, cache-warmth}`。
  - 現在値: **false**。現文書は二次低下までで原因未分離。
  - 観測対象: 層3機序仮説層、backoff 図・論文 prose、critic/selector 入力。
  - 再評価点: 層3 mechanism v3 の schema/prose 凍結時、または backoff 因果説明の出版用凍結時。

## 3. mocc trace-hook

- 事実状態: **未消化**。汎用 TRACE 基盤と S1 carrier はあるが、MOCC 固有 hook・実トレース・verifier の第二 protocol 実証はない。
- S1 の意味:
  - S-1 研究主張とは別物: [phase3.md:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:23)。
  - **S1 = 別 protocol への trace-hook 移植**。旧 headline 2 復活または段7 cross-protocol 着手時に発火: [phase3.md:185](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:185)。
- 証拠:
  - Phase 1 は MOCC hook 未実装のため Silo `BACK_OFF` で代替し、MOCC を残増分とした: [phase1.md:143](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase1.md:143)、[phase1.md:147](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase1.md:147)。
  - 現 pin の MOCC source は trace header を include せず: [mocc/transaction.cc:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/mocc/transaction.cc:1)、commit にも hook がない: [mocc/transaction.cc:1074](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/mocc/transaction.cc:1074)。`git grep` でも `cc/mocc/` 内の `#if TRACE` / `trace.hh` / `izanagi_trace` は 0 件。
  - 探索空間は Silo のみ: [genome.py:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/genome.py:87)。
  - pipeline は trace ファイル中の `C` 件数を数える: [pipeline.py:188](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:188)。hook 無しなら `ncommit=0` となり `trace-empty` reject: [pipeline.py:512](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:512)。
- 反証・不確実性:
  - universal `CCBENCH_TRACE` 定義は存在する: [Options.cmake:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cmake/Options.cmake:15)。ただし MOCC source に hook がなければ出力は生じない。
- 完了と数える証拠の定義:
  - 現 pin MOCC に `#if TRACE` で read/write/commit hook。visible/invisible 両 read path の実行被覆を示す。
  - trace commit 数と CCBench commit 集計が一致し、duplicate commit・orphan version/read・missing txid が 0。
  - 実 MOCC trace が verifier で certified。TRACE=0 binary は `izanagi_trace` symbol 0。
  - 以上を pin、workload、hook diff、binary hashとともに committed 成果物へ束縛する。
- 発火条件述語案:
  - `P_S1 := old_headline2_revived ∨ phase7_cross_protocol_started`。
  - `P_mocc := (P_S1 ∧ "mocc" ∈ frozen_protocol_set) ∨ visible_invisible_correctness_ablation_approved`。
  - 現在値: **どちらも false**。現行主経路は 8b + 層3で、SPACES も Silo のみ。
  - 観測対象: phase の承認済み protocol 集合、実験事前登録、`SPACES`。
  - 再評価点: cross-protocol protocol 集合の凍結時、`mocc` を `SPACES` に加える直前、visible/invisible 正しさ比較の承認時。

## 4. ermia cross-check

- 事実状態: **前提消滅・要再定義**。
- 独立再導出:
  - 旧文書は「版 cstamp=`cstamp<<1`、commit 二系統」とする: [ccbench-anatomy.md:211](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/ccbench-anatomy.md:211)。
  - serial helper `ssn_commit()` は実在し、版 cstamp を shift する: [ermia/transaction.cc:503](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:503)、[ermia/transaction.cc:553](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:553)。
  - しかし YCSB live path は公開 `commit()` を呼ぶ: [ycsb.hh:161](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/include/ycsb.hh:161)。
  - 公開 `commit()` は `ssn_parallel_commit()` だけを呼ぶ: [ermia/transaction.cc:905](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:905)。
  - parallel path は `cstamp_=++Lsn` とし: [ermia/transaction.cc:594](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:594)、[ermia/transaction.cc:602](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:602)、新 version へ **未 shift の `cstamp_`** を保存する: [ermia/transaction.cc:751](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:751)、[ermia/transaction.cc:765](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:765)。
  - low-bit TID flag は現 live path では主に `psstamp_.sstamp_` の符号化であり、`Version::cstamp_` とは別 field: [version.hh:9](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/include/version.hh:9)、[version.hh:92](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/include/version.hh:92)。
  - 初期版は `cstamp=0`: [tuple.hh:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/include/tuple.hh:21)。read は committed/deleted かつ `cstamp<=txid` の版を選ぶ: [ermia/transaction.cc:146](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/external/ccbench/cc/ermia/transaction.cc:146)。
- 反証・不確実性:
  - shifted serial 実装自体は real。ただし repository 内の live workload call pathからは到達しない。外部 consumer が公開 `ssn_commit()` を直接呼ぶ場合は別だが、現 CCBench YCSB の前提ではない。
- 再定義に必要な項目:
  1. pin 固定の workload→公開 `commit()`→reachable helper call graph。
  2. begin `txid`、commit `cstamp`、worker ID の役割分離。
  3. 初期版 `cstamp=0`、inflight 時の `txid`、commit 後の raw `cstamp` への遷移。
  4. `psstamp.sstamp` の TID flag と `Version::cstamp_` を別 decoder にする。
  5. read-own-write、通常 read、update/insert/delete、aborted/inflight/deleted version の trace 規則。
  6. version ID の一意性。少なくとも record identity と raw cstamp を束縛し、初期版の `0` を全 record 共通 producer IDにしない。
- 完了と数える証拠の定義:
  - 上記再導出と hook schemaを現 pinへ束縛した committed 設計。
  - 同一 workload・同一 verifierで SI が G2 赤、ERMIA が緑。両方とも commit 数一致、orphan/duplicate/missing txid 0、TRACE=0 symbol 0。
- 発火条件述語案:
  - `P_ermia := {"si","ermia"} ⊆ frozen_crosscheck_protocols`。
  - 現在値: **false**。
  - 観測対象: cross-protocol 事前登録の protocol 集合。
  - 再評価点: 旧 headline 2 復活または段7 protocol 集合凍結時。実験着手前に上記再定義の充足を検査する。

## 5. calibration K 感度・thread 再較正

- 事実状態: 元行は独立した二タスクの複合。
  - **K 感度: 未消化**。
  - **thread 数変更時の再 calibration: 部分吸収**。4-thread 単点の scale sensitivity だけ取得済みで、4-thread calibration 全体は未実施。
- 証拠:
  - 起源も「thread 再 calibration / K 感度」の二項: [worklog-phase1-2.md:226](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/archive/worklog-phase1-2.md:226)。
  - 段6前提 (b) を含む (a)–(e) は旧 headline 復活まで休眠: [phase3.md:263](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:263)。内容は protocol 登録・protocol 別 calibration・between-run floorで、K sweep の記載なし: [phase3.md:268](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:268)。
  - D15 は K=4 を名前付き knob としただけ: [decisions.md:220](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:220)、[decisions.md:231](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:231)。
  - 実装も既定 K=4 の単値: [analyze.py:19](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/analyze.py:19)。CLI に K 指定・K sweep option はない: [cli.py:100](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/cli.py:100)。
  - JSON の本体 calibration は 48-thread、K=4: [calibration JSON:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:2)、[calibration JSON:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:17)。
  - 4-thread は `scale_sensitivity.small` の `1M records` 単点: [calibration JSON:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:70)。records sweep は全て48-thread: [calibration JSON:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:107)。
  - 実装上も small=4t/1M は scale 特徴量用で、本体 sweep/noiseとは別: [sweep.py:221](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/sweep.py:221)、[sweep.py:247](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/sweep.py:247)。
  - HEAD に committed `calibration_t4_*` は 0 件。
- 反証・不確実性:
  - 既存系列から一部 K を post-hoc 再計算することは可能だが、感度実験・結論表は存在しない。
  - 最小 1M 点で既に working-set/L3=6.6。低い K はすべて同じ最小点へ左打切りされるため、低 K 域の感度には sub-1M 点が必要。
  - 4-thread 点は実測なので「何もない」ではないが、採用 records、within/between floorを決めていないため再 calibration 完了ではない。

### 5a. K 感度の完了証拠

- env/pin/protocol/workload/thread を固定し、事前登録した K 集合ごとに採用 N、LLC miss率、maxrss/L3、下限充足、結論の変化を示す committed JSON/MD。
- K 区間の端で選択 N が測定下限・上限に張り付く場合、その方向へ records sweepを拡張する。
- 既存データを再利用する場合も、使用点の完全性と post-hoc であることを明示する。

発火述語案:

`P_K := (new_lower_bound_calibration_started ∨ K4_based_N_about_to_be_frozen_in_claim) ∧ qualifying_K_sensitivity_table_absent`。

現在値は **false**。段6(b) は休眠で、新しい protocol/thread calibration は active でない。観測対象は calibration plan、`lower_bound_selected`、報告凍結表。再評価点は新 env/protocol/thread 校正の開始時と、K=4 を使う主張の凍結時。

⚠ 訂正 (R2): 承認済み protocol/freeze は `lower_bound_selected=true` かつ `l3_multiple=4.0` の N を参照し、K 感度表は absent のため `P_K` の現在値は **true**。本体 B-015 の精密化した述語と Pegasus `calibration-753f535a8d024727.json:1603`、`docs/worklog.md:725` を参照。

### 5b. thread 再 calibration の完了証拠

- 各 live thread 数 `T` について、同一 env/pin/protocol/workload の `calibration_t<T>_*` JSON/MD。
- records sweep、採用 N、LLC miss/maxrss、within-run noise、対応する between-run floor、thread/NUMA binding、TRACE=0を含む。
- scale sensitivity 内の単一 `small` 点はこの証拠に数えない。

発火述語案:

`P_thread(T) := T ∈ approved_performance_threads ∧ qualifying_calibration(env,pin,protocol,workload,T) = absent`。

現在値は、live 48-thread 座標では **false**、4-thread を性能比較へ採用した瞬間に **true**。観測対象は campaign `PerfConfig.threads` と committed calibration/floor。再評価点は campaign 事前登録・thread数変更・env/pin/protocol変更時。

⚠ 訂正 (R2): Pegasus 48-thread は bootstrap で `scale_sensitivity=not-measured`、between-run floor absent のため `P_thread(48)` は **true**。ただし floor 取得は `docs/phase3.md:66-70` の live carrier が運ぶため、独立裁定は floor 実測完了後に再評価する。

=== X4 REPORT END ===
~~~~

### A.4 追補（レビューで発見された母集団漏れ）

R1 の層化抜き取りで、原掃引 462 項目の外に次の 5 原子項目が見つかった。これを A.1 の訂正後母集団
467 項目へ加えた。これは抜き取りで発見した追補であり、全数保証ではない。

1. **screening payload 用層3 schema の再凍結** — **deferred**
   (`trigger := screening_campaign_added_to_layer3_scope`)。出所は
   `output/insights/2026-07-16_layer3-mechanism-wiring-design.md:45`、live carrier は
   `docs/phase3.md:363`。carrier が生存するため、本体に追加のユーザー裁定行は作らない。
2. **7/11 docs 圧縮監査の real 4 action** — 全件 **done**。
   - 文書地図の漏れ修正
   - literature-map の補記
   - `FIGURE_CONVENTIONS` の参照名修正
   - 15.9KB 値の訂正記録

   完了根拠は `73f63a2`, `2d5b6d4`, `86f3ae7`。原掃引レポートの行は書き換えず、本追補で 4 原子項目を
   terminal 証拠付きで追加する。

## 付録 B — 判定に迷った項目（逐語）

各ブロックは入力レポートの同名節をそのまま収録する。X4 の不確実性は A.3 の各項目内に逐語保存済み。

### X1a_report.md

~~~~text
## 判定に迷った項目
{id: X1A-51, 迷い: D37/modelの「build-errorはterminal」を元約束の正式棄却と数えるか, 両解釈: rejected(reason)=現在の設計は一律terminalを明示 / unresolved=元約束の「infra起因だけ分類」は明示裁定されず単に実装されなかった}

{id: X1A-62, 迷い: 後年の層3 renderer 契約が「WAL proof chain の実体定義」と同一か, 両解釈: done=WAL eventとreport source-refの完全双射まで直接定義・実装 / partial=元課題はシステム全体のproof chain定義で層3だけでは狭い}

{id: X1A-70, 迷い: 日付抜き改名は未実施だが後のディレクトリ集約を何と数えるか, 両解釈: superseded=版別snapshot方針が別構造を採用 / unresolved=字義上の日付抜き改名は行われていない}

{id: X1A-82, 迷い: 後続のultracode利用を暗黙の「常時オン維持」裁定と数えるか, 両解釈: blocked(human)=明示裁定なし / rejected(reason)=利用継続という運用実績を提案棄却とみなす。ただしdone証拠基準に従い前者を採用}

{id: X1A-86, 迷い: 人間git clean義務は実行されたか, 両解釈: superseded=d862da3で成果物を正式追跡対象へ変更 / done=clean不要との後続判断で処置完了。直接の削除証拠がないためsupersededを採用}
~~~~

### X1b_report.md

~~~~text
## 判定に迷った項目

- {id: X1B-19, 迷いの内容: S-1 `known_axes_freeze.json` を「既存軸台帳の独立成果物化」と数えるか, 両解釈: (A) 軸名・構成を機械可読化したのでdone、(B) 元の完了述語はaxis-proposerの人間gateでhole/探索範囲を照合する台帳で、性能比較点freezeはunrelated。本報告はCA-3基準に従い(B)}
- {id: X1B-31/X1B-32, 迷いの内容: 外部会話・送付はリポジトリ外で完了済みかもしれない, 両解釈: (A) 外部で完了、(B) 証拠もcarrierもなく棚卸し上unresolved。本報告は(B)}
- {id: X1B-73, 迷いの内容: F13とmemory/driver実装を「作業の進め方5への配線」の代替完了と数えるか, 両解釈: (A) 実質目的は達成、(B) 完了述語はCLAUDE.mdへの1行配線であり未達。本報告はpartial(children)}
- {id: X1B-74, 迷いの内容: `docs/failures.md` をlive carrierと認めるか, 両解釈: (A) 現行台帳なので実質live、(B) 指定されたcarrier集合に含まれない。本報告は状態deferredを維持しつつ、黙落ち候補の確度をlow}
- {id: X1B-84, 迷いの内容: 07-16の「push可」は判断だけで実pushではない, 両解釈: (A) 当時未pushなのでcontinued、(B) 対象07-13 commit群が現origin/mainのancestorで実pushも後日完了。本報告は(B)}
~~~~

### X2_report.md

~~~~text
## 判定に迷った項目
- {id: X2-13, 迷いの内容: 参照元の「provenance 恒久修正ほか should-fix」の「ほか」が無名集合, 両解釈: (A) provenance 修正80b21deで実質全消化、(B) 別の未列挙should-fixが黙って落ちた。直接証拠がないため unresolved}
- {id: X2-40, 迷いの内容: 現行状態はAGENTS/.codex README/D56に明示されているが、ユーザー指定のlive-carrier集合には含まれない, 両解釈: (A) policy carrierを広く取れば生存、(B) 共通スキーマを厳密適用すれば黙って落ちた候補}
- {id: X2-41, 迷いの内容: D54に将来条件は残るが現行タスク台帳にない, 両解釈: (A) safety decision自体がcarrier、(B) 指定carrier外なので候補。後者を採用}
- {id: X2-45, 迷いの内容: 「共有相手が決まった時点」のtrigger成立有無をrepoから判定できない, 両解釈: (A) trigger未成立の正当なdeferred、(B) 将来義務を運ぶcarrierがない黙落ち候補}
- {id: X2-49, 迷いの内容: 現在worktreeは消えているが処分記録がない, 両解釈: (A) 実体消滅をdoneと推定、(B) doneはfile:line/commit必須なのでunresolved。後者を採用}
- {id: X2-64, 迷いの内容: 元の監査全文は復元不能, 両解釈: (A) 未完、(B) F20付き再構成へ明示置換。phase3.md:71-75が代替完了を直接記すため superseded}
- {id: X2-84, 迷いの内容: 各時点のpushは別コミット集合だが同じ人間所有境界, 両解釈: (A) 全発生を別原子として数える、(B) 後続push判断が旧判断を置換する同一系列。後者でmerged-fromとした}
~~~~

### X3_report.md

~~~~text
## 判定に迷った項目

- {id: X3-24, 迷いの内容: `docs/phase3.md:66-70` の floor 実測列を暗黙 carrier と数えるか, 両解釈: 「実測直前」の従属 step として live と読む余地はある／しかし最終承認そのものが列挙されず、黙って実測へ進めるため high 候補とした}
- {id: X3-45, 迷いの内容: driver の abort reason 閉表が report 偽装面も間接的に閉じるか, 両解釈: 正規 driver 出力だけなら `_outcome_for` が制限する／report は独立 artifact verifier なので `bench-failed` branch 自身の reason 非検査は元の完了述語を満たさない}
- {id: X3-53, 迷いの内容: protocol 実凍結が将来 extime を固定するため continued とするか, 両解釈: 凍結 bytes が結果的に固定する／現 validator は任意正整数を受理し「experiment_numbers 裁定後の束縛」は未実装なので unresolved とした}
- {id: X3-54, 迷いの内容: 個別 branch の push を done と数えるか, 両解釈: 各成果は local main に統合済み／origin は 23 commit behind で push 自体は未完。ただし末尾除外項目の最終 push が全統合分を包含するため superseded とした}
- {id: X3-69, 迷いの内容: standing rule を terminal に数えられるか, 両解釈: checker 実装・文書化は done／「新 script ごとに起動前実行」は継続義務で、指定 live carrier がないため candidate とした}
- {id: X3-74, 迷いの内容: 台帳の「S1 発火時」が原出所に忠実か, 両解釈: cross-protocol trace-hook という核心は忠実／発火条件は 6/18 の逐語ではなく後続 phase 分類から追加された派生要約}
- {id: X3-75/X3-76, 迷いの内容: 台帳の「protocol 別 calibration が部分吸収する」の射程, 両解釈: thread/protocol 再較正には部分吸収が成立／K 感度は別パラメータで吸収されないため child を分離した}
~~~~

### X6_report.md

~~~~text
## 判定に迷った項目

- {id: X6-01/X6-02, 迷い: source 自身が「実用上十分」と述べるため rejected とも読める, 両解釈: 条件付き改善案としては deferred(trigger)。明示的な「採らない」裁定ではないため rejected にしなかった}
- {id: X6-10, 迷い: settle boolean の fails-closed 化自体は未実装, 両解釈: unresolved とも読めるが、より直接的な competing-process admission が pipeline まで昇格したため superseded とした}
- {id: X6-19, 迷い: 後続 S1/8a/8b が複数動作点を扱う, 両解釈: 話題は類似するが「backoff の効く範囲＝abort閾値」という当該完了述語を直接満たさないため unresolved}
- {id: X6-43, 迷い: phase3:320-321 の proposed_tests 再開条件が gallery 追記も含むか, 両解釈: proposed_tests 一般は live だが allowlist 反転と間接 thid 型の裁定は明示されないため carrier なしの deferred とした}
- {id: X6-47, 迷い: 8b が blind/swapped 対照を議論している, 両解釈: 8b は blind を採らず swapped を採用したため当該 prompt 修正は未発火。将来 blind 設計への deferred とした}
- {id: X6-94, 迷い: strict-v2 C3 の大半は実装済み, 両解釈: done とも読めるが、同じ親裁定が残した reps/extime と正式 floor/run-contract 束縛が現行 phase に残るため partial(children)}
- {id: X6-106, 迷い: user settings は repo 外であり後続 worklog に未記録でもユーザーが変更した可能性, 両解釈: 現物を直接確認して fable のままなので unresolved。権限上は blocked(user) とも分類可能だが、依頼済みなのに live carrier が消えた点を優先した}
~~~~
