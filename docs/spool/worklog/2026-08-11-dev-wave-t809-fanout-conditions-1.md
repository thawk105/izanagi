---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t809-fanout-conditions
seq: 1
title: 8c trial の workload fan-out の実行条件を明文化した — 探索 pilot の N 起動だけを条件付きで許し、build 付きと 6 node 散らしは禁止のまま (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t809-fanout-conditions)
---

## 本文

- **依頼は [T-809] の条件明文化** (2026-08-11 /rulings 第 16 回で RP-1〜6 が全問親推奨どおり裁定済み)。
  評価 wave (434) の結論どおり本体 loop を割る実装はせず、`docs/pegasus-runbook.md` §7.5 と
  `docs/phase3-s8c-autonomous-trial-runbook.md` §5 の 2 箇所だけを書いた。**実装差分ゼロ。**
- **§7.5 (運用規範)**: 許すのは `--workloads` 単数の探索 pilot を N 起動する形だけで、
  足りないのは起動側でなく検証側であること (RP-1 (a))。**build を伴う fan-out は許さない**
  (RP-2 (a))。**正式系列 6 trial を 6 node へ散らす読み方は採らず**、配置は着手時に prereg 側で
  再評価する (RP-3 (c))。従来の「そのまま別 job へ割るのは未承認」を置き換えた。
- **8c runbook §5 (trial 固有)**: 割ってよい条件 6 項と、再投入の経路別定義 (RP-5 (a))。
  部分成功の意味論は変えていない (RP-4 (a))。
- **敵対レビュー 1 本 (codex `gpt-5.6-sol`, reasoning=high, 325 秒) が blocker 2 件を返し、
  両方とも real と裁定して採用した。** (i) **`--run-root` を明示すると
  `IZANAGI_EXPLORATION_OUTPUT_ROOT` の git 祖先拒否は走らない** — 親の初稿は「exploration output
  root は repo 外かつ非 git」と書いて機械 gate があるかのように読ませていた。実コードで確認済み
  (`p3_autonomous_workload_trial.py` は `--run-root` があれば `_resolve_exploration_output_root` を
  呼ばず、admission は `layout.py` の明示引数なし経路だけ)。(ii) **request ID は投入結果なので
  「投入前に書き出す」は実行不能** — 逐語どおりでは条件を満たす fan-out が存在せず、後書きを
  事前登録と呼ぶ運用を誘発する。slot と nonce を先に固定し、投入直後に request ID と receipt を
  slot へ束縛する形へ直した。should 4 件 (失われるのは group 保証であって process 内検査ではない、
  `lifecycle-start-once` は exploratory に非適用、freshness gate は既存 checkpoint がある場合の話、
  欠落 artifact のある group の扱い、未測定を「効かない」と断定しない) も全件採用した。
- **受入の要否判定**: `orchestrator/tests/test_check_docs.py::test_real_repo_clean` と
  `::test_normative_exact_section_pins_accept_real_repo` が実 repo に対して `tools/check_docs.py` を
  走らせるため、編集した docs を読む node が実在する。よって免除せず実走した。
- **受入全走は本記録 commit を含む最終 tip で 1 走に集約した。** 受入 lease の TTL は 2400 秒で
  1 走 1055〜1273 秒のため 2 走が入らず、記録前に走らせると land が要求する
  「tested_tip == wave head」を満たせなくなる。**したがって本エントリは受入の数値を持たない**
  (未実施の欄を作らない規律に従う)。走行結果は同 wave の handoff と land 報告に残した。
  この順序制約は段 8 の改善候補として記録した。
- 段 2・3 と変異 matrix は軽量版として省いた。実装面がなく (docs-only)、択一は全問裁定済み、
  受理集合も変わらないためである。凍結逐語は
  `output/insights/2026-08-11_t809-fanout-conditions/` (brief・レビュー prompt・レビュー逐語)。

## 次の一手差分

### 完了

- [T-809] 8c trial の workload fan-out の実行条件を 2 runbook へ明文化した。RP-1〜6 の全項を反映し、
  実装差分はゼロ。
  remaining: none
  base: 3cbd13a8d044dbc4fd3c61bac5cfc2a2a5062beccc19fdd3b2c08028cf8406de

### 新規

- {{T:runbook-request-id-pre-submission}} **P3・ユーザー裁定待ち**: `docs/pegasus-runbook.md` §7.5 の
  一般規範側にも「投入前に期待集合 (…各 request ID…) を書き出す」という逐語が残っている。
  request ID は投入結果なので事前には書けず、逐語どおりでは条件を満たす並行投入が存在しない。
  8c 固有の条件文は本 wave で slot + nonce 先行固定へ直したが、**§7.5 の一般規範は別裁定
  (2026-08-11 の並行投入裁定) の記録なので触っていない。**同じ直し方を一般規範へも適用するか、
  現行逐語を意図どおりとして残すかはユーザー裁定。scope 外 real 所見として敵対レビューが検出した。

- {{T:acceptance-record-order-contract}} **P2・ユーザー裁定待ち**: 段 8 の自己改善候補。
  `DW-S04` は「受入全走を段 7 の記録前に実走し、結果を worklog へ書く」と定めるが、
  `dev_wave_land.py` は `wave head == tested_tip` と `tested_main..tested_tip` の exact closure を
  要求する (`_verify_heads` / `RC_AUDIT`)。記録 commit は受入の後に載るので、**1 走では
  「記録に数値を書く」と「tested_tip が実際に走った tip である」を同時に満たせない。**
  受入 lease の TTL 2400 秒に対し 1 走 1055〜1273 秒なので 2 走は TTL を超え、
  2 走目前の再 claim が要る (これは既知)。択は (a) 2 走 + 再 claim を正本へ明記する、
  (b) 記録 commit を tested_tip の後に許し land 側で ledger 専用 path を例外扱いする、
  (c) 数値を worklog へ書かず insights と land 報告に残すことを正本にする。
  本 wave は (c) 相当で運用したが、正本が (a) を含意しているため裁定が要る。
