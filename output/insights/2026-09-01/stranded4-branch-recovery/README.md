# 取り残し branch 4 本の回収可否を base main 24014bdb2 で再判定した

- authority: none
- default_effect: no-state-change
- base main: `24014bdb259d971571f22b54a8f10a49352b825f`
- 判定日: 2026-09-01

本書は可変状態の正本ではない。タスク状態は worklog、設計判断は decisions を正本とする。

## 結論

**取り込むべき commit は 0 件である。** 4 branch の未着地 commit が触る file は、すべて main の
現物に存在するか、main 側に新しい版があるか、canonical 台帳へ fold 済みである。
merge も cherry-pick も行わない。branch は削除しない。

同じ判定は 2026-08-29 の wave (archive worklog エントリ 1094) が既に下していた。本 wave は
その結論を引用せず、base main 24014bdb2 で独立に再導出して一致を確認した。

## 判定方法

未着地量は三点 diff の file 数・行数で測らない。次の 2 段で行った。

1. `git log --no-merges main..<branch>` で未着地 commit を確定する。
2. `git diff --name-only $(git merge-base main <branch>) <branch>` で、fork 点からの変更 file の
   閉包を取る。commit が触る file だけを数えると、競合解消で内容を入れた merge (evil merge) を
   取りこぼす。この閉包に対して 1 file ずつ blob を照合する。

## branch ごとの未着地 commit と file 閉包

| branch | 非 merge commit | merge-base | 変更 file |
|---|---|---|---|
| `worktree-dev-wave-t1933-reconciliation` | 6 | `c384a90a0` | 19 |
| `worktree-dev-wave-acceptance-fastest` | 3 | `7b4c992de` | 8 |
| `worktree-dev-wave-t1933-acceptance-longest-node` | 2 | `7b4c992de` | 9 |
| `worktree-dw-c01-websearch-ruling-20260827` | 1 | `30e7f8c41` | 1 |

非 merge commit は `6f5de08ce` `5d4393233` `1bafd884a` `2ffb32a0e` `85ab06c3c` `0c2a72713`
`df20d3631` の 7 本で、下位 3 branch の commit は reconciliation branch に包含される。

## file 閉包の全数照合 (distinct 22 path)

| path | branch 側 blob | 判定 |
|---|---|---|
| `.../2026-08-28_t1933-acceptance-longest-node/acceptance-receipt.json` | — | main と同一 blob |
| `.../mutation-report.json` | — | main と同一 blob |
| `.../mutation-spec.json` | — | main と同一 blob |
| `.../mutation-wrapper-receipt.json` | — | main と同一 blob |
| `.../paired-runs.json` | — | main と同一 blob |
| `.../verbatim/adjudication.md` | — | main と同一 blob |
| `.../verbatim/baseline-argv.md` | — | main と同一 blob |
| `.../verbatim/brief.md` | — | main と同一 blob |
| `.../verbatim/s2-plan-v2.md` | — | main と同一 blob |
| `.../verbatim/s3-correctness.md` | — | main と同一 blob |
| `.../verbatim/s3-effectiveness.md` | — | main と同一 blob |
| `.../sources/acceptance-fastest-README.md` | — | main と同一 blob |
| `.../sources/longest-node-README.md` | — | main と同一 blob |
| `.../sources/spool/2026-08-28-dev-wave-acceptance-fastest-1.md` | — | main と同一 blob |
| `.../sources/spool/...longest-node-1.md` | — | main と同一 blob |
| `.../2026-08-28_t1933-acceptance-longest-node/README.md` (fastest 版) | `06d5d70c7` | main の `sources/acceptance-fastest-README.md` に原文保存済み |
| 同 (longest-node 版) | `e3a6b6c6b` | main の `sources/longest-node-README.md` に原文保存済み |
| 同 (reconciliation 版) | `c778863e1` | **main のどの path にも無い。** main 側 `d1b9a2a75` はその後継 |
| `docs/spool/decisions/2026-08-28-dev-wave-acceptance-fastest-2.md` | `707753c08` | fold 済み。D1260 を採番 |
| `docs/spool/failures/...longest-node-2.md` | `3c742c29f` | fold 済み |
| `docs/spool/worklog/2026-08-28-dev-wave-acceptance-fastest-1.md` | `fcb27dfa4` | main の `sources/spool/` に原文保存済み |
| `docs/spool/worklog/...longest-node-1.md` | — | main の `sources/spool/` に原文保存済み |
| `docs/spool/worklog/2026-08-28-worktree-dev-wave-t1933-reconciliation-1.md` | `bee4d47fd` | **main のどの path にも無い。** substance は archive エントリ 1081 が別文言で保持 |
| `docs/spool/worklog/2026-08-27-dw-c01-websearch-ruling-20260827-1.md` | `e94c0ea18` | main の `2026-08-29_stranded-branch-worktree-cleanup/sources/spool/` に原文保存済み |

fold 済みの 2 本は、file 名でなく `docs/spool/FOLDED.md` の `content_sha256` と照合した
(`0ed3e567130b...`、`08e142f33496...`)。

## 着地判定の 3 経路

spool 断片の path が main に無いことは、未着地の証拠にならない。着地には 3 通りの経路がある。

1. **canonical へ fold** — 断片は消え、`docs/spool/FOLDED.md` に content_sha256 の受領証が残る。
2. **別文言で吸収** — 受領証にも canonical の逐語にも一致が出ない。archive worklog の該当
   エントリを読んで初めて分かる。
3. **insight の `sources/` へ原文 blob として保存** — canonical にも受領証にも現れない。
   エントリ 1081 と 1094 の先例。

本 wave の対象では 3 経路すべてが実際に使われていた。1 経路だけを見た判定は 4 本とも
「未着地」と誤る。

## 取り込まない個別の理由

- **実装面はゼロである。** `2ffb32a0e` (T-080 process-memo grouping の追加) と `1bafd884a`
  (その撤去) は対象 2 file について差し引きゼロで、
  `git diff 2ffb32a0e^ 1bafd884a -- orchestrator/tests/conftest.py orchestrator/tests/test_real_repo_serialization.py`
  は空を返す。fork 点からの file 閉包にも test file は現れない。
- **`6f5de08ce` の insight README を取り込むと main が退行する。** main 側 `d1b9a2a75` (6594 bytes) は
  branch 側 `c778863e1` (6085 bytes) の後継で、fresh reconstruction の来歴と fold 後の証拠の扱いを
  加えている。branch 側にしかない事実は無い。
- **4 branch の merge は、記録された意図を覆す。** archive エントリ 1081 は、fresh reconstruction が
  source tip `209698aed` `7da264977`、旧 merge、実装、撤去、停止 tip を**非祖先のまま保った**と
  記録している。今 merge するとこれを崩す。
- **`df20d3631` の逐語 land は決着済みの裁定待ちを live state へ戻す。** 断片が裁定送りにした
  「`DW-C01` の Web 検索禁止と既裁定 [T-981] の不整合」は D1149 (2026-08-27 ユーザー裁定) で
  決着し、`docs/dev-wave/core.md` の当該文も commit `87a4ca79c` で改訂済みである。さらに断片は
  `[T-1273]` への「更新」操作を持つが同 ID は active でなく、`tools/spool_fold.py` が
  `transition-target` で拒否する。

## 本 wave が保存した 2 blob

file 閉包 22 path のうち、main のどの path にも存在しないのは 2 本だけだった。エントリ 1081・1094 の
先例に従い、`sources/` へ原文 blob のまま保存した。

| 保存先 | blob | 内容 |
|---|---|---|
| `sources/spool/2026-08-28-worktree-dev-wave-t1933-reconciliation-1.md` | `bee4d47fd` | 停止した reconciliation の spool worklog 断片 |
| `sources/t1933-reconciliation-README.md` | `c778863e1` | 同 wave の insight README (main 側 `d1b9a2a75` の前身) |

**この 2 本は廃案となった手順の記録であって正本ではない。** full-history merge で 2 branch を
取り込む案は fresh reconstruction に置き換えられており、記述にある merge commit `60c758a86`
`8b677a197` は main の祖先ではない。T-1933 の正本は archive worklog エントリ 1081 と
`output/insights/2026-08-28_t1933-acceptance-longest-node/` である。保存した断片は
`docs/spool/` の外にあるため fold の入力にはならない。
