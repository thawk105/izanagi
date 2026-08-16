## 総括

T-329 段 5 実装を完了しました。変更は指定された 2 ファイルだけで、docs 編集・commit はしていません。

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py)
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py)

`python3 tools/check_docs.py` は rc=0、出力は `check_docs: 違反なし` です。

### 現行の受理・拒否挙動

受理するもの:

- 新旧 carry 書式が、現行 worklog または採番 archive の実在 entry を指す。
- filename と README の主張範囲が実体 entry 集合と完全一致する。
- 4 桁以上の entry 番号を先頭ゼロ規則で採番として扱う。
- 日付だけ／`worklog-phase1-2.md` 型の非採番 archive は新検査の対象外。
- README の折り返し、終了日省略、`YYYY-MM-DD`／`MM-DD` を受理する。

拒否するもの:

- 宙吊り carry、全域 entry 番号の重複。
- filename／README の内部欠番、範囲外 entry、逆転範囲。
- malformed filename。
- 採番 archive の番号なし H2、`(続き)`。
- README 正規行の欠落、bare 行、重複行。

日付一致、carry 参照先での同一 ID 保存、`spool_fold.py` 本体変更は scope 外のままです。

### 実装内容

- carry は参照先番号ごとに最初の `(path, line, task_id)` 1 件だけ保持。
- 既存 archive 走査と README 読取を再利用し、新規 I/O 呼出しは 0 件。
- 欠番は区間走査で判定し、巨大な `set(range(...))` は作成しない。
- README pass には既読 archive の実体集合をメモリで渡す。
- MU-1〜MU-9 に対応する新規テストを追加。
- fold rotation 後に実物の checker を起動する統合テストを追加。
- 既存テストの期待値は変更していません。
- 意図的な U+309A を含む 2 行は base と digest 一致を確認済みです。

### 検査結果

- `python3 tools/check_docs.py`: rc=0、違反なし
- `python3 tools/check_codex_agents.py`: rc=0
- AST parse: 成功
- `git diff --check`: 成功
- 追加された `glob`／`iterdir`／`read_text`／`open`／`stat`: 0
- 変更ファイル: 指定された 2 ファイルのみ

pytest は実装済み・未実走です。`tools/run_tests.py` で次の 2 回を試しましたが、いずれも pytest 起動前の `qstat -Q preflight rc=1` により rc=16 でした。

- 新規テスト群 17 parameter case の焦点走
- `test_backlog_guard_numbered_archive_entry_is_carry_target` 単独走

したがって、実走 nodeid はありません。テストを緑とは報告しません。

### 所有外への波及可能性

- `tools/dev_wave_land.py`、`tools/dev_waves/checker.py`、`task_run_check.py` は checker の rc を consumer として利用。
- `tools/spool_fold.py` は `WORKLOG_ROTATE_BYTES` と checker bytes を入力閉包に含み、生成する filename／README が今回の文法対象。
- `_build_min_repo`、`_write_backlog_docs`、`_archive_readme` は共有 fixture。既存定義・期待値は維持。
- `test_s8c_preregistration_invariant.py` などが `check_docs.main()` を直接呼ぶ。
- `tools/codex_reasoning_ab.py` の hash pin は base blob を読む凍結参照であり、live fixture hash の更新対象ではありません。