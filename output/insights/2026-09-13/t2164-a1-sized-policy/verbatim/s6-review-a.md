## 総括

must-fix は見つかりませんでした。D1452 の5項目は、hash 検査に遮られず各照合で拒否される負例になっています。
R2 の underflow 拒否も、証明書との不一致に依存せず効きます。
real の nit は、M1 が指定負例より先に fixture の正例ロードで赤になる点です。
前後空白・全角数字は数値検査では受理されますが、後段の float 算術は壊れず、凍結 policy の差し替えは別途拒否されます。
実測したのは hash・逐語比較・AST による関数集合・単発の数値変換です。pytest・変異テストは実行していません。

以下、`P` は `orchestrator/campaign/paper_story_a1_paired.py`、`T` は `orchestrator/tests/test_paper_story_a1_paired.py`、`R` は指定の凍結事前登録 README を指します。

## must-fix

なし。

## nit

1. **[real／静的判定] M1 の期待 kill node と実際の失敗位置が一致しません。**

   `s4-ruling.md:150` は期待値を `20000 → 19999` に変えて「search-trials の負例」で kill する計画です。しかし `T:1116` の fixture が先に凍結証明書をロードするため、正しい `20000` が `P:1423` で拒否され、負例本文 `T:1190` に到達しません。fixture を通しても `T:1189` の正例確認があります。

   成果物の値・受理集合・参照への影響はありません。影響は変異検査の帰属です。M1 の期待を「正例拒否」に訂正するか、search 項の削除変異で負例の検出力を別途確認してください。

2. **[real／静的判定] 正例テストを拒否検査の削除耐性の証拠には数えられません。**

   `T:1137` の実 policy 正例、`T:1311` の算術テスト、`T:1334` の seed テストは、D1452 照合や float 正値検査を削除しても緑のままです。それぞれ実値・算術・導出規則を検査するテストなので、恒真という意味ではありません。検出力の内訳は次節の表のとおりです。

   成果物への影響はなく、受入証拠の分類上の注意です。

## refuted

### 1. [refuted] D1452 の負例が hash 検査で先に落ちる

証明書 hash の検査自体は `P:1310` にあり、追加照合より先です。しかし負例は `T:1128` の helper で canonical bytes を書き、`T:1134` で binding の hash も更新しています。呼出先は `_validate_policy_semantics` なので、後段の policy bytes pin も通りません。

| 単独変更 | 先行検査との関係 | 拒否位置 |
|---|---|---|
| `search.trials=19999` | workload・入力 binding を変えない | `P:1423` |
| `certification.trials=99999` | 同上 | `P:1423` |
| `registered_minimum=29` | selected の n/df を変えない | `P:1423` |
| `maximum=4095` | selected・候補列を変えない | `P:1423` |
| `root_seed.digest="0"*64` | 入力 binding・workload を変えない | `P:1423` |

負例は各 field 名で終わるエラーを要求します（`T:1178`、`T:1194`）。各対応項だけを削除すれば、その負例は例外不発で赤になります。これは静的判定です。

なお、**binding の hash を更新せず証明書だけを書き換える攻撃**は、当然 `P:1310` で先に拒否されます。この経路と照合単独の検査を混同していません。

### 2. [refuted] 型込み照合を指定の型がすり抜ける

`P:1423` は型同一性を値比較より先に要求します。

- `True`、`20000.0`、`"20000"`：整数期待値とは型が異なり拒否。
- 大文字 digest：型は同じですが文字列が異なり拒否。
- `int` 派生型：比較位置に直接来れば型相違で拒否。

JSON decode 後には通常の `int` しか残りません。派生型を JSON 整数に直列化して読み戻した場合は、元の Python 型を識別する検査ではありません。これは証明書の JSON 型契約の穴には当たりません。

### 3. [refuted] R2 が underflow・非有限値を受理する

根拠は `P:1275` と `P:1521`。次の変換結果は単発の Python 計算でも確認しました。

| 入力 | sized 数値検査 |
|---|---|
| `"1e-999"` | Decimal は正、float は `0.0`。`P:1531` で拒否 |
| `"-0"` | Decimal の正値検査で拒否 |
| `"NaN"`、`"Infinity"` | Decimal の有限性検査で拒否 |
| `0` | Decimal の正値検査で拒否 |
| `" 2.8315526875186725 "` | 受理 |
| `"２.８３１５５２６８７５１８６７２５"` | 受理 |
| `"２．８３"`（小数点も全角） | Decimal 変換で拒否 |

受理される空白・全角数字は、証明書と同じ数値なら `P:1393` の Decimal 比較も通ります。後段の `float()` も同じ有限正値になり、算術は壊れません。`planned_sigma_tps` も同じ扱いです。

これは表記の受理範囲であり、R2 の正値・有限条件への違反ではありません。凍結 policy と異なる文字列を公開 validator に渡せば `P:1751`、disk bytes を変えれば `P:1756` で拒否されます。

### 4. [refuted] 十進文字列が後段へ漏れて算術・出力を壊す

policy の直接読取箇所は、`k` が4箇所、`planned_sigma_tps` が5箇所です。

| 用途 | `k` | `planned_sigma_tps` |
|---|---|---|
| v2 検証 | `P:1204` | `P:1205` |
| sized 証明書比較 | `P:1394` | `P:1403` |
| sized 数値検証 | `P:1522`（共通ループ） | 同左 |
| 算術・結果出力 | `P:4762` | `P:4769` |
| variance 比較 | — | `P:4770` |

証明書側の読取は別に `P:1396`、`P:1406` です。v2 の受理条件は変更されていません。

producer と consumer はともに `P:4706` の計算へ入り、結果の k/sigma は float になります。JSON 結果への格納は `P:5455`、consumer の再計算比較は `P:7789` と `P:7963`、本文整形は `P:8051` 以降です。receipt・ログ側に元の k/sigma 文字列へ直接算術を適用する箇所は見つかりませんでした。

結果 JSON の sigma は binary float に丸められますが、証明書との厳密照合はその前に Decimal で済ませています。

### 5. [refuted、一部 real の限界] 新規9テストが恒真

下表の関数名は共通の `test_v3_sized_` 接頭辞を省略しています。赤／緑は未実行の静的予測です。

| テスト・根拠 | 対象処理を除いた場合 |
|---|---|
| `frozen_policy_loads_with_registered_certificate` — `T:1137` | **緑**：拒否検査の削除は検出しない。文字列を受理できなくする変更や、列挙された成果物値の変更は検出 |
| `certificate_requires_registered_parameters` — `T:1185` | **赤**：対応する照合項を削除すると例外不発 |
| `certificate_rejects_missing_or_mistyped_registered_parameters` — `T:1210` | **赤**：照合全体の削除を検出。型条件だけの削除も整数相当 float のケースが検出 |
| `certificate_preserves_decimal_statistics` — `T:1236` | **赤**：sigma 比較の削除・float 比較への置換で例外不発 |
| `statistics_reject_invalid_decimal_values` — `T:1259` | **赤**：float 正値条件の削除は、証明書も合わせた underflow ケースが検出 |
| `policy_bytes_are_pinned` — `T:1275` | **赤**：M5 は load／validate の両方で例外不発 |
| `preregistration_binding_has_no_policy_self_reference` — `T:1292` | **赤**：README bytes 検査を削除すると末尾改変が通る |
| `consumer_uses_registered_decimal_statistics` — `T:1311` | **緑**：入力 gate の削除には反応しない。float 変換・半幅・variance 判定の破壊は検出 |
| `schedule_roots_follow_frozen_derivation` — `T:1334` | **緑**：入力 gate の削除には反応しない。凍結原像と異なる seed は検出 |

依存する validator・算術処理を stub していません。fixture の差し替えは複製先の repository root です（`T:1124`）。

不正数値の全ケースが単独の条件を証明するわけではありません。例えば負数は Decimal と float の両方で拒否可能です。ただし M4 の `"1e-999"` は Decimal 側で拒否されず、証明書も同値なので、正値条件の単独証拠になります。

### 6. [refuted] 既存テストの弱体化

AST 比較の実測結果は **124関数 → 133関数、削除0、追加9**。既存の assert・期待例外の変更、削除、skip／xfail の追加はありません。

既存テストへの追加は、凍結された preregistration・policy pin と D1452 に合わせた synthetic fixture の整備です（`T:1018`、`T:1041`、`T:1088`）。既存負例は `T:1096` 以降に残っています。

### 7. [refuted] policy と証明書・seed の不一致

逐語・型比較を実測し、3 workload とも以下が一致しました。証明書は `sizing-certificate.json:1`、policy は `paper_story_a1_paired.v3-sized.json:228`、`:269`、`:310` です。

| workload | reps / df | k | planned_sigma_tps |
|---|---|---|---|
| write-heavy | 30 / 29 | `"2.8315526875186725"` | `"66403.452108019716"` |
| balanced | 30 / 29 | `"2.8315526875186725"` | `"56697.435713574683"` |
| read-heavy | 30 / 29 | `"2.8315526875186725"` | `"74668.489566274948"` |

`R:114` の原像を ASCII・改行なしで独立に SHA-256 計算し、次の3値も policy と一致しました。

```text
write-heavy e82d0c269021faae457924b71e22b720ca881d4ff0ac6726cf4d8c9c774323d3
balanced    f322d1daa33e1dd5bf15d3566cc81bb817a15233be762ca64a22664bb3c0ff94
read-heavy  9ad57bf708b51345af6a65c2208493f99e1d3c308cc48b329b816240d9a701ce
```

policy・README・証明書の実測 hash も、それぞれ module pin／binding と一致しました。

### 8. [refuted] 段4の実装範囲との齟齬

R1 は `P:1036`、R2／R3 は `P:1521`、R4 は workload 検査後の `P:1413` に実装されています。R5 の凍結時点と引き直し禁止は `R:107` 以降に明記されています。

pilot との policy 比較で、裁定外の設定変更は見つかりませんでした。道具側の変更も差分にありません。本走実行面が未完了である限定は `R:402` に残っています。

## 親裁定へ返す項目

- **[real] M1 の変異結果は「指定負例による単独 kill」と記録しないでください。** 現状は fixture の正例ロードが先に拒否されます。
- **[refuted] D1452・R2 の実装不備を理由とする差戻しは不要です。** ただし、本レビューは変異の赤を実測した証拠ではありません。
- 前後空白・全角数字の受理は、数値同一性と凍結 bytes pin を踏まえると追加修正を要する所見ではありません。