---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1697-closed-critic
seq: 4
---

## 新規

### {{F:concurrent-git-status-reports-whole-tree-dirty}}. 同じ worktree へ `git status` を並行させると、全 tracked file が編集中に見えた [計測汚染]

- 事象: 段 1 の編集面重複の実測で、全 worktree を走査する処理を 2 本同時に走らせた
  (1 本目は親が時間切れで打ち切り、2 本目を背景で起動した)。結果、`worktree-dangling-audit-speed` と
  `worktree-dev-wave-t1219-carry-same-id` の 2 本が「`.claude/agents/*.md` を含む tracked tree 全体を
  編集中」と報告した。直後に 1 本ずつ測り直すと**両方とも 0 行 (clean)** で、branch tip も
  `main` と同一だった。
- 根本原因: `git status` は index を refresh して書き戻す。同じ worktree に対して 2 プロセスが
  同時に走ると、一方が書き換え中の index をもう一方が読み、全 tracked file が stat 不一致
  = 編集中として描画されうる。読み取り専用の観測に見えるが、実際には index を書く操作である。
- **誤った結論の一歩手前だった:** この出力を信じていれば「`.claude/agents/*.md` は 2 つの wave が
  所有中」と判定し、本 wave の中心方針 (role file を 1 byte も変えない) を**誤った理由で**
  採ることになっていた。方針自体は別の根拠 (pin 閉包) で正しかったため実害は出ていない。
- 恒久対応: 編集面重複の実測は**同じ worktree へ同時に 2 つ以上の `git status` を当てない**。
  打ち切った走査を再投入するときは、先行プロセスの終了を確認してから起動する
  (`pgrep -af` で worktree path を含む生存 process を照合する)。
  dirty と出た worktree は、**採用する前に単独で測り直す**。
- 再発検知: 全 tree が dirty に見えたら、それ自体を異常の signature として扱い、単独再測を必須にする。
  branch tip が `main` と同一なのに tracked tree 全体が編集中という組合せは、実体としてはまず
  起こらない (その wave はまだ何も commit していないのに全 file を触っていることになる)。

- 併記 (同 wave の near miss、別型・台帳項目を起こさない): 親が段 3 の子 prompt へ
  「負の対照 3 本の docstring が scope 外と書いている」と**現物を数えずに**書き、実際は 2 本だった。
  敵対レンズが実測で訂正したため下流へ伝播していない。既存の敵対相談段が想定どおり機能した
  事例であり、契約側の欠落ではないと判定して手順の変更は行わない。
