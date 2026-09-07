---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2412-frozen-spec-fixpoint
seq: 3
---

## 新規

### {{F:approved-ruling-not-read-in-stage1}}. 承認済みユーザー裁定を段 1 で引かず、裁定より狭い形を実装した [手順漏れ]

- 事象: dev-wave `t2412-frozen-spec-fixpoint` の段 1 で、依頼文と insight の一次資料だけを読んで
  brief を書き、`docs/worklog.md` の T-2412 項と `docs/decisions.md` の D1774 を引かなかった。
  D1774 は「HEAD が `source_commit` の**子孫**であること」を要求していたが、親は段 4 で
  「HEAD が唯一の子であり、かつ差分が spec 1 path だけ」という**より狭い**形を自分で裁定し、
  段 5 の実装、段 6 の敵対レビュー 2 本と変異 9 件まで進めてしまった。段 7 の記録で台帳の
  base digest を取るために main の worklog を読んで初めて気づき、fix 2 本で作り直した。
- 根本原因: 依頼文が一次資料として insight の README を名指ししていたため、それを読めば十分だと
  判断した。DW-S01 の「brief 前に承認済み裁定と引数の前提を実測する」を、依頼文が指す資料の
  確認だけで済ませた。**課題 ID (T-2412) が与えられているのに、その ID を台帳で引かなかった。**
- 恒久対応: {{D:frozen-spec-ancestor-binding}} で裁定に合わせて作り直した。段 1 の brief 前に、
  依頼が課題 ID を含むなら `docs/worklog.md` の当該項と、そこが指す D 番号を必ず引く。
  worktree は wave 開始時点で止まるため、この lookup は land 先の local main の現物に対して行う
  (台帳の base digest を取る手順と同じ)。
- 再発検知: 狭い形を実装した段 4 の裁定文にも、敵対レビュー 2 本にも、変異 9 件にも、
  裁定との食い違いは現れなかった。**子は親が射影した資料しか見ないため、親の資料選択の誤りは
  子の敵対レビューでは検出されない。**検出したのは台帳の base digest 取得という無関係な作業である。
  段 1 の資料選択そのものを検査する機構は無い。

### {{F:commit-landed-in-primary-checkout-via-stale-cwd}}. 永続 shell の cwd が主 checkout に残ったまま commit し、local main を壊した [権限逸脱] [手順漏れ]

- 事象: dev-wave `t2412-frozen-spec-fixpoint` の段 7 で、`git add -A; git commit` を隔離 worktree
  ではなく**ユーザーの主 checkout** で実行した。untracked だった `.codex/worktrees/` の 110 本が
  gitlink (mode 160000) として local main の先頭 commit `c12e25078` に入った。
  全 session の land が DW-O25 の全史 provenance 監査で rc=29 になり、新規 worktree の
  submodule 初期化も `no submodule mapping found in .gitmodules` で rc=1 になった。
  別 session (next-tasks skill relocation) が独立に検出して通報してきた。
- 根本原因: 直前のコマンドが `cd /work/1/SFC/tanab/izanagi && git log` で main の台帳を読んでおり、
  **Bash tool の cwd はコマンドを跨いで残る**。次のコマンドは worktree にいるつもりで書かれていた。
  `git add -A` は「その木の untracked をすべて」拾うため、意図した 1 file ではなく 110 本の
  埋め込み repo を staged にした。
- 併発した第 2 の欠陥: 同じコマンドが `check_ai_provenance.py ... 2>&1|tail -2; git commit` の形で、
  検査の rc をパイプで握り潰していた。検査は「1 件中 1 違反」を報告していたが `set -e` は
  pipeline の rc (tail の 0) しか見ず、commit が実行された。F37 の同型再発である。
- 恒久対応: worktree を跨ぐ session では、状態を変える git 操作を `git -C <worktree の絶対 path>`
  で明示する。cwd に依存しない。`git add -A` を使わず、対象 path を明示して stage する。
  検査は `> <log>; echo "RC=$?"` の形で rc を単独で取り、パイプへ通さない。
- 再発検知: 主 checkout の HEAD が自分の wave の commit になっていないかを、commit 直後に
  `git -C <worktree> log --oneline -1` で確かめる。なお修復も失敗した — `git reset` を試みたが、
  自分の `git status --porcelain` が 110 本の埋め込み repo を走査したまま `index.lock` を
  握り続け、主 checkout の全 git 操作が止まった。**壊した後の修復手段まで同じ原因で塞がる。**

## 再発

### F37

- **再発: 2026-09-08** — dev-wave `t2412-frozen-spec-fixpoint` の段 7 で
  `set -e; git add -A; python3 tools/check_ai_provenance.py --message-file <f> 2>&1|tail -2; git commit -F <f>`
  と書いた。検査は「実装面に Codex role=author がない — 110 paths」で rc=1 を返していたが、
  `set -e` が見るのは pipeline 全体の rc (= `tail` の 0) であるため commit が実行され、
  provenance 違反が local main へ入った (`c12e25078`)。F37 の初出は `&&` の右辺、今回は
  `set -e` 下の逐次実行で、**どちらも「パイプの rc は最後のコマンドのもの」という同じ取り違え**である。
  出力を短くする `| tail` を検査コマンドに付けた時点で guard は恒真になる。
