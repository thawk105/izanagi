## 対応表

| ID | 判定 | 根拠 |
|---|---|---|
| RC-B1 | **partial** | 決定 (4-b) は、状態を `NOT_IMPLEMENTED` に再分類せず承認を保留すると明記し、`NOT_CLAIMED` の将来経路を保存した（[新 D:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:72)、[同:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:79)）。基準は将来の裁定パッケージへ明示的に送られているため、保留は「永久不承認」と同義ではない（[同:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:80)、[worklog fragment:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:90)）。ただし決定 (4) の旧文が分類と承認を再び曖昧にするため、完全には閉じていない。RD-B1。 |
| RC-M1 | **closed** | `phase3.md` に run-envelope／campaign-chain の consumer 2 gate が追加され（[phase3.md:470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3.md:470)）、crash 回復・replicate・0 bit 証明も列挙された（[同:478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3.md:478)）。D138 の残余（[decisions.md:6796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6796)）と一致する。 |
| RC-M2 | **closed** | worklog fragment は U2 一次記録、択一3、wave 裁定、非規範の `brief.md` を個別に分離した（[worklog fragment:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:13)）。directory 全体を逐語 authority とする記述は残っていない。 |
| RC-M3 | **closed** | 現在は「レビューが blocker 5 件を出した」と事実を記録し（[worklog fragment:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:30)）、続けて焦点再レビューの `closed 10 / partial 4 / regressed 1` と再 fix を記録している（[同:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:36)）。「5 件を全件 fix」の虚偽断定は解消された。 |
| RC-N1 | **closed** | provenance の射程を pre-commit HEAD `fc8f070` までと限定し、wave commit 後の完了監査を pending と明記した（[worklog fragment:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:69)）。 |

形式契約は静的確認上、両 fragment とも満たす。worklog は H2 が `本文`→`次の一手差分` の2個、無引用符 title、`更新` の `base:`、新規 placeholder、2-space 継続行を備える（[worklog fragment:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:7)、[同:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:74)、[同:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:86)）。新 D は正しい H2、日付なしの題、決定本文に有効な `[T-数字]` なし（[新 D:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:9)）。

## 新規所見

### RD-B1 — 決定 (4) の旧 fail-closed 文が、決定 (4-b) の状態／承認分離と競合する（blocker）

- **主張:** 決定 (4-b)、決定 (6)(a)、却下案、runbook は「状態を再分類せず、承認だけを保留する」で整合している。しかし決定 (4) はなお「**状態を決められない場合は失敗側に倒す**」と規定する。二つの状態語のうち `NOT_IMPLEMENTED` が FAIL、`NOT_CLAIMED` が免責と定義された直後なので、「失敗側」は `NOT_IMPLEMENTED` への分類と自然に読める。

- **根拠:** 競合する規範は [新 D:63–68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:63) と [新 D:72–84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:72)。後者と同じ分離は決定 (6)(a)（[同:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:92)）、却下案（[同:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:123)）、runbook（[runbook:122–126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:122)）には書けている。U2 と D138 は実装有無だけで二分しており、receipt は `NOT_IMPLEMENTED` の定義に含めない（[worklog.md:568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:568)、[decisions.md:6760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6760)）。

- **成果物影響:** 承認者が決定 (4) を採れば実装状態を `NOT_IMPLEMENTED` と記録し、(4-b) を採れば状態未確定のまま承認保留になる。将来の cap-lift 規範受理集合、P6 status、proof chain・試行台帳の記録が分岐する。

- **修正案:** 決定 (4) 末尾を、決定 (4-b) と同じく「状態を決められない場合は状態を再分類せず、cap-lift 承認を保留する」と明記する。新しい設計は不要で、競合する一文の整合だけでよい。

## 総括

**NO-GO。**

対応結果は **closed 4 / partial 1 / regressed 0**。残る blocker は **RD-B1** の1件だけである。

pytest、受入試験、`check_docs.py`、provenance 検査は本レビューでは実行しておらず、緑認定していない。既存テスト期待値の変更も提案していない。