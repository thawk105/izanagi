G1、G2、M11 を指定 2 ファイルだけで実装しました。commit、add、stash などは禁止された Git 操作は行っていません。

- [check_branch_landed.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py)
- [test_check_branch_landed.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/orchestrator/tests/test_check_branch_landed.py)

## 対応表

| 対象 | 状態 | 対応 |
|---|---|---|
| G1 | closed | branch reason を `one-or-more-states-unproven` に更新。該当 unit の履歴 evidence に `truncated`、専用 reason、観測数、limit、elapsed を固定 |
| G2 | closed | local branch 優先、commit-ish fallback を実装。解決経路と候補を JSON 化し、`branch-not-found` を専用化 |
| M11 | closed | local branch と省略 SHA の衝突を単一 gate で fail-closed。衝突 fixture を追加 |
| partial | なし |  |
| regressed | なし |  |

G1 の履歴 evidence は [check_branch_landed.py:1545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:1545)、テストは [test_check_branch_landed.py:856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/orchestrator/tests/test_check_branch_landed.py:856) です。

G2 の解決処理は [check_branch_landed.py:422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:422) です。JSON には以下を出します。

- `branch.resolution_order`: `["local-branch", "commit-ish"]`
- `branch.resolved_as`: `local-branch` または `commit-ish`
- `branch.resolution_candidates`: 両経路の候補
- `ref_snapshot.end_resolved_as`: 終了時の解決種別

到達不能 commit、存在しない入力、曖昧入力のテストは [test_check_branch_landed.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/orchestrator/tests/test_check_branch_landed.py:390) から追加しています。

## M11

M11 の判定式は [check_branch_landed.py:505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:505) の 1 箇所だけです。

masking がない理由は、衝突 fixture の同名 branch を `main` tip に向けているためです。M11 を無効化すると解決順どおり branch が選択され、closure が空になって `landed`、rc=0 まで到達します。他層が `indeterminate` に戻す条件はありません。

## 非回帰

- F1、F13、M4 の全 parent 差分積集合と proof-unit 集約は未変更です。
- F2、F3、F14 の候補先行照合と positive proof の履歴 gate は未変更です。
- F4〜F7、F9、F11、F12、F15、F16 および M1、M2、M5〜M8、M10 の receipt、corpus、証拠、合成規則は未変更です。
- F10 は unit evidence へ履歴実測を追加して強化しました。
- F17、M9 は開始終了比較を維持し、OID に加えて解決種別も比較するよう強化しました。
- A3 は維持され、receipt 不在は引き続き `indeterminate` です。
- A5 は維持され、`not-landed` は完全な closed-world 負証拠だけです。
- commit-ish は SHA 解決後、従来と同じ `git rev-list <resolved-sha> --not <main-sha>` 以下へ渡されます。

## 検証

pytest は実装済み・未実走です。正規 runner で次を起動しました。

- G1/G2 の新規・更新 4 node
- `orchestrator/tests/test_check_branch_landed.py` 全体、静的には 49 test function、50 node

いずれも pytest child 起動前に終了しました。

```text
qstat -Q preflight rc=1
child_started=false
dispatch infrastructure rc=16
```

したがって、緑と申告できる pytest nodeid はありません。

確認できた範囲:

- Python AST compile: 成功
- whitespace、U+0300〜U+036F: 問題なし
- commit-ish helper smoke: 成功
- 現在の `HEAD` SHA による全 checker smoke: `resolved_as=commit-ish`、rc=0
- 存在しない入力の全 checker smoke: `branch-not-found`、`indeterminate`、rc=2
- M11 の条件式、issue code、コメント: source 上各 1 箇所
- `git status --short`: 指定された 2 ファイルだけ

## 受理集合

受理集合は、既存の local branch に加えて、commit へ一意に peel できる commit-ishへ拡張しました。これにより branch 削除後、GC 前の到達不能 commit SHAも従来と同じ証明規則で判定できます。

一方、次は受理していません。

- local branch と省略 SHA が同時に成立する入力
- branch としても commit-ish としても解決できない入力

前者は `ambiguous-branch-commit-ish`、後者は `branch-not-found` で `indeterminate` になります。`landed` の内容証明条件自体は拡張していません。

## 総括

閉じた所見は G1、G2、M11 の全件です。閉じなかった所見や既知の回帰はありません。

残る不確実性は、Pegasus dispatch infrastructure failure により、新規 3 nodeを含む全 50 nodeが未実走であることです。親は runner 回復後に対象ファイル全体を実走し、特に以下を確認してください。

- 削除済み 8 branch の生存 tip SHAが branch 存在時と同じ verdict になること
- 存在しない branch が `branch-not-found`、rc=2になること
- 同名 branch と省略 SHA の衝突が `ambiguous-branch-commit-ish`、rc=2になること
- G1 unit evidence の観測数、limit、elapsed が非初期値であること