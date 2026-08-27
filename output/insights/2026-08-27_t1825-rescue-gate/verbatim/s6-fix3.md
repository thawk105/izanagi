# 段 6 fix 報告

## 1. 所見ごとの対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| A1 | closed | 候補 branch と撤去 worktree の reflog old/new commit OID を正側へ追加。読取・parse 不能は rc=2 |
| A2 | closed | production CLI から child path 注入を削除。固定 path と import test seam に分離 |
| A3 | closed | 全 Git child に `GIT_NO_LAZY_FETCH=1`。landed checker の子孫 Git には一時 PATH wrapper でも強制 |
| A4 | closed | global/system を無効化せず実効 config を観測。読取失敗は rc=2 |
| A5 | closed | prunable admin directory mtime の使用を廃止。assessment time の `conservative-floor` |
| A6 | closed | production CLI から `--now` を削除 |
| A7 | closed | bare、C-quoted path、locked/prunable の単独・理由付き形式を受理 |
| A8 | closed | `git check-ref-format --branch` を使用。ref/path は surrogateescape で可逆化 |
| A9 | closed | 範囲外 timestamp を `reflog-parse-error`、rc=2 に集約 |
| A10 / B4 | closed | `gc_headroom_at_loss` を削除し、fanout/count/sample threshold/heuristic version を追加 |
| A11 | closed | 非空閉包と ledger-check を通し、固定 child、全 child env、repo control bytes を検査 |
| A12 | closed | candidate tip を main へ戻し、過去 commit が reflog にしか無い fixture へ変更 |
| A13 | closed | pack mtime を assessment time より未来にした m10 fixture と、status 用 m11 fixture に分割 |
| A14 | closed | 裁定どおり変更していない |
| B1 | closed | 新 schema の `branch_delete_authorized` 2 箇所を削除。旧 child 境界検査は維持 |
| B2 | closed | audit の最終 `elapsed_seconds=` を一意かつ最終行として厳密検査 |
| B3 | closed | frontmatter、fence、HTML comment、否定的言及を配線として数えない検査へ変更 |
| 親 D2 | closed | 実 porcelain の `locked` 2 形式を受理し、統合 fixture で rc=0 |
| 親 D4 | closed | `_SYNTHETIC_CLEANUP_COMMAND` を現行 command と byte 一致させた |

期限契約に伴う既存期待値変更:

- packed: `rc=2 / indeterminate` → `rc=0 / conservative-floor`。追補 2 §1 の packed 行。
- alternate-only: `rc=2 / indeterminate` → `rc=0 / conservative-floor`。追補 2 §1 の alternate ODB 行。
- m10 の pack mtime: 過去固定値 → assessment time より未来の fixture。A13 の独立検出力確保であり、期限受理集合の緩和ではない。

## 2. §1 (候補 reflog を正側へ) の実装

[tools/check_branch_rescue.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:786) の snapshot で、候補 reflog を必ず parseし、commit 型 old/new OID を `removed_source_oids` へ追加します。撤去 worktree HEAD reflog も同じ処理です。

保護 fixture:

- [candidate reflog-only](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:340)
- [retired worktree reflog-only](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:838)
- [candidate reflog parse failure](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:859)

## 3. §3 (porcelain parser) の実装

[parser](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:409) が受理する field は次の 7 個です。

- `worktree`
- `HEAD`
- `branch`
- `detached`
- `bare`
- `locked`
- `prunable`

`locked` と `prunable` は単独行と理由付き行を受理します。bare record は HEAD/index root にしません。C-quoted path は Git の escape を byte 単位で復号します。

未知 field は record の `inspection_complete=false` と issue に記録し、その record の既知 HEAD/index を恒久 root 側へ残します。撤去対象 record の場合だけ completeness を失わせ rc=2 にします。

[p05 fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:911) は合成 bare/C-quoted record と、実 Git の locked 単独・理由付き worktree を検査しています。

## 4. §8 (pin 閉包 3 箇所) の更新

旧 synthetic digest:

```text
b42c873e30f2d631d1e745820bc3070616fc78641e21c33e72721def6418fa4d
```

新 digest:

```text
dd4c31cde895ed685366a2e7eb4c7f176082a06a9c5bede97a461f370041cde3
```

現行 command と 2 個の SHA 定数は、作業開始時点ですでに新 digest と一致していました。そのため値は変更せず、[逐語コピー](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_docs.py:627) だけを同期しました。

確認結果:

```text
text_equal True
synthetic_sha dd4c31cde895ed685366a2e7eb4c7f176082a06a9c5bede97a461f370041cde3
expected dd4c31cde895ed685366a2e7eb4c7f176082a06a9c5bede97a461f370041cde3
```

`tools/check_docs.py` は値が正しかったため無変更です。

## 5. 追加変異 m18..m25 / p05..p06 と、それを殺すテスト

| ID | 検出点 |
|---|---|
| m18 / p06 | reflog-only commit の正側 OID と closure 出現 |
| m19 | 未知 worktree field でも非撤去 record は rc=0、恒久 root |
| m20 | global `gc.pruneExpire=now` が retention floor に反映 |
| m21 / p08 | prunable root が `conservative-floor`、assessment time、rc=0 |
| m22 | audit 終端欠落が `audit-contract-invalid` |
| m23 | frontmatter-only path が配線扱いされない |
| m24 | JSON 全階層に `branch_delete_authorized` が無い |
| m25 | promisor fixture の全 child env に `GIT_NO_LAZY_FETCH=1`、repo bytes 不変 |
| p05 | locked 2 形式、detached、bare、C-quoted path を受理 |

追補 2:

| ID | 検出点 |
|---|---|
| m26 | future pack mtime を期限に流用せず assessment floor |
| m27 | storage 分類不能は null、`indeterminate`、incomplete |
| m28 / p07 | packed `conservative-floor` が rc=0 |
| m29 / p09 | alternate-only は外部 ODB basis の `conservative-floor` |
| m30 | `gc.pruneExpire=never` は `determinate` |
| p08 | prunable worktree root は time-limited、rc=0 |

各 fixture は baseline の受理を確認し、対象 field・rc・closure の固有 assert で変異を検出する構造です。

## 6. 単一理由性を確認できなかった変異

なし。コード上の前段拒否がないことと、対象 assert が固有であることを確認しました。

ただし独立 mutation runner による動的 KILLED 実測は、§7 の pytest infrastructure failure のため実施できていません。

## 7. 実走結果

```text
$ python3 tools/run_tests.py orchestrator/tests/test_check_branch_rescue.py
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/output/pegasus-dispatch/bebb7bbf273f865774e31750e6e2c6e9/receipt.json へ保存しました (child rc=16)
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

```text
$ python3 tools/run_tests.py orchestrator/tests/test_branch_rescue_ledger.py
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/output/pegasus-dispatch/ccfaa64ec672434534b2e92c80c4970c/receipt.json へ保存しました (child rc=16)
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

```text
$ python3 tools/run_tests.py orchestrator/tests/test_check_docs.py
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/output/pegasus-dispatch/a555d62b3e0da068a6a7f6fd76c5d17a/receipt.json へ保存しました (child rc=16)
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

3 本とも child は未起動です。pytest が green とは報告しません。生成された dispatch artifact はすべて除去済みです。

補助診断では branch-rescue 43 test function、追加後の p05、ledger 6 test function、pin 単独検査が通りました。これは正式な pytest 実走には数えていません。

```text
$ python3 tools/check_docs.py
check_docs: 違反なし
```

`git diff --check`、Python AST parse、結合文字検査も成功しました。

## 8. 所有外への波及可能性

- ledger schema は 23 field から 26 field へ変わるため、未把握の外部 consumer があれば追随が必要です。現台帳 entry は 0 件です。
- JSON は非 UTF-8 ref/path の可逆性を守るため ASCII escape で直列化します。JSON parse 後の値は同一です。
- landed checker の子孫 Git に lazy-fetch 禁止を伝えるため、一時 directory に短命な `git` wrapper を作ります。repository 内には書きません。
- `.claude/commands/cleanup-branches.md` と所有外 tool は変更していません。

## 9. やらなかったこと・未解決

- A14 は裁定どおり未実装です。
- queue preflight 障害により正式 pytest 3 本は未実走です。
- 実 repo dogfood は親の再実走対象として残しています。
- `git add`、commit、push は行っていません。
- 指定外ファイルの変更はありません。最終差分は指定範囲内の 5 ファイルだけです。

## 総括

採用された A1〜A13、B1〜B3、親 D2/D4 を実装し、A14 は裁定どおり維持しました。期限契約は追補 2 の 3 値へ再基底し、pin の逐語コピーと digest 閉包も一致しています。`check_docs` は green ですが、pytest は Pegasus dispatch infrastructure failure により未実走です。