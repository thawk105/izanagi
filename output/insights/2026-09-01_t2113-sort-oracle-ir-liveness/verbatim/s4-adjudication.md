# [T-2113] 段 4 裁定

基準 main (着手時) = `08a17b3b3`。段 4 直前の main = `834efe61f`。裁定 inbox 再走査済み
(D1359〜D1378 を主題で照合。本 wave の主題に触れる新裁定は無い。D1359 が再確認した D1261 =
「抑制軸は防御的堅牢化にだけ適用し、規律 2 / 3 と実験計画の健全性には適用しない」を裁定の
物差しに使う)。

## 0. 裁定を変えた実測 — 両レンズの中心前提が覆った

段 1 brief・段 2 プラン・レンズ A 所見 1・レンズ B 所見 1/2 は、いずれも
**「実 oracle は masstree 未設定で実行不能。よって ground truth は proxy 型に限る」**を前提にした。
レンズ B はこれを根拠に `status=PASS` 不可、レンズ A は `q2=UNAVAILABLE` を要求した。

**この前提は実測で覆った。** 親が段 3 の待ち時間に実測した (`probe_real_tu.py`)。

- masstree source が `/work/1/SFC/tanab/ccbench-upstream-pr/build-baseline/_deps/masstree-src`
  に実在する (`config.h` / `compiler.hh` を含む。別作業の成果物、読取りのみ)。
- `sort_swo_oracle._translation_unit()` が返す**実 TU** (35103 bytes、実型
  `WriteElement<Tuple>`) が `_compile_command` の実 flag でそのまま compile できる。**rc=0。**
- `_run_matrix(exe, 0, 0)` が**実 broker・実 seccomp・実 arena** を通して
  324 byte の行列を返す。`finding=None`。
- 得られた row0 = `000111111111101111` を corpus 0 の key 列と突き合わせて手検算した。
  空文字列 3 件 (element 0,1,2) と element 13 に対して false、他 14 件に対して true。
  `_TRUSTED_CONTROL_STATEMENT` (`lhs.key_ < rhs.key_`) の意味と**完全一致**する。
  これは行列の添字が element id で正規化されている (`sort_swo_oracle.py:938-941`) ことの
  実測確認でもある。
- compile + run 1 巡は約 1.5 秒。79 値でも約 2 分で収まる。

したがって **proxy C++ harness は不要**であり、段 2 プランの `typed-field-proxy` 設計は採らない。
レンズ A が列挙した「proxy へ置き換えると失われる保証」(実型 member lookup、実 ctor・layout・
alignment・lifetime、実 allocator 上の pointer semantics、throw/abort/call-count 異常、
3 order 間の relation 不一致検出、read-only corpus・seccomp・専用 protocol) は、
**実 TU をそのまま使うのですべて保持される。**

**保持しない限界 (必ず明記する):** `_compile_verified` の dependency manifest 検証は迂回する。
masstree root は `DEPENDENCY_MANIFEST_SHA256` と照合していない。よって本 driver の結果は
**意味の実測**であって供給網検証済みの oracle 実行ではない。`DEPENDENCY_MANIFEST_SHA256` との
一致は主張しない。

## 1. 所見の裁定

| # | 所見 | 裁定 | 処理 |
|---|---|---|---|
| A1 | proxy は実型保証の代替にならない | **real** | 採用。proxy を廃し実 TU にする (§0)。前提が覆ったので結論 (`PASS` 不可) は不成立 |
| A2 | IR 後の受理権威が未定義で T396 と同型の二重化が起こる | **real・scope 外** | 実装しない。裁定パッケージへ (§4) |
| A3 | 「受理集合が狭まる」は集合間写像が未定義で未証明 | **real・一部 scope 内** | 測れる部分を採用: 全 render 値を現行 `_validate_single_sort_statement` と `coder_effect_gate` に通す (M4)。production 統合の全証明は scope 外 |
| A4 | 現行 pin は将来 evaluator の pointer 規則を保護しない | **real・scope 外** | 実装しない。裁定パッケージへ。driver は hash を情報欄として出すに留める |
| A5 | D1355 は D344 の実験変更 (D39) を明示裁定していない | **real・scope 外** | 実装しない。**ユーザー裁定へ返す** (§4)。結論の主張範囲を縛る (§3) |
| B1/B2 | ground truth が proxy で、Python と C++ が同じ誤読を共有しうる | **real** | 採用。実 TU により解消 (§0)。driver は corpus 解釈も allocator も**書かない** |
| B3 | `UNAVAILABLE` が設計上の偽を隠す | **real** | 採用。positive control を先に置き、`PASS`/`FAIL`/`UNAVAILABLE`/`DRIVER_ERROR` を分離 |
| B4 | Q3 の 6 probe は主要な whitelist 条件を測っていない。実 interface は raw C++ 文字列 | **real** | 採用。JSON wire から入れ、負例を拡張し、render/eval/compile を poison sink にする |
| B5 | 31 値は最小でも十分でもない。3 field なら lex3 まで含めて 79 値 | **real** | 採用 (修正あり)。**79 値**を採る。ただし「最小」ではなく **3 field に対する完全閉包**と呼ぶ (§2) |
| B6 | Q1 は表現性でなく emitter replica の正確さを測る | **real** | 採用。`emitter_byte_conformance` へ改名し補助検査へ降格。表現性の主証拠は M2 |
| B7 | proxy と実型の差は pointer にだけ残る | **refuted (前提消滅)** | 実 TU を使うので proxy 差自体が存在しない |
| B8 | 100 行予算は監査可能性を壊す | **refuted (前提消滅)** | C++ harness を書かないので予算が空く。実測して超えたら報告する |

同一 field の 2 段比較を落とす正規化は**正しい**。`a.f != b.f ? cmp1(f) : cmp2(f)` は、
非同値なら `cmp1(f)`、同値なら第二比較も false なので、単一比較 `cmp1(f)` と外延的に同値である。

## 2. IR 値域の確定 — 79 値

比較可能な field は `storage_` / `key_` / `rcdptr_` の 3 つだけである
(`external/ccbench/include/op_element.hh:19-21`)。よって「相異なる field による辞書式比較」の
閉包は深さ 3 で**尽きる**。深さの上限は恣意的な選択ではなく field 数から決まる。

```
const_false                                    1
depth1: 3 field x 2 方向                        6
depth2: 3x2 順序対 x 4 方向                     24
depth3: 3! 順序 x 8 方向                        48
                                       合計    79
```

権威集合 15 件はこの真部分集合である (1 + 6 + 8)。**「最小」とは主張しない** — レンズ A が
正しく指摘したとおり最小性は未証明である。主張するのは「3 field に対して完全」であり、
これは検証可能な性質である。

## 3. 実装するもの (driver の測定項目)

repo 外の使い捨て driver 1 本。repo への実装面差分はゼロ。

- **PC (positive control):** `_TRUSTED_CONTROL_STATEMENT` を実 TU で compile・run し
  `finding=None` を確認する。ここが赤なら以降を測らず `UNAVAILABLE`。
- **M1 `emitter_byte_conformance`:** 15 件の IR を render し `s6_sort_sweep.CANDIDATES` の
  `implementation` と UTF-8 byte 比較。補助検査。
- **M2 `real_type_matrix_agreement`:** 79 値すべてについて、render → **実 TU** → compile →
  `_run_matrix` を 2 corpus x 3 order。実行列が 3 order 間で一致し、かつ Python evaluator の
  行列と全 324 セル一致するか。**これが表現性と再現性の主証拠。**
- **M3 `wire_ingress_rejection`:** JSON bytes から decode して admission に通す。
  正例 (JSON array / 15 件の 1 つ) と負例 (未知 opcode、bad field、bad direction、arity 過不足、
  余分 payload、重複 field、lex3 の field 重複、生 C++ 文字列) を同じ入口へ通す。
  render / evaluator / compile を poison sink にし、負例が 1 つでも到達したら失敗。
- **M4 `narrowing_direction`:** 79 件の render 値すべてを現行
  `_validate_single_sort_statement` に通し、全件が現行の構造 gate を**通る**ことを確認する
  (通らなければ「狭まる」ではなく「ずれる」)。`coder_effect_gate` が import できれば同様に通す。

`status = PASS` は `PC ∧ M1 ∧ M2(79 件全件) ∧ M3 ∧ M4` のときだけ。
compile 不能・依存解決不能だけが `UNAVAILABLE`。driver 自身の protocol/codegen 不良は
`DRIVER_ERROR`。positive control 成功後の個別 IR の compile 失敗は `FAIL`。

## 4. 実装しないもの — ユーザー裁定へ返す

以下は real だが本 wave の scope 外である (ユーザー指示「仮想リスク向けの gate・検査・台帳・
一般化の追加は scope 外」、および D1261 の抑制軸)。**設計択一としてユーザーへ返す。**

1. **D344 / D39 との実験同一性の衝突 (A5)。** D344 は本方向を却下し、理由は技術的不能ではなく
   「raw C++ comparator の独立合成という D39 の実証点を別実験に変える」であり、
   **親は決めずユーザー裁定へ返せ**と書いてある。D1355 はこの却下理由に触れずに方向を採った。
   生死確認が真でも、D1355 が D344 のこの部分を supersede するかは**未裁定**である。
2. **受理権威の役割分離 (A2)。** IR parser / `_validate_single_sort_statement` /
   `coder_effect_gate` / SWO oracle / exact binding のどれが受理権威になり、どれが恒真化するか。
   T396 の破棄理由 (同じ hole に受理権威が 2 つ並ぶ) の再発面。
3. **pointer 意味論の確定と contract 束縛 (A4)。** 現行 C++ の `<` を再現するのか、明示 rank へ
   意味を変えるのか。後者は既存 comparator と非同値になる。また IR schema / parser / renderer /
   evaluator / pointer mapping / TU hash / compiler policy を 1 つの contract digest へ束縛する
   要件は現行 pin に無い。
4. **certified `sort_best` への 79 値の流用禁止 (A2/B5)。** D1357 の 15 組 exact binding を
   79 値 admission で置き換えると受理集合が**広がる**。両者は別の権威である。

## 5. 真と出たときに主張してよいこと・いけないこと

**主張してよい:** 権威集合 15 件は 3 opcode の型付き IR へ全件表現でき、その render 値は
実 oracle TU の実型・実 allocator・実 broker の上で、Python trusted evaluator の行列と
2 corpus x 3 order で完全一致した。JSON wire 経由の未知 opcode・型不一致・生 C++ 文字列は
評価前に拒否された。79 値の完全閉包でも同じことが成立した。

**主張してはいけない:** 供給網検証済みの oracle 実行である / D344 を supersede した /
D39 と同じ実験である / certified 選択結果の受理経路を置換できる /
`sort_best` の権威集合を 79 値へ広げてよい / 現行 pin が将来 evaluator を保護する。

## 6. 変異事前登録

実装面 (D95 決定 2) の repo 差分がゼロなので、`DW-S04` により変異 matrix を免除する。
**受入全走は免除しない。** 段 7 の記録 commit 完了後に投入する。
