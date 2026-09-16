# [T-2651] 段 4 裁定 — 所見の real/refuted、変異事前登録 v2、plan v2

裁定時点の local main = d97c423bdd14e0b416cb4f585d350e6c2b251287 (wave 開始時から不動)。
裁定 inbox (`docs/spool/`) を段 4 直前に再走査した。wave 開始後の新規裁定はない。

## 0. 総論

**実装の must-fix はゼロである。** レンズ 2 本 (sol = 正しさ境界と受理集合、
luna = 証拠の復元可能性と byte 予算) はいずれも、着地実装が受理集合を広げる反例・
fail-closed を fail-open へ倒す到達可能な経路を**確認できなかった**と報告した。
両者とも根拠の種別を「読解」と明記しており、実走による証明ではない。

したがって所見の本体は**記録精度**に集中する — この機構が何を証明し、何を証明しないか。
以下、所見ごとに real/refuted と採否を裁定する。

## 1. 実装への所見 (sol)

| # | 所見 | 裁定 | 採否 |
|---|---|---|---|
| S1 | 通常の発行経路で受理集合を広げる反例なし。admission は整形前に確定し、整形は `not admission.admitted` 枝だけで動く | **real** (読解) | 採用。brief の不変条件を裏付ける |
| S2 | 属性失敗・非 dict・二重の非 green 判定の攻撃は、現行の発行型契約で大部分が排除される | **real** (読解) | 採用 |
| S3 | 「non-green はすべて拒否本文へ入る」は誤り。`supply=green / meaning=unestablished` は admission が受理する | **real** (読解) | 採用 (記録のみ)。gate 本体の変更要求ではない |
| S4 | `BaseException` 非捕捉のため、整形器が `SystemExit(0)` を送出すれば rc=0 で抜けうる。「rc 不変」を無条件保証として書けない | **real** (読解) | 採用 (記録のみ)。明示契約の帰結であり実装欠陥ではない。実際に `SystemExit(0)` を生成する経路は未発見 |
| N1 (sol) | 短文 surrogate は byte 判定で escape されるが返却値に残る | **real・nit** | nit のまま。成果物影響を確定できない |
| N2 (sol) | `test:345-361` は green 時に helper を呼ばないことの直接検査ではない | **real・nit** | nit のまま。検査の射程の注記 |

**実装差分ゼロを維持する。** brief (P3) の方針どおり、段 5 の Codex 実装子は起こさない。

## 2. 機構の実効性への所見 (luna)

| # | 所見 | 裁定 | 採否 |
|---|---|---|---|
| E1 | 上流 gate (`condition_meaning_gate.py:1563-1576` ほか) が既に stderr を末尾 500 bytes へ切っている。driver が保持するのは**加工済み `evidence.detail` の全文**であって raw subprocess 出力の全文ではない | **real** (読解 + 保存ログ照合) | 採用。**記録上の要訂正**。前 wave commit message の「実 rc と実 stderr が復元できた」は、この区別を付けずに書かれている |
| E2 | `sha256=` は照合用であり、省略した中央本文の復元には使えない。digest の対象は `shlex.join([detail]).encode("utf-8", errors="backslashreplace")` であって raw stderr でも raw argv でもない | **real** (読解) | 採用。材料レポートで「全文 sha256 があるので復元できる」と書かない |
| B1 | `1057 * 4` の 4228 bytes は 1 回の観測に由来する余裕であって、重要行が残る保証ではない。重要行が中央へ入る確率は**評価不能** | **real** (読解) | 採用 (記録のみ)。予算の変更は scope 外 |
| B2 | 拒否本文**全体**に上限はない。構造上限は 4 request × 2 arm = 8 record、detail 合計で最大 33,824 bytes | **real** (読解) | 採用。具体値を記録へ書く |
| B3 | 重複 slice・`[-0:]` 全文返し・`available` 非正は、現行定数では到達不能 | **real** (読解) | 採用。**実装 must-fix なし**の根拠 |
| B4 | `omitted` の会計は変換後 bytes に対して整合する。raw stderr の会計ではない | **real** (読解) | 採用 |
| N1 (luna) | 切り詰め結果は shell token として可逆でない | **real・nit** | nit。shell token として解析する production consumer は未確認 |
| N2 (luna) | 短文に digest が無いのは仕様どおり | **real・nit** | nit |

## 3. 親 brief への所見

| # | 所見 | 裁定 | 是正 |
|---|---|---|---|
| B1 (sol) | 完了条件の「全件 KILLED」は、契約上の kill と harness の分類を混同する | **real・採用** | **plan v2 で完了判定を改める** (下記 §5) |
| B2 (sol) | runner を単独 file へ絞った結果を、正しさ防壁全体の保証へ拡張できない | **real・採用** | 記録の保証範囲を限定して書く |
| B3 (sol) | masking の記述は読解と実測、存在と網羅を分ける必要がある。「任意の変異が必ず同じ hash 理由で赤」は強すぎる (構文を壊す変異なら hash 検査へ到達する前に停止しうる) | **real・採用** | brief の当該記述を「読解による存在の同定であり、網羅性の証明ではない」と限定する |
| P1 (luna) | この wave は official 床値取得を直接前進させない。価値は間接的 (診断の信頼性についての残件を閉じる) | **real・採用** | **研究前進の書き方を訂正する** (下記 §5) |
| P2 (luna) | 6 変異の検出は証拠復元可能性の十分条件ではない | **real・採用** | 記録に明記 |
| 未被覆 6 件 (luna) | raw 証拠からの全文保存、中央重要行の復元、4228/4229 の厳密境界、長文を複数 record へ接続する経路、digest **値**改変の検出力、surrogate と引用境界 | **real・観察として採用** | **登録は追加しない** (ユーザーが scope 外と明示)。観察として記録し、必要なら別 wave の材料にする |

## 4. 前 wave の記録への所見 (luna W1) — 追記 erratum を出す

**real・採用。** 前 wave の insight
`output/insights/2026-09-15/t1851-c3c-official-floor-run/README.md` §7 の
「3 回の実機走行で M1〜M3 と M5〜M7 が守る性質を production 経路で直接観測した ―
1 回目は detail なし、2 回目は先頭のみ、3 回目は先頭と末尾の両方が残り、
**いずれも全文 sha256 の印つきだった**」は不正確である。

保存ログの照合で分かったこと。

- 1 回目 (`998882`) の保存拒否本文に digest は無い。
- 3 回目 (`999102`) の digest は **argv の引用整形後全文**に対するもので、
  本 wave が検査している外側の detail digest ではない。
- M2 (複数 non-green 全件掲載)、M3 (整形例外時の拒否保持)、M5/M6 (外側の両端切り詰め) は
  いずれも 3 走行で**発火していない**。掲載された拒否 record は
  `BACKOFF_FIXED:supply-effectuation:preprocess-failed` 1 件だけである。

**絶対規律 7 に従い、過去の判定は追記でのみ訂正する。** 前 wave の本文は書き換えず、
同 README の末尾へ追記の erratum を置き、本 wave の insight からも参照する。
§7 が自ら「harness による kill 判定の代替ではない」と書いている点は正しく、その部分は訂正しない。

## 5. plan v2 — brief の 2 点を訂正する

1. **研究前進** — 「official 床値 campaign を前進させる」ではなく、
   「official 床値 campaign が依存する診断機構について、レビューと変異検証の残件を閉じる。
   床値そのものの取得は `config.h` 供給 blocker (T-2650) が解けるまで進まない」と改める。
2. **完了判定 (b)** — 「M1-M3 / M5-M7 が期待 node 完全一致で KILLED」を
   「M1-M3 / M5-M7 が期待 node 完全一致で**検出され**、`DW-M03` / `DW-M08` に従って
   kill と diagnostic sensitivity pin の別に**分類記録される**」と改める。

## 6. 変異事前登録 v2 (`DW-M01`)

段 1 の実測で anchor 6 件すべての一致数が 1 であることを確認した (行番号は plan と一致:
M1/M2=341、M3=352、M5=291、M6=290、M7=283)。**M4 は取り下げのまま復活させない。**

### 6.1 runner の対象集合 (P1 確定)

`orchestrator/tests/test_s1_direct_comparison.py` **単独**とする。
`orchestrator/tests/test_s8b_oracle_manifest.py:88-89` は `s1_direct_comparison.py` の
live byte sha256 を golden 逐語で pin しており、同 file への変異を一律に赤にする。
`DW-M03` の「過剰決定なら冗長 gate と明記して単独変異の証拠から外す」に従い除外する。
**この除外は当該テストを無効化するものではない** — 受入全走では通常どおり走る。

sol B3 に従い、この除外理由は**読解による存在の同定**であって
「repo 全体に masking が他に無いこと」の証明ではないと明記する。

### 6.2 kill と diagnostic sensitivity pin の分類 (親裁定)

`DW-M03` 逐語「kill は受理集合か fail-closed 挙動が期待方向へ変わったときだけ数え、
診断文字列だけの赤を kill にしない」および `DW-M08` 逐語「受理集合を変えず構造化シグナルだけを
pin する変異は kill でなく diagnostic sensitivity pin へ別枠記録する」に照らす。

**6 変異すべてを diagnostic sensitivity pin に分類する。kill は 0 件である。**

- M1 / M2 / M5 / M6 / M7 — 受理集合も終端 rc も変わらず、観測差は診断の内容だけ。
- **M3 も同じ** — 親が消費側を自分で読んで裏取りした。M3 を当てると整形器の `RuntimeError` が
  `DriverError` を置換して `_condition_records_for_genome` を抜けるが、消費側
  (`s1_direct_comparison.py:1320-1327`) は `except DriverError: raise` に続けて
  `except Exception` を持ち、`_is_transient_prepare_failure()` が `RuntimeError` に対して
  `False` を返すため再送出する。`main()` (同 1409-1415) は `EXIT_REFUSED` を返す。
  **終端 rc は変わらない。** M3 が同時に pin しているのは「拒否が `DriverError` として届き、
  retry 分類器を迂回する」という構造的性質であり、その性質が終端挙動を変える入力
  (整形器が `OSError` 族を送出し、かつ session 未開始) は現行実装では到達不能である (読解)。

**これは失敗ではない。** 着地 commit が主張した「gate の受理集合・reason code 語彙・
admission 判定・rc・green 経路の bytes は変えていない」が、変異の側からも裏付けられたということである。
`DW-M02` に従い、所見ゼロを変異なしで緑と数えないという要求は、6 変異の検出実測で満たす。

### 6.3 単一理由性の注記 (`DW-M01` / sol・luna 共通所見)

- **M1** は本文保持と、注入した割込みの伝播検査の**両方**を同時に壊す。
  「本文保持だけを壊す」という厳密な説明には収まらない。期待 node にはその両方が含まれる。
- **M7** の 4 node は 4 性質の独立証明ではない。`omitted` node は算術比較より前の
  正規表現一致で止まるため、「省略数の誤りも検出した」とは数えない。
- **M2** の fixture は両 arm が同じ `compiler-failed`・同じ detail であり、
  arm 間で detail を取り違える欠陥はこの fixture では識別できない。
- **M5 / M6** は `omitted` が残存量から再計算されるため、計数・digest・予算まで
  独立に壊すとは数えない。

### 6.4 走行方式

plan の推奨どおり **probe → 本走の 2 段構成**とする。期待 node は静的予測であり、
日本語 param の pytest ID 表記を決める設定が plan の射影外だったため、
`DW-M07`「KILLED 期待で node 空の spec は起動前に中止するので probe は全件 SURVIVED で
登録し観測 node を集める」に従う。probe の初回結果は消さず erratum として残す。

## 7. scope 外として実装しない real 所見

次はいずれも real だが、ユーザーが明示的に scope 外と裁定しているため実装しない。
設計択一として裁定パッケージへ送る候補であり、本 wave では観察として記録するだけとする。

- 上流 `condition_meaning_gate` の 500 bytes 切り詰めによる raw stderr 前半の喪失 (luna E1)
- 兄弟 driver 14 箇所への同型修正の横展開 (段 1 で同定、前 wave が非展開と裁定済み)
- 未被覆 6 性質に対する変異・検査の新設 (luna)
- `_CONDITION_DETAIL_LIMIT_BYTES` の母集合に基づく再設計 (luna B1)
