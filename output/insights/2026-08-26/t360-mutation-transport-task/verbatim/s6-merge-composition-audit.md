## 合成判定

- `tools/check_docs.py` — **intact**
  - main 側の `Iterable` import は保持されています。[tools/check_docs.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/check_docs.py:24)
  - carry 不一致の既知集合、期待総数 `4`、母数下限 `404_326` がすべて残っています。[tools/check_docs.py:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/check_docs.py:256) [tools/check_docs.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/check_docs.py:264) [tools/check_docs.py:267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/check_docs.py:267)
  - carry の逐次走査、同一 ID 検査、既知集合照合、母数下限検査も保持されています。[tools/check_docs.py:1989](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/check_docs.py:1989) [tools/check_docs.py:2249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/check_docs.py:2249) [tools/check_docs.py:2427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/check_docs.py:2427)
  - wave 側の alias、container、comprehension、default capture を含む taint 判定も保持されています。[tools/check_docs.py:3732](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/check_docs.py:3732) [tools/check_docs.py:3828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/check_docs.py:3828)
  - main は carry 検査領域、wave は dispatch inventory 領域を変更しており、同じ関数や定数を奪い合っていません。

- `orchestrator/tests/test_check_docs.py` — **intact**
  - main 側の既知 carry fixture、既知集合の固定値検査、母数下限の正例・負例テストが存在します。[test_check_docs.py:422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_check_docs.py:422) [test_check_docs.py:11031](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_check_docs.py:11031) [test_check_docs.py:11223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_check_docs.py:11223)
  - wave 側の container unpack、RHS subtree、各 comprehension、function default capture のテストが存在します。[test_check_docs.py:2687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_check_docs.py:2687) [test_check_docs.py:2705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_check_docs.py:2705) [test_check_docs.py:2742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_check_docs.py:2742)
  - real dispatcher の期待写像には `mutation` と `generic` が明記されています。[test_check_docs.py:2771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_check_docs.py:2771)

- `docs/pegasus-runbook.md` — **intact**
  - task 表には `tests`、`provenance`、`mutation`、`generic` の4行が揃っています。[pegasus-runbook.md:603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/docs/pegasus-runbook.md:603)
  - wave 側の `generic` と `mutation` の説明も保持されています。[pegasus-runbook.md:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/docs/pegasus-runbook.md:570) [pegasus-runbook.md:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/docs/pegasus-runbook.md:577)
  - main 側の attempt pair と ASCII nodeid の注意も保持されています。[pegasus-runbook.md:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/docs/pegasus-runbook.md:1191)

## 両側の意図の対照表

| 対象 | main 側の意図 | wave 側の意図 | merge 後 |
|---|---|---|---|
| checker import・定数 | `Iterable`、既知 carry 集合、`EXPECTED_KNOWN_CARRY_ID_MISMATCHES=4`、`MIN_EXPECTED_CARRY_REFERENCE_COUNT=404_326` | この領域への競合変更なし | 両立 |
| checker ロジック | carry の同一 ID、既知例外、母数下限を検査 | `TASKS` alias、container unpack、comprehension、default capture を taint として追跡 | 両立 |
| checker テスト | carry fixture、固定値、母数下限、異常系を追加 | alias・container・comprehension 回帰と real dispatcher 写像を追加 | 両立 |
| runbook | attempt pair と ASCII nodeid の運用注意を追加 | `mutation`、`generic` の task と説明を追加 | 両立 |
| task 写像 | 既存 `tests`、`provenance` を維持 | `mutation`、`generic` を追加 | runbook と dispatcher が同じ4要素 |

## 直した内容

なし。3 file とも合成は intact で、編集、`git add`、commit、`git merge --continue` は行っていません。

## check_docs 実行結果

- `python3 tools/check_docs.py`
  - rc: `0`
  - finding: `0件`
  - 出力: `check_docs: 違反なし`
- checker の抽出関数による実写像:
  - runbook: `tests` / `provenance` / `mutation` / `generic`
  - dispatcher: 同じ4要素
  - findings: `[]`
- AST parse:
  - `tools/check_docs.py`: 成功
  - `orchestrator/tests/test_check_docs.py`: 成功
- 対象3 file の `git diff --cached --check`: rc `0`
- conflict marker: 検出なし

## 残余

pytest は実行していません。したがって追加テストの実行結果は未確認であり、確認済みなのはコード対照、AST parse、`check_docs` 実走、実写像抽出までです。

## 総括

auto-merge 後も main と wave の意図は両方保持されています。合成破損は見つからず、修正は不要です。