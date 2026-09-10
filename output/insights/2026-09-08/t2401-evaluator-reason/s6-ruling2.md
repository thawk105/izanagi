# 段 6 裁定 (2 巡目) — 焦点再レビュー所見の採否

`s4-ruling.md` の設計 v2 と不変条件 1〜7 は不変。`s6-ruling.md` に追補する。
**焦点再走は 2378 passed / 8 skipped / 赤 0 (計算ノード、110 秒)。実装の欠陥は 1 件も出ていない。**
残る所見はすべて**テスト側の変異感度**である。

## 裁定

| 所見 | 判定 | 採否 | 裁定 |
|---|---|---|---|
| 所見 1 (README allowlist が裁定外の変更) | **事実は real、欠陥ではない** | **不採用 (記録のみ)** | この編集は fix 子ではなく**親**が行った。焦点走で `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries` が赤になり、同メタテストが「自走 harness を足したら allowlist から外せ」と明示的に要求したためである。commit message にも書いてある。**親が段 6 裁定の scope 表へ書き落としていたのは手続きの漏れ**なので、段 7 の記録に残す。差分は元に戻さない (戻すとメタテストが赤に戻る)。 |
| **所見 2 (S7: 128/129 の境界テストが production 定数を oracle にしている)** | **real** | **採用** | 境界入力を `_DIAGNOSTIC_TEXT_MAX_LENGTH` から生成しているため、定数を 127 や 129 に変える変異が緑のまま通る。**派生値の pin は生成器の検査にならない。** 境界テストは literal の 128 / 129 を使い、production 定数が 128 であることも直接固定する。 |
| **所見 3 (S8〜S14: catch 集合を「テスト済みの例外型だけ」へ狭める変異が生存)** | **real・ただし完全閉包は不能** | **一部採用** | 有限の例外型しか試さないテストは、その型だけを列挙する catch 変異に原理的に勝てない。**無限後退なので「閉じた」とは主張しない** (規律 7・D387: repo 内の挙動検査は意図的な弱体化への完全な防壁ではない)。安く効く範囲として、**4 つの catch 地点それぞれの負例を構造的に無関係な例外型で parametrize する**。helper の 2 つの `except BaseException` には `SystemExit` 以外の `BaseException` (例: `KeyboardInterrupt`) の負例を足す。CLI 出力の guard には `OSError` 以外の負例を足す。**残る限界は段 7 に明記する。** |
| **所見 4 (S15: CLI が `ValueError` の診断を選択的に捨てる変異が生存)** | **real** | **採用 (安い形だけ)** | 既存の実 process CLI fixture を**例外型で parametrize** して `ValueError` の場合も通す。新しい fixture file や新規 test file は作らない。parametrize が既存 fixture の構造上できない場合は実装せず報告して止まる。 |
| 所見 5 (A1: 許可文字内の外部由来 reason の由来保証) | real | **scope 外 (裁定済み)** | `s6-ruling.md` で裁定済み。reason 語彙を閉じるのは別の変更。 |
| 所見 6 (A2: 既存 CLI 終端の `str(exc)`) | real | **scope 外 (裁定済み)** | `s6-ruling.md` で裁定済み。段 7 で次の一手へ登録する。 |

## 追加する変異事前登録 (`DW-M01`: fix 前に登録)

### 枠 1 追加 (期待 KILLED)

| ID | 位置 | 変異 |
|---|---|---|
| M6 | test-registry evaluator 側 catch | `except Exception` → `except RuntimeError` |
| M7 | test-registry normalize 側 catch | `except Exception` → `except RuntimeError` |
| M8 | 診断 helper の type 抽出 guard | `except BaseException` → `except SystemExit` |
| M9 | 診断 helper の reason 抽出 guard | `except BaseException` → `except (AttributeError, SystemExit)` |
| M10 | CLI 診断出力 guard | `except Exception` → `except OSError` |

### 枠 2 追加 (診断感度 pin)

| ID | 位置 | 変異 | 検出する assertion |
|---|---|---|---|
| D15 | `_DIAGNOSTIC_TEXT_MAX_LENGTH = 128` | `128` → `129` | literal 128/129 の境界 assertion と定数の直接固定 |
| D16 | CLI 診断出力 loop | `exception_type == "ValueError"` の診断だけ捨てる | `ValueError` の実 process CLI 負例 |

## fix の scope (これ以外を実装しない)

1. 128/129 の境界テストを literal 化し、`_DIAGNOSTIC_TEXT_MAX_LENGTH == 128` を直接固定する。
2. 次の 4 catch 地点の負例を、構造的に無関係な例外型で parametrize する
   (既に試している型に加えて 1 つ以上を足す。`PreregistrationError` は `RuntimeError` の subclass である点に注意)。
   - production evaluator 側 catch / production normalize 側 catch
   - test-registry evaluator 側 catch / test-registry normalize 側 catch
3. 診断 helper の 2 つの `except BaseException` に、`SystemExit` 以外の `BaseException`
   (例: `KeyboardInterrupt`) を送出する負例を足す。
4. CLI 診断出力の guard に、`OSError` 以外の例外を `write` が送出する負例を足す。
5. 既存の実 process CLI 負例を例外型で parametrize し、`ValueError` の場合も stdout bytes 不変と
   evaluator 側 callsite の exact stderr を固定する。

**scope 外 (実装しない):** production コードの挙動変更 (本 fix はテストの追加だけである)、
reason 語彙を閉じる変更、既存 CLI 終端の `str(exc)` 出力、新規 file、gate・検査・台帳・一般化の追加。

## 明示する限界 (段 7 へ記録する)

有限の例外型しか試さないテストは、**その型だけを列挙する catch 変異**に原理的に勝てない。
本 wave はその変異の実装コストを上げるだけであり、閉じたとは主張しない。
repo 内の挙動検査は、gate と検査を同じ主体が変更できる限り、意図的な弱体化への完全な防壁ではない (D387)。
