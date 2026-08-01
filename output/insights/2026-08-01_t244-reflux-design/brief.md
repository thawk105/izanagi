# 段 1 brief — [T-244] 規律 3 の還流設計 wave (2026-08-01)

worktree = `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design`
branch = `worktree-dev-wave-t244-reflux-design`、基準 = local main `3c924bb`

## 1. scope

規律 3 の還流設計 v1 (「機序を漏らさずに失敗理由だけを次世代へ還流させる」) を **起草**し、
decisions の新 D + insights の設計本文 + 既存 docs の「未解決」記述の更新として land する。
**コードは書かない** (P1)。理由: 還流の発火条件 `generations >= 2` は D114 が 3 入口で機械拒否
しており、`DW-G04` の「発火条件を満たす既存 artifact path か計測 ID を brief に書ける場合だけ
実装する」を満たせない。よって設計メモに留める。ユーザー裁定も「起草する」である。

## 2. 確定済みユーザー裁定 (worklog (102))

軸 **(i) 主軸 + (iv) 併用**。(i) = 信頼機械が failure を単調な safety constraint へ変換し
generator は理由を読まない。(iv) = campaign-global な disclosure / query budget で総 iteration と
公開 class 数を束縛する。(iii) (候補 batch 凍結) は (i) の補強として後置可。(ii) 単独は規律 3 を
満たさない封じ込めとして却下済み。成果物は必須 7 項目を含む: ①誰がどの field を見るか
②一世代・一 window あたり最大 bit 数 ③accept-reject query の総予算 ④producer は trusted machine か
外部 role か ⑤run・campaign の origin binding ⑥正式 report・WAL へ残す参照 ⑦受容する残余と
不採用案 (A〜D) を再開できる条件。

## 3. 段 1 前提実測 (承認済み裁定の前提、file:line)

1. **recipient matrix (実測)** — `orchestrator/campaign/p3_autonomous_workload_trial.py`
   planner payload `:816-825` = descriptor + `current_perf` (**絶対 throughput**) +
   leading_indicators + whiteboard、coder payload `:843-860` = `gating_spec` + `planner_direction`
   (axis/direction/magnitude の 3 field) + `baseline` (**絶対 throughput**) + whiteboard、
   auditor payload `:897-905` = `working_diff` 全文 + diff_digest + pre-build correctness digest、
   critic payload `:957-967` = harness_result + `critic_digest` **全文**。
2. **cross-generation チャネルは 2 本だけ** — (a) whiteboard (`:815`, `:824`, `:859`)、
   (b) `prior_reverse` (bool) は `:928`/`:939` で proposal file と `drive()` へ行き
   **次世代の planner/coder payload には入らない**。critic の自然文帰属はどこへも還流しない。
3. **whiteboard の型は閉じている** — `p3_s4_loop.py:108-118` の 5 field、`:367-404` が未知 key を
   fail-closed 拒否、`delta_pct≡None` は load 側 `:394-398` と射影側 `:273-286` で二重強制。
   よって「還流はゼロではない」(result enum が既に世代を跨ぐ) が、**理由は 1 bit も渡っていない**。
4. **機械側 failure 事実の在処** — `_preview` `:479-497` (passed / subtype / reason /
   `forbidden_identifiers`)、`run_one_iteration` の outcome (`p3_s4_loop.py:634-668`:
   rejected|certified|aborted|dry-pass + verdict + WAL records)。いずれも **性能でなく正しさ・構造**
   由来である。
5. **制約強制点が既に存在する** — `p3_s4_loop_trigger_gating.py:105-115` の
   `SYNTAX_CONTRACT_FORBIDDEN` + `check_syntax_contract()` が pre-build で候補を機械拒否する。
   (i) の「単調な safety constraint」は新機構でなく **この面の拡張**として設計できる。
6. **campaign-global 状態と origin binding** — 状態は `loop_state.json`
   (`p3_s4_loop.py:339-340`、iteration / start_wall / reverse_recommendations / whiteboard)、
   campaign 同一性は `ident.canonical_preimage(cfg)` が `search_config` を sorted で含む
   (`ident.py:76-100`)。`generation_budget` は既にその中にある (`p3_autonomous_workload_trial.py:437`)
   ため、**disclosure budget を search_config に置けば campaign ID に束縛される**。
7. **WAL** — `wal.log(layout, variant, stage, env_tag, payload)` (`wal.py:499-509`) が append-only。
   `records_by_stage` で stage 別に読める。参照を残す先はここ。

**承認済み裁定の前提を覆す新事実は見つからなかった。** ただし (i) の危険は実測で明確になった —
constraint 文そのものが理由を運ぶ channel になりうる (P4)。

## 4. 不変条件 (緩めない)

規律 2 / 3 / 6、D39 決定 3 (whiteboard は 5 field・機序フィールドを持たない)、D45 (自然文 lint を
唯一の防壁にしない)、D114 の承認上限 `MAX_APPROVED_GENERATIONS = 1` と freshness gate。
本 wave は **受理集合を一切変えない** (docs のみ)。凍結成果物の bytes を変えない。role md
(`.claude/agents/*.md`) は触らない (`review_ledger.py` の `SOURCE_FILE_SHA256` が role 名で pin する)。

## 5. 親の provisional 裁定 (攻撃対象)

- **(P1)** 実装しない (docs-only)。`DW-G04` 適用が正しいかを攻撃せよ。
- **(P2)** 設計本文は `output/insights/2026-08-01_t244-reflux-design/README.md`、decisions には
  **D116** として要旨 + 必須 7 項目を置く。phase3.md / D114 / 8c runbook の「未解決」記述は
  「設計は確定・実装は多世代開放の前提条件」へ更新する。
- **(P3)** 還流の運搬面は **whiteboard を増やさず**、coder payload の `gating_spec` に追記される
  「機械検査可能な constraint 節」1 本に閉じる。planner へは何も足さない。
- **(P4)** 一世代あたりの公開 bit は 0 を目標にできない (constraint 文は bit を運ぶ)。設計は
  **bit 数を明示的に見積もり**、campaign-global の disclosure budget (iv) で総量を束縛する。
- **(P5)** 受入 = `python3 tools/check_docs.py` + pytest 全走 (Pegasus gen_S 計算ノードへ
  `tools/pegasus/dispatch_compute.py --task tests`)。docs-only ゆえ変異 matrix は対象外
  (`DW-S04` に従い worklog へ射程を明記)。

## 6. 成果物影響 (`DW-G05`)

本設計を land しない場合、多世代開放の前提が設計不在のまま残り、certified 選択の探索は
**1 世代 = single-shot に固定**され続ける (台帳の受理 variant 数と proof chain の世代数が
恒久的に 1 のまま)。本 wave 自体は docs のみで、台帳・レポートの既存の値・受理集合・参照は
1 つも変えない。

## 7. 並列分割

段 2 = codex plan 1 本 (read-only)。段 3 = 敵対相談 2 本 (レンズ A = 情報フローと bit 会計の
実効性・恒真性、レンズ B = 既存実装との整合と実装可能性・規律 2 の gate 探索耐性)。
実装子なし (docs-only。本文は親が書く)。段 6 = 敵対レビュー 2 本 (設計本文と docs 差分に対して)。
