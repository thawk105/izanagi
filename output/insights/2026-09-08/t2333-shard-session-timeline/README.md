# [T-2333] 受入 shard の report.json へ session timeline の観測 field を足す

2026-09-08。branch `worktree-dev-wave-t2333-shard-timeline`。

D1647 (ユーザー裁定) に従い、受入 shard の `report.json` へ観測 field を 1 key 足した。
gate・判定は足さず、D1620 が固定した測定面 (canonical 起動の receipt が記録する最遅 shard の
wall) も変えていない。

## この観測が要る理由

P1 の [T-2273] が確定したいのは、受入 wall の内訳である。shard-0 の wall から最大 worker 占有を
引いた 95〜207 秒が、受入形固有 (collection と deselect、LPT 並べ替え、report 生成) なのか
host 差なのかを分ける手段が現 report には無い。本 wave はその分解に要る観測点を足す。

## 足した field

`report.json` の top-level に `session_timeline` を 1 key 足した。`SCHEMA` は v1 のまま。

```json
{
  "session_timeline": {
    "collection_finished_epoch_s": 1788800000.125,
    "workers": {
      "gw0": {
        "first_test_started_epoch_s": 1788800000.250,
        "last_test_finished_epoch_s": 1788800123.750,
        "real_repo_lock_intervals": [
          {"acquired_epoch_s": 1788800010.5, "released_epoch_s": 1788800021.875}
        ]
      }
    }
  }
}
```

- `collection_finished_epoch_s` は number または null (null = 未観測)。
- `workers` は観測のあった worker だけの map で、worker 名簿ではない。空でもよい。
- 時刻はすべて Unix epoch 秒。shard は別 host になりうるので monotonic では跨げない。

## 判定を足していないことをどう固定したか

`validate_report_evidence` と `merge_reports` は 1 行も変えていない。どちらも
`session_timeline` を読まない。timeline の形を検査する helper も新設していない。
したがって観測値の内容が判定へ流れ込む経路は構造的に存在しない。

これが恒真でないことは変異 M11 で確かめた。`validate_report_evidence` へ
`session_timeline` の非空検査を足すと `test_session_timeline_contents_do_not_change_merge_verdict`
が赤になる。

## 段 4 で覆した所見

段 3 の両レンズが「`_REPORT_FIELDS` へ必須追加するのは D1647 の『受理集合には触れず』違反」と
主張したが、blocker としては refuted とした。理由は 3 つ。

1. `merge_reports` は top-level key 集合の厳密一致を要求するので、「field を足す」実装は
   `_REPORT_FIELDS` を伸ばすか厳密一致を緩めるかの 2 つしかない。後者は gate の弱体化である。
   「key 集合の字面が変わってはならない」と読むと、D1647 は自分が命じた行為の唯一の実装を
   すべて禁じることになる。
2. shard report は 1 回の走行の中で書かれ同じ走行の中で読まれる。producer と consumer は同じ
   commit で出荷される。以前 certified になった走行が reject されることはない。
3. レンズ B が挙げた「旧 14-key を厳密に読む既存 consumer」
   (`output/insights/2026-08-24_t1618-xdist-controller-cost/prepare_inputs.py`) は、
   `orchestrator/tests` と `tools` から参照する test / tool が 0 件 (`git grep -q` rc=1) で、
   `shard_count == 2` と当時の固定 `EXPECTED_COUNTS` を要求するため新しい report を食わせられない。

ただし所見の核 (観測が判定を変えうる) は採用し、plan が予定していた
`validate_report_evidence` への形検査を却下した。

## 段 3 が見つけた実欠陥 (すべて採用)

- collection 終了時刻の採取位置。plan は `pytest_collection_modifyitems` の末尾で採る設計だったが、
  acceptance plugin の同 hook は非 wrapper の `trylast` であり、その後に conftest 側の wrapper が
  yield 後処理 (`_validate_real_repo_shard_state`、suffix 除去、LPT 並べ替え) を実行する。
  そこで採ると、分解したい区間そのものが「collection 後の空白」に化ける。
  acceptance plugin 自身の `pytest_collection_finish` を `trylast` で置く形に変えた。
  conftest 側の同 hook は `tryfirst` なので、prewarm も含めた collection 全体の終端を捉える。
- 観測の欠測・異常が受入の rc を変えうる点。report 組立は `except Exception` で `INFRA_RC` に
  落ちるので、`float(report.start)` の失敗だけで受入が落ちる。すべての時刻を型・有限性・正値の
  検査に通し、通らなければ null や空として記録する形にした。
- xdist の crash `TestReport` は `worker_id` を持たず `start` / `stop` の既定値が 0 である。
  正値 filter でこれを除外する。
- `item.config` の直接参照。既存の protocol 契約テスト
  (`test_real_repo_serialization.py`) は `path` / `name` / `originalname` だけを持つ
  `SimpleNamespace` を渡すので `AttributeError` になる。`getattr` で引く形にした。

## 受入台帳への影響

test node を足すと `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` に触れる。
権威 probe (`IZANAGI_ACCEPTANCE_LEDGER_COVERAGE_PROBE`) で測った値は次のとおり。

| 時点 | rows | covered | 被覆率 | 90% を割らずに足せる node |
|---|---|---|---|---|
| base c5754d1f4 | 21569 | 19419 | 90.031990% | 7 |
| main 取り込み後 240ee6360 | 21596 | 19439 | 90.012039% | 2 |

余裕はほとんど無い。追加した 16 node をすべて `0.0` で登録し `nodeid_count` を更新した。
`consumer_keys` 集合は `--collect-only -q` の素朴な行抽出と集合等価であることを確認した
(段 3 レンズ A の「測り方が権威と違うかもしれない」という指摘は refuted)。

## 変異 matrix

`mutation-ledger.json` が正本。spec は `mutation-spec.json` (実行した bytes と同一)。

baseline PASSED / KILLED 11 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0。
期待 node 完全一致 11/11 (M7 = 14 node、M10 = 2 node、他は各 1 node)。
`repo_head` = `30a5b6bd40a3560b10c238fbd1aea3673614337f`。

| # | 変異 | 赤になったテスト |
|---|---|---|
| M1 | collection 時刻の採取を `pytest_collection_finish` から `pytest_collection_modifyitems` 末尾へ戻す | `test_collection_finish_clock_runs_after_synthetic_modifyitems_wrapper` |
| M2 | worker bounds 更新の正値・有限性 filter を外す | `test_runtest_logreport_ignores_zero_nonfinite_missing_and_huge_bounds` |
| M3 | `getattr(item, "config", None)` を `item.config` へ戻す | `test_runtest_protocol_configless_item_keeps_existing_lock_contract` |
| M4 | lock 取得が失敗しても interval を append する | `test_runtest_protocol_lock_acquire_and_release_failures_record_nothing` |
| M5 | lock 解放が失敗しても interval を append する | 同上 |
| M6 | `access is None` でも clock を読み記録する | `test_runtest_protocol_access_none_reads_no_clock_and_records_nothing` |
| M7 | `_REPORT_FIELDS` から `session_timeline` を外す | 14 node |
| M8 | `_worker_payload` から lock interval を落とす | `test_worker_payload_carries_observations_and_defaults_without_state` |
| M9 | controller 集約の collection 時刻を `max` から `min` へ変える | `test_controller_state_xdist_uses_latest_collection_and_worker_lock_map` |
| M10 | serial 分岐で config-local 状態を使わず `_WORKER_PAYLOADS` を要求する | 2 node |
| M11 | `validate_report_evidence` に `session_timeline` の非空検査を足す | `test_session_timeline_contents_do_not_change_merge_verdict` |

## 受入全走 (段 6 の中間走行)

`acceptance-receipt.json` が正本。**これは段 6 の中間走行**であり、land 対象 tip への最終受入は
本記録 commit の後に別途投入する (記録 commit が tested tip から漏れると land が rc=23 になるため)。

- `verdict` = `child-green`、`child_rc` = 0、`red_nodeids` = []、`flake_nodeids` = []
- `tested_main` = `a916458d894497f4526fc2633f286e77127f8061`
- `tested_tip` = `0465d35be140b22d41d7fb803e0052bf47d2b20b`
- `effective_scheduler` = `loadgroup`

その前の 1 本は post-claim merge が `stage=merge rc=70 source_rc=1` で落ちた。実装の問題ではなく、
走行中に main が進んで受入台帳の `nodeid_count` が再び衝突したためである。test node を足す wave
同士は必ずこの 1 行で衝突する。

## 焦点走 (親の実測)

merge 後の木で `test_run_tests_shards.py` 189 passed、`test_acceptance_schedule_order.py` 79 passed、
`test_update_acceptance_duration_ledger.py` 24 passed、`test_plain_runner_coverage.py` 3 passed。

`test_real_repo_serialization.py` は自走 harness では growth hold が bypass を拒否する
(未変更の main worktree で同一の拒否を再現した。当 wave に非帰属)。`run_tests.py` 経由の走行では
main 240ee6360 時点で 1 件が赤だったが、差分を完全に戻した木 (dirt=0) で同一箇所・同一 assertion を
再現したので main 側の既存赤である。受入時点の main では解消していた。

## 次 wave の出発点

この観測は [T-2273] のためのものである。次は実際の受入走行で `session_timeline` を採り、
shard-0 の wall から collection 区間・worker 占有・lock 保持を引いて、残る 95〜207 秒が
受入形固有か host 差かを判定する。
