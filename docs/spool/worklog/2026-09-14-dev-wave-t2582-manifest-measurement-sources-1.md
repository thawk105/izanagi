---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t2582-manifest-measurement-sources
seq: 1
title: [T-2582] K2 manifestの知識源を測定記録へ絞る規律を正本へ置き、実走導線から引けるようにした (docsのみ、branch worktree-dev-wave-t2582-manifest-measurement-sources)
---

## 本文

- 依頼は D1936 項 2 の運用反映。**実装面 (コード・テスト・機械設定) の差分はゼロで、docs 17 行の
  追加だけである。** `DW-S04` により変異 matrix を免除した。受入全走は免除していない。
- **純増の言い方を段 3 で訂正した。** 親の brief は「送り手側の判断は運用文書に無い」と書いたが、
  レンズ b が `output/insights/2026-09-10_cc-next-precheck/run-card.md` に**当該 1 走の指定として**
  「全文を解決して使い、設計説明の混入・指示検出をすり抜ける加工はしない」が既にあることを示した。
  正しい純増は「1 走限りの判断を常設規律にし、manifest 作成時に読む導線を足したこと」である。
- **段 2 の判定基準が両側へ外れており、段 3・段 6 が別方向から 2 回直させた。** 初案は
  「人間または AI が書いた自由文フィールドを含む file は選ばない」で、(a) 裁定していない
  書き手基準の一律除外を正本へ昇格させ (広すぎ)、(b) 生成器が埋め込む定型の運用説明を
  素通りさせる (狭すぎ) ものだった。確定した基準は**「誰が書いたか」ではなく「何を述べた文か」**。
  決定は {{D:k2-knowledge-source-selection}}。
- **段 6 レビューが、加工の指南に読める文面を 1 件止めた。** 初稿の「どちらも測定値と同居していても
  外す」は field や注記を削る操作として読めた。裁定が明示的に禁じた「指示検出をすり抜ける文章加工」
  そのものなので、「これらの説明を含む**成果物**は…source に選ばない。説明部分を削って投入するので
  はなく、別の測定記録を選ぶ。」へ置換した。
- **段 6 レビューが実在成果物へ当てて、判定が割れる 1 件を出した。** 進行状態と抽象的な成否だけを
  持つ checkpoint の可否が本文だけでは決まらなかった。「観測値と判定を伴わず、探索の進行状態と
  抽象的な成否だけを保存した checkpoint は測定記録に当たらない」を足して一意にした。
  同レビューは別 campaign の成果物にも当て、file 名の許可リストなしで同じ結論が出ることを示した。
- **gate は 1 行も触っていない。** K2 consumer の指示検出、manifest の schema・parser・受領証、
  role 契約、2026-09-02 の歴史 fixture はいずれも不変である。
- **段 3 の子 1 本が部分レビューで終わった。** 自分で組み立てた不在 path 1 件に対して prompt の
  「読めなければ即停止」を適用し、レビュー全体を打ち切った。停止条件の射程 (射影 file に限る) を
  明示して再投入し、全レンズを回収した。型は {{F:child-stops-whole-review-on-self-invented-path}}。
- Codex 子 7 本 (plan 1 / consult 3 / review 2 / focus 1)。全て `gpt-6-astra`・effort medium・
  `outcome=accepted`。焦点再レビューは段 6 の 10 所見すべてを closed と判定し、新規 real はゼロ。
- 成果物と生証拠 = `output/insights/2026-09-14_t2582-knowledge-source-selection/`。
- **裁定パッケージ (未実装):** `docs/agent-architecture.md` の実行境界項が「この role の wrapper が
  実際に consumer を通った成果物は 0 件である」と現在形で断定している。2026-09-02 の走行では
  同 role が proposal を出し production の consumer がそれを判定しているが、本文の「wrapper」の
  射程が一意でないため、断定が偽なのか語が狭いのかは別途の照合が要る。T-2582 の名指し範囲外。

## 次の一手差分

### 完了

- [T-2582] K2 manifest の知識源を測定記録へ絞る送り手側の規律を `docs/agent-architecture.md` の
  K2 role 節へ置き、段 4b runbook から参照を張って manifest 作成時の導線につないだ。
  remaining: none
  base: 3fc764eb55060dbbea18b401be9ca1e69c784130ac5c22b0b0cd08eb7807344e

### 新規

- {{T:k2-wrapper-consumer-artifact-claim}} **P3・新規**: `docs/agent-architecture.md` の
  K2 実行境界項が「wrapper が実際に consumer を通った成果物は 0 件」と現在形で断定している。
  2026-09-02 の走行の一次資料と照合し、断定が偽なら訂正、「wrapper」の射程が狭いなら語を明示する。
