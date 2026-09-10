12+2 の両系統を実装上は `closed` にしました。実走検証のみ infrastructure failure のため `partial`、確認済みの regression はありません。

- 12-node 系統: historical epoch を旧5-key／marker付き6-keyの exact 2集合として受理。旧 report の比較時は fresh 側 marker のみ互換投影から除外し、新 report は marker まで比較します。
- 2-node 系統: backoff の historical test double に production と同じ exact marker property を追加しました。TPS除外・NaN IPC期待は不変です。

受理の含意: marker 無しの旧 historical v3、exact marker 付きの新 historical report、marker 無しの現行 certifying reportを受理します。

拒否の含意: marker 改竄、余分な epoch key、marker 付き `certifying_input=true` は拒否し、unknown keyや certified の受理集合を広げません。

編集 path は次の3件だけで、fix4 として unstaged です。

- [autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/campaign/autonomous_trial_completeness.py:87)
- [test_autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/tests/test_autonomous_trial_completeness.py:4675)
- [test_backoff_consumers.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/tests/test_backoff_consumers.py:36)

正例として旧5-key historical、新6-key historicalを固定し、marker改竄・余分key・certifying markerの負例を追加しました。既存 staged 統合差分は維持し、stage/commit操作はしていません。

実走結果:

- 受入14 node＋新規5 node: wrapper rc=16、`child_started=false`
- 関連4 file全体: wrapper rc=16、`child_started=false`
- backoff file単独および新marker正例単独の再試行: wrapper rc=16、`child_started=false`
- 原因: `qstat -Q preflight rc=1`、NQS socket作成失敗
- 実際に開始した nodeid: なし。したがって緑とは報告しません。
- `git diff --check`: rc=0
- 3編集pathのsyntax compile: rc=0
- 未実走: 上記14+5 node、関連4 file全体、受入全走

波及は historical marker consumer の互換投影とtest fixtureに限定されます。admission decision、campaign/WAL/performance比較、`generated_from_head`、reason enum、purpose、view型、certified schema分離、tracked output/frozen bytesは変更していません。

## 総括

12-node consumer取り残しと2-node fixture欠落はコード上 `closed`、実走検証は環境制約により `partial` です。fix4だけが指定3 pathにunstagedで残り、既存staged統合差分はそのままです。
