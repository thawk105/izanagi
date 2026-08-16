R2 の修正を実装しました。[対象テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:230) の 2 行だけを変更しています。

| 所見 | 状態 | 対応 |
|---|---|---|
| R2 | partial | g4 の schema を `"s8c-prereg-condition-freeze/v2"`、判定器版を `"s8c-decider/v1"` に固定。pytest 未実走のため `closed` とはしていない |

関数 1 の現在 tip と `prereg.SCHEMA_VERSION` / `prereg.DECIDER_VERSION` の比較、`report.effective is False` は変更していません。契約継続性、hash 相異、supersedes、D458、および legacy param `(1, 2, 3)` も維持しています。

検査結果:

- `git diff --check`: 成功
- Python AST parse と指定 assert の静的照合: 成功
- 焦点 nodeid:
  `orchestrator/tests/test_s8c_preregistration_invariant.py::test_generation_4_changes_revision_procedure_without_changing_condition_contract`
- repository runner は Pegasus queue preflight の `qstat -Q` で `rc=16`。pytest は 1 件も実行されていないため、実装済み・未実走です。
- runner が生成した一時 output は除去済みです。

静的な波及可能性:

- production caller: `prereg.generation_path()` と `prereg._load_freeze_record()` を引き続き同じ形で利用。production コードへの変更なし。
- 共有 fixture: 修正関数は `repository_candidate_commit` を使わないため影響なし。関数 1 の fixture consumer は不変。
- consumer test: candidate freeze 検査、現在 tip の版検査、legacy g1〜g3 読取検査はすべて不変。
- collection/meta-test: nodeid、marker、fixture signature、parametrize を変えていないため、real-repo serialization と plain-runner coverage への構造的変更なし。
- 将来の g5: 関数 1 が現在 tip と現在定数を検査し、関数 2 は歴史的 g4 の識別子を固定するため、正当な版 bump を拒否しません。

docs、production コード、既存 output は編集せず、commit も作成していません。

## 総括

R2 の指定修正は完了しています。検査環境の queue preflight failure により焦点 pytest は未実走なので、判定は `partial` です。