---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: worktree-dev-wave-t1777-interleaved-pairing
seq: 2
title: [T-1777] A-1 交互配置の触れる境界を洗い出し、固定 AB 完全交互を却下して配置の択一をユーザー裁定へ返した (docs のみ、branch worktree-dev-wave-t1777-interleaved-pairing、実装面 0・変異 matrix 免除)
---

## 本文

- 依頼は「A-1 の対の作り方を交互配置へ改める。着手前に触れる境界を洗い出して記録すること」。
  境界の棚卸しと配置の設計判定までを行い、**実装面は 1 byte も変更していない。**
  測定投入、v3 policy の発行、事前登録の発行は行っていない。凍結物の bytes も変えていない。
- **T-1777 が着手条件にしていた「批准の執行設計の着地」は D1139 で解消済みだった。** 撤去されたのは
  批准集合との照合による拒否だけで、記録 commit blob と disk bytes の自己整合検査は残る。
  未 commit の編集がある作業木では campaign を初期化できない (F357 の偽赤の正体)。
- **依頼が置いた前提「実装は campaign loop か pipeline を要求する」は不正確だった。** どの配置案でも
  必ず要求されるのは ident と wal の 2 か所である。詳細と根拠は
  {{D:a1-arrangement-change-requires-two-closure-literals}}。
- **固定 AB の完全交互は却下した。** 時間隔の交絡を対内順序の完全交絡へ置き換えるだけだからである。
  配置の択一はユーザー裁定へ返す。根拠は {{D:a1-fixed-ab-interleave-rejected}}。
- **実測。** 2026-08-24 探索走の raw TPS から親が独立に再計算したところ、3 workload すべてで
  対応差の標本 SD が独立近似より 25〜33% 大きく、位置を揃えた arm 間の相関は負だった
  (write-heavy −0.591 / balanced −0.563 / read-heavy −0.765)。現行の位置対応は分散を減らしていない。
  各系列 n=5 であり相関推定は粗い。相関が真に 0 でも 3 workload とも負になる確率は 8 分の 1 ある。
- 敵対検査で親 brief の 3 か所を訂正した。(a)「批准の関門が無くなった」の一般化過大、
  (b)「1 arm 区間 615 秒」は nominal 値であり実測換算は約 689 秒でさらに build と verify が挟まる、
  (c)「bytes を pin する台帳 0 件」は固定 digest 定数が無いという意味で、投入ごとの source binding
  では両 path の bytes が記録・再照合される。
- 敵対検査は親の「費用 205 倍」も訂正した。verify 成功時の nominal extime は 1 秒であり、
  balanced の単純合計は約 30% 増である。build も cache hit が大半を占める。
- 段 2 計画と段 3 レンズ 2 本がともに「新しい事前登録はユーザー発行を待つ必要がある」と結論したが、
  **これは言い過ぎである。** ユーザーの手番と定められているのは、生きた事前登録の後継発行である。
  別 study の新規事前登録は過去に dev-wave が作って凍結した実績があり、現に v2 事前登録がそれである。
  本 wave が実装しない理由は事前登録の発行主体ではなく、配置が未確定であることによる。
- 一次資料は `output/insights/2026-08-29_t1777-interleaved-pairing/`。段 1 brief、段 2 計画、
  段 3 レンズ 2 本の全文と、再計算の生出力を置いた。

## 次の一手差分

### 更新

- [T-1777] **P2・ユーザー裁定待ち**: A-1 の対の配置。境界の棚卸しと設計判定は完了した
  (insight `2026-08-29_t1777-interleaved-pairing`)。固定 AB の完全交互は却下済み。
  裁定してほしいのは次の 3 点。(1) 配置をどれにするか — 5-rep ブロック交互 + 対内順序の
  AB/BA 均衡 (間隔が現行の約 41 分の 1、実装は driver + closure 2 か所)、rep 単位 ABBA
  (間隔が最小だが loop と pipeline も要る)、均衡無作為のいずれか。(2) 先に小規模 pilot で
  対の相関が実際に改善するかを確かめてから本実装へ進むか、配置を凍結して一気に作るか。
  (3) 新しい反復数は新配置の pilot から取り直す必要がある — 旧 planned sigma は流用できない。
  base: 087866711a69fe3d0e101ca8f8dcfac6c84460247949f01f7adfe62309ca6401
