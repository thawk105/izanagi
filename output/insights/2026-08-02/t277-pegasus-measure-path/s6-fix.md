実装を完了しました。コード・テストのみ編集し、docs 編集・commit はしていません。

## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed | trigger 公開 API から `site` を削除。各公開入口で `_current_site()` を1回だけ解決 |
| F2 | closed | `campaign_id` / `layout_root` を返値へ追加し、CLI の旧 cfg 再計算を除去。旧 campaign bytes 不変テストを追加 |
| F3 | closed | 8c の site 配線を撤去し、`run_trial` / `_finish_trial` / `_run_workload` / CLI で OTHER 以外の build を拒否 |
| F4 | closed | `run_campaign` 一括拒否を採用し、raw trace・screening sinkにも実 site 拒否を追加 |
| F5 | closed | dependency prefix を path 要素配列として identity 化。空要素・明示相対 path を cwd 束縛 |
| F6 | closed | required attestation を `loop.run_campaign` 冒頭へ集約。receipt を `CampaignSummary` 経由で driver に返却 |
| F7 | closed | no-resume を campaign lock・loop state・WAL・provenance の全書込み前へ移動 |
| F8 | closed | `env_tag=contract.env_tag` の変異 anchor を再び一意化（静的確認1件） |
| F9 | closed | 8c CLI の compute 拒否を `competing_bench_pids()` より前へ移動 |
| F10 | closed | M14をbehavioral sink検査へ変更。literal key・exact compute ID・8c OTHER build正例を追加し、M7/M8のexact manifest重複帰属を分離 |

## F4 の方式

`run_campaign` 一括方式を採用しました。実 site が COMPUTE の場合、登録済み Pegasus contract 以外は最初の layout/WAL 書込み前に拒否します。

これにより `p2_2.py`、`backoff_repro.py`、`demo.py`、`p3_kickoff.py`、`p3_s4_red.py`、`sanity_silo.py` を含む legacy caller を一箇所で閉鎖しました。`run_campaign` を通らない coverage/frequency raw trace、sweep `_eval_one`、screening sinkには個別防壁も追加しています。

## F6 の attestation

required attestation は [loop.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/loop.py) の campaign sinkへ集約しました。

順序は次のとおりです。

1. calibration の検証済み読み込み
2. hardware probeとreceipt生成
3. contractとのreceipt再照合
4. campaign layout/WAL処理
5. evaluate/build

driver側のprobe実装は削除済みです。2 genomeのcampaignでも上記3処理が各1回だけ発火するテストを追加し、receiptは`CampaignSummary.execution_receipt`からprovenanceへ記録します。

## 変更後の受理・拒否

- OTHER:
  - triggerは従来どおり`linux-baremetal` contractを使用。
  - legacy `run_campaign`、兄弟driver、8c buildを受理。
  - F4防壁による拒否集合の変更なし。
- COMPUTE:
  - triggerのみ`measurement_env="pegasus"`のexact campaign IDで受理。
  - registered Pegasus contract、required attestation、v2 build、no-resumeが必須。
  - legacy campaign、screening、raw trace、8c buildは拒否。
- LOGIN / SUSPECT / 未知 site:
  - trigger計測は引き続き拒否。
- prefix identity:
  - ambient `/tmp/p:/tmp/q` は`["/tmp/p", "/tmp/q"]`。
  - ambient `/tmp/p;/tmp/q` は`["/tmp/p;/tmp/q"]`となり、digestは異なる。
  - 空要素と明示相対pathは実効cwdへ絶対化。
  - v2既存entryはidentity変更によりcold missになり得ます。
- RA-6の依存bytes content hash、`/scr`、claim、reservation、lease、8c compute運転は実装していません。

Compute campaign goldenは次で固定しました。

`p3-s8a-trigger-loop-s8a-trigger-autonomous-75727902`

追加keyはliteral `"measurement_env"` のみです。

## 検査結果

通過した静的検査:

- 変更Python全ファイルの`python3 -m py_compile`
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- 公開APIからの`site`消滅、変異anchor一意性、compute ID、prefix配列の静的確認

pytestは以下10ファイルを`tools/run_tests.py`で計算ノードへdispatchしました。

- `test_buildcache_v2.py`
- `test_build_site_gate.py`
- `test_campaign.py`
- `test_p3_s4_loop_trigger_gating.py`
- `test_p3_autonomous_workload_trial.py`
- `test_s6_sort_sweep.py`
- `test_s8a_trigger_sweep.py`
- `test_screening_opt_in.py`
- `test_plain_runner_coverage.py`
- `test_real_repo_serialization.py`

結果はテスト開始前の`qstat -Q preflight rc=1`、runner `rc=16`です。実走nodeidは0件で、pytest緑は主張しません。

## 所有外への波及可能性

- 全`loop.run_campaign` consumerはCOMPUTE上でexact Pegasus contractが必要になります。
- `CampaignSummary` consumerにはoptional `execution_receipt`が追加されました。既存構築はdefault値で互換です。
- v2 consumer（floor、oracle、T126等）はprefixの配列identity化により初回cold missの可能性があります。
- `screening_driver.evaluate_candidate`の直接callerもCOMPUTEで拒否されます。
- trigger/8cの`site=` keyword callerは静的検索上ゼロです。
- `test_t126_qualification_driver.py`など`test_campaign.py`共有fixture consumerには親の関連全走が必要です。
- 凍結成果物、既存campaign、submodule bytesは変更していません。

## 総括

- caller注入siteとCLIの旧campaign再計算を除去しました。
- COMPUTEのlegacy計測は共通sinkとraw sinkの双方で閉鎖しました。
- required attestationはcampaign sinkの1回だけに集約しました。
- no-resumeはreject、入口stop、WAL-only crash-tailより前に発火します。
- prefix identityはpath配列となり、区切り衝突とcwd未束縛を解消しました。
- 静的検査は通過しましたが、pytestはscheduler preflight障害により未実走です。