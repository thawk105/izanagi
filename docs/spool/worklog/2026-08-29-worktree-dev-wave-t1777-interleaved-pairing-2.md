---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: worktree-dev-wave-t1777-interleaved-pairing
seq: 2
title: [T-1777] A-1 交互配置の触れる境界を洗い出し、次の実走の配置を単一 campaign の 5-rep ブロック交互 + AB/BA 均衡に確定した (docs のみ、branch worktree-dev-wave-t1777-interleaved-pairing、実装面 0・変異 matrix 免除)
---

## 本文

- 依頼は「A-1 の対の作り方を交互配置へ改める。着手前に触れる境界を洗い出して記録すること」。
  境界の棚卸しと配置の確定までを行い、**実装面は 1 byte も変更していない。**
  測定投入、新 policy の発行、事前登録の発行は行っていない。凍結物の bytes も変えていない。
- **T-1777 が着手条件にしていた「批准の執行設計の着地」は D1139 で解消済みだった。** 撤去されたのは
  批准集合との照合による拒否だけで、記録 commit blob と disk bytes の自己整合検査は残る。
  未 commit の編集がある作業木では campaign を初期化できない (F357 の偽赤の正体)。
- **配置は {{D:a1-counterbalanced-block-pairing}} に確定した。** ユーザーが「裁定は codex と
  相談して決めて」と指示したため、段 4 の相談を 1 本追加し、親の推奨を独立評価させたうえで採った。
  反復数の決め方は {{D:a1-new-arrangement-needs-its-own-pilot-and-sizing}}、
  実装が及ぶ範囲は {{D:a1-arrangement-change-requires-all-four-closure-members}}。
- **親の当初案を 2 つとも撤回した。** (a)「固定 AB の rep 単位完全交互」は時間隔の交絡を
  対内順序の完全交絡へ置き換えるだけだった。(b)「1 workload を K 本の campaign へ割れば
  driver だけで済む」は誤りで、`trial_registry.py` が A-1 の campaign 群を workload と同数の
  exact unique triple に固定しており、registry と collector の変更も要する。加えて campaign 境界・
  静定・build/verify・ロック解放を 62 回持ち込む。
- **依頼が置いた前提「実装は campaign loop か pipeline を要求する」も不正確だった。** 必ず要るのは
  ident と wal であり、採用配置では loop と pipeline も要る。つまり閉包 4 member すべてに及ぶ。
- **実測。** 2026-08-24 探索走の raw TPS から親が独立に再計算したところ、この 15 対では
  3 workload とも対応差の標本 SD が独立近似より 25〜33% 大きく、arm 間相関は
  −0.591 / −0.563 / −0.765 だった。**この SD に自由度 4 の片側 95% 上側係数 2.372356 を掛けると
  凍結 policy の planned_sigma_tps と一致する**ので、再計算は v2 が実際に使った値を独立に再現している。
- **統計的な言い過ぎを段 4 相談で訂正した。** 各系列 n=5 で、無相関検定の両側 p は
  0.294 / 0.323 / 0.132、Fisher-z の概算 95% 区間はいずれも 0 を含む。したがって言えるのは
  「この 15 対では分散削減を観測せず、有益な正の共分散の証拠も無い」までで、
  母集団で分散を増やすとも、原因が時間隔だとも言えない。当初書いた「真の相関 0 なら 3 符号一致は
  8 分の 1」も、workload 間の独立性が示されていないので取り下げた。
- 敵対検査で親 brief の 3 か所を訂正した。(a)「批准の関門が無くなった」の一般化過大、
  (b)「1 arm 区間 615 秒」は nominal 値であり実測換算は約 689 秒でさらに build と verify が挟まる、
  (c)「bytes を pin する台帳 0 件」は固定 digest 定数が無いという意味で、投入ごとの source binding
  では両 path の bytes が記録・再照合される。
- 敵対検査は親の「費用 205 倍」も訂正した。verify 成功時の nominal extime は 1 秒である。
- 段 2 計画と段 3 レンズ 2 本がともに「新しい事前登録はユーザー発行を待つ必要がある」と結論したが、
  **これは言い過ぎである。** ユーザーの手番と定められているのは、生きた事前登録の後継発行である。
  別 study の新規事前登録は過去に dev-wave が作って凍結した実績があり、現に v2 事前登録がそれである。
- 段 9 の land は 1 度目に stale-main (rc=10) で競合に負けた。main は 1 bit も動かず lease も
  解放された。local main を取り込み直し、受入を取り直してから再試行した。
- 段 8 の自己改善候補は 1 件出たが**採らなかった**。候補は DW-C01 への 1 節追記。実測すると
  当該節は checker 側に exact 契約として literal 固定されており、追記後は単節予算を
  1034 bytes > 1000 bytes で超える。実装面 (checker) の編集と予算引き上げの裁定を同時に要するため、
  手順の明確化にその費用は見合わないと判断し、記録に留めて編集を戻した。
  再訪条件 = 同節を触る別 wave への相乗り。
- 一次資料は `output/insights/2026-08-29_t1777-interleaved-pairing/`。段 1 brief、段 2 計画、
  段 3 レンズ 2 本、段 4 裁定相談の全文と、再計算の生出力を置いた。

## 次の一手差分

### 更新

- [T-1777] **P2・実装待ち**: A-1 の対の配置。境界の棚卸しと配置の確定は完了した
  (insight `2026-08-29_t1777-interleaved-pairing`、確定内容は上記 3 決定)。
  残るのは実装であり、次の順で進める。(1) 閉包 4 member と driver に、単一 campaign の
  5-rep ブロック交互 + AB/BA 均衡の coordinator・ブロック実行器・profile・collector・
  投入 selector を同じ変更単位で作る。(2) その機構で pilot を 60 対/workload 測る。
  (3) pilot から対 SD とブロック実効 sigma を出し、独立 seed の simulation で反復数を認証する。
  (4) 別 study の policy と事前登録を凍結する。(5) 本走を投入する。
  凍結済みの現行 study は据え置き、bytes を変えない。
  base: 087866711a69fe3d0e101ca8f8dcfac6c84460247949f01f7adfe62309ca6401
