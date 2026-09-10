# 段 4 裁定 — [T-2419]

## 所見の裁定

| # | 所見 | real/refuted | 採否 | 理由 |
|---|---|---|---|---|
| A1 | 非負 witness は hole だけを compile し、実 conditional の枝選択を観測しない | **real** | **不採用 (scope 外)** | 判定器の `MEANING_PROOF_KIND` が自ら `standalone-tu-finite-pointwise-witness` と名乗り、`unestablished_meaning_macros` の docstring も「その proof_kind の境界内で established」と書いている。境界は既に開示済み。さらに 6 driver すべてが同じ family 呼び出しに `-1` を含み、`-1` の supply は `stock-inert-preprocess-identical` を要求するので、`#if BACKOFF_FIXED >= 0` の反転は supply 側で赤になる。限界は insight に明記する (規律 7「限界は主張せず明記する」) |
| A2 / B1 | 生値から codec で期待値を復元する設計は driver の要求意味を証明しない | **real** | **採用 (設計変更)** | 2 レンズが独立に収束した。`backoff_sweep.SWEEP_US` へ物理 3000 µs のつもりで `3000` を足すと、plan 案では宣言 1000.0・観測 1000.0 で green になり、F718 と同型の事故が通る |
| A3 / B5 | 負例が新しい production wiring の mismatch 経路を通らない | **real** | **採用** | 下の設計変更により、負例は production helper を通って red になる |
| A4 / B4 | 親 brief の「現行 file 一致を要求する consumer は無い」は誤り | **real** | **採用 (brief 訂正)** | `s1_known_axes_freeze.verify_document()` が全 source を live で再 hash して拒否する。実際は generator hash mismatch で手前で止まるため受入が赤にならないだけ。既存の乖離であり本 wave が作る赤ではない。凍結は再発行しない |
| B2 | generic screening は生値 1000 を unestablished のまま admit する | **real** | **不採用 (scope 外・裁定パッケージ)** | brief は screening を scope 外と明示済み。完了主張を「この helper を通る 6 driver」に狭める |
| B3 | T2418 の `meaning_witness_status` 固定文字列が、変更後の再走で偽になる | **real** | **不採用 (scope 外・裁定パッケージ)** | 直すと campaign identity と report schema の版上げが要り、T-2418 の事前登録に触れる。既存 artifact は不変。insight と次タスク候補へ書く |
| B (nit) | 循環 import への攻撃 | **refuted** | — | 設計変更で codec を移さないことになり、論点自体が消えた |
| B (nit) | 受入台帳は file でなく nodeid を key にする | **real** | **採用 (brief 訂正)** | 新 2 nodeid を推測値で足さない判断は妥当。変更後の収集で 90% を保つことが条件 |
| B (must-fix) | 「実測環境は login node のみ」は固定できない | **real** | **採用 (brief 訂正)** | 実行場所は `tools/run_tests.py` が決める。追加テストは実 C++ compiler を起動する |

## プラン v2 (確定)

段 2 案から 2 点変える。**gate 側は codec を一切呼ばない。** driver が自分の要求意味を渡す。

1. `orchestrator/campaign/backoff_sweep.py` の `_require_backoff_condition_gate` に
   必須 keyword `backoff_fixed_physical_us: Mapping[int, int]` を足す。
   生値 → その driver が意図した物理 µs の写像である。
2. 検査: 値はすべて exact `int`。key の集合は、要求された非負 `BACKOFF_FIXED` の集合と
   **完全一致**する (欠けても余っても build 前に `RuntimeError`)。値は 0 以上の exact `int`。
3. 宣言: 要求値 `v >= 0` に対し
   `MeaningWitnessDeclaration("BACKOFF_FIXED", (MeaningCase(v, (bits, bits)),))`、
   `bits = condition_meaning_gate.canonical_float64_bits(float(backoff_fixed_physical_us[v]))`。
   `v == -1` の stock branch case は現行のまま。`BACKOFF_FIXED` 以外の macro は現行のまま `None`。
4. **段 2 案の「生値 1000〜2999 と 12000 以上を wire domain 外として拒否する」は採らない。**
   判定器は宣言と観測を突き合わせるだけでよく、新しい拒否面を作る必要がない。
   生値 1000 を「1000 µs のつもり」で渡せば宣言 1000.0 対 観測 0.0 で red になる。これが F718 である。
5. **codec の移動 (段 2 案 P2) は行わない。** `encode/decode_static_backoff_us` は
   `backoff_extended_sweep.py` に残す。循環 import の論点は消える。
6. 呼び出し面 6 箇所が写像を渡す。物理値が scope にある所で作る。
   - `backoff_sweep.py:378` → `{n: n for n in SWEEP_US}` (SWEEP_US が物理格子そのもの)
   - `backoff_profile.py:344` → `{a: a for a in amounts if a is not None}`
   - `backoff_repro.py:72` → 点を組み立てた物理集合から作る (`best_us` と `{5, 10}`)
   - `backoff_extended_sweep.py:527` → run kind の物理格子
     (`EXTENDED_SWEEP_US` / `T2266_REALIZED_US` / `T2418_REALIZED_US`) から
     `{encode_static_backoff_us(a): a for a in grid}`
   - `backoff_overthrottle.py:61` → extended から継承した点しか持たないので、
     driver 自身の既存の点意味関数 (`_point_backoff_us`) を使う。**この 1 本だけ intent が
     decode 由来であることを実装子は報告に明記する**
   - `backoff_requested_us.py:116,132` → `BACKOFF_FIXED` は `-1` のみ、
     `BACKOFF_REQUESTED_US` 呼び出しは対象外なので空写像
7. テスト (`orchestrator/tests/test_backoff_sweep.py` へ追加、新 file を作らない)
   - 正例 A: 生値 5・intent 5 → meaning `green/declared-meaning-observed`、
     `unestablished_meaning_macros == ()`。既存 `:166` の `unestablished` assert を置き換える
   - 正例 B: 生値 3000・intent 1000 (extended 型の符号化点) → green
   - 負例: 生値 1000・intent 1000 (F718 そのもの) → production helper が
     `RuntimeError` で拒否し、meaning record が `red`。実 compiler を通し、
     capture・request・evaluator を stub しない
   - 負例 2: 要求集合と写像の key が食い違う → build 前に `RuntimeError`

## 不変条件 (段 1 から変更なし)

規律 2 を緩めない。受理集合は狭まる方向だけ動く。`-1` の stock branch witness は不変。
凍結成果物の bytes を変えない。判定器 (`condition_meaning_gate.py`)、patch、台帳、
screening driver、b10 shape driver は変更しない。

## 変異事前登録 (実装前)

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| M1 | `backoff_sweep.py` 宣言構築 | 非負値の宣言を `None` に戻す | 正例 A・B が赤 (KILLED) |
| M2 | 同上 | bits を `float(physical)` から `float(raw)` に変える | 正例 B (生値 3000・intent 1000) が赤 |
| M3 | 同上 | 写像の key 完全一致検査を外す | 負例 2 が赤 |
| M4 | `backoff_extended_sweep.py` 呼び出し面 | 写像を `{raw: raw}` に変える | extended 経路の正例が赤 |
| M5 | `backoff_sweep.py` 宣言構築 | 非負値の宣言を全要求で「拒否」に変える (過剰拒否の正例) | 正例 A が赤 |

各変異は実装後に単一理由性を確認する (`DW-M01`)。M1 と M5 が同じテストで死ぬ場合は
位置を分けて再照準する。M2 は `float(raw)` と `float(physical)` が一致する正例 A では死なず、
正例 B でだけ死ぬことを確認する (これが intent 独立性の実効証拠である)。
