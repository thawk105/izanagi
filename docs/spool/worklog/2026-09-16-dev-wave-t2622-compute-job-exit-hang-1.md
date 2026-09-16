---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2622-compute-job-exit-hang
seq: 1
title: [T-2622] 計算ノード job が pytest 完了後に終わらない事象を計算ノードの 4 条件実験で切り分け、子孫の出力 fd 保持が遅延の必要条件でないことを確定した (docs のみ、branch worktree-dev-wave-t2622-compute-job-exit-hang、実装面の差分 0 なので変異 matrix は DW-S04 により免除)
---

## 本文

- **依頼の前提が成り立っていなかった。** 「前 wave が残したトレースが次の再発時にどの段で
  止まったかを与える」が出発点だったが、**その再発が 0 件**である。トレース導入以降の
  計算ノード job 169 本のうち 159 本がトレースを持ち、**全部が `job-run-returned` まで到達**、
  NQSV 会計との差は最大 0.0 秒。保存されている受領証 332 件はすべて `terminal_reason =
  scheduler-end-state` で、`overall-timeout` は 0 件。walltime 比の最大は 0.227。
  **痕跡から同定する経路は行き止まりだった。**
- **厳密な陽性例は F853 の 1 件だけだと分かった。** F901 も同型と数えていたが取り下げた
  (待ち手自身の長時間待機であって pytest 完了後の停止ではない)。F853 / F901 の submission dir は
  どちらも保存されていない。
- **痕跡が使えないので機序を直接測った。** `--task generic` で 4 条件を直列・detached で投入し、
  判定表は結果を見る前に固定した。子の寿命を 75 秒に固定し、job の stdout / stderr を手放す
  時刻だけを動かした (統制 = 子孫を作らない / 即時 / 30 秒 / 手放さない)。
  **解放時刻を動かしても job の終了は 0.285 秒しか動かず、子孫の有無では約 70 秒動いた。**
  結論は {{D:job-exit-delay-attribution}}。
- **親は自分の裁定を段 4 で 3 件、段 6 で 10 件撤回した。棄却した所見は 1 件も無い。**
  段 3 の敵対 2 レンズは「`os.fsync` を refuted とした根拠が誤り (dir fsync は `os.replace` の
  後に来るので result 公開済みでも止まりうる)」「トレースの説明が広すぎる」
  「F846 を thread join 待ちと型付けたのは親の推測で同 F は根本原因未特定と明記」を突き、
  **安全に関わる実 defect を投入前に 1 件見つけた** — 全体期限は RUN 観測前から
  `submitted + walltime + overall_grace` で動くので、当初案の walltime 120 + grace 300 = 420 秒は
  `--queue-wait-timeout 900` より先に `overall-timeout` を起こし取消経路に入る。
  walltime 180 / queue-wait 600 / overall-grace 900 へ直して投入した。
- **段 6 の敵対 2 レンズが結論の断定を 10 か所で削らせた。** 最大のものは
  「**全記録で `sid == pgid` なので session と process group を分離できていない**」で、
  親の「session が終端条件」という同定を撤回した。ほかに「F853 の機序を誤りと断じるのは過大」
  「通常 file には EOF が無いという論証は誤りで `st_mode` も記録していない」
  「事前登録表の時刻原点が曖昧 (`E − J` の期待値は 75 秒でなく約 70 秒)」
  「700 倍離れているので反復不要という主張は端数に左右される」
  「bnode013 ほか — 実際は 4 条件すべて bnode013」がある。すべて real として採った。
- **orphan hold を 1 件も残さずに終えた。** 投入前・各条件の間・投入後で `orphan-holds/` が
  0 件であることを確認し、`qdel` は 1 度も使っていない。probe は必ず自然終了する設計にし、
  walltime kill を終了手段にしていない。
- **実装面の差分は 0 である。** 計算ノード probe は先例 (2026-09-14 t1643 の insight §8) に従い
  Codex `role=author` が書き、実験に使った後 repo へ残さず job dir へ保全した。
  したがって新規 test file も受入所要台帳への追記も無く、変異 matrix は `DW-S04` により免除した。
  受入全走は免除していない。
- **段 5 を 1 回空費した。** 親が実在しない手本 file (`tools/t1643_has_include_pair_probe.py`) を
  射影したため、子が「読めなければ即停止」に従って 1 byte も書かずに戻った。
  **repo の `tools/` に probe file は 1 件も無く、同 path の git 履歴も 0 件である。**
- **実装子 worktree を 2 回作る羽目になった。** `git worktree add --detach` で作ったところ
  midflight gate が `NG: detached HEAD` で rc=1 になり、隔離 session は `git -C` で他 worktree へ
  git を向けられないため後から直せなかった。`-b <branch>` を付けて作り直した。
  未使用の `.codex/worktrees/t2622-impl` が 1 本残っている。
- 一次資料は `output/insights/2026-09-16/t2622-compute-job-exit-hang/` (逐語 8 本と 4 条件の
  生データつき)。job dir は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2622-compute-job-exit-hang/`。

## 次の一手差分

### 完了

- [T-2622] 原因同定を完了した。**子孫の出力 fd 保持は遅延の必要条件ではない**ことを
  4 条件の分離実験で確定し、F853 の機序記述へ supersede を入れた。残る未確定
  (判定方式・F853 当時の機序・対策) は下の新規項へ分けた。
  remaining: none
  base: 9e97d898f061bf5cfb9249a2921a7e2cefce692212e171c08244149184a1c191

### 新規

- {{T:job-exit-termination-criterion}} **P2・新規**: NQSV が request を RUN に留める判定方式が
  session か process group か scheduler の追跡集合かを分離する。[T-2622] の実験は全記録で
  `sid == pgid` だったため分離できていない。所属を変える条件 (`setsid` した子、
  process group だけ変えた子) を足した実験が要る。**対策の向きが変わるので、
  回収処理を設計する前に決める必要がある。**
- {{T:job-exit-delay-countermeasure}} **P2・新規**: 計算ノード job の終了遅延そのものへの対策。
  [T-2622] は原因同定だけで scope を切った。subreaper は採らない (F973)。
  {{T:job-exit-termination-criterion}} の結果が前提になる。
- {{T:dispatch-pre-run-deadline-contract}} **P3・新規・ユーザー裁定待ち**: 投入側 dispatcher の
  全体期限が RUN 観測前から `submitted + walltime + overall_grace` で動く契約の意味と、
  `fresh-qstat-gate` 後の遷移を含む取消の保証範囲。短い walltime を指定すると
  `--queue-wait-timeout` より先に `overall-timeout` が発火しうる。**受理集合と取消経路に
  触れるので親は裁定しない。**
