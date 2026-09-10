修正完了です。index・commit・network には触れず、指定4ファイルだけに未ステージ差分を残しました。

### 変更ファイル

- [tools/dev_wave_land.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py)
- [orchestrator/tests/test_dev_wave_land.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py)
- [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py)
- [orchestrator/tests/test_check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_check_docs.py)

修正前は ignored control container が検査を迂回でき、競合 loser が `rejected` になり得て、HEAD不明・partial mutation が retryable `not-landed`、gitlink wave がD16同期後も回復不能でした。これらを裁定どおり閉じ、無関係な既存 ignored cache は引き続き受理します。

主な修正内容：

- repository/request identity 検証直後にnonblocking common lockを取得
- control-plane identity/bindingをstatus前後で比較
- ignored target collision、foreign handoff/worktree collisionをmerge前に拒否
- include・worktree scopeを含むeffective configからfilter/promisor面を拒否
- HEAD観測不能・partial mutationを非retryable postcondition failureへ分類
- 元のA/T/audit列を保ったgitlink D16同期後の`already-landed`
- audit列の逆順・余分・同長別commitを独立固定
- 二wave E2Eを`winner_tip..resynced_tip`のsynthetic acceptanceへ束縛
- Stage 5用6 finding allowanceを削除
- O23だけのhelper path、Codex Stage 9文言、alternate helper/direct ff経路を機械固定

### 検査結果

- `python3 -m pytest -q orchestrator/tests/test_dev_wave_land.py`
  - 全29 node: `29 passed in 6.93s`
- `python3 -m pytest -q orchestrator/tests/test_check_docs.py`
  - 全143 node: `143 passed in 14.03s`
- 両ファイル合同
  - `172 passed in 21.10s`
- 直接runner
  - land: `29 passed`
  - check_docs: `143 passed`
- `python3 tools/run_tests.py -q orchestrator/tests/test_dev_wave_land.py orchestrator/tests/test_check_docs.py orchestrator/tests/test_plain_runner_coverage.py`
  - relevant plain-runner/meta-test範囲: `175 passed`
- `python3 tools/check_docs.py`
  - `check_docs: 違反なし`
- `python3 tools/check_codex_agents.py`
  - `OK`
- `python3 -m py_compile tools/dev_wave_land.py tools/check_docs.py`
  - rc=0
- `git diff --check`
  - rc=0

### 波及・残存リスク

- `lock-busy`はHEADをlock前に読まないため、JSONの`main_before/main_after`が`null`になります。既存型はnullableですが、外部consumerはこの値を必須扱いしない必要があります。
- HEAD不明・partial mutationはRC 25へ移るため、callerのretry判断がより保守的になります。
- Codex Skillの現行Stage 9文言がexact pinされ、command/Skill内の明白なshell形式の別land経路が拒否されます。
- startup/supervisor helperや他fixtureは変更していません。
- 同一UIDの非協調writer、悪意あるGit admin変更、cross-hostで不整合なflockは従来どおりscope外です。
- 親のmutation matrix・受入全走は未代替です。

## 総括

採用されたmust-fix 9件を指定4ファイル内で実装し、未ステージのまま保持しました。最終差分は4ファイル、`787 insertions / 147 deletions`です。