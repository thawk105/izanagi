## 総括

**判定: NO-GO — real 1 件。**

D1〜D5 の実装差分は裁定どおりで、通常の exact built-in tuple では受理集合の余分な拡大はありません。しかし、削除前の件数 assert が拒否していた production-only 入力を、変更後の D4 と内容 oracle の双方が受理する具体例が存在します。段 4 の「D4 で現行検出力を完全に保つ」という判断は成立しません。

pytest は実行しておらず、緑とは報告しません。実測は Git 差分、静的検索、書込みなしの Python in-memory probe のみです。

### A-1 — real: 削除した件数 assert に検出力の純減がある

(a) 具体的な失敗シナリオ:

1. production の台帳を、実体としては既存 38 件＋未承認 1 件を持つ `tuple` subclass にする。
2. `len()` は通常どおり 39 を返す。
3. `__iter__` は呼出元が `test_known_violation_ledger_matches_literal_entries` の場合だけ未承認行を隠し、それ以外では 39 件すべてを返す。
4. 変更後は次がすべて通る。
   - `observed == expected`: literal test にだけ 38 件を返すため通る。
   - `expected` の SHA 一意性: `expected` は未変更なので通る。
   - registry 件数: registry は 39 件、台帳の `len()` も 39 なので通る。
   - registry 値 tuple: underlying tuple の 39 件と registry の 39 件が一致して通る。
   - real-commit 検査: 固定された 35 SHA しか選択しないため、新しい未承認 SHA は検査されない。
5. 削除前の `assert len(KNOWN_PROVENANCE_VIOLATIONS) == 38` だけは `39 == 38` で確実に失敗する。

書込みなし probe の実測結果:

```text
caller-split-old-count: False
caller-split-new-content: True
caller-split-new-registry-count: True
caller-split-new-registry-values: True
```

(b) file:line 根拠:

- production は `tuple` subclass を `isinstance` で許す: [tools/check_ai_provenance.py:591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:591)
- `KnownViolationSpec` subclass も同様に許す: [tools/check_ai_provenance.py:598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:598)
- 内容 oracle は polymorphic iteration から `observed` を作る: [test_check_ai_provenance.py:1386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1386)
- 内容比較と SHA 一意性: [test_check_ai_provenance.py:1448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1448)
- D4 と直後の値比較: [test_check_ai_provenance.py:1913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1913)
- real-commit 検査は固定 35 SHA: [test_check_ai_provenance.py:1458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1458)
- 段 4 は D4 により検出力を「完全に保つ」とした: [s4-adjudication.md:36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t940-ledger-count/s4-adjudication.md:36)、[s4-adjudication.md:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t940-ledger-count/s4-adjudication.md:50)

これは段 4 で認識済みの subclass 族ですが、「D4 により検出力は一つも失われない」という根拠を反証する新しい具体形です。production だけを変え、test は変更しない入力なので、単に「攻撃者は test も変更できる」として除外できません。

(c) 直し方（逐語）:

`test_known_violation_ledger_matches_literal_entries` の先頭、台帳を一度でも反復する前に次を追加する。

```python
    assert type(provenance.KNOWN_PROVENANCE_VIOLATIONS) is tuple
    for spec in provenance.KNOWN_PROVENANCE_VIOLATIONS:
        assert type(spec) is provenance.KnownViolationSpec
        assert type(spec.commit) is str
        assert type(spec.expected_finding_kind) is str
        assert type(spec.ruling) is str
        assert type(spec.note) is str
        assert type(spec.expected_finding_value) is str
```

その上で、D4 の件数 assert は exact tuple・重複拒否・直後の tuple 比較に完全に含意されるため、次を削除するのが明快です。

```python
    assert len(registry) == len(provenance.KNOWN_PROVENANCE_VIOLATIONS)
```

直後の次の行は維持します。

```python
    assert tuple(registry.values()) == provenance.KNOWN_PROVENANCE_VIOLATIONS
```

つまり、**D4 の削除単独は悪化**しますが、**exact-type guard を実効保証にして D4 を削除する案は、現在の部分的な subclass 検出より強い**です。段 4 D4 の再裁定が必要です。

### A-2 — refuted: D1〜D5 以外の差分が混入した

`db778860f5179ebb748679bbdd914bd0859ba100` は対象 test のみ、`3 insertions / 4 deletions` でした。

- D1: 関数名だけ改名。
- D2: `len(...) == 38` だけ削除。
- D3: `== 38` を `== len(expected)` に置換。
- D4: registry の `== 38` を台帳長との比較へ置換。
- D5: `observed == expected`、38 行の `expected`、両 finding-kind assert は無変更。
- `tools/check_ai_provenance.py` の差分は 0。
- `db778860..HEAD` でも対象 2 ファイルの追加差分は 0。
- `git diff --check` は無出力、rc=0。

整形、空白、`expected` 表、production への指示外変更はありません。

### A-3 — refuted: exact built-in 台帳で通常の拒否経路が抜けた

書込みなし probe で、固定された `expected` に対する次の全ケースが拒否側になることを確認しました。

```text
unapproved-add-caught: True
order-swap-caught: True
commit-change-caught: True
expected_finding_kind-change-caught: True
ruling-change-caught: True
note-change-caught: True
expected_finding_value-change-caught: True
expected-duplicate-caught: True
empty-production-caught: True
empty-expected-caught: True
```

したがって exact built-in 型では以下は refuted です。

- production だけへの未承認 entry 追加
- 既存 entry の五 field の production-only 変更
- entry 順序変更
- `expected` の重複 SHA
- production または literal 表の空化

production 側の重複 SHA も [tools/check_ai_provenance.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:613) で独立に拒否されます。

なお production と `expected` を同時に編集した場合、機械は「承認済み」と「未承認」を区別できません。段 4 の M4 が想定する人間レビュー境界であり、今回の固定 test oracle に対する production 入力検査とは分けました。

### A-4 — refuted: D4 は完全な恒真である

完全な恒真ではありません。実体 39 件、`__len__` だけ 38 を返す tuple subclass では実測上、

```text
len-liar: 39 38 False
```

となり、D4 は発火します。

ただし段 4 の「価値があるのは `__len__` を偽る型だけ」という限定は厳密ではありません。実際の条件は、`_known_violation_registry()` が反復して得た一意 entry 数と、容器が報告する `len()` が違うことです。`__iter__` 側だけが件数を変える subtype でも発火します。

### A-5 — refuted: 旧 node 名の active consumer が残った

全 tracked file に対する完全一致検索結果:

```text
旧 node 名: 0 file
新 node 名: 1 file
```

旧 node 名を要求する pytest 設定、skip/deselect、tracked 検査は残っていません。

### 実測上の注意

1 回、履歴 JSON 内の過去 pytest 収集 stdout に検索が当たり、推奨の 200 行／20 KB を超えました。作業は継続し、その後は `git grep -l/-c` に絞って再検査しました。結論は絞り直した結果に基づきます。Web・外部ネットワーク取得は一切行っていません。