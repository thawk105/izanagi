## 対応表

| 所見 | 判定 (closed / partial / regressed) | 根拠 file:line |
|---|---|---|
| D1 | closed | 3箇所すべてが `git status` の終了値を明示検査し、失敗時に `refuse` する。superproject は `tools/pegasus/p3_s4_loop_pegasus.sh:175-180`、CCBench は同`:208-212`、third-party source は同`:339-344`。負例 stub は expected HEAD と同じ40桁値を返して HEAD gate を通過し、status では空 stdout・rc=1を返す `orchestrator/tests/test_p3_s4_loop_job_contract.py:756-772`。rc=2、status marker 到達、後段 sentinel 未到達を同`:817-826`で固定している。 |
| D2 | closed | `GIT_*` の unset 後、最初の Git 呼出しより前に `GIT_OPTIONAL_LOCKS=0` を export している `tools/pegasus/p3_s4_loop_pegasus.sh:41-48,75`。exact fragment も `orchestrator/tests/test_p3_s4_loop_job_contract.py:173-178`で固定される。 |
| D4 | closed | host gate は bnode を受理し `tools/pegasus/p3_s4_loop_pegasus.sh:26-29`、worktree 拒否は git common-dir 解決より前にある同`:70-76`。harness は `bnode001` を返す同 test`:841-847`、worktree path を入力して gate 固有文言・rc=2・artifactなしを確認する同`:859-886`。PATH sanitize 後は sentinel stub 自体が PATH 外になるが、gate 固有文言と静的順序が拒否本体への実到達を固定しており、拒否削除 mutant は通らない。 |
| D5 | closed | 正規化式とその利用が `tools/pegasus/p3_s4_loop_pegasus.sh:214-221`にあり、exact fragment は test`:224-225`。raw `PBS_JOBID` へ置換する mutant は test`:450-464`で `qstat-jobid` 欠落として拒否される。 |
| D6 | closed | `_shell_executable_surface` は heredoc 本文と全行 comment を除去する test`:45-70`。順序 marker はこの surface 上で各出現数を1に限定し、順序も検査する同`:338-362`。元位置を comment 化して実 trap を後置する前置複製負例は同`:369-378`で拒否される。 |
| D7 | closed | fragment mutant の前提は重複だけを拒否する `count <= 1` となり、欠落検出を helper の正確な例外へ委ねている test`:456-464`。これにより production 変異時の前提由来の二重赤を避ける。M5 は production と実 mutant の代入行を executable surface から抽出し、両方を bash で評価して colon 残存を検出する同`:641-670`。 |

## 回帰

なし。production 差分は optional lock の固定と3 clean gate の fail-closed 化だけで、受理集合を拡大していない。`count <= 1` も恒真化ではなく、base static contract と exact error 検査を組み合わせて欠落・重複・helper 緩和を引き続き検出する。test double に合わせた production 緩和もない。

## 判定

GO。

## 総括

D1・D2・D4・D5・D6・D7 はすべて root cause を閉じている。
指定された負例は静的に、それぞれ対象 gate または実 mutant へ到達する構成である。
fix 差分から受理集合の拡大、既存契約の弱体化、恒真化は認めなかった。
本再レビューでは制約どおり pytest を実行しておらず、判定は静的検査に基づく。