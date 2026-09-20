# docs/phase3-main-experiment.md からの逐語射影 (bullet 単位で切る、省略なし)

## (1) 「検証相 (roadmap §3.2) の配線」の bullet

- **検証相 (roadmap §3.2) の配線:** headline に載せる最終候補は、開発相の 1 run 短 trace 検証だけでなく**検証相 (seed を
  変えた N 回反復 + 長 extime の trace、信頼度 1-εⁿ)** を通過していること。LLM が任意コードを書く Phase 3 でこそ「検証用
  trace が見ていないアクセスパターンでだけ正しい CC」(roadmap §3.4 の reward hack 第 1 項) が現実の脅威になる。実装は
  後続段 6 のタスク。

## (2) 層 1 (iv) 実計測の総予算上限

- **(iv) 実計測の総予算上限 = 合計 12 時間 (宣言値、拘束):** 時間計上 = S-1 の全 campaign
  プロセスの monotonic wall time を**成功・失敗・timeout・機械故障 retry・build・verify・
  bench・floor campaign・検証相校正・検証相のすべて込み**で台帳に累積する。driver は各
  セッション起動前に残予算を検査し、不足なら起動せず、その時点で未完走の**全比較を対称に**
  判定不能へ倒す (観測値を見た選択的な打ち切りをしない)。内訳概算 (拘束は総額のみ): floor
  campaign ≈ 1.5h、検定 campaign ≈ 1.5h、variant build + 開発相 verify (18 構成) ≈ 1h、
  検証相校正 ≈ 0.5h、検証相 ≤ 4h、機械故障 retry 予備 ≈ 2h。予備枠の使途は機械故障 retry
  のみ (層 2 の閉じた列挙)、枠の目的間移転は禁止。

## (3) 層 1 (iv 付属) 検証相の拘束数値

- **(iv 付属) 検証相の拘束数値 (繰延べの撤回):** 対象 = headline 最終候補 = 系側 gate 構成
  のみ (g_rl / g_rt、§7 既定)。**N_verify = 8 独立反復/workload** (計 24 verify)。long
  extime = 校正で確定: trace-enabled build で extime {3, 6, 10}s 各 1 回の verify 所要を
  実測し、**1 verify ≤ 10 分に収まる最大値**を採る (下限 3s = S2 前例)。確定値は本節へ
  日付付き追記。総検証相予算 ≤ 4h、超過見込み時は extime を下げ **N_verify は削らない**
  (信頼度の指数を観測後に弱める自由度を残さない)。判定 = 24 verify 全て anomaly ゼロで
  pass、1 件でも anomaly → 当該 variant は失格 (規律 2)。**形式的信頼度 1-εⁿ は主張しない**
  (ε の定義・seed identity の記録・trace の永続保全 (現行 pipeline は verify 後に trace を
  削除する) のいずれも無いため) — 「独立反復 n=8 × 3 workload で anomaly ゼロ」という操作的
  事実として報告する。roadmap §3.2 の 1-εⁿ 表現は本 S-1 報告では限定表現に置換する。

## (4) 層 1 (iv 付属の校正確定 — 2026-07-16 追記)

- **(iv 付属の校正確定 — 2026-07-16 追記) long extime = 3s に確定:** read-heavy (rr95) ×
  系側 gate `g_rl` の trace-enabled build で extime {3, 6}s を各 1 回実測した (10s は
  「600 秒超過で残候補打ち切り」の規則により未実測)。verifier wall time = 433.3s / 974.7s、
  いずれも verdict = serializable・certified。600 秒以下の最大値として **extime = 3s** を
  採る。検証相の総所要見込み ≈ 433.3s × 24 verify ≈ 2.9h ≤ 4h (予算内)。全候補の生値・
  構成 provenance・選定規則は `output/env/linux-baremetal/calibration/s1_verify_extime.json`
  (人間可読版は同名 `.md`) に凍結した。

## (5) 層 2 「seed×N」の操作的定義

- **「seed×N」の操作的定義:** ycsb は CLI seed を持たず RNG は run ごとに自己シードする —
  検証相・性能計測とも「seed×N」は**独立 N 反復**を意味し、決定論的 seed 固定は導入しない
  (CCBench 改変 (D16) を要するため)。独立性は操作的仮定 (層 1 (ii) と同じ限定)。
