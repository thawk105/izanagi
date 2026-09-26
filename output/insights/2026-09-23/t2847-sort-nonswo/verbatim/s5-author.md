指定された [launch_sort_nonswo.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py) だけを作成しました。commit はしていません。計算ノードでの実走は**実装済み・未実走**です。

起動器は V07 patch を `s5.applied` で一度だけ適用し、その文脈内で gate と v=1／v=0 の 2 build を行います。実コンパイル定義を照合してから R1→R4 を実行し、timeout 時も C 行統計を参考値として保存します。timeout 以外は各 run につき verifier を 1 回呼び、生出力を `verifier/` に記録します。分類は [prereg.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/prereg.md) の段 A〜D の順序で `result.json` に記録します。

### 検査

`python3 -m py_compile`、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py` は成功しました。分類関数の合成観測検査は **27 件すべて期待値と一致**しました。下表の「同左」は出力が期待文字列と完全一致したことを示します。

| 例 | 期待 | 出力 |
|---|---|---|
| A | その他 (未実走) | 同左 |
| B1, B1-17 | 期待どおり (対照) | 同左 |
| B2-timeout, B2-rc, B2-verify, B2-empty | その他 (対照不成立) | 同左 |
| B3-I, B3-N | 誤検出 | 同左 |
| B4-max, B4-integrity | その他 (対照不成立) | 同左 |
| C-control | その他 (対照不成立) | 同左 |
| C1 | その他 (16 要素で停止 = 記録の境界どおり、source 読みの予測外) | 同左 |
| C2 | 別の層で検出 (process の異常終了) | 同左 |
| C3 | その他 (帰属不明の異常終了) | 同左 |
| C4 | その他 | 同左 |
| C5 | 別の層で検出 (verifier) | 同左 |
| C6 | 期待どおり (16 要素では S) | 同左 |
| C7 | その他 (条件未到達) | 同左 |
| D-control | その他 (対照不成立) | 同左 |
| D1 | 期待どおり (hang。verifier の判定は無く、止めたのは timeout = 盲点) | 同左 |
| D2 | 別の層で検出 (process の異常終了) | 同左 |
| D3 | その他 (帰属不明の異常終了) | 同左 |
| D4 | その他 | 同左 |
| D5 | 別の層で検出 (verifier) | 同左 |
| D6 | 未発生 (17 要素の取引が commit し S = 盲点の S) | 同左 |
| D7 | その他 (条件未到達) | 同左 |

### 参照先との照合

| 現行関数 | signature と挙動 | 起動器の対応 |
|---|---|---|
| [`_assert_single_tenant()`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/p2_2.py:300) | 競合プロセスがあれば拒否 | [preflight](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:368) で呼ぶ |
| [`assert_pinned_clean(sub, pin_commit)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/patchharness.py:174) | HEAD と pin、tracked clean を照合 | 同じ preflight で呼ぶ |
| [`applied(patch_path, pin_commit, ccbench_dir)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/patchharness.py:247) | 排他下で適用し、退出時に復元 | [gate と両 build](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:388) を一つの文脈に置く |
| [`_require_condition_gate(source_root, macro)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/s5_permutation_coverage.py:77) | supply・meaning・admission を返し、不 admitted なら例外 | `SORT_VARIANT` で呼び、返値を保存 |
| [`_run_cmake_build(cmd, *, site=None)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/s5_permutation_coverage.py:219) | site 拒否後、並列数を付けて build | [target build](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:180) に使用 |
| [`_verify(trace_dir)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/s5_permutation_coverage.py:192) | verifier の argv・cwd・300 秒 timeout を定義 | [verify_once](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:274) が同じ呼出条件で stdout の追加 field も一度に読む |
| [`_count_p_reasons(trace_dir)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/s5_permutation_coverage.py:144) | P 行を reason 別に集計 | verifier 要約へ保存 |
| [`_oracle_cross_check(p_reasons, details)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/s5_permutation_coverage.py:159) | raw P 集計と構造化 counts を突合 | verifier 要約へ保存 |

verifier の `results[0]` に `verdict`、`certified`、`stats`、`integrity`、`total_cycles` があることは [report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/verifier/report.py:96) で、rc の 0／1／3 対応は [cli.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/verifier/cli.py:11) で確認しました。C 行が **7 field** で最後が `write_count` なのは [parse.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/verifier/parse.py:4) に一致します。

gate がこの木で通る見込みは静的根拠に限ります。[DefineSpec](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/condition_meaning_gate.py:180) は `SORT_VARIANT` を CMake cache 経路、Silo owner、`ycsb_silo.exe` に結び、[_configure_defines](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/condition_meaning_gate.py:1774) は `-DCCBENCH_SORT_VARIANT=<値>` を供給します。[_patch_changed_paths](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/condition_meaning_gate.py:2300) が見る宣言 patch と V07 は `cc/silo/transaction.cc` と `cmake/Options.cmake` を共に変更し、宣言された [branch marker](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/condition_meaning_gate.py:331) `#if SORT_VARIANT` は [V07](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/patches/broken-silo-sort-nonswo.patch:25) にあります。実際の admission は未実走です。

## 総括

実装関数は `timestamp`、`exception_record`、`write_json`、`checked`、`cmake_literal`、`_stage`、`classify`、`build_variant`、`run_trace`、`trace_stats`、`verify_once`、`main`、および `Proxy`／`VerifierRecorder` の各メソッドです。

| prereg の規則・条件 | 実装箇所 |
|---|---|
| 段 A〜D の分類順序 | [`classify` 119 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:119) |
| gate、単一 patch 文脈、2 build | [`main` 388 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:388)、[`build_variant` 180 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:180) |
| W(16)／W(17)、120 秒、R1→R4 | [`run_trace` 227 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:227)、[`main` 394 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:394) |
| C 行統計、timeout prefix | [`trace_stats` 251 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:251) |
| verifier 1 回、integrity 数値 field | [`verify_once` 274 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:274) |
| result・meta・生出力 | [`main` 312 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:312)、[`VerifierRecorder` 62 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:62) |

未実走の範囲は、計算ノード上の依存物準備、gate admission、両 build、R1〜R4、verifier と実際の分類結果です。