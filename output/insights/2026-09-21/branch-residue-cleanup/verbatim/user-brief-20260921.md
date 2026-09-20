# 自己改善 wave の brief — 残骸 branch / worktree が溜まらない構造にする

起点: 2026-09-21 00:20 JST の `/cleanup-branches` (session 172a3a)。ユーザー裁定 (同日 00:40 頃):
「`/cleanup-branches` は branch の `-D` をしてよい」「残骸 155 本は消す」「自己改善 wave で再発を防ぐ」。

## 観測した事実 (一次資料: 本 dir の `deleted-branches.tsv` / `excluded-branches.tsv` / `retire-worktrees.json` / `rescue2.json`)

- 稼働中 session 6 本に対し worktree 42 本・branch 165 本が残っていた。command の安全条件 (ahead=0 のみ `-d`、
  locked は報告のみ) で消せたのは branch 4 / worktree 4 だけ。9/17 の一括掃除も同じ壁で「Codex 子木 80 本は裁定へ」で止まっていた。
- **構造原因**: dev-wave は Codex 子 (impl / fix1..N / probe / unit) ごとに branch と worktree を作るが、main へ入るのは
  wave の記録 commit (verbatim 写し) だけで、子 branch の tip は永遠に main の祖先にならない (ahead>0)。
  段 9 の自己撤去 (DW-O28、`tools/dev_wave_cleanup.py --remove-child`) は worktree を消しても branch は消さず、
  「child is not integrated」で worktree の撤去自体を拒むこともある (例: t2344-impl)。結果 1 wave あたり 2〜8 本の
  branch が恒久に残る (155 本 ≈ 約 40 wave 分)。うち 39 本は内容まで main と同一 (cherry 全 `-`) だった。
- 裁定後の実施: 140 本を `git bundle` で退避 (`deleted-branches.bundle`、5.9 MB、verify OK) してから `-D`、
  unlocked・clean・所有 wave 終了済みの子 worktree 13 本を撤去。除外は稼働 wave 11 本・locked checkout 6 本・
  1 時間以内 1 本・棚卸し後の新規 5 本。

## この wave の成果物 (すべて別 dev-wave で。cleanup 実行は §0/§6 により編集不可)

1. **decisions fragment**: 裁定を D として記録 — `/cleanup-branches` の `-D` 許可と条件 (所有 wave が land 済み /
   稼働 wave・locked checkout・1h 以内・棚卸し後の新規を除外 / 削除前に repo 外へ bundle 退避 / `check_branch_rescue.py`
   を 1 回 / 損失 commit は unreachable-object-ledger へ)。D204 (branch 削除はユーザー指示時のみ) との関係を明記。
2. **`.claude/commands/cleanup-branches.md` §0/§2** の allowlist を裁定に合わせて改訂。byte 予算 5,900 (実測 5,888) 内で
   書き換えが要る。`tools/check_docs.py` の `CLEANUP_COMMAND_SHA256` と `.agents/skills/cleanup-branches/` 側の
   `CODEX_CLEANUP_BRANCHES_SKILL_SHA256` の同期は実装面 → Codex author。**T-2814 wave (`dev-wave-t2814-cleanup-command`、
   同 file §2・§3 を編集中、00:38 起動) の land 後に着手し、その版を base にする** (同 file の並走編集を避ける)。
3. **dev-wave 段 9 / DW-O28 の恒久対応 (再発防止の本体)**: land 後の自己撤去で Codex 子の worktree だけでなく
   **子 branch も消す** (内容は wave の記録 commit に verbatim で保全されている前提を明記)。`--remove-child` が
   「not integrated」で拒む場合の扱い (bundle 退避 → `-D`、または保留して /cleanup-branches へ名指しで引き渡し) を決める。
   実装は `tools/dev_wave_cleanup.py` (Codex author) + `docs/dev-wave/` の該当 leaf (exact pin → fixture placeholder)。
4. **failures fragment**: 型「掃除規約の allowlist が構造的残骸に届かず、40 wave 分が溜まった」。F747 (cleanup の越権) と
   対になる「保守的すぎて溜まる」側の型として。
5. **unreachable-object-ledger**: `rescue2.json` の損失 commit を期限付きで台帳へ転記 (ledger-check の通知が出ていれば必須)。
6. 直前再確認に **lock file の存在検査** (`[ -f .git/worktrees/<name>/locked ]`) を加える (棚卸し後に別 session が lock した実例あり)。

## 起動の一行 (ユーザーが新しい背景 session で)

/dev-wave 残骸 branch/worktree が溜まらない構造 (P1、裁定 2026-09-21 ユーザー: /cleanup-branches の -D 許可 + 再発防止)。
brief は /work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-20260921-rescue/self-improvement-brief.md。成果物は同 brief の 1〜6。
T-2814 wave の land を待ってから cleanup-branches.md に触る。着手直前の local main から fresh worktree。
