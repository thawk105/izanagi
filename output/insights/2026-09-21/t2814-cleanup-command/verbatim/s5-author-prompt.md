単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2814-cleanup-command

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する (射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/s4-adjudication.md` — **親の段 4 裁定 (確定指示)。「裁定」節の「実装面」項が本段の仕事、「変異事前登録」は親が後で走らせる matrix (参考)。** 読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/brief.md` — 段 1 brief (背景・不変条件)。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/.claude/commands/cleanup-branches.md` — **新本文の正本 (読むだけ、触らない)。** HEAD `f6a530523` で親が commit 済み。UTF-8、6,201 bytes、末尾は改行 1 つ。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/.agents/skills/cleanup-branches/SKILL.md` — **新本文の正本 (読むだけ、触らない)。** 同 HEAD、3,052 bytes。読めなければ即停止
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/tools/check_docs.py` — **編集対象** (7,000 行超。全文 cat しない。`grep -n "CLEANUP_COMMAND_SHA256\|CODEX_CLEANUP_BRANCHES_SKILL_SHA256\|COMMAND_LIMITS\|CODEX_CLEANUP_BRANCHES_SKILL_LIMITS"` で位置を出し `sed -n` で読む。編集は 2 定数の値だけ)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/orchestrator/tests/test_check_docs.py` — **編集対象** (12,800 行超。全文 cat しない。`grep -n "_SYNTHETIC_CLEANUP_COMMAND\|_SYNTHETIC_CLEANUP_SKILL\|_EXPECTED_CLEANUP_COMMAND_SHA256\|_EXPECTED_CLEANUP_SKILL_SHA256\|== 6_181\|_make_cleanup_command_mutation_budget_neutral\|_rebind_synthetic_cleanup_command_digest\|discard_changes: true"` で位置を出し `sed -n` で読む)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl` とする。上記以外も repo 内を読んでよい。

## この段の仕事

`.claude/commands/cleanup-branches.md` (6,181 → 6,201 bytes) と `.agents/skills/cleanup-branches/SKILL.md` (2,646 → 3,052 bytes) の新本文が HEAD に commit 済みなので、両 file を whole-file SHA-256 と byte literal で pin する exact 契約の側を追随させる。編集するのは次の 2 file だけ:

1. `tools/check_docs.py` — `CLEANUP_COMMAND_SHA256` を新 command 本文 (HEAD の bytes) の sha256 hex に、`CODEX_CLEANUP_BRANCHES_SKILL_SHA256` を新 SKILL.md の sha256 hex に置換する。定数の形 (3 行の括弧書き) は現行と同じにする。`COMMAND_LIMITS` の `TextLimit(6_204, 110)`、`CODEX_CLEANUP_BRANCHES_SKILL_LIMITS` の `TextLimit(3_100, 210)`、`CODEX_CLEANUP_BRANCHES_DESCRIPTION`、`CODEX_CLEANUP_BRANCHES_OPENAI_YAML`、`CLEANUP_OCCUPANCY_CONTRACT`、他の定数・関数は変えない。
2. `orchestrator/tests/test_check_docs.py` — (a) `_SYNTHETIC_CLEANUP_COMMAND` を新 command 本文の byte 一致 literal に、`_SYNTHETIC_CLEANUP_SKILL` を新 SKILL.md の byte 一致 literal に置換する (**独立に手書きした literal であり、file を読んで代入したり production 定数を import したりしない**。triple-quoted literal 内の backslash・`{`・`$` の扱いは現行の literal と同じ流儀にする)。(b) `_EXPECTED_CLEANUP_COMMAND_SHA256` / `_EXPECTED_CLEANUP_SKILL_SHA256` を新 sha256 に更新 (production 定数と同値だが独立 literal として書く)。(c) `test_cleanup_command_budget_is_pinned_and_enforced` の `assert len(_SYNTHETIC_CLEANUP_COMMAND.encode("utf-8")) == 6_181` を `== 6_201` に更新 (上限 `TextLimit(6_204, 110)` の assert は不変)。SKILL.md 側に同種の bytes assert があれば同様に更新し、無ければ「無い」と報告する。(d) 旧本文の断片に依存する test・helper・期待メッセージが他にあれば新本文へ追随する。とくに `_make_cleanup_command_mutation_budget_neutral` の slack `"discard_changes: true"` は新本文にも 1 回だけ残っているはずなので `count == 1` を実測で確かめる。旧本文だけにあった断片の例: 「削除は不可逆に近いので」「(取り込み済み確認の上)」「rebase/cherry-pick 後も ahead>0」「(ExitWorktree が no-op・cd 非持続)」「`-` prefix なし (初期化済み)」「`git push origin --delete <b>`」「安全なものだけ削除」。これらを検索語や削除対象に使う test があれば新本文の対応語へ追随し、無ければ「無い」と報告に書く。

必ず守る点:

1. **触らない file:** `docs/**`、`.claude/**`、`.agents/**`、`.codex/**`、`hooks/**`、他のすべての test / production file。新規 file を作らない (一時 script は下記 4 の例外)。job dir (`/work/1/SFC/tanab/dev-wave-jobs/...`) へ書かない。
2. **絶対に `git add` / `git commit` / `git stash` / `git checkout` / `git reset` を実行しない。commit は親が行う。** 差分は working tree に残す。
3. **既存 test の期待値を変えない。** 例外は上記 2(b)(c) と、2(d) で旧本文の断片に依存していると実測で判明した箇所だけ。既存 test の反転・緩和・skip・削除は禁止。予算上限 (`6_204` / `3_100` / 最長行 `110` / `210`) の literal は不変。
4. **新本文は 3 箇所 (HEAD の file / production sha 定数 / 合成 fixture literal) で一致させる。** 一致の確認は短い一時 script を repo 内 (例: `<repo root>/.t2814-verify.py`、終わったら削除) に書いて走らせ、`hashlib.sha256(<file bytes>).hexdigest() == 定数 == fixture 定数`、`len(fixture.encode("utf-8")) == 6_201` / `== 3_052`、`fixture == file 本文 (str)` を 2 file とも出力に残す。
5. **テストを甘くしない (F27):** fixture へ file を読んだ値を差し込まない、production 定数を import して fixture に流用しない、`_rebind_synthetic_cleanup_command_digest` 等の helper の意味を変えない。
6. **実走 (sandbox 内で走る形):** `tools/run_tests.py` と `python -m pytest` の直叩きは使わず、次を `cd <repo root>` で走らせ、**実走 nodeid・件数・結果を報告に列挙**する。
   - `PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_check_docs.py','-q','-rf','-p','no:cacheprovider','-k','cleanup or codex_skill or skill_guard or command_budget or command_interface']))"` (cleanup command / skill の pin と予算に掛かる集合。-k は実名に合わせて広げてよい)
   - 上が緑なら同 file の**全件** `pytest.main(['orchestrator/tests/test_check_docs.py','-q','-rf','-p','no:cacheprovider'])` (約 580 件、数分)。赤があれば nodeid と assertion 本文を報告し、本差分に帰属するか (旧本文断片への依存) / 環境起因 (login の /tmp、sandbox の書込不可) かを分類する。
   - `python3 tools/check_docs.py` を repo root で走らせ、rc と最終行を報告する (変更前は「whole-file SHA-256 が契約と不一致」2 件の赤 = 親の実測。変更後は「違反なし」のはず。赤なら本文を直さず定数側を見直す)。
   - 走らない (guard 拒否・環境不備) なら「実装済み・未実走」と書き、緑と書かない。子の実走は親の全走を代替しない。
7. **meta-test:** 変更 file に掛かる制約 meta-test (例: `orchestrator/tests/test_plain_runner_coverage.py`、bytecode guard 系) があれば自ら洗い出して走らせる (新規 test file は作らないので新設義務は無い)。
8. **報告に所有外への波及を静的列挙:** `CLEANUP_COMMAND_SHA256` / `CODEX_CLEANUP_BRANCHES_SKILL_SHA256` / `_SYNTHETIC_CLEANUP_COMMAND` / `_SYNTHETIC_CLEANUP_SKILL` の他の参照元 (`grep -rn` を `orchestrator/ tools/ hooks/ .codex/ .agents/` で)、`docs/failures.md` 等の逐語引用は歴史記録として触らないことの確認。
9. 規模の目安: check_docs.py ±4 行、test_check_docs.py ±40 行 (literal 2 本の置換分)。超えるなら理由を報告に書く。
10. docs を書かない。報告は最終メッセージ本文に書く (file に書かない)。予算が尽きそうなら途中結論を出力形式どおり書いて終わる (無出力が最悪)。
11. **現行の受理・拒否挙動を scope 前に明記:** 変更前の `tools/check_docs.py` が HEAD の 2 file をどう判定するか (親の実測 = 「whole-file SHA-256 が契約と不一致」2 件、rc=1、他の構造検査は緑) を自分でも走らせて 1 行で書く。指示外の受理集合変更をしない。

## 出力形式

- 見出しはすべて `##`。節: `## 変更の要約` (file ごと)、`## byte 一致の確認` (2 file × 3 箇所の bytes・sha・一致の実測)、`## 既存 test 追随の有無` (2(d) の結果)、`## 実走結果` (nodeid・件数・rc。未実走はその旨)、`## 波及` (所有外参照元)、`## 未了・懸念`、最後に `## 総括`。
