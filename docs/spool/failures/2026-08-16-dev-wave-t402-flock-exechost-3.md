---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t402-flock-exechost
seq: 3
---

## 新規

### {{F:parent-violated-own-preregistration}}. 親が自分で 30 分前に凍結した事前登録に反する受理集合の拡大を子へ指示した [手順漏れ]

- 事象: 段 6 fix 2 巡目で、親が実装子へ「qstat の `Request ID:` block が 1 件で、その中に
  job/host の組が 2 組ある形式も受理せよ」と指示した。しかし同じ wave の
  `output/insights/2026-08-16_t402-flock-execution-host/verdict-preregistration.md` は
  `H := 対象 request の qstat block がちょうど 2 件` と凍結しており、**この凍結文は親自身が
  その約 30 分前に書いて commit 対象にしていた**。焦点再レビューが「凍結 H に反する受理集合の
  拡大 = 事前登録違反」と検出し、親は指示を撤回して fix 3 巡目で凍結形へ戻した。
- 根本原因: 過剰拒否 (実 2 job grammar が未知で、正当な出力を拒否して唯一の測定機会を失う恐れ)
  を減らそうとして、**凍結文との整合を確認せずに受理集合を広げた**。凍結を「他人が課した制約」と
  暗黙に扱い、自分が直前に作った制約であることを見落とした。加えて、広げた形は job number 列と
  host 列を出現順に zip するだけで、2 block 形式と同等の束縛を持っていなかった
  (安全側の受理集合が実質的に緩む)。
- 恒久対応: {{D:qstat-grammar-mismatch}} 決定 (5) が「2 job 実出力が未知でも受理集合は広げない。
  過剰拒否で `null` に終わっても実物の raw が証拠として残るのでそちらを採る」を固定する。
  手順側は `DW-S04` / `DW-O13` の「受理集合を変える指示を子へ出す直前に、この wave で凍結済みの
  事前登録文書を再読する」を段 8 で routing する。
- 再発検知: 焦点再レビュー子へ「凍結した判定式の文書」を必読資料として渡し、
  実装・fix 指示との差分を判定させる (本 wave で実際に発火した経路)。

### {{F:waiter-treats-missing-pid-file-as-death}}. 待ち手が pid file 不在を producer 死亡と解釈し、子が走行中に完了通知を出した [恒真ゲート]

- 事象: 段 6 fix 3 巡目で `nohup setsid bash <launcher>` の**直後**に
  `tools/dev_wave_wait.py producer --pid-file <pid>` を起動したところ、待ち手が
  **rc=0・出力ゼロで即座に終了**し、完了通知が届いた。`.done` も成果物も存在せず、
  子 (pid 685171) は実際には生きて走り続けていた。
- 根本原因: launcher script が `echo $$ > <pid file>` を書く前に待ち手が pid file を読み、
  読めなかったため「producer は死んだ」と判定して正常終了した。**待機条件が起動前に恒真で
  満たされる**型である。
- 恒久対応: 待ち手の起動前に pid file の実在を確認する運用へ変えた (本 wave の以後の全投入で実施)。
  機構側の恒久対応は {{T:waiter-pid-file-race}} で起票する — pid file 不在を「未起動」として
  bounded に待つか、待ち手が pid file 不在なら起動前に停止する。
- 再発検知: 完了通知を受けたら**成果物実在 + `.done` + producer 死**の 3 点照合を必ず行う
  (memory `background-task-notifications-can-be-fabricated`)。本事故はこの 3 点照合が捕まえた。
