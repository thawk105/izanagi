---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1174-numactl-contract-gate
seq: 2
---

## 新規

### {{F:mutation-core-mask}}. byte 束縛されたソースへの変異は、意味に無関係な共通核で全変異が KILLED に見える [テスト代表性]

- 事象: `pipeline.py` を対象にした変異 13 件が全て KILLED になったが、内訳を見ると
  44〜56 node のうち **43 node が全変異に共通**していた。この共通核は
  `contract-loader-drift` (disk bytes が記録 commit blob と不一致) であり、変異の意味とは
  無関係に「ファイルが 1 byte 変わったこと」だけで発火する。核だけを見て
  「13/13 KILLED だから検出力がある」と読むと、実際には検出できていない変異
  (このとき 2 件が該当) を検出済みと誤認する。
- 根本原因: `campaign_lock` の enforcement source closure に入るソースは、campaign identity が
  disk bytes と HEAD blob の一致を要求する。変異 harness は HEAD を固定したまま disk を書き換える
  ため、identity を構築する全テストが変異の内容によらず落ちる。`DW-M03` の「過剰決定した fixture」
  がソース束縛の形で現れたもの。
- 恒久対応: `docs/dev-wave/mutation.md` `DW-M02` / `DW-M03` の既存義務 (mask を疑い実効 gate へ
  再照準する / 過剰決定は単独変異の証拠から外す) を、**共通核の集合演算で機械的に適用する** —
  全変異の `failed_nodes` の交差を核として取り、核を差し引いた delta が空でないことを
  変異ごとに確認する。delta が空の変異は KILLED と記録しない。核が非空なら worklog に核の
  件数と原因を明記する。
- 再発検知: 変異台帳に核と delta を併記する運用。delta=1 の変異は、その 1 node が唯一の
  killer であることの証拠になる (本 wave では bench の `record_rep_returncodes=True` 分岐と
  実 trace 起動の argv がこれに該当した)。

### {{F:codex-child-cannot-git-merge}}. codex 子は `.git` が read-only で `git merge` を起動できない [手順漏れ]

- 事象: 実装面の main 取り込みを Codex `role=author` の子に投げたところ、
  `git merge --no-ff --no-commit main` が競合を生成する前に
  `ORIG_HEAD.lock: Read-only file system` で失敗した。子は差分ゼロで正しく報告して降りたが、
  1 起動分 (約 2.5 分) が無駄になった。
- 根本原因: codex の sandbox は working tree を書けても Git 管理領域を書けない。
  既知の「子は dispatch できず repo 外にも書けない」と同族の制約で、merge は Git 管理領域への
  書き込みを伴う。
- 恒久対応: `docs/dev-wave/operations.md` `DW-O17` の merge 手順に、**親が
  `git merge --no-ff --no-commit` を起こして競合マーカーを作り、Codex `role=author` の子は
  working tree の競合解決だけを行い、`git add` と commit は親が行う**、という分担を書く。
  これにより「実装面 path が両親と異なれば Codex `role=author` へ」の義務を満たしたまま
  実行可能になる。
- 再発検知: 子の prompt に「`git merge` を自分で実行するな。親が実行済みで競合マーカーが
  作業木にある」と書く運用。書き忘れても子は fail-closed で降りるため、被害は 1 起動分に留まる。
