実装完了です。commit は作成していません。

### 実装

- RR-1: [tools/ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1615)
  - `receipt_head..snapshot.head` の全 commit を列挙。
  - `diff-tree --stdin -m --root --no-renames` で全 parent に対する変更 path union を取得。
  - rename の旧・新 path、copy 先、merge の side history、変更後に復元された pathも検出。
  - 許可対象は ledger path と ledger-wide の全 receipt pathのみ。
  - 既存の祖先・candidate blob 検査は維持。

- R2R-1: [tools/ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:306)
  - 全 `GIT_*` を除去した sanitized environment に `GIT_NO_LAZY_FETCH=1` を固定。
  - caller が `GIT_NO_LAZY_FETCH=0` を渡しても上書きされます。

### Control

- change → restore → receipt/ledger commit を独立 negative 化し、`receipt-epoch-path` を確認: [test_ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:1235)
- rename/copy/merge の path union control: [test_ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:1252)
- non-shallow promisor repo、欠損 HEAD blob、起動可能な poisoned local transportを構築。helper未起動、`.git` metadata/object store完全不変を確認: [test_ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:1348)
- nonexistent、non-ancestor、candidate blob mismatch、通常の unrelated path negative、および2 candidateが同じ pre-receipt headを共有する positive は全 suite で維持。

### 検証

- `test_ruleops.py`: **83 passed**（54.00秒）
- `test_run_tests_preflight.py`: **83 passed**
- `test_check_docs.py`: **125 passed**
- plain runner coverage: **3 passed**
- 必須テスト合計: **294 passed**
- 最大package内部 preflight実測: **2.131秒**、runner child timeoutは60秒を維持
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`: OK

受理するのは ledger/ledger-wide receiptだけを変更したepochです。途中の無関係path変更は最終treeが元に戻っていても拒否します。advisory-only/read-only、CLI rc/reason、上限・履歴前検査、各既存境界は維持しています。

編集は指定2ファイルのみ。開始時と終了時のstatus path集合は同一で、親所有のdocs/output等の差分は未変更、staged差分なしです。commit、push、remote network、submodule更新は行っていません。Codex hook発火は主張せず、段6 worker契約と保護範囲を手動で遵守しました。