---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: t1371-official-run-root
seq: 3
---

## 新規

### {{F:shared-tmp-git-ancestor-poisoning}}. 共有ログインノードの `/tmp` 直下に他プロセスが一時的に `.git` を作り、repo 外検証を無差別に誤検出させる [計測汚染]

- 事象: `tools/mutation_harness.py --runner-mode local` で本 wave の official/exploration
  repo 外強制ロジック (`_has_git_ancestor`) を検査したところ、`/tmp` 配下の無関係な多数の
  test が「official output_root は repository 外でなければならない」で一括 red 化した
  (最大92件)。直接確認すると `/tmp/.git` という空ディレクトリ (所有者 tanab、本 wave とは
  無関係) が存在し、`_has_git_ancestor()` が `/tmp` 配下の**あらゆる** path を repo 内と
  誤判定していた。`rmdir` で除去すると一時的に解消するが、その後の別走行で再度出現・消失した
  (別プロセスが短時間だけ `/tmp/.git` を作る何らかの操作を行っていると推定、`ps -u` で
  同一アカウントの複数 dev-wave セッションが並行稼働していることを確認済み)。
- 根本原因: `_has_git_ancestor()` (exploration 由来、本 wave 以前から存在) は path 祖先の
  どこかに `.git` という名前の**エントリが存在するだけ**で repo 内と判定し、それが実際に
  機能する git repository か (HEAD・objects・refs を持つか) を検証しない。共有ログインノード
  の `/tmp` は同一アカウントの複数セッション・他ツールが読み書きする共有空間であり、
  この構造検査の弱さが `/tmp` 全体を巻き込む。
- 恒久対応: 未実施 (本 wave の scope 外、規律5に照らし対応せず記録のみ)。将来 `_has_git_ancestor`
  を強化する場合は「実在する完全な git repository か」まで検証する案を検討候補として残す。
- 再発検知: ログインノードでの local test 実行が説明のつかない大量 red (特に「repository 外
  でなければならない」という文言を含む) を出したら、`ls -la /tmp/.git` 等で `/tmp` 直下の
  迷子 `.git` 混入をまず疑う。
