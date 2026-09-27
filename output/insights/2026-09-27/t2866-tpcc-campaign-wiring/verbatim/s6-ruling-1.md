# 段 6 裁定 1 (2026-09-27 JST、親)

入力: 焦点走 focus-1 (HEAD 2bb35c7a4、12 failed / 2753 passed / 5 skipped、log `/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/focus-1.log`)、review A (`codex/s6-review-a.md`、NO-GO)、review B (`codex/s6-review-b.md`、NO-GO)。

| ID | 裁定 | fix 先 | 根拠・放置時の影響 |
|---|---|---|---|
| F1 (焦点走、親) | real must-fix | 単位 B | `pipeline.py:2735` の `for tag, workload, fullscale_isolated in passes:` が引数 `workload` (ycsb / tpcc) を CorrectnessWorkload で上書きし、`:2812` の `_PreparedEvaluation(workload=workload)` と以後の bench が `workload_name=CorrectnessWorkload(...)` を受けて ValueError (`test_tpcc_evaluate_v3_reaches_bench_with_workload` の赤)。放置時は v3 を通った TPC-C 候補も bench で abort し fitness が取れない。修正: 関数入口で bench / build 用の値を別名に確保し、build (`:2105-2114`)、screening (`:2697`)、`_PreparedEvaluation` (`:2812`) はその別名を使う。反復変数の名前は既存コードのまま触らなくてよい。 |
| RA1 | real must-fix | 単位 B | `test_campaign.py:13734` の `_balanced_prepared_fixture` が `_PreparedEvaluation` を直接作り必須 field `workload` を渡さない (焦点走の 11 件の赤)。修正: fixture に `workload="ycsb"` を足す (期待値は変えない)。 |
| RA2 / RB1 | real must-fix | 単位 D (driver) | driver が evaluate 段を省略。段 4 plan v2 の要求。修正: 既存の evaluate 呼び出し (`orchestrator/campaign/s1_direct_comparison.py:1230-1300` 付近、`test_campaign.py` の evaluate test の layout・lock・capability 準備) を雛形に、repo 外の独立 layout で R1 を 1 件 `evaluate(..., workload="tpcc", correctness=<s1-H-base の flag 一式>)`。期待 = WAL に `trace-witness-unsupported-workload` の reject、bench 未起動。**repo のコードを足してはならない。** 使い捨て driver の範囲で閉じないなら、閉じない部品を file:line で報告し、evaluate 以外の段は従来どおり走る形を保つ。 |
| RA3 | real must-fix | 単位 D | `trace_ccbench_root` が `checkout` の一時 worktree を指し、終了時に消える。修正: source root の pin (commit) と tree の digest (または `git -C <root> rev-parse HEAD` と `git status --porcelain` の空) を freeze と別に記録し、verify は checkout が生きている間に行う (現状どおり with 内)。再検証用の再取得手順 (pin からの checkout) を記録に書く。 |
| RA4 / RB2 | real must-fix | 単位 D | driver が結果を検査せず rc=0 で終わる。修正: 各 JSON を保存した後、期待 (job: completed_blocks=32・isolation_start/end=true・next_action="none"、verify: status が "certified" でない (現 pin は v2。witness・件数照合で先に未確定になる場合や、v2 の key で verifier が cycle を出し失格になる場合もありうるので、status と reason は記録し、certified だけを不一致とする)、bench: rc=0・tps>0 の有限値、probe: 下の RA5、evaluate: COMMIT されず abort し bench が起動していない (reason は記録)) と違えば、どれが違ったかを summary.json に書いて非 0 終了。期待と違う結果も記録は残す (create-only)。 |
| RA5 | real should → 採用 | 単位 D | `_probe("tpcc")` の False は composite probe 自体の失敗でも成立する。修正: 同じ時点で `calibrator.composite_competing_probe` を単独で呼び status="passed" を記録し、かつ tpcc 実行中の `_probe("tpcc")`=False・終了後 True・pgrep に既知 PID が出る、を全て満たすときだけ demonstrated=true。 |
| RB3 | real (縮小) | 不採用 | 不正 workload の拒否 test の重複は受理集合・成果物に影響しない (DW-G05)。 |
| RB4 | 維持 | — | TPC-C 限定の workload 記録は維持。 |

fix の規模上限: 単位 B は production 10 行以内・test 10 行以内、driver は 150 行以内の追加。既存テストの期待値を変更しない (反転・緩和・skip・削除の禁止)。赤なら実装側が誤り。期待値が誤りと考えるなら実装を変えず報告して止める。
