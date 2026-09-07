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

### {{F:mutation-wait-done-file-false-positive}}. 変異 harness の待ちを `.done` file で判定すると、走行中に完了と誤判定する [観測]

- 事象: 変異 harness の完了を wrapper の `.done` file で待ったところ、harness が稼働中
  (経過 8 分、ledger を書き進め中) にもかかわらず完了イベントが 2 回出た。`.done` は実在せず、
  成果物も未完成だった。親はこれを「完走」と読み、走行中に注入されていた変異を
  「復元忘れの残骸」と誤読して `git checkout` で消しかけた。消していれば変異走が全損していた。
- 根本原因: 待ち手が producer の生死を、pid file に書かれた **wrapper shell の pid** で見ていた。
  bash は script の最終命令を exec で置き換えることがあり、wrapper の pid が先に消える一方で
  実プロセスは生き続ける。`.done` の実在検査も、この誤りを補えなかった。
- 恒久対応: 変異 harness の待ちは **harness process 自身の pid** を `ps -eo pid,args` から
  引き当てて `kill -0` で見る。`.done` file と wrapper pid を単独の判定根拠にしない。
  同じ誤りは受入の待ちでも起き、別 wave の受入プロセスを自分のものと誤認しかけた
  (receipt file の basename が偶然一致したため)。**pid は argv 全体で一意化して引く。**
- 再発検知: 走行中に tree へ変異が見えるのは正常である。tree の dirty を「復元忘れ」と読む前に
  harness process の生死を実測する。ledger の `summary.registered` と `completed` の差でも
  未完走が分かる。
