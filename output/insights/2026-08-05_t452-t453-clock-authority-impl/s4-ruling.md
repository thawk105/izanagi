# 段 4 裁定 — [T-452] + [T-453] 実装

段 3 の所見 15 件 (A 7 / B 8) を real/refuted、採用/不採用、scope 内/外で裁定する。
refuted は 0 件 — **全 15 件が real**。うち実装するのは 11 件、scope 外として裁定へ返すのが 2 件、
`DW-G04` により設計メモに留めるのが 1 件、backlog が 1 件。

## 親 brief の erratum (段 3 A-7 / B-1 を採用)

**erratum-1**: brief 「(新事実 N1) v1 の観測 artifact は 19 件 (smoke 4 件を含む)」は誤り。
正しくは **論理 JSON 22 件 = success 19 (staging 15 + smoke 3 + silo 1) + failure 3**、
smoke は success 3 + failure 3 の計 6 件である。物理ファイルは **47** =
`.json` 22 + `.stdout` 22 + `.md` 3 (docs 言及)。

**erratum-2**: brief 「(新事実 N2) 既存の観測 artifact 16 件すべてが canonical 述語で落ちる」は
母数が過少。正しくは **success 19 件すべて**が median gate true かつ canonical false である
(親が全文走査で再実測、帯 `[2058.98, 2143.02]`)。

**erratum-3**: brief 不変条件の「既存テストの期待値を反転・緩和・skip・削除しない」は、
裁定済みの受理集合縮小 (U-2/U-3/U-5) と字面で衝突する。**訂正**: 緩和・skip・削除・xfail は禁止のまま。
**明示的に裁定済みの受理集合縮小だけは、旧意味の assertion を独立に残したうえで許す** (B-6)。

## 所見ごとの裁定

| ID | 判定 | 採否 | 裁定 |
|---|---|---|---|
| A-1 / X-B-1 | real | **不採用 (scope 外) → 裁定へ返す** | 下記 R-1 |
| A-2 | real | 採用 (must-fix) | metamorphic を self gate と silo にも広げ、`2%ではfail・3%ではpass` の差分 vector を置く。現行の 45-47% 外れ値負例は literal `5.0` 変異でも落ちるため検出力がない |
| A-3 | real | 採用 (must-fix) | 全 equality 層 (loader/issuer/consumer/self gate) の負例に `math.nextafter(2.0, ±inf)` / `2.5` / `2.9` を加える。`int()` 比較・丸め・`isclose` への退行を殺す |
| A-4 | real | 採用 (must-fix) | v1/v2 の top-level・`profile`・`effective_clock` それぞれに duplicate key を持つ構文上 valid な JSON 負例を置く。全 raw consumer が同じ duplicate-rejecting parser を通ることも固定する |
| A-5 | real | **採用 = 「修正しない」** | 下記 R-2 |
| A-6 / B-2 | real | **部分採用** | 下記 R-3 |
| A-7 / B-1 | real | 採用 (must-fix) | erratum-1/2。corpus test は探索で得た exact path 集合と手書き golden path 集合の一致を assert し、success 19 件すべてで median=true / canonical=false を固定する。`.json` と `.stdout` 22 組の JSON 意味的同一も検査する |
| B-3 | real | 採用 (must-fix) | `run_probe.py` の import/success/probe/write の **4 分岐すべて**を v2 化し、file と stdout の両方を検査する。failure は top-level exact 4 key + `error == {stage,type,message}` + `type(ok) is bool` + `type(observed_epoch) is int and not bool` + 非空文字列。`tools/pegasus/smoke_probe.sh` も caller として受入に含める |
| B-4 | real | 採用 (must-fix) | live silo は parser error を既存 `InfraFailure("parse_failure", …)` へ、raw replay は `EvidenceFailure("raw_bundle", …)` へ明示変換する。malformed / duplicate-key / typed failure の既存期待値は変えない |
| B-5 | real | 採用 (must-fix) | silo の 2 箇所は canonical predicate へ **expected=`{samples_mhz, tolerance_pct}` / observed=`{samples_mhz}` を明示構築して**渡す。full clock map を直結してはならない (全観測が false になる)。`method`/`governor` は従来どおり別の exact 比較で残す。predicate に渡った key 集合を spy で固定する |
| B-6 | real | 採用 (must-fix) | `test_execution_guard.py` の既存 18 vectors は削除・移動せず、`math_want` (private helper) と `canonical_want` (public admission) の **二重 assertion** にする。mapping/list/bool/empty の負例は public predicate 側でも必ず実行する |
| B-7 | real | 採用 (must-fix) | 下記 R-4 |
| B-8 | real | 採用 (backlog) | コード変更対象にしない。`test_campaign.py` / `test_s8b_oracle_report.py` / `test_s8b_ratified_verify.py` を **no-edit consumer regression** として受入範囲に明記する |
| A-S1 | real | scope 外 | [T-477] として起票済み。追加起票は不要 |

## R-1 — loader の self-pass 要求は本 wave で実装せず裁定へ返す

**所見は real である。** 現登録較正は自分の canonical 述語を通らないのに loader は受理し続けるため、
live 観測が偶然すべて帯内なら issuer/consumer を通り、certified receipt が出る。
「再較正まで campaign を閉じる」は現状 **運用宣言であって機械化されていない**。

**しかし本 wave では実装しない。** 根拠 —

1. 設計案 §5 の loader 行が指定するのは **policy 完全一致だけ**であり、self-pass は含まない。
2. U-8 (a) の不利材料に「途中状態では既知例外が残るため certified campaign を開けない」と
   明記されており、**既知例外が残る前提が裁定に織り込まれている**。
3. loader に self-pass を課すと `attestation_mode="required"` の唯一の registry entry が
   load 不能になり、campaign / floor / oracle / freeze / report の現行 consumer が全面 fail-closed に
   なる。これは U-1〜U-8 の射程外の受理集合変更であり、**親が独断で確定しない** (`DW-S04`)。
4. 2 レンズの判定自体が割れた (A = must-fix、B = scope 外 backlog)。

**本 wave での代替措置** — (i) registry 不変条件テストを非恒真化し (件数 assert +
入力可能 helper + schema-valid/policy-valid/self-fail 負例)、この穴が**検出可能**な状態にする。
(ii) worklog と handoff に「[T-419] U-2 の再較正まで certified campaign を開かない」を
運用条件として明記する。**新タスクとして裁定パッケージへ返す。**

## R-2 — T126 の `_attest` バグは修正しない (現挙動を保存して pin する)

親の実測 —

- `t126_driver.py:443-444` は `verified.calibration` (`CalibrationV2`) を `compare_profiles` の
  expected 引数へ渡す。`compare_profiles:612-613` は `AttestationProfile` を要求するため
  **必ず `AttestationError`** となり `QualificationDriverError` へ包まれる。成功経路は到達不能。
- `output/` 配下に `t126-qualification-attestation` を含む artifact は **0 件**。
- `test_t126_qualification_driver.py` に `_attest` / `compare_profiles` を叩く検査は **0 件**。

したがって修正は「常に空だった受理集合を非空にする」変更であり、U-1〜U-8 のどれにも含まれない。
**実装単位は現挙動 (常に fail-closed) を保存する。** 型移行で `compare_profiles` の第 2 引数が
observed 型になっても、第 1 引数に `verified.calibration` を渡し続ける限り挙動は不変である。
現挙動を pin する回帰テストを 1 本置き、**修正は新タスクとして裁定へ返す**。

## R-3 — hash projection の版束縛は「構造的な誤選択防止」だけ採用する

**採用**: projection version を呼出側の自由引数にせず、**parser の戻り値が持つ source schema から
導出**する。`observed_profile_sha256(profile, projection_schema=...)` のような自由引数 API を作らない。
これで「v1 artifact に v2 projection を当てる」誤選択が構造的に不能になる。

**不採用 (設計メモに留める)**: T126 envelope の `t126-qualification-attestation/v2` 昇格と
`observed_profile_projection_schema` の記録。`DW-G04` の発火 gate を満たさない — R-2 のとおり
成功経路は到達不能で、発火する既存 artifact path も計測 ID も brief に書けない。
`_attest` のバグが裁定されて修正されるとき、同じ単位で扱う。

## R-4 — 段 5 は単一 Codex author の 1 実装単位、内部で B → A → C の直列 phase

B/A/C は `schema_v2.py` / `env_attestation.py` / `cli.py` / `certify_calibration.sh` /
`execution_guard.py` / silo / 各テストを重複所有するため、`DW-S05-A` の素集合要件を満たさない。
**単一化の理由**: 3 phase が同一ファイルの同一領域を順に書き換える相互依存であり、
限定 patch で分離すると後段が先段を上書きする。

順序は段 2 の実測どおり **B (observed 型分離) → A (policy authority) → C (trust closure + T-453)**。
A 先行は不可 — `schema_v2` の上限を `<100.0` にした瞬間に `env_attestation.py:439` の
observed sentinel `100.0` が schema 違反になり、A 単独では緑にならない。

## 変異の事前登録 (`DW-M01`)

段 6 で `tools/mutation_harness.py` により実行する。各変異は「同じ入力を拒否する層が前後に無い」
「無効化時の赤理由が一つに絞れる」ことを実装後にコードで確認してから spec に確定する。

| ID | 変異 | 期待 | 単一理由性の根拠 |
|---|---|---|---|
| M1 | policy 定数 `2.0` → `3.0` | KILLED (metamorphic + 各層 wiring) | 他層に literal が無いことを AST test が保証 |
| M2 | loader の policy equality を削除 | KILLED (loader 負例) | 負例は schema-valid な `2.9`。schema も consumer も手前で落とさない |
| M3 | issuer の policy equality を削除 | KILLED (issuer 負例) | samples 完全一致・tolerance `2.9` は数値比較では通る |
| M4 | canonical consumer の policy equality を削除 | KILLED (consumer 負例) | 同上 |
| M5 | 取得時 self gate の外れ値判定を index slice で除外 | KILLED (48 index parameterize) | index 0 / 24 / 47 のいずれでも赤 |
| M6 | receipt の observed exact key 検査を削除 | KILLED (forged receipt 負例) | `_json_value` の任意 key 許可は残すため、この層だけが拒否する |
| M7 | silo の canonical predicate を median 比較へ戻す | KILLED (median-only outlier 負例) | 観測 `[2101]*47 + [3047.574]` は median では通り canonical では落ちる |
| M8 | v1 legacy parser の sentinel 厳密検査を緩める (`== 100.0` → truthy) | KILLED (v1 parser 負例) | `2.0` / `100` (int) / 3 key の負例 |
| M9 | registry 不変条件の loop 内で `passes = True` に固定 | KILLED (件数 assert + 入力可能 helper) | 空 loop 殺しの件数 assert と併走 |
| M10 | expected schema 上限を `== 100.0` の一点判定へ退行 | KILLED (境界テスト) | `nextafter(100, +inf)` と `1e300` が通ってしまう |

受理集合を縮小する wave であるため、**承認外の過剰拒否を検出する正例**も登録する —
P1: policy `2.0` かつ全標本が帯内の観測が canonical consumer と silo の両方で pass する。
P2: 履歴 v1 artifact 19 件が legacy parser で射影でき、`5.0` / `99.0` の expected artifact が
schema では依然 parse 可能である (U-5 の履歴 parse 保持)。

## gate の禁止署名と正例 (`DW-S04`)

- 禁止: `effective_clock_comparison_passes(expected, observed)` が
  `expected["tolerance_pct"] != EFFECTIVE_CLOCK_TOLERANCE_PCT` のとき True を返すこと。
  正例: `expected={"samples_mhz":[100.0],"tolerance_pct":2.0}`, `observed={"samples_mhz":[101.9]}` → True。
- 禁止: `validate_receipt_v2` が observed clock に `tolerance_pct` を含む receipt を通すこと。
  正例: observed が exact `{"samples_mhz":[...]}` の receipt → 通る。
- 禁止: `--effective-clock-tolerance-pct` を受理すること、および legacy env が設定された状態で
  投入が成功すること。正例: option 無しの投入が rc=0 で policy `2.0` の artifact を出す。

## scope 確定

実装する: 段 2 プランの単位 B / A / C から、A-5 (T126 bug fix) と A-6 後半 (T126 envelope v2) を
除いたもの + A-2/A-3/A-4/A-7/B-1/B-3/B-4/B-5/B-6 の是正。
実装しない: R-1 (loader self-pass)、R-2 (T126 bug fix)、R-3 後半 (T126 envelope)、
[T-419] / [T-477] / [T-478] の各面。
