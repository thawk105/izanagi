## 総括

判定は **NO-GO（real 1 系統）**。通常の literal entry を 1〜N 件追加する変異は `observed == expected` が確実に拒否する。一方、production が許している `tuple` / `str` subclass を使うと、未承認 SHA を registry に登録したまま比較を偽装できる。`:1914` の削除は、この経路に残っていた検出を失う。

最小修正は、件数ではなく production 容器・spec・全5 field の exact type を literal oracle の直前で固定すること。その修正後なら、プランの改名、2個の件数 literal 削除、SHA 一意性の動的化は妥当。

必読資料はすべて読めた。pytest は実行しておらず、緑とは判定しない。親の「2 failed / 281 passed」は brief から読んだ親実測であり、私の実測ではない。

### 所見 A-1 — **real: subclass により未知 entry と内容 drift を偽装できる**

(a) 具体的シナリオは二つある。

1. 未承認39件目の混入:

- `KNOWN_PROVENANCE_VIOLATIONS` を `_Ledger(tuple)` にし、内部には既存38件＋未承認1件を保持する。
- `__iter__` は `test_known_violation_ledger_matches_literal_entries` から呼ばれたときだけ末尾を隠し、checker の `_known_violation_registry()` には39件すべてを返す。
- `__len__` は38、`__eq__` は `True` を返す。
- [production:591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:591) は `isinstance(..., tuple)` なので subclass を受理する。
- planned target は38件だけ観測して literal `expected` と一致する。
- registry は未承認39件目を実際に登録する。
- [registry比較:1915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1915) は左辺が通常 tuple、右辺が subclass なので右辺の `__eq__` が優先され、真になる。

副作用なしの in-memory probe で次を実測した。

```text
target_projection_equal True
registry_real_count 39
source_reported_len 38
registry_tuple_equality True
unknown_is_registered True
```

2. 同件数の内容差替え:

- 実 commit test に含まれない `187fed...` の `.commit` を `AliasStr(str)` に差し替える。
- underlying value は別の未承認 SHA、`__eq__` だけ旧 SHA にも真を返す。
- [production:603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/tools/check_ai_provenance.py:603) の `isinstance(..., str)`、SHA regex、registry 登録をすべて通る。
- literal oracle との比較も真になり、checker は旧 SHA ではなく未承認 SHA を既知違反として扱う。

これも in-memory probe で `projection_equal=True`、新 SHA 登録、旧 SHA 非登録を確認した。pytest 実走ではない。

(b) 現行 nodeid が赤にならない根拠:

- literal test は偽装された38行と `expected` を比較するため通る。
- real-commit test の固定35件には `187fed...`、`9408fb...`、`c96803...` がなく、未承認 SHA も選択しなければ余分な registry row は観測されない。
- production-registry test は planned `len(registry) == 38` 削除後、偽装された tuple equality だけになる。
- production registry をそのまま使う残りの node は合成 commit が未登録であることを見るだけ。その他の `KNOWN_PROVENANCE_VIOLATIONS` 使用箇所は `monkeypatch` で独自 tuple に置換する。
- 以上は静的帰結であり、変異 pytest の実測ではない。

(c) 塞ぎ方:

[対象 test:1386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1386) の `observed` 構築直前を次の逐語にする。

```python
    source = provenance.KNOWN_PROVENANCE_VIOLATIONS
    assert type(source) is tuple
    assert all(type(spec) is provenance.KnownViolationSpec for spec in source)
    assert all(
        type(value) is str
        for spec in source
        for value in (
            spec.commit,
            spec.expected_finding_kind,
            spec.ruling,
            spec.note,
            spec.expected_finding_value,
        )
    )
    observed = tuple(
        (
            spec.commit,
            spec.expected_finding_kind,
            spec.ruling,
            spec.note,
            spec.expected_finding_value,
        )
        for spec in source
    )
```

これは test-only scope 内で、件数を再固定せず polymorphism だけを拒否する。production 側を `type(...) is ...` に強化する案はより直接的だが、brief の「production 1 bit も変更しない」を越えるため再裁定が必要。

### 所見 A-2 — **refuted: 通常の literal entry 追加・削除・順序変更は緑にならない**

現行 production は AST 上、Starred のない通常 `tuple`、38個すべて直接 `KnownViolationSpec(...)`。通常の entry を N 件追加すると generator は filter なしで N 件多い内側 tuple を生成し、外側の通常 tuple equality が偽になる。

同様に以下も拒否される。

- 追加と同数削除: 対応位置の5 field または順序が不一致。
- 順序入替え: SHA が一意なので最初の入替え位置で不一致。
- 非 `str` / NaN: literal oracle と不一致になり、registry validation も例外で赤。
- 同値だが別 object: 同じ5 fieldなら意味上同じ entry。object identity は承認境界ではない。

### 所見 A-3 — **refuted: 内容比較は恒真でも到達不能でもない**

AST 静的検査結果:

- `expected` は38要素の直接 tuple display。
- Starred、連結、comprehension はない。
- 参照名は12個の関数ローカル定数だけで、すべて `Constant` から構築される。
- `observed` や production tuple からの導出はない。
- target に decorator、`return`、`yield`、`pytest.skip`、`pytest.xfail` はない。
- 先行構築が例外になれば test errorであり緑にはならない。

収集面も、`pytest.ini` の `testpaths = orchestrator/tests`、`test_*.py` / `test_*` 命名、hold 非登録、autouse fixture の非干渉を確認した。旧 nodeid は親実測で実行済み。改名後 nodeid を参照する選択・skip 設定もない。

任意の `-k`、`--ignore`、`--collect-only` なら実行されないが、これは full file / acceptance 実行の外側条件である。

### 所見 A-4 — **refuted: 現行 exact built-in 前提では `observed == expected ⇒ len一致` は破れない**

現行形では、

```text
len(observed) = len(KNOWN_PROVENANCE_VIOLATIONS)
observed == expected ⇒ len(observed) = len(expected)
```

が厳密に成立する。内側要素の `__eq__` が特殊でも、通常の外側 tuple 同士は長さが異なれば等しくならない。

この含意が破れる前提は次のとおり。

- source が tuple subclass/custom iteratorになる。
- `observed` に filter、slice、dedup、`zip`、短絡 helper が入る。
- `tuple` 名が別 callable に再束縛される。
- `expected = observed`、`(*observed,)`、production由来 helperへ変わる。
- expected の要素数を production の `len` から生成する。
- 外側比較対象が通常 tuple でなく、`__eq__` を上書きした型になる。

A-1 の exact-type pin を追加すれば、今回の変更面ではこれらを閉じられる。

### 所見 A-5 — **refuted: duplicate guard 削除単独は残る tuple 比較が殺す**

重複 guard が消え、同一 SHA が2回挿入された場合、dict は最初の挿入位置を保持したまま値だけを後の spec へ上書きする。source が N 要素なら registry は N−1 要素となり、

```python
tuple(registry.values()) == provenance.KNOWN_PROVENANCE_VIOLATIONS
```

は長さ不一致で赤になる。dict の実挙動も `(a,1),(b,2),(a,3),(c,4)` → `((a,3),(b,2),(c,4))` と局所実測した。

ただし plan の「dynamic length assert は無条件に恒真」は言い過ぎである。

- 現行 guard＋exact built-in 型の正常復帰後には恒真。
- guard 削除後は単独では恒真でないが、後続 tuple 比較に包含される。
- tuple subclass を許す現行型契約では A-1 の probe のとおり `len(source)=38`、`len(registry)=39` が成立し、dynamic assert は発火する。

したがって、`:1914` の削除は **A-1 の exact-type pin とセットなら検出力ゼロ**。pin なしの単独削除は不可。

### 所見 A-6 — **refuted（A-1を塞いだ条件）: kind・ruling・note・value・順序は新たに緩まない**

exact built-in 型を固定すれば、変更直後の受理集合は実際には変わらない。`expected` はまだ38行なので production も38行・全5 field・同順序でなければならない。

将来、承認済み row を production と `expected` の双方へ追加したときだけ件数が伸びる。

- kind: literal projection＋固定 `_LEDGER_FINDING_KINDS` が拘束。
- ruling、note、value: 対応する literal field が完全一致を拘束。
- 順序: 外側 tuple equality が拘束。
- SHA 重複: `len(set) == len(expected)` と registry guard が拘束。

ただし「`expected` の編集が本当にユーザー承認済みか」は機械判定されず、review/provenance の信頼境界である。これは従来から同じで、今回新たに広がる軸ではない。

### 所見 A-7 — **refuted: 親の39件目実測だけでは post-plan 一般化を証明できない**

親実測では literal test が現行 `:1448`、registry test が現行 `:1914` で先に停止する。したがって、その走行は後続の

```python
assert observed == expected
```

および

```python
assert tuple(registry.values()) == provenance.KNOWN_PROVENANCE_VIOLATIONS
```

が39件目を検出したことを実測していない。

また、N件追加、同数入替え、重複、型 subclass、expected drift、再 import、選択実行への一般化もできない。通常 tuple の N件追加については静的証明が補っているが、A-1 はその前提外だった。

実装後の受入には少なくとも次を分離して置くべきである。

- 通常の有効39件目追加 → 改名後 literal node が `assert observed == expected` で赤。
- `_Ledger(tuple)` 追加 → `assert type(source) is tuple` で赤。
- `AliasStr(str)` による SHA 差替え → field exact-type assert で赤。
- duplicate guard 削除 → production-registry node の tuple 比較で赤。

以上はいずれも未実走であり、期待検出点の事前登録案である。