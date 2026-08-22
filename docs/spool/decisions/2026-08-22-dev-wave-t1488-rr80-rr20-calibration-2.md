---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: dev-wave-t1488-rr80-rr20-calibration
seq: 2
---

## {{D:calibration-holdout-bypass}}. calibration取得はholdout保護 (T-523) の対象外とする

**決定:** rr80/rr20のcalibration取得 (証明書発行のための性能測定) は、
`orchestrator/holdout_observation.py` (T-523、commit `ebca2947`) が課すholdout保護
(rr80/rr20でのccbench実行を正式なholdout admissionなしに一律拒否する設計) の対象外とする。
専用の`CalibrationObservationCapability`(formal `HoldoutObservationAdmission`とは別型・
別registry) を新設し、`orchestrator/calibrator/cli.py`の`_certify_main`(ratio 20/80の
ときのみ) だけが発行できるようにする。capabilityはbinary_sha256・完全なgflags・numactl・
timeout・perf・extra_envを束縛し、sweep/noiseのphase状態機械 (sweepのrecords生成規則に
よる束縛、records系列の完全消費またはearly-stop最小観測数3点のいずれかでのみnoiseへ
遷移) を持つ。env非依存のjob単位durable markerでreplayを防止し、issuer呼び出し箇所を
`_certify_main`の1箇所に限定するAST meta-testを追加する。

**理由:**
- calibrationは常にrepoにpinされた単一のstock CCBench (variantではない、
  `certify_calibration.sh`がgitlink一致・pinned-clean検査を行う) の性能特性を測定するだけ
  であり、複数CC実装間の比較データ (T-523が守るholdout情報) を生成しない。
- D655/D658裁定 (rr80/rr20 calibrationの取得・登録をAI/ツールが行ってよい) とT-523保護が
  直接衝突していることが実機投入で判明し、ユーザーに確認した上でこの整理により解決した。

**却下した選択肢:**
- calibration取得を正式なholdout admission発行 (H1/H2実験相当の重い経路、campaign ledgerの
  durable-consumption経路) 経由にする — calibration専用の軽量経路と比べて過剰な設計変更に
  なり、実質的に正式実験の起票に近づいてしまうため不採用。
- T-523の保護を緩和せず、rr80/rr20の取得自体を正式なholdout解禁まで延期する — D655/D658が
  既に取得を許可しており、延期する理由がない。
- `admission=None`の既存tokenless分岐をそのまま緩めてrr80/rr20を通す — 正式H1/H2実験の
  admissionなしrr80/rr20実行と区別がつかなくなり、T-523の保護を実質的に無効化するため不採用。
