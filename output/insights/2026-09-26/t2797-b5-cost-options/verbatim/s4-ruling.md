# 段 4 裁定 — [T-2797] B-5 本走の計算費用削減案 (親、2026-09-26)

- **実装しない (4→7→8→9)。** 依頼は「提示だけで投入はしない」。実装面の差分 0 なので変異 matrix は免除 (DW-S04)、受入全走は行う。
  docs-only で一次資料から事実を再抽出したので、独立 read-only レビュー 1 本 (codex review-1) を残す (DW-C00)。段 2・3 は軽量版で省略。
- (P1) 現行 cohort の 6 比較が判定不能: **real** (report `_project` と判定部の実読、LLM 4 系列は endpoint-fixed / score なし、wh random 2 系列は stock-unestablished)。
  ユーザーへ問う前提として insight §3 に置く。再開の解釈 (429 = §3.3 機械故障) は AI が決めずユーザーへ。
- (P2) 案 (1) は発効束の実行契約の改訂で足りる: **real (条件付き)** — 事前登録 §4.1 (評価ごと単回呼出し)、§5.4 (同機体・同 job は系列開始 stock と最初の評価だけ)、§11 (親の待機は別欄)。
  ただし endpoint 選択が node 間の差を含むので、全 arm に同じ切り方を当てることを勧めとして書く。
- (P3) 取得済み trace の同時検査は検査対象・判定を変えない: **real** — pipeline の直列 fail-fast 構造 (`_run_one_pass`・`evaluate`) と、[T-2850] の vprobe で直列・同時の判定・取引数・辺数・閉路数が全件一致。
  失うのは早期打ち切りだけ。静定待ちの延長 (60 s 以上) が組で要る。
- 計算ノード: 本 wave の枠は rh B0-L-W0 同時 2 の 1 job (Elapse 2,899 s = 0.81 node h、投入は [T-2850] session) + 受入 1 回 (約 0.25 node h 見込み) で 2 node h 未満。
- scope 外 (記録のみ): write-heavy LLM の 12 / 14 却下の原因、静定待ち時間切れの原因、LLM 親の --resume による使用量の伸びへの対策。
- ユーザーへの問い: insight §7 の 4 択 (A n=12・3 workload / B n=9 / C read-heavy を外す / D 見送り)。/rulings 第 35 回は本件を載せない (同 session 返答、D2243 索引外)。
