# 段 1 brief — [T-2159] C05 の schedule 正本を新設する

base: local main `24b31d2a37353d63a4f715ed2170d13e25df3fe3` /
worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority`

## scope

1. `p3_autonomous_workload_trial._load_s8c_schedule_authority` を、引数 `root` を捨てて必ず例外を
   送出する現状から、**実在する schedule 正本を解決する経路**へ置き換える。返す形は既存 consumer が
   要求する 4 key 厳密一致 (`ledger_path` / `schedule_sha256` / `cells` / `limits`) のまま変えない。
2. 解決は改竄検知つきにする。committed artifact bytes を `s8c_schedule.verify_schedule` の
   byte 完全一致再生成で検証し、`consume_schedule` を通してから budget shape へ射影する。
   検証を通さない受理経路を作らない。
3. C05 の到達性要求 (`run_trial -> load_schedule / verify_schedule / consume_schedule`) を満たす配線。
4. 予算数値と `master_seed` は事前登録 §5 を機械 parse して取り、**未記入なら理由別に fail-closed**。
5. runbook の stale な 1 行 (`docs/phase3-s8c-autonomous-trial-runbook.md:71`「12 述語の SATISFIED が
   0 件」) を実測値へ直す。

## scope 外 (触らない)

`output/s8c-preregistration/schedule.v1.json` の生成・commit、事前登録 §5 の記入、
`SATISFIABLE_CONDITION_IDS`、`s8c_preregistration_evidence.py` の評価器本体、
証拠契約 JSON、8b ratified freeze の発効、C06 予算値の決定、仮想リスク向けの gate・台帳・一般化。

## 確定済みユーザー裁定

- **D1448 (2026-09-02):** 引数を捨てて必ず例外を送出する schedule 権威の解決経路について、
  C05 の schedule 正本を新設する。却下: 例外送出のまま据え置く。
- ユーザー引数: 実装面なので Codex author を立てる (D95)。本題の実装だけ。runbook の stale も同 wave。
- **絶対規律 2:** 述語を通すために受理集合を広げる方向は採らない。

## 実測した新事実 (裁定文・worklog 1184 に未記録。段 4 で再裁定する)

- **N1.** 12 述語の実測 (HEAD): C10=SATISFIED、C03=UNSATISFIED、残り 10=EVIDENCE_UNDEFINED。
  C05 = `EVIDENCE_UNDEFINED / schedule-schema-absent` (artifact 不在の第 1 分岐)。
- **N2.** `_evaluate_c05` は全条件を満たしても終端が
  `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` であり、**構造上 SATISFIED を返さない。**
  したがって本 wave は C05 を SATISFIED にできない。できると書いた成果物を作らない。
- **N3.** `registered-effective` の admission は発効済み事前登録 capability を要求し、それは 12 述語
  全充足を要求する。`SATISFIABLE_CONDITION_IDS = {"C10"}` が C10 以外の SATISFIED を ERROR へ倒すため、
  **本経路は上流 (D959 の (a)) で塞がったままである。** 本 wave の実装だけでは正式起動は通らない。
- **N4.** D992 の前提である共有 8b ratified freeze は今も未発効
  (`load_ratified_freeze()` → `[no-active] live active pointer が無い (v2 未発効)` を実測)。
- **N5.** 事前登録 §5 の「累積ベンチ実時間の総上限と arm/holdout ごとの上限」「master_seed」は
  **未記入**。よって本 wave が作る解決経路の**受理分岐は、人が §5 を埋めるまで production で発火しない。**
  ただし事前登録 §6.6 は「値の欄だけ埋めて consumer を作らない形は拒否」と定めており、
  consumer を先に作る順序は事前登録自身が要求している (DW-O13 の値域記録)。
- **N6.** T-1380 (2026-08-27) が挙げた 18 key authority の 3 矛盾は現行コードでも成立する。
  `LEAKPROOF_CONTEXT` は文字列だが authority は object を要求、`_whiteboard()` は正式初期状態で
  空配列を返すが authority は非空を要求、`descriptor_binding` は cell ごとに異なるが authority は
  全 cell 共有の単一 mapping を要求する。**これが本 wave の中心的な設計択一である。**

## 不変条件

- 検証を経ない受理分岐、恒真な保証、artifact を decode しない「置けば通る」経路を作らない。
- 凍結 bytes と証拠契約 JSON を変えない。`s8c_preregistration.py` /
  `s8c_preregistration_evidence.py` / `s8c_generation_projection.py` は campaign lock の
  enforcement source closure (`campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS`) にあるため、
  本 wave では編集しない。編集が不可避と判明した場合は段 4 へ戻す。
- trace-enabled 正しさと trace-disabled 性能の分離、verifier anomaly 即 reject を緩めない。
- 値を発明しない。§5 の数値・master_seed・campaign_id・freeze_id を実装側で決め打ちしない。

## (P1) 親の provisional 裁定 — 攻撃対象

- **(P1-a)** `leakproof_context` は値を発明せず object へ包む射影 (`{"text": LEAKPROOF_CONTEXT}` 相当)
  で渡せる。全単射なので authority の実質を変えない。
- **(P1-b)** `whiteboard` の空配列は authority の非退化要求と真に衝突する。「観測なし」を表す
  非空 sentinel を発明するのは値の発明にあたるので採らず、**authority schema 側の非退化規則を
  whiteboard について実値へ合わせる**か、**本 wave では authority 供給を呼び手に残す**かの二択とする。
- **(P1-c)** `descriptor_binding` (initial-state・単数・全 cell 共有) には cell ごとの値でなく
  **全 cell に共通な binding 規則**を入れるのが正しい射影である。
- **(P1-d)** 予算数値と master_seed の機械 consumer は、既存の `s8c_preregistration._parse_section5` /
  `FieldStatus` を使って作れる。新しい parser を書かない。
- **(P1-e)** 本 wave の実装は production で受理分岐が発火しない。したがって正例・負例は
  合成入力の test で示すしかない。**その test が実体を名指ししない (両層 stub の) 恒真緑にならないこと**を
  段 6 の変異で確かめる必要がある。

## 成果物影響 (DW-G05)

放置すると、`registered-effective` かつ build ありの起動は層 3 レポートへ到達せず、8c 正式系列の
certified 選択・材料レポート・試行台帳がこの経路から 1 件も生まれない。本 wave は上流 (N3/N4) を
解かないので**この経路が今すぐ通るようにはならない**が、D549 が「別 wave へ送る」と名指しした
配線と権威解決の側を実体化し、§5 記入 (人の手番) の前提条件を満たす。

## 実アンカー

|対象|場所|
|---|---|
|置き換える解決経路|`orchestrator/campaign/p3_autonomous_workload_trial.py:1856-1861` `_load_s8c_schedule_authority`|
|呼び手と要求 schema|同 `:1864-1935` `_prepare_s8c_budget_inputs`、`:4706-4730` 予約 call site|
|schedule 正本 module (leaf・既存)|`orchestrator/campaign/s8c_schedule.py` 全体 (18 key authority は `:57-83`)|
|C05 評価器|`orchestrator/campaign/s8c_preregistration_evidence.py:2083-2192` (**編集しない**)|
|C05 証拠契約|`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:190-230` (**編集しない**)|
|§5 parser|`orchestrator/campaign/s8c_preregistration.py:771-873` `_parse_section5` ほか|
|budget の型|`orchestrator/campaign/s8c_budget.py:84-129` `BudgetLimits` / `ReservationCell`|
|矛盾する production 値|`orchestrator/campaign/s8c_generation_projection.py:22-26`、`p3_autonomous_workload_trial.py:1707-1709`|
|既存の合成 test 台|`orchestrator/tests/test_s8c_preregistration_predicates.py:44-` `_c05_authority`、`:1211-1234` 負例|
|現状の raise を固定する test|`orchestrator/tests/test_p3_autonomous_workload_trial.py:9053`|
|stale な 1 行|`docs/phase3-s8c-autonomous-trial-runbook.md:71`|

## 分割方針

設計択一 (P1-b) が割れ、正しさ防壁 (C05 の受理) に隣接するので**軽量版にしない**。
段 2 プラン 1 本、段 3 敵対相談 2 本 (レンズ = 受理集合と恒真化 / 権威の出所と順序裁定との抵触)、
段 5 実装子 1 本 (D95 Codex author、code+test を 1 単位で所有)、段 6 レビュー 2 本 + fix。
親は brief・裁定・統合 commit・変異 matrix・受入・記録・land を担う。

## 稼働 wave との重複

編集面 `s8c_*` / `p3_autonomous_workload_trial` / `phase3-s8c` に触れている稼働 wave は t524 のみ。
重なる file は `orchestrator/tests/test_p3_autonomous_workload_trial.py` 1 本で、t524 の変更は
`_t325_prepare_effective_binding` (:7022, :7038) への 2 行追加。本 wave の編集想定域 (:9053 近傍と
新規 test) とは離れており、行競合の恐れは小さい。`s8c_acceptance_receipt.py` は本 wave の対象外。
