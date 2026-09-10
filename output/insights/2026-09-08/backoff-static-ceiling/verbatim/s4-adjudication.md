# 段 4 裁定 — 静的 backoff の表現可能上限

## 結論

**案 (A) を採る。** 静的値 µ の符号化を次に定める。

- `0 <= µ <= 999`: 生値 `V = µ` (現行のまま、1 bit も変えない)
- `1000 <= µ <= 9999`: 生値 `V = µ + 2000` (生値 3000..11999)

復号側は `V >= 3000` のときだけ `V - 2000` を返す。`V` が 0..2999 のときの復号は現行式のまま。

**採用理由:** 段 3 の 2 本が独立に (A) を推した。(B) は「静的域は 0..999」という右側打ち切りを恒久化する。
受領済み実測では 999 µs でも abort 率が下がり続けており (write-heavy 0.0424 / balanced 0.0586 /
read-heavy 0.0237)、依頼の動機そのものが閉じない。レンズ B は (B) が正解になる条件も探したが、
「999 超は物理的に無意味」「適応軸が同領域を覆う」「trigger gating が代替する」の 3 反論を
いずれも現物で refuted した (適応の上限は 1000 µs、walk model の評価域は [0,1000]、
trigger gating は呼ぶか否かの軸で量の軸ではない)。

## 上限 9999 µs を選んだ理由 (レンズ A 所見 2 への裁定 = real, 採用)

plan の `µ >= 1000` は無上限だった。レンズ A は 2 つの破れを現物で示した。

1. `µ = 2^53+1` で C++ は double へ丸め、Python の `Fraction` は丸めない。両者が同じ関数でなくなる。
2. 実待機は `clocks_per_us * now_backoff` を `uint64_t` にする。`clocks_per_us=2100` で
   `µ = 8784163844623597` 付近から桁あふれする。

したがって**有限域を明示する**。9999 を選ぶ根拠は次の 3 点である。

- 現行 wire は 1000 の桁で意味を切る十進構造を持つ。9999 はその構造を壊さない最大の 1 桁上の域である。
- 現行上限 999 に対し 10 倍の余裕があり、適応 backoff の上限 1000 µs を十分に越えて飽和を特徴づけられる。
- `9999 × 2100 ≒ 2.1e7` で桁あふれから遠く、9999 は double で厳密に表現できる。

**域の強制は Python の符号化器と `exact_model` の定義域で行う。** 生値 11999 超は
`exact_model` が拒否する (現行が負値を拒否しているのと同じ形)。C++ 側の式は
`V - 2000` の 1 項だけにする — hole line は単一物理行の書式契約下にあるため、式を短く保つ。
これは新しい gate ではなく、関数の定義域の宣言である。

## 所見の裁定表

| 出所 | 所見 | 判定 | 処遇 |
|---|---|---|---|
| A-1 | stock の `cache_key` は変わる (`applied_tree_sha256` → admission receipt → cache key) | **real** | 採用。「preprocess digest と `src_token` と `variant_id` は不変、cache key は変化して安全側に miss する」と正直に書く。cache admission の preimage 変更は**行わない** |
| A-2 | 無上限符号化は C++/Python 不一致と桁あふれを起こす | **real** | 採用。上限 9999 を明示 (上記) |
| A-3 | 0..2999 の意味が破れるのではないか | **refuted** | 対応不要。最終項だけを変える限り 3 領域は新式へ到達しない |
| A-4 | 凍結束縛の列挙漏れ: `applied_tree_sha256` / `analysis_code_sha256` / `binding_sha256` / `src/coder-spec.md` / `backoff_requested_us` の歴史 pin / 旧系列 digest 群 | **real** | 採用。全て変更面へ入れる。旧系列 digest 群は**不変のまま残す** |
| A-5 | 「受理集合を緩めていない」とは書けない (定数として表現できる物理値の集合が広がる) | **real** | 採用。「正しさゲートは 1 bit も緩めない。ただし静的値の入力言語は 0..999 から 0..9999 へ**拡張**する」と書き分ける |
| A-6 | runtime 意味 witness は production の admission に接続されていない (非負値は `unestablished` のまま通る) | **real** | 採用するのは**明記だけ**。全 driver への宣言一般化は依頼が scope 外と明示した「一般化」に当たるので**実装しない**。裁定パッケージへ回す |
| A-7 | 正例・負例が Python model との相互比較だけだと共通誤実装を通す | **real** | 採用。生値 3000 / 3001 / 3999 を、Python model 経由でなく独立の期待値 1000 / 1001 / 1999 で固定する |
| B-E1 | 符号化を開けても格子へ足すのは 1000 の 1 点だけ | **real** | 採用。ただし 1000 超の格子点・停止基準・追加予算は**別裁定**。本 wave は表現可能域を開けるところまで |
| B-E2 | 1001 以上を測らないので飽和域には到達しない | **real** | 同上。成果物に「右側打ち切りは 999 から 1000 へ動くだけ」と正直に書く |
| B-E3 | `backoff_overthrottle.py` が生値をそのまま `fixed-<生値>us` と `backoff_us` に書く | **real, must-fix** | 採用。放置すると物理 1000 µs の点が成果物へ `fixed-3000us` と記録される (DW-G05: 材料レポートの値が直接誤る) |
| B-E4 | `backoff_requested_us.py` が可変の `genomes()` を import しつつ凍結 D1106 の生値格子を固定している | **real, must-fix** | 採用。歴史系列の解釈を固定し、新 `genomes()` で読み替えさせない。既存テストが赤になる経路でもある |
| B-E5 | prereg parser が `_SPEC_SCHEMA` を v4 で hard-code | **real, must-fix** | 採用。下記「事前登録」節のとおり |
| B-E6 | 投入 script は取り残されていない | **refuted** | 対応不要。点数 8 のままなら透過。点を増やすときは別裁定と同時 |
| B-E7 | `src/coder-spec.md` の「千の位で待機の形を選ぶ」が q>=3 で偽になる | **real, must-fix** | 採用 |

## 事前登録 (B-10) の扱い — 親が現物で確かめた新事実

`b10_backoff_shape_sweep.py:1533-1537` は **working tree の patch bytes が事前登録 commit の blob と
一致すること**を要求する。さらに `spec.formula_sha256 != FORMULA_SHA256` で赤になる。
したがって符号化を変えると、**新しい登録 commit を持たない限り B-10 の formal run は preflight で
必ず止まる。** 事前登録の版立ては (A) と不可分であり、後回しにできない。

**裁定:** 本 wave の変更単位に B-10 事前登録の次版を含める。ただし次を厳守する。

- 変えるのは `artifacts.patch_sha256` と `artifacts.formula_sha256` と schema 版だけである。
- **R1〜R5、μ 格子、workload、block 数と実行順、threads、extime、反復数、cell の切り方、
  判定手続き (α、Holm、permutation、信頼区間、等価域、欠測、曝露) は 1 文字も変えない。**
- 完了済みの 135 cell (write-heavy `e3de15eb` / balanced `143a3f74` / read-heavy `acf840c8`) は
  **旧版の下に残す。** 新版へ resume・追記・再ラベルしない。旧版の登録 commit・blob・spec SHA・
  patch/formula hash はすべて現状のまま維持する。
- 物理残差 probe の値も旧版に束縛されたまま残す。新版へ機械的に流用しない。

**併走 wave への影響 (実測):** `dev-wave-t1905-b10-readheavy-admit` が稼働中で B-10 read-heavy の
受入を扱っている。現時点で対象 file の差分は 0 件だが、本 wave の land 後は同 wave が
旧登録 commit で formal run を起動すると preflight が `patch-sha` で止まる。
**段 5 投入直前・受入直前・land 直前に再走査し、衝突していれば止めて報告する。**

## 実装しないもの (裁定パッケージとしてユーザーへ返す)

1. **1000 µs 超の測定格子。** どの点を、いくつ、どの停止基準で測るか。追加点数と walltime 予算。
   科学的設計と計算資源を変えるので本 wave で数値を決めない。
2. **全 backoff driver への非負値 meaning 宣言の一般化。** 依頼が scope 外と明示した一般化に当たる。
3. **cache admission の preimage 変更**による旧 cache key の温存。
4. **実測後の T-2216 walk model の更新。** 現行テストが「realized 1000 を拒否」を明示しており、
   反転は実測が出た後の別変更単位。
5. **全 Genome / 全 define に共通する整数上限 gate の一般化。**
6. **完了済み B-10 135 cell の再測定・再ラベル。**
7. **F718・旧図・旧 provenance・paper-story の遡及書き換え。** 旧意味のまま維持する。

## 不変条件 (実装子への拘束)

1. `BACKOFF_FIXED=-1` の stock 枝、マーカー、骨格 (`#if` / `#else` / `#endif`)、待機ループは 1 bit も変えない。
2. 生値 0..2999 の復号は数値的に不変。C++ と Python の両方で固定する。
3. 正しさゲート (verifier、certified 判定、B-10 の R1〜R5) を緩めない。異常を検出した variant の
   即 reject は不変。
4. C++ の hole line と Python の `exact_model` は、宣言した定義域の全体で同じ関数を表す。
5. 旧成果物・旧登録・旧 digest は書き換えない。

## 変異事前登録 (DW-M01)

実装前に登録する。各変異は赤理由が 1 つに絞れることを実装後に確認する。

| # | 変異位置 | 期待して落ちる node |
|---|---|---|
| M1 | C++ hole の最終項 `V - 2000` を旧 `V % 1000` へ戻す | 生値 3000 の独立期待値 1000 を固定するテスト |
| M2 | 同 `- 2000` を `- 1999` にする | 同上 (観測 1001 で過大方向) |
| M3 | Python `exact_model` の `code >= 3` 枝だけを旧 `Fraction(mean_us)` に戻す | C++/Python 同値テストと独立期待値テスト |
| M4 | Python 符号化器の `+ 2000` を `+ 1000` にする | 生値 pin と物理 label の統合テスト |
| M5 | 定義域上限 9999 の判定を撤去する | 上限超過の拒否を固定するテスト |
| M6 | 定義域上限を 10000 に緩める | 同上 (境界の片側) |
| M7 | `backoff_overthrottle` の label を生値のままにする | 生成器から報告までを 1 本で結ぶ統合テスト (新設) |
| M8 | `backoff_requested_us` の歴史格子固定を外し現 `genomes()` を読む | 既存の D1106 凍結テスト |
| M9 | T-2266 の report schema literal を別値へ変える | schema literal を独立に固定するテスト (新設) |
| M10 | `EXPECTED_HOLE_LINE` を patch の現物と食い違わせる | patch と pin の同一性テスト |
| M11 | 事前登録の `patch_sha256` を旧値のまま残す | 登録と現物の突合テスト |
| M12 | 生値 1000 (旧 F718 汚染点) を静的 1000 と宣言する | 既存 F718 負例テスト (観測 0) |

**レンズ B が「変異しても全緑」と予測した箇所は、M7・M9 で新しい node を足して塞ぐ。**
`SPACE_VERSION` / `TRIAL` の据え置きは M11 の登録突合で捕まえる。

## 分割方針

実装面があるので段 5 は Codex `role=author` 必須 (D95)。単位は 2 つに分ける。

- **単位 A (符号化の中核):** patch の hole line、`EXPECTED_HOLE_LINE`、`FORMULA_SHA256`、
  `exact_model`、Python 符号化器と定義域、および対応するテスト。
- **単位 B (下流の追随):** `backoff_extended_sweep.py` の生値/物理値分離、
  `backoff_extended_sweep_report.py`、`backoff_overthrottle.py`、`backoff_requested_us.py` の
  歴史固定、prereg parser の schema、および対応するテスト。

docs (`patches/README.md`、`src/coder-spec.md`、事前登録の次版、spool fragment) は親が書く。
