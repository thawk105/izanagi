---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-b10-backoff-shape-orthogonal
seq: 1
title: B-10 の待ち方 / 待ち量の直交切り分けを設計し事前登録まで通した (コード + docs、branch worktree-dev-wave-b10-backoff-shape-orthogonal、変異 matrix = baseline PASSED・17/17 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「backoff の機序説明のうち待ち方と待ち量の直交切り分けを実験として設計し、実走する」。
  実走の前に因子・セル・反復数を固定し、事前登録の形で commit することも指定された。
- **起動時の重複照合で「実走へ進む」と判定した。** 既存の backoff sweep 成果 5 件は
  すべて 2026-08-02 の旧物で、稼働中 worktree 14 本の編集面にも `backoff_sweep.py` /
  EVOLVE-BLOCK 合成枝の重複は無かった。
- **実装面の編集は EVOLVE-BLOCK 合成枝の 1 行に収まった。** 設計は {{D:b10-half-width-shape-family}}。
- **実走は本 wave では完了していない。** 原因は設計や実装の不足ではなく
  {{F:new-pegasus-executable-unusable-before-land}} である。新しい投入スクリプトは
  main へ着地するまで機械防壁が起動を拒否する。着地後の実測は次の一手へ登録した。
- **段 3 の 2 レンズは親の実験設計を作り直させた。** 最大の指摘は
  「各セルが 1 セッションしかないので、閾値を noise floor に置くと帰無が真でも
  1 セルあたり約 48% で陽性が出る」。判定を独立 3 ブロックの対比較 + 符号反転 exact 検定 +
  Holm 補正へ差し替えた。副産物として外部 floor への依存が消え、
  **Pegasus に rr5 / rr50 の between-run floor が無いという阻害要因が消滅した。**
- **段 6 のレビュー 2 本は「そのままでは 1 セルも動かない」ことを突き止めた。** 投入スクリプトが
  自分の receipt を作業ツリーへ書き、job 側と driver 側の clean 検査がそれを拒否する自家撞着で、
  静的レビューでしか見つからない型だった。実走してから気づけば計算ノードの枠を丸ごと捨てていた。
- **事前登録の実効範囲が主張より狭いことも段 6 で判明した。** 機械的に読んでいたのは 6 値だけで、
  判定規則の大半がコード定数だった。{{D:b10-preregistration-machine-spec}} で全件 parse へ変えた。
- **実行時間の制約は正しさ検証の反復では解かなかった** ({{D:b10-phase-split-keeps-verification-reps}})。
  全規模検証が反復 5 回ぶん回るため単一の割当てに収まらないが、反復を減らすのは
  実行時間のために規律 2 を緩めることなので、相と workload の分割で解いた。
- **実 C++ をコンパイルして Python の厳密モデルと突き合わせる検査が、括弧の閉じ忘れを実走前に捕まえた。**
  この検査は段 3 レンズ B の指摘で入れたものである。無ければ計算ノードで数時間走らせてから
  全セルがビルド失敗で気づくところだった。
- **変異が oracle の恒真を掘り当てた** ({{F:pair-sum-oracle-is-vacuous-for-mixer-mutation}})。
  撹拌器の同一性を数値で検査したつもりが、対の作り方の性質上どんな奇数撹拌器でも成立する
  恒真な検査だった。実効 gate は式の構造検査の側だったので再照準した。
- **fix は 5 巡かかった。** 1 巡目は C++ の括弧と在庫 4 件、2 巡目はレビュー must-fix 8 件、
  3 巡目は変異の再照準と性能 file 在庫、4 巡目は待機実測の probe 相の新設、
  5 巡目は probe が足した起動点の在庫登録。**どの巡でも既存テストの期待値は 1 つも変えていない。**
- **子が 2 度、未 commit 差分で空振りした。** 段 6 のレビュー 2 本が同時に rc=2 で成果物ゼロに
  なった。原因は fix 子が残した設定ファイルの未 commit 差分で、子は作業ツリーが HEAD と
  一致していることを起動条件にする。**子を投げる前に統合 commit する**のが正しい手順だった。
- **本 wave が確かめていないこと:** 性能の値は 1 つも取っていない。事前登録は placeholder 版で
  発効していない。待機の物理残差も未実測である。

## 次の一手差分

### 新規

- {{T:b10-backoff-shape-run}} **P1・新規**: B-10 待ち方 grid の実走。着地後の main で
  `--phase probe` を計算ノードへ投入して待機の物理残差を実測し、事前登録の実測欄を埋めた版を
  commit して発効させ、`build` → `verify` (workload 別) → `perf` (workload 別) を走らせて
  レポートを出す。事前登録は `docs/b10-backoff-shape-preregistration.md`。
- {{T:b10-realized-wait-distribution-diagnostic}} **P2・新規**: 実走での要求待ち量そのものの
  分布 (分位点・自己相関・スレッド間同時値率) を測る診断ビルドの新設。段 4 で scope 外と裁定した
  裁定パッケージ項目。
- {{T:b10-legacy-backoff-consumer-identity}} **P2・新規**: 旧 backoff consumer の campaign
  identity 移行、または v1 patch の別名凍結。現在の凍結成果物は 1 件も壊れていないが、
  旧 consumer を v2 patch で再走すると新しい variant 識別子が同じ campaign に入り、
  8 件の WAL SHA pin を壊しうる。
- {{T:pegasus-between-run-floor-rr5-rr50}} **P3・新規**: Pegasus の write-heavy / balanced の
  between-run floor 取得。B-10 の必要条件からは外れたが、他 campaign の採否参照線として有用。
  既存 driver あり、2 workload で 20〜30 分の見込み。
