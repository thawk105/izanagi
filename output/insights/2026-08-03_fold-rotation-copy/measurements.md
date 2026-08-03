# 親の実測 (2026-08-03, 段 1 前提実測)

環境: この repo が置かれた Linux ホスト、`git version 2.34.1`。
scratch repo = `/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rot/repo` (この wave 専用の使い捨て)。

## 実測 1 — ローテーション形の commit を現行フラグで見ると copy になる

scratch repo に `docs/worklog.md` (399 エントリ相当、約 1200 行) を置き、その本文の **85%** を
新規ファイル `docs/archive/2026-01.md` へ移し、同時に `docs/spool/FOLDED.md` を変更し、
`docs/spool/worklog/2026-01-02-w-1.md` を削除する commit を作った。

- 現行フラグ `diff-tree --root -r -m --no-commit-id --name-status -M -C HEAD`:

```
C084	docs/worklog.md	docs/archive/2026-01.md
M	docs/archive/README.md
M	docs/spool/FOLDED.md
D	docs/spool/worklog/2026-01-02-w-1.md
M	docs/worklog.md
```

- `--no-renames` を付けた場合:

```
A	docs/archive/2026-01.md
M	docs/archive/README.md
M	docs/spool/FOLDED.md
D	docs/spool/worklog/2026-01-02-w-1.md
M	docs/worklog.md
```

## 実測 2 — 移動割合が小さいと copy にならない (閾値依存)

同じ構成で移す割合を **50%** にすると、現行フラグでも `A docs/archive/2026-01.md` になり、
`C` は出なかった。つまり copy 判定は類似度の閾値に依存する。

## 実測 3 — repo-local の diff.renames は plumbing の diff-tree に効かない

同じ scratch repo で `git config diff.renames copies` および `git config diff.renames true` を
設定し、**フラグを何も付けない** `diff-tree --root -r -m --no-commit-id --name-status HEAD` を
実行した。いずれも `A docs/archive/2026-01.md` のままで、`C`/`R` は出なかった。

対照として、同じ設定で porcelain の `git diff --name-status HEAD~1 HEAD` を実行すると
`C084 docs/worklog.md docs/archive/2026-01.md` が出た。

→ この git 版では、plumbing の `diff-tree` は repo-local の `diff.renames` を読まない。
親の懸念 (P1 の理由付け) はこの版では反証されている。

## 実測 4 — 実 repo の状態

- `docs/worklog.md` は 1729 行でローテーション閾値を越えている
- `tools/spool_fold.py:1316 _rotation_name` が作る archive 名は
  `worklog-phase3-<mmdd>-<ord>[-<mmdd>-<ord>].md` で、`_ROTATION_PATH_RE` に一致する
- 既存 archive の実物も同じ形 (`docs/archive/worklog-phase3-0802-113-116.md` など)

## 実測されていないこと (憶測にしないための明示)

- 実 fold commit (実 worklog → 実 archive) での実際の類似度スコアは測っていない。
  裁定の一次資料には `C074` と記録されている。
- git の他バージョンでの挙動は測っていない。
- `--find-copies-harder`、`diff.renameLimit`、binary ファイル、mode 変更の影響は測っていない。
