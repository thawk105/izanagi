静的読解の判定です。pytest は実行していません。親からの「207 passed」は記録としてのみ受領しました。

現行実装の通常経路は、D228 の +1／据置／no-op 拒否、T-657 の linux-baremetal 据置 + pegasus g1→g2、ever-active 解決を満たしています。ただし、回帰テストをすり抜ける誤実装が複数あります。

### 1. changed env を先頭4件だけ検査する変異が生存する

深刻度: must-fix

根拠: `orchestrator/tests/test_env_contract_activation.py:554` のテスト自身が「N >= 5 は既知の残穴」と認めています。現行 gate は `orchestrator/campaign/env_contract_activation.py:300` で全件を回していますが、4 env までしか node がありません。

誤実装片:

```python
# 現行 loop の本体はそのまま
for predecessor, successor in changed[:4]:
    result = is_valid_registered_successor(predecessor, successor)
    # 現行の exact-bool / False / 例外処理
```

この変異は現行の全 test node を通ります。

成果物影響: 5番目以降の env が `False` でも activation record が受理され、certified 選択・レポート・試行台帳の contract 参照が未検証状態になります。

修正案: 5 env 以上の fixture を追加し、5番目の callback が `False`／非 bool／例外の場合に拒否し、全 env の呼出し列を exact assert する。

### 2. serial 2 の pair だけ検査する変異が生存する

深刻度: must-fix

根拠: `orchestrator/tests/test_env_contract_activation.py:598` の「途中 no-op」は悪い pair が serial 2 にあります。`orchestrator/tests/test_env_contract_activation.py:607` の3-recordテストは後続 pair を正例でしか検査していません。

誤実装片:

```python
if previous_rows is not None and serial == 2:
    _validate_activation_transition(
        previous_rows,
        rows,
        activation_serial=serial,
        is_valid_registered_successor=is_valid_registered_successor,
    )
```

成果物影響: serial 3 以降の不正な successor edge が検査されず、無効な terminal contract が certified 選択・レポート・台帳に入ります。

修正案:

```python
def test_transition_rejects_invalid_later_pair():
    records, head = _chain((1, 1), (2, 1), (3, 1))

    def predicate(old, new):
        return not (
            old.env_tag == "env-a"
            and old.generation == 2
            and new.generation == 3
        )

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"successor でない.*env_tag=env-a",
    ):
        _validate(records, head, predicate=predicate)
```

### 3. 後段 env の非 bool／例外を無視する変異が生存する

深刻度: must-fix

根拠: False は2〜4番目も検査されていますが、非 bool と例外は主に最初の changed env だけです。該当箇所は `orchestrator/tests/test_env_contract_activation.py:968`、`:988`、`:1063`、`:1072` です。

誤実装片:

```python
for index, (predecessor, successor) in enumerate(changed):
    try:
        result = is_valid_registered_successor(predecessor, successor)
    except Exception as exc:
        if index == 0 and first_failure is None:
            first_failure = (
                "registered successor 判定中に例外: "
                f"serial={activation_serial} env_tag={successor.env_tag}",
                exc,
            )
        continue

    if index == 0 and type(result) is not bool:
        if first_failure is None:
            first_failure = (
                "registered successor 判定値が exact bool でない: "
                f"serial={activation_serial} env_tag={successor.env_tag}",
                None,
            )
    elif result is False and first_failure is None:
        first_failure = (
            "generation/hash 束縛済み contract が正当な successor でない: "
            f"serial={activation_serial} env_tag={successor.env_tag}",
            None,
        )
```

成果物影響: 後段 env の `1` や例外が成功扱いになり、その env の contract edge だけ未検証のまま受理されます。

修正案: 2番目以降についても非 bool と例外を拒否する node を追加する。`False`、`1`、`None`、`RuntimeError` を各位置で検査する。

### 4. issuer の production adapter 結線を誤っても検出できない

深刻度: must-fix

根拠: 正しい結線は `tools/issue_env_contract_activation.py:206-211` ですが、既存の issuer テスト `orchestrator/tests/test_env_contract_activation.py:1839` と `:1901` は成功／no-op の結果だけを見ており、callback identity や負方向を固定していません。

誤実装片:

```python
is_valid_registered_successor=lambda _predecessor, _successor: True,
```

no-op は numeric gate が先に拒否するため、この変異でも既存 node は通ります。

成果物影響: issuer だけ contract successor 検査を迂回し、head 更新後に未検証の contract pair が certified 選択・レポート・台帳へ流入します。

修正案: issuer テストで `ec.is_valid_successor` を `False` に差し替え、正当な g1→g2 発行が拒否され、ファイルが作成されないことを固定する。併せて渡された callback の identity を assert する。

### 5. adapter が import 時 snapshot を握る変異が生存する

深刻度: must-fix

根拠: 裁定は adapter が呼出し時の module-global `GENERATIONS` を読むと定めています（`s4-adjudication.md:24-32`）。現行実装は `orchestrator/campaign/env_contract.py:403` で呼出し時に読む一方、既存テストは monkeypatch 後も結果が `False` になるケースが中心で、古い snapshot を使っても通ります。

誤実装片:

```python
_GENERATIONS_AT_IMPORT = GENERATIONS

def _is_valid_activation_successor(predecessor, successor):
    def resolve(row):
        try:
            entry = _GENERATIONS_AT_IMPORT[row.env_tag][row.generation - 1]
        except (KeyError, IndexError, TypeError):
            return None
        if (
            entry.generation != row.generation
            or entry.contract.env_tag != row.env_tag
            or entry.contract.contract_sha256 != row.contract_sha256
        ):
            return None
        return entry

    old_entry = resolve(predecessor)
    new_entry = resolve(successor)
    if old_entry is None or new_entry is None:
        return False
    return is_valid_successor(old_entry.contract, new_entry.contract)
```

成果物影響: 現在の `GENERATIONS` と古い snapshot の判定が分裂し、activation の受理集合と certified current/history contract の参照が一致しなくなります。

修正案: monkeypatch で新しい2世代 mapping を設定した後、adapter が新しい `GenerationEntry` を callback に渡す node を追加する。serial 1 だけの synthetic authority ではなく、実際に successor adapter を発火させる。

### fail-open の追跡

`False`、非 bool、通常の `Exception` は、`orchestrator/campaign/env_contract_activation.py:301-328` で first failure として保持され、最後に `ActivationRecordError` になります。後続の `True` による上書きもありません。

一方、`SystemExit` や `KeyboardInterrupt` など `BaseException` は `except Exception` の外へ漏れます（同ファイル `:303`）。これは受理する fail-open ではなくプロセス中断ですが、「判定中の全例外を ActivationRecordError に包む」という契約なら should-fix です。

成果物影響: certified 選択・レポート・台帳の生成が通常の拒否診断ではなくプロセス異常終了になり、拒否結果の参照が失われます。

修正案: `Exception` の対象範囲を明文化し、必要なら専用 node を追加する。`KeyboardInterrupt` まで包むかは運用契約として明示する。

### 不変条件・裁定射程

- `00000001.json` は差分なしで、前後の SHA-256 も一致しています。
- `_ACTIVATION_HEAD_SERIAL` と `_ACTIVATION_HEAD_STATE_SHA256` は変更されていません。
- activation leaf は stdlib import のみで、env 固有 literal も追加されていません。
- T-657 の linux-baremetal 据置 + pegasus g1→g2 は、静的には registry hash、exact +1、`is_valid_successor` の calibration path/SHA 差分を満たします。
- contract 実体 rollback、世代列の再定義、逆引き index の再束縛を新たに防いだという過剰な主張は、実装・docstringには見当たりません。
- テスト差分の no-op／downgrade 期待値の変更は D228 に沿った再著述であり、skip や assert の単純削除ではありません。

ただし、裁定自身が認めるとおり本番 artifact は1 recordのみで、遷移 gate の実 production 発火証拠はまだありません（`s4-adjudication.md:26-32`）。これは今回の順序 override により should-fix とします。

## 総括

判定: **NO-GO**

must-fix 件数: **5**

理由は、現行実装の主経路が正しく見えても、先頭4 env制限、serial 2 pair限定、後段 failure 無視、issuer結線迂回、import snapshot固定という誤実装が、実装済み test node 集合を通過し得るためです。