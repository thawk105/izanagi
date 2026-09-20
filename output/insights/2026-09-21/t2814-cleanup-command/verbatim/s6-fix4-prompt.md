単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2814-cleanup-command

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する (射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/prompt-author.md` — **段 5 の実装子契約 (「必ず守る点」1〜11 と出力形式) を本巡でも全文継承する。** 読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/prompt-fix3.md` — 前巡 (fix 3) の指示。読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/artifacts/dev-wave-t2814-cleanup-command/dev-wave-t2814-cleanup-command-fix-1d429a0e0ed992665b8110857ee4400545d530e6a4ec70c98fdc13238ac132a4/attempt-0001.output.md` — 前巡 (fix 3) の報告 (launcher に未受理。内容は本巡が監査する)。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/.claude/commands/cleanup-branches.md` — 新本文の正本 (読むだけ、触らない)。6,201 bytes。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/tools/check_docs.py` — 編集対象 (前巡の差分を HEAD に含む)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/orchestrator/tests/test_check_docs.py` — 編集対象 (同上)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl` (branch `dev-wave-t2814-unit-fix4`、HEAD `d258b0597` = 前巡 fix 3 の終端 commit。親 docs `8901d6b62` の上に pin 追随の差分が 1 commit 乗っている) とする。

## 最重要の禁止 (前 2 巡が成果物を受理されなかった原因)

**`orchestrator/tests/test_check_docs.py` を `cat` や広い `sed -n` で全文・大範囲出力してはならない。** 同 file の 5749 行と 5772 行に非 NFC の Unicode (test data) が含まれ、
launcher は子の stdout JSONL を「NFC 必須」で検証するため、その行を含む出力が 1 度でも stdout に出ると evidence が invalid になり、**報告全体が未受理になる** (前 2 巡で実測)。
読むときは `grep -n` / `rg -n` で位置を出し、`sed -n 'a,bp'` の範囲は **5749・5772 行を含めず**、1 command の出力を 200 行以内にする。`git diff` / `git show` も
同 file の該当行を含む hunk を出さない (本巡の差分は 570〜700 行付近と 9,940〜9,960 行付近だけのはず)。

## この段の仕事 (fix 4 = 前巡の監査と再検証)

前巡 (fix 3) は HEAD `d258b0597` に「`CLEANUP_COMMAND_SHA256` を c8db749b… へ、`_SYNTHETIC_CLEANUP_COMMAND` の §2・§5 該当行、`_EXPECTED_CLEANUP_COMMAND_SHA256`、
bytes assert 2 箇所 6_201、padding `"x" * 3`」を commit したが、launcher に未受理 (上記の非 NFC 出力が原因) なので、報告が正規に受理されていない。本巡は:

1. **監査:** `git diff 8901d6b62 HEAD --stat` と、同 range の `tools/check_docs.py` の差分、`orchestrator/tests/test_check_docs.py` の差分 (該当 hunk だけ。5749/5772 行を含めない) を読み、
   前巡の変更が指示 (prompt-fix3 の 1・2) と一致するか、余計な変更が無いかを確かめる。
2. **byte 一致の確認:** 一時 script (repo 内、終了後削除) で `HEAD の command 本文 sha256 == CLEANUP_COMMAND_SHA256 == _EXPECTED_CLEANUP_COMMAND_SHA256`、
   `_SYNTHETIC_CLEANUP_COMMAND == command 本文`、`len == 6_201`、SKILL 側も同様 (3,060、3cf0344d…) を出力する (出力は数値・真偽・sha だけ。本文を print しない)。
3. **再検証 (実走):** 段 5 契約 6 の経路で `-k "cleanup or codex_skill or skill_guard or command_budget or command_interface"` → `test_check_docs.py` 全件 → `python3 tools/check_docs.py` →
   `git diff --check` → meta-test 2 file。**pytest の出力は `-q -rf` のまま** (失敗時の assertion 本文は出るが、5749/5772 行の test data を含む node が失敗しない限り安全)。
4. 問題が無ければ **変更 0** で報告する (working tree を触らない)。問題があれば直し、既存 test の期待値は変えない (反転・緩和・skip・削除禁止)。

## 出力形式

段 5 と同じ (`## 変更の要約` (変更 0 ならその旨) / `## byte 一致の確認` / `## 既存 test 追随の有無` / `## 実走結果` / `## 波及` / `## 未了・懸念` / `## 総括`)。
加えて `## 前巡の監査` に、1 の監査結果 (一致 / 不一致の箇所) を書く。
