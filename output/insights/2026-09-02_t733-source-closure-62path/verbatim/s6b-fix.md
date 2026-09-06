## 総括

私有 helper への直接呼出しを公開関数 1 件へ置換しました。  
24 path 全体の commit blob digest 照合と例外理由は維持しています。  
commit、定数、epoch domain、所有外 file は変更していません。

## 所見への対応

実装済み・未実走。

- [contract_loader_binding.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/contract_loader_binding.py:404): 公開照合関数を追加。
- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/artifact_admission.py:999): 私有 helper 呼出しを公開関数へ置換。
- [test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/tests/test_t671_source_binding.py:746): exact 期待一覧を更新。

## 新しい公開関数の署名と、呼び手からの使われ方

```python
def verify_committed_contract_loader_blobs(
    contract_loader_commit: str,
    contract_loader_blob_sha256s: Mapping[str, str],
    relative_paths: tuple[str, ...],
) -> None
```

歴史 authority の commit、digest map、ordered path tuple を渡します。関数内部で root 検証、commit 検証、tuple 順の全 blob 取得と digest 照合を行います。`CONTRACT_LOADER_RELATIVE_PATHS` は暗黙に使いません。

## 期待一覧へ登録した項目

登録した 1 件:

```text
('artifact_admission.py', '_verify_committed_loader_binding',
 'verify_committed_contract_loader_blobs') 1
```

`_validated_root`、`_require_commit`、`_blob`、`ContractLoaderBindingError` constructor の直接呼出しは削除し、allowlist へ登録していません。例外変換用の `except ContractLoaderBindingError` は維持しています。

## 実走したテスト

テスト本体は未実走です。

- 指定 nodeidを2回試行:
  `orchestrator/tests/test_t671_source_binding.py::test_production_contract_loader_binding_call_sites_are_exact`
- 同 nodeid と歴史 blob mismatch nodeidの collect-only も試行。
- すべて `tools/run_tests.py` が Pegasus dispatch 前の `qstat -Q` で rc=1、runner rc=16。`child_started=false` のためテストも collection も開始されていません。
- 代替の静的 AST 集計では、actual Counter が更新後の exact 8 項目と一致しました。
- `git diff --check` は成功しました。

## 赤の内訳

- 回帰によるテスト赤: 観測なし。テスト未起動のため判定不能。
- infrastructure: 3 invocation が dispatch infrastructure failure、rc=16。
- contract-loader drift: 未観測。ただし未 commit の production 2 file は closure member のため、drift 検査を実走すれば既知の期待赤になります。

## 波及可能性 (所有外)

`HISTORICAL_RAW` を通る共有 consumer と歴史 fixture が新しい公開関数を経由します。通常 decoder、encode、resume、certified admission の経路と受理集合は変更していません。追跡対象の変更は指定された 3 file だけです。