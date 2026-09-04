# 段 4 裁定 — [T-2148] 排他権の世代の粒度と非保持走行の値

## 裁定 inbox の再走査 (段 4 直前)

local main は `39086303b` → `229e030a3` へ進んだ。`docs/decisions.md` と、この wave の編集面
(`tools/acceptance_receipt_signature.py`、`tools/acceptance_issuer_reference.py`、
`orchestrator/tests/test_external_acceptance_signing.py`)、および待ち手・着地・dispatch tool
(`tools/dev_wave_wait.py`、`tools/dev_wave_land.py`、`tools/dev_wave_codex.py`、
`tools/wave_land_window.py`) の差分は**いずれも 0 件**である。新しい裁定も、先に取り込むべき
待ち手 bytes の前進もない。main は受入前に取り込む。

## 所見の裁定

レンズ A = sol、レンズ B = luna。

| # | 要旨 | 性質 | 採否 | scope |
|---|---|---|---|---|
| A1 | state と expected が同じ caller 由来で、取得の有無は照合されない | real | 採用 | 内 (主張の縮退) |
| A2 | 「明示入力なら D1499 に該当しない」は強すぎる | real | 採用 | 内 (表現) |
| A3 | 受理値域は marker 1 語だけに限定できる | refuted | 採用 | 内 |
| A4 | 既存の署名・鍵・schema 防壁に弱化は無い | refuted | 採用 | 内 (実測で確認) |
| A5 | 必須 keyword 追加で壊れる caller 9 箇所 | real | **前提消滅** | — |
| A6 | D1443 の縮退は「関門は不可避でない」まで書く | real | 採用 | 内 (docstring 1 文) |
| A7 | 「production consumer 不在」が一般化過剰 | real | 採用 | 内 (記録の限定) |
| A8 | source bytes の pin 0 件は限定主張として維持できる | refuted | 採用 | 内 |
| A9 | brief の走査対象表記の訂正と、author 直前の再実測 | real | 採用 | 内 |
| A10 | CLI→API の state mapping に証拠が無い | real | **前提消滅** | — |
| A11 | repo 外の運用 copy は未測定で、本 wave は更新しない | real | 採用 | **外** (実装しない) |
| B1 | `"not-acquired"` の採用は D1528 越境ではない | refuted | 採用 | 内 |
| B2 | 予約定数と serialized union の検査は本題に必要 | refuted | 採用 | 内 |
| B3 | 必須 `lease_acquired: bool` は第二の discriminator で新設 gate | real | 採用 | **棄却対象** |
| B4 | `expected_lease_acquired` も不要 (既存の完全一致で足りる) | real | 採用 | **棄却対象** |
| B5 | issuer の claims 表の更新は問題なし | refuted | 採用 | 内 |
| B6 | issuer の pair gate と状態転送は projection と重複 | real | 採用 | **棄却対象** |
| B7 | CLI の required mutually-exclusive group は scope 膨張 | real | 採用 | **棄却対象** |
| B8 | 「この 2 file を import するのは test だけ」は字義的に誤り | real | 採用 | 内 (表現) |
| B9 | 冗長 test を新機構の証拠に数えない | real | 採用 | 内 (test 集合を絞る) |
| B10 | (P2) は不要な設計選択、(P4)・閉包は観測範囲を明記 | real | 採用 | 内 |
| B11 | D1450 の実効保証は未完成 (plan は主張していない) | refuted | 採用 | 内 (完了報告の限定) |

**A5 / A10 の前提消滅について。** 両所見は「必須 bool 引数」と「新 CLI option」を前提に成り立つ
指摘である。B3 / B4 / B6 / B7 を採ってその 2 つを実装しないと裁定したので、壊れる caller も
CLI→API mapping も発生しない。所見が誤りだったのではなく、対象が消える。**実装後に「caller の
signature 変更が 0 件であること」を親が実測して閉じる。**

**レンズが割れた点の裁定理由。** marker と 64 桁小文字 16 進は構文的に交わらないので、値そのものが
取得あり / 取得なしを運ぶ。既存の `payload["lease_generation"] == expected_lease_generation` は
その 2 状態を既に区別する。したがって bool 引数は「同じ区別を 2 度目に行う関門」であり、
受理される受領証の集合も署名 bytes も変えない (`DW-G05` の成果物影響を書けない)。依頼の
「仮想リスク向けの gate の追加は scope 外」に該当するので棄却する。加えて A1 が示すとおり
bool を足しても取得の有無は照合されないままなので、棄却によって失う保証は無い。

## プラン v2 (実装する内容)

### `tools/acceptance_receipt_signature.py`

1. module 定数 `LEASE_NOT_ACQUIRED = "not-acquired"` を追加する。
2. `_require_lease_generation(value, field_name)` を追加する。受理は
   **`[0-9a-f]{64}` の完全一致、または `LEASE_NOT_ACQUIRED` との完全一致だけ**。
   それ以外は `ReceiptSignatureError(f"invalid {field_name}")` で拒否する。
   前後空白の除去、大文字小文字の畳み込み、部分一致、正規化を**行わない**。
3. `lease_generation` を検査している現行 3 箇所の `_require_sha256` を、この新しい検査へ置き換える。
   - `project_v5_receipt` (:185)
   - `canonical_signed_payload_bytes` (:212)
   - `verify_signed_receipt_signature` の `expected_lease_generation` (:351)
   他の hash field (`checker_content_sha256`、`issuer_key_id`、v5 の各 field) の検査は変えない。
4. 関数 signature、引数名、`SIGNED_V6_PAYLOAD_FIELDS`、canonical JSON 規則、鍵読取り、
   Ed25519 検証、context mismatch の判定順序は**変えない**。
5. docstring に次の 4 点を書く。
   - `lease_generation` の 64 桁値は**排他権の 1 回の取得**に対応し、別の取得へ再利用しない。
   - `LEASE_NOT_ACQUIRED` は**排他権を取得しなかった走行**を表す。
   - どちらの値も caller の自己申告であり、この module は live な排他権を読まず、
     取得の有無を検査しない。marker の一致は「caller が申告した状態と一致した」ことだけを意味し、
     排他検査を通った証拠ではない。
   - production の着地ツールはこの verifier を呼ばないため、**この関門は不可避ではない** (D1443)。

### `tools/acceptance_issuer_reference.py`

1. `issue_signed_receipt` の入力検査 (:463) を、署名 module の同じ union 検査へ委譲する
   (literal と正規表現を二重定義しない)。
2. 冒頭の claims 表の `lease_generation` 行を、取得ありは caller 提供の「1 取得に対応する識別子」、
   取得なしは `"not-acquired"`、どちらも live lease から独立導出・検査しない、と書き直す。
3. `--lease-generation` は**現行どおり required な単一 option**とし、値として `"not-acquired"` を
   受け付ける。新しい option、mutually-exclusive group、bool 引数、pair gate、
   早期の重複検証は追加しない。

### `orchestrator/tests/test_external_acceptance_signing.py`

既存テストの期待値・literal・canonical hash・root field 集合を**変更しない**。次を追加する。

- **T1 (正例・機構):** 実 production-v5 fixture から marker で projection し、実 Ed25519 鍵で
  署名して検証する。`payload["lease_generation"] == "not-acquired"`、canonical bytes に
  `"lease_generation":"not-acquired"` が含まれること、marker expected で同じ payload が返ることを
  assert する。`project_v5_receipt` / `canonical_signed_payload_bytes` / `attach_signature` /
  `verify_signed_receipt_signature` を実体として呼び、stub を置かない。
- **T2 (負例):** marker で署名した受領証を 64 桁 expected で検証し
  `signed receipt context mismatch` になることを assert する。
- **T3 (負例):** 64 桁で署名した受領証を marker expected で検証し
  `signed receipt context mismatch` になることを assert する。
- **T4 (負例・union の締め):** 予約語以外の非 sha 文字列 (`"none"`、`"NOT-ACQUIRED"`、
  `"not-acquired "`、`" not-acquired"`、`""`) が **projection / canonical payload / expected の
  3 経路すべて**で `invalid lease_generation` になることを assert する。
- **T5 (issuer):** 実 `issuer._parser()` が `--lease-generation not-acquired` を受理し、
  `issue_signed_receipt` の入力検査が `"not-acquired"` を受理して `"none"` を拒否することを
  assert する。

## 不変条件 (段 5・6 を通じて)

- v5 root field 集合、lease payload の bytes、`tools/wave_land_window.py`・
  `tools/dev_wave_wait.py`・`tools/dev_wave_land.py`・`tools/acceptance_launcher.py` は変えない。
- 取得あり経路の canonical bytes・length・sha256 pin は 1 bit も変えない。
- 既存テストの期待値を反転・緩和・skip・削除しない。赤なら実装側が誤りとする。
- 関数の公開 signature を変えない (caller 変更 0 件を実測で閉じる)。
- 新しい gate・検査・台帳・一般化・外部配置の更新をしない。

## 変異事前登録 (`DW-M01`)

各変異は単一理由性を**実装後に確認**する。期待 node は probe で観測してから確定する
(`DW-M07`: probe は全件 SURVIVED 期待で登録して観測 node を集める)。

| ID | 位置 | 変異内容 | 期待 | 単一理由性の確認点 |
|---|---|---|---|---|
| M1 | `_require_lease_generation` の marker 枝 | 完全一致を「64 桁 sha でなければ何でも受理」へ緩める | KILLED | T4 の 3 経路が拒否の唯一の層か。前後・内側に同じ入力を拒否する層が無いこと |
| M2 | `canonical_signed_payload_bytes` の lease 検査だけ | union 検査を `_require_sha256` へ戻す (他 2 箇所は union のまま) | KILLED | T1 が marker の canonical 経路で赤になり、projection と expected では赤にならないこと |
| M3 | `verify_signed_receipt_signature` の expected 検査だけ | union 検査を `_require_sha256` へ戻す | KILLED | T1 の検証段だけが赤になること。T2 は 64 桁 expected なので影響を受けないこと |
| M4 | issuer の入力検査 | union 委譲を元の `_SHA256_RE` のみへ戻す | KILLED | T5 だけが赤になり、署名 module 側の test は緑のままであること |

`DW-M03` に従い、診断文字列だけの赤は kill に数えない。M2 / M3 が同じ node で赤になるなら
過剰決定なので、冗長 gate と明記して単独変異の証拠から外す。

## 実装しない・報告で限定すること

- repo 外の運用 copy の更新、production waiter / lander への配線、世代の導出方式の採用、
  取得間の一意性の強制はいずれも実装しない (D1528、A11)。
- 完了報告は「粒度の契約と非保持走行の値を確定した」までとし、D1450 の実効的な再送防止を
  達成したとは書かない (B11)。
- 「production consumer 不在」は「repo 内で waiter / lander からの配線が無く、tracked な
  着地ツールは v5 だけを受理する。issuer 自身は署名 module を import する。repo 外の運用 copy は
  未測定」と書く (A7、B8)。
