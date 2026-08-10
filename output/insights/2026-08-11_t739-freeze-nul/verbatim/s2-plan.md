結論は、単一 choke point を `evidence_contract_sha256()` に置く方針には賛成ですが、親の P1 と P2 の細部には反対です。

- P1: NUL 検査は `_canonical_bytes()` の前ではなく、成功した後・hash 計算の直前に置くべきです。これなら既存の `evidence-contract-json` を新 reason が横取りしません。
- P2: JSON 全域の exact `"path"` key 再帰走査は、loader が path として読まない未知 schema 内の `"path"` まで拒否します。v1 の2種類の schema 位置だけを列挙するべきです。
- P3、P4には同意します。

## 実装変更

### 1. `s8c_preregistration.py`

対象: [orchestrator/campaign/s8c_preregistration.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:329)

現在の `_strict_json()` 終了後、`evidence_contract_sha256()` の直前、現在の 343 行目へ次を挿入します。

```python
def _evidence_contract_path_fields(
    value: Any,
) -> Iterable[tuple[str, str]]:
    """v1 contract で loader が path として読む位置だけを列挙する。"""
    if not isinstance(value, dict):
        return
    conditions = value.get("conditions")
    if not isinstance(conditions, list):
        return

    for condition_index, condition in enumerate(conditions):
        if not isinstance(condition, dict):
            continue

        required_evidence = condition.get("required_evidence")
        if isinstance(required_evidence, list):
            for evidence_index, evidence in enumerate(required_evidence):
                if not isinstance(evidence, dict):
                    continue
                path = evidence.get("path")
                if isinstance(path, str):
                    yield (
                        f"/conditions/{condition_index}"
                        f"/required_evidence/{evidence_index}/path",
                        path,
                    )

        consumer = condition.get("consumer_requirement")
        if isinstance(consumer, dict):
            path = consumer.get("path")
            if isinstance(path, str):
                yield (
                    f"/conditions/{condition_index}/consumer_requirement/path",
                    path,
                )
```

現在の [344–351 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:344) は次で置換します。

```python
def evidence_contract_sha256(raw: bytes) -> str:
    """evidence contract の JSON 意味内容を canonical 化して hash する。"""
    value = _strict_json(raw, what=EVIDENCE_CONTRACT_PATH)
    try:
        canonical = _canonical_bytes(value)
    except (TypeError, ValueError) as exc:
        raise PreregistrationError("evidence-contract-json", str(exc)) from exc

    for pointer, path in _evidence_contract_path_fields(value):
        if "\x00" in path:
            raise PreregistrationError(
                "evidence-contract-path-nul",
                repr(pointer),
            )

    return _sha256(_DOMAIN_EVIDENCE + canonical)
```

検査順は次のとおりです。

1. `_strict_json()`：UTF-8、JSON syntax、duplicate key、NaN/Infinity。
2. `_canonical_bytes()`：既存の canonicalization failure。
3. v1 path field の NUL。
4. SHA-256。

したがって、NUL のない入力について reason の優先順位は完全に不変です。さらに、NUL path と unpaired surrogate が同居する入力も、従来どおり先に `evidence-contract-json` になります。検査を `_canonical_bytes()` より前へ置く P1 では、この既存 reason が新 reason に変わります。

### path 位置の根拠

loader が path として読む場所は、[s8c_preregistration_evidence.py:213–226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:213) の `required_evidence[].path` と、[236–253 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:236) の `consumer_requirement.path` だけです。

現行契約の38箇所もこの2集合に一致します。

- `required_evidence[].path` 26箇所: [契約:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:9), 26, 50, 79, 95, 122, 133, 158, 174, 199, 215, 236, 251, 272, 281, 308, 316, 340, 361, 382, 398, 410, 435, 451, 464, 472。
- `consumer_requirement.path` 12箇所: [契約:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:37), 66, 109, 145, 186, 223, 259, 295, 327, 369, 422, 480。

`field_paths` 内の `"floor_refs[*].path"` などは path 値ではなく識別文字列なので走査しません。

## reason code と message

新設する reason code は厳密に次です。

```text
evidence-contract-path-nul
```

例外 constructor の detail は、path 値ではなく次の `repr(JSON pointer)` だけです。

```python
repr("/conditions/0/required_evidence/0/path")
repr("/conditions/0/consumer_requirement/path")
```

最終 message は厳密に次の形になります。

```text
[evidence-contract-path-nul] '/conditions/0/required_evidence/0/path'
[evidence-contract-path-nul] '/conditions/0/consumer_requirement/path'
```

生の path 値は一切 message に連結しません。

これは既存2層と整合します。

- `read_blob_at()` は [s8c_preregistration.py:967–970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:967) で detail 自体を省略し、[core test:1029–1032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:1029) が message を reason のみに固定しています。
- `_safe_path()` は [evidence.py:180–184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:180) で `repr(where)` を使い、[predicate test:204–209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_predicates.py:204) と [227–232 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_predicates.py:227) が生 NUL/CR/LF の非漏洩を固定しています。

今回の pointer は path 値を含まず、さらに `repr()` するため、生 NUL が message へ入る経路はありません。

## テスト変更

対象: [orchestrator/tests/test_s8c_preregistration_core.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:27)

まず定数を追加します。

```python
EVIDENCE_CONTRACT_FILE = _ROOT / M.EVIDENCE_CONTRACT_PATH
```

現在の `_commit()` 後、[同ファイル:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:109) へ fixture helper を追加します。

```python
def _contract_with_path_suffix(
    *,
    owner: str,
    suffix: str,
) -> tuple[bytes, str]:
    value = json.loads(EVIDENCE_CONTRACT_FILE.read_bytes())
    condition_index = len(value["conditions"]) - 1
    row = value["conditions"][condition_index]

    if owner == "required":
        evidence_index = len(row["required_evidence"]) - 1
        target = row["required_evidence"][evidence_index]
        pointer = (
            f"/conditions/{condition_index}"
            f"/required_evidence/{evidence_index}/path"
        )
    elif owner == "consumer":
        target = row["consumer_requirement"]
        pointer = f"/conditions/{condition_index}/consumer_requirement/path"
    else:
        raise AssertionError(owner)

    target["path"] += suffix
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
    return raw, pointer
```

最後の condition/path を使うため、走査が先頭要素だけで止まる実装も検出できます。

### 単体・回帰テスト

現在の [test_evidence_contract_hash_is_semantic_canonical_json():429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:429) の直後へ追加します。

```python
@pytest.mark.parametrize(
    "owner",
    [
        pytest.param("required", id="required-evidence"),
        pytest.param("consumer", id="consumer-requirement"),
    ],
)
def test_evidence_contract_hash_rejects_nul_path(owner: str) -> None:
    raw, pointer = _contract_with_path_suffix(owner=owner, suffix="\x00alias")
    assert b"\\u0000" in raw
    assert b"\x00" not in raw

    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)

    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == f"[evidence-contract-path-nul] {pointer!r}"
    assert all(control not in str(caught.value) for control in ("\x00", "\r", "\n"))


@pytest.mark.parametrize(
    "control",
    [
        pytest.param("\r", id="cr"),
        pytest.param("\n", id="lf"),
    ],
)
def test_evidence_contract_hash_accepts_non_nul_path_controls(
    control: str,
) -> None:
    raw, _ = _contract_with_path_suffix(owner="required", suffix=control)
    assert len(M.evidence_contract_sha256(raw)) == 64


def test_evidence_contract_hash_accepts_non_path_nul() -> None:
    value = json.loads(EVIDENCE_CONTRACT_FILE.read_bytes())
    value["conditions"][0]["static_only_note"] += "\x00data"
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
    assert len(M.evidence_contract_sha256(raw)) == 64


def test_evidence_contract_hash_accepts_unconsumed_schema_path_nul() -> None:
    raw = json.dumps(
        {"metadata": {"path": "not-a-v1-path\x00data"}},
        ensure_ascii=False,
    ).encode("utf-8")
    assert len(M.evidence_contract_sha256(raw)) == 64


def test_evidence_contract_hash_preserves_canonicalization_reason_before_nul() -> None:
    raw = (
        b'{"conditions":[{"required_evidence":'
        b'[{"path":"x\\u0000\\ud800"}]}]}'
    )
    with pytest.raises(M.PreregistrationError) as caught:
        M.evidence_contract_sha256(raw)
    assert caught.value.reason == "evidence-contract-json"


def test_current_evidence_contract_hash_is_frozen() -> None:
    assert M.evidence_contract_sha256(EVIDENCE_CONTRACT_FILE.read_bytes()) == (
        "c4f3740202de302c9dafc9cecac39165bc2213ebf425d2da8cf7ede91b264471"
    )
```

新規 nodeid は以下です。

- `orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_path[required-evidence]`
- `...::test_evidence_contract_hash_rejects_nul_path[consumer-requirement]`
- `...::test_evidence_contract_hash_accepts_non_nul_path_controls[cr]`
- `...::test_evidence_contract_hash_accepts_non_nul_path_controls[lf]`
- `...::test_evidence_contract_hash_accepts_non_path_nul`
- `...::test_evidence_contract_hash_accepts_unconsumed_schema_path_nul`
- `...::test_evidence_contract_hash_preserves_canonicalization_reason_before_nul`
- `...::test_current_evidence_contract_hash_is_frozen`

### E2E: 凍結検証

現在の履歴テスト先頭、[同ファイル:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:518) の前へ追加します。

```python
def test_validate_condition_freeze_at_rejects_legacy_frozen_nul_path_contract(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    evidence_raw, pointer = _contract_with_path_suffix(
        owner="consumer",
        suffix="\x00alias",
    )
    _write(root, M.EVIDENCE_CONTRACT_PATH, evidence_raw)

    contract = M.parse_preregistration_markdown(
        (root / M.SOURCE_PATH).read_bytes()
    )
    legacy_value = M._strict_json(
        evidence_raw,
        what=M.EVIDENCE_CONTRACT_PATH,
    )
    legacy_evidence_sha = M._sha256(
        M._DOMAIN_EVIDENCE + M._canonical_bytes(legacy_value)
    )
    record_raw = M._canonical_bytes(
        M._record_document(
            1,
            None,
            contract,
            legacy_evidence_sha,
            "pre-T-739 NUL fixture",
            None,
        )
    )
    _write(root, M.generation_path(1), record_raw)
    head = _commit(root, "install legacy NUL-bound g1")

    with pytest.raises(M.PreregistrationError) as caught:
        M.validate_condition_freeze_at(root, head)

    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == f"[evidence-contract-path-nul] {pointer!r}"
    assert "\x00" not in str(caught.value)
```

nodeid:

```text
orchestrator/tests/test_s8c_preregistration_core.py::test_validate_condition_freeze_at_rejects_legacy_frozen_nul_path_contract
```

旧 hash をテスト内で直接再現するのは意図的です。既存の `_record_raw()`（111–132行）と `_install_g1()`（135–138行）は修正後の `evidence_contract_sha256()` を呼ぶため、攻撃 fixture の組立て段階で拒否され、履歴走査まで到達できません。

このテストは旧実装なら、NUL 契約と一致する g1 record を受理します。修正後は履歴走査の [s8c_preregistration.py:1416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1416) で新 reason になります。

### E2E: 凍結発行

現在の `test_prepare_revision_is_exclusive_create()`、[core test:969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:969) の前へ追加します。

```python
def test_prepare_revision_rejects_nul_path_contract_before_create(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    evidence_raw, pointer = _contract_with_path_suffix(
        owner="required",
        suffix="\x00alias",
    )
    _write(root, M.EVIDENCE_CONTRACT_PATH, evidence_raw)
    destination = root / M.generation_path(1)

    with pytest.raises(M.PreregistrationError) as caught:
        M.prepare_revision(
            root,
            revision_reason="must reject NUL path contract",
        )

    assert caught.value.reason == "evidence-contract-path-nul"
    assert str(caught.value) == f"[evidence-contract-path-nul] {pointer!r}"
    assert "\x00" not in str(caught.value)
    assert not destination.exists()
```

nodeid:

```text
orchestrator/tests/test_s8c_preregistration_core.py::test_prepare_revision_rejects_nul_path_contract_before_create
```

E2E は [テスト冒頭:2–5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:2) の既存方針どおり、`tmp_path` と `_init_repo()`（84–96行）、`_write()`（99–103行）、`_commit()`（105–108行）を使います。Git 履歴自体は作りますが、実プロジェクト repository・index・freeze namespace には触れない使い捨て repository です。履歴検証を mock すると E2E でなくなるため、この既存 fixture が適切です。

## 受理集合の差分

旧実装で hash を返す入力集合を、`_strict_json(raw)` と `_canonical_bytes(value)` の双方が成功する `A` とします。次を `T` とします。

```text
T = A のうち、parsed value の
    conditions[i].required_evidence[j].path
    または conditions[i].consumer_requirement.path
    が str で、その値に U+0000 を1個以上含むもの
```

| 入力集合 | 変更前 | 変更後 |
|---|---|---|
| `T` | hash を返して受理 | `evidence-contract-path-nul` で拒否 |
| `A \ T` | hash を返して受理 | 同じ canonical bytes・同じ hash を返して受理 |
| `_strict_json` が失敗 | 既存 reason で拒否 | 同じ reason で拒否 |
| `_strict_json` 成功後に `_canonical_bytes` が失敗 | `evidence-contract-json` | 同じ `evidence-contract-json` |

したがって、「変更前は受理、変更後は拒否」の差分は厳密に `T` だけです。これは loader が `_safe_path()` に渡す2種類の path 位置と一致し、T-739 の穴に過不足なく対応します。

特に次は変更しません。

- path 値の CR/LF: `"\x00"` だけを比較するため、core hash は従来どおり通ります。
- `static_only_note` など path 以外の NUL: 通ります。
- unknown key、condition count、schema version 等の schema 違反: schema loader を呼ばないため従来どおり通ります。
- schema 違反と `T` が同居する場合だけは、対象 path NUL があるため拒否します。
- loader が読まない未知位置の `{"path": "...NUL..."}`: 通ります。これを拒否するのが親 P2 の過剰拒否です。

現行契約は `T` に属さないため、hash は `c4f374…6471` のままです。[既存 g1 record:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json:1) は変更しません。

## 親 provisional 裁定への回答

| 裁定 | 判断 | 理由・代案 |
|---|---|---|
| P1 | 一部反対 | 関数と choke point には同意。ただし `_strict_json` 後・`_canonical_bytes` 前では既存 canonicalization reason を横取りする。代案は現在の `s8c_preregistration.py:347–351` で canonicalization 成功後、`return _sha256(...)` 前。 |
| P2 | 反対 | JSON 全域の exact `"path"` 再帰走査は、loader 非到達の `metadata.path` 等も拒否する。代案は `s8c_preregistration.py:343` に上記 `_evidence_contract_path_fields()` を置き、evidence loader の `:213–226` と `:236–253` の2位置だけを列挙する。 |
| P3 | 同意 | reason は `evidence-contract-path-nul`、detail は厳密に `repr(JSON pointer)`。path 値を message に入れない。 |
| P4 | 同意 | CR/LF は検査しない。裁定 (c) は採らず、full loader も流用しない。 |

P2 の到達性については、`conditions` と `required_evidence` の全 list index を走査するため、現在の38 path field に未到達箇所はありません。逆に `field_paths` の文字列、`static_only_note`、未知 schema 内の `"path"` は loader の path 入力ではなく、拒否しません。

## `evidence_contract_sha256()` 呼出し元の全列挙

現行 Python コードの実呼出しは次の6箇所です。`__all__` の [core:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:84) や dataclass field 名は呼出しではありません。

| 呼出し元 | 新検査の発火可能性 | 既存テストへの静的影響 |
|---|---|---|
| 履歴検証 [core:1416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1416) | あり。freeze が存在する各履歴状態の evidence blob が `T` なら発火 | 現行契約は NUL-free。既存履歴 fixture の契約も NUL-free |
| 凍結発行 [core:1725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1725) | あり。worktree contract が `T` なら destination 作成前に発火 | 既存 `test_prepare_revision_is_exclusive_create` の dummy contract は `T` 外 |
| `semantic_contract_sha256` [evidence.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:272) | 通常なし。直前の `load_contract_bytes()` が target NUL を `_safe_path` で先に拒否 | 既存 loader reason `contract-path-control-char` は不変 |
| `_record_raw` test helper [core test:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:120) | NUL fixture を渡せば発火するが、現行利用は `{"predicates":[]}` | 既存 freeze tests の setup は変わらない |
| canonical JSON test [core test:432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:432) | なし。両入力に path/NUL がない | 同一 hash assertion は維持 |
| repository invariant [invariant test:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_invariant.py:158) | 現行契約では発火しない | g1 の固定 hash と一致したまま |

静的には既存 assertion を赤化させる入力は見当たりません。ただし、指示どおり pytest は実行しておらず、「緑」とは判定していません。ファイル変更も行っていません。

## 総括

1. 変更ファイル: `orchestrator/campaign/s8c_preregistration.py` と `orchestrator/tests/test_s8c_preregistration_core.py` の2件。docs・契約 JSON・既存 g1 record は変更しない。
2. 追加テスト: hash 単体2系統、CR/LF・非 path NUL・schema 境界、reason 順序、固定 hash、`prepare_revision` 発行 E2E、履歴検証 E2E。
3. 親 brief への反対点: P1 の canonicalization 前配置と、P2 の JSON 全域 exact `"path"` 走査。P3/P4には同意。
4. 残る危険: v1 schema に新しい path 位置を追加した際は列挙 helper の同時更新が必要。pytest は未実走のため、実装子が所定 runner で確認する必要がある。
