---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1279-layer3-head-outside-repo
seq: 3
---

## 新規

### {{F:proxy-precondition-false-red}}. テストの前提 assert を代理条件で書き、環境の残骸で偽赤になった [テスト代表性]

- 事象: repo 外 campaign の fallback を検査する 3 node が、前提 assert
  「campaign の祖先に `.git` が 1 つも無い」で赤になった。実行機に空の `/tmp/.git`
  directory が残っており、pytest の一時 directory がその配下だったため。空 directory は
  git repository として無効なので、テストが本当に必要とする性質 (git HEAD を取得できない)
  は満たされており、production の挙動は正しかった。焦点走 1 回を捨てた。
- 根本原因: 前提が要求する性質そのもの (`_git_head` が送出する) ではなく、その十分条件でも
  必要条件でもない代理条件 (祖先に `.git` が無い) を assert した。代理条件は環境の残骸・
  無関係な repository・bind mount で容易に破れる。
- 恒久対応: 前提 assert は、テストの本体が依存する性質を**その性質を計算する production の
  関数を直接呼んで**固定する。周辺の観測可能な条件で代理しない。代理せざるを得ない場合は、
  代理と本来の性質の差を assert のすぐ上に 1 行で書く。
- 再発検知: 前提 assert が production の判定関数を呼ばずに filesystem・環境変数・path 形状を
  直接見ている箇所は、レビューの「恒真・偽赤」レンズで指摘する。
