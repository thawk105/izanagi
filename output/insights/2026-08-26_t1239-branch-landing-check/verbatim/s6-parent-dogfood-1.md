# 親による実データ実走の結果 (段 6、2026-08-25 22:4x)

親が `tools/check_branch_landed.py` を実 repo の 9 branch へ当てた。
**gate tool は親が実データで 1 回通すまで完成としない**という規律に従う。

## 既定値での結果 (9 本)

```
t1484-backup-before-trailer-fix              rc=2  0s   indeterminate  files_enumerated=false
worktree-agent-ab4539bed30390c7f             rc=2  36s  indeterminate  landed=1 indet=1
worktree-cleanup-branches-20260825           rc=2  57s  indeterminate  landed=0 indet=2
worktree-roadmap-workload-hint               rc=2  15s  indeterminate  landed=1 indet=2
worktree-rulings-20260818-floor-measurement  rc=2  13s  indeterminate  landed=1 indet=1
worktree-rulings-20260818-second             rc=0  13s  landed
worktree-t1458-side-ccbench-provenance-fix   rc=2  14s  indeterminate  landed=5  indet=14 (files=18)
worktree-workload-policy-hint-impl-unitB     rc=2  19s  indeterminate  landed=15 indet=22 (files=27)
worktree-workload-policy-hint-impl-unitC     rc=2  17s  indeterminate  同上
```

**9 本中 8 本が `indeterminate`。** 親の正解 (landed 8 / not-landed 1) と大きく食い違う。
`not-landed` は 1 件も出ない。この状態では削除候補一覧を作れず、tool は目的を果たさない。

## 診断 1 (blocker) — merge commit の証明義務が「全親に対する差」になっていない

裁定 A1 は「各 commit が**全ての親に対して**導入した tree entry の状態を証明する」と定めた。
実装はこれを満たしていない。

実測 (`worktree-t1458-side-ccbench-provenance-fix`):

```
closure = 2 commit
  028a5e2d "merge main"  parents = 69935f09, 2a36d1c3
      vs 69935f09 : 17 file
      vs 2a36d1c3 :  1 file
      全親に対して差が出る file = 0        <- 真の証明義務はゼロ
  69935f09 "docs(spool): ..."  parent = ddf30399
      vs parent : 1 file (docs/spool/decisions/2026-08-21-rulings-...-1.md)
```

真の証明義務は 1 file だけで、それは tool 自身が `landed` と判定している。
にもかかわらず tool は `changed_files=18` を課し、main 側由来の
`docs/decisions.md` / `docs/failures.md` / `docs/worklog.md` / `orchestrator/*` などを
branch の義務として数え、そこで `indeterminate` になっている。

`unitB` も同じ機序で 27 file に膨らんでいる (真の義務は 9 file 前後)。

**成果物影響**: これを直さないと、merge を含む branch は構造的に `indeterminate` にしかならず、
判定表は 4 本を「判定不能」と書く。実際にはそのうち 3 本は着地済みである。

**提案**: 各 merge commit について、全親との name-status 差の**積集合**だけを証明義務にする。
親が実測した `comm -12` と同じ集合になることをテストで固定する。

## 診断 2 (must-fix) — `--history-candidates` の既定 64 が実 repo に対して低すぎる

`worktree-agent-ab4539bed30390c7f` は既定で `history-candidate-limit-exceeded` により
`indeterminate` だったが、`--history-candidates 1024 --history-scan-commits 200000
--timeout-seconds 300` で再走すると **`landed` (rc=0)** になった。所要 16 秒。

`.claude/commands/rulings.md` や `docs/decisions.md` のように多数の commit が触る file では
64 では足りない。既定値は実 repo で `landed` を出せる値にすること。

**成果物影響**: これを直さないと、頻繁に編集される file を触った branch は
既定実行で常に `indeterminate` になり、利用者が上限を手で上げない限り判定できない。

## 診断 3 (must-fix) — 候補上限超過を `truncated` として扱う向きが逆でありうる

`--find-object --max-count=N+1` が N+1 件返すのは「その blob が main 履歴に
**何度も存在した**」ということである。一致が豊富であることを
`truncated` → `indeterminate` へ倒しているなら、正の証拠を捨てている。
実装の該当箇所を確認し、**一致が 1 件でも見つかった時点で `matched` を確定させ、
上限超過は一致ゼロの場合にだけ `truncated` とする**こと。

## 診断 4 (must-fix) — `ledger_probe` の `outcome` が識別力を持たない

probe 自体は正しい信号を出している。

```
worktree-roadmap-workload-hint / decisions fragment
    6 単位中 5 単位が docs/decisions.md に hit   <- 着地済み (D568)
worktree-cleanup-branches-20260825 / failures fragment
    5 単位中 1 単位が docs/archive/worklog-phase3-0819-711.md に hit  <- 定型見出しの偶然一致
```

ところが `outcome` はどちらも `matched` である。1 単位でもどこかに hit すれば `matched` に
なるため、fragment が必ず含む定型見出し (`## 本文`、`### 新規` 等) で恒真化している。

**成果物影響**: 人が `observations` を読んでも、着地済みと未着地を区別できない。
親が手作業でやった判別を tool が再現できない。

**提案**: hit 率と、**単一 file が覆う単位数の最大値**を出す。
`outcome` は「単一 file が全単位の過半を覆う」ときだけ `matched` とし、
それ以外は `weak` または `not-matched` にする。決定性は持たせない (A3 を維持)。

## 診断 5 (must-fix) — merge base が一意でない branch を即 `indeterminate` にしている

`t1484-backup-before-trailer-fix` は `git merge-base --all` が 2 件返す
(`4b1e4914` と `dadd0247`)。tool は `merge-base-not-unique` で
`files_enumerated=false` のまま 0 秒で終わる。

closure ベース (A1) の判定は本来 merge base の一意性を必要としない —
`git rev-list <branch> --not <main>` は merge base を使わずに求まる。
merge base を要求している箇所が closure 判定と無関係なら、要求ごと落とせるはずである。

**成果物影響**: criss-cross 履歴を持つ branch を 1 件も判定できない。9 本中 1 本が該当する。

## 親が確認した非回帰

- `orchestrator/tests/test_check_branch_landed.py` 26 node 緑 (dispatch、Elapse 9 秒)。
- `test_plain_runner_coverage.py` + `test_pytest_collection_config.py` 79 node 緑 (61 秒)。
- `git status --porcelain` は新規 2 file のみ。
