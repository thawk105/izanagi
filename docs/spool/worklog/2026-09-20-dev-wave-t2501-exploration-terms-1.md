---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2501-exploration-terms
seq: 1
title: [T-2501] runbook の「exploration campaign」(campaign の use class) と D1813 の「探索」(標本への帰属) が別語である件を、runbook §7.9 の定義・対応表と glossary 1 項目で整理した — 探索走 t2418-explore は use class では official、A-1 対測定は use class が exploration でも標本帰属は宣言では決まらない (docs のみ、branch worktree-dev-wave-t2501-exploration-terms、実装面差分ゼロ = 変異 matrix 免除、段 6 read-only review 1 本 must-fix 1 / should 4 全件反映)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数の逐語は insight `verbatim/T-2501-origin.md`) の範囲で 1 wave。裁定 = D1879 (探索走 T-2418 が範囲外として
  返した 4 件のうち語の整理だけ。working bytes 拘束と `run_kind == "extended"` 必須化は採らない)。一次資料は
  `output/insights/2026-09-20/t2501-exploration-terms/README.md` (結論・段構成・レビュー裁定・検査の射程・逐語)。decisions fragment は無し
  (新しい設計判断なし。語の区別自体は D1848 理由 5 項目目が既に名指ししていた)。専用 handoff は job dir (`~/.claude/jobs/f5ab0160/tmp/handoff-t2501.md`)。
- 起点 local main `f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad` (worktree 作成時の `7baf3f375` から開始 gate 直前に 7 commit 進んでいたので ff-only で揃えた)。
  開始 gate rc 0 (20:53:36 JST)。段構成: 軽量版 (段 1 → 4 (docs のみ実装) → 5 親起草 → 6 read-only codex review 1 本 → 7 → 8 → 9)。
- **書いたこと。** `docs/pegasus-runbook.md` に `### 7.9` を新設: 語 A = campaign layout の use class `exploration` (`declared_use_class`、閉表
  `official` / `exploration` / `qualification` / `dry`、materialize は前 2 値、出力先の namespace と解決規則を決め、`IZANAGI_EXPLORATION_OUTPUT_ROOT` は
  この語)、語 B = D1813 の測定段階「探索」(静的 backoff 1000 マイクロ秒超の 2 段構成の第 1 段、`run_kind = t2418-explore`、探索値は正式標本へ混ぜず開示だけ)、
  第 3 の表記 (`submit_b10_backoff_grid.sh --explore-campaign` と `b10_backoff_static_tail_formal.py` の検査文言 `mode source must be exploration` は語 B、
  `layout.py` の `ExplorationCampaignLayout` docstring「探索専用 layout」は語 A)、対応表 5 行、読み分け。§8 の該当 checklist 項目へ §7.9 へのポインタ 1 句。
  `docs/glossary.md` §4 (campaign 項目の直後) に 1 項目 (機体固有値なし、対応表は runbook へ委譲)。
- **一次資料で確かめた中心事実。** (1) 探索走 `t2418-explore` は `backoff_extended_sweep.py` が `declared_use_class="official"` を渡し、job 本体
  `tools/pegasus/b10_backoff_grid.sh` が `IZANAGI_OFFICIAL_OUTPUT_ROOT` を export する — use class では `official` (D1848 却下肢 3 のとおり exploration root へ
  移していない)。(2) A-1 対測定 `paper_story_a1_paired.py` は `DECLARED_USE_CLASS = "exploration"` を宣言し job script が `IZANAGI_EXPLORATION_OUTPUT_ROOT` を
  export する — use class の `exploration` は「非正式な標本」を意味しない (A-1 の標本が正式か否かは判定しない)。(3) module-level `DECLARED_USE_CLASS = "exploration"` は
  7 module (s4 driver 族 5 + 8c + A-1 対測定。レビューが AST 走査で 7 件一致を独立確認)。grep の逐語は insight `verbatim/parent-measurements.md`。
- **段 6 レビュー (codex gpt-6-astra / medium、7 call、289 秒) は所見 7 件 = must-fix 1 / should 4 / nit 1 / 記録 1、refuted 0、全件採用。**
  must-fix (R-1) は「`IZANAGI_EXPLORATION_OUTPUT_ROOT` の process pin を全解決経路に広げて書いた」— `layout.py` の
  `_resolve_exploration_output_root` は env 経路だけ pin し、明示引数と repo 既定は対象でない。should は env cell の限定 (R-2)、「code 中の『探索』」を
  2 つの docstring に限定 (R-3)、「直交性」行を「読み違えない点」へ (R-4)、glossary の namespace を `<base>/…` + base 既定と語 B の対象を静的 backoff に限定 (R-5)。
  5 件とも是正案の逐語で反映し、差分が是正案と一致することを親が目視照合した (焦点再レビューは投じていない)。nit (R-6) と記録 (R-7) は brief の記録の射程の話で、
  runbook 本文は正しく、insight §2 / §4 に射程を書き直した。
- 検査: `check_docs` 違反なし (commit 前・fix 後)、`git diff --check` 空、`check_ai_provenance.py` は message-file 2 回とも rc 0・全史 (commit 1 後) 12061 件で
  新規違反なし、三軸語走査は hit が既知 4 file (s8b-floor-official の 3 file と `holdout_freeze.v2.g1.json`) だけで本 wave の file を含まず positive_control 233。
  走査 report は三軸語を含むため insight へ写していない (F1013 型の回避)。
- 事故 (自分起因、実害なし): brief と裁定の見出しに書いた時刻 (21:05 / 21:12 JST) が推定値で、実際はどちらも commit 1 (21:04:51) より前。逐語は改変せず
  insight §2 に訂正を書いた (failures fragment で F1 へ再発追記)。以後 `date` を叩いてから時刻を書く。
- 受入全走は記録 commit 後の tip で 1 走 (結果は land の受領証)。
- 限界・言わないこと: 各 producer の実行時経路は測っていない (静的 grep のみ)。第 2 段 (`t2500-tail-formal`) の投入状態は判定しない。語の整理は
  読み手の誤解を消すだけで、機械可読な区別は D1848 の `declared_use_class` field が既に担う (field も consumer も変えていない)。
- 工数: codex 1 本 (review、7 call)、計算ノード job = 受入全走のみ。

- [T-2501] runbook §7.9 と glossary 1 項目で「exploration (use class)」と「探索 (D1813)」の定義と対応を着地した。D1879 が採らない 2 件
  (working bytes 拘束・`run_kind` 必須化) は実施していない。

## 次の一手差分

### 完了

- [T-2501] runbook §7.9 (定義 2 + 第 3 の表記 + 対応表 + 読み分け) と glossary §4 の 1 項目を着地した。凍結成果物・正式 consumer の受理集合・
  `run_kind`・コードは変えていない。
  remaining: none
  base: 19f323902e7a3f70e5e4ac050f2f91b0ddc4fd9b2170df82f138024e096d8c57
