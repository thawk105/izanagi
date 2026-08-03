# G01 transport smoke driver

この directory は anchor `ea6ca433eb83d666ec64f3629cc35c769a2b5c19` に対する使い捨て driver である。
恒久 transport、cross-node lock、scheduler signal / resume の安全性は検証しない。

## 0. 固定値

以下を同じ shell にコピーする。

```bash
SOURCE=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch
G01=/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01
WORKTREE=$G01/worktree
ANCHOR=ea6ca433eb83d666ec64f3629cc35c769a2b5c19
PY=/usr/bin/python3.10
```

## 1. 使い捨て worktree

新規の `g01/worktree` に anchor を展開し、submodule を初期化する。既存 path や既存 ledger があれば再利用せず停止する。

```bash
test "$(git -C "$SOURCE" rev-parse HEAD)" = "$ANCHOR"
test -z "$(git -C "$SOURCE" status --porcelain=v1 --untracked-files=all --ignore-submodules=none)"
test ! -e "$WORKTREE"
test ! -e "$G01/leg1-ledger.json"
test ! -e "$G01/leg2-ledger.json"
git -C "$SOURCE" worktree add --detach "$WORKTREE" "$ANCHOR"
git -C "$WORKTREE" submodule update --init --recursive
test -z "$(git -C "$WORKTREE" status --porcelain=v1 --untracked-files=all --ignore-submodules=none)"
```

## 2. leg 1 — 現行個別 dispatch

launcher は harness を `setsid nohup` で detach し、終了 rc を `leg1.done` に原子的に置く。

```bash
"$G01/run_leg1_dispatch.sh"
while test ! -f "$G01/leg1.done"; do sleep 30; done
LEG1_RC=$(cat "$G01/leg1.done")
test "$LEG1_RC" = 0 || test "$LEG1_RC" = 1
test -f "$G01/leg1-ledger.json"
test "$(git -C "$WORKTREE" rev-parse HEAD)" = "$ANCHOR"
test -z "$(git -C "$WORKTREE" status --porcelain=v1 --untracked-files=all --ignore-submodules=none)"
git -C "$WORKTREE" diff --quiet "$ANCHOR"
```

`leg1.done` が現れない場合は `leg1.pid` と `leg1.log` を確認し、同じ directory で再投入しない。

## 3. leg 2 — 1 job bundle

この repository 作業では qsub していない。親がログインノードの永続 shell から次を実行する。

```bash
cd "$G01"
qsub "$G01/submit_leg2_bundle.sh" | tee "$G01/leg2.qsub.txt"
qstat
while test ! -f "$G01/leg2.rc"; do sleep 30; done
LEG2_RC=$(cat "$G01/leg2.rc")
test "$LEG2_RC" = 0 || test "$LEG2_RC" = 1
test -f "$G01/leg2-ledger.json"
test "$(git -C "$WORKTREE" rev-parse HEAD)" = "$ANCHOR"
test -z "$(git -C "$WORKTREE" status --porcelain=v1 --untracked-files=all --ignore-submodules=none)"
git -C "$WORKTREE" diff --quiet "$ANCHOR"
```

両 leg の rc=1 は完走した期待不一致 ledger なので比較へ進む。`leg2.rc` の 90 / 91 / 92 は
status dirt / anchor diff / 両方、93 は HEAD drift、94 は終了検査不能である。16〜18 は compute
preflight の infra / dirt / out 既存を表し、これらと rc=2 は比較へ進めない。

## 4. verdict 比較

```bash
PYTHONDONTWRITEBYTECODE=1 "$PY" "$G01/compare_verdicts.py" | tee "$G01/compare.txt"
test "${PIPESTATUS[0]}" = 0
```

rc 0 の `GO` だけを transport smoke の一致とする。collection 差は `WARNING` で別枠表示され、GO/NO-GO を変えない。

## 5. 終了後

比較結果と scheduler の `.o` / `.e` を親が記録した後にだけ、使い捨て worktree を外せる。

```bash
git -C "$SOURCE" worktree remove "$WORKTREE"
git -C "$SOURCE" worktree prune
```

変異残留や dirt がある場合は worktree を削除せず、`git diff` と ledger / log を保存して親の復元手順へ渡す。
