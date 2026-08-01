## 総括

F1〜F4 の修正を実装しました。コード／テスト 5 ファイルのみが未コミットで、docs・policy JSON・共有 policy は無変更です。

### (a) 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed（pytest 未実測） | submit の Python 内で walltime 値を直接固定。既存 Bash 比較も維持。NUL 負例を追加 |
| F2 | closed（pytest 未実測） | 両 script で walltime を strict `str`、数値 7 key を strict `int` 化。bool も拒否 |
| F3 | closed | strict int 後は単独比較削除が等価変異に戻ることを整数算術で確認 |
| F4 | closed（pytest 未実測） | override 無しは `copy2`、override 有りは `copymode`。source/fixture mode を assert |
| F5 | partial | 裁定どおり未修正。command substitution が末尾空行を消す残存限界として記録 |

### (b) 編集箇所

- [submit_t126_qualification.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:199): strict 型検査、Python 内 walltime 比較
- [t126_qualification.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:453): strict 型検査、既存 mapping assert 維持
- [test_t126_pegasus_tools.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:827): mode 保存・assert
- 同テスト [submit 負例](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:3066)、[job 負例](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:3977)
- 段5から継承した [contract.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/qualification/contract.py:240) と [contract tests](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_qualification_contract.py:48) は維持

### (c) 新設・更新テスト

今回新設:

- `test_submit_rejects_nul_in_walltime_before_scheduler_calls`
- `test_submit_rejects_reservation_policy_type_drift_before_scheduler_calls`
  - equal-float / near-float / bool / walltime-not-string
- `test_job_rejects_reservation_policy_type_drift_before_mapping`
  - equal-float / near-float / bool / walltime-not-string

段5から継承した新設・更新テストも変更せず維持しています。

### (d) 検査結果

成功した静的検査:

- `git diff --check`
- 両 shell の `bash -n`
- 変更 Python 3 ファイルの `python3 -m py_compile`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- F3 整数算術マイクロプローブ

以下を `tools/run_tests.py` で dispatch しましたが、どちらも `qstat -Q preflight rc=1`、runner rc=16 で投入前停止しました。

- `test_submit_rejects_nul_in_walltime_before_scheduler_calls`
- submit/job の型負例
- 段5の submit/job 境界テスト
- `test_shell_scripts_pass_bash_syntax`
- `test_fr3_mutation_node_registry_is_exact_and_complete`
- protocol 正例・compensated-drift 負例

したがって pytest 実走 nodeid は 0 件で、緑は主張しません。親 docs 未 land により許容する赤 finding は事前指定どおり 0 件です。

### (e) F3 の結論

strict int の下では、member/gap と残る cap 比較を canonical に固定すると、和 29100 から削除した cap が canonical 値へ一意に決まります。よって submit の cap 比較単独削除は再び等価変異です。

同値 float は型検査だけが拒否理由です。near-float は型検査に加えて既存の個別値比較でも拒否されるため過剰決定です。テストは型診断が先に発火することを確認しますが、型 guard 単独の mutation kill 証拠には数えません。

### (f) 波及可能性

- レビューで列挙された既存 `_attempt` caller 62 件。mode は production の `0755` へ復元されます。
- `_submit_fixture`、`_run_submit`、`_run_bound_job_terminal` の既存 caller。追加引数は optional で互換性を維持。
- script identity/hash、source-tree、series identity、spooled-script consumer tests。
- `validate_protocol` を通る submission、driver、collector/public consumer。
- scope 外の予約 policy consumer 意味論、重複 key 非対称、他 7 readarray、term grace には変更なし。

### (g) 未了事項

- 焦点 pytest、test file 全体、変異 matrix、計算ノード全走は未実行。
- 親による再レビュー、受入、記録、commit が必要。
- F5 は未修正の残存限界。
- `git add`・commit・push は実行していません。