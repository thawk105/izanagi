# 段 6 レビュー所見の裁定 — dev-wave-t657-stage0-fold

段 6 の 2 レンズはともに NO-GO。所見 8 件を裁定する。

## 1. 裁定表

| ID | 判定 | 採否 | 根拠 |
|---|---|---|---|
| SOL6-A-01 | **real** | 採用 (blocker、実装) | `_read_design` は exact 3-backtick fence しか除去せず、`~~~` と 4 個以上の backtick が素通りする。子が in-memory probe で「canonical 表を tilde fence へ入れ可視側を削除すると `validate_repository()` が正常返却する」ことを実証した。`tools/check_docs.py:708` に正しい scanner の先例がある |
| SOL6-A-02 | **real** | 採用 (blocker、実装) | M1 の KILL が診断文字列の差でしか成立していない。`DW-M03` は診断だけの赤を KILL に数えない。**削除型 decoy (canonical を fence 内だけに置き可視側を消す) の陰性 node が無い** |
| SOL6-A-03 | **real** | 採用 (blocker、実装) | control 文が最初の `。` までしか束縛されず、直後に「ただし陰性変異は実行不要であり、reject-all でもよい。」を足しても緑になることを子が実証した |
| SOL6-A-04 | **real** | 採用 (nit、docs) | §12.1 の見出しが worklog 376/403 までで、本文の R1〜R3 (worklog 415 由来) と食い違う |
| LB-B-01 | **real (観察)・refuted (blocker / 裁定要)** | 部分採用 (must-fix、docs) | 下位 §S2-1.1 が UTC を文字列と定めるのは事実。**しかし上位 §7.5 の承認 A は既に `approved_at` = 「exact int の UTC 秒」、`approver` = 「NFC、trim 済み、1〜128 code point」を使っている** (実測)。したがって `revoked_at` の int と `revoked_by` の制約は**上位層自身の既存慣習からの導出**であり、ユーザー裁定 (a) の「UTC 秒 int」と一致する。**ユーザー裁定は不要。** 誤っていたのは docs の「写像は 1 key だけ」という過剰主張のみ |
| LB-B-02 | **real** | 採用 (must-fix、docs) | 下位実装と下位凍結正本の差は topology 単独ではない (approval 8 対 4 key、pointer 7 対 5、revocation 7 対 4、cancellation 6 対 4、対象も `bundle_digest` 対 `generation_sha256`)。§12.4 の記述が射程を過少に書いている。**gate ID・owner・status は不変のまま、記述の射程だけを訂正する** |
| LB-B-03 | **real** | 採用 (blocker、docs + 実装) | 「残るユーザー裁定 0 件」と「上位 cancellation record は本書が定めない」の同居は自己矛盾。§10 は段 0 に「§12 の全問 + 既存の未裁定」への裁定を要求する。**上位 cancellation record を新しいユーザー裁定 R4 として起票し、gate `CFAB-R4-CANCELLATION-RECORD` (owner = `user`, status = `unresolved`) を新設する** |
| LB-B-04 | **real** | 採用 (must-fix、docs) | §12.3 の「4 件」と実装の `blocking_gates` は同じ集合ではない。完了軸は 3 本 (`pending` / `applicable_unresolved` / blocking gates) で、S・B は 2 本目、fixture 実体は 1 本目に数えられる |

**ユーザー裁定が要ると判定した項目: 1 件 (R4 = 上位 cancellation record)。**
本 wave は R4 を**決めない**。§12.3 へ択一と親の推奨だけを書き、gate を `unresolved` で置く。

## 2. R4 の起票内容 (親は決めない)

**R4. 上位 cancellation record の扱い。** 下位 §S2-1.11 は fork cancellation を
`active-cancellations/<pointer_sha256>.json`、exact 6 fields で定めている。上位 pointer X も
fork しうるため、対応する record が要る。R1 は失効 record についての裁定であり、
cancellation は範囲外だった。

- (a) 下位 §S2-1.11 と同型を 1 層上へ写す (`active-cancellations/<pointer raw sha256>.json`)。
- (b) 上位では cancellation を持たず、fork の回復も補償世代 (Q3 (i)) だけで行うと明示禁止する。
- (c) 先送り確定項目として §12.2 へ移し、S / B と同じ扱いにする。

**親の推奨は (a)。** 理由は 2 つ。第 1 に、Q3 (i) の補償世代は「祖先へ戻さず前進する」規則であって、
**同一世代内で 2 本目の X が置かれた fork の敗者を無効化する手段ではない** — (b) を採ると
fork 敗者が永久に解決不能のまま残り、§7.2 の「live tip を一意に解決する」義務と衝突する。
第 2 に、下位が既に同じ問題を fork cancellation で解いており、(a) は R1 と同じ
「下位の形を 1 層上へ写す」判断で、上位だけ別解にする理由が無い。

(c) は「決めなくても段 0 が閉じない」点で (a) と同じ効果を持つが、cancellation は S / B と違って
**封印・副作用境界に依存しない**ため、先送り箱へ入れる理由が無い。

## 3. 実装の fix (Codex `role=author` が書く)

### I1 (SOL6-A-01) — fence 除去の完全化

`_read_design` の fence 除去を、`tools/check_docs.py` の scanner と同じ規則にする。

- 開き fence は `~{3,}` または `` `{3,} `` を許す。
- 閉じ fence は**同じ文字で、開き以上の長さ**でなければならない
  (短い closer では閉じない。長い外側 fence の中の短い fence を本文にしない)。
- 閉じられていない fence は `ContractError` で拒否する (現行どおり)。
- **既存 5 extractor の anchor はいずれも fence 外にあることを親が実測済み**である。
  受理集合は縮小のみで、既存 node は緑のままのはず。赤が出たら報告して止まれ。

### I2 (SOL6-A-02) — 削除型 decoy の陰性 node

現行 `test_design_fenced_decoy_is_not_authoritative` は「複製 + 可視側の緩和」型であり、
fence 除去を外した mutant でも `missing or duplicated` で拒否されるため、
**診断文字列の差だけで赤くなる偽 KILL** である。

- **canonical な表 / 段 6 行を fence 内へ置き、可視側からは削除する**型の陰性 node を新設する。
  fence 除去がある実装では「missing」で拒否され、外した mutant では**受理される** —
  これが受理集合の差による真の KILL である。
- §7.5 失効表と §10 段 6 行の**両方**について作れ。
- tilde fence と 4 個以上の backtick の型も加えよ (I1 の検出力を固定する)。
- 既存の複製 + 緩和型 node は**消さない** (別の検出力を持つ)。

### I3 (SOL6-A-03) — control 文の後続まで束縛

`_extract_stage6_contract` が control 文を最初の `。` で切り、後続を「空白で始まる」以外
検査していない。canonical control の直後に相反する但書を足しても緑になる。

- **clauses の後の残余全体**を、control 文と実行境界文の 2 つに分けて exact 比較せよ。
- 実行境界文 (「本行が固定するのは predicate であって実行ではない」で始まる文) の全文も
  独立定数として pin し、後続に**それ以外の文が残らない**ことを要求せよ。
- 相反する但書を足した synthetic doc が拒否されることを陰性 node で固定せよ。

### I4 (LB-B-03) — gate `CFAB-R4-CANCELLATION-RECORD` の新設

- `_EXPECTED_REQUIRED_GATES` と `manifest.v1.json` に
  `("CFAB-R4-CANCELLATION-RECORD", "user", "unresolved")` を加える (`gate_id` 昇順)。
- `count` = 13。`entries_sha256` は**親が独立に再計算した値**を prompt で渡す。
- `blocking_gates` は 4 → **5**。既存テストの期待値を新しい正しい値へ更新する。
- 段 0 の他の軸 (`status=incomplete` / `pending=5` / `applicable_unresolved=2`) は**不変**。

## 4. docs の fix (親が書く)

- **D1 (LB-B-01):** §7.5 の conformance 段落を書き直す。形状と 4 意味規則は §S2-1.10 の写しだが、
  **field の表現は上位層自身の慣習に従う** (`revoked_at` は A の `approved_at` と同じ int 秒、
  `revoked_by` は A の `approver` と同じ制約) と明記し、「写像は 1 key だけ」の過剰主張を撤回する。
  下位が UTC を文字列と定める点との差は**意図した層差**であり、ユーザー裁定 R1 (a) が
  「UTC 秒 int」を明示的に選んでいることを根拠として記す。
- **D2 (LB-B-03):** §12.3 を「残る裁定 1 件 = R4」へ書き直し、§2 の択一と推奨を載せる。
- **D3 (LB-B-04):** §12.3 の未完了理由を「4 件」でなく 3 軸 (`pending=5` / `applicable_unresolved=2` /
  blocking gates 5 件) の正確な列挙にする。
- **D4 (LB-B-02):** §12.4 の `FREEZE-AX-TOPOLOGY` の記述を、topology 単独でなく
  approval / pointer / revocation / cancellation の schema 全般の不適合まで含む射程へ訂正する。
  **gate ID・owner・status は不変。**
- **D5 (SOL6-A-04):** §12.1 の見出しに worklog 415 を加える。

## 5. 成果物影響 (DW-G05)

- **SOL6-A-01 未修正:** tilde fence 1 つで設計正本の可視部を丸ごと差し替えられ、
  失効 schema と段 6 受理集合を隠れた decoy から供給できる。
- **SOL6-A-02 未修正:** M1 を KILLED と記録できず、wave 前の恒真ゲート形を閉じた証拠が成立しない。
- **SOL6-A-03 未修正:** 段 6 の陽性・陰性 control 義務を後続 prose で無効化でき、reject-all が通る。
- **LB-B-03 未修正:** 上位 pointer の fork 敗者を無効化する手段が未定義のまま裁定閉包だけ完了扱いになり、
  §7.2 の「live tip を一意に解決する」義務が満たせない状態が残る。
- **LB-B-01 / LB-B-02 / LB-B-04 未修正:** 受理集合は変わらないが、conformance 主張・不適合の射程・
  未完了理由の 3 つが台帳と実装で食い違い、段 0 の完了証拠が再現不能になる。

## 6. fix の分割

**単一単位 (一枚岩)。理由:** I1 と I3 は `calibration_freeze_authority_contract.py`、
I2 は test file、I4 は contract.py + manifest + test file の 3 者にまたがる。
所有が素集合にならないため分割できない。
