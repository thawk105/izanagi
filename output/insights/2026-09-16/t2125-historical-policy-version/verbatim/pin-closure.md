# [T-2125] DW-O09 pin 閉包 (変更 source の path で全列挙)

変更 source: `orchestrator/campaign/artifact_admission.py`、`orchestrator/campaign/build_admission.py`、
`orchestrator/campaign/wal.py`、`orchestrator/campaign/layer3_schema.json`。
`git grep -ln` を worktree (base d97c423bd) で実行した。

## 閉包所属

| 変更 source | enforcement source closure (`campaign_lock.py` の ordered path tuple) |
|---|---|
| `artifact_admission.py` | **member** (`campaign_lock.py:57,126`) |
| `build_admission.py` | **member** (`campaign_lock.py:82`) |
| `wal.py` | **member** (2 箇所) |
| `layer3_schema.json` | 非 member (0 件) |

**pin は path であって内容 hash ではない。** したがって中身を変えても tuple は壊れない。

## 影響

- **編集すると現行 closure の digest が動く。** その結果、本変更より前に記録された campaign を
  **certified** で読むと epoch が `E1-stale` / `recorded-current-closure-mismatch` になる。
  これは **この 3 module を編集するどの wave でも起きる既存挙動**であり (D1245 / D1365)、
  本 wave が新しく作る性質ではない。歴史閲覧側は D1245 のとおり拒否理由にしない。
- `contract_loader_blob_sha256s` の照合は **記録 commit の blob** と比べる
  (`contract_loader_binding.py:558,577`)。現行 disk bytes との一致要求ではないので、
  本変更が過去 campaign の contract 照合を壊すことはない。

## path が現れる tracked file (README・archive を除く)

- `orchestrator/campaign/campaign_lock.py` — 閉包の ordered literal
- `orchestrator/campaign/p3_b4_closed_critic.py`、`p3_b4_raw_record_producer.py`
- `orchestrator/qualification/contract.py`
- `orchestrator/tests/acceptance_duration_ledger.json` — 所要台帳 (test file 名で pin)
- `orchestrator/tests/fixtures/b10_backoff_shape_locks/{balanced,read-heavy,write-heavy}.campaign.lock`
  — 記録済み fixture lock。**記録時の blob sha を持つが、照合は記録 commit 側なので編集で壊れない**
- `orchestrator/tests/test_artifact_admission.py`、`test_campaign_lock_codec.py`、
  `test_ccbench_spawn_sites.py`、`test_p3_b4_closed_critic.py`、
  `test_s1_9pair_figure_provenance.py`、`test_t126_pegasus_tools.py`、
  `test_t671_source_binding.py`
- `docs/decisions.md`、`docs/failures.md` (説明)

## 新規 literal の閉包 (`classification = "historical-policy-version"`)

`admitted-new-schema` を key に検索した結果、値域を固定しているのは次のとおり。

- `orchestrator/campaign/layer3_schema.json:293` — classification enum (**要変更**)
- `orchestrator/campaign/autonomous_trial_completeness.py:240` — certifying 条件 (変更不要)
- `orchestrator/tests/test_artifact_admission.py` — `EXPECTED_CAMPAIGN_CLASSIFICATIONS` は
  **v1 corpus の表**であり `classify_campaign` (certified 固定) の結果を比べる。
  新 classification は歴史閲覧でしか出ないので、**この表は赤にならない** (レンズ B 所見 9 が指摘)。
- `orchestrator/tests/test_layer3_report.py` (3 件)、`test_autonomous_trial_completeness.py` (4 件)、
  `test_p3_autonomous_workload_trial.py` (10 件) — 既存期待値。
  新 classification を足すだけでは赤にならないが、schema 変更と相殺の実効性はここで確かめる。

**新規凍結成果物は発行しない。durable manifest の再発行も要らない。**
