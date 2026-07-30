round 3 の 2 residual を閉じました。index・docs・commit・network には触れず、未ステージ差分は指定 4 ファイルだけです（243 insertions / 9 deletions）。

変更内容:

- [tools/dev_wave_land.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py)
  - pure deletion と gitlink→normal blob/tree を区別。
  - replacement は T の通常 entry を許可しつつ、旧 `.git` identity と `.git/modules/<path>` の消去を要求。
  - pure deletion は従来どおり path・metadata の双方不在を要求。
- [orchestrator/tests/test_dev_wave_land.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py)
  - normal tree/blob の双方で、初回 postcondition failure、identity/metadata 残存拒否、同一 A/T/audit による `already-landed` を固定。
- [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py)
  - interpreter/global option の個数・順序に依存しない広い command-line grammar に変更。
- [orchestrator/tests/test_check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_check_docs.py)
  - 指定された option 付き 4 形式を独立負例として追加。
  - non-land Python、non-ff Git command、通常 inline prose の正例を維持。

Red / Green:

- 修正前焦点: `2 failed, 1 passed`
- land: `34 passed`
- check_docs pytest: `146 passed`
- 合同: `180 passed`
- direct land: `34 passed, 0 failed`
- direct check_docs: `146 passed, 0 failed`
- plain-runner/meta: `183 passed`
- `tools/check_docs.py`: `違反なし`
- `tools/check_codex_agents.py`: `OK`
- 4 ファイル `py_compile`: rc=0
- unstaged `git diff --check`: rc=0

追加で実行した staged `git diff --cached --check` は、所有外の既存 index snapshot 内にある `parent-brief.md` と `s3-git-race.prompt.md` の blank-line finding 2 件で rc=1でした。index は変更していません。

波及先は D16 cleanup caller、Claude command/Codex Skill の land-route checker、plain-runner coverageです。特殊な非標準 gitdir 配置、複数行 shell、`env python ...` は従来どおり今回の明白 command 境界外です。

## 総括

gitlink の pure deletion と normal blob/tree replacement を正しく分離し、option 付きの通常 land command 迂回も閉鎖しました。指定 4 ファイルだけに未ステージ差分を残し、round 2 と同じ必須検査はすべて green です。