# [T-2113] sort SWO oracle を検証済み IR へ縮める方向の生死確認 — 4 項目すべて真

2026-09-01、dev-wave `dev-wave-t2113-sort-oracle-ir-liveness`、
着手時 main = `08a17b3b3`、記録時 main = `265aa16e3`。
**本 wave は実装面の差分を持たない。** 生死確認だけを行い、縮小そのものは実装していない。

逐語は `verbatim/`。段 1 brief、段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定、driver 本文、
実測 JSON を凍結した。

## 1. 結論

D1355 が先に確かめよと定めた 4 点は**すべて真**である。ただし主張できる範囲は §5 に限る。

| 問い | 結果 |
|---|---|
| 権威集合 15 件を小さい型付き whitelist IR へ全件表現できるか | **真** (`m1_emitter_byte_conformance=true`) |
| trusted evaluator が現行 2 corpus の関係行列を再現するか | **真** (`m2_real_type_matrix_agreement=true`、不一致 0) |
| 未知 opcode・型不一致・任意 C++ 文字列を評価前に拒否できるか | **真** (`m3_wire_ingress_rejection=true`) |
| render 値が現行の構造 gate を通るか (規律 2 の向き) | **真** (`m4_narrowing_direction=true`) |

`status=PASS`。実測 JSON は `verbatim/liveness-result.json`。

## 2. 何を測ったか — 模擬型ではなく実型で測った

段 2 プランと段 3 の両レンズは、いずれも
**「実 oracle は `IZANAGI_SORT_SWO_MASSTREE_ROOT` 未設定で実行不能。ground truth は 3 field だけの
proxy 型に限る」**を前提にした。レンズ B はこれを根拠に `PASS` 不可、レンズ A は
`q2=UNAVAILABLE` を要求した。D344 が「模擬型を置くと模擬では SWO を満たすが実型では
満たさない comparator が通る」として実型 harness を必須にしていたためである。

**この前提は親の実測で覆った。** masstree source が
`/work/1/SFC/tanab/ccbench-upstream-pr/build-baseline/_deps/masstree-src` に実在し
(別作業の成果物、読取りのみ)、`sort_swo_oracle._translation_unit()` が返す**実 TU**
(35103 bytes、実型 `WriteElement<Tuple>`) が `_compile_command` の実 flag でそのまま
compile できた (rc=0)。`_run_matrix` が**実 broker・実 seccomp・実 arena**を通して
324 byte の行列を返した。

したがって driver は proxy C++ harness を**書いていない**。ground truth は
`ground_truth="real-oracle-tu-and-broker"` であり、レンズ A が列挙した
「proxy へ置き換えると失われる保証」(実型 member lookup、実 ctor・layout・alignment・lifetime、
実 allocator 上の pointer semantics、throw/abort/call-count 異常、3 order 間の relation 不一致検出、
read-only corpus・seccomp・専用 protocol) はすべて保持されている。

driver は corpus も allocator も**書かない**。corpus は `_CORPUS_TOPOLOGY` を読むだけ、
allocation は実 TU が行う。レンズ B が指摘した「Python と C++ が同じ誤読を共有する」経路は、
片側を production 実装にすることで構造的に消えている。

## 3. 測定の規模

- IR 値域 = **79 値**。3 field に対する「相異なる field による辞書式比較」の**完全閉包**
  (`const_false` 1 + depth1 6 + depth2 24 + depth3 48)。権威集合 15 件はその真部分集合。
- compile = **80 回** (positive control 1 + IR 79)。すべて実 TU。
- 行列比較 = 79 値 x 2 corpus x 3 order x 324 セル = **153,576 セル**。不一致 **0**。
- `m2_mismatch_count=0`。

## 4. 緑が恒真でないことの証拠 — 負例対照 3 件すべて KILLED

M2 の緑は、Python evaluator を意図的に壊すと赤になることを確かめて初めて意味を持つ。
実 TU 側は一切変えず、Python 側の値取り出しだけを壊した (`verbatim/negative_control.py`)。

| 変異 | 誤りの型 | 検出 | 差分セル数 |
|---|---|---|---|
| `signed-storage` | `storage_` を符号つき 32bit と誤解する | **KILLED** | corpus ごとに非 0 |
| `reversed-pointer-rank` | arena の割当順を取り違え aliases と separate を逆にする | **KILLED** | 各 corpus 108 |
| `nul-truncated-key` | `key_` を C 文字列と誤解し最初の NUL で切る | **KILLED** | corpus0 12 / corpus1 14 |

3 件とも `clean_evaluator_agrees=true` かつ `mutated_evaluator_detected=true`。
とくに `reversed-pointer-rank` が 108 セルで検出されたことは、
**pointer 順位の導出が偶然一致したのではなく実際に検査されている**ことの証拠である。

corpus はこれらの誤りを踏ませるよう作られている。`storage` は
`0x7FFFFFFF` / `0x80000000` / `0xFFFFFFFE` / `0xFFFFFFFF` を含み符号を誤ると順序が反転する。
`key` は `\x7f` / `\x80` と埋め込み NUL (`\0`, `a\0`) を含む。

## 5. 主張してよいこと・いけないこと

**主張してよい:** 権威集合 15 件は 3 opcode の型付き IR へ全件表現でき、その render 値は
実 oracle TU の実型・実 allocator・実 broker の上で Python trusted evaluator の行列と
2 corpus x 3 order で完全一致した。JSON wire 経由の未知 opcode・型不一致・生 C++ 文字列は
評価前に拒否され、render / evaluate / compile のいずれにも到達しなかった。
79 値の完全閉包でも同じことが成立した。

**主張してはいけない:**

- 供給網検証済みの oracle 実行である — `_compile_verified` の dependency manifest 検証は
  迂回した。masstree root は `DEPENDENCY_MANIFEST_SHA256` と照合していない
  (`dependency_manifest_verified=false`)。本 driver の結果は**意味の実測**である。
- D344 を supersede した / D39 と同じ実験である — §6。
- certified 選択結果の受理経路を置換できる / `sort_best` の権威集合を 79 値へ広げてよい —
  D1357 の 15 組 exact binding とは別の権威である。79 値で置き換えると受理集合が**広がる**。
- 現行 pin が将来 evaluator を保護する — `CORPUS_SHA256` は allocation 順の変更を捕捉しない。
  `CONTRACT_VERSION` / `AXIOM_CHECKER_VERSION` は固定整数であって検出器ではない。

## 6. ユーザー裁定へ返す 4 件 (実装しない)

1. **D344 / D39 との実験同一性の衝突。** D344 は本方向 (typed IR / AST allowlist) を
   **明示的に却下**しており、理由は技術的不能ではなく「合成が事前 allowlist からの選択に化け、
   raw C++ comparator の独立合成という D39 の実証点を別実験に変える」であって、
   **親は決めずユーザー裁定へ返せ**と書いてある。D1355 はこの却下理由に触れていない。
   生死確認が真でも、D1355 が D344 のこの部分を supersede するかは**未裁定**である。
2. **受理権威の役割分離。** IR parser / `_validate_single_sort_statement` /
   `coder_effect_gate` / SWO oracle / exact binding のどれが受理権威になり、どれが恒真化するか。
   trigger 軸の AST allowlist v1 は「同じ hole に受理権威が 2 つ並ぶ」を理由に破棄された先例がある
   (`output/insights/2026-08-15_t396-hole-allowlist-refuted/`)。
3. **pointer 意味論の確定と contract 束縛。** 現行 C++ の `<` を再現するのか、明示 rank へ
   意味を変えるのか。後者は既存 comparator と非同値になる。また IR schema / parser / renderer /
   evaluator / pointer mapping / TU hash / compiler policy を 1 つの contract digest へ束縛する
   要件は現行 pin に存在しない。
4. **受理集合の包含の完全証明。** 本 wave が測ったのは render 値が
   `_validate_single_sort_statement` を通ることまでである。production 統合全体で
   現行 accepted 集合の部分集合になることは未証明。レンズ A は逆に広がる具体経路として、
   現行 effect gate が拒否する `while (true) { break; }` 入り comparator と外延同値な IR が
   accept されうる点を挙げた。

## 7. 限界と再現手順

- driver は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2113-sort-oracle-ir-liveness/`
  に置いた (`liveness_driver.py` + `liveness_main.py` + `negative_control.py`)。逐語は
  `verbatim/` に `.md` として保存した。
- **`DW-G01` の 100 行予算を超えた。** driver 本体は 270 物理行である。C++ harness を書かない分は
  縮んだが、79 値の完全閉包・JSON wire の 12 例・2 corpus x 3 order の全セル比較・
  4 状態の分離を 100 行に収めると、生成 C++ の複雑さを行数から隠すだけになる
  (段 3 レンズ B の指摘と同じ)。検査範囲を黙って減らさず、超過を明記する方を選んだ。
- masstree root は本 repo の管理外にあり、この機体固有の事実である。別環境で再現するには
  同等の masstree source を用意する必要がある。
