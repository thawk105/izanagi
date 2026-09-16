# 親 brief — [T-2639] 救出検査の landed 判定を path 一次判定へ寄せる

wave: `dev-wave-t2639-branch-rescue-path-first`
worktree (投入先 repo root): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2639-branch-rescue-path-first`
基準 commit: `61e0e9c4a` (main と同一)

## 依頼 (ユーザー原文の要旨)

`tools/check_branch_rescue.py` の landed 判定がこの repo の規模で解けず、rc が常に 2 (可視化不完全)
になる。2026-09-15 実測で `--assessment-timeout-seconds` を既定 8 秒から上限 60 秒へ上げても、対象
commit のうち 1 件が assessment-timeout、残りが `one-or-more-states-unproven` のまま残った。所要は
114 秒 → 644 秒。常に不完全を返す gate は警告として情報を運ばず、無視する習慣を作る。

同じ判断を実際に解いたのは、commit が導入した path を main と 1 本ずつ突き合わせる照合で、数秒で
終わり「不在は fold 済み spool fragment、相違は main 側の改版」と確定した。

この path 照合を一次判定に据え、総当たりの状態証明を残余への fallback にする。「fold 済み spool
fragment の不在」は未証明でなく既知正常として一級に扱う。上限 60 秒という定数が repo 規模に対して
据え置きである点も見る。**判定を甘くする方向の変更はしない — 未着地を着地と誤る側の誤りは許さない。**

## 研究前進 (土台)

`/cleanup-branches` は 1 回 98 分で、うち救出検査 12.6 分が常に rc=2 を返す。判定できない残余が
消えないので掃除が止まり、worktree 90 本・branch 92 本が積み上がって全 wave の起動費
(worktree 作成が 25475 file の checkout) を押し上げている。放置時の成果物影響は、到達不能 object
台帳 `docs/unreachable-object-ledger.md` へ記帳するかの判断材料が常に不完全なまま出続け、記帳が
1 件も進まないこと。

## 親が段 1 前に取った実測 (すべて main checkout 61e0e9c4a 上、read-only)

**M1 再現。** `python3 tools/check_branch_landed.py --repo . --timeout-seconds 60 <branch>`

| branch | rc | verdict | 所要 | git 子 process | unit 数 |
|---|---|---|---|---|---|
| worktree-dev-wave-prov-incremental-audit | 2 | indeterminate / one-or-more-states-unproven | 39.9 s | 2003 | 10 |
| worktree-dev-wave-t2515-calib-rr95-rr5 | 2 | indeterminate / one-or-more-states-unproven | 51.3 s | 1190 | 41 |

unit の内訳 (prov-incremental-audit): `exact-state-not-proven` 6、`folded-receipt-absent` 4。
(t2515): `exact-object-seen-at-another-path` 17、`landed` 11、`exact-state-not-proven` 7、
`folded-receipt-absent` 6。

**M2 費用の所在。** path = `orchestrator/tests/test_check_ai_provenance.py` (候補 361 commit)、
main の commit 数 10608。

- 候補列挙 `git log --full-history --format=%H --max-count=1025 main -- <path>`: **0.48 s**
- 現行方式 = 候補ごとに `git ls-tree <commit> -- <path>` を 361 本: **10.92 s**
- 一括 `git cat-file --batch-check` (入力 1 行 = `<commit>:<path>`): **0.09 s**

費用は履歴走査ではなく **subprocess 起動**である。

**M2b 健全性の反例 (重要)。** `git log --raw` 1 本で post-image oid を集める形は **不可**。同 path で
raw の post-image oid は 71 種、per-commit の tree 参照は 89 種であり、merge commit が導入した状態を
18 件取りこぼす。batch 化は `<commit>:<path>` の tree 参照を保ったまま行う。

**M3 spool fallback の正例・負例。**

- 正例 (着地済み wave): `worktree-dev-wave-t2625-sealed-snapshot-qualification` の
  `docs/spool/worklog/2026-09-15-dev-wave-t2625-sealed-snapshot-qualification-1.md` は branch 側 blob
  `2d2217e3df506eda4ee0b02bb5faffe247ae8948`。main 履歴の候補 6 commit のうち **5 commit で
  exact blob が一致**し、残る 1 件 (main tip `61e0e9c4a`) は `missing` (fold が削除済み)。
- 負例 (未着地 wave): `worktree-dev-wave-t2515-calib-rr95-rr5` の spool fragment 2 本は main 履歴の
  候補 commit が **0 件**、exact blob も不在。

つまり exact-state 履歴探索は spool fragment にも decisive に効き、未着地は正しく落ちる。

**M4 定数。** `check_branch_rescue.py`: `DEFAULT_ASSESSMENT_TIMEOUT_SECONDS = 8.0`、
`--assessment-timeout-seconds` は `_bounded_float(1, 60)` で **上限 60 秒に据え置き**。
`check_branch_landed.py`: `DEFAULT_TIMEOUT_SECONDS = 60.0`、`DEFAULT_HISTORY_CANDIDATES = 1024`、
`DEFAULT_HISTORY_SCAN_COMMITS = 20000`、`COMMAND_TIMEOUT_SECONDS = 5.0`。

**M5 依頼の前提と一次資料の差。** 依頼は「対象 3 commit のうち 1 件が assessment-timeout」と書くが、
一次資料 `docs/archive/worklog-phase3-0915-1506.md` は「削除で最後の根を失う **4 commit**、
`not_landed=0`、**3 件を indeterminate のまま**」である。所要 114 秒 → 644 秒は一致。
親は一次資料を採る — これは `(P1)` として攻撃対象に置く。

**M6 消費側。** `.claude/commands/cleanup-branches.md` §2 の削除条件は `ahead=0` であり rescue の rc を
使わない。rescue は §1 棚卸しと §5 報告に配線されている。§1 は既に「`+` 行は実在でなく内容で判定する
(spool の不在は fold で正常)」と書いている。

**M7 凍結閉包。** `check_branch_landed` を path で引くと参照は `tools/check_branch_rescue.py:57`、
`orchestrator/tests/test_check_branch_landed.py`、`orchestrator/tests/test_check_branch_rescue.py`、
`orchestrator/tests/acceptance_duration_ledger.json`、`docs/decisions.md` の 2 箇所のみ。凍結成果物・
oracle gate・proof chain への結線なし。

## scope

- **S1 候補走査の一括化。** `tools/check_branch_landed.py` の `_find_exact_state` (および必要なら
  `_find_object_any_path`) の候補ごとの `git ls-tree` 呼び出しを、`git cat-file --batch-check` の
  1 回呼び出しへまとめる。`_entry_matches` が見る (path, mode, object type, oid) の同時一致は
  1 bit も変えない。`--batch-check` は mode を返さないので、oid と type が一致した候補にだけ
  `_tree_entry` で mode を確認する形にする。
- **S2 spool fragment の fallback。** fold receipt が一致しない spool fragment に対して、D922 の
  決定的証拠 (a) すなわち exact-state の履歴探索へ **正例のみ** fallback する。matched なら `landed`、
  それ以外は現行どおり `indeterminate`。
- **S3 定数。** S1 実測後の所要分布を根拠に、`--assessment-timeout-seconds` の上限 60 と既定 8、
  `DEFAULT_HISTORY_CANDIDATES` の 1024 が repo 規模に対して妥当かを示し、必要なら改める。

## scope 外

rc の意味 (D1231)、`_aggregate_verdict` の集約規則 (D922 点 4)、`not-landed` の判定条件、
`check_branch_rescue.py` の retention / ledger / snapshot 系、`/cleanup-branches` 本文。

## 不変条件 (破ってはならない)

- **I1** `landed` を返す決定的証拠は D922 の (a)(b) だけ。新種の証拠を足さない。patch 指紋・
  task ID 検索・逐語照合・`ledger_probe` を verdict へ昇格させない。
- **I2** spool fragment に `not-landed` を返さない (D922 点 5)。`_regular_decision` の
  `pure-add-path-never-present` 枝を spool 経路で有効化しない。**t2515 の負例は候補 commit 0 件・
  pure add なので、素朴に `_regular_decision` へ流すとここに落ちる。**
- **I3** rc の意味は D1231 のまま。`indeterminate` が 1 件でも残れば rc=2。「indeterminate でも
  rc=0」は D1231 が明示的に却下済み。
- **I4** batch 化で `git log --raw` の post-image へ置き換えない (M2b の反例)。
- **I5** 探索の打ち切り・timeout・上限超過・parse 不能は `indeterminate` へ倒す (D922 点 4)。
- **I6** `GIT_COMMAND_ALLOWLIST` / `GIT_CONFIG` などの子 process 防護を緩めない。
  `cat-file` は既に allowlist にある。
- **I7** 削除 (required.missing) の state と、非 blob (tree / symlink) の state の扱いを変えない。

## 成果物の形

`tools/check_branch_landed.py` の改修、必要なら `tools/check_branch_rescue.py` の定数、
`orchestrator/tests/test_check_branch_landed.py` / `test_check_branch_rescue.py` への正例・負例追加、
段 7 の insight。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1)** 依頼の「3 commit・1 件 timeout」より一次資料の「4 commit・3 件 indeterminate・
  `not_landed=0`」を採る。
- **(P2)** 「fold 済み spool fragment の不在を一級に扱う」の実装形は S2 の exact-state fallback とする。
  代案「fold receipt を identity (authored, wave, seq) でも引く索引を足す」は D922 点 2 の決定的証拠
  そのものを変えるので採らない。
- **(P3)** M2 の 121 倍という実測は 1 path・361 候補の 1 点であり、分布ではない。
