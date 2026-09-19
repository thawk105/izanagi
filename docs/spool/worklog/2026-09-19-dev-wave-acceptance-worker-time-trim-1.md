---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-acceptance-worker-time-trim
seq: 1
title: 受入 worker 時間を s8b builder の disk memo と preflight の小 repo 入力で削った (コード + docs、branch worktree-dev-wave-acceptance-worker-time-trim)
---

## 本文

- ユーザー依頼: 受入台帳の上位 6 file (t080 e2e を除く) の worker 時間を、受理集合・assertion・hold・成分粒度を変えずに局所修正 4 型だけで削る。効果は同 job A/B、変異 matrix で kill 集合同一。目標値は置かない。
- 段 1 は計算ノードで実測 (login の `/tmp` fsync 30 ms/回で歪むため打ち切り)。費用は ratified_verify = 同一入力の再構築、preflight = 実 repo 走査、floor = production の二乗 ledger 回復 + 実 repo 走査、p3_b4 = production ScratchTree + subprocess、codex_ab/t1259 = worker ごとの module fixture。
- 実装は U1 (s8b builder の session basetemp 下 disk memo、fork 子でも残る) と U3/R (preflight 9 関数 18 node の fingerprint 入力を小 repo へ) の 2 単位。U2 (floor digest 共有)、U3/A (codex_ab)、U4 (p3_b4)、t1259 は相談・裁定で不採用 (残る律速として insight に記録)。D2068 の 3 案は提示せず。
- 計画 1・相談 2・author 2・レビュー 2・fix 3 (U1 2 巡)・焦点再レビュー 1。レビュー must-fix 4 (decorator 欠落は親の指示ミス、session 境界、報告の言い方、A/B script)、should 3。fix 1 巡目の path 形の締めで V が 416 s へ戻る回帰を focus2 で捕捉し、2 巡目で key による session 分離へ変更して解消。
- 焦点走 (計算ノード、同走): focus3 1159 passed / 0 failed。統合 commit `ecff42ec6` (test 2 file のみ)。full provenance 監査 11,631 件・新規違反なし。
- A/B (同 job、bnode012、4 対): V −620.6 s、R −208.3 s、6 file 合計 −917 worker 秒 (中央値、幅 −681〜−993)、無変更 4 file は走間変動内。変異 matrix: 7 変異の失敗 node 集合が修正前後で一致 (差は新正例 1 node)。受入全走は記録 commit 後に投入 (受領証は land の受領証と job dir)。
- 一次資料: `output/insights/2026-09-19/acceptance-worker-time-trim/README.md` と同 `verbatim/`。専用 handoff は repo 外 job dir の `HANDOFF.md`。dev-wave 改善候補は記録のみ。

## 次の一手差分

### 新規

- {{T:floor-attempt-ledger-recovery-quadratic}} **P2・新規**: `orchestrator/campaign/s8b_holdout_admission.py` の attempt ledger 回復 (`_floor_attempt_recovery_candidate_locked`) が attempt 数に対し二乗 (test_s8b_floor_campaign.py の約 90 node × 5.8 s = 受入 worker 時間の主因、profile は insight 参照)。production 側の改善は受理集合を変えないことを変異で示したうえで別 wave。
