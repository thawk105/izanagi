# 段 4 裁定 — [T-452] tolerance_pct の権威設計

親 (manager) が段 2 設計案と段 3 敵対 2 レンズ (A: 恒真ゲート / B: 整合・consumer) を裁定した。

## 0. 実装の可否

**実装しない。** 本 wave の依頼は「設計案の起草」であり、方向裁定 (2026-08-04 /rulings) は
「policy 固定値の方向で起草し、最終形は設計案で確定」である。段 3 が **両レンズとも NO-GO** を
返し、その must-fix の 2 件 ([所見 B-1] / [所見 B-2]) は**他タスクの所有面と順序**に触れる。
親がここを独断で確定しない (`DW-S04`)。したがって `4→7→8→9` とし、段 5・6 を飛ばす。
実装差分が無いため**変異 matrix と受入全走の変異部分は射程外**である (受入テストは記録 commit 後に走らせる)。

## 1. 所見の裁定 (12 件)

| 所見 | 判定 | 採否 | scope | 親の裏取り |
|---|---|---|---|---|
| A-1 loader/issuer の負例が schema に遮蔽される | real | 採用 | 内 | 設計案が schema 上限を `<100.0` にする以上、`100.0` 負例は手前で落ちる。論理的に自明 |
| A-2 取得時 gate の負例が末尾外れ値のみ | real | 採用 | 内 | `cli.py:381-391` は list slice を 1 行で無効化でき、既存負例 (`test_calibrator_certify.py:531-577`) は index 47 固定 |
| A-3 observed tolerance の混入経路が閉じていない | real | 採用 | 内 | **実測**: `execution_guard.py:216-221` の `_json_value` は Mapping を任意 key で再帰許可する。receipt の nested observed に `tolerance_pct` を足しても `validate_receipt_v2` は通る |
| A-4 policy golden は値だけで wiring を固定しない | real | 採用 | 内 | 各層に literal `2.0` を直書きしても値一致 test は緑。論理的に自明 |
| A-5 registry 不変条件に constant-pass 負例が無い | real | 採用 | 内 | `test_env_contract.py:436-463` は `passes = True` 変異を殺せない |
| A-6 tolerance 値は守れても producer provenance は証明できない | real | 採用 (射程の明示) | 一部外 | **実測**: `test_env_contract.py:339-371` の canonical path 検査は `output/env/<key>/calibration/` 配下のみを要求し、`registered/` を要求しない。別タスクへ起票 |
| A-7 `100` 一点テストは `<100` 境界を固定しない | real | 採用 | 内 | 現 schema 負例集合に上限超過ケースが無い |
| A-8 入力面不在テストが文字列検索に依存 | real | 採用 | 内 | 分割表記・別名で source search を回避できる。論理的に自明 |
| B-1 contract SHA が凍結 floor protocol まで波及 | real | 採用 | **scope 拡大** | **実測**: `output/s8b-freeze/floor_protocol.json` は `contract_sha256=e576e9cd…` を内包し、同 file は `FROZEN_MANIFEST` の pin 対象。calibration path/sha を動かすと contract SHA が動く |
| B-2 T-453 の median consumer を残した authority は不完全 | real | 採用 | **裁定へ返す** | `silo_ladder_rung1.py:1964,3407` は loader/issuer/canonical のどの防壁も通らない独立経路。ただし T-453 は別タスクの所有であり、結合可否は親が決めない |
| B-3 observed 型変更に schema 版と履歴 replay が無い | real | 採用 | 内 | **実測**: staging の observed 15 件は `pegasus-probe-output/v1` で clock key が 4 個 (`tolerance_pct` を含む) |
| B-4 fixture / golden 移行 matrix が不足 | real | 採用 | 内 | 任意 tolerance を前提にした golden vectors (`test_execution_guard.py:360-470`) が policy 一致導入で一斉に変わる |

**refuted は 0 件。** 段 2 設計案の中心方針 (単一 policy 定数 2.0 / observed 型分離 / 各 trust
boundary での再検査 / issuer 独立実装の維持) は 2 レンズとも支持しており、破棄しない。

## 2. 親の provisional 裁定 (P1)〜(P5) の帰結

- **(P1) 独立 policy module** — 維持。ただし A-4 により「単一定数の存在」ではなく
  「各層が同一識別子を参照する wiring」を検査対象とする条件付き。
- **(P2) 固定値 2.0** — 維持。現 artifact (+46.641 %) を救済しない事実を設計案に明記済み。
- **(P3) observed 専用型** — 維持。B-3 により **observed 出力 schema の版上げと v1 の履歴
  replay 経路**を必須条件として追加する。
- **(P4) 値域を狭めるのではなく権威を一元化** — 維持。A-8 により入力面不在の検査を
  文字列検索から parser dest 集合 + 実行検査へ強化する条件付き。
- **(P5) 本 wave は実装しない** — 維持。

## 3. plan v2 (設計案 v2) の確定内容

段 2 の設計案に、上記 12 所見の採用結果を織り込んだものを
`output/insights/2026-08-04_t452-clock-tolerance-authority/README.md` に確定する。
主な差分は次の 5 点である。

1. 負例の値を `100.0` から **schema-valid な非 policy 値 (`5.0` / `99.0`)** へ変更 (A-1)。
2. 反証テストを「値一致」から **wiring / metamorphic (policy を `3.0` にすると全層が追従する)**
   へ変更 (A-4)、取得時 gate の負例を **外れ値位置で parameterize** (A-2)、
   registry 不変条件に **schema-valid・policy 一致・self-fail の負例**を追加 (A-5)。
3. receipt と歴史 raw の **observed effective-clock shape を exact key 集合で閉じる**機械を追加 (A-3)。
4. 移行を **contract 世代 (generation)** の設計へ格上げし、凍結 floor protocol・selector journal・
   golden を旧世代のまま解決可能に保つ (B-1)。旧 evidence の遡及再束縛は禁止のまま。
5. observed 出力を **`pegasus-probe-output/v2`** とし、v1 は「4 key かつ sentinel が厳密に 100」の
   legacy parser で内部型へ射影する (B-3)。fixture 移行 matrix を実装前提とする (B-4)。

## 4. 変異事前登録 (`DW-M01`)

**実装差分が無いため事前登録しない。** 代わりに、設計案の各機械に対して段 3 が構成した変異
(A-1〜A-8 の具体変異) を**実装 wave が事前登録すべき変異候補**として設計案 §5 に凍結する。
これらは「無効化しても全テストが緑」であることをコード上で確認済みの変異であり、
実装 wave はこれを起点に `DW-M01` の登録を行う。

## 5. ユーザーへ返す設計択一

`README.md` の §7 に U-1〜U-8 として置く。うち **U-6 (T-453 との結合)** と
**U-7 (contract 世代移行の所有)** は他タスクの所有面に触れるため、親は推奨だけを書き裁定しない。
