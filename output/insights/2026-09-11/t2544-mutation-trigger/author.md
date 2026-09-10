## 総括

実装済み・未実走。対象1 literal のみ訂正しました。自走による親受入の代替・closed 判定はしていません。

## 変更

[tools/check_docs.py:962](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2544-mutation-trigger/tools/check_docs.py:962) の `CONDITION_TRIGGER_CONTRACT["15"]`：

- 変更前：旧文言「fix 後に変異を走らせる直前」を受理、新文言を拒否。
- 訂正後：新文言「変異を走らせる直前」を受理、旧文言を拒否。

上記は静的確認です。条件15の参照先 `DW-M07`、correctness 受理集合、検査ロジックは変更していません。独立した既存 pin はなく、テスト編集もありません。

## 検証

`python3 tools/run_tests.py -n 0 … -v` で、次の既存 nodeid を指定しました。接頭辞はすべて `orchestrator/tests/test_check_docs.py::` です。

- `test_real_repo_clean`
- `test_synthetic_repo_baseline_clean`
- `test_dev_wave_dispatch_conditionality_retyping_is_rejected`（4ケース）
- `test_condition_18_contract_pins_exact_two_points_and_targets`

runner は `qstat -Q preflight rc=1` により **rc=16、child_started=false**。実走範囲は0件で、テストの緑・期待赤・回帰赤は未判定です。`git diff --check` は成功しました。

正例の実体は親が訂正済みの `.claude/commands/dev-wave.md:103`。負例は同じ条件15だけを旧文言に戻した docs ですが、変異は実施していません。

## 波及

- 直接 consumer：`_check_command_docs_guard()` の条件照合（`tools/check_docs.py:6446`）。
- 共有 fixture：`_write_command_guard_docs()` が定数から条件15を生成し、`_build_min_repo()` 経由の既存テストへ反映されます。fixture は無編集です。
- 所有外 caller：`dev_waves/checker.py`、`dev_waves/daemon.py`、`dev_wave_land.py`、`task_run_check.py`。実 checker の呼出経路へ新契約が反映されます。
- その他 consumer：`test_s8c_preregistration_invariant.py` は実 checker を呼びます。`test_check_ai_provenance.py` の参照定数、`spool_fold.py` の予算定数は変更対象外です。
- `codex_reasoning_ab.py` にファイル全体の hash pin が存在します。条件15の独立 pin ではなく、scope 外として変更していません。

docs 編集、git add、commit、全走、変異本走は行っていません。