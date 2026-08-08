# 段 1 brief — [T-671] + t530 件 6 設計択一 (設計 wave、実装しない)

## scope

- 争点 A ([T-671]): 汎用 certified 経路 (campaign loop COMMIT / 材料レポート / WAL producer) に
  loader module (env_contract.py / env_contract_activation.py) の source binding を課すかの設計択一。
- 争点 B (t530 件 6 = F-12): contract 更新 (pegasus g2 活性化) で campaign id が分裂する結合の扱い。
- scope 外: t530 件 1〜5・7 の実装 (件 5 = D125(2) supersession 表記は隣接事実として言及のみ)、
  [T-189] served-model attest、[T-184] stage matrix、あらゆる本番コード編集。
- 成果物: `output/insights/2026-08-09_t671-source-binding/package.md` (R 番号択一)、
  worklog fragment、期待経路 1→2→3→4→7→8→9 (DW-S04「実装しない」裁定、変異免除)。

## 確定済みユーザー裁定 (最新まで辿った)

- rulings2 (08-09) 件 1: [T-671] 設計 wave 承認、件 6 と束ねてよい (ユーザー明言)。
- [T-530] 08-08 裁定: hash 束縛実装 wave 起票可 → wave は段 6 中断、7 件パッケージ未提出。
- [T-657] 順序確定 (§44)。並行 wave (t657-t660) が本日活性化を段 3 で前進中。
- D205: 堅牢化投資はプロトタイプ基準。D125 決定 (2) は T-343 が既に破って land 済み (t530 実測)。

## 実測で確定した前提 (Explore 子 2 本、file:line は handoff に詳細)

1. 非対称は実在: silo (`silo_ladder_rung1.py:254-294`, live bytes) と qualification
   (`qualification/contract.py:38-76`, git blob) は**独立 2 実装**で 2 module を code identity に束縛。
   汎用 certified 経路は束縛ゼロ。activation 参照は record JSON の hash のみで loader 改変を検出しない。
2. 例外 = `certified_writer_preflight._verify_loaded_repo_modules` (:85-126) が唯一 loader bytes を
   検査するが floor/t126 の投入前 gate 限定、campaign loop へ未配線。
3. 分裂の発火条件 = t530 land ∧ g1 開始未完了 campaign の g2 跨ぎ resume。原因は identity 確定前の
   ambient `lookup/authorize` (現 15 か所超)。lock 固定世代を引き継ぐ仕組みは現存しない。
4. main のままなら分裂なし、代わりに g1/g2 COMMIT の無区別合流 (provenance 消失)。
   分裂後は discover 2-hit で FileNotFoundError (fail-closed だが読出し不能)。
5. g2 は未活性化 (serial 1 のみ)。既存 30 campaign の id 到達不能は status quo。

## 親の provisional 裁定 (攻撃対象)

- (P1) 争点 A の択一軸は「既存機構の配線先」で立てる: (a) silo 型 binding の汎用化 /
  (b) 既存 preflight の campaign loop 配線 / (c) 記録のみ (gate なし) / (d) 見送り (D205)。
  親 provisional: (b) 系が最小新規実装。独立 2 実装 (silo/qualification) が既にあるため
  DW-G03 の「独立 2 例」gate は汎用化を許す側に立つ、と読む。
- (P2) 争点 B の択一軸: (i) t530 設計維持 + lock 世代を resume 時に ever-active 解決で引き継ぐ /
  (ii) id pre-image から契約 hash を外し lock/WAL のみ束縛 / (iii) 分裂を仕様として受け入れ
  discover 側を世代考慮に直す。親 provisional: (i) が t530 plan v2 と両立し二重化を根絶する。
- (P3) [T-671] の裁定は g2 活性化の追加前提に**しない** (並行 t657 wave を止めない)。
  §44 の前提 2 件に本件を足すかはユーザーが決める事項としてパッケージに明記する。
- (P4) 両争点は「書込み時点の ambient を焼く vs 権威を固定して引き継ぐ」という同型軸を持つ。
  1 パッケージ・共通の設計原則 + 争点別 R 択一で返す。
- (P5) 受入環境: Pegasus 計算ノード、dispatch recipe、lease 遵守、背景投入。実装差分ゼロでも
  受入全走は免除しない (DW-S04)。実 repo を読むテストの存在判定と証拠を worklog へ 1 行書く。

## 成果物影響 (DW-G05、実装しない/放置した場合)

- 争点 A 放置: g2 活性化後、dirty / 未レビュー loader bytes で生成された certified 選択・レポート・
  WAL が activation 参照だけの検証を通過し、受理集合が暗黙に「loader 改変込み」へ広がる。
- 争点 B 放置: t530 land 後の g2 活性化で、進行中 campaign の WAL が新旧 2 dir へ静かに二重化し、
  該当 slug のレポート・replay 読出しが FileNotFoundError で停止する (可用性破断)。

## 並列分割方針

- 段 2: read-only codex 1 本がプラン (択一案 + file:line 根拠 + 推奨) を起草。
- 段 3: 敵対 2 レンズ並列 (A=sol / B=luna 混成、DW-S03 に従う)。brief と plan の両方を攻撃対象にする。
- 段 5・6 なし (実装しない)。段 7 で親が記録、fragment のみ commit。
