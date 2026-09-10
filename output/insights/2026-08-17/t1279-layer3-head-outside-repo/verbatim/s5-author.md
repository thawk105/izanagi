## 総括

- 段 4 裁定のプラン v2 を実装した。
- repo 外 v2 campaign では lock authority pin へ退避する。
- repo 内、Git-backed、v1、明示値の既存挙動は維持した。
- 指定された 5 契約の回帰テストを追加した。
- 8c E2E の `_git_head` monkeypatch を除去し、persisted report を実 pin と照合した。
- 変更は所有対象のコード・テスト 3 ファイルのみ。
- commit、docs 編集、pytest 実走は行っていない。実装済み・未実走である。

## 変更したファイルと行

- [layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/campaign/layer3_report.py:174)
  - `_resolve_generated_from_head` を追加。
  - `build_report` の既存 ternary を helper 呼び出しへ置換。
- [test_layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/tests/test_layer3_report.py:1666)
  - repo 外 v2、Git 優先、repo 内 fail-closed、repo 外 v1、明示値優先の 5 テストを追加。
- [test_p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/tests/test_p3_autonomous_workload_trial.py:2362)
  - 成功値を返す `_git_head` monkeypatch を除去。
  - 3 campaign 全件で persisted report と decoded lock authority pin の完全一致を検査。

## 現行の受理・拒否挙動と変更後の差

変更前は、明示値を非 hex の `"fixed"` も含め無変更で受理し、未指定時は campaign の Git HEAD を使用、取得失敗は常に拒否していた。

変更後も明示値と Git HEAD 成功時の挙動は不変である。Git 失敗時のみ、source repo 外かつ authority 付き v2 lock を新たに受理し、`contract_loader_commit` を返す。source repo 内、authority のない v1、壊れた lock は従来どおり拒否する。新しい検証、hex 検査、lock 読み取り、gate は追加していない。

## 洗い出した制約 meta-test

- `test_ccbench_spawn_sites.py`: `_git_head` の subprocess site は引き続き 1 箇所。
- public signature 検査: `build_report`、`build_accepted_report`、`render`、`main` の引数構造は不変。
- schema 系テスト: schema・返り値構造・certifying 区画は変更なし。
- `test_generated_from_head_mutation_is_rejected`: downstream の hex40/hex64 制約に対し、v2 decoder 済みの hex40 pinを返す。
- 逐語台帳、manifest、schema version、subprocess site の二重管理は新設していない。

## 波及可能性

所有外 production caller の `p3_autonomous_workload_trial.py`、`autonomous_trial_completeness.py`、CLI、certifying 経路は未変更。共有 fixture `_campaign` と v2 lock builder も未変更で再利用した。

波及候補は、明示値を使う qualification tests、`build_accepted_report`、直接 `render`、CLI、completeness の campaign-chain consumer、および subprocess site 数検査である。いずれも signature や既存受理集合の変更はない。

## 未実走であることの明記

pytest は指示どおり実行しておらず、緑とは報告しない。`git diff --check`、3 ファイルの AST 構文解析、主要 signature の静的照合は成功した。現在の差分は指定された 3 ファイルだけで、commit は作成していない。