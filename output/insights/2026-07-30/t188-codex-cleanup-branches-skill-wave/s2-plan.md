指定10ファイルはすべて読み取り可能でした。以下は read-only の段2 plan です。ファイル編集、Skill 初期化、pytest 実走、branch/worktree 掃除は行っていません。

静的確認では、対象ディレクトリ `.agents/skills/cleanup-branches/` は未作成、既存 handoff はなし、作業木の差分は段1 brief の未追跡ディレクトリだけです。新規 gate なので `DW-O13` も期限内に確認済みです。

## 実装方針

実装面は次の4ファイルに閉じます。

- `.agents/skills/cleanup-branches/SKILL.md`
- `.agents/skills/cleanup-branches/agents/openai.yaml`
- `tools/check_docs.py`
- `orchestrator/tests/test_check_docs.py`

記録面の `docs/phase3.md` と `docs/worklog.md` は親だけが編集します。`.claude/commands/cleanup-branches.md` は共通 dispatcher の正本として再利用し、T-173 では変更しません。同ファイルは現在 3,959 bytes で、既存 4,000-byte 上限まで41 bytesしか余裕がありません（[check_docs.py:148](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:148)）。

## 段5 author の初期化

段4で plan v2、所有パス、mutation 登録を確定した直後、段5 author が手編集より先に initializer を実行します。initializer は既存ディレクトリを上書きせず、`SKILL.md` と `agents/openai.yaml` を生成します（[init_skill.py:271](/home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/init_skill.py:271)、[init_skill.py:287](/home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/init_skill.py:287)）。

```bash
python3 /home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  cleanup-branches \
  --path /home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.agents/skills \
  --interface 'display_name=Cleanup Branches' \
  --interface 'short_description=Izanagi の branch・worktree を安全条件付きで掃除' \
  --interface 'default_prompt=Use $cleanup-branches to safely clean up merged Izanagi branches and worktrees.'
```

`--resources` と `--examples` は渡しません。README、scripts、references、assets を作らず、最小2ファイル閉包にします。`$cleanup-branches` は shell 展開を避けるため single quote のまま渡します。

## Skill 2ファイル

### `.agents/skills/cleanup-branches/SKILL.md`

想定行構成は次のとおりです。

- `:1-4` — frontmatter は `name` と `description` のみ。

  - `name: cleanup-branches`
  - description は「安全な local branch/worktree cleanup」と、「cleanup-branches 明示起動または同等依頼で使う」trigger を含める。
  - remote branch 削除や main push には使わないことも trigger 境界に含める。

- `:6-9` — Skill の目的だけを簡潔に記述。

- `:10-21` — 「共通 dispatcher を使う」。

  1. `AGENTS.md` と `CLAUDE.md` を全文読み、クラス2起動順を実行。
  2. [cleanup-branches.md:6](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/.claude/commands/cleanup-branches.md:6) を毎回全文読み、そのまま実行。棚卸し、判定、削除順、事後検査を Skill に複製しない。
  3. command の `$ARGUMENTS` を Skill に渡された対象限定へ読み替える。
  4. command 内の `/cleanup-branches` を Codex の `$cleanup-branches` へ読み替える。
  5. command 不在・読取不能・矛盾時は推測せず停止。

- `:22-34` — Codex 固有 adapter 境界だけを保持。

  - Claude の PreToolUse hook が Codex でも発火したとは主張しない。Codex には未配線であり、`hooks/README.md` の保護面を手動で守る（[hooks/README.md:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/hooks/README.md:15)）。
  - F26 の不変条件として `git submodule deinit` を使わない（[failures.md:332](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/failures.md:332)）。
  - F51 の不変条件として cwd 固定時は自分が居る worktree のディレクトリ削除・prune を行わず、残りを引き渡す（[failures.md:947](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/failures.md:947)）。
  - remote branch 削除と main push は行わず、人間へ対象を列挙する。
  - 自己改善は command の発火条件に従い、`docs/skill-self-improvement.md` を再利用する。

F26/F51 は削除手順全体を再掲せず、「破ってはいけない安全意味論」だけを adapter に残します。

### `.agents/skills/cleanup-branches/agents/openai.yaml`

生成結果を次の exact bytes に固定します。

```yaml
interface:
  display_name: "Cleanup Branches"
  short_description: "Izanagi の branch・worktree を安全条件付きで掃除"
  default_prompt: "Use $cleanup-branches to safely clean up merged Izanagi branches and worktrees."
```

`short_description` は36文字で25–64文字制約内です（[openai_yaml.md:30](/home/SFC/tanab/.codex/skills/.system/skill-creator/references/openai_yaml.md:30)）。手編集せず、Skill 本文確定後に同じ `--interface` 値で `generate_openai_yaml.py` を再実行します。

## `tools/check_docs.py`

既存 helper [check_docs.py:1433](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1433) は、exact file closure、regular-file/UTF-8、byte/line budget、frontmatter、必須 literal、生成 metadata bytes を既に共通検査できます。helper 自体は変更しません。

[check_docs.py:187](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:187) の rulings 定数群の直後へ追加します。

```python
CODEX_CLEANUP_BRANCHES_SKILL_LIMITS = {
    ".agents/skills/cleanup-branches/SKILL.md": TextLimit(3_000, 400),
    ".agents/skills/cleanup-branches/agents/openai.yaml": TextLimit(500, 160),
}
CODEX_CLEANUP_BRANCHES_SKILL_FILES = frozenset(
    CODEX_CLEANUP_BRANCHES_SKILL_LIMITS
)
```

必須 literal は短い単語ではなく、可能な限り意味を含む句で固定します。

- `AGENTS.md`
- `CLAUDE.md`
- `.claude/commands/cleanup-branches.md`
- `手順を本 Skill の記憶や要約で代用しない`
- `command の \`$ARGUMENTS\` は本 Skill に渡された対象限定と読み替える`
- `command 内の \`/cleanup-branches\` は Codex の \`$cleanup-branches\` と読み替える`
- `クラス 2`
- `hooks/README.md`
- `PreToolUse hooks が Codex でも発火したとは主張しない`
- `Codex には未配線`
- `F26`
- `` `git submodule deinit` は使わない ``
- `F51`
- `自分が居る worktree の削除と prune を行わず`
- `リモートブランチの削除と main の push は行わず`
- `docs/skill-self-improvement.md`

同所へ exact `CODEX_CLEANUP_BRANCHES_OPENAI_YAML` も追加します。

最後に [check_docs.py:1780](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/tools/check_docs.py:1780) の既存2回の `_check_codex_skill_guard` 呼び出しに、`cleanup-branches` の3回目を追加します。

## `orchestrator/tests/test_check_docs.py`

変更点は既存 rulings Skill の型をそのまま第三 Skill へ適用します。

- [test_check_docs.py:267](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:267) — synthetic baseline に cleanup Skill の2ファイルを生成。SKILL 本文は新 literal tuple から合成し、metadata は checker 定数を使用。

- [test_check_docs.py:1812](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:1812) — `_mutate_command_guard` に以下の負例を追加。

  1. `codex_cleanup_skill_deleted` — `SKILL.md` を削除。
  2. `codex_cleanup_skill_extra_file` — `README.md` を追加。
  3. `codex_cleanup_skill_name_changed` — frontmatter name を変更。
  4. `codex_cleanup_skill_adapter_deleted` — F51 の長い安全 literal を除去。
  5. `codex_cleanup_skill_openai_changed` — `display_name` を1 byte相当変更。

- [test_check_docs.py:1895](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:1895) — 上記5件を `_COMMAND_GUARD_CASES` へ追加。

- [test_check_docs.py:1951](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:1951) — finding を次の語で固定。

  - 必須 file が不在
  - 予算未登録実体
  - `name は 'cleanup-branches' 必須`
  - `Codex adapter 契約がない`
  - `生成済み Skill interface 契約と不一致`

- [test_check_docs.py:2082](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/orchestrator/tests/test_check_docs.py:2082) の rulings pin の直後 — `test_codex_cleanup_branches_skill_contract_pins_exact_surface` を追加。checker/fixtureを同時に弱める自己整合を避けるため、テスト側の literal で次を独立固定します。

  - exact 2-file set
  - 上記 adapter literal tuple 全体
  - exact `openai.yaml` bytes

## Mutation 事前登録

段4で、実装開始前に次を登録します。各変異は期待 finding を単一理由にします。

| ID | 変異 | 期待する kill |
|---|---|---|
| M1 | `SKILL.md` または `openai.yaml` を1件削除 | 必須 file 不在 |
| M2 | Skill root に README / nested file を追加 | 予算未登録実体 |
| M3 | name、frontmatter key集合、description空を各単独変更 | frontmatter/name/description finding |
| M4a–g | `$ARGUMENTS`、invocation変換、クラス2、hook、remote/main push、F26、F51 の各 literal を単独除去 | adapter 契約 finding |
| M5 | metadata の display name/default prompt/newline を単独変更 | interface exact-bytes finding |
| M6 | Skill または metadata を budget +1 byte にする | byte budget finding |
| M7 | cleanup の guard 呼び出しを削除 | 5件の positive-control 負例が赤にならず、テストが失敗 |
| M8 | checker literal/file set と synthetic fixture を同時縮小 | 独立 surface pin が失敗 |
| M9 | 正しい2ファイル・全 literal・exact metadata | baseline green。過剰拒否の正例 |

実変異は統合 commit 後だけに行い、`DW-O15` / `DW-M07` / `DW-O19` の anchor・復元契約に従います（[mutation.md:5](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/dev-wave/mutation.md:5)）。

## 記録と所有境界

段5 author の所有は上記4実装ファイルだけです。repo-scoped Skill 2ファイルは実行設定として実装面に含めますが、`docs/**` は編集せず、commit もしません。これは [workers.md:26](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/dev-wave/workers.md:26) の所有境界に合わせます。

親は統合後に次を行います。

- [phase3.md:514](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/phase3.md:514) — T-058 に `safety_gate_changed` の発火を記録。coverage 実測をしていなければ、その旨だけ記録。
- [phase3.md:515](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/phase3.md:515) — T-059 に validator/rejection gate 変更と mutation 実績を、実走値確定後に記録。
- [phase3.md:517](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/phase3.md:517) — T-173 完了項を T-172 の手前へ追加。
- [worklog.md:968](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-cleanup-branches-skill/docs/worklog.md:968) — 末尾を再読し、その時点の次の連番で T-173 entry を追記。初期化、4実装ファイル、実走した検査、mutation結果、親/子工数、push未実施、実 branch/worktree cleanup 未実施を記録。未実走値の placeholder は作らない。

## 実装・検査順

1. 親が段4で plan v2、所有、mutation を確定。
2. 段5 author が initializer を実行。
3. author が Skill 本文、checker、tests を編集。
4. `generate_openai_yaml.py` で metadata を同じ interface 値から再生成。
5. author が quick validation。

```bash
python3 /home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/cleanup-branches
```

6. author が focused tests。

```bash
pytest -q \
  orchestrator/tests/test_check_docs.py::test_synthetic_repo_baseline_clean \
  orchestrator/tests/test_check_docs.py::test_command_docs_guard_positive_controls \
  orchestrator/tests/test_check_docs.py::test_codex_cleanup_branches_skill_contract_pins_exact_surface \
  orchestrator/tests/test_check_docs.py::test_real_repo_clean
```

7. author は差分と実走 nodeid を親へ返し、docs/commit は行わない。
8. 親が統合し、phase/worklog を編集。
9. 親が統合状態で全対象検査。

```bash
python3 /home/SFC/tanab/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/cleanup-branches
pytest -q orchestrator/tests/test_check_docs.py
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
git diff --check
```

10. 親がコード・Skill・tests・phase/worklog を同一 commit にし、commit 後に実走。

```bash
python3 tools/check_ai_provenance.py
```

ここで列挙した検査は親が実装後に走らせる受入項目です。本段2では静的読解だけを行っており、将来の pytest/check 緑は主張していません。

## 総括

**GO。** 既存の汎用 Skill guard を第三 Skillへ追加するだけで、共通 dispatcherを複製せず実装できます。最大のリスクは literal guard が「文言の存在」は証明しても実行時意味論までは証明しない点です。長い安全句、独立 surface pin、F26/F51 個別 mutation、段3の敵対レビューで補強してください。