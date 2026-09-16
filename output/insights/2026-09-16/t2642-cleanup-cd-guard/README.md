# [T-2642] /cleanup-branches の進入禁止と cwd 検査 — 設計成果の凍結

authority: none
default_effect: no-state-change

この dir は可変状態の正本ではない。`/cleanup-branches` の本文も checker も、本 wave では 1 byte も
変えていない。ここにあるのは、実装を降りた wave が残した設計成果と実測値である。

- wave: `dev-wave-t2642-cleanup-cd-guard`
- 基準 commit: `61e0e9c4a48d08c92526f5026c4cd017b150b898`
- 日付: 2026-09-16
- 成果物: 本 dir と `docs/spool/worklog/2026-09-16-dev-wave-t2642-cleanup-cd-guard-1.md` だけ

## なぜ実装しなかったか

[T-2641] が同じ編集面 (`.claude/commands/cleanup-branches.md` の §1/§2/§3、
`tools/check_docs.py` の `CLEANUP_COMMAND_SHA256`) を触る wave として先に立っていた。
`.git/worktrees/` の birth time は T-2641 = 2026-09-16 04:34:10、本 wave = 04:34:38 で
**T-2641 が 28 秒先発**。依頼が定めた「重なれば後発が降りる」に従い、後発の本 wave が降りた。

着手前 (≈04:33 JST) の重複検査では、全 74 worktree の未 commit 差分・branch tip 差分・`ps` の
いずれも 0 件だった。**相手が worktree を作った直後で、まだ 1 byte も編集していなかったため。**
この検査法では着手直前の wave を捕まえられない。

## 収録物

| file | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief。scope、不変条件、割れうる前提 (P1)(P2)(P3)、変更面アンカー表 |
| `s2-plan.md` | 段 2 プラン (codex read-only)。文面案・byte 収支・pin 追従手順 |
| `s3-sol.md` | 段 3 敵対相談 A (安全義務の実効性と事故経路の被覆) |
| `s3-luna3.md` | 段 3 敵対相談 B (pin 閉包・予算・逐語契約の整合)。3 回目の投入で採用 |
| `s4-adjudication.md` | 段 4 裁定。実装しない判断と所見の real/refuted |

## 次に実装する人が使える結論

### 1. 文面案 (**そのまま使ってはならない**)

§1 冒頭へ進入禁止 1 行 (68 bytes)、§1 の 31-32 行と §2 の 41-42 行を縮約して 108 bytes 捻出、
§2 末尾の退避指示を §3 へ移設・強化 (143 bytes)。改訂後 **5897 / 5900 bytes、84 行、最長 105 文字**
(2 者が独立に検算して一致)。

**この案は敵対相談の must-fix 2 件を反映していない。** 直すべき点は下記 2・3。

### 2. 「撤去対象」と書くと棚卸し中の進入を許す

2026-09-15 に実際に踏んだ経路は、**撤去対象が確定する前**の棚卸し (§1 の status / untracked 確認) で
`cd` したものだった。禁止の文面が「撤去対象へは `cd` しない」だと、順に読む実行者は
「まだ撤去すると決めていない worktree なら入ってよい」と読める。禁止対象に**棚卸し候補を含む**ことを
明記しなければ、再発経路は塞がらない。

### 3. 占有 checker の rc0 は退避の証明ではない

`tools/check_worktree_occupancy.py` について実測で確定したこと:

- **自己 PID の cwd は除外されない。** `:586` が `/proc` の全列挙 PID を走査する。`:453` の
  自己除外は cmdline の検査だけに効く。`seen = {self_pid}` (`:305`) は祖先探索の循環防止であって
  cwd 走査の除外集合ではない。
- **しかし「対象内に居れば必ず rc=1」は成立しない。** rc0 になる経路が 4 つある —
  (i) 別 PID namespace の process、(ii) cwd 読取権限不足 (`:403` は非阻害診断)、
  (iii) cwd の `resolve(strict=True)` が PermissionError (`:422` も非阻害)、
  (iv) 対象外の deleted cwd (`:430`)。対象自体が不存在・非 directory なら `invalid-target` で rc2
  (`:533`、`:716`)。
- したがって文面には「**rc0 を退避の証明として扱わない**」「別 cwd を指定した一時シェルの `pwd` だけでは
  確認完了としない」を載せる必要がある。限界の正本は D821。

### 4. pin 閉包 17 群

`.claude/commands/cleanup-branches.md` を束縛する検査。**親が brief で 10 群を全数として書いたのは
誤りで、敵対相談が 7 群を追加検出した。**

`tools/check_docs.py` 側 (6 群):

| 位置 | 内容 |
|---|---|
| `:285` | `TextLimit(5_900, 110)` — 予算 5900 bytes、最長行 110 **文字** (`len(line)`、byte ではない) |
| `:753` | `CLEANUP_COMMAND_SHA256` — command 全文の sha256。**要更新** |
| `:755` | `CLEANUP_OCCUPANCY_SECTION` = "3. worktree の削除手順 (F26)" |
| `:756-761` | `CLEANUP_OCCUPANCY_CONTRACT` — §3 冒頭 2 行の exact 逐語 |
| `:6054-6085` | F26 と `docs/failures.md` の同一可視行共起、§3 可視節の一意性、`$ARGUMENTS` 1 件、frontmatter key 集合、`docs/skill-self-improvement.md` への到達性 |
| `:744` | `CODEX_CLEANUP_BRANCHES_SKILL_SHA256` — **command だけ変えるなら更新不要** (`:5183`・5219 は skill 自身の文字列だけを hash、command は `:6571` で別に hash する) |

`orchestrator/tests/test_check_docs.py` 側 (11 群):

| 位置 | 内容 |
|---|---|
| `:581` | `_EXPECTED_CLEANUP_COMMAND_SHA256`。**要更新** |
| `:627` | `_SYNTHETIC_CLEANUP_COMMAND` — command 全文の逐語複製。末尾 LF まで一致が要る。**要更新** |
| `:897`・923 | `_build_min_repo` が synthetic から最小 repo を生成する。全文追従が要る |
| `:9843`・9848 | byte assert `== 5_898` が 2 か所。**要更新** |
| `:9849` | 超過生成の詰め物 `("x" * 2)`。改訂後 byte + LF 1 + 詰め物 = 5901 になるよう調整が要る |
| `:9935`・9941 | 文字列 `commit graph` が command 全文で一意であること |
| `:9963`・9979・9991 | `## 4. 事後検査` の見出し全文 |
| `:10232`・10242 | **§2 の見出し全文が一意であること** |
| `:10153`・10186・10209・10232 | §3 の checker 呼出しから「停止。」までの部分逐語 |
| `:10262-10403` | 「正本は `docs/failures.md` F26。」の住所表現そのもの |
| `:10356`・10361 | frontmatter の description 行の全文 |
| `:10103`・10109 | `CLEANUP_COMMAND_SHA256` の**代入書式** (3 行の形を `count(old) == 1` で探す) |
| `:10123` | `_make_cleanup_command_mutation_budget_neutral` の slack literal `"discard_changes: true"` が**全文で一意**であること (21 文字) |

**command の固定行番号・総行数を assert する pin は、この 2 file には無い** (行番号・数値・digest・
値文字列で検索した実測)。行数が変わること自体は赤にならない。

`orchestrator/tests/test_branch_rescue_ledger.py:167`・344 が §1 の見出しと rescue/audit の bullet を
解析する。§1 を並べ替えるならここも見る。

### 5. 追従漏れの症状

- checker 定数と期待 digest だけ更新 → synthetic の派生 digest assert (`:9835`) が落ちる。
- synthetic だけ更新 → 同 assert と未更新の byte assert (`:9843`) が落ちる。
- checker だけ更新して synthetic を残す → `_build_min_repo` が旧 command を生成し、baseline 成功期待も
  digest 不一致で落ちる。
- **実 command だけ更新して checker と fixture を両方残す → fixture 中心の test では実 file との差を
  直接検出できない。** 実 repo に対する `tools/check_docs.py` の実走が要る。

## 主張しないこと

- 文面を足すことは機械防壁の追加ではない。`check_docs.py` の構造 lint は「可視行に語が共起するか」
  しか見ない。新しい進入禁止行を消しても、digest を再束縛すれば既存の構造検査はその欠落を拒否しない。
- 観測不能な harness まで含めた機械的保証は、文面だけでは成立しない。それを求めるなら checker か
  実行基盤の変更が要り、[T-2642] の scope を超える。D821 が「観測ベースの discharge は正の証拠でしか
  作れない」と既に裁定している。
- 「74 worktree で重複 0 件」は観測時点の範囲に限られる。以後の重複不在を保証しない。
- 本 wave は pytest の緑を主張しない。実走したのは `tools/check_docs.py` と
  `tools/check_codex_output.py` と受入全走だけである。
