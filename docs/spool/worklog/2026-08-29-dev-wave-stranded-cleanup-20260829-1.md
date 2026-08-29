---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-stranded-cleanup-20260829
seq: 1
title: 取り残し branch の着地を fold receipt で判定し、停止 worktree 32 本を撤去した (docs のみ、branch worktree-dev-wave-stranded-cleanup-20260829、実装面差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

ユーザー起票。「未 land の記録断片 2 本を land、着地済み branch を報告、停止 worktree を撤去」の
3 点。段 1 前の実測で前提が 2 点覆ったため段 4 で裁定を変えた。逐語と判定根拠は
`output/insights/2026-08-29_stranded-branch-worktree-cleanup/` に残す。

- **未 land 2 本のうち 1 本は既に fold 済みだった。** `worktree-cleanup-branches-20260825` の
  断片 2 本は content_sha256 が `docs/spool/FOLDED.md` の receipt と一致し、F599 / [T-1752] /
  [T-1753] を採番済みだった。fold は別 branch `worktree-dev-wave-t1239-branch-landing-check`
  経由。三点 diff の行数を根拠にした「未 land」の申告は、fold receipt を照合すると覆る。
- **残る 1 本は未 fold だが逐語 land が機構上できない。** `worktree-dw-c01-websearch-ruling-20260827`
  の断片は `[T-1273]` への「更新」操作を持つが、entry 1083 が D205 に従い同 ID を active から
  外している。`tools/spool_fold.py` は active でない操作対象を `transition-target` で拒否する。
  加えて断片が裁定送りにした「`DW-C01` の Web 検索禁止と既裁定 [T-981] の不整合」は D1149
  (2026-08-27 ユーザー裁定) が決着済みで、`docs/dev-wave/core.md` の当該文も改訂済みだった。
  逐語 land は決着済みの裁定待ちを live state へ戻すので行わず、entry 1081 が T-1933 系で
  採った先例に従い原文 blob を insight の `sources/spool/` へ保存した。
- **着地済み残骸 8 本を blob 照合で確定した。** 非 merge commit 0 が 3 本
  (`worktree-dev-wave-t1484-floor-restart-registry`、`worktree-agent-a9e73a59e1b7c38a8`、
  `worktree-dev-wave-t1219-carry-same-id`)。残り 5 本は変更 file の blob が main の現物または
  履歴に実在することで確定した。`backup-before-trailer-fix` は 1061 file 中 1053 が main と
  同一、残る 8 も main の履歴に実在し、記録は archive entry 1017 と F679 にある。
- **worktree 116 本を棚卸しし、32 本を撤去した。** 未 commit 内容は 1 件ずつ main の blob と
  照合し、「作業くず」と「main に無い内容」を分けた。撤去可 65 本 (実体 56 + 登録残骸 9)、
  保留 51 本。保留のうち 31 本は main に無い未 commit 内容を持つ。撤去は 1 本ごとに
  `tools/check_worktree_occupancy.py` を絶対 path・wrapper 無しで通し、`status=unoccupied`
  かつ `scanned>0` のときだけ進めた。`git worktree list` は 116 → 61 本、prune 候補 0 件。
  branch 削除はユーザー指示に従い 0 件。
- **撤去で内容が失われないことを 2 経路で確かめた。** `tools/check_branch_rescue.py --ledger-check`
  は rc=2・`not_landed: 0` で、撤去対象 worktree の reflog だけが根の commit 15 本を可視化した。
  15 本すべてを first parent 差分の blob 単位で照合し、失われるのは推敲途中の版だけで
  最終成果物はすべて main にあると確定した (T-1941 は entry 1084、T-1936 は archive entry 1042)。
  救出期限の下界は `2026-09-21T09:14:50Z`。
- **dangling 監査の rc=1 は拡張子違いだった。**
  `tools/audit_dangling_commits.py --offrepo-root /work/1/SFC/tanab/dev-wave-jobs` は
  rc=1・`elapsed_seconds=547.484` (上限 300 秒超過) で 36 commit の findings を出したが、
  job 成果物を除く insight 系は main に `.gz` 圧縮版として実在するものだった。監査は
  拡張子違いを同一視しないため未着地に見えるだけで、救出は不要と判断した。本 wave の掃除が
  作った状態ではない。
- **開始時 snapshot も陳腐化する (F633 の再発)。** 走行中に別 session が worktree と branch を
  並行して掃除し、私が触る前に 24 本が消えた。私は branch を 1 本も削除していないのに消えた
  worktree の branch も消えている。占有検査の `invalid-target` (rc=2) が、存在しない対象への
  detach と削除の前で fail-closed した。F633 の未実施対応は「生きた登録でなく走行開始時の
  snapshot を読む形へ変えれば構造的に閉じる」としているが、本件は **snapshot 側でも 56 件中
  24 件が実行前に陳腐化した**実測であり、snapshot 化だけでは閉じないことを示す。閉じるのは
  対象ごとの実行直前検査であって、列挙時点の一貫性ではない。
- 掃除の前後で primary worktree の `git status --porcelain` は完全一致し、`?? .codex/worktrees/`
  の行も残った (撤去後も 45 本が現存)。`.git/info/exclude` は触っていない。
- repo 直下に 0 byte の untracked file 5 本 (`Bespoke`、`GenDB`、`Jitskit`、`indicators`、
  `single-agent`、いずれも 2026-08-28 00:41) と、日本語 file 名の 0 byte file 群が残っている。
  shell の誤 redirect の跡だが、共有 untracked 集合を変える操作は本 wave の scope 外として
  触っていない。

## 次の一手差分
