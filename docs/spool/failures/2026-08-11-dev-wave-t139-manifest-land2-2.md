---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t139-manifest-land2
seq: 2
---

## 新規

### {{F:mutation-preregistration-before-implementation}}. 実装前の段 4 で登録した変異が実効 gate に当たらない [恒真ゲート]

- 事象: 段 4 で事前登録した 10 変異のうち **7 件**が、段 6 のレビューで
  mask (前後層が同じ入力を先に拒否) / equivalent (受理集合が動かない) /
  テスト自身を弱めるだけで production の状態が変わらない / 受理集合でなく内部表現の assert が
  赤くなるだけ、と判定された。単独 KILL を書けたのは 3 件だけだった。
- 根本原因: `DW-M01` は「各変異は位置に加え、同じ入力を拒否する層が前後に無いこと、無効化時の
  赤理由が一つに絞れることを**コードで確認する**」と定めるが、**実装は段 5 で生まれる**ため
  段 4 の時点では確認対象のコードが存在しない。親は段 2 プランの設計から変異位置を書いた。
- 恒久対応: 実装が段 5 で生まれる wave では、**段 4 の変異登録を暫定とし、段 6 の fix 子へ
  「その検査を消したとき赤くなる nodeid を名指しせよ」と要求して再導出する**。
  本 wave の段 6 fix prompt 3 本がこの形を持ち、`verbatim/s6-fix2d.md` /
  `s6-fix2e.md` / `s6-fix2f.md` の「変異 gate」節が実体である。
  再導出後の spec で 9/9 KILLED・期待 node 完全一致を実測した。
- 再発検知: 変異 harness の MISMATCH。期待 node が実効 gate に当たっていなければ
  過少・過剰申告として `matches_expectation=false` になる。

### {{F:split-leaves-isomorphic-defect}}. 所有分割の副作用で同型欠陥が別ファイルに残る [手順漏れ]

- 事象: `BlobRef` の digest 比較が `str` subclass で迂回できる欠陥を lane B が塞いだが、
  **同型の欠陥が `ComposedCore.require_sha256()` に残った**。合成後 digest の比較が文字列比較のままで、
  `__ne__` が常に `False` を返す 64 桁 hex の subclass を渡すと不一致でも正常終了する
  (段 6 レビュー C が実行で確認)。
- 根本原因: 段 5 の所有分割で `blobref.py` は lane B、`erratum.py` は lane A が持ち、
  **lane B は同型欠陥を見つけても隣のファイルを編集できず、lane A は自分の担当所見でなかった**。
  親の段 4 裁定も欠陥を 1 ファイルの問題として記述していた。
- 恒久対応: **欠陥の型 (「検査済み値を subclass で置き換えて比較を恒偽化する」) で repo を
  全数検索してから lane を切る**。本 wave では段 6 の敵対レビュー 2 本を差分全体へ当てることで
  検出した (`DW-S06-A` の「異なるレンズの敵対レビューを必ず 2 本並列」)。
  レビュー対象を lane 単位でなく**統合 commit 全体**にすることがこの検出の条件である。
- 再発検知: 段 6 レビュー prompt に「同型の迂回が他ファイルに残っていないか」を明示的に含める。
  本 wave の `verbatim/s6-revC2.md` の担当項 1 がその形である。
