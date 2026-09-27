## 総括

- **must-fix:** plan は TPC-C の workload を `measure_point` まで渡すとしているが、通常 bench の中継点 `_PreparedEvaluation` に保持する手順がない。このままでは v3 trace が検証を通った後、TPC-C perf run に YCSB flag が渡る。
- **must-fix:** 現 pin の v2 trace は `pipeline.evaluate` で bench 前に拒否される。生死確認には、計算ノードで TPC-C perf binary を使う `measure_point` の直接 1 回実行を加える必要がある。
- brief と plan の「`cell.flags` は int」は誤り。実コードは `_cell` で全値を文字列化している。
- 認定の核は、57:43 の trace 受理、witness、verifier 後の v3 判定、`vr.certified` をすべて通すこと。`ccbench_root` には **trace binary を作った CCBench source root** が要る。
- 静的検査では、これらの gate を維持する限り v2・witness 欠落・anomaly が certified に届く新経路は見つからない。テストと実機測定は行っていない。

## 所見

**A1 — must-fix｜通常 bench への workload 伝播が未完。** [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:1258) の `_PreparedEvaluation` に workload がなく、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:2836) の `_bench_prepared` は保存済み値だけで `_run_bench` を呼ぶ。`_run_bench` 内の二つの `measure_point` 呼び出しは [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:1442) にある。**放置時:** v3 認定後の TPC-C perf run が既定 YCSB argv になり、評価値または WAL が得られない。**修正:** workload を `_PreparedEvaluation` に保存し、通常 bench と screening 側の呼び出し（[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:2681)）の双方から `_run_bench` へ通す。

**A2 — must-fix｜bench 生死確認が計画から抜ける。** [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:702) は verifier 直後に TPC-C v2 を拒否し、`evaluate` は prepare が abort を返せば [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:3177) で終了する。**放置時:** TPC-C bench の argv と parser が未実測のまま「評価可能」と報告される。**修正:** 計算ノードの同じ driver から perf binary に対して `measure_point(..., workload_name="tpcc")` を直接 1 回呼び、argv、rc、TPS を保存する。実行器の `run_job` は別途 [t2851_transfer_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/t2851_transfer_runner.py:431) で `run_once` の `throughput[tps]` も通せる。出力側には [result.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/external/ccbench/common/result.cc:52)、parser 側には [benchparse.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/calibrator/benchparse.py:22) の対応があるが、実機成立は未確認。

**A3 — should｜`records` の意味を二義化する。** [runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/calibrator/runner.py:1085) の `records` と [PerfConfig](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:187) は YCSB 件数として既存の測定値に残る。plan の TPC-C 案では同じ値を倉庫数にする。**放置時:** レポートや台帳の `records=1` を YCSB 件数と読めてしまい、測定条件の参照が曖昧になる。**修正:** YCSB の既存形は保ち、TPC-C 用には名前付きの `tpcc_num_wh` を受ける別入口、または workload ごとに明示した測定条件を使う。`-tpcc_num_wh` と `-ycsb_tuple_num` の二重指定も拒否する。

**A4 — should｜probe の可視性は未証明。** [t2851_transfer_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/t2851_transfer_runner.py:342) は YCSB canary の後、TPC-C だけ `pgrep -af` の rc=1 と空 stdout を「不在」と読む。YCSB canary は TPC-C 実行プロセスの可視性を直接は示さない。**放置時:** TPC-C 競合を見逃せば採用する性能値が汚染される。**修正:** driver の argv に一致パターンを含めず、既知の TPC-C PID が見える状態で False、終了後 True を実測し、rc・stdout・PID を記録する。可視性が確認できなければ `pgrep` の空結果を合格にしない。

**A5 — should｜正例 test は実 verifier と source root を通す必要がある。** 実行器は [t2851_transfer_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/t2851_transfer_runner.py:525) で凍結した `trace_ccbench_root` を渡す。verifier は [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/verifier/core.py:54) でその root の compiled source から proof surface を評価する。`vr.certified` は [model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/verifier/model.py:570) の integrity clean を含む。X/P は認定条件で、I は記録面である（[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/verifier/model.py:77)）。**放置時:** fixture が `certified=True` を返すだけの正例では、source root の欠落で実結果が indeterminate になる欠陥を検出できない。**修正:** 合成 v3 trace を実 verifier に通し、正しい trace binary の source root では certified、root 欠落・不読では indeterminate を検査する。

**A6 — should｜YCSB bytes 不変と v2 hit を差分全体で固定する。** legacy key は [buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/buildcache.py:640)、v2 preimage は [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/buildcache.py:1323) にある。plan の「TPC-C の場合だけ追加」は妥当。ただし v2 hit は binary relpath と compiler target を別々に受ける（[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/buildcache.py:2729)）。**放置時:** 同 genome の異 workload が誤 hit するか、YCSB の cache 名・manifest・受領証参照が変わる。**修正:** target を一度決め、fresh/hit/再現コマンドの全呼び手へ渡す。YCSB の key、bdir、v2 preimage、manifest、argv、WAL/受領証の既存 golden bytes と、YCSB↔TPC-C 相互 hit 拒否を検査する。既定引数を使う p3・s8b の既存呼び手は YCSB のまま維持できる。

## brief と plan の誤り

- `cell.flags` は int ではない。[t2851_transfer_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/t2851_transfer_runner.py:48) の `_cell` が全値を `str` にする。TPC-C だけ文字列化する修正は不要で、この前提を使う試験も修正すべき。
- brief の P1 は plan 冒頭で訂正されている。現 pin の `evaluate` で確認できるのは build、trace、v2 reject の WAL までであり、bench 到達ではない。
- `vr.certified` が要求する proof surface は X/P の二面である。I は三面レポートに載るが認定 gate には入らない。`ccbench_root` は存在する任意の repo root では足りず、trace binary を作った protocol source の root が必要。
- [事前登録 §3.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/docs/tpcc-unseen-condition-transfer-preregistration.md:198) は留保 cell の解禁に、段ごとの認定経路が **local main** にあることを要求する。今回の s1 配線と錨 smoke だけで留保 cell を解禁したとは記録できない。現行 activation は段と `certification_path` の記録を要求する（[t2851_transfer_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/t2851_transfer_runner.py:268)）。解析器は status 語を使うが reason 語には依存しない（[t2851_transfer_analysis.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/t2851_transfer_analysis.py:110)）。

## 変異案

| ID | 変異内容 | 殺すべき test |
|---|---|---|
| M1 | `_PreparedEvaluation` から workload を落とす | 実 `_bench_prepared` 経由で TPC-C argv に `-tpcc_num_wh` があり、`-ycsb_tuple_num` がない正例 |
| M2 | v2 判定を外す、または verifier 前へ移す | 実 verifier に通した v2 は indeterminate、v3 正例のみ certified |
| M3 | witness 欠落・batch commit 非ゼロでも verifier へ進める | `_trace_witness_ok` の各条件を一つずつ壊し、認定不能を確認 |
| M4 | `ccbench_root` を省略・perf 側の別 root にする | 合成 v3 trace と実 verifier で proof surface 不在が certified にならない試験 |
| M5 | v2 hit の compiler target だけ YCSB 固定に戻す | TPC-C fresh→hit の manifest 再検証と YCSB↔TPC-C 相互 hit 拒否 |
| M6 | s1 の比率判定を緩め、s2 または非 57:43 を通す | 実行器から `_run_trace` まで通す境界試験。`043`、欠落、s2 を含める |
| M7 | anomaly がある v2 を indeterminate にする | v2 の非直列化・anomaly は disqualified が優先される試験 |

合成 verifier を `certified=True` に差し替えるだけの正例は M2・M4 を殺せない。実 verifier を使う正例と、現 pin での実測拒否を分けて記録するのが必要です。