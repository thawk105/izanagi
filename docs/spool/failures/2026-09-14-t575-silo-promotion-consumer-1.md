---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: t575-silo-promotion-consumer
seq: 1
---

## 新規

### {{F:main-replaced-under-fresh-worktree}}. 並行 session が local main を同じ件名の別 SHA へ置き換え、fresh gate も `--ff-only` も通らなくなった [手順漏れ] [ドリフト]

- 事象: 2026-09-14 の wave 立ち上げで、`git worktree add ... main` が `d9bbdb6b0` を取った直後に
  local main が `75bea8e5f` へ進んだ。両者は**件名が完全に同一**で、`75bea8e5f` は `d9bbdb6b0` の
  子孫ではない (共通祖先は `f5423e2ff`)。`tools/check_wave_startup.py --mode fresh` は
  `NG: HEAD != local main` を返し、`DW-O20` が指示する `git merge --ff-only main` も
  `fatal: Not possible to fast-forward` で rc=128 になった。
- 根本原因: `DW-O20` は HEAD 差の解消手段として `--ff-only` だけを与える。これは main が
  **前進**した場合の手順であり、main が**置き換えられた**場合 (別 session の amend / 作り直し) には
  定義上成立しない。並行 session が多い環境では、worktree 作成から起動 gate までの数十秒に
  この置き換えが入りうる。
- 実害なし (near miss)。wave 開始前に検出したため成果物は無傷。所要は約 2 分。
- 恒久対応: memory `worktree-discipline` (branch 作り直しの手順を追加) —
  未 commit の成果が無い段階では `git checkout --detach` → `git branch -D <branch>` →
  `git checkout -b <branch> main` で branch を作り直す。**`git reset --hard main` を使わない** —
  branch reflog に reset entry を残さず `branch: Created from main` だけにするためであり、
  作り直しなら追加の履歴痕を持ち込まない。作業済み commit がある段階でこの状況に入った場合は
  作り直しではなく通常の merge (非 ff) を使う。
- 再発検知: 起動 gate が `NG: HEAD != local main` を返したとき、`git merge-base main HEAD` が
  HEAD と一致しなければ本型である (一致すれば単なる前進なので `--ff-only` で足りる)。
  `DW-O20` 本文への追記は `docs/dev-wave/**` の byte 予算に収まらないため行わない
  (F66 と同じ扱い。予算超過で撤回した恒久対応は本台帳と memory が担う)。

## 再発

### F287

- **再発: 2026-09-14** — silo 昇格 consumer の同定 wave で、親が canonical な decisions 記録へ
  「production で昇格用途を渡す call site は oracle の 1 本だけである」と書いた。実際は
  `certified-selection` / `paper` を渡す call site が複数実在する
  (`orchestrator/campaign/p3_s4_loop.py:441`、`orchestrator/campaign/paper_story_a2_certification.py:784` 他)。
  原因は 2 つ重なっている。(1) `rg ... | head -20` で出力を切った。(2) 同じ command に渡した
  `--glob '!*/tests/*'` が**効いておらず**、限られた表示枠をテスト側の hit が占めていた。
  F287 の型 (完全性を要する主張を切り詰めた出力から書く) と同一だが、**本件は「無い」ではなく
  「1 本だけ」という一意性の主張**であり、同じ根本原因が肯定側の数量主張にも出ることを示した。
  検出経路は段 6 の敵対レビューで、現物の反例を file:line で出した。親が検算して訂正した。
  是正: 切らずに数え直し、記録から「1 本だけ」を削除して、用途の宣言は機械的な昇格禁止ではないと
  明記した。判定 (昇格 consumer の不在) は反転していない。
  恒久対応: memory `closure-and-search-discipline` へ「『N 本だけ』『唯一』も不在と同じ全数検査が
  要る」「除外指定が効いたかを出力で確かめる」の 2 点を追記した。
  **適用先が「不在の実測」から「件数・一意性の主張」へ広がった点が本追記の顕在化である。**

### F106

- **再発: 2026-09-14** — 受入全走の走行中に、親が段 8 の自己改善 fragment 1 本を worktree へ
  新規作成し、worklog fragment 1 本を編集した。受入は preflight の `prerun-clean` で `rc=70`
  停止し、テストを 1 件も走らせずに 1 回分を失った。**2026-09-02 の再発と同型で、今回は
  「段 7 の記録」ではなく「段 8 の自己改善」が起草先だった。** 親は「受入を待つ間に独立作業を
  進める」という規律 (`CLAUDE.md` 作業の進め方 9) に従ったつもりで、その独立作業の書き先が
  repo 内だったことに気づいていなかった。2026-09-02 の追記が既に
  「待ち時間に進めてよい独立作業は repo 外に置くものだけである」と書いており、
  **恒久対応は memory `dirty-tree-during-pending-job` から変更なし。**
  段 8 は段 7 の後・受入の後に置く方が構造的に安全だが、入口の段順序の変更は
  自己改善の範囲外なので実施せず、この観測だけを残す。
