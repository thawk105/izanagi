## 総括

P1 は条件付き採用です。新規の再利用可能な SPRT/ledger module と、既存 S8a 評価器を呼ぶ薄い opt-in driver の分離は妥当です。ただし同じ wave で実際の Layer 3 promotion consumer まで配線しない構成は不採用です。

P2 は次の二段階裁定が必要です。

- コード実装の受入としては、全 256 系列列挙・実 WAL fixture・consumer/mutation 検査で進められる。
- production-ready / T-126 完了としては、設計 §8 の実測 positive control を省略できない。省略する場合は `implemented-but-unqualified` とし、headline gate の運用開始を保留する。

現ホストは Pegasus login node で scheduler allocation がなく、重い性能測定は禁止されています。また Pegasus は `allow_resume=false` のため、時間窓を跨いで再開する初期 T-126 driver の対象環境にはできません。[runbook §7](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/pegasus-runbook.md:252) [env contract](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/env_contract.py:169)

実装・編集・pytest 実行は行っていません。worktree は clean です。

## 現行配線の判定

実在入力は成立しています。

- baseline は `41b196c96428` (`g_lc+rt`)、variant は `e932c4502198` (`g_rt`) です。[provenance](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/reports/s8a_trigger_sweep_provenance.json:36)
- median は 930,077 → 961,862、相対差は +3.417%、各 reps=5 は完全分離し、両 COMMIT が `verify_configs=["legacy","s2"]` です。[variant WAL](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/runs/wal.jsonl:19) [baseline WAL](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/runs/wal.jsonl:31)
- D19 の保守 floor 3% に対し 3% < 3.417% ≤ 4.5% なので `near_floor=True` です。[stability.compare](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/calibrator/stability.py:223)

現状の穴は明確です。

- `p2_2_report` は `near_floor` を警告文へ出すだけで、promotion を拒否しません。[比較生成](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/p2_2_report.py:149) [警告表示](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/p2_2_report.py:166)
- `backoff_repro` は固定 config で 1 campaign を一度走らせるだけです。[driver](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/backoff_repro.py:89) 同じ identity を反復すると `run_campaign` の terminal skip に入ります。[terminal replay](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/loop.py:76)
- Layer 3 v2 は材料射影で、比較・series・promotion field を持ちません。[builder](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/layer3_report.py:314) schema も `additionalProperties:false` の閉じた v2 です。[schema](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/layer3_schema.json:5)

## End-to-end 実装 plan

配線は次の一本に限定します。

```text
s8a_seqstop.main
  → source campaign を厳密読込
  → stability.compare で near_floor を再計算
  → series identity / ledger を open
  → round_started を先行追記
  → S8a _eval_one × 2
      → run_campaign
          → full pipeline.evaluate
  → round WAL を厳密再照合
  → round_observed を追記し SPRT を再計算
  → layer3_promotion.require_promotable
```

### 1. 再利用 module

新規 `orchestrator/campaign/sequential_stopping.py` に以下を置きます。

型:

- `SprtPolicy`: `p0=.5, p1=.9, alpha=.1, beta=.1, max_rounds=8`
- `SourcePairRef`: source campaign/lock/WAL record refs、向き付き pair
- `SeriesSpec`: floor、比較 alpha/margin、policy、order seed、30分間隔、env/perf/verify、adapter version
- `RoundPlan`
- `RoundStarted`
- `RoundObservation`
- `SeriesState`

主関数:

- `decide_prefix(bits, policy)` — 副作用なしの SPRT
- `canonical_series_bytes()` / `series_id()`
- `round_campaign_config()`
- `append_event()` / `load_ledger_strict()`
- `repair_unframed_tail_for_resume()`
- `replay_series()`
- `reconcile_round_wal()`

境界は設計どおり strict `LLR > ln(9)` / `LLR < -ln(9)`、Rmax 到達時は `indeterminate` とします。[設計 §4(a)](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/insights/2026-07-15_sequential-stopping-design.md:58)

### 2. production driver

新規 `orchestrator/campaign/s8a_seqstop.py` を唯一の計測 entrypoint とします。

`main()` / `start_or_resume()` は次を実施します。

1. source campaign の `campaign.lock`、provenance、WAL を厳密に読む。
2. certified な pair の `tps` から `compare()` を再実行する。CLI や ledger 内の `near_floor` boolean は信用しない。
3. `verdict in {"faster","slower"}` かつ `near_floor=True`、stable、低 abort class、legacy+S2 を満たさなければ、series directory 作成前に拒否する。
4. 一回の起動では「期限到来済みの round を最大一つ」だけ走らせる。前 round の COMMIT 時刻から 1,800 秒未満なら無書込で終了し、back-to-back を防ぐ。
5. s8a の凍結済み setup/config を import し、`_eval_one` を決定論的な順序で二回呼ぶ。

S8a candidate は同じ Genome flags に異なる source mutation を適用するため、一つの `run_campaign(cfg, [g1,g2])` にはまとめられません。実体は同じ round campaign config の下で、

- 先行 candidate: `_eval_one` → `run_campaign(cfg,[genome])`
- 後続 candidate: `_eval_one` → `run_campaign(cfg,[genome])`

の二呼出しです。[S8a `_eval_one`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/s8a_trigger_sweep.py:346) 各呼出しは既存 `run_campaign` から full `pipeline.evaluate` に到達します。[loop](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/loop.py:136)

各評価は次を保持します。

- `PerfConfig.reps=5`。[PerfConfig](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/pipeline.py:87)
- legacy + S2。[loop wiring](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/loop.py:54)
- verify 全通過後だけ BENCH/COMMIT。[pipeline verify](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/pipeline.py:537) [COMMIT](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/pipeline.py:702)
- candidate ごとの competition/admission 検査。[bench admission](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/pipeline.py:267)

### 3. series / round identity

`series_id` は以下の canonical JSON の完全 SHA-256 とします。

- source campaign-id
- source `campaign.lock` SHA-256
- baseline/variant の向き付き ID
- 両者の source BENCH_DONE/COMMIT canonical refs
- original direction、floor、MWU alpha、near-floor margin
- `p0/p1/alpha/beta/Rmax`
- order seed、minimum interval
- env tag、records/threads/extime/reps、verify configs
- adapter/schema version、S8a candidate 名と effective-reasons

round は series ID に含めず、既存 campaign identity に次を焼き込みます。

```json
"seqstop": {
  "schema": "seqstop-round/v1",
  "series_id": "<full sha256>",
  "round": 1,
  "order": ["e932c4502198", "41b196c96428"]
}
```

これを S8a の既存 `search_config` に加え、trial も `seqstop-<short-id>-rNN` とします。既存 canonicalization は nested value を含む全 `search_config` を hash します。[canonical preimage](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/ident.py:76)

### 4. ledger と resume

配置は source campaign ではなく、新規 coordinator campaign とします。

```text
output/campaigns/t126-seqstop-series-<cfg-hash8>/
  campaign.lock
  runs/
    series.jsonl
    series-run.lock
    repairs/
  reports/
    promotion.json
```

source campaign の `campaign.lock` / WAL には書きません。coordinator の新規 `campaign.lock` は `SeriesSpec` を含む `CampaignConfig` から既存 atomic identity 機構で作ります。[identity guard](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/ident.py:141)

ledger event は三種類に閉じます。

- `round_started`: round、予定 campaign-id、順序、開始時刻、env contract hash、hostname、実 boot-id
- `round_observed`: round WAL/lock hash、BENCH_DONE/COMMIT refs、両 median、signed rel、`x`、累積 LLR、停止状態
- `series_stopped`: correctness/測定不成立、boot 変更中断など、統計 observation にしてはならない終端

`round_started` の先行記録は必須です。現行 campaign WAL は boot-id を持たないため、round 完走後・`round_observed` 前の crash/rebootをこれなしでは復元できません。

writer は既存 WAL writer と同じく、`O_APPEND|O_NOFOLLOW`、regular-file 検査、`flock`、newline tail gate、short-write loop、file/dir `fsync` を持たせます。[既存 WAL append](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/wal.py:283)

strict loader は以下を拒否します。

- blank、duplicate key、unknown/missing key、non-finite value
- newline 未終端 tail
- seq/round gap、重複 start/observation
- observation のない次 round
- terminal 後の追記
- symlink/non-regular file

通常の promotion consumer は tail を修復しません。resume driver だけが series identity 照合後に未終端 bytes を receipt 付きで除去し、終端済み record は一切変更しません。

WAL 再照合は次の規則です。

- ledger に observation がある: round campaign-id/configを再計算し、strict WAL から median/rel/x/LLRを再導出。相違は `inconsistent` として停止し、ledger値を採用しない。
- `round_started` の後に両 COMMIT がある: 再計測せず WAL から `round_observed` を補完。
- 一方だけ完了・同じ boot・`allow_resume=true`: 同じ round configを `run_campaign` へ戻し、terminal variant skipを利用して欠けた側だけ完遂。
- boot が変わった、または `allow_resume=false`: session pair を混ぜず `series_stopped/indeterminate`。
- ABORT、anomaly、unstable、tps 5点未満、wrong env、legacy+S2 不足、BENCH/COMMIT median 不一致は `x=0` にせず、統計外の `indeterminate`。

### 5. promotion consumer

既存 `layer3_report.py` と `layer3_schema.json` は変更しません。historical report が generator hash を内包し、v2 schema が閉じているためです。[generator provenance](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/layer3_report.py:369)

代わりに以下を新規追加します。

- `orchestrator/campaign/layer3_promotion.py`
- `orchestrator/campaign/layer3_promotion_schema.json`

公開関数は `assess_headline()`、`require_promotable()`、`render()` とします。`require_promotable()` は boolean を返して呼び手に無視させるのではなく、拒否時に `HeadlinePromotionError` を投げ、CLI も非ゼロで終了します。

許可条件は一つだけです。

```text
source comparison が near_floor
AND ledger/WAL が完全整合
AND statistical decision == reproduced
AND observed boot-id が2種類以上
```

`not-reproduced`、`indeterminate`、`same-boot`、running、ledger欠損、tail不正、WAL不一致はすべて拒否します。新 driver は終端時にこの consumer を直接呼ぶため、書くだけの未配線 gate にはなりません。

## P1 / P2 裁定

### P1

「再利用 module + 薄い opt-in driver」は採用でよいです。ただし受理単位は以下の三点セットです。

1. `sequential_stopping.py`
2. `s8a_seqstop.py`
3. `layer3_promotion.py` と閉じた schema

1 と 2 だけでは、現行と同じ「警告はあるが promotion が通る」状態を残すため不十分です。

### P2 と実測 positive control

全系列列挙と tracked WAL は次を十分検証します。

- SPRT 算術・停止境界
- near-floor gate の実在入力
- historical WAL schema
- COMMIT/legacy+S2/identity loader
- promotion negative matrix

しかし、実際の round driver、時間分離、boot provenance、full pipeline の連続運用は検証しません。設計 §8 は実測 positive control を明記しています。[§8](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/insights/2026-07-15_sequential-stopping-design.md:187)

さらに、§8 の「floor 内の既知非再現 pair」は production entrypoint の `near_floor` admission を通りません。このため、次のどちらかが必要です。

- 推奨: 通常 entrypoint を通る「既知 near-floor かつ非再現」の pair を選ぶ。
- 別裁定: promotion を構造的に禁止した qualification-only series を追加する。

後者は現 brief の「near_floor 保守形だけ」を越えるため、本 wave に黙って追加すべきではありません。したがって P2 は「コード landing は可、production activation は positive control 待ち」が最も整合的です。実測は `linux-baremetal` で行い、Pegasus 対応は別タスクとします。

## テスト検出力の区別

| vector | 既存が覆うもの | 新規でのみ増える検出力 |
|---|---|---|
| near-floor | flag の境界と report 警告。[test_stability](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_stability.py:189) [report test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_campaign.py:2800) | production admission と promotion 拒否 |
| identity | generic campaign hash、trial/S2 分離。[identity tests](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_campaign.py:135) | series parameter binding、round/order別 campaign、旧 round 非再利用 |
| WAL | parser、append、tail repair、terminal replay。[WAL tests](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_campaign.py:438) | ledger event topology、round WALとの双方向整合、bootを跨ぐcrash |
| full evaluate | S2配線、verify後COMMIT、abort隔離。[S2 test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_campaign.py:2456) | opt-in CLIから `_eval_one → run_campaign → evaluate` に到達すること |
| report | Layer 3 strict schema、commit欠損reject。[layer3 tests](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_layer3_report.py:54) | `reproduced` 以外を headline にしない negative matrix |
| 実 WAL | bench-first の uncertified TPS隔離。[real fixture](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_bench_first_real_wal.py:46) | T-126 pair の +3.417%/p/near_floor/legacy+S2 を実 schemaで固定 |
| env | registry値、allow_resume、reservation boot照合。[env tests](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_env_contract.py:215) | dangling `round_started` の同一boot resume / 異boot拒否 |

新規 test node 候補:

- `test_sequential_stopping.py::test_all_256_sequences_pin_stop_prefix_and_oc_table`
- `::test_boundary_sequences_1100_010_1111`
- `::test_series_id_binds_every_policy_and_source_field`
- `::test_round_campaign_id_binds_series_round_and_order`
- `::test_strict_ledger_rejects_tail_duplicate_gap_and_post_terminal`
- `::test_resume_recovers_complete_round_from_wal_without_measurement`
- `::test_resume_rejects_ledger_wal_disagreement`
- `::test_round_started_preserves_boot_across_crash`
- `test_s8a_seqstop.py::test_real_c2d838b8_pair_enters_production_gate`
- `::test_driver_calls_two_full_evaluations_in_recorded_order`
- `::test_non_near_floor_and_high_abort_refuse_before_side_effects`
- `test_layer3_promotion.py::test_only_reproduced_multi_boot_is_promotable`
- `::test_negative_status_matrix_never_reaches_headline`
- `::test_missing_or_inconsistent_ledger_fails_closed`

pytest 専用にするなら [tests README allowlist](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/README.md:92) も更新します。

## Mutation 候補

- SPRT 上下境界の `>` / `<` を `>=` / `<=` に変更
- 不一致 increment を `ln(0.2)` 以外へ変更
- Rmax を 8 以外へ変更、または indeterminate を reproduced に変更
- `abs(rel) > floor` を `>=` に変更、方向検査を削除
- `series_id` から p1/alpha/beta/Rmax/order seed のいずれかを削除
- round config から `series_id` / round / order のいずれかを削除
- strict loader を prefix-tolerant `wal.read_records()` に置換
- ledger値をWALより優先
- `round_started` の boot-id記録を削除
- legacy+S2または reps=5 の照合を削除
- promotion allowlistへ indeterminate / same-boot / missing を混入
- driver の `_eval_one` 呼出しを no-op/fake result に置換

各 mutation は上記の専用 node が単独で殺せるよう対応をコメントで固定します。

## 変更候補と no-touch 境界

新規追加:

- `orchestrator/campaign/sequential_stopping.py`
- `orchestrator/campaign/s8a_seqstop.py`
- `orchestrator/campaign/layer3_promotion.py`
- `orchestrator/campaign/layer3_promotion_schema.json`
- 新規 test 2〜3本

docs 更新:

- [sequential stopping design §4/§8](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/insights/2026-07-15_sequential-stopping-design.md:58): 実装 identity/ledger schema、全系列 OC、positive-control activation条件
- [phase3 current checkpoint](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/phase3.md:19): opt-in範囲と qualification 状態
- [roadmap §3.6](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/roadmap.md:209): cross-run gate の実装済み契約
- `docs/decisions.md`: promotion allowlist、P2二段階受入、Pegasus非対応の決定
- [Pegasus runbook §7.1](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/pegasus-runbook.md:309): T-126 は `allow_resume=true` 環境限定
- `docs/worklog.md`: 実装・mutation・positive-control未実施状態

変更しない production dependencies:

- `stability.py`
- `model.py` — 保守形なので新 WAL stage なし
- `ident.py`
- `loop.py`
- `pipeline.py`
- `wal.py`
- `p2_2_report.py`
- `layer3_report.py` / `layer3_schema.json`
- `backoff_repro.py`
- `s8a_trigger_sweep.py`
- `axis_trigger_gating.py`

特に `s8a_trigger_sweep.py` と `axis_trigger_gating.py` は freeze source hash に含まれるため no-touch です。[known axes freeze](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/s1-freeze/known_axes_freeze.json:46) 既存 23 freeze artifact の bytes も維持します。[frozen manifest](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_frozen_artifacts.py:38)

また以下には一切書きません。

- `p3-s8a-trigger-sweep-balanced-sweep-c2d838b8` の全既存ファイル
- 既存 campaign の WAL / `campaign.lock`
- freeze artifact /既存 generator
- `external/ccbench` submoduleおよび gitlink