---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1050-fragment-recovery
seq: 2
---

## 再発

### F270

- **再発: 2026-08-16** — 三度目。取り残し branch 3 本の回収を依頼する wave brief が、
  各 branch の未着地量を `git diff --stat main...<branch>` の insertions で数えていた
  (2,246 insertions / 889 行)。**三点記法は merge-base から branch tip までの branch 側全作業を
  出すため、既に着地した branch でも同じ数字を返す。** 実測では 3 本のうち 2 本が着地済みで、
  数字どおりに回収していれば、後続版が実環境欠陥を修正した checker と、期待表 135 件・
  変異 8/8 KILLED を伴う `hooks/guard_bash.py` の上位互換実装を、どちらも旧版で上書きする
  退行になっていた。代理指標は本体 (path 実在) と 2 例目 (lease 混雑の worktree 数推定) に続いて
  3 種類目であり、**族としては「安価に測れる量を状態の代わりに読む」で同一**である。
- 併記する実測: 判定を反転させたのは 2 手だった。(a) `git cherry main <branch>` の patch-id 照合
  — (1) は非 merge 3 commit が全て `-`。(b) **branch 名でなくタスク ID での台帳・archive 検索**
  — (2) は branch 名 `t1025-impl` では worklog / archive に 0 件だが、`T-1025` では
  `docs/archive/worklog-phase3-0816-569-570.md` に完了記録があり、着地 commit `4f47bc74` の
  `git merge-base --is-ancestor` が rc=0 だった。既存 memory
  `check-withdrawal-rulings-before-wave` は「機構名で検索する」を求めており、
  **branch 名は機構名でもタスク ID でもない**ため、branch 名 grep だけでは構造的に当たらない。
- 恒久対応: 新規の機械検査は本 wave では入れず、lint 化の可否を
  {{T:stranded-branch-landing-lint}} へ起票した (F270 本体の恒久対応が「lint 化の可否は裁定へ返す」で
  止まっているため、同じ場所へ戻さず独立 3 例目の実測を添えて起票する)。
  当面の防壁は本項と memory `cherry-plus-judged-by-content-not-path` である。
- 再発検知: **機械検査は無い (prompt 規律)。** F270 本体と同じく恒真な保証にしないため明記する。
  代理指標の型を 1 つ足す: 着地/未着地の判断に `git diff` の三点記法の行数を使った報告。
