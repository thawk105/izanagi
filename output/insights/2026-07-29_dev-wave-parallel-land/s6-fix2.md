5件の採用 residual を閉じました。round 2 差分は指定4ファイルだけに未ステージで残し、index・commit・network・docsには触れていません。

### 変更内容

- [tools/dev_wave_land.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:805)
  - collapsed `!! cache/` を sibling 衝突と誤認しない精密検査
  - merge直前の full control snapshot 再検証
  - A/T両gitlink mapと、削除済みgitlinkのworktree・`.git/modules/...`残存検査
- [orchestrator/tests/test_dev_wave_land.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py:355)
  - ignored sibling正例、exact/ancestor負例
  - handoff/worktree置換seamとmain不変検査
  - gitlink削除・metadata-only残存・同一evidence回復検査
  - subprocess acceptance receipt E2E
- [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:241)
  - `$`有無、`python`/`python3`、`tools/`/`./tools/`を検出
  - `git -C <main> merge ... --ff-only`とoption順序変種を検出
  - 現行DW-S09 acceptance→計測→O23 literalをexact pin
- [orchestrator/tests/test_check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_check_docs.py:2321)
  - 構文変種の独立負例、通常prose正例、S09 literal削除負例

round 2 差分は `431 insertions / 57 deletions` です。

### Red / Green

- fix-1基準: `172 passed`
- test-only焦点走行: `5 failed, 69 passed`
  - sibling fixtureの最初の1件は共有excludeによる`git add`拒否だったため、`git add -f`へ是正
  - 是正後、sibling nodeは期待どおり旧実装の過剰collisionで `1 failed`
  - gitlink metadata残存、merge直前replacement、checker構文変種、S09順序literalも期待どおり赤
- 最終:
  - land pytest: `32 passed in 8.17s`
  - docs pytest: `145 passed in 14.80s`
  - 合同: `177 passed in 22.69s`
  - direct land runner: `32 passed, 0 failed`
  - direct docs runner: `145 passed, 0 failed`
  - plain-runner/meta: `180 passed in 4.80s`
  - `tools/check_docs.py`: `check_docs: 違反なし`
  - `tools/check_codex_agents.py`: `OK`
  - 4ファイルの`py_compile`: rc=0
  - `git diff --check`: rc=0

### 波及と残存リスク

living consumerはDW-S09/DW-O23、Claude command、Codex Skill、およびplain-runner coverageです。いずれも変更せず検査済みです。caller側では、削除gitlinkのD16 cleanupがworktreeだけでなく標準の`.git/modules/<path>`まで必要になります。

残存するscope外リスクは、最終snapshot直後に介入する非協調same-UID writer、特殊な手動配置gitdir、および`env python ...`や複数行shellなど「明白なcommand」外の表記です。acceptance receiptはsynthetic E2Eで実行接続を固定しますが、helper自身がreceiptを認証しない既裁定境界は維持しています。

## 総括

採用された5 residualを指定4ファイル内で閉鎖し、全必須検査をgreenにしました。round 2変更は未ステージ、commitなし、所有外変更なしです。