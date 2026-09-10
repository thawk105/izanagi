## 直した内容

- [test_axis_b5_search_executor.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-fix2/orchestrator/tests/test_axis_b5_search_executor.py) のみ変更。
- `tmp_path` 上の一時 tree で `_walk_files` を直接検査し、`__pycache__` 内と単独の `.pyc` が除外されることを固定。
- 実 repo の生存確認は実際の `HEAD` に対する `verify_registration(..., repo_root=ROOT)` のみに変更。共有 tree への作成・削除を廃止。
- extra-file、module-path、mode、bytes の既存拒否検査は維持。
- `preflight.py` の意味論は変更なし。

## test の増減

0 件です。変更前 34 node、変更後 34 nodeです。

## 実走した test

- `orchestrator/tests/test_axis_b5_search_executor.py` 全 34 node: 34 passed
  - `::test_worktree_scan_excludes_pycache_and_pyc`
  - `::test_registration_accepts_exact_commit_tree_and_returns_schema_valid_seal`
- `orchestrator/tests/test_axis_b5_search_parsers.py` 全 20 node: 20 passed
- `git diff --check`: 問題なし

## 波及可能性

共有 repo へ probe `.pyc` を書かなくなったため、xdist worker 間の `registered_path_set_mismatch` 干渉を除去しました。`PYTHONDONTWRITEBYTECODE` 環境でも成立し、`__pycache__` 除外を落とす変異は一時 tree の単位 test が検出します。

## 未実走・未実装

- xdist を使う全受入走行と変異走行は未実走です。
- 指定範囲外の変更、network 利用、commit は行っていません。

## 総括

共有状態を書き換える非決定的 test を、決定的な一時 tree 単位 testと読み取り専用の実 repo 生存確認へ分離しました。指定 harness は合計 54/54 passed です。