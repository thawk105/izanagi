[起動器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py) だけを修正しました。commit はしていません。**実装済み・計算ノードでは未実走**です。

`result["builds"]["v<v>"]` は build と照合の前に作り、失敗時も取得できた argv、Cache、`flags.make`、binary hash と `failure` を `result.json` に残します。build 失敗時の段 A、全 run「その他 (未実走)」、launcher rc=1 は維持しました。C 行は 7／10 field を受理し、どちらも `fields[6]` を数えます。run 起動例外ではその run の失敗を記録し、verifier と分類を行わず rc=1 で停止します。出力先の準備は preflight 内に移し、失敗時も両 JSON を個別に書き込むようにしました。

### 自己検査

`py_compile`、`git diff --check`、`check_codex_agents.py`、`check_docs.py` は成功しました。作業木外の合成入力では、**分類27例と追加4分岐の計31例がすべて期待値と一致**しました。

| 分類例 | 件数 | 期待値＝出力 |
|---|---:|---|
| A | 1 | その他 (未実走) |
| B1、B1-17 | 2 | 期待どおり (対照) |
| B2-timeout／rc／verify／empty、B4-max／integrity、C-control、D-control | 8 | その他 (対照不成立) |
| B3-I／N | 2 | 誤検出 |
| C1／C2／C3／C4／C5／C6／C7 | 7 | 順に「その他 (16 要素で停止 = 記録の境界どおり、source 読みの予測外)」「別の層で検出 (process の異常終了)」「その他 (帰属不明の異常終了)」「その他」「別の層で検出 (verifier)」「期待どおり (16 要素では S)」「その他 (条件未到達)」 |
| D1／D2／D3／D4／D5／D6／D7 | 7 | 順に「期待どおり (hang。verifier の判定は無く、止めたのは timeout = 盲点)」「別の層で検出 (process の異常終了)」「その他 (帰属不明の異常終了)」「その他」「別の層で検出 (verifier)」「未発生 (17 要素の取引が commit し S = 盲点の S)」「その他 (条件未到達)」 |

追加4分岐では、build 定義不一致でも記録と `failure` が残ること、7／10 field の C 行と不正 field 数、起動例外時の rc=1・verifier 0回・未分類、空でない out-dir での rc=2・両 JSON 保存を確認しました。

参照先の呼出契約は維持しています。`s5` の [`_require_condition_gate(source_root, macro)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/s5_permutation_coverage.py:77)、[`_run_cmake_build(cmd, *, site=None)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/s5_permutation_coverage.py:219)、[`_verify(trace_dir)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/s5_permutation_coverage.py:192) と同条件の verifier 呼出、[`_count_p_reasons(trace_dir)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/s5_permutation_coverage.py:144)、[`_oracle_cross_check(p_reasons, details)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/s5_permutation_coverage.py:159)、`_assert_single_tenant()`、[`assert_pinned_clean(sub, pin_commit)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/patchharness.py:174)、[`applied(patch_path, pin_commit, ccbench_dir)`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/patchharness.py:247) の呼び方は変更していません。

gate 通過の見込みも静的根拠のままです。`SORT_VARIANT` は [CMake cache 経路と Silo target](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/condition_meaning_gate.py:180)に登録され、[_configure_defines](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/condition_meaning_gate.py:1774) が `-DCCBENCH_SORT_VARIANT=<値>` を供給します。[_patch_changed_paths](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/condition_meaning_gate.py:2300) が変更 path を読み、[branch marker](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/orchestrator/campaign/condition_meaning_gate.py:331) は `#if SORT_VARIANT` です。admission 自体は未実走です。

## 総括

| 所見 | 状態 | 変更行 |
|---|---|---|
| 1 build 記録 | closed | [build_variant:180](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:180)、[main:431](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:431) |
| 2 C 行 7／10 field | closed | [trace_stats:293](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:293) |
| 3 run 起動例外 | closed | [run_trace:269](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:269)、[main:441](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:441) |
| 4 出力先準備と JSON | closed | [main:354](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:354)、[main:477](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:477) |
| 5 C 行形式の報告 | closed | 本報告で 7／10 field、`write_count=fields[6]` と訂正 |

prereg の段 A〜D は [`classify`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:119)、build と gate は [`build_variant`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:180) と `main`、W(16)／W(17)・120秒・R1→R4 は [`run_trace`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:269) と `main`、verifier は [`verify_once`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:316) に対応します。計算ノード上の依存物準備、gate、両 build、R1〜R4、verifier の実走結果は未確認です。