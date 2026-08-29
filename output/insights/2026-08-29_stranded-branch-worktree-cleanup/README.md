# 取り残し branch / worktree の棚卸しと掃除 (2026-08-29)

ユーザー起票。「未 land の記録断片 2 本を land し、着地済み branch を報告にまとめ、停止した
worktree を撤去する」という 3 点の依頼に対し、一次資料で前提を実測してから実行した。
前提のうち 2 点が実測で覆ったので、段 4 で裁定を変えている。

## 1. 未 land と申告された記録断片

### `worktree-cleanup-branches-20260825` (commit 88114f943) — 既に fold 済みだった

断片 2 本の内容 sha256 が `docs/spool/FOLDED.md` の receipt と一致した。

| 断片 | content_sha256 | 採番 |
|---|---|---|
| `failures/2026-08-25-cleanup-branches-20260825-1.md` | `9ca6adea…24d` | F599 |
| `worklog/2026-08-25-cleanup-branches-20260825-2.md` | `ac0442a7…bff` | [T-1752] / [T-1753] |

fold は別 branch `worktree-dev-wave-t1239-branch-landing-check` (tested tip `d8a78728`) 経由で
行われていた。**land 対象ではなく着地済み残骸である。**

### `worktree-dw-c01-websearch-ruling-20260827` (commit df20d3631) — 未 fold だが逐語 land 不能

fold receipt は無い (content_sha256 `7654e9fd…097` は FOLDED.md に不在)。しかし逐語では land
できない。理由は 2 つあり、どちらも一次資料で確認した。

1. **操作対象が active でない。** 断片は `[T-1273]` への「更新」操作を持つ。worklog entry 1083
   (2026-08-28) が D205 に従い `[T-1273]` を active から外し、`docs/phase3.md` の見送り台帳へ
   送っている。`tools/spool_fold.py` は active でない ID への操作を
   `transition-target` (`active でない操作対象`) で拒否する。
2. **裁定送りの中身が決着済み。** 断片が新規項目として起票しようとした「`DW-C01` の Web 検索禁止を
   既裁定 [T-981] と整合させるか」は、**D1149 (2026-08-27 ユーザー裁定)** が決着させている。
   現行 `docs/dev-wave/core.md` の `DW-C01` も既に
   「Web検索は必要な段だけ明示して使う。」へ改訂済みである。

**裁定 (段 4):** 逐語 land はしない。着地済みの結論へ解決済みの裁定待ち項目を差し戻すことになり、
fold も止まる。代わりに worklog entry 1081 が T-1933 系で採った先例と同じく、**原文 blob を
`sources/spool/` へ保存し、経緯を本 wave の worklog へ記録する**。記録は失われない。

原文: `sources/spool/2026-08-27-dw-c01-websearch-ruling-20260827-1.md` (47 行、
commit `df20d3631` の blob をそのまま)。

## 2. 着地済み残骸と裏取りできた branch

判定は三点 diff の行数ではなく、`git log --no-merges main..<branch>` と blob 照合で行った。

| branch | 非 merge commit | 判定根拠 |
|---|---|---|
| `worktree-dev-wave-t1484-floor-restart-registry` | 0 | merge commit のみ |
| `worktree-agent-a9e73a59e1b7c38a8` | 0 | merge commit のみ |
| `worktree-dev-wave-t1219-carry-same-id` | 0 | merge commit のみ |
| `worktree-dev-wave-t1933-reconciliation` | 6 | 変更 19 file 中 15 が main と同一、spool 3 本は fold 済みまたは entry 1081 へ別文言で吸収、insight README は main 側が新しい版 |
| `worktree-dev-wave-t1933-acceptance-longest-node` | 2 | 同上 (9 file 中 6 が同一) |
| `worktree-dev-wave-acceptance-fastest` | 3 | 同上 (8 file 中 5 が同一) |
| `backup-before-trailer-fix` | 5 | 変更 1061 file 中 1053 が main と同一、残る 8 も branch 側 blob が main の履歴に実在。記録は archive worklog entry 1017、失敗は F679 |
| `worktree-cleanup-branches-20260825` | 1 | 上記のとおり fold 済み |

`output/insights/2026-08-28_t1933-acceptance-longest-node/README.md` は main 側と branch 側で
内容が異なるが、main 側が fresh reconstruction 後の上位互換 (6594 bytes 対 6085 bytes) であり、
branch 側にしかない事実は無い。

## 3. worktree の撤去

### 判定方法

`git worktree list --porcelain` の全 116 本について、(a) directory の実在、(b) `git status`
による未 commit 差分、(c) HEAD の main 包含、(d) `/proc` 走査による稼働 process の参照、
(e) 中断 handoff からの参照、を実測した。さらに **未 commit の内容 1 件ずつについて、同じ path の
blob が main の現物または履歴に存在するか**を照合し、「作業くず」と「main に無い内容」を分けた。

- 撤去可: 65 本 (実体 56 + 登録だけの残骸 9)
- 保留: 51 本。うち **31 本が main に無い未 commit 内容を持つ**

### 実行結果

- 撤去 32 本。1 本ごとに `tools/check_worktree_occupancy.py` を絶対 path・wrapper 無しで通し、
  `status=unoccupied` かつ `scanned>0` のときだけ detach → directory 撤去へ進んだ。
- 24 本は実行時点で既に消滅しており、占有検査が `status=invalid-target` (rc=2) で止めたため
  一切触れていない。
- `git worktree list` は 116 → 61 本。`git worktree prune --dry-run --verbose` の候補は 0 件。
- **branch 削除は 0 件** (ユーザー指示によりこの wave では行わない)。

### 保留した worktree の理由

| 理由 | 本数 |
|---|---|
| main に無い未 commit 内容を持つ | 31 |
| 稼働 process が参照 (実行中の wave) | 10 |
| 中断 handoff が再開待ちで指す | 2 |

中断 handoff が指すのは `dev-wave-t2024-t1760-a2-rightsize` と
`dev-wave-t1998-balanced-stock-inline` の 2 本で、どちらも「状態: 中断」である。

## 4. 掃除の安全側で確かめたこと

### 到達不能 commit 15 本は内容を失わない

`tools/check_branch_rescue.py --ledger-check` (rc=2、`not_landed: 0`) が、撤去対象 worktree の
reflog だけが根になっている commit 15 本を可視化した。15 本すべてについて、first parent との
差分 file の blob が main の現物または履歴に存在するかを個別に照合した。

- 8 本: main に無い blob ゼロ
- 7 本: 途中版の blob を持つが、**path はすべて main に実在**する。内訳は T-1941
  (`backoff_requested_us.py` 他、worklog entry 1084 で着地)、T-1936 の spool 断片
  (archive worklog entry 1042 で着地、decisions/failures 断片は fold 済み)、`conftest.py` の中間版。

失われるのは推敲途中の版だけで、最終成果物はすべて main にある。救出期限は
`2026-09-21T09:14:50Z` (`gc.reflogExpireUnreachable` の下界)。

### dangling 監査 rc=1 の内訳は拡張子違い

`tools/audit_dangling_commits.py --offrepo-root /work/1/SFC/tanab/dev-wave-jobs` は
rc=1・`elapsed_seconds=547.484` (上限 300 秒を超過) で、36 commit の findings を出した。
うち job 成果物 (log / pid / prompt / wait script) を除く insight 系は、**main に `.gz`
圧縮版として実在する**ものだった (例:
`output/insights/2026-08-11_t817-verifier-epoch/log-survival-scan.txt` に対し main は
同 path の `.txt.gz` を持つ)。監査は拡張子違いを同一視しないため未着地に見えるだけで、
救出は不要と判断した。これは本 wave の掃除が作った状態ではなく、既存の状態である。

### 共有 untracked 集合は不変

掃除の前後で primary worktree の `git status --porcelain` は完全一致した。
`?? .codex/worktrees/` の行も残っている (撤去後も 45 本が現存)。`.git/info/exclude` は
触っていない。`external/ccbench` は初期化済みで pin 一致。

## 5. 実測で分かった運用上の事実

**一括撤去リストは、作った時点から陳腐化する。** 本 wave の走行中に別 session が
worktree と branch の掃除を並行して行い、私が撤去する前に 24 本が消えた。私は branch を
1 本も削除していないのに、消えた worktree の branch も消えている。この競合を安全側で
止めたのは `tools/check_worktree_occupancy.py` の `invalid-target` (rc=2) であり、
存在しない対象へ detach や削除を試みる前に fail-closed した。
`git worktree list` の登録数は 116 → 61 と、私の撤去 32 本より多く減っている。
