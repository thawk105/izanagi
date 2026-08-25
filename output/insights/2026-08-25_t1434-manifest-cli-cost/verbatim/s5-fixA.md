## 直した赤

1. `test_find_rollout_pinned_rejects_child_candidate_before_full_scan[type-a]`
2. `test_find_rollout_pinned_rejects_child_candidate_before_full_scan[type-b]`

原因は monkeypatch 偽物が新しい `expected_sha256=` keyword を受け取れず、`TypeError` が握り潰されていたことです。

偽物へ keyword-only の `expected_sha256` を追加し、渡された値が `verified_content` の SHA-256 と一致することを assert しました。実検証関数にも同じ値を渡しています。

3. `test_verify_snapshot_submodule_gate_rejects_default_spec_path`

`_snapshot_spec` の偽物へ keyword-only の `task_manifest` を追加しました。値は単に受け取るだけでなく、期待する `TOOL.TASK_MANIFEST` object と同一であることを `is` で assert しています。併せて `case == "POS"` も確認します。

## except Exception の射程についての判断

狭めました。

```python
except (OSError, ValidationError):
    pass
```

- SHA 不一致の `ValidationError` は従来どおり全走査へ fallback します。
- rollout 読み取りや path 解決の `OSError` も従来どおり fallback します。
- `TypeError`、`AttributeError`、`MemoryError` は握り潰さず伝播します。
- 正常入力の受理集合は変えず、実装欠陥や実行継続不能な例外の扱いだけを fail-fast にしています。

`TypeError` と `AttributeError` の伝播を確認する回帰テストを追加し、既存の `MemoryError` テストも伝播期待へ修正しました。ただし後述の基盤障害により未実走です。

## 変異 M14 の単一理由性の確認結果

実装子 A の報告はコード上で正しいです。

`_load_task_manifest()` の top-level `dict` 検査を外しても、直後の `_validate_task_manifest(value)` が最初に `isinstance(manifest, Mapping)` を検査し、同じ配列を拒否します。

したがって現行テストでは loader の検査だけを無効化した単一理由性を確保できません。M14 は登録取り下げが妥当です。

## 実走結果

実行コマンド:

```text
python3 tools/run_tests.py orchestrator/tests/test_codex_reasoning_ab.py
```

結果:

- runner rc: `16`
- 原因: `qstat -Q preflight rc=1`
- child: 未起動
- failed: 取得できず
- passed: 取得できず
- skipped: 取得できず

したがって成果は「実装済み・未実走」です。実装子 A の未実走項目で今回 pytest 実走できた nodeid はありません。

直前の親実測で赤だった次の 3 nodeid は修正済みですが、現在の結果は未確認です。

- `test_find_rollout_pinned_rejects_child_candidate_before_full_scan[type-a]`
- `test_find_rollout_pinned_rejects_child_candidate_before_full_scan[type-b]`
- `test_verify_snapshot_submodule_gate_rejects_default_spec_path`

新たな回帰 nodeid の有無も、child 未起動のため判定できません。AST parse と `git diff --check` は成功しました。

## 総括

指定された 3 件の原因を修正し、keyword の値を明示的に assert しました。危険な `except Exception` は入力由来の検証失敗だけを fallback する境界へ狭めました。M14 は上流 validator と拒否理由が重なるため、単一理由性なしと確認しました。

編集は指定された 2 ファイルだけです。docs、凍結成果物、`_aggregate_verified`、`resource_ledger` は変更せず、commit も行っていません。