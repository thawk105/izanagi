# 段 6 fix 裁定 — レビュー R1 / R2 の所見

両レビューとも NO-GO。親が各所見を real/refuted と must-fix/nit に裁定する。

## 所見裁定表

| # | 出所 | 所見 | 裁定 | 対応 |
|---|---|---|---|---|
| 1 | R1-1 | M3 は calibration spy が確実に kill する (恒真説は不成立) | refuted | 変更なし。段 4 の再設計が効いた |
| 2 | R1-2 / R1-3 | M1・M2 は単独変異でも mask されず kill される | refuted | 変更なし |
| 3 | **R1-4** | **M4 (真の legacy 受理の正例) の証拠が恒真。既存 4 本はいずれも清浄な受理正例でない** | **real・must-fix** | **正例を 1 本追加する** |
| 4 | R1-5 | resume 正例の役割は正しい | refuted | 変更なし |
| 5 | R1-6 / R2-7 | 合成 2 世代 fixture は一貫し、xdist 汚染もない | refuted | 変更なし |
| 6 | R1-7 | 揮発 payload の焼き込みなし | refuted | 変更なし |
| 7 | R1-8 / R2-8 | `_receipt_expectations` の新 docstring は正直。ただし module 冒頭 docstring が stale | real (nit) | **採用** — 安いうえ正直さの問題 |
| 8 | **R2-1** | **report source bytes が変わると `generator_versions.report` pin が動き、live `run_block` の manifest 受理が反転する** | **real (事実)・must-fix ではない** | 記録する。下記 |
| 9 | R2-2 | `_receipt_expectations` の live 直接漏出はない | refuted | 変更なし |
| 10 | R2-3 | 受理集合の表現は「構文上の差分領域」と「実際に completed→protocol_violation になる条件」を区別すべき | real | 親の記録側で対応 |
| 11 | R2-4 / R2-5 | 既存テストの期待値改変・権限境界違反・禁止語はいずれも無し | refuted | 変更なし |
| 12 | R2-6 | 波及 inventory の報告漏れ (manifest generator-hash suite 等) | real | 親の受入全走で被覆。個別にも走らせる |

## 裁定 — R2-1 を land blocker にしない

R2 は「report 本体の byte hash が `generator_versions.report` に pin されており、
本 wave の編集で pin が `4b317080…` から `d60af42d…` へ動くため、旧 hash を記録した official
manifest が live `run_block` で拒否されるようになる。D202 の明示裁定まで land するな」と主張する。

事実は real である。しかし land blocker にはしない。

1. **これは source-byte pin の設計どおりの意味論**である。`generator_versions.report` は
   「この manifest はこの bytes の report で作られた」という byte identity であり、
   pin 対象ファイルを**どう編集しても**必ず動く。bug fix でも同じことが起きる。
   これを blocker にすると `s8b_oracle_report.py` を永久に編集できなくなる。
2. **発行済み official manifest は 0 件**である (親が裏取り済み、`docs/decisions.md` に既記録)。
   よって既存の certified 成果物の受理は 1 件も変わらない。
   受理述語は変わるが、その述語が適用される artifact が存在しない。
3. **D202 が守る境界とは別物**である。D202 は「履歴世代の解決が live 実走 admission の受理集合を
   広げてはならない」という境界であり、本件は世代解決とは無関係な生成器 bytes の同一性である。
   本 wave は live の**述語**を一切変えていない (R2-2 が refuted と判定したとおり)。

ただし R2 の指摘は台帳へ残す価値がある。worklog と insights に
「report source bytes 変更により `generator_versions.report` の pin 値が動く。発行済み manifest が
0 件のため既存受理は不変」と記録し、親は `test_s8b_oracle_manifest.py` を明示的に走らせる。

## fix の scope (fix 子へ投げる分)

1. **正例の追加 (R1-4、must-fix)。** `DW-M01` は受理集合を縮小する wave に
   「承認外の過剰拒否を検出する正例」の登録を義務づける。現状の M4 はその証拠にならない。
   public `build_observations` 経路で、`run_contract` を持たず
   `campaign-start.execution_receipt` も持たない完成 campaign を作り、
   全行 `completed`、resolver 未呼出し、calibration 未呼出しを固定する正例を 1 本追加する。
2. **module docstring の訂正 (nit だが採用)。** `s8b_oracle_report.py:8-11` を
   「session identity 層」と「receipt expectation 層」に分け、後者の新しい拒否を書く。

fix 子の所有ファイルは段 5 と同じ 3 ファイル。production の受理述語を変えてはならない。

## 変異事前登録の更新 (`DW-M01`)

M4 を差し替える。

| ID | 対象 | 変異内容 | 期待 |
|---|---|---|---|
| M4' | `_receipt_expectations` の `if not isinstance(run_contract, Mapping): return None` | `return None` を削除し field 不在でも identity 検査へ落とす (過剰拒否へ倒す変異) | **KILLED** — 新設した真の legacy 正例が赤になる |

M1・M2・M3・M5 は段 4 の登録どおり。
