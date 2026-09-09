## 実装

- [model.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2536-author/orchestrator/campaign/model.py:39) に17軸の静的表、正逆変換、protocol内単射性検査、未知軸の恒等 fallback を追加しました。
- [cli.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2536-author/orchestrator/calibrator/cli.py:432) は受領証の cache 名を逆変換します。
- [screening_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2536-author/orchestrator/campaign/screening_driver.py:142) の局所組み立て2箇所を共有変換へ統一しました。
- [test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2536-author/orchestrator/tests/test_pegasus_calibration_workload.py:38) に実 CMake parser による照合、両側 rename 負例、単射性、fallback、非対称値、受領証検査を追加しました。実 repo・submoduleは変更していません。

## 受理・拒否の変化

変更前は cicada が汎用名を生成・受理し、実体名は `missing_axes` で拒否されました。変更後は実体名 `CCBENCH_INLINE_VERSION_OPT_CICADA` を生成・受理し、旧汎用名は `receipt-genome-invalid` で拒否します。

既存の `missing_axes`、duplicate define、build argv内define、`TRACE`がちょうど1回0という拒否経路は維持しています。silo・mocc・tictoc、補助defineのargv、`Genome.canonical()`、認定protocol集合は不変です。

## 検査

`tools/run_tests.py orchestrator/tests/test_pegasus_calibration_workload.py -q` を実行しましたが、`qstat -Q` preflight失敗により `rc=16`、`child_started=false` でした。したがって追加nodeidを含む同ファイル全体と、関連する `test_calibrator_certify.py`、`test_campaign.py`、`test_buildcache_v2.py`、`test_t2187_adaptive_const_probe.py` は未実走です。

実行できた静的検査:

- 4編集ファイルの構文コンパイル成功
- producerと未知軸fallbackの軽量診断成功
- `git diff --check` 成功
- `tools/check_codex_agents.py` は `rc=0`
- `tools/check_docs.py` は `rc=0`
- 既存テストファイルはpytest専用allowlist登録済みで、meta-test台帳更新は不要

## 変異アンカー

M1は静的表と実体照合・producer検査、M2は旧汎用名拒否、M3は不正な表のcopyを渡す両方向単射性検査、M4は軸ごとに異なる値のproducer検査、M5はCCBench側・Izanagi側rename負例がそれぞれ捕捉します。

## 波及可能性

所有外では `buildcache.py` の2呼び出しと、s2・s3・s5・s6・s8a各driverの `cmake_defines()` 利用箇所へ波及します。実質的なargv変更はcicadaだけです。受領証consumerは `test_calibrator_certify.py`、fallback固定は `test_campaign.py` と `test_t2187_adaptive_const_probe.py`、build経路は `test_buildcache_v2.py` が関連します。共有 `SPACES` と既存fixtureは編集していません。

## 総括

静的な17軸写像をproducer・receiver・screeningで共有し、cicadaの実体cache名へ合わせました。  
実CMakeとの独立照合、両側rename負例、単射性、非対称値検査を追加しました。  
実装済みですが、正式pytestはPegasus dispatchのrc=16により未実走です。