## 総括

指定された2ファイルだけを修正しました。

- [codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:722)
  - `ls-files --stage --recurse-submodules` を廃止。
  - `.gitmodules` の path を再帰的に列挙し、superproject と各 submodule で個別に `git ls-files --stage -z` を実行。
  - 各 index の mode、object ID、stage を構文検査し、stage≠0、未知 mode、gitlinkと`.gitmodules`の不一致をfail-closedで拒否。
  - submodule index のpathをsnapshot相対pathへ変換してfilesystem閉包へ合成し、各submoduleの`.git` pointerも閉包に維持。
  - superprojectのgitlinkとsubmodule側の通常file entryを混同しない構造に変更。

- [test_codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:835)
  - ASTソース検査により、`ls-files`へ`--stage`と`--recurse-submodules`を同時に渡さないことを固定。
  - 合成Git repository＋submodule fixtureを追加。root indexの`160000/stage 0` gitlinkとsubmodule indexの`100644/stage 0` fileを別々に確認し、object/filesystem閉包が成立する期待を固定。
  - fix2で復元された500-byte境界、st_mode、untracked、prompt replacement、pair timing、post-treatment denominator、Git answer object再注入、attempt=4、pair片側retryの負例は削除・弱化していません。

Git 2.34.1の静的確認には、ローカル同梱manpageの`Source: Git 2.34.1`を使用しました。確認済みは、top-level `-c`、`config -f/--get-regexp/--name-only/--remove-section`、`submodule init/update --init --no-fetch/status`、`rev-parse --show-toplevel/--absolute-git-dir`、`for-each-ref --format=%(refname)`、`update-ref -d`、`remote remove`、`reflog expire --expire/--expire-unreachable/--all`、`repack -A/-d`、`prune-packed`、`prune --expire`、`fsck --unreachable/--no-reflogs`、`cat-file -e`、`log --all/--format`、`hash-object --no-filters`、`clone --no-hardlinks/--no-checkout`、`checkout -B`、`diff --binary/--cached/--name-only/--numstat`、`apply --whitespace`、`show -s/--format`、`status --porcelain/-z/--untracked-files`、`symbolic-ref --short`、`ls-files --stage/-z`です。`rev-list --missing`や新しい`cat-file` batch option等の使用はありません。参考となる上流仕様は[git-ls-files](https://git-scm.com/docs/git-ls-files.html)と[git-submodule](https://git-scm.com/docs/git-submodule)です。

`python3 -m py_compile tools/codex_reasoning_ab.py orchestrator/tests/test_codex_reasoning_ab.py`のみ成功しました。ユーザー指示に従い、**pytest、tools/run_tests.py、snapshot build、合成fixture実走、mutation、live Codexはすべて未実行**です。したがってテスト緑は主張しません。docs編集・commitも行っていません。親側で計算ノード上の131件＋追加2件を含むpytest、POS/NEG build-snapshot、受入全走を実測する必要があります。