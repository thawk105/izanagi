修正は所有範囲内で完了しました。ただし Pegasus の実行基盤制約により pytest は実走できていません。

## 総括

`partial` はすべて「実装済み・pytest 未実走」を意味します。

| 所見 | 状態 | 対応 |
|---|---|---|
| F-1 | partial | 非ゼロ浮動小数・char・string を含む、単一 token で真と確定する core literal を検出。指定 3 形を scanner／seam 負制御へ追加 |
| F-2 | partial | 256 KiB／4096 token 上限を fail-closed で追加。括弧対応を一度だけ計算する線形処理へ変更 |
| F-3 | partial | critic の affirmative security claim を撤回。allowlist 済み `rule_id`・`category`・件数を独立フィールドで WAL→loader→render へ結線 |
| F-4 | partial | sort／trigger の実 `_quarantine_and_audit` に事後矛盾 auditor を入力する behavioral kill を追加 |
| F-5 | partial | materialized marker hole を再抽出し、harness のインデントだけ逆変換して scanner 入力と byte-exact 比較 |
| F-6 | partial | AST meta-test を `textwrap.dedent` に変更し、behavioral test を別途追加 |
| F-7 | partial | 固定化された候補由来例外を S6 の `error`・ログ・永続 provenance JSON まで通す sentinel 非反射テストを追加。本体変更なし |
| F-8 | partial | 指定された scope 外・未閉鎖層を [coder_effect_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py) の module docstring に全件列挙 |
| F-9 | partial | module invariant の `assert` 3 件を明示的な `RuntimeError` へ変更 |

実走結果:

- 実行済み nodeid: なし。
- `tools/run_tests.py` へ以下を投入しましたが、いずれもテスト開始前に `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`、rc=16 で停止しました。

  - `orchestrator/tests/test_coder_effect_gate.py` 全体
  - byte-exact binding、critic 構造化、AST 配線、両 driver behavioral kill の各 nodeid
  - S6 provenance 非反射 nodeid

- user-slice のローカル余裕も最小 1 GiB 未満でした。
- 静的検査は成功:

  - 所有 12 ファイルの `python3 -m py_compile`
  - `python3 -O` での gate import
  - `git diff --check`
  - 指定所有範囲外の変更なし

波及可能性:

- 所有外 caller: `p3_autonomous_workload_trial.py`、`s1_direct_comparison.py`、`s1_verify_extime_calibration.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`
- 共有 consumer: sort/trigger driver、critic loader/render、autonomous workload の rejection projection
- 所有外 consumer test／fixture: `test_p3_s4_loop_trigger_gating.py`、`test_critic.py`、`test_p3_autonomous_workload_trial.py`、`test_s8a_trigger_sweep.py`、`test_s1_direct_comparison.py`、`test_p3_exploration_namespace.py`
- 新フィールドは既定値付きのため既存 keyword constructor との互換性を維持しています。

残余・未実装:

- 親環境で焦点 node、関連ファイル全体、mutation matrix、受入全走の再実走が必要です。
- docs 編集・commit は指示どおり行っていません。
- F-8 に列挙した `p3_s4_red.py`、手動 patch、直接 buildcache/CMake、shell materializer、cache/WAL/COMMIT/freeze 非束縛等は意図的に未閉鎖です。