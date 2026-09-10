## 所見

全件検索は `grep -rln` で対象ファイルを抽出後、各ファイルを `grep -n` で再確認した。pytest は未実行であり、緑とは判定していない。

[B-1] 反転閉包は4面ではなく5面ある。  
(a) 主張: C12 の現行 repo tripwire に、計画が数えていない overlay 検査がある。  
(b) 根拠: `orchestrator/tests/test_s8c_preregistration_predicates.py:139,169,196,607`、特に `:643` の baseline 不在 assertion と `:650`。集合 pin は `orchestrator/tests/test_s8c_preregistration_invariant.py:321-329`。  
(c) 放置すると実装後に `baseline_calls` が空集合でなくなり受入が赤くなる。削除すると allocation consumer の現在地を pin する検査が失われ、status/reason 台帳が漂流する。  
(d) overlay を「現行 HEAD に両 call が存在する」正例へ反転し、anchor 差し替えと不在 assertion を廃止する。synthetic absence test は維持する。  
(e) 自信度: high

[B-2] C04 の `reject_started_trial` は契約にあるが、判定器も実装計画も call edge を閉じていない。  
(a) 主張: 契約は crash handler と preflight の3 consumerを要求するのに、判定器は2 consumerしか検査しない。  
(b) 根拠: `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:164,175-176`、`orchestrator/campaign/s8c_preregistration_evidence.py:1611-1621`。計画も `s2-plan.md:32-37` では定義追加、`:53-58` では mark/forbid 呼出しだけである。  
(c) 放置すると `reject_started_trial` が死んだ定義でも C04 が `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` へ進み、preflight の受理集合と拒否時点を誤って台帳へ反映する。  
(d) `run_trial` preflight から実際に呼び、判定器にも `(trial_registry_path, "reject_started_trial")` の reachability を追加する。定義だけの負例も追加する。  
(e) 自信度: high

[B-3] sealed admission の「一度だけ」は、現行の全 site/env 権威を閉じていない。  
(a) 主張: `_trial_launch_admission`、origin preflight、transport gate、worker が別々に site/env を再解決するため、呼出し削減は意味保存ではない。  
(b) 根拠: `p3_autonomous_workload_trial.py:986-987,1081-1082,1997,2019,2430,2804,2811,3338,3367`。site 列を2回消費する既存 test は `test_p3_autonomous_workload_trial.py:1802-1827`、call count pin は `test_claude_transport.py:1598-1643`。  
(c) 放置すると site A で作った campaign identity を site B の contract/transport で実行し、campaign_id、reservation 要否、reject/accept 集合、report の certified 候補が変わる。  
(d) `run_trial` の真の境界で admission を解決し、launch admission/origin/transport/worker 全てへ渡す。直接 worker 呼出しの `None` fallback は残し、site sequence と identity の不変 test を追加する。  
(e) 自信度: high

[B-4] Pegasus fixture の修正対象は計画の1件ではなく、少なくとも2件ある。  
(a) 主張: single-process contract を通る既存 `run_trial` test が予約 keyなしで残る。  
(b) 根拠: `test_p3_autonomous_workload_trial.py:1971-1987` は Pegasus を強制するが予約 keyなし。`test_claude_transport.py:115-124,1588-1620` の `_source` も `PBS_JOBID` 以外の予約 keyを持たない。Pegasus の `single_process=True` は `env_contract.py:253-260`、必須8 keyの読込は `reservation.py:159-175`。  
(c) 放置すると意図した transport error または complete report まで到達せず ReservationError で止まり、report、call count、lifecycle assertion が赤くなる。  
(d) 共有 valid reservation fixture を追加し、PBS job、boot、deadline と8 keyを整合させる。Linux/OTHER fixture は予約不要のままにする。  
(e) 自信度: high

[B-5] C12 の静的 consumer 判定は launch 前支配性を証明しない。  
(a) 主張: `_c12_allocation_binding_verdict` は reachable call の集合しか見ず、call が campaign/provider 起動後でも通す。  
(b) 根拠: `s8c_preregistration_evidence.py:1747-1762`。実際の campaign identity と driver 到達は `p3_autonomous_workload_trial.py:2817-2836,3153-3168`。計画の負例案は `s2-plan.md:83-97` にあるが、現時点では未実装。  
(c) 放置すると判定器だけが通り、予約検査前に起動した測定が report/ledger の certified 選択材料へ混入し得る。  
(d) 各 mismatch test に provider/campaign 未起動 assertionを必須化し、late-call mutation を拒否する。必要なら専用 preflight helper の位置を静的に pin する。  
(e) 自信度: medium

[B-6] 上位 PBS/計算ノード launcher は現在の C12 scope に存在しない。  
(a) 主張: 現在の in-repo public caller は `run_origin_trial` と CLI だけで、実運用の compute dispatch 経路は未実装である。  
(b) 根拠: `p3_autonomous_workload_trial.py:3687-3690,3802-3825`、`docs/phase3-s8c-autonomous-trial-runbook.md:103-108`。  
(c) 放置すると将来の PBS wrapper が `run_trial` を bypass した場合、予約なし実行を C12 が検査できず、report の受理集合が別経路で広がる。  
(d) 「全 launcher が sealed admission/run_trial を呼ぶ」か「CLI/public boundary のみを保証範囲とする」かを裁定 package として明記し、dispatch 実装時に別 wave で接続する。  
(e) 自信度: high

[B-7] 並行 wave の衝突は行番号ではなく意味集合にある。  
(a) 主張: t1333 は p3 を +237 行変更し、t1348 は同じ status snapshot/invariant 集合を更新し、t1353 は trial_registry の schema/capability 面を未コミット変更している。  
(b) 根拠: 親 brief `s1-brief.md:168-173`、t1348 brief `s1-brief.md:80-94,123-137`、現行 status dict `test_s8c_preregistration_predicates.py:148-166`、集合 pin `test_s8c_preregistration_invariant.py:43-123`、t1353 branch の `trial_registry.py:48-154,281-320`。  
(c) 放置すると後発 patch が C01/C09/C10/C04/C12 の status、`MACHINE_CONTRACT_FUNCTION_CHECKS`、lifecycle schema のいずれかを上書きし、受入結果または ledger key を誤る。  
(d) 後発側は先行 land を取り込んでから関数単位で再マージし、status は全条件の和集合、CHECKS/EXCLUSIONS は現行 contract から再導出、trial_registry は schema field を保持した上で C04 API を追加する。  
(e) 自信度: high

[B-8] signature の現行呼出しは互換だが、新引数の契約 pin がない。nit。  
(a) 主張: production は `_run_workload` 1箇所、`_finish_trial` 1箇所の keyword call。test は direct call、`**kwargs` wrapper、monkeypatch、AST/inspect pin があるが、`execution_admission=None` 自体は pin していない。  
(b) 根拠: 定義 `p3_autonomous_workload_trial.py:2344,2747`、call `:2472,3614`、direct/wrapper `test_p3_autonomous_workload_trial.py:113-118,1772-1774,1825,4295-4301,6924-6925`、Claude wrapper `test_claude_transport.py:2059-2111,2190-2191`。`functools.partial` の該当利用はない。  
(c) 現状の default `None` なら成果物影響はないが、required/positional 化すると direct fixture と monkeypatch callback が runtime error になり、受入全走が赤くなる。  
(d) `inspect.signature` で両関数の keyword-only、default `None` を pin する。  
(e) 自信度: medium

## 反転・修正が要る箇所の完全一覧

- `orchestrator/tests/test_s8c_preregistration_predicates.py:151,157,165`  
  `C04/C12 = UNSATISFIED + crash/allocation reason`  
  → `C04/C12 = EVIDENCE_UNDEFINED + completion-proof-not-machine-checkable`。

- `orchestrator/tests/test_s8c_preregistration_predicates.py:169,176-177`  
  `C12.status/reason == UNSATISFIED/allocation-enforcement-consumer-absent`  
  → `C12.status/reason == EVIDENCE_UNDEFINED/completion-proof-not-machine-checkable`。

- `orchestrator/tests/test_s8c_preregistration_predicates.py:196,217-220`  
  `_c12_allocation_binding_verdict(...) == (UNSATISFIED, ALLOCATION...)`  
  → `_c12_allocation_binding_verdict(...) is None`。

- `orchestrator/tests/test_s8c_preregistration_predicates.py:607,623-650`  
  現行 HEAD を overlay して baseline 不在を確認  
  → 現行 HEAD の reachable call 集合に `read_binding` と `check_reservation` が実在することを直接確認。anchor 差し替えは削除する。

- `orchestrator/campaign/s8c_preregistration_evidence.py:1611-1616`  
  C04 target `{mark_experiment_indeterminate, forbid_trial_restart}`  
  → 契約を維持するなら `reject_started_trial` も reachability target に追加。判定器を変更しないなら contract/invariant から当該 token を削除する裁定が必要。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:3524-3535,3630-3641`  
  `_record_indeterminate_terminal(...)` を直接呼ぶ  
  → `mark_experiment_indeterminate(...)` が先に `forbid_trial_restart` を呼び、その後 terminalizeして元例外を再送出。

- `orchestrator/campaign/trial_registry.py` lifecycle API  
  `forbid_trial_restart` / `reject_started_trial` 不在  
  → 既存 lifecycle ledger と atomic start check を再利用する2 APIを追加。新 JSON ledger 形式は作らない。

- `orchestrator/tests/test_s8c_preregistration_invariant.py:43-85,87-96`  
  C04 3 tuple が EXCLUSIONS の `declared-unimplemented-token`  
  → 同じ3 tupleを CHECKS へ移し、EXCLUSIONS から削除する。exact set は C09/C10 wave の変更も含めて再計算する。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:2344-2367,2747-2759`  
  `_finish_trial` / `_run_workload` に admission 引数なし  
  → keyword-only `execution_admission: _RunEnvironmentAdmission | None = None` を追加。既存 keyword caller は省略可能にする。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:986-987,1081-1082,2804-2811`  
  各 helper が site/env を独自解決  
  → run boundary の sealed admission を受け取り、identity、origin、transport、worker が同じ値を使う。直接 helper は `None` 時だけ従来 fallback。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py:1772-1774,4295-4301`  
  `site` 不在と `gating_spec_snapshot` だけを pin  
  → `execution_admission` の存在、keyword-only、default `None` も pin。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py:1971-1987`、`orchestrator/tests/test_claude_transport.py:115-124,1591-1620`  
  Pegasus fixture に予約 binding なし  
  → valid `IZANAGI_RESERVATION_*` 8 key と一致する PBS/boot/deadline fixtureを追加。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py:1802-1827`  
  site 呼出し順 `OTHER -> PEGASUS` に依存  
  → sealed site の一回性と T-276 reject を明示的に pinし、呼出し削減で受理挙動を変えない。

- `docs/phase3-s8c-autonomous-trial-runbook.md:103-108`  
  compute dispatch 経路なし  
  → 本 wave では変更せず、上位 launcher 接続を別裁定 package とする。

- docs の逐語 status は `docs/decisions.md:18257,18438`、archive worklog は `docs/archive/worklog-phase3-0817-627.md:94` 等の歴史記録のみ。active ledger test ではないため反転しない。

## 親 brief への反証

- M4: 反証。mark/forbid の不在観測は正しいが、契約 JSON は `reject_started_trial` も要求しており、「C04 consumer は2件」と閉じた説明は不完全。判定器もその call edge を見ていない。
- M6: 反証。現行 predicate の反転面は snapshot、registry、helper、overlay の4面であり、invariant exact setを加えると5面。overlay `:607-650` が未列挙。
- P4: 部分反証。preflight の位置自体は妥当だが、site/env identity の全作業を一つの admission が支配することは、`:986,1081,3338,3367` の呼出し構造から未成立。
- M1、M2、M3の静的到達部分、M5、P1、P2、P3、P5の意味論は今回の静的検査では反証しない。ただし P5 に伴う既存 Pegasus fixture の列挙は不十分。

## 総括

反転対象は、計画の4面ではなく predicate 4面と invariant 集合の計5面。  
最大の実効性欠陥は、契約上の `reject_started_trial` が死んだままでも C04 が通る点。  
sealed admission は全 site-dependent consumer へ渡さない限り受理集合を保存しない。  
Pegasus fixture、PBS dispatch scope、並行 wave の集合再導出を land 前の必須条件にする。  
pytest は未実行であり、緑の報告はしていない。