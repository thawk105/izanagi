# 段 1 brief — [T-244] U-10 値案起草 (実験予算 tuple)

## scope

`output/insights/2026-08-05_t244-p3-design/s2-plan.md` §1.3 の**入力 12 項目**に、
8c パッケージの **V-3 (R の値と実行時間影響)** と **V-2 (seal の result evidence の正本)** を足した
**14 項目**について、根拠付きの値案 1 式をユーザー批准パッケージとして起草する。docs のみ。

## 確定済みユーザー裁定 (不変条件)

- 方式は 2026-08-06 /rulings の **(b) 起草 → 批准**。発行主体は人間のまま (D147 決定 4)。
- **本番 authority (`reflux_origin_authority_v2.json`、71 bytes) へ entry を 1 件も書かない** (D183)。
  本 wave は同ファイルの bytes を変更しない。
- 前提は D198 (狭まった codec 包絡線)、D189 (予約時消費)、T-564 の較正 (未活性、N7)。
- D205 (プロトタイプ基準) に従い、防御的堅牢化のための値の水増しはしない。
- 規律 2 (正しさゲートを緩めない) / 規律 3 (シグナルを後付けにしない) は不変。値案が
  「floor を下げて通しやすくする」方向を採ってはならない。

## 成果物

`output/insights/2026-08-06_t244-u10-budget-values/` に批准パッケージ 1 式
(値表 14 項目 + 各項の根拠 + 制約検算 + 却下案 + 批准後の発火手順)。
批准は `/rulings` でユーザーへ返す。**実装・結線・authority 書込みはしない。**

## 成果物影響 (DW-G05)

authority の予算値は certified selection の**探索量**と proof chain の**受理集合**を決める。
値が決まらない限り P3 は FAIL のまま、8c 結線は再起票禁止 (D201)、origin ledger は
本番で 1 件も発火しない。値が緩すぎれば floor が実効を失い「候補多様性を名乗る」抜け道が開く
(D198 が閉じた誤読の再演)。値が厳しすぎれば 1 generation = 1 drive の 8c が構造的に certifiable
terminal へ到達できない authority になる。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** floor tuple の \(R\) (= parser の `rounds`) と 8c V-3 の \(R\) (= member 行数) は
  別量なので、値案では `R_rounds` / `R_replicates` へ改名して提示する (N6、D75)。
- **(P2)** 科学的 cell の同一性は現行 `cell_key` (workload / axis / verifier / environment) を
  そのまま採り、series 内での `cell_key`・`origin_id` 再利用禁止だけを authority 側の追加規則とする。
- **(P3)** 唯一の現実的 consumer は 8c (1 origin = 1 generation = 1 drive、3 cell) である。
  値は「8c が certifiable terminal へちょうど到達できる最小」に置き、将来の探索余地を先取りしない。
- **(P4)** `R_replicates` は parser 下限の **2** を第一案とし、中央値が取れる **3** を代案として
  実行時間コストと併記する。8c の 1 drive は `reps=2 × extime=1s` × 最大 3 round なので、
  R 倍は harness 実測時間に直接効く。
- **(P5)** 失敗の課金範囲は D189 の予約時消費をそのまま採る = candidate 生成失敗・評価失敗・
  provider 失敗のいずれも **返却しない (forfeit)**。no-refund は例外を作らない。
- **(P6)** codec 上限・storage 上限は authority へ literal で写さず、authority が持つのは
  `Kmax` だけとし、`C_codec` / `K_codec` / 64MiB は実装側定数のまま参照する (二重正本を作らない)。
- **(P7)** V-2 の result evidence の正本は、`drive()` の戻り値から導出する
  **新規の result-evidence record** とし、既存 outcome の再利用で済ませない。

## 並列分割方針

docs-only のため実装子は不要。ただし codec feasibility の 2 本 (origin_bytes / head_bytes) は
閉形式でなく実行検査 (N3) なので、**制約検算の probe だけは Codex `role=author` が書き**、
親が走らせて値を確定する。probe は repo 外 (job dir) に置き land しない。
段 2 プラン起草 1 本 → 段 3 敵対 2 レンズ → 段 4 裁定 → 段 5 probe 実装 → 段 6 レビュー 2 本。

## 未確認・子へ渡す宿題

- 8c の 1 drive の実 wall-clock (R 倍の絶対コストを言うため)。
- `_affine_batch_bytes` の実バイト勾配 (Qmax の上限がどこで 64MiB に当たるか)。
- `Kmax` が実際に効く場所 (`OriginSealed` の class hash 数) と 8c での必要数。
