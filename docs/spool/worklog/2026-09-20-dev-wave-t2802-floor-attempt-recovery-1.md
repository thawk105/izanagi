---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2802-floor-attempt-recovery
seq: 1
title: [T-2802] floor attempt ledger 回復の二乗構造を per-call memo で直し、受理集合不変を差分 probe・変異 8/8 KILLED で示し、受入 shard の A/B 隣接対 3 組で効果を測った (コード + test、branch worktree-dev-wave-t2802-floor-attempt-recovery)
---

## 本文

- 依頼 (T-2802 起票文 + ユーザー引数) の範囲で 1 wave。一次資料は `output/insights/2026-09-20/t2802-floor-attempt-recovery/README.md`
  (機序・受理集合不変の証拠・変異台帳・A/B 走表と対表・裁定パッケージ・逐語)、設計判断は {{D:floor-attempt-recovery-per-call-memo}} と
  {{D:floor-recovery-ab-measurement-contract}}。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery/HANDOFF.md`。
- 段 2 plan の訂正: 代表 node は measurement-generation 経路で、v1 の main 行ごとの sha256 は直接の律速でない。「1 s 未満」は取り下げ、
  効果は作業仮説として実測に委ねた。段 3 相談 2 本 (正しさ境界 / 実効性・測定設計) の must-fix 6 は全て測定設計側 (must-fix 基準の拡張、
  200 s は実用閾値でノイズ由来でない、別 tree 比較は D2068 の同一 tree 条件を満たさない、無効対と実装起因の赤の分離、nodeid 完全集合の凍結、
  warm-up の対称化) で全採用。親の追加案 P5 (main ledger 生読取の呼び出し内共有) は遅延形だけ採用 (eager は例外順序を変える)。
- 段 5 は Codex author 2 本並列 (production + test / A/B launcher・集計器・差分 probe)。author sandbox では guard で pytest が起動できず
  全て未実走 → 親の焦点走 (計算ノード) で 282 passed → 実装 commit `06d101fee`。consumer 13 file の焦点走 2522 passed / 16 skipped / 0 failed。
- 段 6 レビュー 2 本 (過剰・削除 / 正しさ境界) はどちらも production の受理集合変更を未検出。must-fix は検証成果物側 (正例の期待文書が
  production constructor 経由、集計器の非隣接対・赤分類・上限、warm-up 証跡、差分 probe の正例を実変異で) → fix 3 本 (test 1、script 2) →
  焦点再レビュー 1 本 (残 must-fix 1 = 系列文法 → fix) → fix commit `7adf2eea6` (test のみ)。凍結 S_all の 3 node が常時 skipped
  だった件は erratum 1 (走は skipped 可、対内で集合一致) で測定前に訂正した。
- 受理集合不変の証拠: 差分 probe (変更前 module を別名 import、40 状態両順序で新旧一致、M1 形の一時変異で 2 状態の不一致を検出 = 正例)、
  変異 matrix (独立 clone、probe → final の 2 段、**KILLED 8 / SURVIVED 1 (等価) / matching 9/9**、baseline PASSED)。
- A/B (段 4 §6 + erratum 1〜5 の事前登録どおり、A = base `b7f970dfa` の clean worktree、B = `7adf2eea6` の wave worktree、直接投入、
  両 tree を計算ノード collect-only で warm、2026-09-20 09:46〜13:50 JST、10 走中有効 6 走、無効 3 走は infra (投入時の他 leader 超過 /
  A 側 shard の xdist INTERNALERROR / 親の orphan-hold 解除漏れ)): **一次判定は `effect-not-established`** — 凍結 `S_all` 523 node の
  worker 秒 F は 3 対とも B が大きい (ΔF = −614 / −1315 / −1335 s)。一方、二乗回復の載る `S_mid` 65 node は 3 対とも A ≈ 400 s →
  B ≈ 123 s (ΔF_mid = +276.7 / +275.1 / +276.8 s、64〜65 node が各 ≥ 3 s 短縮) で狙った費用は消えた。B の増分は floor の snapshot 系
  19〜22 node の実 repo lock 待ちで、lock 保持者は floor file 外の `test_s8b_oracle_driver` t080 群 (shared base 構築 A 113〜164 s →
  B 189〜245 s)。output/ 残骸差と git status 所要差は除外、tree/node 起因の切り分けは診断走 (README §5.4) に載せた。判定式は結果を
  見て変えていない。
- 棄却・限界: 別 tree 比較は D2068 の同一 tree 条件を満たさない (path・pyc・page cache の差は残る)。有意差は主張しない。残る二乗成分
  (marker 読取・A ledger 全読・constructor・比較・sort、claim 数の増加) は線形化でない。lock 契約外の実行履歴同値は保証しない。
- 工数: codex 11 本 (plan 1、consult 2、author 2、review 2、fix 4、focus 1)、計算ノード job = 焦点走 3 + 変異 (probe 10 + final 10) +
  warm 2 + 測定 10 走 × 3 shard (03-A は 2 shard が SIGTERM 後も計算ノードで完走) + 診断走 4。land 調停は待ち手の post-claim merge で main を取り込み受入全走を通した。

## 次の一手差分

### 完了

- [T-2802] production `s8b_holdout_admission._floor_attempt_recovery_candidate_locked` の per-call memo (成功済み claim 射影 + main ledger
  生行列の呼び出し内共有) を実装し、受理集合不変を差分 probe (40 状態) と変異 (8/8 KILLED、等価 1 SURVIVED) で示し、受入 shard の
  隣接対 3 組で効果を記録した (一次判定は未確立、狙った費用は S_mid で 3/3 対消失、採否は README §6 の裁定パッケージ)。
  remaining: none
  base: 5ff85caef5f36dfe26585c59ad4e4a303ba8fe036f00bf367caa831fb9555a95
