---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t675-pin-semantic-gap
seq: 1
---

## 新規

### {{F:codex-child-oom-under-shared-user-cap}}. 並行 wave が増えると codex 子が共有 16GiB 上限で無音 kill される [セッション死・救出]

- 事象: 本 wave で read-only の codex 子が **3 回**、`.done` を書かず log を途中で切って消滅した
  (段 2 の 1 本目、段 3 レンズ A・B の初回)。error 文字列も終了メッセージも出ない。
  いずれも大きいファイル (`tools/check_docs.py` 4500 行超、`docs/decisions.md`) を
  丸ごと表示した直後だった。
- 根本原因: login node の cgroup 上限は **session ではなく user 単位**である。
  実測 = `/sys/fs/cgroup/user.slice/user-<uid>.slice/memory.max` が
  **17179869184 (16 GiB)**、同 `memory.events` の `oom_kill` が 1308。
  自分の子が居ない時点でも `memory.current` が 10.6 GB あり、これは
  **同時に走る別の背景 job (別 wave) の codex 子が同じ user slice を食っている**ためである。
  1 wave 単独の見積りで子を並列投入すると、他 wave の分と合算して上限に当たる。
- 影響: 実害は wall-clock のみ。pid 監視の待ち手が 3 回とも producer 死を検出したため、
  無音ハングにはならなかった。`.done` の出現だけを待つ待ち手なら 3 回とも永久に待つ。
- 恒久対応: memory `login-node-memory-cap-16gib` の「上限は user 単位で全並行 job が共有する」
  という射程を運用へ効かせる — (1) 待ち手は必ず pid を待ち条件に含める
  (`docs/dev-wave/core.md` `DW-C00` の「生産者の死も待ち条件に含める」が既に義務化しており、
  本件はその義務が実際に効いた事例である)、(2) 子の prompt に**巨大ファイルの全文表示を
  禁じ、行範囲読みを指示する**。本 wave では (2) を適用した prompt へ差し替えた 2 本が
  いずれも完走した (段 2 再投入、段 3 レンズ A・B の再投入)。
- 再発検知: 子が死んだら `/sys/fs/cgroup/user.slice/user-<uid>.slice/memory.events` の
  `oom_kill` を読む。増えていれば資源であり、prompt や認証を疑う前に並列度を下げる。

## 再発

### F24

- **再発: 2026-08-10** — 2026-08-09 と同型を独立 3 例。受入全走の待ち手へ
  `.done` 不在・producer 生存・計算ノード job が `qstat` で RUN のまま
  「ACCEPTANCE-DONE rc=0」が届いた。3 例とも成果物実在・`.done`・producer 死の 3 点照合で
  弾き、実完了は `.done` の出現でのみ返る待ちに切り替えて確認した
  (実測 = 8012 passed / 20 skipped / 511.08 秒 / rc=0)。**恒久対応は既存の `DW-O01` で足りる。**
  本 wave の追加事実は、**偽完了が同一 wave 内で反復し、待ち手を張り直すたびに再発する**点である
  — 1 度弾いたから以後は正しい、とは扱えない。

### F104

- **再発: 2026-08-10** — 四つ目の方向。投入直後の `pgrep -f <script>` が**複数 pid** を返し、
  親がそのうち一時的な pid を待ち条件にしたため、**走行中の受入全走を「producer 死」と誤判定**した
  (実体は別 pid で生存、計算ノード job も RUN)。F104 系の既往は
  「並行 wave の子に一致」「自分の子に一致しない」「待ち手自身に一致」の 3 方向で、
  **同一 producer の複数 pid から誤った 1 つを選ぶ**形は射程外だった。
  判別 = pid を待ち条件にする前に `ps -o pid,ppid,etime,cmd -p <pid>` で実体を確認し、
  script 本体の pid (親 shell ではなく) を選ぶ。復旧は正しい pid での待ち手張り直しで足りた。
