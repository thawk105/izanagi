F1〜F4 の実装修正は完了しましたが、焦点 pytest が環境要因で未実走のため、全項目を `partial` と報告します。既存テストの期待値・docs・index・commit は変更していません。

| 項目 | 状態 | 対応 |
|---|---|---|
| F1 | partial | `evaluate_fn(...)` に `authorization_contract=` を明示 keyword で追加。AST 条件は静的確認済み |
| F2 | partial | 認可追加前の固定 signature spy でも `extra_correctness` が keyword で届く互換分岐を追加 |
| F3 | partial | `extra_correctness=None` も同じ互換分岐で evaluate へ到達 |
| F4 | partial | `current_site` 本体の置換を廃止し、hostname と `_has_nqsv` 入力だけを中立化 |

変更ファイル:

- [s1_direct_comparison.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix3-a/orchestrator/campaign/s1_direct_comparison.py:814)
  - `authorization_contract` を `**kwargs` から外し、sink 呼出しの明示 keyword に変更。
- [loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix3-a/orchestrator/campaign/loop.py:40)
  - injected evaluate の signature を検査。
  - production sink、明示認可引数、`**kwargs` 対応 spy には従来どおり契約を転送。
  - 認可追加前の固定 signature spy だけ契約 keyword を省略し、`extra_correctness` は両分岐で明示転送。
  - run 単位の認可検査は引き続き `layout.ensure()`、WAL、build より前。A2 の5条件と pipeline の認可検査は変更なし。
- [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-fix3-a/orchestrator/tests/conftest.py:42)
  - `site_policy.current_site` の monkeypatch を廃止。
  - `site_policy.socket` の局所 proxy と `_has_nqsv=False` で `OTHER` を決定的に返す。
  - stdlib `socket` を共有する他 consumer には波及しない。
  - `_detect_site_under_test` opt-out は維持。

静的な波及確認:

- `pipeline.evaluate` と `**kwargs` spy は引き続き認可契約を受け取ります。
- 旧固定 signature spy でも run 冒頭の認可は完了済みで、認可後にのみ呼ばれます。
- `extra_correctness` は有効／無効の両枝で常に keyword 渡しです。
- site-policy 専用テストは `_detect_site_under_test` により実 detector を使用します。
- テスト自身による `current_site`、`T._current_site`、hostname 入力の明示 monkeypatch は fixture より後に適用され、従来どおり優先されます。
- `T._current_site is site_policy.current_site` と中立入力での `OTHER` は静的プロセス検査で確認済みです。

検証結果:

- Python 構文解析、sink AST inventory、spy signature、site seam 検査: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- 焦点4テスト: 未実走
  - `tools/run_tests.py` 経由で起動したが、`qstat -Q preflight rc=1`、runner rc=16 でテスト開始前に停止。
  - targeted run は未初期化 submodule marker も警告しましたが、停止原因は dispatch infrastructure failure です。
  - pytest への直接迂回はしていません。

直せなかった実装項目はありません。ただし実走できていないため、4件を `closed` とは申告できません。

## 総括

F1〜F4 の原因に対応する最小実装を3ファイルへ入れ、期待値の変更や認可条件の弱体化はしていません。静的検査は全て通過していますが、runner の dispatch preflight 障害により「実装済み・未実走」です。