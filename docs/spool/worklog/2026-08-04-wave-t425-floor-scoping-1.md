---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-t425-floor-scoping
seq: 1
title: Pegasus floor scoping を最小 env 化で安価実測し、真正 floor 取得設計を裁定パッケージへ返した — 同窓 between CV は rr5 系 0.786% / rr50 系 0.345%、取得設計は K=15 固定を推奨 (コード + docs、branch worktree-wave-t425-floor-scoping、変異 = 4/4 KILLED)
---

## 本文

- **依頼はユーザー command 引数 `/dev-wave [T-425]` (背景 job)。** 軽量版 — 設計択一は裁定
  パッケージでユーザーへ返し本 wave では決めない・正しさ防壁非接触・受理集合不変と段 1 で判定し、
  段 2・3 を省略。子は codex author 1 本 + fix 2 本 + read-only レンズ 3 本 (3 巡)。
- **(162) 裁定「既存 driver の最小 env 化で安価に測る」を実装・実測した。** between_run_floor.py
  同形の scoping driver + 薄い job wrapper (計 3 新規ファイル、commit d9cd84d + 5bec729)。
  実測 (request 887785.nqsv、bnode138、8 sessions × 5 reps、387 秒):
  write-heavy 系 = 同窓 between CV 0.786% / within 2.071% / abort 77.1%、
  balanced 系 = 同窓 between CV 0.345% / within 0.964% / abort 67.3%。
  **値は scoping であり floor でも品質ゲートでもない** (D145 決定 1〜2。JSON 自身が
  `eligible_for_compare=false` / `time_window_clusters=1` を刻み、命名は consumer glob に不可視)。
  両点とも同窓 between < within で linux と同構図 — 事前規定どおり安定性の証明とは解釈しない。
- **真正 floor の取得設計は裁定パッケージ U-1〜U-7 (v4) としてユーザーへ返した** (正本 =
  `/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md`、凍結写し = insight)。
  v1 は段 6 レンズ 1 巡目が **NO-GO (ADV-01〜10)** で反証し、親が全件 real 裁定して改稿、
  2 巡目焦点再検 (closed 7 / partial 3 / regressed 0 + 新規 1) と 3 巡目 (上限、残 ADV3-01 =
  二成分推定量と χ² nominal 表の不整合) も反映した。3 巡上限到達のため ADV3-01 は DW-O16 に
  従い親が real 裁定し、「nominal 表は K 選択の設計指針に限定し、取得後の実判定は
  simulation-based calibration を既定・必須の事前登録手続きとする」役割分離で閉じた
  (docs のみの所見で変異裏取りは非適用) —
  estimand は consumer と同じ 1 session-median 周辺 CV に是正、検出力設計を χ² nominal 表 (窓間支配モデル限定) で
  実体化 (境界 3% の危険誤りは全 K で nominal 5% 固定、設計感度 1.5% での検出力 K=8=0.72 /
  K=15=0.976)、逆転点の算術誤り訂正 (正 = 1.50 倍、v1 は約 2 倍と誤記)、費用は実測から
  0.08 node-hour/窓 へ (v1 は 0.7 と過大)、official 8b/8c per-pair との境界を U-7 に新設。
  **K は設計感度 × 検出力の裁定であり scoping 値を推薦根拠に使わない** (署名間非転移)。
  親の推奨 = **K=15 固定 (択 b、約 1.3 node-hours、逐次増補なし)**。依存順序 (U-6) を含む。
- **実測で確定した環境事実 2 件。** (i) 計算ノードの perf 実体はノード個体差がある —
  初回 885102.nqsv (bnode074) は kernel 5.15.0-173 対応 linux-tools 不在で全 rep 失敗 (43 秒
  fail-fast)。登録 calibration の bnode011 は同 kernel で実体あり。fix F-2 で preflight +
  fallback 探索を job script に追加し、bnode138 では `/usr/lib/linux-tools-5.15.0-100/perf` を
  採用して成功した。(ii) dispatch_compute の overall-timeout は queue 待ちを含めて数えるため、
  保守明けの滞留 (QUE 227) では walltime+既定 grace が queue 内で尽きる — 受入 1 回目は
  rc=16 (infra)、`--overall-grace 21600` で再走し緑。
- **投入前監査で job script の qstat 呼び出しが測定を殺す欠陥 (F-1) を検出し fix した**
  (raw PBS_JOBID + set -e 致死 → prefix strip + 非致死 capture、floor_campaign.sh と同形)。
- **走行中に緊急保守 (15:00–19:00) と scheduler 回復遅延があり、ユーザー指示で一時停止 →
  回復後に再開した。** 停止中の queue request は保守明けに実行され、受入緑 (355 秒) を得た。
- **検査結果**: 受入 (IZANAGI_TEST_TRIGGER=final、計算ノード) 緑。変異 M1〜M4 = 4/4 KILLED、
  赤 node は事前登録と完全一致、baseline PASSED @ 5bec729 (mutation-ledger は insight に凍結)。
  provenance full 監査 rc=0。裁定パッケージへは read-only レンズ 3 巡 (上記)。
  F98 回避のため測定は repo 外 checkout で実行し、wave worktree は clean を維持した。

## 次の一手差分

### 更新

- [T-425] **P1・ユーザー裁定待ち (本エントリ)**: 安価測定は完了し、真正 between-run floor の
  取得設計を裁定パッケージ U-1〜U-7 (v4、レンズ 3 巡検証済み) で返した (時間窓 K・node の数え方・
  検出力からの標本数規則・workload 署名・below-within 事前規定・依存順序・official 8b/8c との境界)。
  正本 = `/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md`、凍結写しと
  一次データ = `output/insights/2026-08-04_t425-floor-scoping/`。推奨 = K=15 固定 (択 b) +
  H1/H2 署名 + 層 C scalar 限定 (U-7 択 a)。裁定後の実装は依存順序 (U-6: T-419 U 系 →
  較正再取得 → T-424/T-272 → floor infra) に従う
  base: 852ed35ef63e595ffe0bcaba178d12e86e78e06b3f93d45fee8017f483e54443

### 見送り追記

- [T-272] 2026-08-04 の floor scoping 実測で、裸 python3 の版数に加えて perf 実体のノード個体差 (bnode074 不在 / bnode011・bnode138 実在) も同じ環境 gate の射程だと確定した。scoping 側は job script の preflight (5bec729) で自衛済み、certify 経路は未対応のまま。
