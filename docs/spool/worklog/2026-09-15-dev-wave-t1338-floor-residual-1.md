---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t1338-floor-residual
seq: 1
title: [T-1338] 依頼が名指した 3 件は前日に撤去済みで、台帳の残件 3 件には撤去授権が無かった (実装なし、branch worktree-dev-wave-t1338-floor-residual、変異 matrix = 免除 (実装面差分ゼロ))
---

## 本文

- ユーザー依頼は「[T-1338] 受入関門 3 述語の撤去後に残った 3 件を閉じる — per-pair 床値対表の
  exact 検査、floor_budget_snapshot_sha256、oracle driver への expected_perf_sha256 供給。
  既存の正しさ契約の完成に限定し、新しい受入条件を増やさない。着手直前の local main から fresh
  worktree を作る。規律 2 を緩めない。Codex author = D95。本題の実装だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外」。
- **brief 前の実測で依頼の破線節が覆った。** 名指しされた 3 件は前日 (2026-09-14、エントリ 1479) の
  wave が D1985 に従って撤去済みだった。破線節は撤去**前**の持ち越し文
  (`docs/archive/worklog-phase3-0818-643.md:597`) の括弧内をそのまま写していた。台帳が記録する
  実際の残件は別の 3 件 (R1 = driver の floor/budget null refusal、R2 = budget の凍結数値 loader、
  R3 = report の解決経路) で、いずれも**撤去**である。
- **段 2 と段 3 の 2 レンズが独立に「実装対象なし」へ到達した。** R1〜R3 はいずれも現用経路で
  撤去授権が無い。段 4 で実装しないと裁定し、`4→7→8→9` を通した ({{D:floor-residual-no-authorization}})。
  実装面差分は 0 byte で、`DW-S04` により変異 matrix を免除した。
- **親 brief の断定を 5 点訂正した。** (1) D811 の却下選択肢が禁じるのは「床値を空のまま
  `floor-null` の拒否だけを個別に解く」案に限られ、R2・R3 へ拡張できない。R1 の残置根拠は
  D1985 の「残すもの」に置くべきである。(2) **D501 決定 7 の留保 (条件 3 は逐語凍結、再裁定が
  要る) は D510 (2026-08-18 ユーザー裁定) が既に解決していた** — 決定 1 が最終判定から
  between-run floor との比較を撤去し、決定 3 が消える保証 4 件を名指ししている。親が一次資料で
  裏取りした。(3) R3 のアンカーは assertion 1 行ではなく解決経路 :2547–2560 である。
  (4)「R1〜R3 の撤去はいずれも受理集合を広げる」は未立証で、局所述語の削除・経路の破損・
  最終受理集合の拡大は別物である。(5) 床値系列 (D1758〜D2013) の存続だけでは古い撤去要求の
  失効を証明できない — D1985 自身が床値系列と共存しながら 3 述語を撤去している。
- **不在の主張の測定範囲も訂正した。** 親の件数は `orchestrator/` 配下の Python に限った測定
  だったが、repo 全体の件数として読める書き方をしていた。段 3 レンズ B が別 key で取り直し、
  `perf_sha_by_cell` は tracked 6 行 (production 0)、`floor_budget_snapshot_sha256` は tracked
  17 行 (JSON の実 key としては 0 件) と確定した。`expected_perf_sha256` の production 供給元
  0 件は維持され、`pipeline.evaluate` の production caller 5 箇所の列挙で裏づけられた。
  ただしこれは**動的呼出しまで排除する全称証明ではない**。
- **refuted と裁定した所見 2 件。** 「R1〜R3 を残すこと自体が D496 決定 1 に違反する」は、
  3 者とも過去 throughput との比較でないため refuted。「実装なしで返すこと自体が絶対規律 2 に
  反する」も、新たな anomaly 受理も verifier の迂回も立証されていないため refuted。
  **受理集合の拡大一般と、anomaly を見逃す正しさ検証の弱体化は同義ではない。**
- **仮に R3 を撤去した場合の pin 閉包は空ではないことを記録した。** `s8b_oracle_report.py` は
  `generator_versions` の対象であり、`test_ccbench_spawn_sites.py:2959–2964` が
  `s8b_oracle_driver.py` の評価行 1783 を literal で pin している。前 wave が実際に赤にした型で、
  識別子検索にも hash 検索にも掛からない。
- **手順の逸れ 1 件:** `tools/dev_wave_submodule_init.py` が 1 度目に
  `runtime-io-failure: update-no-fetch` で落ちた。submodule は実体まで展開済みで、原因は同 tool の
  30 秒締切 (`_GIT_TIMEOUT_S`) が並行 worktree 作成下の `submodule update --recursive` に足りな
  かったこと。`DW-O08` に従い同じ引数で 1 度だけ再実行し rc=0 を得た。「この worktree では
  初期化できない」とは一般化しない。
- **受入 attempt 1 は `child-green`。** 23662 passed / 68 skipped / 0 failed (tested main
  `0600887d9`、tested tip `83b0e98f0`、非帰属赤 0)。投入時の `/proc/loadavg` は
  213.97 / 218.31 / 206.24 で、同時に 7 wave・10 本の `run_tests.py` が走っていたが赤は出な
  かった。**実装面 0 byte の wave なので、仮に赤が出ても本 wave へは帰属しえない。**
- **land が rc=23 で拒否し、記録と受入の循環が実測で表に出た。** 受入結果を書いた commit を
  `--landing-wave-tip-sha` で足して land したところ、`forward main merge first-parent commit
  must have exactly two parents` で拒まれた。**tested tip より後ろに置けるのは main の forward
  merge だけ**であり、内容 commit は置けない。一方 `DW-S07` が指示する amend は receipt の
  tested tip 束縛を壊す。したがって受入結果は**次の commit へ書き、その tip で受入を取り直す**
  しかない。本エントリはその形で書いており、**本エントリを含む tip での走行結果は本文には
  書けない — 受理された receipt が権威である。**
- **`DW-S07` の「再走値は amend する」は実測と食い違うが、本 wave では是正できなかった。**
  L1 予算の空きは 1 byte しかなく、`DW-O18` への統合は同節が whole-section の exact 契約と
  1000 byte の単節予算を持つため両方に抵触した。D782 が委任する D730 の手順では、既存記述の
  削減が安全義務に触れ、収容例も独立 1 例しかないため、本案件は「実施しない」へ落ちる。
  上限引き上げには至っていない。**同型が独立 3 例そろった時点で収容できる。**
- **受入 attempt 2 は `claim-self-unverified` (rc=70) で弾かれた。** attempt 1 の lease を
  自分が保持したままだったため。`tools/wave_land_window.py release` で解放して投げ直した。
  受入の子は 1 度も起動していない (非帰属赤ではない)。
- 記録前後の検査: `check_docs.py` rc=0、`spool_fold.py --dry-run --show-diff` rc=0、
  三軸語・placeholder 走査 (`s8b_holdout_freeze search`) rc=0 で自 wave の file は hit 0 件、
  全史 provenance 監査 10105 件で新規違反なし。
- 工数: codex 子 3 本 (plan 1 = medium 200.6 s / 7 call、consult 2 = medium 190.0 s / 8 call と
  372.7 s / 17 call)。実装子・fix 子・レビュー子は段 4 の「実装しない」裁定により起動していない。
- 一次資料は `output/insights/2026-09-15/t1338-floor-residual/README.md`。裁定パッケージ 3 件
  (撤去要求の取下げ可否、generic な `expected_perf_sha256` gate の扱い、D811 の「門が守っていた
  性質」の読み) を同 README へ置いた。

## 次の一手差分

### 更新

- [T-1338] **P1・撤去授権なし・ユーザー裁定待ち**: 依頼が名指しした 3 件 (per-pair 床値対表
  exact 検査、`floor_budget_snapshot_sha256`、oracle driver の `expected_perf_sha256` 供給) は
  D1985 で**撤去済み**。台帳が言う残件は別の 3 件で、R1 = driver の floor/budget null refusal
  (`orchestrator/campaign/s8b_oracle_driver.py:524-527`)、R2 = budget の凍結数値 loader
  (`orchestrator/campaign/s8b_budget.py:96-118` の `load_oracle_limits`、呼出しは driver:1433)、
  R3 = report の解決経路 (`orchestrator/campaign/s8b_oracle_report.py:2547-2560`)。
  **3 者とも現用経路で撤去授権が無い** (2026-09-15 実測)。R1 は D1985 が「残すもの」に名指し、
  R2 は freeze の budget を今回の資源上限へ射影するもので過去値比較ではなく、R3 は D1984 が
  現用挙動を記録し既存 consumer test が g1 選択規則不一致の拒否を要求する。**撤去要求そのものの
  取下げがユーザー裁定待ちで、取り下げれば本項は閉じられる。** 取り下げないなら R2・R3 について
  「何を・なぜ撤去するのか」の新規裁定が要る (R1 は D1985 の残置と正面から衝突する)。
  一次資料は `output/insights/2026-09-15/t1338-floor-residual/README.md`。
  base: 626e2fe7b5b8528d3b5f97d430840d2e3f53fb7d89eeacabf235c55c96ac2a06
