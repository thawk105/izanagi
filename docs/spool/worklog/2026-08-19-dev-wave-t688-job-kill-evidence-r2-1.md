---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t688-job-kill-evidence-r2
seq: 1
title: 床値 job の kill 証拠を repo 外へ残して事後診断へ接続した — 塞ごうとした signal 経路は最初から死んでいた (コード + テスト + 記録、branch worktree-dev-wave-t688-job-kill-evidence-r2、変異 matrix = baseline PASSED・10/10 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 着手前の実測で、2026-08-12 の裁定文の前提の一部は既に満たされていた。driver は fsync 付き
  append-only の `journal.jsonl` を持ち `session-start` を計測直前に書くため、**計測相の
  「落ちた構成」は既に特定できていた**。残る穴は driver 起動前の相 (見積り約 900 秒) と、
  PBS job id から証拠へ辿る索引の 2 つだけであった。scope をこの 2 つへ狭めた。
- 親の当初の主張のうち 1 件を自分で撤回した。「起動前 rc=16 の診断ゼロは実測で反証済み」は
  標本が不適切だった — `output/pegasus-dispatch` の 58 receipt は正常完了 56・親 SIGTERM 2 で、
  node 側 kill を 1 件も含まない。正しくは「親が観測する pre-start 失敗はコード構造上被覆済み、
  node 側 kill は未実測」である。
- **最大の発見は、塞ごうとした診断経路の 1 本が最初から到達不能だったことである。** NQSV は既定で
  `Accept Sigterm = No` であり SIGTERM が job script へ配送されない。この状態は PBS job から
  pytest、xdist worker、subprocess、`bash -c` まで継承される。したがって床値 job の signal trap は
  一度も発火しえず、`signalled` の診断は原理的に記録され得なかった。checkpoint を足すだけでは
  この経路は永久に死んだままだった。詳細は {{F:floor-signal-trap-unreachable}}、
  採った対処と主張の限界は {{D:floor-job-accept-sigterm}}。
- この欠陥は環境をまたいで測ったから見つかった。同一 commit に対しログインノードでは
  168 tests / 0 failures、計算ノードでは 1 failed / 132 passed であった。ログインノードだけで
  判定していれば緑に見え、受入全走で初めて落ちていた。
- 段 3 敵対相談は 26 件 (real 17 / uncertain 5 / refuted 4)、段 6 敵対レビューは 23 件
  (real 17 / refuted 7)。段 6 で refuted された攻撃には、診断用環境変数の実測 process への漏れ
  (絶対規律 1)、権威 journal の strict 性の緩み (絶対規律 2)、W1 が `fsynced` を騙ること
  (絶対規律 3)、変異 V1-V10 に対応する赤 test の不在が含まれる。これらは実装が持ちこたえた。
- fix は 5 巡を要した。1-3 巡目はレビュー所見と自己回帰、4-5 巡目は親の実測で新たに出た赤
  (計算ノード限定の signal 赤と、PBS ディレクティブ検査の逐語不整合) である。
  2 巡目は自分の新設テスト 7 件を落とす回帰を出し、3 巡目で dirfd walker が directory を
  作らない production バグとして閉じた。
- 段 6 レビューが「既存の検査が恒真になっている」を 1 件検出した。short write の fault 注入 fake が
  bytes を一切書かずに長さだけ返しており、「既存 evidence bytes 不変」の assertion が常に真だった。
  実際に `os.write(payload[:-1])` する fake へ差し替えて実効化した。
- 変異 matrix は本走前に 1 度空振りした。`--runner-mode local` では dispatch の成功時 relay が
  出力を切り、collection が 133 件中 34 件しか見えず、期待 node 16 件が「実在しない」と誤判定された。
  `--runner-mode dispatch` + runner argv の `--force-dispatch` へ組み直して本走した。
- 待ち手の運用で 1 度失敗した。焦点走の完了通知が届かず約 9 時間空転した。以後は通知任せにせず
  完了ファイルの実在で裏取りする見張りを併用した。
- codex 子の即死を「資源枯渇で fail-closed 停止」と早計に断定し、worktree まで畳んだ。実際には
  一過性で 8 分後に回復していた。並行 2 セッションの独立観測により、同時刻の即死には
  usage limit 型と `401 Unauthorized` 型の 2 症状があり、外形 (rc=1・model_calls 0・log 0 byte) では
  区別できず、いずれも自然回復すると判明した。

## 次の一手差分

### 完了

- [T-688] job wrapper 側に durable checkpoint と partial-log path を作り、driver 起動前の相と
  job id → 証拠の索引を塞いだ。書き込み先はすべて repo 外で、`output/` へ untracked を足さない。
  partial-log は診断専用であり計測値の権威にしない。
  remaining: none
  base: 0668d5dab59cd90efc80e18bff3e97d06249a7d5d29459d6393df27d42f683f4

### 新規

- {{T:dispatch-node-kill-evidence}} **P3・新規**: dev harness の `dispatch_compute.py` について、
  node 側 SIGKILL と親自身の SIGKILL で診断が残るかは**未実測**である。親が観測する
  pre-start 失敗はコード構造上被覆済みだが、node 側 kill の被覆は測っていない。床値計測より
  価値が低いと判断して T-688 の scope から外したので、独立に裁定する。
- {{T:floor-phase-marker-completion}} **P3・新規**: driver の phase marker (preflight / oracle /
  build) は開始のみで完了記録が無く、in-flight と完了済みを区別できない。再走単位は journal で
  決まるため certified 値も受理集合も変わらない。外部 checkpoint の consumer が成立した今、
  別 wave で扱えるかを裁定する。
- {{T:floor-liveness-stageout-race}} **P3・新規**: `floor_liveness` は qstat が absent / END に
  なった時点で終端証拠を 1 度だけ読むため、PBS の stage-out 完了前だと証拠を見落とす。
  本 wave 以前から在る欠陥で、新設 checkpoint は stage-out に依存しないため依存自体は減った。
- {{T:floor-walltime-signal-measurement}} **P2・新規**: `--accept-sigterm=yes` だけでは
  walltime 打ち切りで SIGTERM が送られる保証にならない。{{D:floor-job-accept-sigterm}} と
  既裁定に従い、`elapstim_req="max,warn"` と `--warning-signal=elapstim:SIGTERM` を含む構成の
  実測を行うかを裁定する。実測するまで walltime 被覆を主張しない。
