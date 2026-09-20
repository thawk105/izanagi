単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2814-cleanup-command

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 統合差分 (レビュー対象、docs commit f6a530523 + 実装 commit 92263e53e の累積、base 285477c00): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/s5-cumulative.diff.txt
- 依頼の逐語 + T-2814 / T-2601 の carry 原文 + D2044 項 17 の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/T-2814-origin.md
- 親の段 1 brief: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/brief.md
- 親の段 4 裁定 ((P1)〜(P4) の採用、実装面、T-2601 閉鎖、変異事前登録): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/s4-adjudication.md
- 親の削減・追加の対応表 (A1・A2 追加、R1〜R9 削減。**これ自体が検査対象**): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/reduction-table.md
- 旧本文 (差分の `-` 側の全文): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/cleanup-branches.old.md, /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/SKILL.old.md
- 一次資料 (事故の凍結記録): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/loss-record-README.md、failures 台帳 F1034 の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/F1034.md
- 予算処理の委任裁定 D782 の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/D782.md
- command 入口の編集条件 (`docs/skill-self-improvement.md` の該当節の逐語): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/ssi-entry-edit-conditions.md
- 段 5 Codex author の報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/s5-author.md
- 段 7 記録の草稿 (worklog fragment。T-2601 閉鎖の文言と本文の事実主張を検査): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/worklog-fragment-draft.md
- repo 内 (統合 commit 済みの wave worktree、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2814-cleanup-command/ 配下の
  `.claude/commands/cleanup-branches.md` (新本文 6,201 bytes)、`.agents/skills/cleanup-branches/SKILL.md` (新 overlay 3,052 bytes)、
  `docs/spool/failures/2026-09-21-dev-wave-t2814-cleanup-command-2.md` (F1034 への supersede 追記 1 行、untracked)、
  `tools/check_docs.py` (`grep -n "CLEANUP_COMMAND_SHA256\|CODEX_CLEANUP_BRANCHES_SKILL_SHA256\|COMMAND_LIMITS\|CLEANUP_OCCUPANCY_CONTRACT\|CODEX_CLEANUP_BRANCHES_SKILL_LIMITS"` で位置を出し `sed -n` で読む。全文 cat しない)、
  `orchestrator/tests/test_check_docs.py` (`grep -n "_EXPECTED_CLEANUP_\|_SYNTHETIC_CLEANUP_COMMAND = \|_SYNTHETIC_CLEANUP_SKILL = \|== 6_201\|== 6_205\|\"x\" \* 3\|_make_cleanup_command_mutation_budget_neutral\|discard_changes: true"` で位置を出し `sed -n` で読む。全文 cat しない)、
  `tools/cleanup_remove_dirs.py` (冒頭 docstring だけ。退避を作らないことの確認)、`docs/spool/worklog/README.md` と `docs/spool/failures/README.md` (fragment 文法)。

書込可能な tmp は無い。pytest 緑を要求しない。静的検査でよい。テスト実測は親が行う (author の実走結果は報告に列挙済み: test_check_docs.py 580 passed / 3 skipped、check_docs 違反なし。親の実測: 統合後 check_docs 違反なし、provenance 全史 12183 件違反なし)。

## 前置き — この依頼の性質

研究用 repo の掃除手順書 `.claude/commands/cleanup-branches.md` (Claude 用 command、`tools/check_docs.py` が whole-file SHA-256 と byte 予算 6,204 で pin) と、
それを不可分に適用する Codex 用 overlay `.agents/skills/cleanup-branches/SKILL.md` (同じく SHA pin、予算 3,100) に、事故 F1034 (cleanup の引き渡し script の退避 tar が
`tar --null -T - -czf out -C "$w"` の順で書かれて 0 entry のまま worktree 4 本を撤去し、K2 loop の campaign 原本 (未追跡 `output/exploration/`) を失った) の再発防止として
2 命令 — (a) 未追跡 `output/` を候補にする前に該当 wave の insight「証拠の所在」節で repo 外原本かを確かめる、(b) 退避 tar の `-C` 順と entry 数の検算を撤去の前提にする — を
足した wave である。command は予算 6,204 に対し旧 6,181 (余白 23) だったので、親が D782 手順 1 段目 (既存記述の削減) で 6,201 に収め、Codex author が pin 側
(check_docs の sha 定数 2 個、test_check_docs の byte literal 2 本・sha・bytes assert) を追随させた。上限は上げていない。併せて、裁定済み carry T-2601 (worktree 1 本の
撤去) の対象 2 本が worktree list・branch・admin dir・directory・到達不能台帳のいずれにも無いことを実測して閉鎖する。正しさゲート (verifier) には触れない。
scope 外: command 本文以外の gate・検査・台帳・一般化の追加。

# 依頼 — 4 レンズを 1 本で: (A) 縮約の意味保持 / (B) 追加 2 命令の一次資料整合と実効性 / (C) pin 整合 / (D) 過剰・削除

差分を守らず検査する。親の裁定 (段 4) と対応表 (reduction-table) も検査対象で、誤っていれば名指しせよ。各所見は「何が・どこで・どう壊れるか」と、
放置したときに成果物 (次の `/cleanup-branches` 実行が撤去する集合、check_docs の受理集合、pin の整合、台帳の事実) がどう変わるかを 1 行で書く。示せない所見は nit に落とす。

A. **縮約の意味保持。** 旧本文と新本文を文単位で対応づけ、R1〜R9 の各件が「意味を変えない縮約」か、それとも安全義務の削除・弱化 (編集条件が禁じる「予算のために
   安全義務を削除・弱化」) かを 1 件ずつ判定せよ。とくに (1) R3 (§0 末尾「削除は不可逆に近いので、以下の条件を満たすものだけ消し、迷ったら残して報告する。」の段落削除) —
   「迷ったら残して報告」は §2 高い条件「迷えばユーザー確認」と同義か、それとも「確認」と「残す」は違う義務か。(2) R6 (「`git log` で確認」の手段指定を落とした) —
   手段指定は義務か説明か。落とすと確認が形骸化する経路があるか。(3) R2 (「commit」と「後から」を落とした) — §0 の allowlist と §6 で同じ禁止が保たれるか。
   (4) R7 (「(ExitWorktree が no-op・cd 非持続)」を落とした) — 「cwd 固定の背景セッション」だけで判定条件が読めるか (F51 を引けば分かるか)。(5) R1 (argument-hint) —
   Claude Code の UI 表示だけの変化か、`$ARGUMENTS` の意味 (対象限定) が変わらないか。
B. **追加 2 命令の一次資料整合と実効性。** (1) A1 (§2) の文言が loss record §2 見落としの 2 段目・§5 教訓 2 と一致するか。「候補にせず残置・報告」は、§1 の棚卸し
   (status 保存) と §2 安い条件 (foreign・locked は inventory/report のみ) の流れのどこで発火するか — 「安い条件」の後・「高い条件」の前に置いた位置で、
   `?? output/exploration/` を持つ submit-tree が F1034 の型 (「単なる dirty」として裁定候補 1 に載る) を再び辿らないか。「該当 wave の insight」をどう同定するか
   (worktree 名 → wave → insight) が読み手に分かるか。(2) A2 (§3) の文言が loss record §2 原因 (1)・§4 修正・§5 教訓 1 と一致するか (`-C` を `-T` の前、list と entry 数の
   一致、不足なら撤去しない)。「§5 で引き渡す dirty 撤去 script」という書き方が command の構造 (command 自身は §2 の status 空だけ撤去し dirty は §5 で引き渡す。
   §5 には script の語が無い) と整合し、読み手が「引き渡し script を書くときも §3 に従う」と読めるか。「entry 数が一致」は loss record §4 の「tar の非 dir entry 数が list 数を
   下回れば撤去せず」と同値か (tar は directory entry も数えるので「非 dir」を落とすと検算が緩む・厳しくなるか)。(3) F1034 のポインタ表記 `(F1034)` が command 内の
   他の F 参照 (F26 / F51 / F152) と同じ流儀か。(4) SKILL.md overlay の 2 項が command §2・§3 と矛盾しないか、Codex 固有の縮退 (foreign/unknown と同じく保持、
   検算を欠く撤去手順を人間へ渡さない) として意味が通るか。(5) 引数 (依頼) が求めた (a)(b) の両方が command §2・§3 と SKILL.md の両方に入ったか。
C. **pin 整合。** (1) HEAD の command 本文 / `CLEANUP_COMMAND_SHA256` / `_EXPECTED_CLEANUP_COMMAND_SHA256` / `_SYNTHETIC_CLEANUP_COMMAND` が一致するか (差分の `+` 側を
   目視で照合。末尾改行・行折返し位置・全角半角・NFC。fixture literal 内の backslash・`{` の流儀が現行と同じか)。SKILL.md 側も同様 (`CODEX_CLEANUP_BRANCHES_SKILL_SHA256` /
   `_EXPECTED_CLEANUP_SKILL_SHA256` / `_SYNTHETIC_CLEANUP_SKILL`)。(2) bytes assert 6_201 が実 bytes と一致するか (UTF-8 で数えよ)。(3) 超過入力の padding 23 → 3
   (`oversized = original + "\n" + "x" * 3` で 6,205 bytes) が test の意味 (上限 6,204 の +1 で拒否) を変えないか。(4) `_make_cleanup_command_mutation_budget_neutral` の slack
   `discard_changes: true` が新本文に 1 回だけ残り、`added_bytes < len(slack)` (21) を各 mutation test が満たすか (新本文で余白が 3 bytes になったことで、
   `_make_cleanup_command_mutation_budget_neutral` を使わない mutation test が予算超過で別理由の赤になる経路が無いか)。(5) 旧本文の断片に依存する test・checker・docs 参照が
   残っていないか (author は「無い」と報告。`grep -rn` 相当の静的探索で裏取りせよ。`docs/failures.md` の逐語引用は歴史記録で対象外)。
D. **過剰・削除 (DW-S03 固定レンズ)。** (1) 本 wave が足したのは (a)(b) の 2 命令 (+ overlay 2 項) だけか。gate・検査・台帳・一般化を足していないか。(2) 削減が D782 の
   1 段目「既存記述の削減」の範囲内か。上限 (6,204 / 3,100) を動かしていないか。(3) T-2601 の閉鎖記録 (worklog fragment 草稿の `完了` 項) が「不在の実測」だけを書き、
   実行者・日時を推測していないか。D2044 項 17 の「実行段で占有と差分を再確認」は対象不在で実行対象が無い、という結論が正しいか。(4) F1034 への supersede 追記
   (failures fragment) が `docs/spool/failures/README.md` の 1 物理行・`** — ` 区切り・literal `F1034` の規則を満たし、本文が事実だけか。(5) 逆に、足りないもの
   (例: 引数の「稼働中の cleanup session の final が返す罠」は待たない、退避検算の機械強制は scope 外) が worklog 草稿の「言わないこと」に正しく記録されているか。
   ただし新しい gate・検査・台帳の追加は提案しない (scope 外)。

## 出力形式

- 見出しはすべて `##`。節: `## 所見` (番号付き。各所見に レンズ (A/B/C/D)・must-fix か nit か・「放置時の成果物影響 1 行」・根拠 (file と行または引用) を書く。
  所見ゼロなら「ゼロ」と書き、何を検査してゼロだったかを列挙する)、`## 親裁定への反証` (段 4 と reduction-table の判定に誤りがあれば)、
  `## GO / NO-GO` (must-fix があれば NO-GO、無ければ GO。判定理由 1 行)、最後に `## 総括`。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終わる (無出力が最悪)。
