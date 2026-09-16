## 所見一覧 (real / refuted / 不明、各 1 行の成果物影響つき)

- **real A1：「実在の境界 byte 入り path は必ず報告される」は成立しない。** 境界 byte より上にある祖先 directory の参照でも条件 5 は成立する。成果物影響：README・決定台帳が、現行実装では抑止されうる候補を「必ず finding が残る」と誤記する。
- **real A2：「単根の probe と本番の入力形は同じ」は限定が必要。** 本番の全 match 由来の根集合では、長い根が内部の境界 byte を跨ぎ、単根 probe では拾えない pattern を拾う場合がある。成果物影響：単根の真偽表から本番全体の matched 集合・抑止集合を過小評価する記録が残る。
- **refuted A3：未収録の型で P>H が生じる。** 本番が追加する token は必ず helper の左右境界条件を満たすため、反例は作れない。成果物影響：本番 ⊆ helper という向きは維持できる。
- **refuted A4：`unmatched_patterns` の逐次縮小で最終 matched 集合が変わる。** 根集合を固定すれば、pattern の削除は他の token の探索に影響しない。成果物影響：逐次縮小について追加の抑止差はない。
- **refuted A5：P11 の根外 pattern が通常の本番経路から生成される。** 根の resolve 後、その根からの `os.walk` で得た path と同じ根を `_ExternalMatch` に保持する。成果物影響：P11 の差 4 行を本番到達可能な差として数える必要はない。
- **refuted A6：6 file の対照では実在 path での差の存在を示せない。** 存在命題には足りる。成果物影響：18 行の差の記録は有効だが、467 file 全体の発火件数や実監査の抑止差には外挿できない。
- **不明／nit：今日、当該 file が到達不能 blob の一致候補になっているか。** 本 probe は測っていない。成果物影響：現在の findings・抑止件数への影響は未確定。
- **nit：README の P0「全 74 行」は 72 行。** 成果物影響：表の説明値だけが不正確で、862／718／144／0 の集計と実際の抑止集合は変わらない。

A1 は、本番の `_reference_patterns()` が file 自身だけでなく、探索根より真に下位の祖先すべてを生成し、参照された pattern の owner を候補 file に戻すことから成立する。実在対照の最初の file にも、空白入り `g2 clean scan Ω` より上の `test_generation_two_rejected_b0` や `dev-wave-suite-floor-recheck` が pattern として含まれていた。これらの境界付き参照があれば、file 自身の参照が False でも条件 5 は True になる。別の一致候補・hardlink alias の参照でも抑止されうるため、「必ず」はさらに強すぎる。

A5 では `_validate_offrepo_roots()`、`_enumerate_offrepo_candidates()`、`_compare_offrepo_candidates()` を追った。根は resolve 済み、候補は `Path(directory) / filename` の `.absolute()` であり、候補だけを別の場所へ resolve していない。directory symlink は `followlinks=False`、file symlink は `lstat()` の regular-file 条件で除外される。hardlink の alias 配布も各 `_ExternalMatch(path, root)` の組を維持する。P11 のような根外 pattern は、この生成経路からは得られない。

P14 × main blob は、条件 5 の**祖先参照の陽性対照として妥当**。R0824 の file 自身は両方 False、R0825 の job directory は両方 True であり、D247 の祖先条項を直接確認している。ただし条件 1〜4 を含む実際の抑止成立を測った対照ではない。

## 候補集合に足すべき行 (bytes と期待値、無ければ「無し」と根拠)

**P>H を作る行は無し。** ただし、A1・A2 を結論に反映するため、次の対照が必要である。以下は静的に分岐を追った期待値であり、実測値ではない。H は helper、P は本番を表す。

**追加行 1：境界 byte 入り file を、境界 byte のない祖先参照で抑止可能にする。**

```python
roots = {b"/offrepo"}
patterns = {
    b"/offrepo/w/my dir/a.py",
    b"/offrepo/w/my dir",
    b"/offrepo/w",
}
content = b"'/offrepo/w'"
```

期待値：

| pattern | H | P |
|---|---|---|
| `/offrepo/w/my dir/a.py` | False | False |
| `/offrepo/w/my dir` | False | False |
| `/offrepo/w` | True | True |

根の出現は `index=1`、左 byte は引用符。境界探索は `1 + len(b"/offrepo") = 9` から始まり、閉じ引用符の位置 `11` で止まる。token は `b"/offrepo/w"` となり、`patterns` に含まれる。この祖先 pattern の owner は当該 file なので、他の必要条件も満たせば条件 5 により抑止可能である。

**追加行 2：全 match 由来の複数根で、単根 probe の False が True に変わる。**

```python
patterns = {
    b"/offrepo/my dir/a.py",
    b"/offrepo/my dir",
}
content = b"'/offrepo/my dir/a.py'"

roots_single = {b"/offrepo"}
roots_global = {b"/offrepo", b"/offrepo/my dir"}
```

file pattern の期待値は、単根で **H=True・P=False**、複数根で **H=True・P=True**。

短い根では `index=1`、境界探索開始 `8+1=9`、空白の位置 `12` で止まり、token は `b"/offrepo/my"`。長い根では探索開始が `1+15=16` となり、内部の空白を越えて閉じ引用符の位置 `21` まで進むため、file pattern 全体を取得する。

同じ file が両方の根で列挙され、bytes 比較に成功すれば、両方の根が本番の `encoded_roots` に入る。根同士の包含関係を `_validate_offrepo_roots()` は禁止していない。これは本番で生成可能な入力形である。

**追加行 3：境界 byte を挟む prefix pattern 同士。**

```python
roots = {b"/offrepo"}
patterns = {b"/offrepo/a", b"/offrepo/a b"}
content = b"'/offrepo/a b'"
```

短い pattern は **H=True・P=True**、長い pattern は **H=True・P=False**。本番は空白で切れた短い token を取得する。各 pattern を別々の一致候補が所有していれば、既存の本番でもこの差が owner ごとの抑止へ伝わる。

**P>H が作れない理由：**

本番の `matched.add(token)` に到達するには、非空の根に一致した位置 `index` で左境界が成立し、`token = content[index:end]` が pattern と完全一致する必要がある。`end` は境界 byte の位置か content 末尾なので、helper の右境界条件も必ず成立する。helper は `start = index + 1` で再探索するため、その出現を飛ばさない。空根は skip され、本番が空 token を追加する経路もない。

chunk 幅を `K`、根長を `L` とすると、chunk 内最後の開始位置 `chunk_end-1` にある根の末尾まで、`search_end = chunk_end+L-1` が届く。`index >= chunk_end` の出現は次 chunk の担当になる。右境界探索は content 末尾まで行うため、token の chunk 跨ぎでも切り詰められない。同じ根の近接出現も `index+1` から拾い直す。

複数根、接頭辞関係にある根、pattern と等しい根、pattern より長い根も、この証明を破らない。複数根は取得できる token を増やしうるが、取得した token はすべて helper が True になる。

また、固定した根集合 `R` が content `c` から作る token 集合を `T(c,R)` とすれば、本番の戻り値は `patterns ∩ T(c,R)`。各 blob 後に既検出 pattern を削除しても、最終集合は元の pattern 集合と全 blob の token 集合の和集合との積で変わらない。**逐次縮小は同値、単根から全根集合への変更は同値とは限らない**、という区別が必要である。

## 数値の検算

真偽表のデータ行を解析し、監査文書の P型×C型×向きの集計表と照合した。集計セルの不一致はなかった。JSON からも主要値を再計算した。

| 項目 | 再計算値 | 判定 |
|---|---:|---|
| データ行 | 862 | 一致 |
| H=P | 718 | 一致 |
| H>P | 144 | 一致 |
| P>H | 0 | 一致 |
| 実在対照の H>P | 18 | 一致 |
| P0 × C11 | 42 | 一致 |
| P0 全体 | **72** | README の 74 は誤り |
| Markdown 物理行数 | 874 | 監査文書と一致 |

144 行には入力領域外の P11 の 4 行が含まれる。したがって、その 4 行を除いた差は 140 行である。18 行は 6 file × 3 content 形であり、18 個の異なる file や実監査 finding ではない。

実在対照は JSON の選択 path と hits を照合し、4 directory 配下の regular file 数を再計数した。

| 対照 | regular file 数 |
|---|---:|
| `test_generation_two_rejected_b0/g2 clean scan Ω` | 107 |
| `test_deterministic_artifacts_a0/a much longer root with spaces Ω` | 80 |
| `test_production_emitter_staged0/a much longer root with spaces Ω` | 173 |
| `test_chain_g2_env_tag_unchange0/g2 clean scan Ω` | 107 |
| 合計 | **467** |

これに直接の file 2 件があり、hits の「6 entry」は **4 directory＋2 file**。境界 byte を含む full path が全部で 6 個という意味ではない。選択された 6 file の存在も確認した。ただし、探索根全体を再走査して「hits 以外が存在しない」ことまでは再検証していない。

## 総括

**P>H の反例はなく、本番 ⊆ helper は実装から支持できる。** ただし、README の「境界 byte 入りの実在 path は必ず報告される」は撤回が必要であり、単根の真偽表を本番の全根集合と同一視する説明も修正が必要である。

本番維持の方向を変える必要はない。是正対象は、祖先参照と複数根の対照追加、結論の適用範囲の明記、P0 の 74→72 の訂正である。ファイル変更・probe 実行・pytest は行っていない。