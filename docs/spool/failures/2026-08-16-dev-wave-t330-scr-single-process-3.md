---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t330-scr-single-process
seq: 3
---

## 新規

### {{F:floor-claim-identity-not-protocol-scoped}}. `single_process` を名乗る床値 claim が、同一 protocol の二重投入を排除しない [恒真ゲート]

- 事象: (2026-08-16、静的検査) 床値 campaign は `isolation_policy.single_process` が真のとき
  claim を取得するが、その claim identity は `_fresh_run_id(protocol_sha256, started_at)` =
  **秒精度の UTC 時刻 + protocol hash 先頭 8 桁**である
  (`orchestrator/campaign/s8b_floor_campaign.py:4235-4239`, `:4618-4619`)。
  `O_EXCL` が排他するのは同一 identity のファイルだけなので、**同一 protocol を別の秒に投入した
  2 job は別 claim を取得し、同時に走れる**。
- 根本原因: 排他の単位を「campaign の同一性 (protocol)」ではなく「この run の識別子」に取った。
  `orchestrator/campaign/campaign_claim.py:167-174` の docstring 自身が
  「clone ごとに別 out_root を与えた実行同士はこの leaf では排他できない」と明記しており、
  同一 out_root でも identity が秒で分かれる以上、同じ穴が out_root 内にも残っていた。
  あわせて `orchestrator/campaign/reservation.py:218-270` は現在の `PBS_JOBID`・boot ID・時刻・
  残容量しか照合せず、現在 hostname・実行 script SHA・submission nonce を検証しない。
  claim には未検証の `binding.host` が転記される (`s8b_floor_campaign.py:4253-4262`)。
- 影響: 単独性の主張が計測値の proof chain 上で成立しない。ただし本 wave は二重投入が実際に
  起きた記録を発見しておらず、**既存の床値値を疑わしいとは主張しない**。
  単独性の実効的な担保は現状 runbook の手続 (計測ノード上での `pgrep` 確認) 側にある。
- 恒久対応: **未実施。** claim identity を protocol 単位へ変える案と、reservation を
  scheduler 所有の create-only receipt から照合する案を再裁定へ返した
  (材料 = `output/insights/2026-08-16_t330-scr-single-process/s4-adjudication.md` の決定 3)。
- 再発検知: 「単独性」「single process」を名乗る排他が、campaign の同一性ではなく
  run 単位の識別子 (時刻・PID・UUID) を key にしていること。

### {{F:loop-sink-declares-single-process-without-enforcement}}. 計測 sink が `single_process` / `allow_resume=False` を宣言だけして一度も強制しない [恒真ゲート]

- 事象: (2026-08-16、静的検査) `orchestrator/campaign/loop.py:61-89 _authorize_measurement` は
  required attestation を最初の書込みより前に発火させる一方、claim 取得・reservation 検査・
  `allow_resume=False` の拒否をいずれも行わない。Pegasus 契約は
  `single_process=True` / `allow_resume=False` を宣言している
  (`orchestrator/campaign/env_contract.py:245-253`)。
- 根本原因: 宣言 (env 契約 registry) と強制 (sink) を別レイヤに置いたまま、強制側の実装が
  「発火する caller が無い」という理由で見送られ、その後に caller 側だけが 8c live pilot として
  実装された。宣言は契約 hash に載るため、**強制の不在は台帳からは見えない**。
- 影響: 8c live pilot の transport 欠陥が解消した時点で、この sink は単独性を一度も検査しないまま
  exploratory の WAL・report・binary SHA・throughput を受理し始める。certified 選択・材料レポート・
  proof chain・凍結 bytes は現時点では不変である。
- 恒久対応: **未実施。** `contract.isolation_policy.single_process is True` のときだけ発火する
  sink-local な強制を入れる案を、2026-08-03 の「発火 caller を持たない部分実装は採らない」という
  裁定の明示解除とセットで再裁定へ返した
  (材料 = `output/insights/2026-08-16_t330-scr-single-process/s4-adjudication.md`)。
- 再発検知: 環境契約が bool を宣言しているのに、その field を読む production consumer が
  dataclass 定義とテスト以外に存在しないこと。

## 再発

### F57

- **再発: 2026-08-16** — docs-only wave の受入全走 (request 912424、計算ノード 48 worker、
  11,224 items、152.97 秒) が `test_codex_worker_launch.py` の 2 node
  (`test_cli_reported_running_max_latches_usage_rollback`、
  `test_fake_can_reproduce_thread_id_change_and_multiple_sessions`) で赤になった。
  前者は `cli_reported` が 1000 でなく 0、後者は `codex_exit_code=-9` /
  `wall_clock_s=1.08` で、いずれも本エントリが「未確定」として挙げた **fake の既定 wall 上限 3 秒**
  と整合する。本 wave の差分は docs のみ (spool fragment 3 件と output/insights) で当該 test file に
  1 行も触れていない。計算ノードでの単独再走 (request 912438) が 3 node まとめて
  **3 passed / 3.27 秒**で緑になり、非帰属と判定した。

### F306

- **再発: 2026-08-16** — 上と同じ受入全走で
  `test_dev_wave_wait.py::test_public_main_failure_restores_handler_without_release` が
  同時に赤になった。2026-08-15 の再発と**同一 node** である。単独再走は上記のとおり緑。
  待ち手の非帰属 checker は今回も 3 件すべてを `attributable` と分類した (rc=70) — docs-only の
  差分でも `attributable` になる経路は塞がれていない。
