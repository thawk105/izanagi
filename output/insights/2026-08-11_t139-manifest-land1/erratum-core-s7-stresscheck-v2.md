# [T-139] 凍結事前登録 core の較正義務に対する第 2 erratum (v2。2 operation)

```text
authority: none
default_effect: no-state-change
study_label: rf_partial_recovery / paired_cluster / main_study / core_erratum
document_kind: preregistration_core_erratum
erratum_id: t139-core-s7-stresscheck-v1
supersedes_draft: output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md
supersedes_draft_sha256: 9eb96f88e93f0d027e7f86281ebd7ee00e0cb4d243e0c27edd2afa1e78b4885c
```

## 0. 本書は何であって何でないか

本書は、凍結事前登録 core の**特定の 1 blob** に対する **one-off の exact replacement** である。
承認済み第 1 erratum (`t139-core-s15-exactkey-v1`) の兄弟であり、置換の対象節が異なる。

- **core の bytes を一切変更しない。** core を編集すると §15 要件 3 が破れ凍結が壊れる。
- **一般の errata registry ではない。** 本書は §1 の三つ組に束縛される。
- **追補ではない。** 追補 A の `fields` の一部ではなく `a14` 相当でもない。
- **`erratum_id` は草案 (v1) と同一である。** 草案は台帳へ承認されておらず、
  承認 manifest の `approved_errata` に入ったことがない。したがって同じ `erratum_id` のもとで
  operation 集合が 1 件から 2 件へ変わることは、承認済み文書の書き換えではない。
  **本書の digest が承認対象であり、草案の digest (`9eb96f88…885c`) は承認対象ではない。**
- registry へ validator が登録されていることは承認ではない。承認集合を定めるのは
  canonical 台帳とその approval manifest だけである。

### 0.1 草案 (v1) から変えた点

**operation を 1 件から 2 件へ増やし、置換内容を digest で pin した。**
段 6 の敵対レビューが、検査 1〜7 だけでは同じ `erratum_id` のまま科学的に逆向きの `new_text`
(例: `結果を見て q を選び直す。`) を持つ文書が通ることを構成例で示したため、
`new_sha256` と `expected_composed_sha256` を §3 の受理述語へ入れた。

**operation を増やした理由。** 草案は core 221 行 (§7 の帰無仮説段落) だけを置換していたが、
**同じ較正義務が core 333 行 (§14 の `a12` 行) にも残る**ことが判明した。221 行だけを置換すると、
置換後の core は「§7 では事前固定 stress model のもとでの確認」「§14 では型 I 誤りの較正」を
同時に要求する**二重状態**になる。

実測 (親が凍結 core の blob から独立に算出):

```text
core 全体で文字列 `較正` を含む行は 221 と 333 の 2 件のみ
221 行 LF 込み SHA-256 = 225268a9fe702eae37ac3f4c150fcbc24e71835ce40bd3735ce0116784278e89
333 行 LF 込み SHA-256 = a7852ad9a4812f8adc8ebf33354a5934bd6620205a23defa48732a1737a89952
2 operation 適用後、core に `較正` を含む行は 0 件になる
```

## 1. 対象 (この三つ組以外には適用しない)

```yaml
target_core:
  path:   output/insights/2026-08-07_t139-mainrun-design/preregistration.md
  commit: 88d68f9127b31df5aafc3d59607896626a1652e8
  sha256: ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
```

`commit` は限定例外の決定 (D234) を canonical 台帳へ fold した commit `F` である。
resolver は `(path, commit, sha256)` の**三つ組が exact 一致**した場合にだけ本書を適用する。

## 2. 事実 — core は保証していない性質を「較正する」と 2 箇所で書いている

core §7 の末尾は次を課す (`F` 時点の 219〜221 行目)。

```text
**帰無仮説は weak mean null を primary とし** (estimand が平均 contrast のため)、
sharp null は副次感度分析とする。weak null の型 I 誤りは、同じ許容 schedule 集合を使う
事前 simulation で較正する。
```

core §14 の追補 A field 表は、同じ義務を `a12` の仕様名として繰り返す (`F` 時点の 333 行目)。

```text
| a12 | weak null の型 I 誤りを較正する事前 simulation の仕様 |
```

この「較正する」は、**cluster level の型 I 誤りを較正したという主張として読める。**
ところが利用可能な raw は J=1 screen の 1 割当て分 (2 workload × 3 arm × 5 反復 = 30 行) だけで、
**割当て間 (cluster 間) の変動は 1 点も観測されていない** (core §17)。

追補 A パッケージ段 3 のレンズ A が示した反例 — 未観測の cluster 効果
`P(U = a) = 0.99`, `P(U = −99a) = 0.01` を加えると `E[U] = 0` で weak mean null を満たすが、
`J ≤ 13` の全 cluster が正側になる確率は `0.99¹³ ≈ 0.878` あり、片側下限は高確率で正になる。
**この cluster 効果は J=1 データから識別できない。**

したがって現行の逐語は、絶対規律 3 が禁じる「保証していない性質を保証したと書く」に該当する。
追補 A の `a12` は既に「事前固定した stress model のもとで名目を超えないことの確認」という
限定を明記しているが、**追補は core の意味を変えられない** (D234)。
core 側の逐語を置換しない限り義務は未達のまま残る。

これは追補 A パッケージの裁定 R2 で **(a) が承認された方向**である
(§47、2026-08-08「推奨通りで」) — ただし承認されたのは方向であり、本書という文書ではない。

## 3. supersede する箇所 — 構造化された exact 2 operation

**本節は散文ではなく、要素数がちょうど 2 の置換 operation 配列である。**
resolver はこの配列だけを読み、本書の他の節を受理述語の入力にしてはならない。
配列の長さが 2 でない erratum、またはいずれかの `old_sha256` が対象 core の当該行と一致しない
erratum は**解決失敗**とする。

`old_sha256` は、対象 core の当該行の **bytes (行末 LF を含む) の SHA-256** である。

```yaml
operations:
  - index: 1
    locator:
      section: "7"
      anchor: "帰無仮説の段落の最終行"
      line_number_at_target_commit: 221
    old_sha256: 225268a9fe702eae37ac3f4c150fcbc24e71835ce40bd3735ce0116784278e89
    new_sha256: 92fd71754c81b45b6cc01fb14600bfdc140af8e464c50484b45e1bb8caaa01a4
    old_text: |
      事前 simulation で較正する。
    new_text: |
      事前固定した stress model のもとで名目水準を超えないことを事前 simulation で確認する。
  - index: 2
    locator:
      section: "14"
      anchor: "追補 A field 表の a12 行"
      line_number_at_target_commit: 333
    old_sha256: a7852ad9a4812f8adc8ebf33354a5934bd6620205a23defa48732a1737a89952
    new_sha256: b8741cc99c5c45acee8e9c78a9e72a34f9ab9c2a0e27bdfd5ee71e9ec54b37fe
    old_text: |
      | a12 | weak null の型 I 誤りを較正する事前 simulation の仕様 |
    new_text: |
      | a12 | 事前固定した stress model のもとで名目水準を超えないことを確認する事前 simulation の仕様 |
expected_composed_sha256: e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c
```

**検査可能性。** 「この 2 箇所だけ」「この置換内容だけ」は自己記述ではなく次で機械的に判定できる。
**検査 8〜12 は、同じ `erratum_id` を名乗りながら別の `new_text` を持つ文書を拒否するために要る**
(検査 1〜7 だけでは、`較正` を含まない任意の 1 行へ置換する文書が通ってしまう)。

1. `operations` の要素数が `== 2` であり、`index` の集合が exact `{1, 2}` であること。
2. 各 `old_sha256` が、対象 core の当該行の bytes の SHA-256 と一致すること。
3. 対象 core 全体で、文字列 `較正` の出現が**ちょうど 2 件**であり、その 2 行が
   `operations` の 2 行と**一致**すること。
4. 各 `new_text` が対応する `old_text` と同じ 1 行であること (行数不変)。
5. 置換後の core 全体で、文字列 `較正` の出現が**0 件**であること。
6. 第 1 erratum の locator (404 / 424 行) と本書の locator (221 / 333 行) が**互いに重ならない**こと。
7. index 2 の置換後の行が、`| a12 |` で始まる表の行の形を保つこと (列数不変)。
8. **各 `new_text` の bytes (行末 LF を含む) の SHA-256 が、当該 operation の `new_sha256` と
   一致すること。** すなわち置換内容が本書の宣言値に pin される。
9. **各 `old_text` の bytes が、対象 core の当該行の bytes と exact 一致すること**
   (`old_sha256` との二重検査)。
10. **本書の 2 operation と第 1 erratum の 2 operation をすべて適用した core 全 bytes の SHA-256 が
    `expected_composed_sha256` と一致すること。**
11. `operations` の各要素の key 集合が exact
    `{index, locator, old_sha256, new_sha256, old_text, new_text}` であり、
    `locator` の key 集合が exact `{section, anchor, line_number_at_target_commit}` であること。
12. 本節の YAML block を parse する際、**duplicate key を拒否する**こと。

**上記 2 operation 以外の core の bytes・文言・受理条件・閉集合・投入順序・commit/blob 束縛を、
変更または supersede しない。**本書の他の節 (§0 §1 §2 §4 §5 §6 §7) は説明であって受理述語ではなく、
**「解釈」「補足」の名目で第 2 の受理条件を追加する経路を持たない。**
特に次は本書の射程外である。

- §15 の exact-key (第 1 erratum の管轄。本書の locator と重ならない)。
- §7 の pairing・順序均衡・trace 分離・validator 権威の各条 (219〜221 行の外)。
- §14 の閉集合 `a01`〜`a13` の**構成** (本書は `a12` の**仕様名**の逐語だけを置換し、
  閉集合の要素を増減しない)。
- `a11` の `q(J, α_k)` と `a13` の有意水準 (追補 A の管轄)。
- §4 の Fieller 同値、§9 の失敗分類、§6 の標本数規則。

### 3.1 承認済み追補 A の見出し行は据え置く

承認済み追補 A の `a12` 見出し行 (`### a12 — weak null の型 I 誤りを較正する事前 simulation の仕様`)
にも `較正` の語が残る。**本書はこれを対象にしない。**理由は次の 2 つである。

1. 同見出しの直後の本文が「本 field はその較正を与えない」と明記しており、
   追補側の規範内容は既に限定されている。
2. 承認済み blob を再発行すると、追補 A の digest を pin する承認 payload と実装 pin が連鎖的に
   変わる。**受理集合を動かさない語の整合のために承認済み三つ組を組み替えるのは、
   得るものより壊すものが大きい。**

したがって当該見出しは **legacy label** であり較正の主張ではない、という扱いを
承認 payload と材料 report に逐語で記録する。

## 4. 受理集合はどちらへ動くか — **変わらない**

第 1 erratum (`∅ → R13` の拡大) と違い、本書は**投入 gate の受理述語を動かさない。**

- §15 の要件 1〜7 は本書の置換後も逐語が同一である (locator 221 / 333 行はいずれも §15 に属さない)。
- §14 の閉集合の要素 (`a01`〜`a13`) は変わらない。置換するのは `a12` の仕様名の逐語だけである。
- 追補 A の exact-key 期待集合も、`q` の導出も、`α₁` も変わらない。
- 変わるのは**解析時に何を主張してよいか**である。置換前は「cluster level の型 I 誤りを
  較正した」と読めたが、置換後に主張できるのは「事前固定した stress model のもとで
  名目水準を超えないことを確認した」だけになる。

したがって本書は**受理集合に対して中立であり、主張の強さを弱める方向にだけ効く。**
**この事実を「だから安全なので承認不要」の根拠に使ってはならない** — core の逐語を変える
行為であり、明示の裁定を要する。

## 5. 発効点と機械配線の契約

**発効点。** 本書は、本書を承認する決定を canonical 台帳へ fold した commit 以後にのみ効力を持つ。
その commit を `F_s` と呼ぶ。`F_s` より前の checkout から得た cluster に本書を適用しない。

**承認集合への membership。** 本書が承認 manifest の `approved_errata` に入るのは `F_s` の後だけである。
それまでは `draft_errata` に置く。

**固有検査だけでは pin にならない (段 6 の焦点再レビューが示した限界)。** §3 の検査 8〜12 は
「宣言した `new_sha256` / `expected_composed_sha256` と本書の `new_text` が整合するか」を見る
**自己整合検査**である。したがって攻撃者が `new_text` と `new_sha256` と
`expected_composed_sha256` を**まとめて**差し替えた文書は、同じ `erratum_id` のまま検査 8〜12 を通る。
**唯一の anchor は、承認 manifest が本書の blob digest を pin し、resolver がそれを台帳の
承認 payload と exact 一致させることである。**gate を実装する wave は、この 2 段の照合
(台帳 → manifest → blob digest) を erratum 適用の前提条件に含めなければならない。
**`erratum_id` 別 validator registry (D263) への登録は、承認とは独立である** —
registry は「この ID の文書をどう検査するか」を定めるだけで、「適用してよいか」は定めない。
D263 の理由節が本書 (相当の第 2 erratum) を「既に承認済み」と記す箇所は事実誤りであり、
本書を承認する決定が前向きに supersede する。

**合成後 digest。** 第 1 erratum (locator 404 / 424) と本書 (locator 221 / 333) の locator は
重ならないので、合成は順序に依らず定義される。親が凍結 core の blob から独立に算出した値は次のとおり。

```text
第 1 erratum のみ適用          d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82
第 1 + 本書 (計 4 operation)   e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c
適用順を入れ替えても同じ       e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c
```

**pilot の停止。** 本書が未承認である間、pilot は投入できない。
これは新たな gate の作為によってではなく、**T-139 の投入 API が 1 つも実装されておらず、
D264 が `resolve_effective_preregistration` / `PreregBinding` / `submit_pilot` / `verify_receipt`
の非 export を機械検査で固定していること**によって成立している。
将来 gate を実装する wave は、**その gate の受理条件に「core の較正義務が
承認済み erratum によって解決済みであること」を含めなければならない。**
含めない実装は、本書が未承認のまま pilot を通してしまう。

## 6. 通る正例 (1 つ)

`F` を D234 を fold した commit、`F_s` を本 erratum を承認する決定を fold した commit とする。
core が `F` の path `P` に blob `B` (`h = SHA-256(B)`) として存在し、
本 erratum が commit `C_s` の path `P_s` に blob `B_s` として存在し、
`B_s` が対象として `(P, F, h)` を記し supersede 箇所が §3 の 2 箇所だけであり、
承認 manifest の `approved_errata` が本書を含み、`F`・`F_s`・`C_s` がすべて実 checkout の
HEAD の祖先であるとき、本書は解決に成功し、第 1 erratum と合成して
`e0b0caea…8e0c` を与える。

## 7. 本書が主張しないこと

- **本書が pilot 停止 gate を実装した、とは主張しない。** 停止は §5 の既存事実による。
- **core の他の条項に誤りが無い、とは主張しない。** 本書が扱うのは 221 / 333 行の 2 箇所だけである。
- **置換後の逐語が cluster level の型 I 誤りを制御する、とは主張しない。**
  制御は `a11` の planning model のもとでの Hotelling / t / 非心 t が与えるものであり、
  simulation は事前固定 stress model のもとでの確認に留まる。
  **cluster 間変動は依然として未観測である。**
- **承認済み追補 A の見出し行を整合させた、とは主張しない** (§3.1 のとおり据え置く)。
