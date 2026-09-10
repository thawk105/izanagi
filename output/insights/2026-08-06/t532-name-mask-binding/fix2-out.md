F-3 は **partial（実装済み・未実走）** です。

- 非 `str` の3経路で対象 object の `repr` を呼ばず、型名だけを含む `FreezeError` を直接送出するよう修正しました。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:97)
- `repr` が例外を送出する object で3経路を固定する、引数なし・非 parametrized の専用回帰 node を追加しました。[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:247)
- 既存テスト期待値、docs、編集禁止ファイル、凍結成果物は変更していません。凍結 JSON の SHA-256 は引き続き `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516` です。
- commit・stage は行っていません。

受理集合は、非 `str` の拒否条件を維持したまま例外構築だけを変更し、plain `str` の membership・mask 照合経路を変更していないことを静的に確認しました。builder も型検査と重複検査を分離しただけで、成功条件は同一です。

検査結果：

- `py_compile`、`git diff --check`、`check_codex_agents.py`、`check_docs.py`: 成功
- 関連2 test file、および新設 node・M1 node・32 mask 正例・plain-runner meta-testを `tools/run_tests.py` で試行
- いずれも `qstat -Q preflight rc=1`、dispatch rc=16 で実走前に停止。pytest の緑は主張しません
- M1〜M7 の kill 経路は静的には変化なし。M1 は引き続き `test_trigger_name_mask_binding_rejects_comparison_spoof_name` が期待 kill です

## 総括

- F-3 は診断経路と専用回帰 nodeを実装済み。
- 受理・拒否条件および M1〜M7 の kill 経路は静的に不変。
- 禁止ファイル・凍結 bytes・既存期待値への変更なし。
- 残る不確実性は、Pegasus dispatch 障害により pytest が未実走である点のみ。