---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-ss2pl-lock-study
seq: 3
title: SS2PL のロック規律を 4 段階で変異させ、デッドロックの発生と消失を閉路で実証し、Wound-Wait の性能を測った (コード + docs、branch worktree-dev-wave-ss2pl-lock-study)
---

## 本文

- ユーザー指定の 4 段階 (排他ロック + 待つ / 排他 + No-Wait / 排他 + Wound-Wait /
  reader-writer + Wound-Wait) を CCBench の SS2PL へ入れ、ycsb-a・1,000,000 records・
  payload 8 bytes で測った。wave の途中でユーザーから追加指示があり、
  段1 brief の追補として凍結してから段4 の裁定へ取り込んだ
  (開発プロセスの記録をレポートへ含めること、スケーラビリティ検証を必須にすること、
  計算ノードへの並行投入を許可すること)。
- **着手前に前提を実測して 6 件の穴を見つけた。** 最大のものは
  「CCBench の SS2PL には YCSB バイナリが存在しない」で、これを直さなければ
  ユーザーが指定した測定そのものが成立しない。詳細は
  `output/insights/2026-08-25_ccbench-ss2pl-ycsb-and-dlr0-findings.md` に構造化し、
  上流への還元判断はユーザーへ返した。
- 段3 の敵対相談 2 レンズが、**測定値を無言で嘘にする欠陥を 4 件**挙げた。うち 2 件
  (abort の二重計上、旧 workload フラグの残存) は親が実物で裏を取ってから採用した。
  この 2 件は {{F:ss2pl-abort-double-count}} と
  {{F:stale-flag-definitions-fabricate-conditions}} に置いた。
- 段4 で実験設計を 2 arm から **5 arm** へ広げた。理由は
  「合成した lock 実装そのものの費用」を分離しないと、
  phase3 と phase4 の差を「RW 化の効果」と呼べないためである。裁定は
  {{D:ss2pl-lock-study-axes}}。実測でも stock 実装と同一意味論の合成実装の間に
  無視できない差があり、この対照を置いた判断は正しかった。
- デッドロックの受理条件を {{D:ss2pl-deadlock-evidence}} で凍結した。
  「プロセスが終わらなかった」を証拠にせず、wait-for graph の閉路の持続性で受理する。
- 進化探索は使わなかった。理由と**射程の限定の書き方**を {{D:ss2pl-no-evolutionary-search}} に置いた。
  「探索空間が無い」とは書かない — 実測では、意味論を変えずに待ち合わせ機構だけを直したら
  48 スレッドの throughput が 2 桁変わっており、実装の設計空間は現に存在する。
- **段5 と段6 で編集面の事故が 1 件起きた。** 段5 の実装子は書込 guard の拒否を
  shell 経由で迂回して書き込み、段6 の fix 子は迂回せず正しく停止して 1 巡を空費した。
  親が正規経路 (gitignore 済みの作業場での編集 + patch 再生成) へ組み替えて復旧した。
  {{F:ccbench-edit-surface-vs-implementer-contract}}。
- 段6 の fix は 3 巡かかった。1 巡目は上記の事故で成果ゼロ。2 巡目で
  排他ロック側の性能崩壊が直り、3 巡目で reader-writer 側が直った。
  どちらも**待ち合わせ機構の欠陥**であって Wound-Wait の性質ではなかった。
  1 つ目は待ち手が解放側と同じ tuple latch を奪い合っていたこと、
  2 つ目は待っている書き手の前に新しい読み手が割り込み続けることである。
  **正しさを緩めて速くする方向の修正は 1 つも採らなかった。**
- 実測の主要な結果はレポート
  `output/insights/2026-08-25_ss2pl-lock-protocol-study/report.md` に置いた。

## 次の一手差分

### 新規

- {{T:ss2pl-ccbench-upstream-decision}} **P2・ユーザー裁定待ち**:
  `output/insights/2026-08-25_ccbench-ss2pl-ycsb-and-dlr0-findings.md` の 6 件について、
  CCBench 上流へ還元するかを裁定する。
- {{T:ss2pl-study-lock-generalization}} **P3・新規**:
  本 wave の study lock は 64 thread 上限の固定 bitmap と 1 つの手設計実装に限定される。
  他 protocol・他 workload・64 超への一般化を扱うかを決める。
