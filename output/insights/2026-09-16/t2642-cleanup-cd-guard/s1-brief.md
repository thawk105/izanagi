# [T-2642] 段 1 brief — /cleanup-branches §3 に「撤去対象へ cd しない」を明文化する

wave: dev-wave-t2642-cleanup-cd-guard
worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2642-cleanup-cd-guard
基準 commit: 61e0e9c4a48d08c92526f5026c4cd017b150b898 (= local main、clean tree)

## 研究前進

土台 (並行 dev-wave の継続性)。止めている研究は「同時に走る複数 wave が止まらずに land し続けること」。
2026-09-15 の F51 再発では、`/cleanup-branches` 実行セッションが撤去対象 worktree の untracked file を
見るために `cd <worktree>` し、harness が追従して作業ディレクトリが撤去対象の中へ移った。撤去を実行して
いれば以後の全 Bash 呼び出しの cwd が壊れ、復旧経路は `EnterWorktree` の path 形だけで、その間 guard が
全 Bash を拒否する。最小差分は `/cleanup-branches` 本文 2〜3 行。
完了判定 = (a) 「撤去対象へは `cd` せず `git -C` と絶対 path で扱う」が command の可視行として入る、
(b) `python3 tools/check_docs.py` rc=0、(c) 下記 pin 9 点がすべて追従、(d) 受入全走が緑。

## scope

- IN: `.claude/commands/cleanup-branches.md` の §3 (必要なら §1/§2 の既存行の是正を含む) の文面改訂。
- IN: `tools/check_docs.py` の `CLEANUP_COMMAND_SHA256`。SKILL.md を変える場合だけ
  `CODEX_CLEANUP_BRANCHES_SKILL_SHA256` も同時更新。
- IN: `orchestrator/tests/test_check_docs.py` の pin 追従 (`_SYNTHETIC_CLEANUP_COMMAND` 全文、
  `_EXPECTED_CLEANUP_COMMAND_SHA256`、byte assert)。
- OUT: `tools/check_worktree_occupancy.py` の実装変更。F51 本文の再編 (再発記録は 2026-09-15 に済)。
  [T-2641] の直列/並列化 (別タスク、編集面は重なるが本 wave では触らない)。
  `.agents/skills/cleanup-branches/SKILL.md` の Codex overlay の意味変更。

## 確定済みユーザー裁定

- 実装面なので Codex `role=author` が要る。親は docs 本文も含めて直接編集しない
  (command 本文は checker 定数と同時更新が要るため実装面として扱う)。
- [T-2641] と編集面が重なれば後発が降りる → 実測で重複 0 件 (全 74 worktree の未 commit 差分・
  branch tip 差分ともに 0、`ps` でも稼働 0 件)。本 wave が先発として進む。

## 不変条件 (すべて実測済み)

1. 予算: `.claude/commands/cleanup-branches.md` は 5900 bytes / 最長行 110 **文字**。
   現在 **5898 bytes (余り 2)**。**予算のために安全義務を削除・弱化してはならない**
   (`docs/skill-self-improvement.md` 「command 入口の編集条件」)。収まらなければ意味等価の縮約で作る。
2. `tools/check_docs.py` の `CLEANUP_OCCUPANCY_SECTION` = "3. worktree の削除手順 (F26)" と
   `CLEANUP_OCCUPANCY_CONTRACT` (§3 冒頭 2 行の exact 逐語) は pin。変えるなら定数も同時更新する。
3. `"discard_changes: true"` は command 内に **一意** のまま残す
   (`_make_cleanup_command_mutation_budget_neutral` の slack literal、21 文字)。
4. F26 と `` `docs/failures.md` `` が同一可視行に共起する行を残す (address edge 検査)。
5. `$ARGUMENTS` は 1 件、frontmatter key は description/argument-hint、
   `docs/skill-self-improvement.md` への到達性を保つ。
6. §3 の可視 H2 節は 1 つだけ。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1)** 「撤去 step の cwd 検査」は既存 `tools/check_worktree_occupancy.py` で足りており、
  **新設しない**。§3 は既にこの checker を「削除の直前に対象ごと」呼び rc0 のみ進む契約を持つ。
  checker は `/proc/*/cwd` を全 PID について走査するので、cleanup 実行セッション自身の cwd が
  対象配下にあれば rc=1 で止まる (限界の正本は D821)。よって純増は文面の明文化だけとする。
- **(P2)** 2026-09-15 の経路は **§1 の棚卸し** (untracked を見るため `cd`) で対象へ入った。
  「`cd` しない」を §3 だけに書くと、入る側の §1 を塞げない可能性がある。
  §1 / §2 / §3 のどこへ何 byte 置くかは、予算と「入る前に読まれるか」で決める。
- **(P3)** §2 末尾の「自分がその worktree 内で作業中なら、先に main checkout 側へ抜けてから操作する」は、
  cwd 非固定セッションでは「`cd` で戻れる」と読め、対象へ入る誘因になりうる。是正対象かを裁定する。

## 成果物の形

3 file の差分 + `docs/spool/` fragment (worklog エントリ、必要なら failures 追記) +
`output/insights/2026-09-16_t2642-cleanup-cd-guard/` (brief・plan・相談・裁定・レビュー・実走ログ)。

## 並列分割方針

段 2 plan 1 本 / 段 3 敵対相談 2 本 (レンズ A = 安全義務の実効性と F51 経路の被覆、
レンズ B = pin 閉包・予算・逐語契約の整合) / 段 5 実装子 1 本 (3 file は pin で一体、素集合に割れない) /
段 6 敵対レビュー 2 本 + fix。

## 受入・実測環境

login node。repo 内の docs + checker + test のみで計算ノードは不要。
受入は `tools/dev_wave_wait.py acceptance --lease-optional`、land は `tools/dev_wave_land.py`。

## 変更面アンカー表 (実測、行番号は 61e0e9c4a 時点)

| # | path:line | 内容 |
|---|---|---|
| 1 | `tools/check_docs.py:285` | `".claude/commands/cleanup-branches.md": TextLimit(5_900, 110)` |
| 2 | `tools/check_docs.py:752` | `CLEANUP_COMMAND_SHA256 = "ad9b3362...81a4fd35"` |
| 3 | `tools/check_docs.py:754` | `CLEANUP_OCCUPANCY_SECTION` |
| 4 | `tools/check_docs.py:755-761` | `CLEANUP_OCCUPANCY_CONTRACT` (§3 冒頭 2 行 exact) |
| 5 | `tools/check_docs.py:6054-6085` | F26 address edge + §3 可視節の一意性検査 |
| 6 | `tools/check_docs.py:744` | `CODEX_CLEANUP_BRANCHES_SKILL_SHA256 = "268a32ae...b2d85dea"` |
| 7 | `orchestrator/tests/test_check_docs.py:580` | `_EXPECTED_CLEANUP_COMMAND_SHA256` |
| 8 | `orchestrator/tests/test_check_docs.py:627` | `_SYNTHETIC_CLEANUP_COMMAND` (command 全文の逐語複製) |
| 9 | `orchestrator/tests/test_check_docs.py:9836-9857` | byte assert (5_898 x2、TextLimit(5_900,110)、5901 超過 message) |
| 10 | `orchestrator/tests/test_check_docs.py:10123` | `_make_cleanup_command_mutation_budget_neutral` の slack |
| 11 | `.claude/commands/cleanup-branches.md:48-65` | §3 本文 (編集の主対象) |
| 12 | `.claude/commands/cleanup-branches.md:26-47` | §1 棚卸し / §2 安全条件 (P2/P3 の対象) |
