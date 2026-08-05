# [T-428] 段 5 親レビュー — coder-v4-autonomous-trigger-gating.md の契約変更 (子 A 起草)

日付: 2026-08-04。レビュー者 = 親 (wave manager)。被レビュー = 子 A (Codex role=author) の
agent 定義 diff。pin 反映 (manifest / adapter / review_ledger) は本レビューの後に別所有の
子 C が行う — 起草者と pin 更新者を分離し、レビュー台帳の独立性を保つ (段 4 裁定 §1 A10/B3)。

## 判定: 承認

- **出力契約**: `implementation` (C++ 1 行) → `wire` (5 文字、`0|1`、左から LSB-first)。
  bit 順 = bit0 lock-conflict / bit1 update-absent / bit2 readvali-tid / bit3 readvali-locked /
  bit4 node-vali。`axis_trigger_gating.GATEABLE_REASONS` および `reflux_ir._EXPECTED_REASONS`
  と一致することを親が照合した。極性 (1 = backoff する) も裁定 §2 と一致
- **fail-safe**: `kUnset` は emitter 専権と明記され、coder に kUnset 用 bit を出力させない。
  reflux_ir.emit_predicate が常に sentinel を先頭に付加する実装と一致
- **遮断設計は不変**: frontmatter (`tools: []`、model、effort)、fresh subagent、
  リーク遮断 (勝ち筋 gate・候補順位・未評価候補の性能を使わない)、value フィールド非搭載、
  要約フィールド非搭載 (D43 継承) の各文言は 1 つも弱められていない
- **削除の妥当性**: C++ 骨格・enum・closed-region 制約・禁止識別子列挙の削除は、coder の
  出力面から C++ が構造的に消えたことに伴う整理であり、これらの強制は production 側
  (凍結 parser/emitter、diff 検疫、auditor) に残る。禁止識別子の実強制は
  `SYNTAX_CONTRACT_FORBIDDEN` の drift assertion として維持 (子 A 実装)
- **pipeline 記述**: 「凍結 parser と emitter が正準 C++ へ変換 → diff 検疫 → auditor +
  digest 照合」は新実装と一致

## 権限根拠

ユーザーが `/dev-wave T-428` で起動した task 本文 (consumer 閉包に proposal schema を明示) と
D149 決定 (6)。最終確認は裁定パッケージ W7 として wave 報告でユーザーへ返す。
