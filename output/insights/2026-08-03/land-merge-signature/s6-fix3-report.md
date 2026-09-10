指定されたテストファイルだけに 2 fixture を追加しました。実装・既存テスト・docs は変更せず、commit もしていません。

| 穴 | closed | partial | regressed | 対応 |
|---|---|---|---|---|
| H1 / M03 | yes | なし | なし | 複数 trusted parent の外側だけに署名を配置 |
| H2 / M04 | yes | なし | なし | cutoff なしで第 2 parent だけに署名を配置 |

新設 node:

- `orchestrator/tests/test_dev_waves_git_state.py::test_octopus_with_multiple_trusted_parents_rejects_signature_visible_only_from_untrusted_parent`
- `orchestrator/tests/test_dev_waves_git_state.py::test_landed_interval_without_cutoff_rejects_signature_visible_only_from_second_parent`

コードは [test_dev_waves_git_state.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:562) に追加しています。

H1 では `first_trusted` と `cutoff` の 2 parent が cutoff の祖先です。octopus の最終 tree は両 trusted parent と `FOLDED.md` が同一で、untrusted parent とだけ `M docs/spool/FOLDED.md` になります。

- 現行の `len(trusted) == 1` は偽なので全 parent を走査し、untrusted parent の署名を検出して拒否します。
- M03 の `len(trusted) >= 1` では trusted 2 parent のみに絞られ、署名が消えます。pending fragment もないため検証は受理へ進み、拒否を要求する新 node 単独で赤になります。

H2 では merge tree を第 1 parent と完全に同一にし、第 2 parent とだけ `FOLDED.md` が異なる構成にしました。

- 現行の `diff_parents = parents` は第 2 parent の署名を検出して拒否します。
- M04 の `parents[:1]` は差分のない第 1 parent しか走査しません。pending fragment もなく受理されるため、新 node 単独で赤になります。

確認結果:

- pytest: **未実走**。実行環境が Pegasus ログインノード `pegasus02` であり、単一 nodeid を含め pytest 実行は禁止されています。
- `python3 -m py_compile orchestrator/tests/test_dev_waves_git_state.py`: 成功
- `git diff --check`: 成功
- 既存 2 node は無変更で残存
- `tools/dev_waves/git_state.py` は無変更

## 総括

- H1 / H2 はともに closed、partial・regressed はありません。
- 追加はテスト 2 本、70 行のみです。
- 両 fixture とも対象 parent だけに `FOLDED.md` 変更署名を置いています。
- 現行実装で拒否、対象変異で受理となることを静的に確認しました。
- pytest は未実走、実装・docs・既存期待値・commit は非変更です。