単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2814-cleanup-command

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する (射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/prompt-author.md` — **段 5 の実装子契約 (「必ず守る点」1〜11 と出力形式) を本 fix でも全文継承する。** 読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/prompt-fix2.md` — 前巡 (fix 2) の指示。読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/artifacts/dev-wave-t2814-cleanup-command/dev-wave-t2814-cleanup-command-fix-e20a9ccd5c495cdf2a2bafadb1b233c760851250e15699a2be44b2134dd85151/attempt-0001.output.md` — 前巡 (fix 2) の報告 (予算ちょうどで `test_cleanup_command_leading_space_h2_is_rejected` が 2 件違反になり停止した)。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/.claude/commands/cleanup-branches.md` — **fix 3 後の新本文の正本 (読むだけ、触らない)。** HEAD `8901d6b62`、6,201 bytes (余白 3)。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/tools/check_docs.py` — **編集対象** (tracked で HEAD の file だが本巡の編集対象である)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/orchestrator/tests/test_check_docs.py` — **編集対象** (同上)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl` (branch `dev-wave-t2814-unit-fix3`、HEAD `8901d6b62` = fix 1 の pin 追随 (47e1730b7) + 親の docs fix 2 (b36da2b09) + 親の docs fix 3 (8901d6b62)) とする。
**注意:** HEAD の pin 側 (check_docs 定数・fixture) は fix 1 時点 (本文 6,200、sha 664815df…) のままである。前巡 (fix 2) の作業は別 branch の終端 commit にあり本 HEAD には入っていない。

## この段の仕事 (fix 3)

親が command 本文を fix 2 (§2「削除直前に status 空と非施錠を再確認。」) + fix 3 (§5「remote branch 削除と main の push は行わず」= 助詞 1 語削除) の状態、6,201 bytes へ確定した。
SKILL.md は fix 1 のまま (3,060 bytes、sha `3cf0344d…`)。pin 側を新本文へ追随させる:

1. `tools/check_docs.py` — `CLEANUP_COMMAND_SHA256` を HEAD の command 本文 (6,201 bytes) の sha256 hex に置換。`CODEX_CLEANUP_BRANCHES_SKILL_SHA256` (3cf0344d…) と他は変えない。
2. `orchestrator/tests/test_check_docs.py` — (a) `_SYNTHETIC_CLEANUP_COMMAND` の §2 該当行 (fix 2) と §5 該当行 (fix 3) を新本文と byte 一致するよう更新 (独立 literal、file を読んで代入しない)。(b) `_EXPECTED_CLEANUP_COMMAND_SHA256` を新 sha へ。(c) `test_cleanup_command_budget_is_pinned_and_enforced` の bytes assert 2 箇所を `6_200` → `6_201` へ、超過入力の padding を `"x" * 4` → `"x" * 3` へ (6,205 bytes の拒否と期待メッセージは維持)。(d) 旧本文断片 (「§1 の status 空を再確認」「remote branch の削除と」) に依存する test・helper があれば追随、無ければ「無い」と報告。`_make_cleanup_command_mutation_budget_neutral` の slack `discard_changes: true` は本文に 1 回のまま (helper 不変)。

**既存テストの期待値を変更しない** (上記 2(b)(c) と 2(d) の実測で判明した箇所だけが例外)。反転・緩和・skip・削除は禁止。赤なら nodeid と理由を報告して止める。

実走 (段 5 契約 6 と同じ経路): `-k "cleanup or codex_skill or skill_guard or command_budget or command_interface"` の焦点 (前巡で赤だった `test_cleanup_command_leading_space_h2_is_rejected` が緑に戻ることを明記) → 緑なら `test_check_docs.py` 全件 → `python3 tools/check_docs.py` (変更前は「whole-file SHA-256 が契約と不一致」1 件の赤 = 親の実測、変更後は「違反なし」のはず) → `git diff --check`。meta-test (`test_plain_runner_coverage.py`、`test_check_subprocess_bytecode_guard.py`) も走らせる。

規模の目安: check_docs.py ±2 行、test_check_docs.py ±8 行。超えるなら理由を報告に書く。

## 出力形式

段 5 と同じ (`## 変更の要約` / `## byte 一致の確認` / `## 既存 test 追随の有無` / `## 実走結果` / `## 波及` / `## 未了・懸念` / `## 総括`)。
