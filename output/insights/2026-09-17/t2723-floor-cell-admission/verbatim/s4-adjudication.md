# 段 4 裁定 — [T-2723] floor セル読取経路を §5 の admission 契約へ接続する

基準: local main 1042a1bc9 (段 4 直前に再確認、HEAD..main = 0 commit、T-2723 に触れる新裁定なし)。
入力: s1-brief.md、s2-plan.md (受理 rc=0)、s3-a.md (レンズ A 正しさ境界)、s3-b.md (レンズ B 整合・consumer)、親 probe (parent-probe-before.txt)。

## 1. 所見の裁定 (real / refuted、採用 / 不採用、scope 内 / 外)

### レンズ A
- A1 NFKC 後で sentinel を比べると `未記⼊` (末尾 U+2F0A) が拒否→None へ変わる — **real・採用・scope 内**。sentinel 比較は **strip 後 raw** (`raw_values[FLOOR_LABEL] == "未記入"`) に掛ける。NFKC は label 正規化と cell の default-ignorable 拒否にだけ効く。負例 test 12 と変異 M10 を追加。
- A2 §5 外の同 prefix 行の無視は strip と独立の「拒否→受理」 — **real・採用 (説明の訂正)**。これは依頼が名指す境界修正そのもの。brief の不変条件「縮小 + strip だけ」を撤回し、§3 の列挙契約へ置き換える。
- A3 / A4 / A5 共有 parser の全条件 (見出し一意性・12 行・header・両端 `|`・2 セル・label 集合・全セルの default-ignorable 拒否)、path 中の `|`、fence / comment 内だけの floor 行、literal `<!--` の過剰拒否、strip の射程 — **real・採用 (説明)**。受理→拒否の差分として insight に列挙する。規律 2 の緩和ではない。コード変更なし。
- A6 P5 (utf-8-sig) 単独の拡大 — **refuted**。旧経路も BOM 付きを decode できた。P5 を緩和に数えない。
- A7 真正 §5 の見出しが保たれる限り floor 行の破損 + 外側複製は閉じる — **refuted (攻撃不成立)**。変更不要。
- A8 両見出しを軽微に壊し別所へ canonical §5 を置く F423 型は残る — **real・scope 外**。admission 契約自身の既知限界 (見出し探索は raw exact 一致の文書全体走査)。insight と worklog fragment に残存限界として明記。新 gate は足さない (依頼の scope 外指定、DW-G05)。
- A9 fence / comment / インデントの扱いの説明 — **real・採用 (docstring の正確化)**。
- A10 P3 の述語は 5 例で同一受理集合 — **refuted (問題なし)**。brief の「責任者未指名を拒否」は「責任者セルが既存 admission 述語に違反する場合を拒否」へ狭める (`hello` は両方受理、D2079 決定 2)。
- A11 loader へは strip 後 raw の path/hash を渡す — **real・採用** (plan と同じ)。
- A12 docstring は正規化の実順序・absence の前提・完全 admission を証明しない旨を書く — **real・採用**。
- A13 他欄が `未記入` でも有効 pin なら floor が present になる残存 — **real・scope 外 (既存仕様、本 wave の緩和ではない)**。完了主張を「floor セルの読取を §5 固定表 + 責任者行述語へ接続した」に限定する。
- A14 M1 は decoy test でも `exact 1` で赤になり専属 killer でない — **real・採用**。harness の KILLED は失敗集合の完全一致契約なので、期待 node は probe 走で実測して固定する (全変異共通)。
- A15 M0〜M9 の机上帰属 — plausible。probe 走で確定。
- A16 「6 欄」「pin 0 件」「record 0 件」— **refuted (反証なし)**。P4 の結論は「現行 tracked の登録対象について失効処理不要」に限定。
- A17 brief と plan の「strip 以外の緩和を防ぐ」文 — **real・採用**。§3 の列挙契約で置換。

### レンズ B
- B1 consumer 一覧に `test_p3_b4_material_report.py:1065` (`test_present_floor_projects_required_verbatim_non_guarantees`) を追加 — **real・採用 (nit)**。
- B2 literal 参照 3 test file は焦点追加不要 — **real・採用 (記録のみ)**。
- B3 共通 fixture の利用箇所 (m9 `:867`、non-guarantees 正例 `:1064`)、`test_p3_b4_analysis_path.py:574` は無関係 — **real・採用**。最小文書を一律に完全表へ変えない。
- B4 m05/m06 は fixture が壊れていても `pytest.raises(B4FloorArtifactError)` だけで緑になる — **real・採用**。各 mode の期待 error code を固定 (missing → `load_authoritative_floor` 側の code、hash → 同、schema → 同。現物の code 名は author が実装時に `load_authoritative_floor` から読み取り、`preregistration_floor_row_error` では通らないことを assert)。
- B5 cross-test import の破綻懸念 — **refuted**。`from orchestrator.tests.test_p3_b4_admission_record import _section5_document` を関数内 import で使う。
- B6 / B7 例外送出順序は test で観測不能 — **real / refuted**。順序は差分レビューで維持、test は観測可能な契約だけ。
- B8 / B9 P4・固定 golden — **refuted / real・採用**。固定 golden (`test_m8_absent_authority_public_bytes_match_pre_change_golden` 等) は更新しない。
- B10 実 repo 直読 test の real-repo 分類登録 — **real だが不採用 (P7)**。根拠: (i) 先例 `test_p3_b4_analysis_prereg_consumer.py:23,59` は実文書を直読して未登録・marker 無し、(ii) access map で親 working tree への access は全 node が `read` で writer は存在せず、登録は shared lock と xdist group 付与だけで正しさに効かない、(iii) 分類監査 (`test_real_repo_serialization.py`) は TMPDIR literal を AST 走査するだけで、実 repo 読取を機械検出しない、(iv) 依頼が「仮想リスク向けの台帳追加は scope 外」と定める。conftest / golden 2 file は触らない。受入全走で `test_real_repo_serialization.py` / `test_acceptance_schedule_order.py` が赤になれば新事実として再裁定する。
- B11 実文書 None 期待は floor 登録で壊れる — **plausible・採用 (説明)**。test docstring に「現在の未登録状態の回帰。floor 登録 wave で更新する」と書く。
- B12 M4 が複合 — **real・採用**。M4 は helper の `.strip()` 除去だけの単一変異にする。
- B13 killer 帰属の記録 — **plausible・採用**。matrix の期待 node は probe 実測で固定。
- B14 M0 — refuted。等価変異の SURVIVED を欠陥と数えない。
- B15 / B16 brief の不変条件・責任者の説明 — **real・採用**。§3 へ。
- B17 P6 の見積り — plausible。author 1 本は維持。scope は 3 module (admission / floor issuer / material report docstring) + test 3 file (floor issuer / material report fixture / admission 小追加)。conftest・golden は触らない。
- B18 label pin は index でなく独立 literal + 集合所属で — **real・採用**。material report の docstring (`:6` 「verbatim sentinel」) を更新対象へ追加。事前登録 §7.2 は変更不要。

## 2. plan v2 (author への確定指示)

1. `orchestrator/campaign/p3_b4_admission_record.py`
   - 602〜701 の本体を 2 helper へ切り出す: `_parse_section5_fixed_table_source_cells(document_blob: bytes)` (617〜666 をそのまま移す。戻りは normalized label → normalized value / strip 済み raw value / strip 前 label の 3 系列。小さな frozen dataclass か 3-tuple。`cells[0]` の保存以外に条件・順序を変えない) と `_assert_section5_source_cell_has_nonempty_value_and_no_reserved_sentinel(label, value)` (668〜686 の for 本体。`continue` → `return`)。
   - 既存関数は helper を呼び、687〜701 (expectation 行の raw / normalized 二重 grammar 検査と期待値照合) はそのまま残す。**例外型・message bytes・`from exc`・処理順は不変。**
   - module docstring 27〜30 行: 「完全な admission 検査」であることを明確化し、floor 読取が固定表解析と責任者行述語を共有するが他セルの sentinel と expectation 宣言は検証しない旨を 1〜2 文で足す。31〜36 行は残す。
2. `orchestrator/campaign/p3_b4_floor_artifact_issuer.py`
   - `_floor_cell(raw: bytes) -> str` (strip 済み raw の floor cell を返す)。共有 helper を呼び、`B4AdmissionRecordError` は `__cause__` が `UnicodeError` なら `preregistration_encoding_error`、それ以外は `preregistration_floor_row_error` (detail に helper の message) へ写す。floor 行の strip 前 label が `PREREGISTRATION_FLOOR_LABEL` と exact 一致しなければ `preregistration_floor_row_error`。責任者行 (`実行責任者・開始時刻`) の normalized value に 1 セル述語を掛け、違反は `preregistration_floor_row_error` (detail に「§5 実行責任者・開始時刻: …」)。**責任者検査は sentinel による None 返却より先。**
   - `resolve_preregistered_authoritative_floor`: `raw_cell == PREREGISTRATION_ABSENT_SENTINEL` (strip 後 raw、NFKC なし) なら None。それ以外は `_FLOOR_PIN_RE.fullmatch(raw_cell)`、既存の grammar error、`_relative_path`、`load_authoritative_floor` は不変。docstring 1489 行の「verbatim sentinel」を、共有する §5 契約 (境界・形状・label 集合・cell 正規化・責任者行述語)、strip 後 raw の sentinel、raw pin grammar、他欄の sentinel と expectation は検査しない (完全 admission の成立を証明しない) に書き換える。
   - 新 error code は作らない。`main()` は不変。
3. `orchestrator/campaign/p3_b4_material_report.py`: module docstring 5〜7 行の「verbatim sentinel」を新しい受理集合 (§5 固定表の floor セル、strip 後 raw の sentinel) に合わせて更新。コードは不変。
4. `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py`
   - `_preregistration(value)` を `_section5_document` (関数内 import) の wrapper にする: floor = `value`、責任者 = `実行責任者 = fixture-owner、開始時刻 = 未記入` (D2079 形)、他欄は builder 既定値のままでよい。終端 `### 5.1` は builder が持つ。
   - 期待値変更: `test_resolver_exact_sentinel_is_the_only_absence` の ` 未記入` / `未記入 ` は None 期待へ (strip)、`TBD` / `artifact_path=x` は grammar error のまま。`test_resolver_rejects_duplicate_floor_rows` は完全表の別 label 行を floor label へ置換して 12 行のまま重複させ、`preregistration_floor_row_error` を検証 (`match="exact 1"` を外す)。m05/m06 は mode ごとの期待 code を固定 (B4)。
   - 新規 test (すべて subprocess 無し、tmp_path 上の小さな doc): (1) 実 repo 文書 (`Path(__file__).resolve().parents[2]`) → None [現在の未登録状態の回帰と docstring に明記]、(2) §5 は sentinel + `### 5.1` 以降に有効 pin 行 → None かつ loader 未呼出 (monkeypatch で観測)、(3) §5 の floor 行を削って 9 行 + 外側に有効 pin → row error・loader 未呼出、(4) 完全表 + 有効 pin、責任者 `実行責任者 = 未記入、開始時刻 = 未記入` → row error・loader 未呼出、(5) 責任者行欠落 + 有効 pin → row error、(6) fence 内 / HTML comment 内に偽 §5 完全表 + pin、真正 §5 は sentinel → 両方 None、(7) `PREREGISTRATION_FLOOR_LABEL` が独立 literal と一致し `_SECTION5_LABELS` に含まれる、(8) padded pin は strip されて loader へ exact path/hash が渡る、`artifacts/Ａ.json` は raw のまま渡る (NFKC されない)、(9) floor label の外周空白 / 全角化 → row error、(10) 無関係 1 label を未知 label へ置換 (行数維持) → row error、(11) 不正 UTF-8 → `preregistration_encoding_error`、先頭 BOM 付き完全表 → 通常結果、(12) `未記⼊` (末尾 U+2F0A) → `preregistration_floor_grammar_error` (None にならない)。
   - 有効 pin は既存の `_synthetic_source` + `issue_authoritative_floor` で作る (依存先を stub しない)。loader 未呼出の観測だけ monkeypatch でよい。
5. `orchestrator/tests/test_p3_b4_material_report.py`: `_write_floor_preregistration` (137〜142)、aggregate 正例 (1004〜1008)、m7 (1113〜1119) の単一行書込みを `_section5_document` wrapper の完全表へ。**新規 test 関数を足さない** (全 node が `test_real_repo_serialization._P3_B4_MATERIAL_REPORT_NODES_GOLDEN` に列挙されている)。既存の期待値は変えない。
6. `orchestrator/tests/test_p3_b4_admission_record.py`: helper の raw / normalized 二系列を区別する小さな test を 1 件足す (NFKC でだけ一致する入力で `raw_values` と `values` が異なる)。既存 test の期待値は変えない。
7. conftest / `test_real_repo_serialization.py` / 事前登録文書 / `docs/phase3.md` は触らない (docs は親が段 7 で扱う)。

## 3. 受理集合の契約 (brief の不変条件を置換)

floor 読取経路の受理集合の変化は次の列挙どおりで、これ以外は認めない。
- 拒否→受理 (2 系統): (a) §5 固定表の floor 値セルの外周空白 (strip、admission と同一)、(b) 真正 §5 の外にある同 prefix 行の存在 (fence / HTML comment 内を含む) は無視される。
- 受理→拒否: 共有 parser の全条件 (`## 5.`〜`### 5.1` の一意な見出し境界、区間内の fence / comment 無し、12 非空行、exact header、各行の両端 `|` と 2 セル、正規化後 label の重複なし・10 label 集合と一致、全 label / 値セルの default-ignorable・Cf 拒否)、floor label の strip 前 exact 一致、責任者行の既存 admission 述語 (D2079 の 1 形 + 一般 sentinel 規則)、path 中の ASCII `|`。
- 不変: sentinel は strip 後 raw の `未記入` だけ、pin grammar は strip 後 raw、loader へ渡す path / hash は raw、他欄の sentinel と expectation 行は検査しない (現行文書 = 6 欄 `未記入` で None、材料レポートの legacy 経路不変)。
- admission 関数自身の受理集合・error signature は不変。

## 4. 変異 matrix の事前登録 (実装前に登録、single-site、hang_risk なし)

runner 焦点 = `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py orchestrator/tests/test_p3_b4_admission_record.py orchestrator/tests/test_p3_b4_material_report.py`。期待 node は probe 走 (全件 SURVIVED 登録) で実測して本走 spec に固定する。A = admission module、F = floor issuer。

| ID | category | 対象 | 変異 | 想定 killer (probe で確定) |
|---|---|---|---|---|
| M0 | positive (等価) | A docstring | comment 1 行追加 | SURVIVED 期待 |
| M1 | negative | F `_floor_cell` | 共有解析を捨て、文書全体の `|<label>|` prefix 走査で 1 行を選ぶ旧挙動へ戻す (bytes→str decode を含む実行可能 patch) | (2) outside-pin、(6) decoy、(3)/(5)/(10) 等 |
| M2 | negative | F `_floor_cell` | 責任者行への述語呼び出しを削除 | (4)、(5) は parser で落ちるので別 |
| M3 | negative | A helper | label 集合一致検査 (`set(values) != set(_SECTION5_LABELS)`) を削除 | (10)、admission 側 test |
| M4 | negative | A helper | `cell.strip()` を `cell` に (strip 除去) | padded sentinel (`test_resolver_exact_sentinel_is_the_only_absence`)、(8)、admission 側 |
| M5 | negative | A helper | `raw_values[label] = value` (normalized を raw 系列へ格納) | admission `test_section5_expectation_row_rejects_nfkc_only_ascii_grammar_matches`、(8)、新 admission test |
| M6 | negative | A `_markdown_block_context` 利用箇所 | 境界探索と区間検査から fence 除外を外す | (6) fence、admission fence test |
| M7 | negative | A 同 | HTML comment 除外を外す | (6) comment、admission comment test |
| M8 | negative | F resolver | `_FLOOR_PIN_RE.fullmatch` と loader へ normalized 値を渡す | (8) |
| M9 | negative | F `_floor_cell` | floor label の strip 前 exact 一致検査を削除 | (9) |
| M10 | negative | F resolver | sentinel 比較を normalized 値に掛ける | (12) |
| M11 | negative (過剰拒否の正例、DW-M01) | F `_floor_cell` | 述語を責任者行だけでなく全 label に掛ける | (1) 実文書、`_preregistration` 利用 test 群、material report 正例 |

M6 / M7 は既存 admission test も killer になりうる (専属性不成立を記録、SURVIVED と扱わない)。

## 5. 残存限界 (scope 外、記録のみ)
- 見出し decoy (両見出しを壊して別所へ canonical §5) は admission 契約自身の既知限界 (F423 既知の残存と同型)。
- 他欄が `未記入` のまま有効 pin を置けば floor は present になる (既存仕様)。完了主張は「floor セルの読取を §5 固定表 + 責任者行述語へ接続した」に限定。
- 実文書の None 期待は現在の未登録状態の回帰であり、floor 登録 wave で更新する。
