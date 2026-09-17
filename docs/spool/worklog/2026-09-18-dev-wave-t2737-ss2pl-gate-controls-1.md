---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2737-ss2pl-gate-controls
seq: 1
title: [T-2737] SS2PL runner の condition gate 問題の対照材料 — (ii) define 差分化の試作は非 inert 4 軸を patch だけで green にし、inert (S) は stock に ycsb target が無い限り構造的に未成立 (登録簿 target=tpcc の診断でも残差 1 行)、(iii) warm-up は既存 helper prepare_masstree_fetchcontent 1 回で前処理失敗が解消 — 計算ノード 2 job・45 cell、docs のみ (branch worktree-dev-wave-t2737-ss2pl-gate-controls、実装面差分 0 byte、変異 matrix 免除)
---

## 本文

- 起点はユーザー裁定 D2120 項 12 と `/dev-wave [T-2737]` 引数。一次資料は `output/insights/2026-09-17/t2644-ss2pl-wfg-connect/README.md` §5 の 1〜3。成果は `output/insights/2026-09-18/t2737-ss2pl-gate-controls/README.md` (採否は書かず、§6 の 1 表と §7 の裁定パッケージ案まで)。
- **先頭の限定 (段 3 / 段 6 レンズ A、親が採用):** D2120 が要求する「stock 側 `ycsb_ss2pl.exe` target / owner TU の成立を含む比較」は gate 不変では構造的に成立しない (stock の ss2pl は `WORKLOADS bomb tpcc`)。登録簿 `target` を `tpcc_ss2pl.exe` に差し替えた shadow の結果は機構診断であり、測定する ycsb TU の「stock 逐語」の認証にはならない。
- 実測 (計算ノード job 2 = `0:5051.nqsv` bnode048、probe 144 秒、45 cell すべて予測と一致): (a) 非 inert phase1 の 4 軸は試作 patch (revS) だけで `requested-default-preprocess-different`、raw-measurement admission=true (現行 patch は IMPL/WFG が `dependency-closure-drift`、DLR が `compile-command-drift`)。(b) inert S は現行登録簿で `owner-tu-unresolved` (KIND は companion を stock へ渡すので `configure-failed`)、shadow target=tpcc + companion 除去でも `stock-inert-mismatch` で gate の evidence `root_diff_line_count=1` (login diff では `ERR` macro の `__LINE__` 97→154)。abort 増分を無条件除去した対照版は 218 行、現行 patch は 3,666 行。(c) KIND は companion ありで S が C、companion なしで phase1 が `preprocess-bytes-identical` — IMPL に従属する軸は同じ登録簿で S と phase1 を両立できない。(d) pristine staging では 8 cell とも `preprocess-failed` (`config.h`)、`buildcache.prepare_masstree_fetchcontent` 1 回 (13.7 秒) の後は stock / patched 両木の前処理が通る。
- 段 4 直前の裁定 inbox 再走査で D2131 (同日) を発見: condition gate を通す 9 driver と t316 probe はすべて `prepare_masstree_fetchcontent` で masstree を準備してから関門へ供給しており、SS2PL runner だけが欠く。(iii) の実体はこの 1 段を足すこと。
- runner の静的契約: revS は `validate_abort_counter_ownership` に拒否 (token 走査は `#if` を評価しない)、abort 無条件版は受理されるが S の gate 比較は 218 行。「S の stock 一致」と「abort 所有権契約」は現行のままでは両立しない。S build の `_wfg_absence_evidence` は accepted (`wfg.cc` は CMake 条件付きのまま。段 3 レンズ A が plan の無条件化を runner の source 名検査に抵触すると指摘)。
- 段 3 レンズ A/B (real 4 + 8)、段 6 レビュー A/B (real 7 + 4) はすべて記述の限定・件数訂正で閉じ、code fix・再投入は 0 件。段 6 fix は 2 巡: fix1 = `insert()` の stock 復元 (残差 2→1 箇所)、fix2 = warm-up の `FETCHCONTENT_BASE_DIR` を mkdir (job 1 = `0:5036.nqsv` bnode022 が内部例外、plain build 後の 20 cell は有効)。
- probe・試作 patch 2 本は repo へ入れず job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/probe/`) に置き、insight の `verbatim/` に `.md` 逐語 (sha256 付き)。実装面差分 0 byte のため変異 matrix は免除 (DW-S04)、受入全走は実施 (結果は land 時の receipt)。
- 工数: 親 Claude 1 context、Codex 子 8 (plan 1、consult 2、author 1、fix 2、review 2)、計算ノード job 2 (各 150 秒)。06:20 起動。

## 次の一手差分

### 更新

- [T-2737] **P2・ユーザー裁定待ち (再提示)**: 対照材料は `output/insights/2026-09-18/t2737-ss2pl-gate-controls/README.md` §6 の 1 表と §7 の裁定パッケージ案。(iii) = runner に `prepare_masstree_fetchcontent` を 1 段足す (単独では `controls` は動かない)。(ii) 非 inert 側 = 試作 patch の a〜d を本 patch へ (phase1 型 arm だけ通る)。(ii) inert 側 = 登録簿 target の差し替え (認証 TU が測定 TU と別になる隙間)、KIND の従属を解く軸設計 (runner の軸表が変わる)、残差 1 行 (`__LINE__`) の解消、abort 所有権契約か S 一致のどちらかを譲る、の 4 点にユーザー判断が要る。gate 本体と `controls` mode は現行のまま。
  base: 3713d81560e34c49352649c5544a9d3be65c3369c0d5a4c1c499244a820babed
