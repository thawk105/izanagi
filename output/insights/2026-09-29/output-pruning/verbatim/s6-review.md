## 所見

| id | 対象 (file:行) | 種別 | 主張 | 根拠 (command と結果) |
|---|---|---|---|---|
| F1 | `output/insights/2026-09-29/output-pruning/README.md:10–16`、`docs/spool/worklog/2026-09-29-dev-wave-output-pruning-1.md:7` | should-fix | 「外せたのは 6 file だけ」「全数走査」の**計数範囲を結論の近くに明記すべき**。走査対象は固定 commit の `output/insights/` であり、`output/` 全体でも削除時点の全 file でもない。 | `git ls-tree -r --name-only 035fc11fa... output/` は 31,651 件、同 `output/insights/` は 27,176 件で、対象外が 4,475 件。固定 commit から削除基準 `c0bcf1abb...` までの `git diff --name-status -- output/insights/` は追加 109 件。段 1 brief には insights 外を残す方針とあるが、結論と worklog の「全数走査」にはこの範囲が出ていない。 |
| F2 | `output/insights/2026-09-29/output-pruning/README.md:100–104` | should-fix | 仮 tree の 27,721 件という比較値は、**次段候補 7,549 件に加えて第 1 段の 6 件も削除し、索引を 1 件追加した値**。その内訳を効果の表に添えると、比較対象を取り違えずに済む。 | `git diff --name-only --diff-filter=D c0bcf1abb... c7bfccd7b` は 7,555 件。集合照合では候補 7,549 件と索引記載 6 件の和に完全一致した。`git ls-tree` は基準 35,275 件、仮 tree 27,721 件で差は 7,554 件。 |
| F3 | `docs/spool/worklog/2026-09-29-dev-wave-output-pruning-1.md:16` | should-fix | 「全量走査 3 回 (各 約 37 分)」は経過記録と一致しない。 | 一次資料 README:34 は最終走査を 2,286.854 秒（約 38 分）、README:41 は初回を「約 20 分後に停止」と記録する。初回を約 37 分の全量走査に数える表現は修正が必要。 |

## 成立しなかった攻撃

- 走査の 27,176 件、分類 v5 の A 131・B 0・C 0・D 27,045、C pool の 344 root・1,550 file は元データと一致した。次段候補の圧縮 TSV も 7,549 行で、区分は 2,996・3,179・1,374 件だった。
- 索引の 6 path は基準 tree の blob id・size と全件一致し、第 1 段 commit では全件不在だった。走査 commit から削除基準までの 41 commit に対象 6 path の変更はなかった。削除元の README と残存資料から、対象名による参照や保護すべき hash 束縛の反例は見つからなかった。device probe 2 件の host・device・結果は元 README §3 に記録されている。
- 生 TSV の worktree add 比は 0.853・0.847・0.846、 第 1 段比は各 1.000 で記載どおり。A/B は各組でほぼ同時に開始している。status の揺れ、各 3 組という標本数、混雑時未測定という限界も明記されている。harness の `concurrent_worktree_add` は `git -C ... worktree add` を数えないため、その列を総同時本数に使えないという注記も正しい。
- 「上位 40 root に高確信度の B は無い」は調査範囲を限定して記されている。decisions fragment の保護境界と worklog の次段をユーザー判断に委ねる書き方は、依頼 file の条件と矛盾しない。

## 総括

**GO。must-fix は 0 件。** 件数の誤算や削除集合の不一致は確認できなかった。F1〜F3 は、計数範囲と履歴・比較条件を正確に読めるようにする修正を推奨する。