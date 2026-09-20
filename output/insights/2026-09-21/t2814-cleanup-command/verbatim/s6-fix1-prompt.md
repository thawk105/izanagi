単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2814-cleanup-command

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する (射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/prompt-author.md` — **段 5 の実装子契約 (「必ず守る点」1〜11 と出力形式) を本 fix でも全文継承する。** 読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/s5-author.md` — 段 5 author (自分の前巡) の報告。読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/s6-review.md` — 段 6 レビュー (must-fix 1 = §3 の検算条件、nit 1)。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/.claude/commands/cleanup-branches.md` — **fix 1 後の新本文の正本 (読むだけ、触らない)。** HEAD `82c53b98d`、6,200 bytes。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/.agents/skills/cleanup-branches/SKILL.md` — **fix 1 後の新 overlay の正本 (読むだけ、触らない)。** 3,060 bytes。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/tools/check_docs.py` — **編集対象** (tracked で前巡 (03d416070) の差分を含む HEAD の file だが、本巡の編集対象である)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/orchestrator/tests/test_check_docs.py` — **編集対象** (同上)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl` (branch `dev-wave-t2814-unit-fix1`、HEAD `82c53b98d` = 前巡の pin 追随 (92263e53e) + 親の docs fix 1 (82c53b98d)) とする。

## この段の仕事 (fix 1)

段 6 レビューの must-fix 1 を親が docs 側で直した (§3 の 1 文を「`ls-files -o` の list 数を tar の非 dir entry 数が下回れば撤去しない (F1034)」へ、§4 の 1 行を縮約、
SKILL.md overlay の「entry 数照合」→「非 dir entry 数照合」)。本文の bytes と sha256 が変わったので、前巡と同じ pin 側 2 file を新本文へ再追随させる:

1. `tools/check_docs.py` — `CLEANUP_COMMAND_SHA256` を HEAD の command 本文 (6,200 bytes) の sha256 hex に、`CODEX_CLEANUP_BRANCHES_SKILL_SHA256` を HEAD の SKILL.md (3,060 bytes) の sha256 hex に置換。他は変えない。
2. `orchestrator/tests/test_check_docs.py` — (a) `_SYNTHETIC_CLEANUP_COMMAND` / `_SYNTHETIC_CLEANUP_SKILL` の該当行 (§3 の 1 文・§4 の 1 行・overlay の 1 行) を新本文と byte 一致するよう更新 (独立 literal、file を読んで代入しない)。(b) `_EXPECTED_CLEANUP_COMMAND_SHA256` / `_EXPECTED_CLEANUP_SKILL_SHA256` を新 sha へ。(c) `test_cleanup_command_budget_is_pinned_and_enforced` の bytes assert 2 箇所を `6_201` → `6_200` へ、超過入力の padding を `"x" * 3` → `"x" * 4` へ (6,205 bytes の拒否と期待メッセージは維持)。(d) 旧本文断片 (「list と entry 数が一致」「cleanup 前の status を保存し」「entry 数照合)」) に依存する test・helper があれば追随、無ければ「無い」と報告。`_make_cleanup_command_mutation_budget_neutral` の slack `discard_changes: true` は本文に 1 回のまま (helper 不変)。

**既存テストの期待値を変更しない** (上記 2(b)(c) と 2(d) の実測で判明した箇所だけが例外)。反転・緩和・skip・削除は禁止。赤なら実装側 (literal・定数) が誤りとして直す。期待値が誤りと考える場合は実装を変えず報告して止める。

実走 (段 5 契約 6 と同じ経路): `-k "cleanup or codex_skill or skill_guard or command_budget or command_interface"` の焦点 → 緑なら `test_check_docs.py` 全件 → `python3 tools/check_docs.py` (変更前は「whole-file SHA-256 が契約と不一致」2 件の赤 = 親の実測、変更後は「違反なし」のはず) → `git diff --check`。meta-test (`test_plain_runner_coverage.py`、`test_check_subprocess_bytecode_guard.py`) も走らせる。

規模の目安: check_docs.py ±4 行、test_check_docs.py ±10 行。超えるなら理由を報告に書く。

## 出力形式

段 5 と同じ (`## 変更の要約` / `## byte 一致の確認` / `## 既存 test 追随の有無` / `## 実走結果` / `## 波及` / `## 未了・懸念` / `## 総括`)。
加えて `## 所見対応表` に、段 6 の所見 1 (must-fix) と所見 2 (nit) について、本 fix で closed / partial / regressed のどれか、根拠 (file:行) と共に 1 行ずつ書く
(所見 2 は docs の対応表・worklog で記録対応するので pin 側には作業が無いはず — その場合「pin 側の作業なし」と書く)。
