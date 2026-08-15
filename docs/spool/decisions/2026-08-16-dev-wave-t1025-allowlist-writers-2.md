---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1025-allowlist-writers
seq: 2
---

## {{D:hooks-edit-route}}. hooks/ 配下を変更する wave は有効化前 commit の別 worktree で実装し merge で持ち込む

**決定:** `hooks/` 配下のコードを変更する wave は、次の経路だけを使う。

1. 親が、`guard_write` に hooks 判定が入る 1 つ手前の commit を base にした**第 2 worktree** を作る。
2. Codex 実装子はそこで対象ファイルだけを編集する。テストは編集可能な wave worktree 側で
   別の実装子が書く (所有を分ける)。
3. 親が第 2 worktree で統合 commit を作り、wave branch へ `git merge` で持ち込む。
4. merge 後に親が受理集合を再実測し、wave 前との**反転検査**を通してから次へ進む。

D374 は「guard の修正が必要になったら有効化前の commit から作り直す」と定めていたが、
その前提は「wave 開始時点では hooks/ を編集できる」だった。hooks/ の自己保護が main に
入った後は**開始時点で既に編集不能**であり、この経路が唯一の実行形になる。

**理由:**
- 実測で `apply_patch` / `Write` / `Edit` のすべてが `hooks/` 配下を拒否する
  (例外は exact `hooks/README.md` のみ)。Codex 実装子も親も、直接には 1 byte も書けない。
- 残る手段は設計上の限界を突く形 (script file 越しの書き込み、path literal を持たない
  `git apply`) だけで、どちらも hook が「見えない」と自認している経路であり、
  拒否の迂回にあたる。防壁を狭める wave がその防壁を迂回して実装するのは筋が通らない。
- 別 base の worktree は迂回ではない。guard の判定は worktree ごとに checkout された
  guard 自身が行うので、有効化前の base では**設計どおり**編集が許可される。
  main へは merge を通してのみ入るため、統合時の監査は従来と変わらない。

**却下した選択肢:**
- 一時的に判定を無効化する flag / env — 受理集合を縮める目的と矛盾し、fail-open 経路を残す。
- script file 越しの書き込み・`git apply` — 拒否の迂回であり、以後の wave が同じ手を
  正当化する前例になる。
- 親が直接編集する — 実装面の Codex author 契約に反する。

## {{D:acceptance-set-reversal-check}}. 受理集合を変える wave は wave 前との反転検査を証拠にする

**決定:** 防壁の受理集合を変える wave は、期待表の緑だけを証拠にしない。**wave 前の実装と
wave 後の実装へ同一のコマンド集合を通し、`deny → allow` の反転が 0 件であること**を実測して
記録する。反転が 1 件でもあれば land しない。

**理由:**
- 受理集合を縮める意図の実装が、綴りの解析を作り込む過程で**元から拒否していた形を
  通すようになる**ことがある。期待表は「閉じたい形」を列挙するため、この向きの後退を
  構造的に検出できない。
- 実際にこの wave で、script positional の後ろに置いた in-place option が
  wave 前 deny から wave 後 allow へ反転した。期待表は全件緑のままだった。
- 反転検査は wave 前後の 2 実装へ同じ入力を通すだけで、追加の人手判断を要さない。

**却下した選択肢:**
- 期待表へ「wave 前から deny の対照群」を足すだけで足りるとする — 対照群は列挙した分しか
  守らず、実装が新設した解析器の綴り空間を覆えない。
- レビュー子の指摘に依存する — 実際に見つけたのはレビュー子だったが、これは属人的で
  再現性がない。機械検査へ落とす。
