# 親が段 1 で実測した生の値 (2026-08-26、base = local main b253e0b7)

すべて親が login node 上の worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate` と
main checkout `/work/1/SFC/tanab/izanagi` で実行した。

## M1. git の版と gc 設定 (すべて未設定 = 既定)

```
git version 2.34.1
gc.auto                     = (未設定 → 既定 6700)
gc.pruneExpire              = (未設定 → 既定 2.weeks.ago)
gc.reflogExpire             = (未設定 → 既定 90 days)
gc.reflogExpireUnreachable  = (未設定 → 既定 30 days)
core.logAllRefUpdates       = true
```

`git count-objects -v` (main checkout):
```
count: 6268          <- loose object 数。gc.auto の閾値 6700 に近い
size: 66736
in-pack: 64396
packs: 6
size-pack: 147346
prune-packable: 0
garbage: 0
size-garbage: 0
```

## M2. `tools/check_branch_landed.py` の実走 (1 本、3 秒)

```
$ python3 tools/check_branch_landed.py worktree-dev-wave-t1219-carry-same-id
rc=2  elapsed=3s
```
出力 JSON の要点:
```
schema                    = "izanagi-branch-landed-v1"
assessment_scope          = "D720-condition-1-only"
closure.commit_count      = 1     (b2a38a46..., is_merge=true)
closure.complete          = true
closure.limit             = 4096
closure.elapsed_seconds   = 0.260461
decision.verdict          = "indeterminate"
decision.reason           = "closure-has-no-introduced-state"
branch_delete_authorized  = false
land_authorized           = false
manual_review_required    = true
condition2.status         = "not-checked"
limits.timeout_seconds    = 60.0
limits.max_closure_commits= 4096
observations.ledger_corpus.bytes_read = 21275222 (800 file、0.58 秒)
```

## M3. `branch_delete_authorized` / `land_authorized` は無条件定数

`tools/check_branch_landed.py` 内の出現は各 1 か所だけで、いずれも `_base_payload()` の
literal である。再計算する経路は無い。

```
326:        "land_authorized": False,
335:        "branch_delete_authorized": False,
```

docstring: "This tool never authorizes landing or branch deletion."

## M4. 呼び手の全件検索 (repo コードと docs)

```
$ git grep -n "check_branch_landed\|branch_delete_authorized" \
    tools/ orchestrator/ docs/ .claude/ .agents/ hooks/
```
7 hit。内訳は `orchestrator/tests/test_check_branch_landed.py` の 4 行 (import 2 +
`assert ... is False` 2)、`docs/decisions.md` 1 行 (D922 の定義)、`docs/archive/` 2 行。
**production の呼び手はゼロ。**

## M5. closure の算出式 (`_enumerate_closure`、line 567-596)

```python
result = git.run([
    "rev-list", "--topo-order", "--reverse", "--parents", f"--max-count={limit + 1}",
    branch_oid, "--not", main_oid,
])
```
`--not` に渡すのは `main_oid` **だけ**。他の branch、tag、他 worktree の HEAD、reflog は
root に入らない。

## M6. 削除で実際に到達不能になる集合は事前に算出できる (生死実験、DW-G01)

親が使い捨てで確かめた。`refs/heads` と `refs/tags` から自分を除いた集合を `--not` へ渡す。

```
worktree-dev-wave-t1219-carry-same-id   → 1 commit (b2a38a46...)
worktree-dev-wave-mocc-trace-pair       → 0 commit
worktree-cleanup-branches-20260825      → 1 commit (88114f94...)
```
所要は各 1 秒未満。**この root 集合は不完全である** — 他 worktree の detached HEAD を
含んでいない。実測では `--all` は他 worktree の detached HEAD
(`e29084e0...`、`.codex/worktrees/flaky-holds-a`) を **含んだ**。

## M7. `tools/dev_wave_cleanup.py` の削除経路 (line 990-998)

```python
phase = "branch-recheck"
if _resolve_commit(args.main_worktree, f"{ref}^{{commit}}") != args.landing_wave_tip_sha:
    raise ValueError("wave branch changed before deletion")
ancestry = _git(args.main_worktree, "merge-base", "--is-ancestor", ref, "refs/heads/main")
if ancestry.returncode != 0:
    raise ValueError(f"branch ancestry recheck rc={ancestry.returncode}")

phase = "branch-delete"
_delete_branch(args.main_worktree, args.wave_branch, args.landing_wave_tip_sha)
```
`_delete_branch` (line 919) は `git branch -d` を使い、診断行の sha が landing tip と
一致することまで照合する。

## M8. branch 削除の呼び出し面の全件列挙

`git grep -n -E 'branch +-d|branch +-D|update-ref +-d +refs/heads|delete_branch'` を
`output/` と `external/` を除いた全 tracked file に対して実行 (90 hit)。
archive worklog とテストを除いた **現用**の面は次だけである。

- `.claude/commands/cleanup-branches.md:24` (§2 削除条件)、`:36` (§3 手順 2)、`:45` (F51 縮退)
- `docs/dev-wave/operations.md:207` (DW-O28) — 実体は `tools/dev_wave_cleanup.py` (M7)
- `.agents/skills/cleanup-branches/SKILL.md` は削除手順を複製せず
  `.claude/commands/cleanup-branches.md` へ全面委譲する overlay である
  (「command を全文読み……そのまま実行する」)。よって command を配線すれば両入口を覆う。

## M9. 起動時の編集面重複検査 (ユーザー指示)

- branch tip: 全 28 branch に対し対象 path 限定 `git diff --name-only main...<br> -- <paths>`
  → 重複 0 件。
- worktree 未 commit: 53 worktree 全件に `git status --porcelain` → 実在の重複 1 件のみ。
  `dev-wave-b4-prereg-enactment` が `tools/dev_wave_cleanup.py` (+62/-20) と
  `orchestrator/tests/test_dev_wave_cleanup.py` (+230) を staged 保持。内容は占有判定
  (`_assert_unoccupied` / `_occupancy_issue_summary`) で `_delete_branch` ではない。
- ユーザーが名指しした 3 本のうち `dev-wave-b10-backoff-shape-orthogonal` と
  `dev-wave-flaky-holds-20260826` は対象 path に committed / uncommitted とも差分なし。
- 注意 (親の失敗): 最初の走査で 2 つの worktree が `tools/*` を含む大量の staged 削除を
  示したが、timeout 無しで再測すると 6.5 秒で差分ゼロだった。**稼働中の worktree を
  `git status` で覗くと、`git worktree add` の checkout 途中という一過性の状態を読む**。
