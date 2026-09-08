# 段 6 裁定 — レビュー所見の採否と変異事前登録の追加

段 4 裁定 (`s4-ruling.md`) を上書きせず追補する。**設計 v2 と不変条件 1〜7 は不変。**

## レビュー所見の裁定

### レンズ A (実装の不変条件)

| 所見 | 判定 | 採否 | 裁定 |
|---|---|---|---|
| A1 charset・長さ検査は値の由来と機密性を保証しない / sentinel 偽装が可能 | **一部 real** | **一部採用** | 「由来まで保証せよ」は本 wave の scope 外 (`PreregistrationError.reason` は設計上開いた語彙であり、閉じるのは別の変更)。**ただし sentinel 偽装は安く閉じられるので採用する:** 両 sentinel を、それぞれの受理正規表現に**一致しない**文字列へ変える (例: 受理は `[a-z0-9-]+` なので sentinel に `<` `>` を含める)。これで「表現不能だった」と「たまたま sentinel と同じ値だった」が曖昧にならない。 |
| **A2 CLI の外側 catch が `str(exc)` を stderr に出す** | **real** | **scope 外** | これは本 wave が入れた経路ではなく、変更前から存在する CLI の終端である。裁定の不変条件 4 は**本 wave が足す診断 channel** に掛かる。ここを変えると既存 CLI の stderr 出力が変わり、別の受理集合の話になる。段 7 で次の一手へ登録する。 |
| **A3 診断出力の `print` が `OSError` を出すと未処理例外になる (blocker)** | **real** | **採用** | 不変条件 7 に直接抵触する。stderr 閉鎖・broken pipe・容量不足で、変更前なら定義済みの値を返した評価が未処理例外に変わる。**診断の出力全体を `except Exception` で囲み、失敗しても現行の終了値を返す。** 診断が出せなかったこと自体で終了値・stdout を変えない。 |

### レンズ B (テストと変異の検出力)

事前登録した M1〜M3・D1〜D8 は **11 件すべて検出可能**と裏取りされた。追加所見は次のとおり。

| 所見 | 判定 | 採否 | 裁定 |
|---|---|---|---|
| **B1 `except Exception` → `except RuntimeError` の変異が生存 (S1/S2)** | **real** | **採用** | 捕捉集合を変えない不変条件を直接攻撃する変異が殺せていない。現行の負例が `RuntimeError` family (= `PreregistrationError` を含む) に偏っているため。**evaluator が `ValueError` を直送する負例と、遅延 iterable が materialize 中に `TypeError` を出す負例**を足す。 |
| **B2 CLI が evaluator 側 callsite を通らない (S3)** | **real** | **採用** | CLI で callsite ごとに診断を捨てる変異が生存する。**live evaluator が `RuntimeError` を直送する実 process CLI fixture**を足し、evaluator 側 callsite の stderr を exact で固定する。 |
| **B3 長さ境界と charset 拒否境界が未固定 (S4〜S6)** | **real** | **採用** | 128 文字ちょうどを受理する assertion、129 文字を sentinel にする assertion、`_` を含む reason を sentinel にする assertion を足す。 |

## 追加する変異事前登録 (`DW-M01`: 段 6 の real 所見は fix 前に登録)

### 枠 1 追加: 受理集合・捕捉集合の変異 (期待 KILLED)

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| M4 | `_default_registry_results` の evaluator 側 catch | `except Exception` → `except RuntimeError` | KILLED (`ValueError` 直送の負例が未処理例外になる) |
| M5 | `_default_registry_results` の normalize 側 catch | `except Exception` → `except RuntimeError` | KILLED (遅延 `TypeError` の負例が未処理例外になる) |

### 枠 2 追加: 診断感度 pin (`DW-M08` の別枠)

| ID | 位置 | 変異 | 検出する assertion |
|---|---|---|---|
| D9 | CLI の診断出力 loop | `callsite` で絞り、evaluator 側の診断を出さない | evaluator 直送の実 process CLI 負例 |
| D10 | reason の長さ検査 | `<= 128` → `< 128` | 128 文字ちょうどの reason を受理する assertion |
| D11 | exception type の長さ検査 | `<= 128` → `< 128` | 128 文字ちょうどの type 名を受理する assertion |
| D12 | reason の受理 charset | `[a-z0-9-]` へ `_` を足す | `_` を含む reason が sentinel になる assertion |
| D13 | CLI の診断出力を囲む `except` を外す | 診断出力の失敗が終了値を変える | stderr の `write` が `OSError` を出す状況で `main()` が現行の終了値を返す assertion |
| D14 | sentinel を受理正規表現に一致する値へ戻す | sentinel 偽装が復活する | sentinel が受理正規表現に一致しないことを直接固定する assertion |

## fix の scope (これ以外を実装しない)

1. 両 sentinel を受理正規表現に一致しない値へ変える (A1 の一部)。
2. CLI の診断出力全体を `except Exception` で囲み、失敗しても現行の終了値・stdout を保つ (A3)。
3. 次のテストを足す (B1・B2・B3・D13・D14 に対応)。
   - evaluator が `ValueError` を直送する負例 (12 件の exact fallback + 診断 3 field)。
   - 遅延 iterable が materialize 中に `TypeError` を出す負例 (同上、callsite は normalize 側)。
   - live evaluator が `RuntimeError` を直送する実 process CLI 負例 (stdout bytes 不変 + evaluator 側 callsite の exact stderr)。
   - 128 文字ちょうどの reason / type 名を受理する assertion と、129 文字が sentinel になる assertion。
   - `_` を含む reason が sentinel になる assertion。
   - stderr の `write` が `OSError` を出す状況で `main()` が現行の終了値を返し、stdout が不変である assertion。
   - 両 sentinel がそれぞれの受理正規表現に一致しないことを直接固定する assertion。

**scope 外 (実装しない):** A2 の既存 CLI 終端の `str(exc)` 出力、reason 語彙を閉じる変更、gate・検査・台帳・一般化の追加。

## 受理・拒否の含意 (`DW-C01`)

- **拒否側:** 例外理由が表現できない (型・文字種・長さが外れる) 入力は、診断へ生の値を載せず sentinel へ倒す。sentinel は受理正規表現に一致しないので、正当な reason と取り違えられない。
- **受理側:** `[a-z0-9-]` だけからなり 128 文字以下の reason は、そのまま診断に現れる。**通る正例:** `PreregistrationError("predicate-result-type")` は `preregistration_reason == "predicate-result-type"` として診断に出る。
