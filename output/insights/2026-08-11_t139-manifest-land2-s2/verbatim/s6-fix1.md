F-1〜F-4の4件を対応しました。変更は [blobref.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s2/orchestrator/preregistration/blobref.py:30) と [test_t139_blobref_git_trust.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s2/orchestrator/tests/test_t139_blobref_git_trust.py:143) のみです。commit、docs、`output/` の編集はしていません。

F-1 は `git config -z --type=bool --get-regexp` を使い、NULでレコードを分離してから、各レコードの `key LF normalized-value` を解析します。一般空白で分割しないため、remote subsection 内の空白・TABと値の境界が曖昧になりません。boolean値の正規化はGit自身に委ねています。

挙動差は次のとおりです。

- 変更前に誤拒否されていた、空白またはTABを含むremote名で `promisor` が偽となるrepositoryを受理します。これは `false/no/off/0/空値` の全クラスを含みます。
- 空白・TABを含むremote名でも真値は、解析不正ではなくpromisor remoteとして明示的に拒否します。
- `yes/on/1/裸key` は真、`no/off/0/空値` は偽というGitの正規化を固定しました。
- `http-alternates` のみを持つrepositoryは引き続き拒否され、その専用負例を追加しました。
- `/usr/bin/git` 固定と `GIT_NO_LAZY_FETCH` の挙動は変更せず、裁定された運用束縛・promisor補助防壁を日本語コメントで明記しました。

追加nodeidは以下です。

- `orchestrator/tests/test_t139_blobref_git_trust.py::test_fixed_git_executable_resolves_to_absolute_path`
- `orchestrator/tests/test_t139_blobref_git_trust.py::test_http_alternate_object_store_is_rejected`
- `orchestrator/tests/test_t139_blobref_git_trust.py::test_remote_promisor_false_with_whitespace_subsection_is_accepted[space]`
- `orchestrator/tests/test_t139_blobref_git_trust.py::test_remote_promisor_false_with_whitespace_subsection_is_accepted[tab]`
- `orchestrator/tests/test_t139_blobref_git_trust.py::test_remote_promisor_true_with_whitespace_subsection_is_rejected[space]`
- `orchestrator/tests/test_t139_blobref_git_trust.py::test_remote_promisor_true_with_whitespace_subsection_is_rejected[tab]`
- `orchestrator/tests/test_t139_blobref_git_trust.py::test_remote_promisor_true_boolean_alias_is_rejected[yes]`
- `…::test_remote_promisor_true_boolean_alias_is_rejected[on]`
- `…::test_remote_promisor_true_boolean_alias_is_rejected[one]`
- `…::test_remote_promisor_true_boolean_alias_is_rejected[bare]`
- `…::test_remote_promisor_false_boolean_alias_is_accepted[no]`
- `…::test_remote_promisor_false_boolean_alias_is_accepted[off]`
- `…::test_remote_promisor_false_boolean_alias_is_accepted[zero]`
- `…::test_remote_promisor_false_boolean_alias_is_accepted[empty]`

既存テストの期待値は一つも変更していません。test差分の削除行は0で、追加のみです。AST parse（2ファイル）と `git diff --check` は成功しました。

テスト実走は未完了です。次の範囲を `tools/run_tests.py` 経由で2回要求しましたが、どちらもpytest開始前に `qstat -Q preflight rc=1`、runner rc=16で停止しました。

- `orchestrator/tests/test_t139_blobref_git_trust.py`
- `orchestrator/tests/test_plain_runner_coverage.py`

したがってテスト赤は観測されていませんが、緑とも申告しません。

## 総括

- F-1〜F-4の4件を実装しました。
- AST parse 2ファイルと `git diff --check` は成功しました。
- pytestはdispatch基盤rc=16のため実装済み・未実走です。
- 未解決事項は焦点テストとmeta-testの実走のみです。