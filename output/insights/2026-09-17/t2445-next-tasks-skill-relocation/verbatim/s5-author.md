## 変更した file と anchor (file:line、何を足したか)

編集は指定の 2 ファイルだけ。commit・git add・branch 操作はしていません。

- `tools/check_docs.py:732`：next-tasks の予算、2 file 集合、23 literal、YAML 契約を追加。
- `tools/check_docs.py:874`：必須 H3 に `next-tasks` を追加。
- `tools/check_docs.py:6596`：rulings と cleanup-branches の間に guard 呼出しを追加。
- `orchestrator/tests/test_check_docs.py:972`：合成 skill 2 file を追加。
- 同 `:1096`：合成 self_doc に H3 を追加。
- 同 `:2559`：command 現物 byte pin を `26_950` に更新。
- 同 `:6976`、`:7425`：負例 5 case を追加。
- 同 `:7470`、`:7603`、`:7878`：case 一覧、needle、登録確認へ追加。期待 finding 件数は既定の各 1 件。
- 同 `:9864`：手書き期待値による独立 pin test を追加。

既存 3 skill の定数・呼出し・pin、guard 本体、`SELF_LIMITS`、`COMMAND_LIMITS`、`COMMAND_INTERFACES` は変更していません。

## 受理集合の変化 (変更前の受理・拒否 → 変更後、2 文に分けて正例を 1 つ添える)

変更前は `next-tasks` H3 がない契約文書を受理し、ある文書を孤児 H3 として拒否していましたが、変更後は当該 H3 を必須として受理します。

変更前は next-tasks skill を検査していませんでしたが、変更後は指定 2 file の閉包・予算・interface・literal を検査し、正例として親 docs commit の現物は実 repo 検査を通過しました。

## 実走結果 (baseline / 変更後の `_run` 件数、`check_docs.py` の rc と出力)

| 実走 | baseline | 変更後 |
|---|---|---|
| 指定 `_run` コマンド | rc=1、開始前拒否、件数未取得 | rc=1、開始前拒否、件数未取得 |
| `python3 tools/check_docs.py` | rc=1 | rc=0 |

`_run` は両方とも次の例外で停止しました。テスト結果の `N passed, M failed` は出力されていません。

```text
GrowthTestHoldBypassRefused: IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1 {"node_id":"test_check_docs.py::*","release_env":"IZANAGI_RUN_GROWTH_HELD_TESTS","release_token":"explicit-user-command"}
```

baseline の checker 出力：

```text
check_docs: 1 件の違反
  - docs/skill-self-improvement.md: dispatch 契約にない孤児 H3 — ['next-tasks']
```

変更後の checker 出力：

```text
check_docs: 違反なし
```

追加の検算は成功しました。

- 23 literal すべてが現物 SKILL.md に存在。
- YAML は末尾 LF を含め現物 208 bytes と完全一致。
- SKILL.md は 5,458 bytes、最長行 223 chars。
- command 現物は 26,950 bytes。
- 両編集ファイルの AST 解析と `git diff --check` が成功。

## 波及の静的列挙 (所有外 caller・共有 fixture・consumer test)

- 所有外 consumer：`tools/dev_waves/checker.py:351`、`tools/dev_waves/daemon.py:232` が checker の実行指定を識別。呼出し契約の変更はありません。
- 共有 fixture：`orchestrator/tests/test_check_docs.py:814` の `_write_command_guard_docs` を通じ、`:1242` の `_build_min_repo` 利用テストへ新 skill と H3 が供給されます。
- 見出し集合の派生：`tools/check_docs.py:877` の `_SELF_SECTIONS` に新 H3 が入り、`:942` の段 8 preflight と `:3465` の「全節」展開へ伝播します。
- consumer test：`test_dev_wave_dispatch_accepts_self_all_sections`（`:3702`）、guard positive controls（`:9994`）、新独立 pin（`:9864`）、登録確認（`:7873`）が関連します。
- 実走阻害：`orchestrator/tests/growth_test_holds.py:790` の拒否が `_run` より先に発生しました。解除設定や test harness は変更していません。

## 変異 matrix への anchor (裁定の M0〜M6 それぞれの正確な file:line と old 文字列)

すべて `tools/check_docs.py` の変更後行番号です。変異 matrix 自体は未実走です。

| ID | anchor | old 文字列 | 予定変異 |
|---|---|---|---|
| M0 | `:732` | `# next-tasks の repo-scoped Skill 契約を登録する。` | 末尾句点のみ変更 |
| M1 | `:874` | `3: {"dev-wave", "cleanup-branches", "rulings", "next-tasks"},` | `"next-tasks"` を除去 |
| M2 | `:6596` | 下記呼出し全文 | 呼出しを除去 |
| M3 | `:734` | `".agents/skills/next-tasks/SKILL.md": TextLimit(5_460, 400),` | `5_460` → `546_000` |
| M4 | `:764` | `  display_name: "Next Tasks"` | `Next Tasks` → `Next Taskx` |
| M5 | `:739` | `    "AGENTS.md",` | 当該 tuple 要素を除去 |
| M6 | `:737` | `CODEX_NEXT_TASKS_SKILL_FILES = frozenset(CODEX_NEXT_TASKS_SKILL_LIMITS)` | 期待集合から YAML path を除去 |

M2 の exact old：

```python
    _check_codex_skill_guard(
        findings,
        skill_name="next-tasks",
        limits=CODEX_NEXT_TASKS_SKILL_LIMITS,
        expected_files=CODEX_NEXT_TASKS_SKILL_FILES,
        literals=CODEX_NEXT_TASKS_SKILL_LITERALS,
        openai_yaml=CODEX_NEXT_TASKS_OPENAI_YAML,
    )
```

独立 pin の node は `orchestrator/tests/test_check_docs.py::test_codex_next_tasks_skill_contract_pins_exact_surface`。負例 node は同ファイルの `test_command_docs_guard_positive_controls[case]` で、追加した 5 case の ID はすべて ASCII です。

## 総括

指定実装は完了し、実 repo の `check_docs.py` は rc=0 です。テストは hold による開始前拒否のため、**実装済み・テスト未実走**として引き継ぎます。親での関連テストと M0〜M6 の変異実走が残っています。
