---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t1488-rr80-rr20-calibration
seq: 3
---

## 新規

### {{F:certify-python-interpreter-unpinned}}. certify_calibration.shが裸のpython3を呼びholdout importの3.10構文で計算ノードのpython3.9下で失敗する [ドリフト]

- 事象: rr80 calibration投入 (933127.nqsv、bnode001) で
  `TypeError: dataclass() got an unexpected keyword argument 'slots'`。
  `orchestrator/calibrate.py` → `calibrator/cli.py` → `calibrator/runner.py` →
  `orchestrator/holdout_observation.py` (T-523) の`@dataclass(frozen=True, slots=True)`
  (Python 3.10+構文) のimportで発生した。
- 根本原因: `tools/pegasus/certify_calibration.sh`が計算ノードのpython3バージョンを固定
  しておらず、`docs/pegasus-runbook.md` §3が警告する既知のノード依存 (intelpythonが
  PATH前方に来て3.9に解決される) を踏んだ。decisions.mdの[T-272]backlogが指摘していた
  「certify経路には版数gateが無く、floor_campaign.shだけが持つ非対称が残る」の実例。
- 恒久対応: `tools/pegasus/dispatch_compute.py`と同型の`_INTERPRETER_CANDIDATES`解決
  (python3.10 → /usr/bin/python3.10 → /bin/python3.10の順にsmoke checkして採用) と
  fail-closed拒否を`certify_calibration.sh`に追加した。
- 再発検知: `orchestrator/tests/test_pegasus_tools.py`の
  `test_certify_calibrator_resolves_and_shims_versioned_interpreter`、
  `test_certify_calibrator_interpreter_resolution_fails_closed`。

### {{F:certify-interpreter-fix-breaks-perf-path}}. python3.10 interpreter修正がperf選定PATHの優先順位を壊す回帰を生んだ [手順漏れ]

- 事象: 上記{{F:certify-python-interpreter-unpinned}}の修正を適用した直後、rr80再投入
  (935547.nqsv、bnode003) で`ccbench failed. rc=2 stderr=WARNING: perf not found for
  kernel 5.15.0-173`。
- 根本原因: interpreter解決で追加した`CALIBRATE_PATH="$(dirname "$CALIBRATE_PYTHON"):
  $CALIBRATE_PATH"`が、既存のperf選定シンボリックリンク (`$TMPDIR/bin/perf`、
  `certify_calibration.sh:729-731`) より**前**にpython3.10のdirname (`/bin`) をPATHへ
  挿入してしまい、Ubuntu標準の`/bin/perf`ラッパー (kernel version不一致を検出して警告
  終了する) が選定済みperfより優先されるようになっていた。fix作成時に既存のPATH構築との
  相互作用を検証していなかった。
- 恒久対応: `CALIBRATE_PATH="$TMPDIR/bin:$(dirname "$CALIBRATE_PYTHON"):$PATH"`に順序を
  修正し、`$TMPDIR/bin`(perf選定) を最優先に戻した。
- 再発検知: `orchestrator/tests/test_pegasus_tools.py`のPATH順序期待値検査
  (`test_certify_calibrator_resolves_and_shims_versioned_interpreter`内)。実機再投入で
  実証。

### {{F:holdout-capability-early-stop-overreject}}. holdout capability機構がsweepの正当なearly-stopを未消費と誤検出した [手順漏れ]

- 事象: 段6敵対レビューが指摘した「未消費sweepでnoise遷移可能」(reviewB所見2) への
  fixを適用後、rr80再投入 (935759.nqsv、bnode085) で
  `HoldoutObservationError: sweep phase still has unconsumed records`。stdoutを見ると
  sweepは1M/2M/4Mの3点を測定した後、`sweep.py`の`run_sweep`が持つ正当な早期終了
  (絶対規律4に基づき、3点以上測定した時点でL3サイズ下限基準を満たせば`max_records`まで
  回さず打ち切る設計) で正しく停止していた。
- 根本原因: fixが要求した「`next_sweep_records is None`(records系列を`max_records`まで
  完全消費)」という条件が、`run_sweep`のearly-stop経路 (`len(points) >= 3`の時点で
  `analyze.find_saturation`を呼び、下限基準を満たせば`break`する) を想定しておらず、
  実機で実際に発火する正当な早期終了を「未消費sweep」と誤検出して拒否した。
- 恒久対応: `transition_to_noise`のsweep完了判定を「`next_sweep_records is None`
  (全消費) または `len(state.sweep_records) >= 3` (early-stopが正当に発動しうる最小
  観測数に達している)」のいずれかに緩和した。段6所見2が実証した1点消費での即noise遷移
  (`len(sweep_records)==1 < 3`) は引き続き拒否される。
- 再発検知: `orchestrator/tests/test_holdout_observation.py`に、3点消費後のnoise遷移
  許可テストと1点消費の拒否テストの両方を追加した。実機のrr80/rr20成功投入で最終実証。
