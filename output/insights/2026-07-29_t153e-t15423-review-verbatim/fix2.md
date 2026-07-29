R-1 の root cause を最小fixで閉じました。fix2で編集したのは [tools/check_ai_provenance.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423-author/tools/check_ai_provenance.py:165) と [test_check_ai_provenance.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423-author/orchestrator/tests/test_check_ai_provenance.py:583) の2ファイルです。`tools/check_docs.py` と `test_check_docs.py` は段5からの既存stage済み差分を保持し、fix2では変更していません。

履歴loopは commit ごとの policy ancestry を先に判定し、`validate_message(..., check_cab=False)` を pre-policy commit にだけ渡します。これにより legacy AI-Agent parser、scope、Codex-author検査は従来どおり走る一方、canonical CAB parser、fresh temporary directory、raw CAB grammar は一切呼ばれません。post-policy と `--message-file` は既定の `check_cab=True` のままで、受理集合を他の境界へ拡大・縮小していません。

挙動は次のとおりです。

- pre-policy: fix前はCAB結果を捨てる前にparserを起動するため、parser障害がrc=2へ遡及。fix後はparser call count 0で、既存AI検査が適合するcommitはrc=0。
- policy導入commit以後: fix前後ともcanonical parserを実行。parser failureはrc=2。
- `--message-file`: fix前後ともpolicy履歴によらずcanonical parserを実行。parser failureはrc=2。

新規nodeidは以下です。

- `test_cab_pre_policy_range_does_not_call_canonical_parser`
- `test_cab_post_policy_parser_failure_fails_closed_with_rc2`
- `test_message_file_parser_failure_fails_closed_with_rc2`

実走結果:

- 新規3 node＋関連する既存pre/post/message-file 4 node: `7 passed / 0 failed`
- `python3 tools/run_tests.py orchestrator/tests/test_check_ai_provenance.py orchestrator/tests/test_check_docs.py`: `187 passed / 1 failed`
- 唯一の期待赤: `test_policy_needle_literal_matches_production_and_repo_policy_exactly_once`。親だけがlandする `docs/ai-provenance.md` のpolicy literalがauthor worktreeでは0件であるためです。それ以外の回帰はありません。
- consumer node `test_run_tests_task_run.py::test_check_wrapper_records_fixed_suite_kind_and_duration`: `1 passed`
- `python3 tools/check_docs.py`: 違反なし
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_ai_provenance.py`: 495件、違反なし
- 新規nodeの存在・内容を別途pinする既存meta-testは検索上ありませんでした。

所有外への波及可能性は、CLI callerの [tools/task_run_check.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423-author/tools/task_run_check.py:18)、手動実行consumerであるAGENTS/CLAUDE/O17、親がlandするpolicy literalとD98です。直接の `validate_message` / `_parsed_trailers` callerは所有テスト内だけです。共有fixtureは同ファイル内の `_policy_history` と `SPLIT_CAB_NONE` に閉じています。`test_check_docs.py` はprovenance予算registryのみをconsumeし、今回のCAB分岐には到達しません。

HEADとの差分は指定された所有4ファイルだけで、docs、wave成果物、handoff、その他のパスは編集していません。commitも作成しておらず、HEADは `8c8dc5e` のままです。fix2のstagingはsandboxのread-only Git indexにより失敗したため、2ファイルは既存stage差分に対する未stage差分として残っています。

## 総括

R-1は、policy ancestryをCAB検査より先に判定し、pre-policy履歴からcanonical parser経路を完全に除外することで閉じました。新規3境界nodeはすべて緑で、指定全焦点走の赤は親docs未landによる独立policy literal node一件だけです。所有外編集・test弱体化・xfail・fixture hash差し込み・揮発値pin・commitはいずれも行っていません。