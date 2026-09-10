## 総括

- P1 の「`:1391-1394` だけ外して既存 claim を再利用」は不十分である。finalize 側の重複拒否と、既存 claim の旧 run identity 照合でも停止する。`orchestrator/campaign/s8b_holdout_admission.py:1391-1448,1553-1599`
- P2 の「attempt ticket は無変更で残す」も成立しない。既存 run は claim 12 枚に加えて attempt marker 96 枚を残しており、cell 拒否を外しただけでは最初の実測時に再び停止する。`docs/archive/worklog-phase3-0826-965.md:14-16`
- 解決策は、cell の効果 key と測定世代 claim を分離し、`O_EXCL` と attempt 一回性を測定世代内へ限定することである。`orchestrator/campaign/s8b_holdout_admission.py:730-756,3960-3970`
- 同じ世代の同じ attempt の二重実行は引き続き拒否し、別測定世代だけを許す。これなら D893 を保ったまま D1124 を満たす。`rulings/D893.md:1-7`, `rulings/D1124.md:9-16`
- 承認 flag、Python 引数、env、ledger/result field は identifier 閉包ごと削除する。`brief.md:4-9`
- freeze、gflags、argv snapshot、run-once allowance、検証済み manifest、scheduler recovery の正しさゲートは変更しない。`orchestrator/holdout_observation.py:387-538,1155-1211`, `orchestrator/calibrator/runner.py:584-654`
- 親の裁定が要るのは旧 floor claim/receipt の live inspector 互換性と、R33 protocol pin を既存 file 上書きにするか successor file にするかの 2 点である。`orchestrator/campaign/s8b_holdout_admission.py:5129-5203`, `output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json:9-15`
- sandbox 制約どおりテストは実走しておらず、以下は静的プランである。

## 1 撤去面の閉包

### 実装・運用コードの identifier 全出現

- `orchestrator/campaign/s8b_floor_campaign.py`: `6954,6979,6981,6983,7007,7021,7075,7077,7079,7675,8196,8423-8424`
- `orchestrator/campaign/s8b_holdout_admission.py`: `370,1211,1222,1232,1245,1247,1255,1368,1507,1548,2121,3056,3058,3102,3118,3121,3269,3287,3909,3924,4075,5096,5121,5144`
- `orchestrator/campaign/s8b_oracle_n_pilot.py`: `1252,1261,1263,2323,2560,2612,2633,2647,2699-2700,2794,2861,2884,2909,2918,2952,2983,3006`
- `tools/pegasus/submit_floor.sh`: `9,33,44-45,628-629`
- `tools/pegasus/floor_campaign.sh`: `549-550,1236-1237`
- `tools/pegasus/submit_oracle_n_pilot.sh`: `11,44,106-107,151-152`
- `tools/pegasus/oracle_n_pilot.sh`: `61-66,346,360,374-375`
- `tools/pegasus/README.md`: `226,241-243`
- Oracle 側の別名 env も同じ閉包で削除する。`IZANAGI_PILOT_CONFIRM_IRREVERSIBLE_HOLDOUT` は `tools/pegasus/submit_oracle_n_pilot.sh:324`、`tools/pegasus/oracle_n_pilot.sh:61-66,374-375` にある。
- `orchestrator/campaign/s8b_holdout_freeze.py` には該当 identifier と一回性拒否はないため変更しない。

### テスト・fixture の identifier 全出現

- `orchestrator/tests/s8b_floor_evidence_fixture.py`: `193,201-202,252,270`
- `orchestrator/tests/test_pegasus_floor_tools.py`: `1964,1970-1973,1994,2042,2064,2083,2523,2536,2548,2561,2624,2647,3634,3665`
- `orchestrator/tests/test_s8b_floor_campaign.py`: `743,770,5274,6465,6518,6708,6896,6925,6935,6937`
- `orchestrator/tests/test_s8b_freeze_io.py`: `542`
- `orchestrator/tests/test_s8b_holdout_admission.py`: `240,317,493,513,541,564,578,666,876,2388,2620`
- `orchestrator/tests/test_s8b_oracle_n_pilot.py`: `301,305,307,348,358,372,396,406,414,422,432,457,460,516,883,947,967,979,985,1153,1566,1578,1617,1720,1945`
- Oracle 別名 env の pin は `orchestrator/tests/test_s8b_oracle_n_pilot.py:1938-1945` にある。

### 予約を cell の過去消費で拒否する全地点

- floor 予約本体: 既存 effect-key claim の存在拒否 `orchestrator/campaign/s8b_holdout_admission.py:1380-1394`、旧 claim の run identity 照合 `:1411-1448`、missing claim の `O_EXCL` `:1465-1484`
- floor finalize: ledger を effect key で一意化する拒否 `:1553-1571`、fresh 再利用拒否 `:1581-1598`
- oracle: ledger の effect-key 重複拒否 `:1781-1801`、claim `O_EXCL` と既存 ledger 拒否 `:1802-1813`
- R33 n-pilot: transaction 適用時の effect-key 一意化 `:2728-2757`、stage 前の ledger intersection と既存 claim 拒否 `:2981-2997`
- legacy n-pilot: ledger の effect-key 重複拒否 `:3294-3314`、claim `O_EXCL` と既存 ledger 拒否 `:3315-3326`

### attempt 一回性の全地点

- oracle: marker path と二重消費拒否 `orchestrator/campaign/s8b_holdout_admission.py:1882-1891`
- R33: exact marker key、path、ledger identity `:3359-3475`、消費時拒否 `:3598-3621`
- legacy n-pilot: marker path と拒否 `:3705-3729`
- floor: journal authorization `:3783-3823`、marker recovery と二重消費拒否 `:3826-3869`、marker exact schema/path `:3926-3970`、claim・ledger からの再導出 `:3973-4092`、marker/ledger identity の一意性 `:4095-4172`
- retry registry が要求する既消費 marker: `:4483-4518`

### exact schema key と bytes/argv pin

- floor claim/ledger/attempt key 集合: `orchestrator/campaign/s8b_holdout_admission.py:3905-3930`
- floor inspector の ledger/claim exact 検査: `:5069-5082,5105-5146,5151-5203`
- R33 receipt、cell、manifest、transaction の exact key 集合: `:2303-2325`、検査 `:2328-2442,2452-2501`
- R33 attempt marker exact key 集合: `:3359-3386`
- portable floor admission receipt の exact key 集合は承認 field を持たないため温存する。`orchestrator/campaign/s8b_floor_contract.py:66-70,357-390`
- floor submit receipt の exact top-level key は承認を含まないため温存する。`orchestrator/campaign/floor_submit_receipt.py:15-19,51-64`, `tools/pegasus/floor_campaign.sh:633-690`
- shell argv の現行 pin は `orchestrator/tests/test_pegasus_floor_tools.py:1962-2002,2060-2085`
- R33 protocol は編集対象 driver/job の bytes を固定している。`output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json:9-15`。実行時にも exact hash を照合する。`orchestrator/campaign/s8b_oracle_n_pilot.py:575-595`
- floor job bytes は submit 時と job 内で commit blob に束縛される。`tools/pegasus/submit_floor.sh:254-279`, `tools/pegasus/floor_campaign.sh:728-789`

### 文書・履歴内の出現

運用文書として改訂するのは `tools/pegasus/README.md:226,241-243` と `docs/phase3-8b-restart-runbook.md:235`。決定・worklog・過去測定 evidence は過去事実なので書き換えない。

履歴側の exact hit は `docs/decisions.md:19228-19231,37876`、`docs/archive/worklog-phase3-0816-600-601.md:1048`、`docs/archive/worklog-phase3-0817-609.md:63,78`、`docs/archive/worklog-phase3-0820-742-743.md:570-572,581,605`、`docs/archive/worklog-phase3-0827-1029.md:936`。過去 artifact 側は次のとおり。

- `output/insights/2026-08-16_t523-holdout-admission/verbatim/s6-fix-unit-b.md:12,57`
- `output/insights/2026-08-16_t1180-pilot-approval/verbatim/s2-plan.md:7,19,23,32,43,64,91-92,114`
- `output/insights/2026-08-16_t1180-pilot-approval/verbatim/s3-consult-a-sol.md:7,19,31-32`
- `output/insights/2026-08-16_t1180-pilot-approval/verbatim/s3-consult-b-luna.md:19,55`
- `output/insights/2026-08-16_t1180-pilot-approval/verbatim/s4-adjudication.md:42,54,70,97,103,112,117,121,130,132,173`
- `output/insights/2026-08-16_t1180-pilot-approval/verbatim/s6-review-a.md:21`
- `output/insights/2026-08-17_t987-floor-rebind/verbatim/s3-lensB.md:88`
- `output/insights/2026-08-20_t1142-n-pilot-r33-admission-redesign/README.md:71`
- `output/insights/2026-08-16_t1142-n-pilot-prereg/r33-qsub-procedure.md:24,39,49,59`
- floor 投入記録: `output/insights/2026-08-20_t1431-floor-pilot-measurement/README.md:19,37-38`、`2026-08-21_t1431-floor-pilot-resubmit/README.md:22,59`、`2026-08-23_t1431-floor-pilot-rerun/README.md:23`、`2026-08-25_t1431-floor-pilot-submit/README.md:24`、`2026-08-25_t1431-floor-pilot-values/README.md:15`
- 隣接調査記録: `output/insights/2026-08-21_t1461-masstree-staging-scope-finding/README.md:52`

## 2 予約拒否と台帳追記の分離

### 共通骨格

既存 effect key は cell 座標として維持する。`orchestrator/campaign/s8b_holdout_admission.py:730-748`

```python
cell_key = _key_fields(...)
measurement_generation = {
    "cell_key": cell_key,
    "reservation_id": reservation_id,
}
generation_digest = _sha256(measurement_generation)

generation_claim = {
    "schema_version": "...-cell-claim/vNext",
    "event": "observe",
    "key": cell_key,
    "reservation_id": reservation_id,
    # commit/env/ccbench/protocol/run coordinates
}
_write_exclusive(_generation_claim_path(root, generation_digest), generation_claim)

ledger_row = {
    "schema_version": "...-ledger/vNext",
    "event": "observe",
    **cell_key,
    "claim_digest": generation_digest,
    "reservation_id": reservation_id,
    # provenance
}
_append_ledger(..., [ledger_row])
```

旧 `claims/<effect_digest>.claim` は履歴として残すが、新予約の可否には使わない。新しい測定ごとに generation claim を `O_EXCL` で作る。これにより `O_EXCL` は上書き・同一世代競合の防壁として残るが、過去の cell 観測を拒否する権限は失う。D1124 の「台帳は履歴だが予約権限を持たない」に直接対応する。`rulings/D1124.md:9-16`

### floor

- `:1211-1258` の承認引数、exact bool、pilot 拒否を撤去する。
- `:1351-1370` は承認 field を除き、`campaign_run_id` と `manifest_sha256` から導いた測定世代 claim schema へ上げる。
- `:1380-1394` の「既存 effect claim があれば fresh 拒否」を撤去する。
- `:1411-1448` の旧 effect claim と current run identity の比較を、同一 generation claim を resume するときだけの exact 比較へ限定する。
- `:1465-1484` の `O_EXCL` は generation path に対して残す。
- `:1553-1599` は effect digest 一意表をやめ、`(campaign_run_id, generation_digest)` で current row を照合する。同一 resume 行は冪等、別世代は常に append とする。
- `:3905-3925,5069-5203` は承認 key を除いた次世代 exact schema に更新する。inspector は選択中 `campaign_run_id` の ledger row が示す generation claim だけを読む。
- `:4035-4056` の「effect digest に main ledger row が exact 1 件」を「marker の generation digest と campaign identity に一致する row が exact 1 件」へ置換する。全履歴で同 cell が 1 件という条件は撤去する。

### oracle

- `:1781-1801` の effect-key ledger 一意化を generation identity 一意化へ変更する。
- `:1802-1809` の既存 effect claim 拒否を撤去し、予約呼び出しごとに 1 個の `reservation_id` を発行して generation claim を作る。
- `:1810-1813` は「同一 generation ledger が claim 無しなら拒否」として残す。過去の同 cell ledger は拒否理由にしない。
- `:1814` の ledger append は毎予約で実行する。
- token state `:1828-1837` は generation digest を持たせる。

### n-pilot legacy

- `:3056-3061,3102-3124` の承認引数・拒否を撤去する。
- `:3237-3292` の claim/ledger から承認 field を削除し、予約単位の `reservation_id` と generation digest を追加する。
- `:3294-3314` の effect-key ledger 一意化を generation identity 一意化へ変更する。
- `:3315-3326` は generation claim の `O_EXCL` と同世代整合性検査だけを残し、過去 cell の存在では拒否しない。
- `:3327` は毎予約で 12 行を追記する。

### n-pilot R33

- transaction ID は既に毎予約で乱数発行される。`orchestrator/campaign/s8b_holdout_admission.py:2970-2976`。これを claim 作成より前へ移し、R33 の `reservation_id` と generation digest の構成要素にする。
- `:2082-2138` から承認 field を削除し、transaction/reservation identity を claim と ledger に記録する。
- `:2981-2997` の effect-key intersection と既存 effect claim 拒否を撤去する。重複検査は同一 transaction generation に限定する。
- transaction recovery `:2728-2758` も effect digest ではなく generation digest で index する。異なる世代 row は append し、同じ世代の conflicting bytes だけを拒否する。
- 公開 receipt の top-level/cell key 集合は変えない。既に `transaction_id`、`claim_digest`、claim/ledger hash を持つためである。`orchestrator/campaign/s8b_holdout_admission.py:2303-2313,2938-2963`
- consumption は receipt の `claim_digest` と `ledger_row_sha256` により current generation を exact に束縛したままにする。`orchestrator/campaign/s8b_holdout_admission.py:3565-3597`

### 「再利用」ではなく「新しい世代 row」を選ぶ根拠

旧 singleton claim は `campaign_run_id`、`run_relpath`、mode、protocol、attempt 集合まで含む。`orchestrator/campaign/s8b_holdout_admission.py:1351-1370`。したがって別 run がそれを再利用すると `:1446-1448` の exact identity と矛盾する。また attempt canonicalization も singleton claim の run identity を権威にしている。`:3989-4088`

このため、既存 claim を無条件再利用する P1 は採らず、新測定世代 claim を追加する。旧 claim を書き換えないので過去 provenance も保持できる。

## 3 attempt ticket の扱い

P2 はソース上、一般にも今回の 12 cell にも成立しない。

floor の cell claim digest は campaign run を含まない。`orchestrator/campaign/s8b_holdout_admission.py:730-756`。attempt ID も `cell_id::seqN` または `cell_id::retryN` だけである。`:1194-1202`, `orchestrator/campaign/s8b_floor_campaign.py:6352-6355`。marker filename はこの 2 値だけから作られる。`orchestrator/campaign/s8b_holdout_admission.py:3960-3970`

したがって現状の attempt 拒否は二つを兼ねている。

- 同じ issued reservation の同じ attempt を二度起動する場合は、D893 の reward-hack 防壁として働く。`:3826-3869`
- 別 campaign run で同じ cell を再測定する場合も同じ inode に衝突し、D1124 が撤去を命じた反復拒否として働く。`:730-756,1194-1202,3960-3970`

2026-08-24 run は claim 12 枚だけでなく consumed marker 96 枚を残した。`docs/archive/worklog-phase3-0826-965.md:14-16`。よって `:1391-1394` だけを消すと、予約後の最初の既消費 attempt で `:3861-3867` に落ちる。

分離案は durable attempt identity を `(generation claim digest, local attempt_id)` と定義すること。

- 同じ generation の二重 consume は従来どおり `O_EXCL` で拒否する。`:3853-3868`
- 新 generation は claim digest が異なるので、新 marker と ledger row を作れる。
- floor、oracle、legacy n-pilot の marker path を generation digest 基準にする。`:1882-1889,3720-3727,3960-3970`
- R33 は transaction generation を claim digest に含める。`:2938-2953,2975`
- marker/attempt-ledger の exact key、marker先行、ledger追記、run-once allowance は残す。`:3359-3475,3885-3902,3926-4092`
- completed attempt の同世代再発行拒否は残す。`:4151-4155`
- journal の canonical session-start と retry trigger 検査も残す。`:3783-3823,4483-4633`

これにより「別測定を許す」と「同一試行を複数実行先で走らせる」を分離できる。値を見た後の結果選択禁止はこの wave では変更せず、D1124 が明記する選択・proof-chain 側の義務として残る。`rulings/D1124.md:20-27`

## 4 12 cell が通ることの根拠と残る関門

### 現行の拒否列

1. `tools/pegasus/submit_floor.sh` が nonce と job script を束縛し、`qsub` argv を組む。`tools/pegasus/submit_floor.sh:305-322,627-645`
2. job が submission nonce/receipt を検査する。`tools/pegasus/floor_campaign.sh:541-555,557-698`
3. job が driver argv を構築して起動する。`:1186-1241`
4. driver parser/main が CLI を受け、`run_campaign()` を呼ぶ。`orchestrator/campaign/s8b_floor_campaign.py:8182-8199,8392-8426`
5. public wrapper が `_run_campaign_core()` へ渡す。`:6945-7008`
6. core が予約関数を呼ぶ。`:7660-7685`
7. 予約関数が同じ effect digest の旧 claim 12 件を発見する。`orchestrator/campaign/s8b_holdout_admission.py:1380-1390`
8. fresh なので `holdout cell key was already consumed by another fresh run` を送出する。`:1391-1394`

実測ログでもこの列の終端が確認されている。`docs/archive/worklog-phase3-0827-1029.md:7-20`

### 撤去後に一回性面を通る根拠

- submitter は承認 option/env を作らず、nonce だけを `qsub -v` に渡す。置換対象は `tools/pegasus/submit_floor.sh:9,33,44-45,627-630`
- job は承認 env の一致検査と driver flag append を行わない。置換対象は `tools/pegasus/floor_campaign.sh:549-555,1230-1238`
- driver parser、wrapper、core、予約呼び出しから承認値を消す。置換対象は `orchestrator/campaign/s8b_floor_campaign.py:6954-7007,7021-7083,7667-7676,8195-8198,8418-8425`
- 新 run の `campaign_run_id` は protocol hash と新しい開始時刻から作られる。`:7177-7187,7805-7814`
- この run ID から新 generation claim digest を作るため、旧 12 effect claim inode と衝突しない。
- attempt marker も新 generation digest を prefix にするため、旧 96 marker と衝突しない。
- 新 ledger row は過去 effect-key row の存在にかかわらず追記される。現行 append primitive は append-only である。`orchestrator/campaign/s8b_holdout_admission.py:1166-1191`

この変更を固定する統合テストとして、旧形式の claim 12件、attempt marker 96件、両 ledger を事前配置したうえで、新しい floor fresh reservation、finalize、最初の `consume_attempt_ticket()` まで通す `test_floor_rereservation_ignores_legacy_cell_and_attempt_consumption` を追加する。fixture の現行構築面は `orchestrator/tests/s8b_floor_evidence_fixture.py:187-309`。

### 残る別の関門

以下は一回性ではなく、変更せず残す。

- submission source の clean/tracked job-script gate。`tools/pegasus/submit_floor.sh:201-280`
- `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` の投入前 gate。`:340-398`
- staged third-party payload の pin/clean 検査。`:408-520`
- qsub 自体、request ID、submit receipt の成立。`:642-715`
- PBS site、policy、job receipt exact schema、source commit/job bytes の照合。`tools/pegasus/floor_campaign.sh:19-43,466-539,610-698,728-799`
- scheduler の allocation、host、start、10h elapse の照合。`:804-976`
- gflags/glog の pinned-clean build。`:1015-1113`
- current protocol resolver。`:1186-1212`
- protocol current generation、environment contract、calibration、execution receipt。`orchestrator/campaign/s8b_floor_campaign.py:7119-7153`
- freeze type、bytes hash、schema、cell/schedule 再導出。`:7098-7099,7160-7176`
- scheduler reservation budget と submit receipt binding。`:7199-7237`
- durable output root と live campaign claim。`:7239-7286`。これは同時実行排他であり、終了後の再測定回数を数える cell 台帳ではない。
- perf preflight、build、ccbench pin、binary receipt、manifest。`:7312-7455,7653-7658`
- runner 内の live admission、host/process provenance、single-tenant/competition、journal state。`:6276-6349`
- commit、node、時刻の記録は admission ledger の `measurement_head/env_tag/ccbench_pin/protocol_sha256` と、campaign journal の hostname/job/UTC に残る。`orchestrator/campaign/s8b_holdout_admission.py:1532-1551`, `orchestrator/campaign/s8b_floor_campaign.py:1744-1752,6280-6307`
- `--flagfile`、`--fromenv`、`--tryfromenv`、非canonical protected argv、`FLAGS_` env 除去、run-once allowance は温存する。`orchestrator/holdout_observation.py:241,387-538,1155-1211`, `orchestrator/calibrator/runner.py:609-654`
- attempt registry と scheduler accounting は retry のときだけ使う。planned start は registry 分岐前に返る。`orchestrator/campaign/s8b_holdout_admission.py:3809-3823`。retry では authority pin、receipt exact bytes、budget、registry replay をすべて残す。`:4292-4479`
- floor official の `_assert_official_permitted` と人間の budget approval は変更しない。`orchestrator/campaign/s8b_floor_campaign.py:453-462,8394-8401`, `rulings/D1161.md:1-10`

したがって静的に保証できるのは「cell/attempt の過去消費だけを理由とした停止が消える」までである。scheduler、予算コマンド、calibration、build 等の実環境 gate が実際に通るかは、親による P4 の実 qsub で確認が必要である。`brief.md:48-52`

## 5 テスト改訂面

### 「2度目の予約拒否」を固定する既存テスト

- **反転** `orchestrator/tests/test_s8b_holdout_admission.py:269-279`  
  `test_two_worktrees_parallel_fresh_runs_cannot_both_claim_the_same_keys` を、両 run が admitted、generation claim が 24 件、ledger が 24 行になることへ反転する。同時実行の cell 観測を許すだけで、同一 generation attempt の一回性は別テストで維持する。
- **反転** `orchestrator/tests/test_s8b_holdout_admission.py:882-893`  
  `test_protocol_master_seed_change_does_not_reset_cell_key` を、effect key は同一のまま別測定世代が予約・追記できることへ反転する。freeze/key exactness は `:321-371,1112-1268` のテストを温存する。
- **反転** `orchestrator/tests/test_s8b_oracle_driver.py:5702-5746`  
  同じ verified manifest/block の 2 回目予約が通り、別 generation digest を持つことへ反転する。verified manifest、schedule、reps の拘束は同テスト前半 `:5702-5738` を維持する。
- **温存** `orchestrator/tests/test_s8b_floor_campaign.py:5283-5331`  
  これは durable cell 一回性ではなく、同時 live campaign owner の排他 `campaign_claim.acquire_claim()` を固定している。規律1の観測環境分離なので弱めない。

### attempt 一回性テスト

次は削除しない。generation scope に期待値を更新するだけである。

- `orchestrator/tests/test_s8b_holdout_admission.py:550-601` — 同じ legacy n-pilot token の同一 attempt は二重消費不可。
- `:1457-1471` — 同じ floor generation の同一 attempt は二重消費不可。
- `:1526-1537` — M+A+ は新 marker を作らず拒否。
- `:1591-1607` — completed attempt の同世代再発行不可。
- `:1610-1644` — measure callback crash 後に同一 issued attempt を再実行不可。
- `:1474-1506,1540-1588` — cut-6 の marker先行、ledger recovery、exact marker 再導出を維持。
- R33 に同じ receipt/global index の二重消費拒否テストを追加する。現行拒否実装は `orchestrator/campaign/s8b_holdout_admission.py:3613-3621`。

### 承認 closure のテスト

- **削除または不存在テストへ置換**: `orchestrator/tests/test_s8b_holdout_admission.py:498-547,855-879`、`orchestrator/tests/test_s8b_floor_campaign.py:6835-6843,6932-6937`、`orchestrator/tests/test_s8b_oracle_n_pilot.py:291-307,446-452,974-1007`
- **mechanical call-site 更新**: `orchestrator/tests/test_s8b_floor_campaign.py:734-770,5274,6515-6519,6892-6926`、`orchestrator/tests/test_s8b_freeze_io.py:531-543`、`orchestrator/tests/test_s8b_holdout_admission.py:230-240,482-495,550-578,646-666,2381-2389`
- **result/schema 更新**: `orchestrator/tests/test_s8b_oracle_n_pilot.py:923-949,1541-1583,1586-1619,1690-1724`。承認 field だけを除き、receipt、manifest、schedule、allocation、perf、holdout admission identifier の検査は維持する。
- **shell dataflow テスト削除・argv 固定へ統合**: `orchestrator/tests/test_pegasus_floor_tools.py:1962-2002,2060-2085,2519-2653,3631-3685`
- 新しい `test_removed_irreversible_confirmation_identifiers_are_absent` で、実装・shell・active README に指定 5 identifier と Oracle 別名 env が 0 件であることを固定する。
- fixture は承認引数・field を消し、次世代 generation claim/ledger/attempt schema を正例にする。`orchestrator/tests/s8b_floor_evidence_fixture.py:187-309`
- 旧 v1/v2 inspector テスト `orchestrator/tests/test_s8b_holdout_admission.py:2592-2621,2694-2719` は、親が旧 live inspection 互換を不要と裁定する場合、新 schema の exact/tamper テストへ置換する。claim tamper、未知 schema、extra key 拒否そのものは弱めない。

## 6 変異事前登録の候補

1. 対象 `orchestrator/campaign/s8b_holdout_admission.py:1391`  
   変異: 旧 effect claim が存在したら fresh を拒否する分岐を復活。  
   kill: `orchestrator/tests/test_s8b_holdout_admission.py::test_floor_rereservation_ignores_legacy_cell_and_attempt_consumption`

2. 対象 `orchestrator/campaign/s8b_holdout_admission.py:1555-1599`  
   変異: ledger を再び effect digest で一意化する。  
   kill: `orchestrator/tests/test_s8b_holdout_admission.py::test_floor_fresh_rereservation_appends_generation_rows`

3. 対象 `orchestrator/campaign/s8b_holdout_admission.py:1803-1809`  
   変異: oracle generation path を effect claim path に戻す。  
   kill: `orchestrator/tests/test_s8b_oracle_driver.py::test_oracle_repeated_reservation_is_admitted`

4. 対象 `orchestrator/campaign/s8b_holdout_admission.py:2981-2997`  
   変異: R33 ledger intersection による過去 cell 拒否を復活。  
   kill: `orchestrator/tests/test_s8b_holdout_admission.py::test_r33_repeated_reservation_uses_new_generation_receipt`

5. 対象 `orchestrator/campaign/s8b_holdout_admission.py:3315-3322`  
   変異: legacy n-pilot claim を effect digest の singleton に戻す。  
   kill: `orchestrator/tests/test_s8b_holdout_admission.py::test_legacy_n_pilot_repeated_reservation_is_admitted`

6. 対象 `orchestrator/campaign/s8b_holdout_admission.py:3960-3970`  
   変異: floor marker filename から generation digest を除き、旧 effect digest に戻す。  
   kill: `orchestrator/tests/test_s8b_holdout_admission.py::test_floor_attempt_single_use_is_scoped_to_measurement_generation`

7. 対象 `orchestrator/campaign/s8b_holdout_admission.py:1882-1889`  
   変異: oracle attempt marker を generation 非依存に戻す。  
   kill: `orchestrator/tests/test_s8b_oracle_driver.py::test_oracle_attempt_single_use_is_scoped_to_measurement_generation`

8. 対象 `orchestrator/campaign/s8b_holdout_admission.py:3861-3867`  
   変異: 同じ generation の既存 marker を無視して再発行する。  
   kill: `orchestrator/tests/test_s8b_holdout_admission.py::test_attempt_ticket_is_durably_single_use`

9. 対象 `orchestrator/campaign/s8b_holdout_admission.py:1599`  
   変異: 既存 effect key がある場合は新 ledger row を append しない。  
   kill: `orchestrator/tests/test_s8b_holdout_admission.py::test_floor_fresh_rereservation_appends_generation_rows`

10. 対象 `orchestrator/campaign/s8b_floor_campaign.py:8195-8198`  
    変異: 削除した confirmation CLI option を復活。  
    kill: `orchestrator/tests/test_s8b_floor_campaign.py::test_removed_irreversible_confirmation_identifiers_are_absent`

すべて ASCII の nodeid であり、日本語 parametrize id は使用しない。

## 7 並列分割

### 実装子 A: admission と durable evidence

所有 file:

- `orchestrator/campaign/s8b_holdout_admission.py`
- `orchestrator/tests/test_s8b_holdout_admission.py`
- `orchestrator/tests/s8b_floor_evidence_fixture.py`
- `orchestrator/tests/test_s8b_oracle_driver.py`

担当は generation claim、ledger schema、attempt namespace、旧 12/96 fixture、floor/oracle/n-pilot/R33 の再予約テスト。中核アンカーは `orchestrator/campaign/s8b_holdout_admission.py:1205-1910,2082-3750,3826-4172,4918-5447`。

### 実装子 B: driver、shell、active protocol pin

所有 file:

- `orchestrator/campaign/s8b_floor_campaign.py`
- `orchestrator/campaign/s8b_oracle_n_pilot.py`
- `tools/pegasus/submit_floor.sh`
- `tools/pegasus/floor_campaign.sh`
- `tools/pegasus/submit_oracle_n_pilot.sh`
- `tools/pegasus/oracle_n_pilot.sh`
- `orchestrator/tests/test_s8b_floor_campaign.py`
- `orchestrator/tests/test_s8b_oracle_n_pilot.py`
- `orchestrator/tests/test_pegasus_floor_tools.py`
- `orchestrator/tests/test_s8b_freeze_io.py`
- R33 successor protocol file。現行 pin は `output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json:9-15`

担当は identifier closure、CLI/env/argv 撤去、result field 撤去、shell syntax/argv テスト、driver/job hash pin の successor 更新。所有 file は実装子 A と重複しない。

`tools/pegasus/README.md:226,241-243`、`docs/phase3-8b-restart-runbook.md:235`、worklog/decisions fragment は D95 に従い親の統合担当とする。`rulings/D95.md:10-25`

## 未確定・親の裁定が要る点

1. **旧 floor claim/ledger の live inspector 互換性**  
   推奨は、旧 v1/v2 bytes は履歴として保存するが、新予約と新 result の live authority にはしないこと。旧 inspector を維持すると、削除対象 field 名を source schema に残す必要があり identifier 閉包と衝突する。現行互換面は `orchestrator/campaign/s8b_holdout_admission.py:3905-3925,5129-5203`、テストは `orchestrator/tests/test_s8b_holdout_admission.py:2592-2621`。

2. **R33 protocol pin の更新方式**  
   driver と job script を編集すると現行 protocol の hash pin は必ず不一致になる。`output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json:11-14`, `orchestrator/campaign/s8b_oracle_n_pilot.py:590-595`。推奨は過去 protocol を上書きせず、T-1981 successor protocol を新規作成し、active 手順とテストを successor へ向けること。

3. **P2 の維持可否**  
   これは裁量的な未確認事項ではなく、現行 96 marker と marker identity の静的証拠から棄却が必要である。`docs/archive/worklog-phase3-0826-965.md:14-16`, `orchestrator/campaign/s8b_holdout_admission.py:3960-3970`。P2 をそのまま残す場合、T-1981 の「同じ cell を何度でも測る」と P4 の床値再投入は達成できない。