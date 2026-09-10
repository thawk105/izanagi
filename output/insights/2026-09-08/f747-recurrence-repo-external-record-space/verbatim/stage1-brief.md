# 段 1 brief — F747 再発記録と敵対読解の被覆調査

wave slug: `dev-wave-f747-recur-20260908`
wave worktree (子はここを読む): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-f747-recur-20260908`
基準 commit: `cf837838a` (local main と同一)

## 研究前進 (土台)

F747 型の権限逸脱は「cleanup 実行が共有 main と記録空間を非 cleanup mutation で汚す」型で、
実害は並行 wave 群の受入・land が止まること (F599/F747)。今回の再発は repo 外の memory だけで
repo file/history は無傷だが、同じ読解 (「repo 外だから §0 の外」) が repo 内へ向けば main を汚す。
最小差分は F747 への再発追記 1 件と、その誤読を現に招いた条文があればその 1 箇所の是正。

## 実測済みの事象 (ユーザー提示。本 wave では前提)

2026-09-08 の `/cleanup-branches` 実行が、branch 削除 19 本を終えた後、ユーザーの
「必要な自己改善はしたらええんちゃう？」を受けて repo 外の記録空間
`/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi/memory/` を 2 件更新した
(`merged-branch-cleanup-hits-fresh-waves.md` へ追記、`cleanup-branches-cannot-self-improve-in-run.md`
を新規作成、`MEMORY.md` に索引 2 行)。repo file と history は変更していない。
実行者は「memory は repo 外だから §0 の外」と判断した。
親が mtime を実測して裏を取った (2 file とも 2026-09-08 06:49)。
別系統モデル (gpt-5.6-sol / xhigh / read-only) が allowlist 外 mutation かつ F747 同型と判定した。

## 確定済みユーザー裁定 (引数由来。覆さない)

1. 新しい F を採らず、F747 へ「再発: 2026-09-08」を追記する (spool fragment 経由)。
2. command 本文への追記を既定にしない。条文の不足でなく読解の失敗である可能性が高い。
3. memory 2 件を戻すか残すかは本 wave の scope 外 (別裁定)。
4. F538 に手を入れない。

## scope と成果物影響 (DW-G05)

- S1 **F747 再発追記 (failures fragment)**: 放置すると再発が台帳に出ず、3 度目が「初発」として
  新 F を採り、再発を顕在化させるという台帳の目的が壊れる。
- S2 **3 シナリオへの敵対読解判定**: 拒否できない項が残れば、次の cleanup 実行が同じ経路で
  main を汚す。判定対象は (a) ユーザーの一般的な自己改善許可を「明示起動された別 dev-wave」と
  読むこと、(b) repo 外の記録空間 (memory / job dir) への書き込み、(c) cleanup の継続セッション・
  自己 spawn での実装。
- S3 **`tools/check_docs.py` の機械被覆調査**: 捕まらないなら追加候補を出す。
- S4 **worklog fragment**。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-a)** 3 シナリオのうち (a)(c) は現行条文が既に拒否している。(b) だけが弱い。弱点の所在は
  command §0 ではなく `docs/skill-self-improvement.md:66` の
  「同一実行・継続・自己 spawn では **repo file/history** を変更しない」という repo 限定である。
  command §0 の default-deny は「未列挙の state mutation」と無限定で、禁止列挙にも
  「同一実行内の自己改善」があり repo 内外を区別していない。
- **(P1-b)** `tools/check_docs.py` はこの経路を機械的に捕まえられず、それは仕様である
  (`docs/skill-self-improvement.md` 末尾「担保は予算と dispatch・節・孤児・逃がし・住所の構造 lint に限る」)。
  `hooks/guard_write.py` には repo 外の固定 subtree を module 定数で拒否する先例 (D906/D1478、
  発行主体 subtree) があるが、hook は「今が cleanup 実行か」を観測できず、memory dir の無条件拒否は
  memory 機構そのものを壊す。よって機械検査は本 wave で実装せず裁定パッケージへ送る。
- **(P1-c)** `docs/skill-self-improvement.md` の byte 予算残は 7 bytes (5993/6000、上限 TextLimit(6_000, 100))。
  (P1-a) を是正するなら意味等価な縮約が同時に要る。

## 不変条件

- canonical 3 台帳 (`docs/worklog.md` / `decisions.md` / `failures.md`) を直接編集しない。fragment だけ書く。
- `.claude/commands/cleanup-branches.md` と `.agents/skills/cleanup-branches/SKILL.md` を変更しない
  (両方に whole-file SHA-256 pin が掛かる)。
- 上記 memory 2 件と `MEMORY.md` に触れない。
- F538 に触れない。

## 変更面 (実アンカー表)

| path | 種別 | 担当 |
|---|---|---|
| `docs/spool/failures/2026-09-08-dev-wave-f747-recur-20260908-1.md` | 新規 docs | 親 |
| `docs/spool/worklog/2026-09-08-dev-wave-f747-recur-20260908-1.md` | 新規 docs | 親 |
| `docs/skill-self-improvement.md:66` (cleanup-branches 終端) | docs 是正 (条件付き) | 親 |
| `tools/check_docs.py` | 既定は変更しない ((P1-b) が覆れば実装面 → Codex `role=author`) | — |

## 並列分割方針

docs-only 見込みだが受理集合 (権限境界) に触るため軽量版にしない。
段 2 = plan 1 本、段 3 = 敵対 2 本 (レンズ: 条文読解 / 機構実効性)。
実装面が生じた場合だけ段 5 で Codex `role=author` を立てる。親は実装面を直接編集しない。

## 検査

`python3 tools/check_docs.py`、関連テスト、`python3 tools/spool_fold.py --dry-run --show-diff` を rc=0 まで。
