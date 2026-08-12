## 変更前の現行挙動

- 通常名と `dir/-answer` は path として hash される。
- root の `-answer` は option と誤認され、rc=129 の `ValidationError(RC_SNAPSHOT)` になる。
- root の `--stdin` は stdin を hash し、ファイル自身の blob を見逃す fail-open になる。
- production built-in spec から root の先頭 `-` は到達せず、直接 helper 呼び出しと test 用 `spec=` 経路だけが到達面である。

## 実装 scope

- [tools/codex_reasoning_ab.py:1330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1330)
  - `hash-object --no-filters -- relative` とし、path operand の前に引数区切りを追加。
  - 診断文字列・例外種別・rc・その他の行は変更していない。
- [test_codex_reasoning_ab.py:1418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_codex_reasoning_ab.py:1418)
  - `test_leading_dash_untracked_path_is_hashed_as_path`
  - `test_option_named_untracked_path_is_hashed_not_stdin`
  - 既存 `_synthetic_nested_submodule_snapshot` と `TOOL._seal_git_object_closure` のみを使用。

差分は指定された 2 ファイルのみで、37 insertions / 1 deletion。docs 編集・commit・Web 検索は行っていない。

## 制約 meta-test の確認

静的に以下を確認した。

- 命名: 2 関数とも pytest の `test_...` 規約に適合し、AST 検査で一意。
- collection: 既存 `testpaths = orchestrator/tests` 配下で、新しい marker や parametrization はない。
- growth hold registry: 実 repository や履歴 corpusではなく、固定サイズの `tmp_path` synthetic repo のため登録対象外。
- real-repo serialization registry: 実 checkout/shared submodule を読み書きしないため登録対象外。
- contract test: registry 登録済み node の存在を検査する契約であり、全 node の登録を要求していない。
- mutation harness: 事前登録された新設 2 nodeid と実装した関数名が一致する。

## 検査結果

実装済み・未実走。

`tools/run_tests.py` で次を投入したが、いずれも pytest 起動前に `qstat -Q preflight rc=1`、rc=16 の dispatch infrastructure failure で拒否された。

- 新設 node:
  - `test_codex_reasoning_ab.py::test_leading_dash_untracked_path_is_hashed_as_path`
  - `test_codex_reasoning_ab.py::test_option_named_untracked_path_is_hashed_not_stdin`
- meta-test 範囲:
  - `test_growth_test_holds_contract.py` 全体
  - `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
  - `test_mutation_harness.py::test_expected_node_must_exist_in_pytest_collection`

ローカル直 pytest には迂回していない。実走済み nodeid は 0 件。

静的・共通検査は以下が通過した。

- `git diff --check`
- Python AST parse と追加テスト名一意性
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

## 変異帰属

- `test_leading_dash_untracked_path_is_hashed_as_path`: `"--"` を削除すると `-answer` が option 扱いされ、rc=129 の `ValidationError` により最初の `reasons == []` まで到達せず赤になる。
- `test_option_named_untracked_path_is_hashed_not_stdin`: `"--"` を削除すると `--stdin` が option として stdin を hash し、保存済みのファイル内容 blob を検査しないため専用 reason が欠落して赤になる。

## 所有外への波及可能性

- 直接 caller: `verify_snapshot`。
- 間接 consumer: `build_snapshot`、実行前後の supervise、pair 起動前検証、replay、`aggregate` / `verify` CLI。
- 共有 fixture consumer: 隣接する nested submodule の受理・gitlink pin・object injection テスト。
- 回帰面: 通常 path を扱う既存 `_git_closure_reasons` / `verify_snapshot` テストと `test_codex_reasoning_ab.py` 全体。
- 残存 scope 外リスク: 裁定 A2 の leading-dash symlink、正規化、snapshot 内包 gate は未実装。

## 総括

- `hash-object` の path 前へ `"--"` を追加し、裁定どおり二相テスト 2 本を追加した。
- 差分・AST・共通 checker は正常で、編集は許可された 2 ファイルだけ。
- pytest は dispatch 防壁の rc=16 により実装済み・未実走。
- 残るリスクは未実走回帰・変異検査と、scope 外として裁定済みの symlink 経路。