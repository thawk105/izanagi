# 親の実測 (段 6 fix 第 2 巡の後、2026-08-25 23:3x)

## テスト

`orchestrator/tests/test_check_branch_landed.py` **50 passed / 0 failed**
(dispatch、gen_S、child rc=0)。第 1 巡で残っていた 1 件の赤は閉じた。

## 実データ (生存 branch 1 本 + 到達不能 commit 7 件)

commit-ish 解決 (G2) が効き、削除済み branch も判定できるようになった。

```
label                     入力          rc  所要  verdict        units  resolved_as
cleanup-branches-20260825 branch 名     2   1s   indeterminate  2      local-branch
t1484-backup              39407cfd      0   2s   landed         6      commit-ish
agent-ab4539              b3611129      0   1s   landed         2      commit-ish
roadmap-workload-hint     15b5c389      2   1s   indeterminate  3      commit-ish
rulings-0818-floor        fe56f5f7      2   1s   indeterminate  2      commit-ish
rulings-0818-second       a6a9f2b7      0   0s   landed         1      commit-ish
t1458-side                028a5e2d      0   1s   landed         1      commit-ish
workload-unitBC           500f47a6      2  10s   indeterminate  11     commit-ish
```

**段 6 fix 前の親の期待表と完全に一致した。**

証明義務の縮小が効いている (F1 の積集合)。
`t1458-side` は 18 unit から **1 unit** へ、`t1484-backup` は
レビュー B の予測 171 unit から **6 unit** へ減った。
所要も 13〜57 秒から 0〜10 秒になった (F7 の lazy corpus)。

## 残る 1 点 — probe の識別力が worklog fragment で機能していない

`unresolved_fragment_candidates` の実測。

```
着地済み
  docs/spool/decisions/2026-08-19-roadmap-workload-hint-2.md
      matched_unit_count=5 / unit_count=6, hit_targets=[docs/decisions.md]      <- 正しく強い
  docs/spool/worklog/2026-08-19-roadmap-workload-hint-1.md
      matched_unit_count=1 / unit_count=5, hit_targets=[worklog-phase3-0819-711.md]  <- 誤り
  docs/spool/worklog/2026-08-18-rulings-20260818-floor-measurement-1.md
      matched_unit_count=4, hit_targets=[worklog-phase3-0819-670.md]            <- 正しく強い

真に未着地
  docs/spool/failures/2026-08-25-cleanup-branches-20260825-1.md
      matched_unit_count=1 / unit_count=5, hit_targets=[worklog-phase3-0819-711.md, docs/worklog.md]
  docs/spool/worklog/2026-08-25-cleanup-branches-20260825-2.md
      matched_unit_count=1 / unit_count=5, hit_targets=[worklog-phase3-0819-711.md]
```

着地済みの roadmap worklog fragment と、未着地の cleanup fragment 2 本が
**どちらも 1/5・同じ file を指す**ため区別できない。

真の着地先は `docs/archive/worklog-phase3-0819-710.md` で、その冒頭は

```
## 2026-08-19 (710) — workload descriptor に人間の自由記述ヒントを任意で許すよう roadmap §1 を協議改訂した (docsのみ、branch worktree-roadmap-workload-hint)
```

対応する fragment の frontmatter は

```
title: workload descriptor に人間の自由記述ヒントを任意で許すよう roadmap §1 を協議改訂した (docsのみ、branch worktree-roadmap-workload-hint)
```

**probe は fragment が持つ最強の identity 信号である frontmatter の `title:` を使っていない。**
fold は worklog fragment の `title:` を canonical の `## <日付> (<番号>) — <title>` 見出しへ
そのまま持ち込むため、`title:` の逐語一致は着地のほぼ確実な指標になる。

これは非決定の観測層なので verdict には影響しないが、
人が「どの fragment を回収すべきか」を読み取る唯一の手掛かりであり、
誤った信号は着地済み fragment の再 fold (T 番号の二重採番) を招く。
