## 総括

**plan v3 を実装済み・pytest は未実走です。** docs 編集・commit はしていません。

変更した3ファイル：

- [checker](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2803-unit-impl/tools/check_ai_provenance.py:2269)：`_attribute_candidates` を新設。merge 第1親 diff の祖先 dir を候補に追加。`_attribute_fingerprint` を文字列返値へ戻し、`_receipt_bindings`、`_receipt_prefix`、`_publish_audit_receipt`、`_audit_history` から候補保存・包含検査を撤去。schema は1。
- [テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2803-unit-impl/orchestrator/tests/test_check_ai_provenance.py:8265)：T-pos-1〜T-neg-3 を追従。T-neg-6 `test_attribute_retired_directory_reintroduced_falls_back` を追加。`test_attribute_candidates_damage_falls_back`、`test_attribute_candidates_extra_path_falls_back` と専用 helper を削除。
- [probe](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2803-unit-impl/build/probe/t2803_receipt_attr_cold_rate.py)：新形の判定を digest の隣接比較だけに変更。候補増減は `_attribute_candidates` で集計。

base `f94b61fc8` の全既存テスト関数は **AST 比較で変更・削除とも0件**。3ファイルの構文検査と `git diff --check` は成功しました。

焦点走は次を試行しましたが、`qstat -Q preflight rc=1` により runner が rc=16、`child_started=false` で終了しました。テスト結果ではありません。

```bash
python3 tools/run_tests.py orchestrator/tests/test_check_ai_provenance.py \
  -k 'attribute or many_commit_delta_warm_hit or receipt_first_valid_nonempty_delta_stops' -q
```

**変異対応表（静的予測・変異実走なし）**

nodeid は `orchestrator/tests/test_check_ai_provenance.py::` に表の名前を連結します。

| 変異 | 赤になる test nodeid の末尾 | 最初の赤理由 |
|---|---|---|
| M-1 実在 entry も除外 | `test_additional_attribute_sources_fall_back[untracked]` | 属性変更を見逃し、rc=1 期待が0 |
| M-2 absent 再包含 | `test_attribute_absent_directory_addition_warm_hit` | 新 dir 追加前後の digest 同一 assertion が失敗 |
| M-3 unreadable 除外 | `test_attribute_candidate_lstat_unreadable_falls_back` | digest 不一致 assertion が失敗 |
| M-4 履歴由来候補を除外 | `test_attribute_retired_directory_falls_back` | digest 不一致 assertion が失敗 |
| M-4 同上 | `test_attribute_retired_directory_reintroduced_falls_back` | retired dir の候補包含 assertion が失敗 |
| EQ-1 同集合・同順序 | なし | 等価。SURVIVED 期待 |

exact な置換対象行と置換後は以下です。各対象行の出現数は1と確認済みです。

M-1〜M-3 共通の対象行：

```python
        if source != {"kind": "absent"}:
```

置換後：

```python
        if False:
```

```python
        if True:
```

```python
        if source != {"kind": "absent"} and source.get("kind") != "unreadable":
```

M-4：

```python
    for name in paths.split(b"\0"):
```

→

```python
    for name in ():
```

EQ-1：

```python
    return tuple(sorted(attribute_paths))
```

→

```python
    return tuple(sorted(set(attribute_paths)))
```

**指定 grep の結果**

以下はファイル名だけを `C=tools/check_ai_provenance.py`、`T=orchestrator/tests/test_check_ai_provenance.py` に短縮した全結果です。`base64`・`zlib`・受領証の `attribute_candidates` field は残っていません。

```text
C:2237:_RECEIPT_SCHEMA = 1
C:2269:def _attribute_candidates(head, *, policy=None) -> tuple[bytes, ...]:
C:2308:def _attribute_fingerprint(head, *, policy=None) -> str:
C:2363:    candidates = _attribute_candidates(head, policy=policy)
C:2375:def _receipt_bindings(head, scope_epoch, implementation_epoch, ancestry):
C:2386:        "schema": _RECEIPT_SCHEMA,
C:2408:        "attributes": _attribute_fingerprint(head, policy=policy),
C:2468:        _, current = _receipt_bindings(
C:2512:                or receipt["schema"] != _RECEIPT_SCHEMA
C:2600:            path, bindings = _receipt_bindings(
C:2684:            "schema": _RECEIPT_SCHEMA, "returncode": 0, "bindings": bindings,
T:8163:    before = provenance._attribute_fingerprint(head)
T:8165:    after = provenance._attribute_fingerprint(head)
T:8167:    assert provenance._attribute_fingerprint(head) == after
T:8169:    assert provenance._attribute_fingerprint(head) != after
T:8220:def test_attribute_fingerprint_is_independent_of_tip(tmp_path, monkeypatch):
T:8229:    assert provenance._attribute_fingerprint(old) == provenance._attribute_fingerprint(tip)
T:8267:    before = provenance._attribute_fingerprint(_git(tmp_path, "rev-parse", "HEAD"))
T:8268:    candidates_before = provenance._attribute_candidates(_git(tmp_path, "rev-parse", "HEAD"))
T:8270:    after = provenance._attribute_fingerprint(tip)
T:8272:    assert set(candidates_before) < set(provenance._attribute_candidates(tip))
T:8282:    before = provenance._attribute_fingerprint(_git(tmp_path, "rev-parse", "HEAD"))
T:8283:    candidates_before = provenance._attribute_candidates(_git(tmp_path, "rev-parse", "HEAD"))
T:8286:    after = provenance._attribute_fingerprint(tip)
T:8288:    assert set(candidates_before) < set(provenance._attribute_candidates(tip))
T:8299:    before = provenance._attribute_fingerprint(merge)
T:8305:    after = provenance._attribute_fingerprint(tip)
T:8322:    before = provenance._attribute_fingerprint(head)
T:8323:    candidates_before = provenance._attribute_candidates(head)
T:8328:    after = provenance._attribute_fingerprint(head)
T:8330:    assert candidates_before == provenance._attribute_candidates(head)
T:8340:    before = provenance._attribute_fingerprint(head)
T:8341:    candidates_before = provenance._attribute_candidates(head)
T:8351:    after = provenance._attribute_fingerprint(head)
T:8353:    assert candidates_before == provenance._attribute_candidates(head)
T:8370:    assert b"tools/retired/.gitattributes" in provenance._attribute_candidates(deleted)
T:8374:    before = provenance._attribute_fingerprint(deleted)
T:8382:    assert provenance._attribute_fingerprint(tip) != before
T:8446:    monkeypatch.setattr(provenance, '_receipt_bindings', lambda *a: (_ for _ in ()).throw(RuntimeError('cold')))
```

未完了は親側の焦点走・変異 matrix・E-1/E-2 実測です。保存直前の bindings 再計算は裁定どおり維持したため、受領証を発行する走行では履歴候補列挙も再実行されます。