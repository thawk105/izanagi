実装は完了しましたが、pytest は Pegasus の dispatch 障害（rc=16）で未実走のため、F-1〜F-4 は `partial` とします。docs 編集・stage・commit は行っていません。

変更内容:

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:266)
  - `_visible_markdown_text()` で comment・fence を除外し、blockquote も除外。
  - 可視な全 `reasoning=<値>` を抽出し、値列が厳密に `["max"]` の場合だけ受理。
  - `max+high`、重複 `max`、不可視 decoy を拒否。
  - finding を D207 に基づく時不変の文言へ変更。
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4805)
  - S02/S03 両方について comment・fence・blockquote decoy、`max+high`、重複 `max` を追加。
  - S03 値欠落を追加。
  - `_build_min_repo()` と `_run_check()` を通る production-path 負例を S02/S03 に追加。
  - finding 文言の時不変性を独立固定。

追加 nodeid:

- `test_dev_wave_reasoning_effort_pin_rejects_missing_dw_s03_value`
- `test_dev_wave_reasoning_effort_pin_rejects_dw_s02_decoys_and_duplicates`
- `test_dev_wave_reasoning_effort_pin_rejects_dw_s03_decoys_and_duplicates`
- `test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s02_high`
- `test_dev_wave_reasoning_effort_pin_production_path_rejects_dw_s03_high`
- `test_dev_wave_reasoning_effort_pin_findings_are_time_invariant`

実走結果:

- 新旧 10 node＋`test_command_docs_guard_positive_controls`＋plain-runner meta-test: runner が `qstat -Q preflight rc=1`、最終 rc=16。実装済み・未実走。
- `python3 tools/check_docs.py`: rc=0、現行 `workers.md` を受理。
- `python3 tools/check_codex_agents.py`: rc=0。
- AST parse、`git diff --check`: 成功。
- 変更は指定された 2 ファイルのみ。tracked テスト期待値の削除・反転・緩和はありません。

静的な波及先は、production caller の `main()` → `_check_command_docs_guard()`、共有 fixture `_build_min_repo()`、同 fixture を使う `test_check_docs.py` の全 consumer、custom `_run()`、plain-runner coverage meta-test です。`_reference_id_sections()` は変更しておらず、DW-S05 の `reasoning=high` は対象外です。

## 総括

- F-1: partial — 実装・負例追加済み、pytest 未実走。
- F-2: partial — S02/S03 production-path 負例追加済み、pytest 未実走。
- F-3: partial — S03 欠落・両節 duplicate 負例追加済み、pytest 未実走。
- F-4: partial — 時不変 finding と独立 pin 実装済み、pytest 未実走。
- 変更 file: `tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`。
- 追加 nodeid: 6、継承 node と合わせて焦点 10 node。
- 実走: `check_docs`/`check_codex_agents`/AST/diff は成功、pytest は基盤 rc=16。