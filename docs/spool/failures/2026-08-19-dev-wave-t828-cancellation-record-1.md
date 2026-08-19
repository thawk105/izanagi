---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t828-cancellation-record
seq: 1
---

## 新規

### {{F:record-name-decoy-slips-past-table-prefix-check}}. table_prefix 一意性検査は、本物 marker を軽微に破壊し decoy で補う攻撃に脆弱 [テスト代表性]

- 事象: T-828 (CFAB-R4-CANCELLATION-RECORD を resolved にする wave) の段6 敵対レビューが、
  `orchestrator/tests/calibration_freeze_authority_contract.py` の
  `_extract_design_{revocation,cancellation}_schema` の table_prefix (marker 全文 + header)
  一意性検査を、「本物の marker 継続節を改行→半角空白で軽微に破壊し、直前へ『注記: 』付きの
  未改変 canonical コピーを挿入する」decoy で欺けることを実証し、`validate_repository()` が
  relaxed な本物の table 内容 (`scope` 行) を見過ごしたまま受理することを実コードで確認した。
  fix (record 名の短縮 anchor 一意性を先に検査、{{D:record-name-uniqueness-defense}}) 適用後の
  焦点再レビューが、全角 (fullwidth) homoglyph (`record C` → `record Ｃ`) で同じ型の攻撃を
  再構成し、byte-exact 一意性検査も回避できることを実証した。NFKC 正規化での対策後、親が
  自らゼロ幅文字 (U+200B) 混入でも同型の decoy が理論上なお成立することを追加検証した。
- 根本原因: 文書全体からの string search で「本物の一意箇所」を特定する設計は、攻撃者が
  本物側の任意の一部 (検索対象の外) を破壊しつつ、別の場所へ canonical な複製を置ける限り
  根本的に欺ける (「一致した場所を信頼する」設計そのものの弱点であり、個々の homoglyph 種別の
  もぐら叩きでは閉じない)。
- 恒久対応: {{D:record-name-uniqueness-defense}} — record 名一意性検査 (NFKC 正規化込み) を
  table_prefix 検索より前に追加し、revocation・cancellation 両 extractor へ適用した
  (DW-G03: 同型欠陥の独立 2 件による一般化)。regression pin 4 本
  (`test_design_revocation_plaintext_decoy_declaration_is_rejected`,
  `test_design_cancellation_plaintext_decoy_declaration_is_rejected`,
  `test_design_revocation_fullwidth_homoglyph_decoy_is_rejected`,
  `test_design_cancellation_fullwidth_homoglyph_decoy_is_rejected`)。変異 matrix
  (`output/insights/2026-08-19_t828-cfab-r4-mutation-ledger.json`) で baseline 84 passed・
  3/3 KILLED・SURVIVED 0・MISMATCH 0 を確認した。
- 既知の残存: ゼロ幅文字・Cyrillic/Greek 等の非 NFKC-foldable homoglyph による同型 decoy は
  親が自ら検証し理論上なお成立しうると確認した。design doc は信頼できる中核 (CLAUDE.md 規律6)
  の内側で親が編集するファイルであり、目視不能な注入は通常の編集フローでは発生しないため、
  本 wave では追加対応を起票しない。Unicode カテゴリ全体のホワイトリスト化という質的に異なる
  対応が必要になった時点で再訪する。
- 再発検知: 同型の exact-match schema 抽出器 (§7.5 の Q/A や将来追加される record 種別等) を
  書く wave は、本エントリを参照して record 名一意性検査を最初から組み込む。監査トリガ
  (CLAUDE.md 規律6) 発火時のレンズ設計にも本型タグを含める。
