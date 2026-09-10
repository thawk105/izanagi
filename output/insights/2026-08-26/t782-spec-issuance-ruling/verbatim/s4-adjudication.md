# 段 4 裁定 — [T-782] 査読済み spec の凍結発行

## 0. 結論

**この wave では実装しない (`4→7→8→9`)。** 裁定 D840 の向き (b) は不採用にせず維持する。
新事実を添えてユーザー再裁定へ返す (DW-S04 の「親は不採用にせず、新事実を添えて
ユーザー再裁定待ちへ戻す」)。

理由は 1 つに集約される。**この wave が触れる全機能は、今日発火しない gate の下流にある。**
`DW-G04` は「条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を brief に
書ける場合だけ実装する。書けなければ設計メモに留める」と定める。書けない。

## 1. 段 4 直前の裁定 inbox 再走査で拾った決定的な更新

wave 開始後 (09:53 以降) に main が `9463bcbc → 68fc629e` へ進み、**D959 が着地した**
(`docs/decisions.md:34281`、2026-08-26)。本文は B-2 の閉塞を依存の層として記録し、
上流から (a) 発効判定に充足を返す終端が無い / (b) 事前登録 §5 の数値欄 7 件が未記入 /
(c) 正式 profile の hard stop / (d) 6 cell manifest・二段束縛 record・trial registry の不在 /
**(e) schedule authority の無条件 raise** / (f) 共有 8b ratified freeze が active でない、
と並べたうえでこう書いている。

> **(b)〜(e) は (a) に従属する下流症状であり、順序を入れ替えて先に解除してはならない。**

**(e) schedule authority の無条件 raise が、まさに本 wave の対象**である
(`load_approved_spec` が `no-approved-spec` を上げる箇所)。同じ日に着地した決定が、
本 wave の実装を「順序違反」と名指ししている。

同 D959 はこうも書く。

> **(f) だけは (a) と独立に進められる別線である。**

したがって T-782 の実際の次の一手は T-782 自身ではなく **(f) 共有 8b ratified freeze の
発効**である。これは「できない」ではなく「先にどれを動かすか」の話である。

## 2. 所見の裁定 (real/refuted・採否・scope)

### sol レンズ

| ID | 判定 | 採否 | 根拠 |
|---|---|---|---|
| S1 v1 trust root 迂回 | **real** | 採用・実装しない wave では設計メモへ | `V1_FREEZE_SHA256` (`s8b_ratified_freeze.py:65`) を親が実在確認。producer が照合を欠く指摘は正しい |
| S2 「生成不能」の一般化は不成立 | **real** | 採用 (親の誤りを確定) | `blocker-correction.md` で撤回済み。sol の境界線 (candidate は作れる / official manifest は作れない) が正しい |
| S3 導出可能値を外部入力へ戻した | **real (ただし向きが逆)** | 採用・後述の訂正へ | 下記 §3 参照 |
| S4 `(h, file 無し)` 枝が未検査 | **real** | 採用・設計メモへ | 状態機械の網羅漏れ |
| S5 symlink で査読外 bytes を承認済みにできる | **real** | 採用・設計メモへ | 親も独立に同型を検出済み (`parent-design-note-2.md`)。ただし発火は pin 非 None 後 |
| S6 親の pin 閉包列挙が不完全 | **real** | 採用 (親の誤り) | `PIN_GATE_SPEC_RAW` 等を実在確認。brief §3 の「全件」は偽 |
| S7 変異事前登録 6 件が帰属不成立 | **real** | 採用・実装時に再設計 | 具体 witness つき。実装しないので今回は登録しない |
| S8 新規 test file が偽緑ガードで赤 | **real** | 採用・設計メモへ | `test_plain_runner_coverage.py:60` を実在確認 |
| S9 運用層が scope 外 | **real** | 採用・裁定パッケージへ | |

### luna レンズ

| ID | 判定 | 採否 | 根拠 |
|---|---|---|---|
| L1 fixture との二重 assembler | **real** | 採用・設計メモへ | 交差検査が serializer 部分にしか効かない指摘は正しい |
| L2 D840 の逐語と現行実装が衝突 | **real** | **採用・ユーザー再裁定へ** | 下記 §4 |
| L3 candidate bytes の consumer が repo 内に存在しない | **real** | **採用・実装しない主因の 1 つ** | D841 が名指しした型 |
| L4 A/B の編集面は素集合でない | **real** | 採用 (親の誤り) | 境界検査を足すなら B と同じ file を触る |
| L5 run_contract の入力契約が親記録と衝突 | **real** | 採用・§3 の訂正へ | |
| L6 除外理由 4 行は oracle の値域ではない | **real** | 採用 (親の誤り) | 下記 §3 |
| L7 binding identity は site/compiler 依存 | **real** | **採用・実装しない主因の 1 つ** | 生成 site と実走 site が違えば `binding-refused` |
| L8 A/B とも設計メモ止まりが正しい順序 | **real** | **採用 — 本裁定の結論と一致** | |
| L9 承認・設置・受入・runbook が閉じない | **real** | 採用・裁定パッケージへ | 既存設計資産 (下記) を発見した点も採用 |
| L10 v1 は trust root であり、論点設定は半分誤り | **real** | 採用 (親の誤り) | 親の「批准を経ていない」という枠組みは不正確 |
| L11 hash が合う stale spec を受理する | **real** | 採用・設計メモへ | D480 が数日単位の失効を実測済み |

**refuted と裁定した所見はゼロ。** 両レンズとも根拠が file:line で追え、親が独立に
実在確認した 6 件 (S1/S6/S8/L6/L9/L10 の要の主張) はすべて成立した。

## 3. 親の実測記録の訂正 (2 度目)

`measurements-2.md` の「3 項目は導出できる」は、**spec の権威という意味では誤り**だった。
S3/L5/L6 が正しい。

- `run_contract.clocks` / `contract_sha256` / `ccbench_pin` / `env_tag` は
  **spec validator では任意値**である。証拠は `test_s8b_oracle_manifest.py:66-99` の
  `PIN_GATE_SPEC_RAW` — 承認経路の positive fixture が `env_tag:"test-env"`、`clocks:1800`、
  `contract_sha256:"0"*64`、`ccbench_pin:"pin"` を通している。
  env 契約との照合は **driver 実走時に初めて起きる** (`s8b_oracle_driver.py:954`)。
- `allowed_excluded_reasons` の承認凍結 4 行は **floor protocol の権威**であって
  oracle spec の権威ではない (`s8b_floor_contract.py:523-528` が floor 側)。
  oracle spec validator は重複なし非空文字列列を任意に受理し
  (`s8b_oracle_spec.py:172-178`)、同 fixture は `machine-failure-日本` を意図的に通している。
  親は floor の権威を oracle へ無裁定で移植していた。

**正しい整理**: 「導出できる/できない」の二分ではなく、**どの層が値を拘束するか**である。

| 軸 | spec validator | driver 実走 | 結論 |
|---|---|---|---|
| `holdout_ids` / `configuration_ids` | freeze と突合しない | freeze の完全積と突合 | 実質 freeze 由来 |
| `generator_versions` | live source bytes と一致必須 | — | live 由来・数日で失効 (D480) |
| `reps` / `extime` / `verify` / `screening` / `bench_max_rounds` | 承認凍結値に完全一致必須 | — | 固定 |
| `clocks` / `contract_sha256` / `env_tag` / `ccbench_pin` | 型のみ | env 契約と完全一致必須 | **設計値。実走で初めて拘束** |
| `allowed_excluded_reasons` | 型のみ | report の受理集合を決める | **設計値。oracle 側に凍結表は無い** |
| `n` / `master_seed` / `block_sizes` / `campaign_ids` | 型と整合のみ | — | 設計値 |
| `binding_identity` | 内部整合のみ | 再実体化と完全一致必須 | **生成 site 依存 (L7)** |

## 4. ユーザー再裁定へ返す論点

### Q1 — D840 の逐語をどう読むか (L2)

D840 は「CLI 側は凍結 spec の指紋照合だけを行い、**内容の再導出や束縛検査を持たない**」と書く。
しかし現行実装は既に内容を再導出している — `verify_manifest`
(`s8b_oracle_manifest.py:1123-1157`) が承認済み spec から schedule を再生成して完全一致を要求し、
campaign_ids / run_contract / binding_identity / allowed_excluded_reasons / generator_versions を
projection ごとに突合する。

**D840 を逐語で実装すると、既に動いている正しさ検査を撤去することになる。** これは絶対規律 2 に
真正面から反する。親はこれを「D840 は新しい解釈を追加しないという意味である」と読み替えて
進めることもできたが、裁定文の逐語を親が黙って弱めるのは `DW-S04` が禁じる形なので、
**読み替えの可否をユーザーへ返す。**

親の推奨: **「消費側へ *新たな* spec 解釈を足さない」と読む。** 既存の再導出は D302 が
「hash は識別子にすぎず、承認は内容の再導出を伴う」と裁定済みであり、撤去は受理集合の拡大になる。

### Q2 — 順序: T-782 と (f) 批准凍結のどちらが先か (D959)

D959 は T-782 の対象 (e) を下流症状と位置づけ、順序の入れ替えを禁じた。同時に (f) は独立線と
明記した。**T-782 を今動かすと D959 の順序規定に反する。**

親の推奨: **T-782 は (f) の後へ送る。** (f) が発効すれば binding identity の権威が定まり、
L7 の site 依存も批准された値で解決し、L3 の consumer 不在も 6 cell manifest の配線で埋まる。

### Q3 — 凍結する bytes の再現性 (L7)

`src_token` は `source_digest` 自身が cxx/環境依存と明記する値である。生成 site (login node) と
実走 site (計算ノード) が違えば、凍結した identity が実走時の再実体化と一致せず
`binding-refused` になる。**「先に凍結する」ためには、どの site の identity を凍結するかを
先に決めなければならない。**

親の推奨: 凍結は実走する計算ノード上で行い、spec に生成 site を記録する。ただしこれは
schema の追加であり D355 の v1 据え置きに触れるため、(f) と同じ変更単位で扱う。

### Q4 — 既存設計資産の扱い (L9)

`output/insights/2026-08-12_t499-spec-producer-design/verbatim/s2-plan.md` に、
T-499 の段 2 が既に producer 設計を書き終えている — `preview` と `install-approved` の分離、
create-only、`--output` を持たせない、`_write_approved_manifest` の安全性を踏襲、まで。
**本 wave の plan はこの資産を参照せず再設計していた。** 実装 wave はこれを起点にすべきである。

## 5. 実装しないことの成果物影響 (DW-G05)

**現在と 1 bit も変わらない。** `APPROVED_SPEC_SHA256` は `None`、durable spec は 0 件、
official manifest は 0 件、certified 選択・レポート・台帳の値は全て不変である。
これは L8 の指摘と一致する — A も B も、land しても成果物の値を 1 つも変えない。

逆に実装した場合に増えるのは、休眠 capability と休眠 test state だけである。
そのうえで D959 の順序規定に反し、S1/S5/L7/L10 の穴を持った producer を先に置くことになる。

## 6. 段 5・6 を飛ばす。変異 matrix は免除、受入全走は免除しない

`DW-S04` に従い、実装差分ゼロなので変異 matrix を免除する。受入全走は免除しない。
docs 変更後に `tools/dev_wave_wait.py acceptance` で全走を投入する。
