---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: worktree-t2850-trial-prereg
seq: 1
title: [T-2850] 探索の独立反復の試走の事前登録 v1 を書いた — Silo の backoff 値空間 × write-heavy / read-heavy × 5 手法 × 各 3 系列、評価数の族と経過時間の族の分離、本比較の系列数を手法対の対差 SD の計画値から決める規則、試走の試算 128.7〜145.4 node 時間と上限 200 (docs のみ、branch worktree-t2850-trial-prereg)
---

## 本文

- 依頼 (ユーザー、/dev-wave の引数): 試走の事前登録を計算なしの docs として書く。決めるもの = 試走の規模、2 つの比較の分離、記録項目、B・A・系列数・費用上限・比較の族、
  本比較の規模を試走の探索間の分散から決める規則。生成・選択に [T-2851] の留保条件を使わない。実走・runner 実装・計算投入・gate/検査/台帳の追加は scope 外。
- 成果物: `docs/search-repetition-trial-preregistration.md` (v1)、`docs/README.md` の 1 項目、insight `output/insights/2026-09-23/t2850-trial-prereg/`。設計判断は {{D:t2850-trial-prereg}}。
- 起点 local main `cadaf3805`、開始 gate rc 0 (08:35 JST)。段 2 は省略 (docs のみ、brief と草稿を plan とした)。
- 段 3 (Codex read-only、reasoning medium): 相談 A (統計設計・公平性・情報の漏れ) must-fix 7 / should 5 / nit 1、相談 B (実行可能性・費用の算術・既存規則との整合と過剰)
  must-fix 7 / should 5 / nit 2。27 件をすべて real と判定し採用 (refuted 0)。主な訂正は、pool した分散の上側限界を手法対の対差 SD の最大値に替えた、試走では E_T を再計測しない、
  本比較の block を n block と定めた、欠測を含む比較を判定不能にした、課題の選択に手法差を使わない。
- 段 4 直前の裁定 inbox の再走査で /rulings 第 32 回 (2026-09-23 08:2x 受領) の 2 件を反映した: MOCC の pin 候補の承認 (項 1、S2 の記述)、B-5 本走の承認 (項 2、既知結果の扱い)。
- 段 6 (Codex read-only レビュー 1 本): NO-GO、must-fix 3 / should 3 / nit 1 (段 3 の 27 件は closed 24 / partial 3)。7 件とも real。最大は本比較の費用の試算が登録した式と
  一致しなかったこと (bal の代入と E_T の再計測の加算)。§8.1 を「手法ごとの最大値」と明確にし、試算を v3 で計算し直した (S1 の 3 workload の計画用 C(5) = 417.8〜485.7 node 時間)。
  焦点再レビュー 1 巡目は NO-GO (must-fix 1 / should 2)。must-fix は段 6 の fix で親が入れた回帰 (E_T の優先で品質欠測を endpoint より先に置き、基盤設計 §4.6 と
  逆転) で、基盤設計の順へ戻した。2 巡目は GO (must-fix 0 / should 1、機械故障による結果の未解決を列挙へ残す) で、should も反映した。
- 実装面の差分はゼロなので変異 matrix は免除 (DW-S04)。受入全走は land 直前に同じ tip で実施する (本 fragment の時点では未実施)。

## 次の一手差分

### 更新

- [T-2850] **P1 (VLDB 差分分析 P3: 探索の独立反復と費用・成果の曲線)**: 事前登録 v1 `docs/search-repetition-trial-preregistration.md` を作った ({{D:t2850-trial-prereg}})。
  規則は着地時点で固定、測定の発効は計算確認の決定による。残りは 3 つ。(1) 試走: [T-2849] の実装 (基盤設計 §11 の単位 1〜7) の着地後、発効束 (事前登録 §10: 実装の commit、
  未指定の実装定数、model の exact ID と全 role への解決 (D2222 の起動契約)、prompt、環境・引数、schedule、walltime) を揃え、Silo の backoff 値空間 × write-heavy / read-heavy
  × 5 手法 × 各 3 系列 (B 10・A 30・初期点 2・N_eval 5、3 block) を投入する。見積り = 試算 128.7〜145.4 node 時間 (論理 600 session)、上限 200 node 時間、LLM の直列時間
  約 13 時間 (A = 30 使い切りで約 39 時間の仮定値) — 投入前にユーザー確認 (D2212 項 4)。(2) 試走の後: 事前登録 §8 の規則で T_c・計画の対差 SD・課題の集合・系列数を
  計算して追補に書き (手法間の差と曲線は使わない)、D2219 項 6 の再提示条件を評価し、本比較の上限 (提案 510 node 時間。S1 の 3 workload の計画用 C(5) は 417.8〜485.7) を
  ユーザー確認してから本比較を投入する。算出できない・上限を超えるなら n を縮めずユーザーへ返す。(3) MOCC (S2)・policy IR (S3) は、その空間の最初の生成より前の追補で足す。
  **生成・選択には [T-2851] の留保条件を使わない** (`docs/unseen-condition-transfer-preregistration.md` §2.3・§3、D2223)。学習条件は同書 §2.1 の錨の部分集合で、cell ごとに
  生成器が repo の docs を読めたかを記録する。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P3、記録 `output/insights/2026-09-23/t2850-trial-prereg/README.md`。
  base: d069818d09d5a72733c21d8ec1e6e2e270c4e9d2284111cd1b865714becb200d
