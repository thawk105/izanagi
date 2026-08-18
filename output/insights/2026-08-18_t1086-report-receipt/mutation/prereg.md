# 変異事前登録 v2 (段 6、fix 後に走らせる) — [T-1086]

段 4 の登録を、段 6 敵対レビュー 2 本の所見で訂正した版。これが変異 matrix の正本。

## 全登録に共通する期待 (F226)

`s8b_oracle_report.py` / `s8b_oracle_judge.py` を変異させる登録は、source hash pin により
**必ず**次の 2 件も赤にする。期待 node 集合にこれらを常に含める。

- `orchestrator/tests/test_s8b_oracle_manifest.py::test_build_approved_valid_fixture_output_depends_only_on_spec_pin`
- `orchestrator/tests/test_s8b_oracle_manifest.py::test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal`

「この変異は source hash を変えるか」= M1〜M10 のすべてで **Yes** (両 file が対象のため)。

## 登録一覧

| # | 変異 | 期待 node (上記 pin 2 件に加えて) | 訂正の有無 |
|---|---|---|---|
| M1 | `s8b_oracle_report.main()` の official 分岐で `reverified_freeze=` の受け渡しを削り、wave 前の「reverified を捨てる」形へ戻す | 段 4 の裁定どおり A-7 の CLI baseline (実 store root で receipt の exact content を検査するもの) | 段 4 で killer 差し替え済み |
| M2 | receipt helper で `expected_sha256 = actual_sha256` にする | `test_v2_post_run_store_change_is_reported_and_refused[replaced]` | — |
| M3 | store を読まず `actual_sha256 = expected_sha256` にする | 同上 | — |
| M4 | OSError 分岐を `state="match", actual=expected` にする | `test_v2_post_run_store_change_is_reported_and_refused[removed]` | — |
| M5 | outer 判定を `all(...)` から `any(...)` へ | `[replaced]` と `[removed]` の両方 | — |
| ~~M6 (旧)~~ | ~~judge validator が receipt 欠落時に `[]` を返す~~ | — | **取り下げ**: 欠落は validator 呼び出し**前**の caller 分岐 (`s8b_oracle_judge.py:607-611`) で処理されるため、validator 側の変異では指定 node を殺せない (RB-2) |
| M6' | `s8b_oracle_judge.py` の **caller 側**の receipt 欠落分岐を削除する | `test_official_store_reverification_absence_is_indeterminate` | **再照準 (RB-2)** |
| ~~M7~~ | ~~aggregation gate から store reasons を外す~~ | — | **取り下げ済み (段 4、A-8)**: `unknown = bool(top_reasons)` により受理集合が変わらない |
| M8 | judge の cell exact 検査を `set(entry) >= required_keys` へ緩める | `test_store_reverification_requires_exact_keys[cell-extra]` | — |
| M9 | judge の receipt cell 集合 equality を subset 判定へ緩める | `test_store_reverification_rejects_receipt_cell_outside_schedule` | — |
| ~~M10 (旧)~~ | ~~resolver の `relative_to(output_root)` containment を削る~~ | — | **取り下げ**: 親 symlink は `:1876`、leaf symlink は `:1905` の `lstat` 検査が先に拒否するため等価変異 (RA-2 / RB-1 が独立に一致) |
| M10' | **両層同時変異**: containment (`relative_to`) と、親 component / leaf の symlink 拒否を**同時に**削る | `test_store_reverification_rejects_out_of_root_symlink[parent]` と `[leaf]` | **両層同時変異へ差し替え (DW-M04)** |
| M11 | `_resolve_store_path` の字句検査 (絶対 path / `..` / backslash / 制御文字) を削る | `test_store_reverification_rejects_out_of_root_store_path[absolute]`, `[parent]`, `[control]`, `[backslash]` | 新規 (字句層の単独検出力を明示) |
| M12 | `O_NOFOLLOW` を両方削る | 段 6 fix [F-2] で追加する競合対照 2 本 | 新規 (RA-1 の防御が発火することの証明) |
| M13 | output_root 不在を `missing` でなく `ReportError` に戻す | 段 6 fix [F-1] で追加する対照 1 本 | 新規 ([F-1] の回帰検出) |

## 単一理由性の確認 (DW-M01)

- M2〜M5、M8、M9 は、同じ入力を拒否する層が前後に無いことをレビュー B が静的に確認した
  (「M1〜M5、M8、M9 は現在の実装位置へ正しく注入すれば指定 nodeid が機能差を直接検出する」)。
- M6'、M10'、M11〜M13 は本 wave で新設・再照準したため、**変異走行の結果で単一理由性を裏取りする**。
  SURVIVED が出たら DW-M02 に従い他層の mask と等価変異をまず疑う。
- 全登録で pin 2 件が同時に赤になるのは**先取りではなく併発**である (F226 の記録どおり)。
  pin 2 件だけが赤で指定 node が緑なら、その変異は **KILLED と数えない**。
