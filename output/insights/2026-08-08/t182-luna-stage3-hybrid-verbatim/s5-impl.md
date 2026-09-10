実装済みです。編集は指定された 2 ファイルだけで、docs の既存差分は親の変更として保持し、commit / add / stash はしていません。

### 実装箇所

- 定数群 `CODEX_DEV_WAVE_STAGE_MODEL_LITERAL`、各 finding、`DEV_WAVE_MODEL_SLUG_RE`: [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:264)
- 新規 `_check_dev_wave_model_pins`: [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3409)
- `_check_command_docs_guard` からの呼び出し: [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3648)
- min repo の dispatcher literal／`DW-O01 -m <model>` fixture: [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_check_docs.py:480)
- production-path helper と負例 5 件・正例・独立 pin: [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_check_docs.py:5057)

`_check_dev_wave_reasoning_effort_pins`、`REFERENCE_LIMITS`、`COMMAND_LIMITS`、`DEV_WAVE_AGGREGATE_BYTES` は変更していません。既存テストの期待値も変更していません。

### 受理・拒否差分

変更前は model 固有検査がなく、dispatcher 行の改変・削除や `DW-S02` / `DW-S03` / `DW-O01` への slug 混入を受理していました。

変更後は次を追加で拒否します。

- dispatcher exact literal が存在しない: 1 finding
- 対象節が非一意、または可視本文に `gpt-5.6-*` がある: 節ごとに 1 finding
- backtick、`-m`、`--model=`、行頭 bare の表記差はすべて検出

HTML comment／fenced code 内は従来の可視本文規則どおり対象外です。対象節外や別の既存 gate の受理・拒否集合は変えていません。

### pytest

実装済み・未実走です。次の範囲を試行しましたが、pytest 起動前に `tools/run_tests.py` が rc=16 で停止しました。

```text
orchestrator/tests/test_check_docs.py
-k "dev_wave_model_pin or dev_wave_reasoning_effort_pin"
```

新規 nodeid は以下です。

- `test_dev_wave_model_pin_production_path_rejects_dw_s03_backticked_slug`
- `test_dev_wave_model_pin_production_path_rejects_dw_s03_bare_model_decoy`
- `test_dev_wave_model_pin_production_path_rejects_dw_s02_slug`
- `test_dev_wave_model_pin_production_path_rejects_dw_o01_concrete_model`
- `test_dev_wave_model_pin_production_path_rejects_dispatcher_literal_drift`
- `test_dev_wave_model_pins_accept_current_docs_contract`
- `test_dev_wave_model_pin_contract_is_time_invariant`

原因は sandbox 外の予約台帳を更新できず dispatch に倒れ、`qstat -Q` が `Unknown user-id` になったためです。direct pytest では迂回していません。

実走済みの静的検査は以下です。

- `python3 tools/check_docs.py`: 違反なし
- `python3 tools/check_codex_agents.py`: OK
- `py_compile`: OK
- `git diff --check`: OK
- min fixture: reference 2,040 / 25,200 bytes、dispatcher 4,122 / 9,500 bytes

### 所有外への波及可能性

- caller: `main()` → `_check_command_docs_guard`: [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:4107)
- 共有 fixture `_build_min_repo()` の全 consumer は、新しい正常 baseline を継承します。
- `tools/task_run_check.py`、`tools/dev_wave_land.py`、dev-wave integration/checker tests は `check_docs.py` 実行結果を消費するため、新しい拒否条件が波及します。
- `test_s8c_preregistration_invariant.py` は `check_docs.main()` を直接呼びます。
- `tools/codex_reasoning_ab.py` の両ファイル hash は歴史 snapshot pin であり、本変更では更新対象外です。

### 総括

- dispatcher の段別 model 行を exact literal で pin しました。
- `DW-S02` / `DW-S03` の可視本文から `gpt-5.6-*` を排除しました。
- `DW-O01` にも同じ不在 pin を追加し、`-m <model>` を受理します。
- 公開経路の負例 5 件と実 docs 正例、独立 literal/regex pin を追加しました。
- 静的検査は緑、pytest は Pegasus admission/dispatch 障害により未実走です。