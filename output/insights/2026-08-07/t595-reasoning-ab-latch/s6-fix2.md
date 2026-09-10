G-1 の修正は実装済みです。ただし pytest が dispatch 基盤障害で起動しなかったため、判定は `partial` です。

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:276)
  - 単一 regex で `reasoning`、`reasoning_effort`、`model_reasoning_effort` を認識。
  - 単・二重引用値に対応。
  - blockquote 除去を削除し、HTML comment / code fence 除去は維持。
  - 抽出値が厳密に `["max"]` の場合のみ受理。

- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4904)
  - S02/S03 の双方に指定負例 (a)〜(e) を追加。
  - production path の (a) を双方に追加。
  - comment/fence 内の high、無関係な境界語を受理する正例を追加。
  - 単引用値の負例も追加。
  - 既存 assert・期待値は変更、緩和、skip、削除していません。揮発値も追加していません。

追加 nodeid:

- `test_dev_wave_reasoning_effort_pin_rejects_dw_s02_real_keys_and_quotes`
- `test_dev_wave_reasoning_effort_pin_rejects_dw_s03_real_keys_and_quotes`
- `test_dev_wave_reasoning_effort_pins_ignore_comment_and_fence_examples`
- `test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s02_real_key`
- `test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s03_real_key`

検査結果:

- `python3 tools/check_docs.py`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- AST parse、regex の書込みなし probe、`git diff --check`: 成功
- `test_check_docs.py -k 'dev_wave_reasoning_effort'`: runner rc=16、pytest 未起動
- 新規 S02 node 単独: runner rc=16、pytest 未起動
- plain-runner meta-test＋`test_command_docs_guard_positive_controls`: runner rc=16、pytest 未起動
- 原因はいずれも `qstat -Q preflight rc=1`。テスト失敗ではなく dispatch infrastructure failure です。

静的な波及先は `main()` → `_check_command_docs_guard()`、共有 `_build_min_repo()` / `_run_check()`、worker-section mutation helpers、既存の全 `test_dev_wave_reasoning_effort_*`、command-guard consumer、plain-runner coverage meta-test です。`_reference_id_sections()`、RA-4、RB-5/RB-6、指定定数には触れていません。docs 編集・commit もありません。

受理集合は意図どおり縮小します。blockquote 内の effort も可視扱いとなるため、引用内の `high` 例示は赤になります。一方、comment / code fence 内の `high` は引き続き無視されます。

## 総括

- G-1: `partial` — 実装済み、pytest は基盤 rc=16 で未実走。
- 変更 file: `tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`。
- 追加 nodeid: 上記 5 件。
- 実走成功: `check_docs`、`check_codex_agents`、AST、regex probe、diff check。
- pytest 範囲: reasoning 全 node、S02 新規単独、command-guard、plain-runner meta-testを試行。
- 受理集合: 引用内 effort 例示を新たに拒否。comment / fence 内例示は引き続き受理。