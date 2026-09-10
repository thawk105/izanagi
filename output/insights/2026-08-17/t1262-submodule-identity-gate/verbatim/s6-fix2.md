## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| G1 | partial | seal 前だけ transport key を許可する実装済み。pytest 未実走 |
| G2 | partial | `includeif.*` と絶対 `core.worktree` を別理由で固定済み。pytest 未実走 |
| G3 | partial | 回帰原因を修正し対象 10 node を投入したが、基盤 `rc=16` で未実走 |
| G4 | partial | seal 前後の境界と静的禁止 key の回帰 node を追加済み。pytest 未実走 |

`regressed` と判定した所見はありません。

## 診断への異論

なし。

## 変更内容

- [tools/codex_reasoning_ab.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1118)
  - `_submodule_inventory` に `allow_builder_transport=False` を追加。
  - 再帰を含む `_submodule_worktree_state` へ値を伝播。
- [tools/codex_reasoning_ab.py:1268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/tools/codex_reasoning_ab.py:1268)
  - `_seal_git_object_closure` だけが `allow_builder_transport=True` を指定。
  - verify、relocation、内容同一性経路は既定の strict 判定を維持。
- [test_codex_reasoning_ab.py:1647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:1647)
  - relocation fixture を production と同じ封緘済み base に修正。
- [test_codex_reasoning_ab.py:1841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:1841)
  - G2 は node 分割を採用。既存 node は derived copy の絶対 `core.worktree` 拒否だけを検査し、新 node で `includeif.*` 拒否理由を完全一致で固定。
- [test_codex_reasoning_ab.py:3111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity/orchestrator/tests/test_codex_reasoning_ab.py:3111)
  - seal 前の transport key 受理、seal 後の strict 拒否、seal 前の静的禁止 key 拒否を追加。

F1〜F10 の production 検査は削除・緩和していません。RA3 も実装していません。

## 追加・変更したテスト

- `orchestrator/tests/test_codex_reasoning_ab.py::test_derived_preflight_rejects_path_dependent_absolute_core_worktree`
- `orchestrator/tests/test_codex_reasoning_ab.py::test_derived_preflight_rejects_forbidden_includeif_config`
- `orchestrator/tests/test_codex_reasoning_ab.py::test_seal_allows_preseal_transport_but_strict_inventory_rejects_postseal`
- `orchestrator/tests/test_codex_reasoning_ab.py::test_seal_preflight_rejects_forbidden_static_config`
- 封緘済み fixture の影響範囲:
  - `test_shared_base_copy_preserves_metadata_and_relocates_submodules`
  - `test_snapshot_relocation_preflight_rejects_absolute_gitdir[...]`
  - `test_snapshot_relocation_preflight_rejects_absolute_core_worktree[...]`

## 実走結果

`fix2-evidence.txt` の 10 nodeと新設 3 nodeを `tools/run_tests.py` へ投入しましたが、いずれも pytest 起動前に停止しました。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
rc=16
```

したがってテストは実装済み・未実走であり、緑とは報告しません。

静的検査は成功しました。

```text
git diff --check -- tools/codex_reasoning_ab.py orchestrator/tests/test_codex_reasoning_ab.py
python3 -m py_compile tools/codex_reasoning_ab.py orchestrator/tests/test_codex_reasoning_ab.py
```

## 波及と残件

- `_build_snapshot_base` と synthetic fixture の seal 前 inventory が transport key で落ちる回帰を解消する変更です。
- `verify_snapshot`、`_preflight_snapshot_relocation`、内容同一性 helper の呼出しは指定なしのため strict のままです。
- `core.fsmonitor`、`filter.*`、`include.path`、`includeif.*` などは seal 前でも許可されません。
- 親環境で evidence 10 node、新設 3 node、焦点集合全体の再走が必要です。
- docs 編集および commit は行っていません。作業ツリー上の変更対象は指定された 2 ファイルのみです。

## 総括

回帰原因だった seal 前 inventory の strict transport 判定を、封緘前後の明示的な境界へ修正しました。  
strict 認証境界は verify、relocation、内容同一性経路に維持しています。  
`includeif.*` と絶対 `core.worktree` は別 node で単独理由を固定しました。  
基盤 `rc=16` のため、最終判定は親の計算ノード再走待ちです。