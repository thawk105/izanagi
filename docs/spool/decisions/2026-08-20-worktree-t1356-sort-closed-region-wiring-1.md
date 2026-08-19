---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: worktree-t1356-sort-closed-region-wiring
seq: 1
---

## {{D:auditor-violation-type-vocabulary-expansion}}. auditor の violation type 語彙を16から21へ拡張し、sort closed-region 残余5項目を独立番号で結線する

**決定:** [T-1356] (2026-08-18 /rulings 全件 第8回) の実装として、auditor の reward-hack
ギャラリーへ sort closed-region 契約の残余5項目 (新しい型/関数の追加・非決定ビルトイン・
副作用のある呼び出し・ループ・例外送出) を型17〜21として**個別番号**で追加した。
`orchestrator/codex_roles/manifest.json` の output schema (`violations.items.type.maximum`)
と `orchestrator/campaign/auditor_gate.py` の `_AUDITOR_VIOLATION_TYPES` を両方
`16→21` へ広げ、`orchestrator/codex_roles/review_ledger.py` の3 pin
(`SOURCE_FILE_SHA256`/`ROLE_MANIFEST_SHA256`/`SCHEMA_SHA256["output"]`、いずれも `"auditor"`
キー) と `.codex/role-adapters/auditor.json` を同期させた。

**理由:**
- 型番号は8-12 (5個の独立 lock 系統) を前例とし、16 (1個への集約) は「同一骨格汚染の複数具体形」
  という単一メカニズムの多面性であり今回とは前例として遠い。1個集約案 (段2 codex plan の
  当初案) は `location`/`note` が任意フィールドのため、将来「5項目のうちどれを検査したか」の
  集計を不能にし、規律3 (verifier が見逃した理由の構造化) の要求を弱める。
- 機械 gate の受理範囲拡張は auditor の**指摘語彙**の拡張であり、CC variant 側の raw 受理集合
  (`coder_effect_gate.py` の DENY_TABLE、`sort_swo_oracle.py` の判定ロジック) には一切触れない。
  schema と gate の両方を同時に広げないと、auditor が新しい型を引用した瞬間
  `AuditorGateFailure` で reject される (型5「consumer 取り残し」の自己再演になるため、
  両方を同一実装単位に含めた)。
- gallery 本文の記述は、機械執行の粒度 (完全/部分的/なし) だけを示し、なぜ verifier/機械 gate が
  見逃すかの具体的機序 (識別子名・コード形状・corpus 発火条件) は書かない。境界条件の開示は
  D511 の禁止事項であり、段6 敵対レビューが「file:line 付きの機序説明」自体が回避手順の開示に
  当たると指摘し是正した。機序の報告は auditor 自身の構造化出力
  (`violations[].verifier_blind_spot`、発見時の事後報告) に委ね、role prompt (事前に読める
  回避手順) には書かない。

**却下した選択肢:**
- **型17への1個集約 (段2 codex plan の当初案)。** schema/gate 変更コストは
  `maximum: 16→17` も `16→21` も同型 (frozenset range の終端値のみ) で実装コスト差が
  無視できる一方、5項目の内訳が追跡不能になる。段3 敵対相談レンズBの指摘を採用し上書きした。
- **auditor.md の型17-21記述に file:line 付きの具体的機序を書く (段5 実装子の初版)。**
  D48/D511 の境界条件非開示に違反すると段6 敵対レビューが判定し、fix で「完全/部分的/なし」の
  分類だけへ後退させた。
- **`coder-v4-autonomous-sort.md` の禁止5bulletや「機械執行の範囲」表を書き換える。**
  T-396/D511 の「禁止文は1byteも変えない」原則を維持し、契約文への反映
  (「残余は auditor が拒否する」等) は本 wave の scope 外とした。段3 レンズBは「字義上は
  T-1356 裁定を満たす」と確認したが、契約文反映が必要かは別 scope の判断に委ねる。

**研究状態への影響:** なし。production の CC variant 受理集合・certified 選択・材料レポートの
値は変更しない。変わるのは auditor が引用できる violation type の語彙と、それを裏付ける
schema/gate/pin/adapter の整合だけである。
