## 総括

- MF-1 と MF-2 を所有対象のコード・テストへ実装した。
- certifying 入口の受理集合を wave 前と同じ範囲へ戻した。
- repo 外 v2 の lock pin を source HEAD と異なる固定 hex40 にした。
- repo 外・Git 祖先なしというテスト前提を明示的に固定した。
- 既存テストの期待値、production signature、schema は変更していない。
- docs、所有外ファイル、commit には触れていない。
- 実装済み・未実走である。

### MF-1 の実装

[layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/campaign/layer3_report.py:598) で、`build_accepted_report` の `generated_from_head` が未指定なら、`build_report` の前に `_git_head(resolved_campaign)` で確定するようにした。certifying 経路の受理集合を広げない理由も1行コメントで記録した。

[test_layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/tests/test_layer3_report.py:914) に、有効な certifying receipt と repo 外 v2 campaign を与えても `Layer3ReportError` になるテストを追加した。既存の `_certifying_receipt_for` を再利用している。

### MF-2 の実装

v2 lock builder に既定値不変の `contract_loader_commit` 引数を追加した。repo 外 v2 テストでは `"b" * 40` を使用し、source repo HEAD と異なることも明示 assert している。

v2 admission は記録 commit の実在も検証するため、DW-M03 の単一理由 fixture 契約に従い、既存 admission view を保持して lock SHA だけ更新した。これにより fallback の検査前に別 gate で落ちることを防いだ。

[test_layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/tests/test_layer3_report.py:218) の共通 helper は、campaign が source repo 外であり、filesystem root まで `.git` 祖先が存在しないことを assert する。repo 外 v2 正例と v1 負例の双方で使用している。production を source repo HEAD fallback へ壊すと、固定 pin との完全一致検査が落ちる。

### 現行の受理・拒否挙動と変更後の差

段5時点では、非 certifying の `build_report` は repo 外 v2 を authority pin で受理し、repo 外 v1、source repo 内の Git 失敗は拒否する。明示 `generated_from_head` と Git HEAD 成功時の挙動も維持されている。一方、`build_accepted_report` まで repo 外 v2 を受理していた。

変更後は非 certifying 経路の挙動を維持し、`build_accepted_report` だけが未指定時に Git HEAD を要求する。値と例外型は wave 前と同じになる。新しい gate、hex 検査、schema 変更はない。

### 洗い出した制約 meta-test

- `test_ccbench_spawn_sites.py` の `_git_head` subprocess site 1箇所制約
- `test_accepted_report_api_has_no_return_code_or_stdout_parameter`
- generic generator に `certifying_input` 引数を許さない signature 検査
- receipt と `certifying_input` の同値性、admission、E1 epoch の schema・reader 検査
- `test_generated_from_head_mutation_is_rejected`
- 8c E2E の persisted report と lock authority pin の完全一致検査

### 波及可能性

所有外 production caller では、`p3_autonomous_workload_trial.py` の非 certifying render、CLI、直接 `render`、`autonomous_trial_completeness.py` が静的な波及候補である。いずれも signature と返り値構造は不変である。

共有 `_campaign` fixture の挙動は変更していない。v2 lock builder の新引数も既定値では従来どおり現在の binding commit を使う。所有外の `test_p3_autonomous_workload_trial.py` にある既存差分には触れていない。

### 未実走であることの明記

pytest、mutation matrix、acceptance は指示どおり実行していない。実装済み・未実走であり、緑とは報告しない。`git diff --check` と対象2ファイルの AST 構文解析は成功した。commit は作成していない。