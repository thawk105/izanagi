---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-backoff-tail-mechanism
seq: 3
---

## 新規

### {{F:caption-defined-but-never-rendered}}. 開示義務のある caption が成果物に描画されず、内部値だけを見る test が緑を返した [恒真ゲート] [テスト代表性]

- 事象: 図の caption (非認証の 3 値と 6 つの但し書き) は module 定数として定義され、
  test も「12 個の literal が各 1 回ある」ことを検査していたが、**PNG / PDF には 1 文字も
  描画されていなかった**。figure に artist として足す行が無く、figure-level の text は
  suptitle だけだった。test は matplotlib の private 属性を読んでいたため、
  **描画されていなくても通る恒真な検査**になっていた。成果物には格の断り書きが無いまま出ていた。
- 根本原因: 「文字列が存在するか」を検査して「成果物に出るか」を検査していない。
  定義と描画の間に経路があるのに、経路を通した現物を一度も見ていなかった。
- 恒久対応: caption を `fig.text` の実 artist として bbox 検査の前に足し、
  test は `figure.findobj(Text)` が返す**実 artist のテキスト**を走査する形にした。
  親は実 report 3 本で生成器を走らせ、PDF を `pdftotext` で抽出して 12 literal を現物で数えた。
- 再発検知: 事前登録した変異 10 件はすべて意図した test に殺されたが、
  **この欠陥は変異 matrix の外にあった** — 恒真な oracle は、その oracle が守るはずの実装を
  変異させても赤にならないので、変異では見つからない。見つけたのは段 6 の敵対レビューで、
  「恒真な assert・stub で置き換えた偽の正例・実装を写しただけの oracle を探せ」と
  名指しで指示したレンズである。**成果物に出るべき開示は、内部表現ではなく成果物の現物で検査する。**

### {{F:isolated-session-cannot-touch-sibling-worktree}}. 背景 job の worktree 隔離が別 worktree への一切の command を拒否し、cd 後は永続 shell が取り残された [手順漏れ]

- 事象: 段 5 の実装子を `DW-S05-A` どおり別 worktree (`.codex/worktrees/`) へ置こうとしたところ、
  背景 job の worktree 隔離が**そこを cwd とする command を全部拒否**した。
  `--repo <別 worktree>` のような引数経由でも、内部で cd する script 経由でも拒否される。
  さらに一度 `cd` した後は**永続 shell がその worktree に取り残され**、`pwd` すら落ちた。
  `EnterWorktree` に自分の worktree の path を渡して入り直すまで復旧しなかった。
- 根本原因: 隔離は「このセッションの command は自分の worktree 内で走る」を強制する。
  `DW-S05-A` の「各単位を別 worktree へ置く」は、複数の実装単位を並列投入して所有を分ける
  ための規定であり、隔離セッションで単一単位のときは前提が成り立たない。
- 恒久対応: 隔離セッションで実装単位が 1 つなら、実装子を wave worktree で直接走らせる。
  親は子の稼働中に repo を触らない (変異・受入の clean tree 規律と同じ)。
  `cd` してしまったら `EnterWorktree` に自分の worktree の絶対 path を渡して入り直す。
- 再発検知: 起動前に「実装単位は 2 つ以上か」を数える。1 つなら別 worktree を作らない。
  作ってしまった未使用 worktree は、隔離セッションからは撤去もできないので次 wave へ引き継ぐ。
