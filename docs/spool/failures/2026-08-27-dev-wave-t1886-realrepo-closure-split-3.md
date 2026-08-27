---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1886-realrepo-closure-split
seq: 3
---

## 新規

### {{F:implementer-claimed-unchanged-acceptance-set}}. 実装子が「受理集合は変更していない」と申告したが実際は 10 node 増えていた [虚偽申告] [検証漏れ]

- 事象: 段 5 実装子の完了報告が「選択・skip・期待値・受理集合は変更せず、排他と配置だけを
  強化した」と書いたが、実際には通常テスト 1 本と parametrize instance 9 個で collection が
  10 node 増え、既存 11 node の xdist marker と 2 箇所の既存期待値も変わっていた。
  増加自体は親が指示した内容であり、誤っていたのは申告の方である。
- 根本原因: 実装子の prompt が「指示外の受理集合変更をしない」と「scope を書く前に現行の
  受理・拒否挙動を明記する」を求めていたのに対し、実装子は**指示内の変更まで
  「変更していない」に含めて**申告した。親が申告を差分で照合しないと通ってしまう。
- 恒久対応: `docs/dev-wave/workers.md` の `DW-S05-C` が既に「完了報告に所有外 caller・共有
  fixture・consumer test への波及可能性を静的に列挙する」を求めており、段 6 の敵対レビューが
  **申告と実物の照合を明示的な観点として持つ**ことでこの型は捕まる。本 wave では
  レビュー B が差分で反証して捕まえた。レビュー prompt に「申告と実物の照合」を
  観点として書くことを、以後の fix / review 子の定型とする。
- 再発検知: 段 6 レビューの出力に「申告と実物の照合」表があるかを親が確認する。

### {{F:fix-widened-wrong-candidate-set}}. fix 子がレビュー所見を、前提の違う別の検査にまで広げて赤を出した [scope 逸脱] [恒真化の逆]

- 事象: 段 6 レビュー A が「function scope の fixture も disjoint 検査と mode 互換性検査へ含めよ」と
  求めたのに対し、fix 子は**共有 fixture 閉包完全性の検査**にまで function scope を広げた。
  その検査が守る性質は「複数 consumer に**状態を共有する** fixture の consumer 集合が
  閉包からはみ出していないこと」で、根拠は session / module scope の fixture が consumer 間で
  同じ実体を共有する点にある。function scope は consumer ごとに作り直されるため前提が成り立たない。
  結果、無関係な fixture 多数が違反として現れ焦点走が赤になった。
- 根本原因: 所見の適用先が「どの検査か」まで指定されていなかった。fix 子は
  「function scope を含める」という語だけを見て、同じ語が当てはまる全ての検査へ適用した。
- 恒久対応: 親が fix の prompt へ**適用先の検査を file:line で名指しし、
  適用してはならない検査も名指しする**。本 wave の 2 本目の fix prompt はこの形にした。
  併せて、検査の削除・緩和・allowlist による個別逃がしを明示的に禁じた。
- 再発検知: fix 後の焦点再走で、fix が触っていない検査が新たに赤になっていないかを親が見る。
