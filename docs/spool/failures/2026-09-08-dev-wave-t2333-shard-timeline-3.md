---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2333-shard-timeline
seq: 3
---

## 新規

### {{F:ledger-nodeid-count-merge-collision}}. 受入台帳の `nodeid_count` が、test node を足す wave 同士の必然的な衝突点になっている [資源競合]

- 事象: 受入全走の post-claim merge が `stage=merge rc=70 source_rc=1` で落ち、受入 attempt を
  1 つ捨てた。原因は `orchestrator/tests/acceptance_duration_ledger.json` の `nodeid_count` の
  1 行が衝突したこと。node の map 自体は git が和集合として自動 merge するが、`nodeid_count` は
  両側が同じ行を別の値へ書き換えるので必ず競合する。同日の 2 回の main 取り込みで 2 回とも起きた。
- 根本原因: `nodeid_count` は map の長さから決まる派生値でありながら台帳に実体として持たれている。
  test node を足す wave はすべてこの 1 行を書き換えるため、並行する限り互いに衝突する。
  受入は 25 分かかるので、走行中に別 wave が land すると取り直しになる。
- 恒久対応: 未了。緩和の設計にはユーザー裁定が要る (台帳の schema と既存 consumer に触れるため)。
  当面は「main を固定 SHA で取り込んでから受入を投げ、落ちたら固定 SHA を取り直して詰める」で回す。
  次の一手へ登録した。
- 再発検知: 受入 receipt の `IZANAGI_ACCEPTANCE_ATTEMPT_V1` が
  `classification=merge` / `reason=terminal-merge` を出す。台帳 file が衝突 path に含まれるかは
  `git diff --name-only <base> <main>` と wave 側の同 diff の交差で事前に測れる。

### {{F:background-waiter-false-completion}}. 背景の待ち手が producer 稼働中に「完了」を出し、走行中の変異を復元忘れと誤読しかけた [観測]

- 事象: 変異 harness の完了待ちが、harness 稼働中 (経過 8 分、ledger を書き進め中) に完了イベントを
  2 回出した。`.done` は実在せず成果物も未完成だった。親はこれを「完走」と読み、走行中に注入されて
  いた変異を「復元忘れの残骸」と誤読して `git checkout` で消しかけた。消していれば変異走が全損して
  いた。同じ誤検知は同 wave で受入の待ちでも 2 回起き、計 4 回出た。
- 根本原因: 2 つあり、どちらも待ち手 script の書き方に起因する。
  (a) **背景コマンドと Monitor の command に書いた改行が空白へ潰れる。**
  `while cond` / `do` / `sleep` / `done` / `echo` を改行区切りで書くと 1 行に崩れ、
  `done echo "..."` として loop を通らずに即 echo する。実測で
  `eval 'P=$(cat f) while kill -0 "$P"; do sleep 60; done echo "..."'` の形に崩れていた。
  (b) **sandbox 内の shell は他プロセスへ signal を送れないため `kill -0 <pid>` が必ず失敗する。**
  親の対話 shell では同じ pid に対し `kill -0` が rc=0 を返すので、書いた側では再現しない。
  生存判定が常時「死亡」になり、待ちが即終わる。
- 恒久対応: 待ち手 script は **1 行に書き、区切りを `;` で明示する**。生存判定は signal ではなく
  **`[ -d /proc/<pid> ]` の読取り**で行う。pid は pid file でなく `ps -eo pid,args` から
  **argv 全体で一意化して**引く (別 wave の同名 receipt file と誤一致した実測がある)。
  `.done` file の実在を単独の完了根拠にしない。
- 再発検知: 完了を読んだら必ず成果物 (receipt / ledger / `.done` の中身) を実在で検算する。
  走行中に tree へ変異が見えるのは正常であり、tree の dirty を「復元忘れ」と読む前に
  producer の生死を `/proc` で実測する。変異台帳は `summary.registered` と `completed` の差でも
  未完走が分かる。
