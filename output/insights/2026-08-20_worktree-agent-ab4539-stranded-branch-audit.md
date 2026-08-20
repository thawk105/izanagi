# stranded branch `worktree-agent-ab4539bed30390c7f` 監査 (2026-08-20)

authority: none
default_effect: no-state-change

発端: `/dev-wave CLEANUP-agent-ab4539` (main 起点、継承 branch なし)。監査対象は
stranded branch `worktree-agent-ab4539bed30390c7f`
(tip `b3611129412e70fa1b6318cd28861308e868f286`, authored 2026-08-20 13:16:19 +0900,
handoff/worktree はすでに消滅)。差分は `.claude/commands/rulings.md` と
`docs/spool/worklog/2026-08-20-worktree-agent-ab4539bed30390c7f-1.md` の 2 file のみ
(`git diff main...worktree-agent-ab4539bed30390c7f --stat`)。

## 検証手順と実測

1. **rulings.md の内容差分**: `git diff main worktree-agent-ab4539bed30390c7f -- .claude/commands/rulings.md`
   (merge-base 経由でなく HEAD 同士の直接比較) は **空**。main の `.claude/commands/rulings.md`
   (4,988 bytes) は既に branch の変更後内容と byte 一致している。
2. **main 側の該当 commit**: `git log -- .claude/commands/rulings.md` の先頭は
   `21ae135d` (2026-08-20 13:16:19 +0900、件名「docs(rulings): 索引出力形式の指示を表/ID主体から
   平易な段落形式へ是正」)。この commit の diff・本文・`AI-Agent:` trailer
   (`product=claude; model=claude-sonnet-5; reasoning=default; role=author; scope=docs`) は
   stranded branch tip `b3611129` と **完全一致** (件名・本文・timestamp・diff すべて同一、
   親 commit のみ異なる並行 commit)。
3. **worklog spool fragment のハッシュ照合**: branch 上の
   `docs/spool/worklog/2026-08-20-worktree-agent-ab4539bed30390c7f-1.md` を
   `git show <branch>:<path> | sha256sum` すると
   `e78f224170a11e6207d0d44e7ac7993a2219bd76c74015c24061850a0102be9b`。
   `docs/spool/FOLDED.md` に既存 receipt
   `{"wave":"worktree-agent-ab4539bed30390c7f","seq":1,"content_sha256":"e78f2241...02be9b","wave_ref":"refs/heads/worktree-rulings-20260820-all", ...}`
   があり **content_sha256 が完全一致**。
4. **fold commit の追跡**: fold commit `5f7e4ea4` (main の祖先、2026-08-20 16:01:39 +0900、
   「Fold landed documentation fragments」) が、この fragment と sibling fragment
   `2026-08-20-worktree-rulings-20260820-all-1.md` を同時に GC し、`docs/worklog.md` へ吸収、
   `docs/spool/FOLDED.md` へ receipt 追記している (`git show 5f7e4ea4 --stat`)。
   現行 `docs/spool/worklog/` に該当 fragment は存在しない (fold 済みのため正常)。

## 結論

stranded branch の差分は **100% 別 wave (`worktree-rulings-20260820-all` 系列) 経由で
main へ完全着地・fold 済み**であり、branch 固有の新規内容はゼロ。おそらく同一セッションが
同じ自己改善 commit を 2 箇所 (直接 main 向けと、この worktree) へほぼ同時に作った、または
2 セッションが同じ実測 (ユーザーが `/rulings all` の表形式出力を拒否した事実) から独立に
同じ是正へ到達し、片方が先に land・fold されたと考えられる。rulings skill との整合は現状で
確保済み (main の `rulings.md` が是正後の内容)。canonical worklog への反映も不要
(fold 済みで二重記録の余地がない — 二重記録すると T/D/F 採番が二重化する)。

適用した判定 doctrine (memory): `rulings-fold-base-mismatch-means-already-implemented`
(内容一致は実装先行を疑う) / `stranded-branch-land-needs-blob-compare`
(blob/hash 照合で既着地を確認) / `folded-md-receipt-detects-already-landed-spool-fragments`
(FOLDED.md の (wave, seq, content_sha256) 照合だけで確定できる)。

## 適用したアクション

- **land しない**: 実装差分ゼロ (main が既に是正後の内容を持つ)。land 候補なし。
- **branch `worktree-agent-ab4539bed30390c7f` は削除しない** (削除はユーザー指示があるときのみ)。
- 兄弟 branch `worktree-rulings-20260820-all` および他の既吸収 branch は本監査の scope 外とし
  再処理しない。
- 本 insight と対の worklog fragment を no-op 記録として追加 (地の分は本 insight を一次資料として
  参照するだけの短い要約)。

## 還元判断

CCBench 還元対象ではない (dev-wave 運用プロセスの監査)。ユーザー確認不要 — 事実確認のみで
選択の余地がない結論 (hash 完全一致)。
