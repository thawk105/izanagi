---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1946-t2107-registry-proof-wiring
seq: 1
title: [T-1946][T-2107] 配線と束縛を実装しようとして、対象が 3 件の閉包であることと、裁定済みの proof の形だけでは束縛が恒真になることを実測した (docs のみ、branch worktree-dev-wave-t1946-t2107-registry-proof-wiring、実装面の差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

- **実装指示で始めたが、段 4 の 2 巡目で本 wave では実装しないと裁定した (4→7→8→9)。**
  段 2 plan を 2 巡、段 3 敵対検査を 2 巡 (計 4 本) 回し、所見 39 件を裁定した。
  一次資料は `output/insights/2026-09-01_t1946-t2107-registry-wiring-design/`。
- **対象は 2 件ではなく 3 件の閉包だった。** T-2107 の配線は T-1851 の前半と同一の作業で、
  T-1851 段 4 が次 wave へ渡した骨格が逐語で「launcher / campaign 配線、final inspector /
  verifier までを同時に land する」と書いている。T-1851 は D1193 / D1194 で裁定済み・実装待ち。
  D1341 と同段 4 の「書き手と検査を別々に land する分割は不可」が 3 件を 1 commit へ束ねる。
- **裁定済みの proof の形だけでは束縛が恒真になる (裁定パッケージ 1)。** D1337 の
  `{row_count=N, chain_head_at_N}` は genesis 1 行だけの台帳でも別 campaign の台帳でも通る。
  4 本の独立検査が実測した。親は「被覆の追加は D1337 の変更ではなく D1194 の実装」と読んで
  採用したが、ユーザーが覆せる裁定として返す。被覆は集合等値では足りず、schedule と
  admission claim から独立導出した authoritative 集合と全単射で照合する必要がある。
- **分類権限の新設 (裁定パッケージ 2)。** 配線に必要な入力 6 件のうち、launcher の出力前分類方針を
  名指しする production 定数は新しい信頼の根にあたる。既存の scheduler accounting authority と
  同じ形で方針 bytes から digest を導出する案を採用したが、ユーザーが覆せる裁定として返す。
- **refuted:** 「理由の機械導出が値を見てから選べる」という強い読み。現行 `excluded_reason` は
  凍結閾値の単一純関数と固定優先順位で決まり自由選択が無い。D1032 の「性能量に到達する前に
  理由を固定する」は規則の凍結という意味では現行コードでも満たされている。両レンズの指摘は
  信頼境界 (導出を campaign が実行している) であり、修正は同じ純関数を launcher から呼ぶだけ。
- **refuted:** 共有 admission root の残骸が本番と現行 test へ衝突するという懸念。残骸は本番と
  別の凍結の下にあり、test は一時 Git repository を作る。
- **親 brief の実測 3 件が誤っていた。** 既存台帳 0 件 (実際は共有 admission root に 2026-08-27 の
  実装試行が残した 193 行の台帳と 96 行の catalog が実在)、編集面 8 file (実際は 23-24 path)、
  稼働 wave との重なり 0 件 (実際は 3 件)。1 巡目の brief と plan と検査 2 本を invalidate し、
  brief を差し替えて段 2 から再実行した。
- **セッション異常:** `tools/check_ai_provenance.py` が Pegasus へ投入する検査であることを知らず、
  既定 2 分の timeout つきで前面実行してラッパーだけが死に、投入が孤児化した。
  以後この worktree からの全投入が rc=16 で止まった。scheduler で対象 job の不在と作業ツリーの
  clean を確認し、`orphan-hold.json` と `orphan-holds/<request>.json` の**両方**を削除して復旧した
  (gate は後者に entry があるだけで成立する)。証拠は job dir へ退避。以後 rc=0。
- **工数:** codex 子 5 本 (plan 2、consult 4 のうち 4 本、いずれも `gpt-5.6-sol` / xhigh / read-only)。
  実装子・fix 子は起動していない。
- **人間手番:** 裁定パッケージ 2 件 (上記)。および稼働 3 wave の着地順。

## 次の一手差分

### 更新

- [T-1946] **P1・裁定済み (D1337/D1340/D1341/D1342) → 実装待ち。実装は T-1851 前半・T-2107 と
  同一の land 単位で行う**。2026-09-01 の設計 wave で、裁定済みの proof の形
  `{row_count=N, chain_head_at_N}` だけでは genesis 1 行の台帳でも別 campaign の台帳でも
  検証が通ることを 4 本の独立検査が実測した。被覆の追加をユーザー裁定へ返している
  (`output/insights/2026-09-01_t1946-t2107-registry-wiring-design/s4-adjudication-r2.md`)。
  base: 7134d31fc7959831e67abae3d42e6c41568dc352cd33b29a3eb6f5e74a4a34d0
- [T-2107] **P1・裁定済み (D1340) → 実装待ち。T-1851 前半と同一の作業であり同時 land する**。
  配線に必要な入力 6 件の解は段 4 裁定で確定した。うち分類権限の新設だけがユーザー裁定待ち。
  base: 074fc324510415bad680ded7f5e04467f97f716dbac51cf81858f8cbf6bb68b4
- [T-1851] **P1・裁定済み (D1193/D1194) → 実装待ち。T-2107・T-1946 と同一の land 単位**。
  段 4 が渡した骨格の前半が T-2107 の配線そのものであることを 2026-09-01 に確認した。
  実装単位は `B1 → A → B2 → D1 → C → D2` の 6 段、規模は更新テスト 220 node 超・2,650-4,000 行超。
  着手前に稼働 3 wave (t2027、t2074 の 2 系統) の着地を待つ。
  base: 4f1d3940bda898b7beb68f5a057f06623a1694d3bc12c4f93a63c719bb97858b

### 新規

- {{T:floor-registry-shared-root-residue}} **P3・新規**: 共有 admission root に 2026-08-27 の
  実装試行が残した schema v1 かつ 2 段 path の試行台帳 (193 行) と consumption catalog (96 行) が
  ある。本番と別の凍結の下にあり本番 campaign にも通常 test にも影響しないため触っていないが、
  T-1851 の実装で世代列挙を入れるときに同 shape の合成 fixture を横断予算 test へ入れる。
