# 段 5 単位 B 実装報告

## 1. 触った file と行数・byte 数

| file | 最終行数 | 最終 byte 数 | 変更 |
|---|---:|---:|---|
| [.claude/commands/cleanup-branches.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/.claude/commands/cleanup-branches.md) | 64 | 3,996 | 3,999 byte → 3,996 byte |
| [docs/unreachable-object-ledger.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/docs/unreachable-object-ledger.md) | 99 | 5,417 | 新規 |
| [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_docs.py) | 6,822 | 270,836 | SHA 値 1 行のみ |
| [orchestrator/tests/test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_docs.py) | 12,158 | 452,470 | SHA 値 1 行のみ |
| [orchestrator/tests/test_branch_rescue_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_branch_rescue_ledger.py) | 75 | 2,612 | 新規 |

command の最長行は 87 文字で、上限 110 文字以下。§2 は変更していない。

最終 `git status --short --untracked-files=all`:

```text
 M .claude/commands/cleanup-branches.md
 M orchestrator/tests/test_check_docs.py
 M tools/check_docs.py
?? docs/unreachable-object-ledger.md
?? orchestrator/tests/test_branch_rescue_ledger.py
```

## 2. command から新文書へ移した内容の対応表

| 移動前 | 移動後 |
|---|---|
| audit rc0=削除続行 | 台帳「dangling audit の分岐」に rc `0` は削除手順を続行可能と記載 |
| audit rc1=§5 報告・救出判断 | 同節に rc `1` は §5 報告と救出判断と記載 |
| audit rc2=実行不能・削除停止 | 同節に rc `2` は実行不能で削除停止と記載 |
| 抑止行も rc0 で §5 報告 | 同節へ移動 |
| `elapsed_seconds=` 欠落・未知 rc は削除停止 | 同節へ移動 |
| 上限超過行は報告するが rc・削除可否を変えない | 同節へ移動。上限の正本が tool `--help` であることも保持 |

command 側には audit の起動、パイプ禁止、rc の直後保存、F152、台帳への可視な指し先を残した。既存の安全義務は削除していない。

## 3. command へ足した配線

§1 の逐語:

```text
- `python3 tools/audit_dangling_commits.py --offrepo-root <runbook §7.2 の dir>` を単独実行
  (パイプ禁止、rc直後保存、F152)。分岐: `docs/unreachable-object-ledger.md`
- 全削除・撤去候補を 1 回で `python3 tools/check_branch_rescue.py --ledger-check --branch <b>...
  --retire-worktree <absolute-path>...` に渡す。rc0完全/2不完全/3通知/64usage・JSON は §5 へ
```

§5 の逐語:

```text
削除しなかった branch は理由 (ahead>0/dirty 等)・閉包・判定・救出期限、worktree は理由を報告する。
```

## 4. SHA pin の更新

旧 digest:

```text
b42c873e30f2d631d1e745820bc3070616fc78641e21c33e72721def6418fa4d
```

新 digest:

```text
dd4c31cde895ed685366a2e7eb4c7f176082a06a9c5bede97a461f370041cde3
```

次の 2 箇所を同じ値へ更新した。

- `tools/check_docs.py` の `CLEANUP_COMMAND_SHA256`
- `orchestrator/tests/test_check_docs.py` の `_EXPECTED_CLEANUP_COMMAND_SHA256`

厳密な 3 行形は維持している。

## 5. 台帳文書と LEDGER_FIELDS の一致確認

文書側 23 field、CLI 側 23 field。順序を含む静的 `diff -u` は差分なし、rc=0 だった。

```text
schema, entry_id, recorded_at, source_refs, source_tips,
assessment_report_sha256, object_oid, object_type, assessment_schema,
assessment_verdict, assessment_reason, storage_kind, object_mtime,
loss_possible_not_before, lower_bound_basis, gc_auto_threshold,
loose_count_at_loss, gc_headroom_at_loss, status, resolved_at,
rescue_ref, resolution_note, object_retention_provided
```

schema 名、`object_retention_provided: false`、3 つの覆わない範囲も文書と新 test に固定した。台帳本文には実 entry 以外の行頭 `- ` を置いていない。

## 6. 実走結果

```text
$ python3 tools/check_docs.py
check_docs: 違反なし
```

rc=0。最終訂正後にも再実走して同じ結果だった。

```text
$ python3 tools/run_tests.py orchestrator/tests/test_branch_rescue_ledger.py
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/output/pegasus-dispatch/cea55f1247ed6ad21b248ad31660f020/receipt.json へ保存しました (child rc=16)
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

rc=16、pytest child 未起動。緑とは報告しない。

```text
$ python3 tools/run_tests.py orchestrator/tests/test_check_docs.py
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/output/pegasus-dispatch/29870cf1ac8652ea1952afb802bf8f63/receipt.json へ保存しました (child rc=16)
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

rc=16、pytest child 未起動。生成された 2 個の ignored dispatch directory は exact path 確認後に除去した。

## 7. 所有外への波及可能性

- `tools/check_docs.py` と `test_check_docs.py` は並行 wave との競合可能性があるが、指定どおり SHA 定数値の各 1 行しか変更していない。
- 新 test は `check_branch_rescue.py` の公開定数を読み、台帳文書と command の配線を検査する。production 動作は変更しない。
- command digest 更新により、command 本文と checker pin は整合している。
- 指定 5 file 以外に残存差分はない。

## 8. やらなかったこと・未解決

- `tools/check_branch_rescue.py` を含む単位 A の成果物は変更していない。
- command §2、DW-O28、D978 の未施行部分、手動 `git branch -d` は変更していない。
- 台帳の自動編集や実 entry の追加、Git ref の作成は行っていない。
- `git add`、commit、Web 検索は行っていない。
- 未解決は Pegasus preflight 障害により、指定 2 test file の pytest child が起動できなかったこと。親環境で再実走が必要。

## 総括

指定 5 file だけで単位 B を実装した。command は 3,996 byte、最長 87 文字で予算内。台帳の 23 field は `LEDGER_FIELDS` と完全一致し、rescue CLI と台帳への可視配線を機械検査へ固定した。docs 検査は rc=0。pytest 2 件は外部 dispatch 障害で未実走である。