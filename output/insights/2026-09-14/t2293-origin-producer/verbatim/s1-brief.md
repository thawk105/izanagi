# 段 1 brief — [T-2293] R1/R3 の producer 層 (8c 起点試行)

wave: dev-wave-t2293-origin-producer / branch: worktree-dev-wave-t2293-origin-producer
base: d9bbdb6b09f4f63e8484e5dae9b0359208b2c49a (local main、clean、submodule 再帰初期化済み)
実装 worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-origin-producer

## 研究前進

論文主張 B-3 (8c 正式系列「セッション非依存な駆動で workload 特化合成が回る」) の土台。止めている実測は
**起点試行の 33 本の物理 campaign run を実行する production コードが 1 行も存在せず、R1 の envelope 束縛も
R3 の `execution-provenance/v2` も test fixture でしか発火しないこと**。最小差分は origin executor 1 本
(設計 §J 受入要件 12) を置き、そこで出た証拠を実運用 consumer (`evaluate_formal_origin`) が読む形にすること。
完了判定 = fixture builder が作った 33 root を 1 つも使わず、production コードが書いた証拠だけで
formal consumer が終端 (`P6Unavailable` 到達) まで進むこと。

## 成果物影響 (DW-G05)

放置すると、起点試行の formal terminal は **呼び手が手渡した `result_record_bytes` で成立しうる**。
これは設計 §10 が却下した「issuer 文字列を権限証明にする」自己申告型の恒真化と同型で、P6 の判定が
実行と無関係になる。本 wave は受理集合を**狭める** — 呼び手申告の証拠経路を塞ぎ、実行が書いた証拠だけを
受ける。certified 選択・材料レポート・試行台帳の**現在値は 1 つも変わらない** (発行 3 条件 0/3、
本番 authority 0 件)。この点は正直に名乗る。

## 確定済みユーザー裁定 (前提、覆さない)

- D1667 (R1 = lifecycle start の起点専用 optional key `origin_run_plan_sha256`)。
- D1669 (R3 = `execution-provenance/v2` 新設、起点 consumer は v2 だけ受理、v1 decoder は作らない)。
- D1670 (R4 = §G の 3 写像は既裁定の範囲内)。D1616 (V-8 (a) 1 query ordinal = 1 campaign run)。
- D1745 / D1746 / D1747 (契約側の是正: loader の射程、失敗終端の緩和、consumer は錠前の場所を計算する)。
- D1809 / D1853 (result-evidence producer core API と `run_campaign()` への per-result 配線、名乗りの上限)。
- D1530 (受理判定の権威束縛は本番の呼び手を繋ぐ変更と同じ単位で行う) — 依頼文の「同じ変更単位」の根拠。

## brief 前の実測で判明した、依頼の前提を覆す事実 (段 4 で再裁定する)

依頼は「R1 と R3 の producer 層を設計・実装する」だが、**producer 関数は既に実在する**。

1. R1 の producer は `p3_autonomous_workload_trial.run_trial` L4890-4941 に実在 (envelope を create-only で
   書き、sha256 を `record_trial_start_once` へ渡す)。
2. R3 の producer は `reflux_result_evidence.issue_campaign_result_evidence` L1196-1341 に実在し、
   `loop.run_campaign` が `result_evidence_context` 非 None のとき per-result で呼ぶ (loop.py L681/L828)。
3. **欠けているのは 33 本を実行する executor。** `_execute_origin_topology` は repo に不在 (grep 0 件)。
   `origin_runtime.campaign_runs` は envelope 構築と consumer への digest 供給にしか使われない。
4. **証拠は呼び手が手渡している。** `OriginProducerInputs.result_record_bytes` (L462-473) を
   `_complete_origin_runtime` (L1840) が `evaluate_formal_origin` へ渡す。33 物理 root・`campaign.lock`・
   `reports/execution-provenance.json` を作るのは `orchestrator/tests/reflux_origin_fixture_builder.py`。
   既存 test は `_run_workload` を monkeypatch する (test_p3_autonomous_workload_trial.py L11116)。
5. 非 test の呼び手は `run_origin_trial` が 0 件、`result_evidence_context` を渡す caller も 0 件。

したがって本 wave の「producer 層」は **(3)(4) を閉じること**と読み替える。(P1)。

## scope

- **S1 (executor)**: `_run_workload` の generation loop と**排他**の origin executor を置く。各 q で
  `exploration_campaign_layout(identity_q, campaign_output_root)` → `_assert_fresh_campaign_state` →
  `_assert_resume_allowed` → `run_campaign(cfg_q, [genome], ..., result_evidence_context=ctx_q)` →
  actual (`CampaignSummary.campaign_id`) と plan の一致 → 残時間 (`ReservationCheck.ensure_remaining`) を掛ける。
  plan からの複写を actual にしない。
- **S2 (証拠の出所を実行へ移す)**: 各 q で issue された result-evidence record を **disk から読み**、
  `_complete_origin_runtime` がそれを `evaluate_formal_origin` へ渡す。
  `OriginProducerInputs.result_record_bytes` の呼び手申告経路は塞ぐ。
- **S3 (R1 の束縛を実行に効かせる)**: executor は envelope の `planned_campaign_run_identity` 33 件と
  実際に実行した identity の全件一致を要求する。不一致・重複・欠落は fail-closed。

## scope 外 (実装せず、構造化して返す)

- `run_origin_trial` の production 呼び手 (D1853 が却下済み。4 障害 = `main()` の fixture provider real build
  拒否 / `--no-build` 経路 / `generations == 2` 制約 / completeness の origin 分岐)。
- R2 (起点専用 completion)・受入要件 18 (completeness の origin 分岐と origin report)。
- ledger producer FSM、witness normalizer、材料レポート renderer。
- 33 本の実走 (33 × 374〜908 s、T-2261 実測)。本 wave は経路を置くまでで、実走は名乗らない。
- 仮想リスク向けの gate・検査・台帳・一般化 (依頼文の明示指示)。

## 不変条件

- 規律 2: anomaly を検出した variant の即 reject を緩めない。executor の検査を「通しやすく」しない。
- originless 経路の bytes・受理集合は不変 (設計 §6.5 の projection 規律)。既定 caller は無変更。
- 名乗りの上限 (D1853 を継承): 「8c を結線した」「本番で 33 本を回した」「発行 3 条件が進んだ」とは言わない。
- 実装面は Codex `role=author` が書く (D95)。親は docs 本文だけ編集する。
- `loop.py` / `pipeline.py` は enforcement source closure に載るため変異登録から外す (F923)。

## 凍結 bytes の pin 閉包 (DW-O09 / DW-O10)

- `orchestrator/tests/reflux_origin_fixture_baseline.json` — fixture builder の出力を固定する凍結 snapshot。
  pin 元は `reflux_origin_fixture_builder.py:40`。**fixture builder の出力形を変えるなら独立再計算が要る。**
- `orchestrator/tests/test_reflux_result_evidence.py:24-27` の 64 桁 hex literal 4 件。
- `orchestrator/tests/acceptance_duration_ledger.json` — 新規 test 関数は正本 producer で追記が要る。
- producer が書く file 種 (DW-O10): q ごとの campaign layout root、`campaign.lock`、WAL、
  `reports/ordered-wal-projection.json`、`reports/execution-provenance.json`、result-evidence record、
  および trial 単位の `origin/recovery-envelope.json`、lifecycle 行、attempt registry。

## gate 入力の実在 (DW-O13、実測済み)

`CampaignSummary.campaign_id` / `.layout_root` (loop.py L62-63)、`ReservationCheck.ensure_remaining`
(reservation.py L105)、`_assert_fresh_campaign_state` (p3_autonomous L551)、`_assert_resume_allowed`
(p3_s4_loop_trigger_gating L475)、`exploration_campaign_layout` (layout.py L589)、
`ResultEvidenceIssuanceContext` の 15 field (reflux_result_evidence L240-254) はいずれも実在する。

## 生死確認 (DW-G01)

33 本の executor を書く前に、**q = 0,1 の 2 本**で「異なる layout root が立ち、各々に
`reports/execution-provenance.json` が production 経路で書かれる」ことを最小 test で確かめる。
立たなければ executor 本体を書かずに止め、何が立たなかったかを返す。

## 成果物の形

コード + テスト (実装子)、insight (親)、worklog / decisions の spool fragment (親)。
実装面の file: `orchestrator/campaign/p3_autonomous_workload_trial.py` を中心に、必要なら
`reflux_formal_consumer.py`。`loop.py` / `ident.py` / `model.py` / `s8b_*` / `campaign_claim.py` は変更しない。

## 並列分割方針

段 5 は排他所有で 2 単位に割る。単位 A = executor 本体 (`p3_autonomous_workload_trial.py` の
origin executor と runtime 配線)。単位 B = 証拠の出所移行と consumer 側の受け口
(`_complete_origin_runtime` と `OriginProducerInputs` の縮小、対応 test)。同 file を触る場合は
単位 A を先に land させ、単位 B を継続子にする。

## 受入・実測環境

受入全走は login node の `tools/dev_wave_wait.py acceptance`。計算ノード dispatch は行わない
(実走は scope 外)。所在の正本 = worklog、機体固有 = `docs/pegasus-runbook.md`。
