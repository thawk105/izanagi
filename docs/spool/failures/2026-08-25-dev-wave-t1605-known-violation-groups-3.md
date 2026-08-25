---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1605-known-violation-groups
seq: 3
---

## 新規

### {{F:partition-derived-positive-control}}. partition から作った positive control が、その partition の定義から導かれる恒真だった [恒真ゲート] [テスト代表性]

- 事象: known-violation 台帳を 2 群へ分ける wave で、親が段 4 の裁定に
  「上限と対で置く positive control」として次の 3 つを指定した — 2 群の和が台帳全体と一致する、
  2 群が互いに素である、群ごとの件数の和が台帳の件数と一致する。
  裁定文には「台帳を空にすればこの 3 つが赤になる」と書いた。**これは誤りだった。**
  実装は歴史群を `台帳 ∩ baseline`、新規群を `台帳 − baseline` と定義しており、
  この 3 つは集合演算の定義から導かれるので、**valid な入力では 1 つも falsify できない。**
  台帳を空にしても 3 つとも緑である。実際に空台帳を捕まえるのは
  「baseline ⊆ 台帳」の 1 本だけだった。
- 根本原因: positive control を**分割そのものから作った**こと。
  分割 `H = L ∩ B` / `G = L − B` の内部整合性は定義の言い換えであって、
  外部の事実を何も検査しない。上限が守るべき対象 (凍結された B の内容) は分割の**外**にあるのに、
  検査は分割の**中**だけを見ていた。同じ理由で「凍結 baseline の 53 キー」にも
  独立した oracle が無く、baseline 定数を台帳から実行時導出する退行が全検査を通過した。
- 恒久対応: 上限の対象を分割の外へ出し、production から独立した 53 複合キーの literal oracle を
  テスト側へ置いて完全一致を要求する形にした ({{D:known-violation-frozen-baseline}})。
  恒真だった 3 assertion は削除し、独立 oracle と正規化台帳から期待値を作る検査へ置き換えた。
- 再発検知: 変異 `t1605.m01` (凍結 baseline から 1 要素を削除) と `t1605.m02` (baseline を空にする) を
  事前登録した。どちらも独立 oracle が唯一の拒否理由になる。
  設計時の一般則は「positive control は、それが守る対象と同じ定義から導けてはならない」。

## 再発

### F333

- **再発: 2026-08-25 (同日 2 例目、引き金が別の族)** — 親が `tools/run_tests.py` の**焦点走**を
  Bash の既定 2 分タイムアウトのまま前景で投げ、打ち切りで dispatch job `945538.nqsv` を
  孤児化して `pegasus-orphan-hold/v1` を武装させた。既存記述は引き金を
  「監査・受入・変異のように dispatch する検査」と書いていたが、**焦点走もこの族である**。
  「テスト 1 ファイルだけだから軽い」という見積りが誤りで、dispatch するか否かは
  runner 側の自動判定が決める。作業ツリーへの被害はゼロ (変更 2 file・差分・HEAD すべて不変)。
  `qdel.attempted` が false だったので F47 の submission-disabled は武装せず、
  hold の recovery 契約 (request の不在確認 → source の clean/HEAD 確認 → 手動削除) を
  親が実行して 140 秒で解除した。`qstat` は消えた request にも rc=0 を返すため、
  不在判定は出力本文で行った。
