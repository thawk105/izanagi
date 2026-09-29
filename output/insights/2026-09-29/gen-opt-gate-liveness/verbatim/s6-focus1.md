## 所見ごとの対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| F1 | closed | fix job の CI build は両 workload の走行・判定後にあり、失敗を記録して次の build へ進む。[起動器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix1-out/launch_gate_liveness.py:260) |
| F2 | closed | CI 用 configure は genome define と `CCBENCH_TRACE` を渡さず、全 target を build する。compiler・依存物供給などの差も記録する。[起動器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix1-out/launch_gate_liveness.py:64)、[上流 build.yml](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-gen-opt-gate-liveness/external/ccbench/.github/workflows/build.yml:68) |
| F3 | partial | `prereg` と終了値を実装した。fix の D2b `not-exercised` は、対応条件が未発生なら許す事前登録と整合し、B1 committed と D1(b1) 件数の一致も診断に留める。JSON の `results[0]`・`verdict`・`certified`・`stats.txns` は実際の出力と一致。ただし既存判定器の非 0 判定を一律に「失敗」扱いし、診断として記録すべき verdict でも中断する。[起動器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix1-out/launch_gate_liveness.py:88)、[判定器 CLI](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-gen-opt-gate-liveness/orchestrator/verifier/cli.py:84)、[事前登録](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/s4-ruling.md:69) |
| F4 | closed | D2b(ii) は書きのある取引で発生扱いとなり、複数回書きの件数は別に残る。[照合器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix1-out/gate_check.py:175) |
| F5 | refuted-confirmed | 親の裁定が正しい。`<vector>` の追加位置は pin の `#if TRACE` 内。[計装 patch](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix1-out/patches/instr-silo-gate-witness.patch:4)、[pin の trace.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-gen-opt-gate-liveness/external/ccbench/include/trace.hh:25) |
| F6 | closed | test 名を正例に改め、`--repo-root` を追加した。abort 非混入を test 済みとする主張は外れた。[自走 test](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix1-out/test_gate_check.py:46) |
| F7 | partial | build 所要は記録するが、予算内の見積りはこの成果物にない。なお前回の「依存物準備が全体 build」という内訳は誤りで、その build の target は `ycsb_silo.exe`。[起動器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix1-out/launch_gate_liveness.py:75)、[依存物準備](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-gen-opt-gate-liveness/orchestrator/campaign/silo_policy_coverage.py:392) |
| F8 | closed | tar.gz の sha256 を結果に格納してから削除する。削除失敗時も例外処理が `result.json` を保存する。[起動器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix1-out/launch_gate_liveness.py:237) |
| F9 | closed | 計装と照合器は `V`・`Q` で一致。指定された判定器および CCBench の trace・witness 出力に同 tag の既存使用は見つからない。[計装 patch](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix1-out/patches/instr-silo-gate-witness.patch:38)、[照合器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix1-out/gate_check.py:41) |

## 新しい所見

**N1 — must-fix — [起動器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix1-out/launch_gate_liveness.py:254)。** 既存判定器は `non-serializable` に rc=1、`indeterminate` に rc=3 を返すが、起動器は JSON を保存した後、どちらも実行失敗として中断する。[判定器 CLI](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-gen-opt-gate-liveness/orchestrator/verifier/cli.py:105) B1 の verdict は「記録だけ」、stock の verdict も診断という事前登録に反し、**(a)(b) の後続 workload と判定が欠け、(d) でも到達可能な prereg 不一致を rc=4 でなく rc=1 と読む**可能性がある。**推奨:** JSON が正常で意味のある判定 rc（0・1・3）は verdict として扱い、両 workload の記録と `prereg` 評価を続ける。JSON 不正・起動失敗だけを rc=1 の実行失敗にする。

## 総括

**NO-GO。** 投入済み stock job の結果は保存して確認できるが、B1 job と修正 job は N1 を直してから投入する。今回の確認は静的点検であり、計算ノードの実走結果はまだ確認していない。