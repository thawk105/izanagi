# [T-330] — `/scr` fresh namespace と `single_process` 強制の前提を現行 main で測り直す

wave: `dev-wave-t330-scr-single-process` / 2026-08-16 / branch
`worktree-dev-wave-t330-scr-single-process` / 基準 commit `330f67d0`

## この材料が答えたこと

依頼は [T-330] (裁定択 (a) = `/scr` fresh namespace と `single_process` 強制を、使用権を供給する
wrapper の新設とセットで実装する) の実装であり、あわせて「裁定は 2026-08-03 と古いので、まず現行
main で前提が生きているかを実測せよ。失効していたら実装差分ゼロで裁定へ返してよい」という
条件が付いていた。

**実装は行わなかった。** 実装差分ゼロで再裁定へ返す。理由は「不要になったから」ではなく、
**裁定 (a) が指定した形の受入条件 (caller が実在することをテストで固定) が現行 main では
満たせない**からである。判断の全文は `s4-adjudication.md`。

## 構成

- `brief.md` — 段 1 brief (前提実測を含む)。親の誤り 3 件はここに残っている。
- `brief-addendum.md` — 段 2 投入後に見つけた F319 の実測を段 3 の両レンズへ渡した追補。
- `s4-adjudication.md` — 段 4 裁定 (本材料の結論)。
- `verbatim/s2-plan.md` — 段 2 codex プラン (結論 X)。
- `verbatim/s3-lensA.md` — 段 3 敵対レンズ A (「X は誤り」側)。
- `verbatim/s3-lensB.md` — 段 3 敵対レンズ B (「Y は誤り」側)。

## 主要な実測 (すべて静的検査。計測ジョブは投入していない)

- **裁定当時の「使用権を供給する wrapper が存在しない」は床値経路では失効している。**
  `tools/pegasus/submit_floor.sh:403-432` が claims/ を create-only 0700 で事前 provisioning し、
  `tools/pegasus/floor_campaign.sh:733-` が `IZANAGI_RESERVATION_*` 8 値を export する。
  強制も発火済みで、`orchestrator/campaign/s8b_floor_campaign.py:4236-4273` と
  `s8b_oracle_driver.py:1026-1037` が claim を取得し、
  `orchestrator/qualification/t126_driver.py:886` が `single_process is not True` を拒否する。
- **ただし D125 決定 (5) の対象は床値ではなく `campaign.loop.run_campaign` である。**
  `orchestrator/campaign/loop.py:61-89` は required attestation を発火させるが、claim 取得・
  reservation 検査・`allow_resume=False` 拒否をいずれも行わない。
- **`run_campaign` へ到達する compute caller は repo 外に実在する。**
  `/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1097-s8c-live-abc/live/live.pbs:145-154` が
  計算ノードで `p3_autonomous_workload_trial` を起動する。request 911106 は D122 transport
  admission で停止し role attempt 0、`run_campaign` 到達 0 だった。untracked の wave 専用 job
  script であり、tracked なテストで固定できない。
- **`/scr` へ cache_root を移す案 (S4) は現行の正しい設計ではない。** 床値 wrapper は依存を
  `/scr/${PBS_JOBID}` へ build して `CMAKE_PREFIX_PATH` へ export し、v2 build identity が
  dependency prefix を path 要素として束縛するため、床値経路は durable cache root でも
  実質 job ごとに cold である。また S4 は F319 (third-party source cache の ignored 生成物 71 件)
  を閉じない — 対象の root が違う。
- **床値の claim identity は秒精度の run ID であり、protocol 単位の排他ではない (新発見)。**
  `s8b_floor_campaign.py:4235-4239` と `:4618-4619`。`campaign_claim.acquire_claim` の docstring
  自身が「別 out_root を与えた実行同士は排他できない」と明記する (`campaign_claim.py:167-174`)。
- **dispatch は計測経路ではない。** `tools/pegasus/dispatch_compute.py` の `TASKS` は `tests` と
  `provenance` の 2 種のみで、冒頭 docstring が「certification submitter は置き換えない」と明記する。
- **8c 事前登録 C12 の機械評価器は休眠している。** `machine_checkable` が false のため
  `_evaluate_c12` は走らず、現況値は EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable
  (`orchestrator/tests/test_s8c_preregistration_predicates.py` の 2 node を実走して確認)。
  なお契約が名指しする `reservation.single_process_required` という関数は実在せず、
  現行の名前は `is_reservation_required` である。

## 模擬と実の差 (F29)

本 wave は静的検査と repo 内テスト 2 node の実走だけで、PBS job・build・計測を一切走らせていない。
`live.pbs` の内容と request 911106 の journal は読んだが、外部 artifact の権威性は検証していない。
