---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t189-stage2-plan-replayer
seq: 1
---

## 新規

### {{F:stage2-launch-test-representativeness-gap}}. T-181/T-1434の既存test群がreal codex execの実ネットワーク経路を一度も検証していなかった [テスト代表性]

- 事象: T-189 stage2-plan-replayer実装のsmoke gate (DW-G01) で、`tools/codex_reasoning_ab.py`
  既存の`_bwrap_exec_argv`経由でreal codex execを試みたところ、実ネットワーク到達不可
  (120秒timeout・exit -15・output 0 bytes、stderr: code-mode host未配置)で失敗した。
- 根本原因: `_supervise_one`が使う`environment`辞書 (`_clean_environment`の
  `ENV_ALLOWLIST = {CODEX_HOME, HOME, LANG, LC_ALL, PATH, TERM, TZ}`のみ) は、
  `dry_run=True`(直接Popen、bwrap非経由)でも`dry_run=False`(bwrap経由)でも同じ縮小dictを
  使う。T-1434の既存test (292+ passed) はdry_run=Trueかつfake codex binaryのみを使っており、
  「real codex binaryを実ネットワーク接続込みで、この縮小環境の下で起動する」という
  production相当の経路を一度も実測していなかった。292+ passedという緑の実績は、
  bwrap/env-strip層の実ネットワーク到達性については無関係 (代表性を持たない)。
- 恒久対応: 本waveの新規機構 (stage2-plan-replayer) は同じ罠を踏まず、ambient env継承+HOME
  上書き+auth/configコピーという実証済みrecipeを使う ({{D:stage2-direct-launch-recipe}})。
  この選択の理由と根本原因は`tools/codex_reasoning_ab.py`のdownstream起動コード付近の
  docstring/コメントに残した。既存の`_bwrap_exec_argv`自体・T-181由来の既存test群の
  代表性ギャップは本waveでは修正していない (規律5、apparatus全体に及ぶ横断的変更のため
  scope外、{{T:t189-stage5-author-replayer}}以降の実験実施waveが引き継ぐべき前提条件として
  {{D:stage2-direct-launch-recipe}}に明記)。
- 再発検知: 新規サブプロセス起動機構をこのapparatus上に構築するwaveは、DW-G01の生死確認を
  `dry_run=True`やfake binaryだけで済ませず、実binary・実認証・実ネットワークでの
  smoke testを要求する (段4裁定のF8/F13相当の扱いを一般化)。機械lint化は未実装 — 次に
  同型の罠を踏んだ wave が出たら、DW-G01の記述へ「fake/dry_run実績だけでは生死確認済みと
  扱わない」旨を明文化する候補とする。
