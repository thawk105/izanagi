# [T-2293] 8c 結線の設計 wave — V-8 (a) が実行形を持たない原因 2 つの解消案

2026-09-05。branch `worktree-dev-wave-t2293-8c-wiring-design`。docs のみ、実装面の差分 0。
検査対象 HEAD は `97ee3cd3a` (plan・レンズの時点)、docs 編集は local main `b152eec77` を ff で取り込んだ後。

- 依頼: D1616 が採った V-8 (a) 「1 query ordinal = 1 campaign run」が現行コードで実行形を持たない原因 2 つ —
  campaign identity が候補の違いを含まず 33 run が同じ identity になり claim で拒否される、identity を分けると origin capability が
  `campaign_id` を 1 つしか持てない — の解消案を `docs/phase3-8c-wiring-design.md` §11 V-8 行と関連節に書く。
- 成果物: 設計文書の追記節「追記 (2026-09-05) — V-8 (a) の実行形: 論理 campaign と物理 campaign run の分離」(§A〜§J) と、
  §11 V-8 行への裁定済みの印。既存 bytes は不変。
- 逐語: `s1-brief.md`、`verbatim/s2-plan.md` (codex plan)、`verbatim/s3-lens-a.md` (整合・実効性)、`verbatim/s3-lens-b.md`
  (正しさ境界・恒真化)、`s4-adjudication.md`、`verbatim/prompts/`。

## 1. 親の実測 (brief 前) — 覆した前提

| # | 前提 | 実測 |
|---|---|---|
| 1 | 「identity が genome を含まない」 | 33 行で変わるのは genome でなく `TriggerGateBinding` (mask / wire)。`Genome("silo", _BASE)` 1 個 (`p3_s4_loop_trigger_gating.py` `_run_one_iteration_resolved`)。ordinal だけが衝突しない (source 行と `m == m_s` の validation 行は同 wire) |
| 2 | 「止めているのは claim」 | Pegasus (`allow_resume=False`、`env_contract.py`) では `_assert_resume_allowed` が同 layout の lock / loop_state / WAL / provenance を理由に claim より先に拒否。同 layout の WAL が `loop.run_campaign` の `done` seed で同 variant を skip する。layout と WAL も分けないと解消にならない |
| 3 | 「run plan に束縛先が要る」 | `TopologyMember.planned_campaign_run_identity` は既に存在し 33 相異を要求するが、production の producer も consumer も参照しない (test は `fixture-run-0000` 等) |
| 4 | 「`execution-provenance/v1` の producer」 | consumer (`reflux_result_evidence.py`) と test fixture (`reflux_origin_fixture_builder.py`) だけ。production の書き手は不在 |
| 5 | 先例 | D1190 (s8b): 効果 key は座標、測定世代は run ごと決定的 (`s8b_holdout_admission.py` `_new_measurement_generation`)。A-1 pilot の `campaign_lock.py` は 1 共有 record に 3 campaign を ordinal で束ねる |
| 6 | 稼働 wave | t1851-unit-a / t524 の両 worktree は orchestrator / docs / tools の未 commit 差分 0 (branch tip の blob hash と作業木 file を照合。隔離 worktree の guard が他 worktree での VCS 実行を拒否するため)。t524 の slot は `campaign_id` 1 つ・`replicate_index == 0`・1 unit に final terminal 1 件 |

## 2. 段 2 plan と段 3 レンズ 2 本

plan (codex read-only、xhigh) は brief の (P1)〜(P6) を概ね採用し、A2 不足 (completeness が素の trial を要求)、A8 重大
(Pegasus の第 2 世代拒否 → executor 必須)、A13 過大、A15 anchor 不足を訂正した。

レンズ A (整合・実効性): blocker 5 (ledger producer FSM 不在、run plan の hash cycle、`drive_iteration` が origin 用に使えない、
report / completeness / Layer 3 / acceptance が単一 campaign 前提、witness normalizer 不在)、must-fix 6 (`trial_registry.py` 変更 0 は誤り、
残時間検査、crash 表現、論理 cfg の受け渡し境界、completeness の gate 名指し誤り、A6 の反例 `spec_slug`)。判定は作り直し。

レンズ B (正しさ境界・恒真化): blocker 6 (provenance 文字列比較は issuer 文字列型の恒真化、envelope の束縛が一方向で差し替え可、
物理 identity が slot / attempt を含まず過去 attempt を流用可、受理集合の拡大を裁定に返していない、`trial` 接尾辞の名前空間衝突、
envelope の write が observation 開始後)、must-fix 2 (completeness の lock 再読は formal terminal より後、mixed WAL shape)。
偽装 (a) は FC05a/b で拒否、(b)(c)(f) は plan を素通り、(d)(e) は差し替え経路が残る。判定は作り直し。

## 3. 段 4 裁定 (要点、全文は `s4-adjudication.md`)

- refuted は「受理集合が広がる」を blocker とする 1 件だけ (D1616 (a) の帰結そのもの。記載義務として §G の表に残す)。
- 設計変更 2 点: 物理 identity の成分を `trial` 接尾辞から `search_config["origin_campaign_run"]` (structured、D75) へ。入力に
  `AttemptSlotCapability.capability_digest_sha256` を足す (D1190 の同型、別 attempt は別 identity)。
- 設計要件: formal consumer は各物理 run の `campaign.lock` から identity を再導出し、envelope を disk から再読し、WAL ref を layout 配下に
  束縛する。順序は slot 予約 → 33 identity 導出 → envelope create-only → digest 束縛 → observation 開始 → executor。残時間検査。
  process crash は非終端 (§7.5)。§8 の capability への digest 束縛は循環のため撤回。
- scope 外 (real): ledger producer FSM、witness normalizer、report / completeness / Layer 3 / acceptance の origin 化 — §9 の未存在層。
  executor の分岐点・origin 専用 entry point・completion 権威 (R2) を §12 の受入要件と裁定パッケージへ。
- 実装 wave が触れる file は `trial_registry.py` (report / measurement-target 部分) を含む → t524 着地後に着手。

## 4. 裁定パッケージ (ユーザーへ返す 4 件、設計文書 §I)

| # | 択一 | 親の推奨 |
|---|---|---|
| R1 | run plan (envelope) digest の durable な束縛先: (a) lifecycle start 行の origin-only optional key (b) ledger `BatchReserved` payload (c) in-process seal のみ | (a) |
| R2 | origin cell の completion 権威: (a) origin 専用 completion (issued capability + formal receipt + 33 `campaign_runs` の lock / WAL 再検査) (b) 33 物理 campaign に通常 Layer 3 admission | (a)。(b) は P6 の qualifying rejection と矛盾 |
| R3 | `execution-provenance` の schema 世代: (a) v2 新設、v1 は historical decoder (b) v1 in-place | (a) |
| R4 | (確認) 受理集合が動く 3 写像 (q 別 claim / layout、native WAL shape、origin report 形) を D1616 / D1555 / §6.5 の範囲内として実装 wave へ渡してよいか | 可 |

V-6 / V-9 / V-10 は未裁定のまま。発行 3 条件 0/3、本番 authority 0 件、結線実装 wave の起票制限は不変。

## 5. 検査

- `python3 tools/check_docs.py`: 編集前 rc=0 (21 s)、編集後 rc=0 (違反なし)。
- 焦点走 `orchestrator/tests/test_check_docs.py`: 571 passed / 3 skipped (計算ノード dispatch、request 978596)。
- 実装面の差分 0 につき段 5・6 と変異 matrix は免除 (DW-S04)。
- codex 子 3 本 (plan 1、consult 2)、wall 601〜853 s、model call 35〜57、attempt 各 1。receipt は job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/artifacts/`。

## 6. 名乗らないこと

- 結線の完了、発行 3 条件の充足、P6 の発火、本番 provisioning。本 wave が閉じたのは「V-8 (a) の identity / capability 衝突の解消案」だけ。
- ledger producer・witness normalizer・renderer の設計。§9 の「未存在」のまま。
- 33 run の実測費用 (T-2261 の値を引用しただけ)。
