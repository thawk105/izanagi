---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: dev-wave-t2293-8c-wiring-design
seq: 1
title: [T-2293] 8c 結線の設計 wave — V-8 (a) が実行形を持たない原因 2 つの解消案を設計文書へ追記した (docs のみ、branch worktree-dev-wave-t2293-8c-wiring-design、実装面の差分 0、裁定パッケージ 4 件)
---

## 本文

- ユーザー依頼は「D1616 が採った (a) 1 query ordinal = 1 campaign run が現行コードで実行形を持たない原因 2 つ (campaign
  identity が genome を含まず 33 run が同じ identity になり claim で拒否される、identity を分けると origin capability が
  `campaign_id` を 1 つしか持てない) の解消案を `docs/phase3-8c-wiring-design.md` §11 V-8 行と関連節に書く。file と関数で名指し、
  択一が残れば裁定パッケージ。実装しない。(b) は再検討しない。稼働中 t1851-unit-a / t524 の前提と食い違わない。docs のみ」。
- **結果:** 設計文書に追記節「追記 (2026-09-05) — V-8 (a) の実行形: 論理 campaign と物理 campaign run の分離」(§A〜§J) を足し、
  §11 V-8 行に裁定済みの印を足した。既存 bytes は不変。設計判断は {{D:v8-two-layer-campaign-identity}}。
  一次資料は `output/insights/2026-09-05_t2293-8c-wiring-v8-identity/README.md`。
- **brief 前の実測で覆した前提 3 点:** (1) 33 行で変わるのは genome でなく trigger wire (`Genome("silo", _BASE)` 1 個)。
  (2) Pegasus (`allow_resume=False`) では同 identity の 2 run 目を claim より先に `_assert_resume_allowed` が拒否し、同 layout の
  WAL が `done` seed で同 variant を skip する → layout と WAL も分けないと解消にならない。(3) `TopologyMember.planned_campaign_run_identity`
  が既に存在し 33 相異を要求するが producer / consumer のどちらも参照しない (束縛先の無い field)。
- **稼働 wave の前提:** t1851-unit-a / t524 の両 worktree は orchestrator / docs / tools の未 commit 差分 0 (branch tip の blob hash と
  作業木 file を照合)。t524 の実験単位 = slot (`campaign_id` は論理値、`replicate_index == 0`、1 unit に final terminal 1 件) と両立。
  t1851 (s8b の `campaign_run_id` / 測定世代) は変更 0。
- **段 2 plan (codex read-only、xhigh) → 段 3 レンズ 2 本 (整合・実効性 / 正しさ境界・恒真化) → 段 4 裁定。** 両レンズとも
  「plan 作り直し」判定 (A: blocker 5 + must-fix 6、B: blocker 6 + must-fix 2)。refuted は「受理集合が広がる」を blocker とする
  1 件だけ (D1616 の帰結そのもの。記載義務として §G の表に残した)。裁定で設計を 2 点変えた —
  物理 identity の成分を `trial` 接尾辞から `search_config["origin_campaign_run"]` (structured、D75) へ、入力に attempt slot
  capability digest を足す (D1190 の同型。同 trial の別 attempt の 33 run が同 identity になる流用穴を塞ぐ)。
  設計要件として、formal consumer が各物理 run の `campaign.lock` から identity を再導出する (provenance の文字列比較は §10 の
  issuer 文字列型の恒真化)、envelope を disk から再読する、順序を slot 予約 → envelope → 束縛 → observation にする、
  残時間検査、process crash は非終端 (§7.5) と書き分ける、を足した。
- **ledger producer の FSM・witness normalizer・report / completeness / Layer 3 / acceptance の単一 campaign 前提**はレンズ A が
  blocker として挙げたが、いずれも §9 の「未存在」層であり本 wave は設計しない (scope 外・real)。executor の分岐点と
  origin 専用 entry point、completion の権威 (R2) を §12 の受入要件と裁定パッケージへ足した。
- **裁定パッケージ 4 件 (§I):** R1 envelope digest の durable な束縛先 (推奨: lifecycle start 行の origin-only optional key)、
  R2 origin cell の completion 権威 (推奨: origin 専用 completion)、R3 `execution-provenance` の schema 世代 (推奨: v2 新設)、
  R4 受理集合が動く 3 写像の確認 (推奨: 可)。V-6 / V-9 / V-10 は未裁定のまま、発行 3 条件 0/3・起票制限は不変。
- **検査:** `tools/check_docs.py` rc=0 (編集前後)、`test_check_docs.py` 焦点走 571 passed / 3 skipped (計算ノード dispatch、
  978596)。実装面の差分 0 なので段 5・6 と変異 matrix は免除。codex 子 3 本 (plan 1、consult 2)、wall 601〜853 s、
  model call 35〜57。local main は wave 中に 97ee3cd3a → b152eec77 (D1644〜D1649、本件に無関係) へ進み、docs 編集前に ff で取り込んだ。
- 段 8 の改善候補: 隔離 worktree の guard は他 worktree での VCS 実行を拒否するので、稼働 wave の未 commit 差分は branch tip の
  blob hash と作業木 file の照合で見た (worktree-discipline の memory へ)。docs / reference の変更は不要。

## 次の一手差分

### 更新

- [T-2293] **P1・ユーザー裁定待ち (R1〜R4) → 結線実装 wave**: V-8 (a) の解消案は設計文書の追記 (2026-09-05) 節に確定
  ({{D:v8-two-layer-campaign-identity}})。論理 campaign (座標、1 trial 1 つ) と物理 campaign run (slot capability digest + q から
  決定的に導出、33 個) の 2 層。裁定 R1 (envelope digest の束縛先)、R2 (origin cell の completion 権威)、R3 (provenance schema 世代)、
  R4 (受理集合が動く 3 写像の確認) を /rulings で提示する。実装 wave は t524 着地後、V-7 と R1〜R4 の裁定後に起票する。
  base: 59bca1a9d84b9d8578ad85d261f4a077710149ba8f4f107c0b8070a0ea1d63ae
