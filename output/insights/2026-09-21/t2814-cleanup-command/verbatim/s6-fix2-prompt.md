単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2814-cleanup-command

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する (射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/prompt-author.md` — **段 5 の実装子契約 (「必ず守る点」1〜11 と出力形式) を本 fix でも全文継承する。** 読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/prompt-fix1.md` — 前巡 (fix 1) の指示。読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/s6-fix1.md` — 前巡 (fix 1) の報告。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/.claude/commands/cleanup-branches.md` — **fix 2 後の新本文の正本 (読むだけ、触らない)。** HEAD `b36da2b09`、6,204 bytes (予算 6,204 ちょうど。check_docs の判定は `size > max` なので緑)。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/tools/check_docs.py` — **編集対象** (tracked で前巡の差分を含む HEAD の file だが、本巡の編集対象である)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/orchestrator/tests/test_check_docs.py` — **編集対象** (同上)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl` (branch `dev-wave-t2814-unit-fix2`、HEAD `b36da2b09` = fix 1 の pin 追随 (47e1730b7) + 親の docs fix 2 (b36da2b09)) とする。

## この段の仕事 (fix 2)

親が command 本文の §2 高い条件の 1 文を「削除直前に §1 の status 空を再確認。」→「削除直前に status 空と非施錠を再確認。」へ変えた (+4 bytes、6,200 → 6,204)。
SKILL.md は変わっていない (3,060 bytes、sha `3cf0344d…` のまま)。command 本文の bytes と sha256 が変わったので、pin 側を再追随させる:

1. `tools/check_docs.py` — `CLEANUP_COMMAND_SHA256` を HEAD の command 本文 (6,204 bytes) の sha256 hex に置換。`CODEX_CLEANUP_BRANCHES_SKILL_SHA256` と他は変えない。
2. `orchestrator/tests/test_check_docs.py` — (a) `_SYNTHETIC_CLEANUP_COMMAND` の §2 該当行を新本文と byte 一致するよう更新 (独立 literal、file を読んで代入しない)。(b) `_EXPECTED_CLEANUP_COMMAND_SHA256` を新 sha へ。(c) `test_cleanup_command_budget_is_pinned_and_enforced` の bytes assert 2 箇所を `6_200` → `6_204` へ、超過入力の padding を `"x" * 4` → 6,205 bytes になる形へ (本文 6,204 + `"\n"` で 6,205 なので `"x" * 0` か、`+ "\n"` だけの形。`assert len(oversized.encode("utf-8")) == 6_205` と上限 +1 の拒否・期待メッセージは維持)。(d) 旧本文断片 (「§1 の status 空を再確認」) に依存する test・helper があれば追随、無ければ「無い」と報告。`_make_cleanup_command_mutation_budget_neutral` の slack `discard_changes: true` は本文に 1 回のまま (helper 不変)。
   **注意:** 本文が予算ちょうど (余白 0) になったので、`_make_cleanup_command_mutation_budget_neutral` を使わずに本文へ bytes を足す mutation test が「予算超過」の別理由で赤にならないか (test の期待違反件数が 1 件のまま成り立つか) を全件走で確かめ、赤があれば nodeid と理由を報告して止める (テストの期待値は変えない。期待値が誤りと考える場合も実装を変えず報告する)。

**既存テストの期待値を変更しない** (上記 2(b)(c) と 2(d) の実測で判明した箇所だけが例外)。反転・緩和・skip・削除は禁止。

実走 (段 5 契約 6 と同じ経路): `-k "cleanup or codex_skill or skill_guard or command_budget or command_interface"` の焦点 → 緑なら `test_check_docs.py` 全件 → `python3 tools/check_docs.py` (変更前は「whole-file SHA-256 が契約と不一致」1 件の赤 = 親の実測、変更後は「違反なし」のはず) → `git diff --check`。meta-test (`test_plain_runner_coverage.py`、`test_check_subprocess_bytecode_guard.py`) も走らせる。

規模の目安: check_docs.py ±2 行、test_check_docs.py ±6 行。超えるなら理由を報告に書く。

## 出力形式

段 5 と同じ (`## 変更の要約` / `## byte 一致の確認` / `## 既存 test 追随の有無` / `## 実走結果` / `## 波及` / `## 未了・懸念` / `## 総括`)。
加えて `## 余白 0 の影響` に、上記 2 の注意点 (予算ちょうどで helper 非利用の mutation test が別理由の赤にならないか) の実測結果を 1〜3 行で書く。
