---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: t1310-formal-workload-profile
seq: 1
title: 正式 workload profile は producer 配線の前に 3 つの前提が要ると実測で判明し、実装せず裁定へ返した — 親は自分の裁定と不変条件の書き方を 3 件撤回した (docs のみ、branch worktree-t1310-formal-workload-profile)
---

## 本文

**結論。** [T-1310] (正式 holdout `rr80` / `rr20` を producer の production profile として実装し、
正式 scale を campaign / perf / descriptor の 3 sink へ束縛する) は、台帳項どおりの形では
本 wave で実装しなかった。実装差分 0 件、docs のみ。段 4 で「実装しない」と裁定し `4→7→8→9` で閉じた。

**既裁定との整合。** [T-822] は 2026-08-17 の `/rulings` 全件 第 6 回で
「(i) と (ii) は前提タスクの後ろへ送る。空振りする検査を置いて保証があるように見せる方が、
保証が無いことを明示するより悪い (規律 3)」と裁定済みである。本 wave の裁定はこの既裁定の適用であり、
新たな方針変更ではない。**発火しない配線を置いて C01 の静的条件だけ通す形を採らなかった。**

**実装できない理由 (3 件、いずれも親が一次資料で再確認)。**

1. **Layer-3 の突き合わせ検査が「producer は単一 scale」を機械的に固定している。**
   `orchestrator/campaign/autonomous_trial_completeness.py` の campaign-chain 検査は、各 cell の
   workload が探索表 `producer.WORKLOADS` に在ることを要求し、さらに descriptor を
   **profile を渡さない `_descriptor_for(flags)` で再導出して完全一致**を要求する。
   よって正式 run の cell は必ず落ちる。探索表へ正式名を足しても profile-less 再導出は探索 scale を
   返すため一致しない。通せる形は (形 1) scale を workload 表の entry に持たせ producer と検査が
   同じ entry から導出する (探索側の成果物 schema と campaign identity も変わる)、
   (形 2) 検査を profile-aware にする (= [T-822] (i) が必須化しようとしている検査層そのものの改訂で、
   前提の順序が逆になる) の 2 つだけで、**どちらも台帳項の scope を超える。**
2. **正式受理の材料が未充填。** v1 凍結の `floor` と `budget` はいずれも null で、同 artifact の
   注記自身が「対象別 floor 再実測後に再凍結 + 承認で充填する」と要求している。
   `layer3_report.py` の floor 照合は records / threads / workload の完全一致を要求する。
   配線だけを「正式 profile 実装済み」と記録すると、床値なき成果物を正式扱いすることになる。
3. **DW-G04 (条件付き機能の発火 gate) に触れる。** 正式 profile の発火条件は
   「承認済み active v2 世代 + 登録済み manifest + 床値/予算」であり、親は発火条件を満たす
   既存 artifact path も計測 ID も書けない。ratified loader は `no-active` (v2 未発効) で止まり、
   manifest なしの起動は holdout workload を登録簿が拒否する。

**親が撤回した 3 件 (敵対レンズの refute を受理)。**

- **(a) 「値も identity も ratified 経路のみ」を最善とした暫定裁定。** これは発火不能な配線であり、
  規律 2/3 が禁じる恒真な保証そのものだった。レンズ A の指摘で撤回した。
- **(b) 「凍結 bytes の pin テストが事故を止める」という不変条件の書き方。** 凍結 artifact 内の
  generator SHA は現 generator source の SHA と既に相違し、当該検査は
  `freeze_verification_hold` で保留中である。よって pin が現在発火する防壁だとは主張できない。
- **(c) C01 判定 snapshot の更新対象を 2 箇所とした brief の記述。** 実際は 1 箇所だけで、
  もう 1 箇所は「perf sink を探索 scale へ戻す変異を殺す負の control」である。更新すると検出力を壊す。
  段 2 プランの指摘で訂正した。

**親の実測が支えていない一般化 (レンズ A 所見 8 / レンズ B 所見 11 を受理)。**
現 snapshot の緑・現 HEAD の active pointer 不在・v1 に値が実在すること・登録経路が実在すること・
descriptor が正の整数を受理すること — これら 5 件はいずれも
**正式 scale の runtime 射影・v2 承認・正式受理集合の非空**を支えない。記録でもこの限定を保つ。

**本 wave の文書自身が repo scan invariant を破った (実測して直した)。**
親が段 1 brief の追記で正式 holdout の値を inline JSON の正規形のまま引用したところ、
`s8b_holdout_freeze.holdout_conjunction_hits` による実測でその文書が rr80 の三軸 conjunction hit に
なった (0 hit → 1 hit)。insights へ複写する前に検出し、原文 sha256 を残した可逆 defang
(`"key": "value"` 表記を並記へ開くだけ) で 0 hit へ戻した。**この wave の主題である不変条件を、
この wave の説明文が破りかけた。**同時に、同じ実測で「producer に read 比率を正規形で 1 行足すと
即 1 hit になる」ことも反実仮想として確認した。

**repo scan invariant の全 repo 検査は AI が実行できない。** 当該テストは成長比例コストゆえに
恒久保留で、pytest 経由では skip、plain runner では
`GrowthTestHoldBypassRefused` (`release_token: explicit-user-command`) が出る。
よって本 wave は「変更した file 本文に対する `holdout_conjunction_hits`」で性質を証明した。
**held テストが緑になったとは記録しない。**

**エージェント工数。** codex 子 3 本 (plan `reasoning=max` 1 本、consult `reasoning=max` 2 本、
いずれも `sandbox=read-only`)、`check_codex_output.py` は 3 本とも rc=0。
プラン子は約 15 分、レンズ 2 本は並列で約 14 分。実装子・fix 子・変異 matrix は
「実装しない」裁定により起動していない。

**ユーザーへ返す択 (3 件)。** 詳細は下記 [T-1310] の更新本文に置く。
親の推奨は (α) 前提の充填を先に置く順序組み替えである。(β) は自作の証拠水準を明示的に下げる案で、
`rr80` / `rr20` の 1,000,000 records / 48 threads の**物理測定は今日でも可能**であり、
塞いでいるのは v2 承認と床値という自作の手続きであることを明示する。

**段 8 (自己改善) の裁定 = 編集なし。** 候補は 3 件記録した — (1) 段 1 brief の実アンカー表が
「値を exact 照合する consumer 層」を含んでいなかった、(2) wave の説明文が主題の不変条件を破りかけた、
(3) 全 repo の holdout scan は AI が実行できない。いずれも編集しない。(1) は段 3 の敵対レンズが
実際に検出しており (`DW-S03` の既存義務が機能した)、consumer 列挙は `DW-O13` と `DW-S05-C` が既に負う。
(2) は `DW-S07` の D88 走査義務が既に定めており、実際にその手順で検出・defang した。
(3) は行き先が dev-wave docs ではなく本エントリである。dev-wave docs は 3 層とも予算満杯で、
D271 の新規 L2 節の第 3 条件 (同じ意味検索で既存正本なし) も満たさない。

**受入。** 本 wave の差分は `docs/spool/` の fragment 1 本と `output/insights/` 配下のみで、
実装面の変更は 0 件である。

## 次の一手差分

### 更新

- [T-1310] **P2・実装せず裁定へ返した (2026-08-17) → ユーザー裁定待ち**: 正式 holdout
  `rr80` / `rr20` の producer 配線は、**単独では成立しないと実測で判明した。**塞いでいるのは
  (1) Layer-3 の campaign-chain 検査が workload を探索表に限定し descriptor を profile-less に
  再導出して完全一致を要求すること、(2) v1 凍結の `floor` / `budget` が null で注記自身が
  再実測・再凍結・承認を要求していること、(3) ratified v2 世代が未発効で登録済み manifest も
  無いこと、の 3 点である。**択 = (α) 順序を組み替え、床値/予算の対象別再実測 → v2 世代の発行と承認
  → Layer-3 検査の profile 対応 (= [T-822] (i) の層) を先に置き、producer 配線を最後にする。
  (β) 自作の証拠水準を明示的に下げ、`load_legacy_freeze` の `legacy-v1` 源を暫定源として
  non-certifying と明記のうえ受理し、正式 scale の実測を今日から可能にする。
  (γ) 現状維持で本項も凍結する。**親の推奨は (α)。(β) を採る場合も (1) の形の裁定が同時に必要で、
  `load_verified_freeze` を expected_hash なしで使う形は任意の working-tree bytes を受けるため採らない。
  実装時の要件として次を保存する — 正式値は literal で書かず実行時読取にする (repo scan invariant を
  1 行で壊すため)、3 sink 各々に正式 scale の照合を置く (C01 は関数内の整数 literal の存在しか見ず、
  実射影の証拠にならない)、探索既定は不変で profile は明示 selector とする。正本 =
  `output/insights/2026-08-17_t1310-formal-workload-profile/README.md`
  base: 5be97f50baeecc18d532316039f953442c623bd9b18af7b0605584581b5aed4a

### 新規

- {{T:layer3-single-scale-ruling}} **P2・新規・ユーザー裁定要 ([T-1310] から分岐)**: Layer-3 の
  campaign-chain 検査が「producer は単一 scale」を機械的に固定している問題をどう解くか。
  択 = (形 1) scale を workload 表の entry に持たせ producer と検査が同じ entry から descriptor を
  導出する — 探索側の cell に載る値の形と campaign identity が変わる。
  (形 2) 検査を profile-aware にする — [T-822] (i) が必須化しようとしている層そのものの改訂となり、
  「前提を先に」の順序と逆になる。**この裁定が付くまで正式 profile の producer 配線は着手できない。**
- {{T:exploratory-scale-nonregression-lock}} **P2・新規**: 探索経路
  (`ycsb-a/b/c` @ 100,000 records / 4 threads) の byte 単位非回帰を固定する。現状、3 sink 全ての
  records / threads、campaign identity の preimage、`PerfConfig`、descriptor の projection record を
  同時に pin するテストが無く、探索側の値が変わっても既存テストが緑のまま通りうる
  (段 3 レンズ B の所見)。規律 4 の防壁として、正式 profile の実装より前に置ける独立項である。
