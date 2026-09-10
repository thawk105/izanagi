# 親が fix 後に実 repo で走らせた結果 (2026-08-27)

対象 repo は main checkout `/work/1/SFC/tanab/izanagi`。実装は wave worktree の
`fe6652d20` + 段 6 fix の未 commit 差分。

## E1. 親のテスト実走

```
$ python3 tools/run_tests.py orchestrator/tests/test_check_branch_rescue.py \
    orchestrator/tests/test_branch_rescue_ledger.py orchestrator/tests/test_check_docs.py
609 passed, 3 skipped in 11.31s     (rc=0)

$ python3 tools/check_docs.py
check_docs: 違反なし                (rc=0)
```

fix 子は sandbox の制約 (`qstat -Q` rc=1 → dispatch rc=16) で pytest を実走できず、
「緑と報告しない」と正直に書いた。上の実走は親が行ったものである。

## E2. 単一候補、閉包が非空

```
$ python3 tools/check_branch_rescue.py --repo <main-checkout> \
    --branch worktree-cleanup-branches-20260825
RC=0
deletion_loss_closure.complete = True
deletion_loss_closure.commit_count = 1
  88114f943854  verdict=landed  storage=packed
                loss_possible_not_before=2026-08-26T22:23:14Z
                deadline_status=conservative-floor
issues = []
root_snapshot.roots = 8082 件、complete = True
```

段 4 で親が独立に測った値 (N7: この branch の喪失閉包は 1 commit) と一致する。
**dogfood 1 回目の `worktree-list-parse-error` (locked field) は解消した。**

## E3. read-only の実地確認

E2 の実行前後で `git count-objects -v` の全出力が byte 一致した
(md5 `2f130fafbbf7eaa2026827b8cc0a94ae` で不変)。

## E4. 存在しない候補は fail-closed

```
$ ... --branch worktree-dev-wave-b10-backoff-shape-orthogonal \
      --branch worktree-dev-wave-b10-overthrottle-grid
RC=2
issues = ['candidate-ref-missing', 'landed-assessment-indeterminate', 'candidate-ref-missing']
```

この 2 branch は wave の途中で land・自己撤去され消えていた。存在しない候補で
絵を描いたことにせず rc=2 に倒れる。

## E5. `indeterminate` が残ると rc=2 になる (ユーザー要求の中核)

```
$ ... --branch worktree-dev-wave-t1629-ratification-broker \
      --branch backup-before-trailer-fix
RC=2
deletion_loss_closure.commit_count = 5, complete = True
判定    = {'landed': 1, 'indeterminate': 4}
期限    = {'conservative-floor': 5}
storage = {'packed': 5}
最早の喪失可能時刻 = 2026-08-26T22:25:01Z
gc auto = proximity=below-90-percent, sample_fanout='17'
issues = landed-assessment-indeterminate x4
```

閉包と期限は完全に描けているが、5 commit のうち 4 件が `indeterminate` なので rc=2。
「判定できないものが残る間は通さない」が実データで発火している。

## E6. **branch だけ消す場合と worktree も畳む場合で結果が変わる (設計の核心)**

同じ branch について 2 通りを走らせた。

```
$ ... --branch worktree-dev-wave-t1629-ratification-broker
RC=0    deletion_loss_closure.commit_count = 0

$ ... --branch worktree-dev-wave-t1629-ratification-broker \
      --retire-worktree <...>/.claude/worktrees/dev-wave-t1629-ratification-broker
RC=2    deletion_loss_closure.commit_count = 12
```

branch だけ消しても、その worktree の HEAD が残る限り 12 commit は到達可能である。
worktree も畳むと 12 commit が失われる。

**依頼は文字どおりには「branch 削除前の gate」だった。** branch 削除だけをモデルにする
実装だったなら、この入力に対して「失われるものは無い (rc=0)」と報告し、その直後に
`/cleanup-branches` §3 が worktree を撤去して 12 commit を失う。
段 4 §2.2 で「掃除操作をひとつの操作としてモデルにする」と裁定した判断が、
実データで裏付けられた。

## E7. 焦点再レビューで確かめてほしいこと

E6 の差が**意図した機構**によるものか (撤去対象 worktree の HEAD と index を負側から外す経路)、
それとも偶然そう見えているだけかを、コードで確認すること。
