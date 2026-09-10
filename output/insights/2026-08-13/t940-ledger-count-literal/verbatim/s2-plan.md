## 総括

変更対象は `orchestrator/tests/test_check_ai_provenance.py` のみとし、4 編集を推奨する。

- 件数入り nodeid を `test_known_violation_ledger_matches_literal_entries` へ改名する。
- production 件数の `== 38` は削除する。
- expected 内 SHA の一意性検査は `len(expected)` 基準へ変える。
- (P2) の registry 件数 assert は dynamic 置換せず削除する。置換案は直後の tuple 比較に厳密に含意され、現実装でも成功復帰時には必ず真だからである。

`assert observed == expected` が production 全 entry の5フィールド・順序・件数を引き続き完全固定する。意図して広がる受理集合は、expected も更新された承認済み件数変更だけである。

## 静的実測

- 必読 brief、指定された test 範囲、production 台帳全体（現行 225–569）、`_known_violation_registry` 全体（588–694）は読了した。読めなかったものはない。
- AST 静的計数:
  - production: `Tuple`、38要素、SHA 38種。
  - `expected`: `Tuple`、38要素、`Starred` なし。
- git 状態は clean。書き込みは行っていない。
- pytest は実行しておらず、緑とは判定しない。brief 記載の「2 failed, 281 passed」は親の計算ノード実測であり、私の実走結果ではない。

以下、元行は現行 clean tree、変更後行は2行削除後の予測行番号である。

## 編集プラン

対象: [orchestrator/tests/test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1328)

1. 現行 1328、変更後 1328 — nodeid 改名

変更前の逐語:

```python
def test_known_violation_ledger_is_exactly_thirty_eight_literal_entries():
```

変更後の逐語:

```python
def test_known_violation_ledger_matches_literal_entries():
```

同 file の直後にある現行 1459 の `test_known_violation_ledger_matches_real_commit_findings` と同じ `ledger_matches_*` 規約に揃う。テスト本体は変わらないため検出力は不変。

2. 現行 1448 — production 件数固定を削除

変更前の逐語:

```python
    assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == 38
```

変更後:

```text
行自体を削除。代替文なし。
```

後述のとおり、変更後 1448 の `assert observed == expected` が同じ長さ条件を厳密に含む。失われるのは意図的に外す「絶対件数38」だけで、未知追加・削除・内容 drift の検出は失われない。

3. 現行 1450、変更後 1449 — expected の SHA 一意性を可変長化

変更前の逐語:

```python
    assert len({row[0] for row in expected}) == 38
```

変更後の逐語:

```python
    assert len({row[0] for row in expected}) == len(expected)
```

集合の要素数と元 tuple の要素数が等しいのは、全 `row[0]` が一意な場合に限る。件数に依存せず、重複 SHA の検出力は同値に維持される。

4. 現行 1914 — registry 件数固定は削除を推奨

変更前の逐語:

```python
    assert len(registry) == 38
```

変更後:

```text
行自体を削除。代替文なし。
```

直後の次の行は逐語維持し、変更後 1913 になる。

```python
    assert tuple(registry.values()) == provenance.KNOWN_PROVENANCE_VIOLATIONS
```

`len(registry) == len(provenance.KNOWN_PROVENANCE_VIOLATIONS)` への置換は推奨しない。tuple equality が成立すれば両 tuple の長さは等しく、かつ `len(tuple(registry.values())) == len(registry)` なので、この dynamic length assert は直後の assert に完全に含意される。

5. 内容・kind 集合 oracle は逐語維持

現行 1449、変更後 1448:

```python
    assert observed == expected
```

現行 1451–1456、変更後 1450–1455:

```python
    assert provenance._LEDGER_FINDING_KINDS == frozenset({
        "missing-ai-agent", "missing-codex-author", "malformed-ai-agent",
    })
    assert provenance._NOTE_REQUIRED_FINDING_KINDS == frozenset({
        "malformed-ai-agent",
    })
```

production と docs は変更しない。

## `observed == expected` の長さ含意

現行 1386–1395 の構築式は次の逐語である。

```python
    observed = tuple(
        (
            spec.commit,
            spec.expected_finding_kind,
            spec.ruling,
            spec.note,
            spec.expected_finding_value,
        )
        for spec in provenance.KNOWN_PROVENANCE_VIOLATIONS
    )
```

`expected` は現行 1396 の `expected = (` から1447の `)` までの直接 tuple display で、AST 実測では38要素・展開要素なしだった。

Python の意味論上、generator は `KNOWN_PROVENANCE_VIOLATIONS` の各 `spec` につき常に1個の5-tupleを生成し、filter はない。したがって、

```text
len(observed) == len(provenance.KNOWN_PROVENANCE_VIOLATIONS)
```

が成り立つ。両辺とも組み込み `tuple` なので、`observed == expected` が真になるには、順番どおりの全要素が等しく、かつ長さも等しくなければならない。従って、

```text
observed == expected
⇒ len(observed) == len(expected)
⇒ len(KNOWN_PROVENANCE_VIOLATIONS) == len(expected)
```

は厳密に成立する。長さが異なれば tuple equality は真にならない。構築中に例外が出てもテストは緑にならない。このため現行1448の明示的件数 assert は受理集合を狭める追加条件ではなく、同じ失敗を先に出すだけである。

## (P2) の判定

推奨は「削除」。

[tools/check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:588) の実装は次の順序である。

- 596で空 dict を作る。
- 597から全 spec を走査する。
- 613–617で `spec.commit in registry` を検出した時点で `RuntimeError`。重複 SHA を黙って折り畳まない。
- 全検証後、693で `registry[spec.commit] = spec`。
- 694で返す。

したがって現実装が正常復帰した時点で、source tuple の各要素は同順序で1対1に registry へ入っている。さらに直後の値 tuple 比較そのものが長さを含むため、dynamic length 置換は二重に冗長である。

重複 guard が将来誤って削除され、production tuple に同一 SHA が2件入った場合でも、dict の上書きにより `tuple(registry.values())` が source tuple より短くなり、変更後1913の値 tuple 比較が赤になる。現行実装なら、その前の変更後1911にある `_known_violation_registry()` 呼び出し自体が例外で赤になる。

## 改名による参照影響

repo 全体で現行 nodeid の完全一致検索を行った結果、hit は定義行1328のみだった。

- docs: 参照なし。
- mutation-spec / mutation-ledger: 現行 nodeid の参照なし。
- CI設定: 参照なし。
- skip / deselect / ignore 一覧: 参照なし。
- その他の tracked file: 参照なし。

したがって改名で壊れる参照はない。過去成果物には `...thirty_four...` など別の歴史的 nodeid が残るが、今回の現行 nodeid への参照ではなく、改名対象でもない。repo 外の親 brief は歴史的段1成果物なので編集しない。

## 必須3変異の発火先

いずれも変更後1448の次の assert が保証された検出点になる。

```python
    assert observed == expected
```

| production 変異 | 赤になる変更後行 | 理由 |
|---|---:|---|
| 未知の39件目を追加 | 1448 | `observed` が39要素、`expected` が38要素で tuple 長不一致 |
| 既存 entry の `note` を1文字変更 | 1448 | 対応する内側5-tupleの4番目が不一致 |
| 既存 entry を1件削除 | 1448 | `observed` が37要素、`expected` が38要素で tuple 長不一致 |

note の変更文字が禁止文字や非記述文字なら、別途 registry 検証も例外になる可能性があるが、文字種に依存しない完全一致の保証点は1448である。

## 将来の entry 追加時の更新面

テスト側に限れば、必要なのは変更後の `expected` 表への1行追加だけになる。

repo 全体を文字どおり数えるなら、当然ながら実体である `tools/check_ai_provenance.py` の `KNOWN_PROVENANCE_VIOLATIONS` への追加と、test の `expected` 行の2箇所が必要である。それ以外の件数、nodeid、registry test、CI・skip・docs の更新は不要。

現行1459の real-commit test は既に38件すべてではなく固定35件、現行2530の empty-registry test は固定30件の歴史的部分集合を検証している。`_audit_history` は選択 commit と registry key の積集合だけを対象にするため、新しい別 SHA を加えてもこれらの固定部分集合を更新する必要はない。追加 entry も同じ end-to-end 部分集合へ含めたい場合の更新は任意の被覆拡張であり、受入に必要な更新面ではない。

実装後の静的確認は、旧 nodeidと3個の `== 38` が対象 test から消えたこと、AST parse 成功、`git diff --check`、変更ファイルが対象 test だけで production/docs diff が空であることを確認する。pytest 実測は brief どおり親へ残す。