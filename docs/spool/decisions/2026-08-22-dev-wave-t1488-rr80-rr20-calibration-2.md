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

## {{D:rr80-rr20-artifacts-withheld-until-holdout-release}}. rr80/rr20 calibration 成果物は holdout 解禁まで repo へ置かない

**決定:** rr80/rr20 の calibration 取得・検証は AI/ツール経路で行ってよい (D655/D658 のまま) が、
**その成果物を tracked な repo へ置くのは holdout 解禁 (g1→g2 activation) までとする。**
本 wave は取得と実装だけを land し、成果物 142 file
(`output/env/pegasus/calibration/{attempts,job-staging}/0[_:]936025.nqsv`・同 `936044.nqsv`、
`registered/calibration-6cfeb65b12970eb6.json`・`calibration-7e2be8adff051662.json`、
`output/calibration-capability-markers/` の 2 件) を repo から除いた。
実測そのものは repo 外の
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1488-rr80-rr20-calibration/withheld-artifacts/`
に byte 同一で保全してあり、解禁後に同じ bytes を再登録できる (証明書 2 件の SHA-256 は
filename 前置語と一致することを退避時に照合済み)。

**理由:**
- T-523 の repo 全体 holdout 走査は「同一 file が rratio / skew / rmw の三軸すべてに一致したら
  1 hit」と数え、rr80/rr20 は 0 hit でなければならない。rr50 は陽性対照 (85 hit) であり、
  **calibration 成果物が走査対象に入ること自体が設計である。**
- 有効な rr80/rr20 証明書は workload descriptor を必ず含むため、**それを repo に置くことと
  repo に三軸表現が 1 件も無いことは同時に成り立たない。** 実装の欠陥ではなく、D655/D658 と
  T-523 の射程の衝突である。
- 実測: 現ツリーで rr80=5・rr20=5・FAIL、当該 10 file 除外で rr80=0・rr20=0・rr50=85・PASS。
  除去後の素の走査でも rr80=0・rr20=0・rr50=85・PASS。
- 2026-08-22 にユーザーが承認した {{D:calibration-holdout-bypass}} は**実行時 admission gateway**
  の迂回であり、repo 内容の走査はその射程に入っていない。

**却下した選択肢:**
- freeze scan に calibration 成果物の allowlist を足す — repo を読める者が rr80/rr20 の存在と
  実測特性を見られるようになり、T-523 が守ろうとしているものを直接損なう。正しさ防壁の緩和で
  あり、ユーザー裁定でも本 wave では採らないと決めた。
- D88 の可逆 defang で三軸語を無害化する — `registered/calibration-*.json` は filename が内容の
  SHA-256 前置語で published self-comparison gate も内容に束縛されるため、bytes を変えると
  証明書が無効になる。docs には使えるがこの 10 file には適用できない。
- wave 全体を解禁まで保留する — 敵対レビュー 2 本と変異 matrix 3/3 KILLED を通った実装
  (capability 機構、python3.10 interpreter 解決、perf の PATH 順序、sweep early-stop 遷移) が
  滞留し、実機で 3 回踏んだ欠陥の修正が他 wave へ効かない。
