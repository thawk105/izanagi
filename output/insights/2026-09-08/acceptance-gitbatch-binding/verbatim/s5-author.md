## 実装結果

- [`contract_loader_binding.py`](/work/1/SFC/tanab/izanagi/.codex/worktrees/gitbatch-author/orchestrator/campaign/contract_loader_binding.py) を `ls-tree -r -z` と OID 指定 `cat-file --batch` の2呼出しへ変更しました。
- tuple 順・重複、literal pathspec、OID exact 照合、binary body、timeout 倍率、全 malformed/missing/余剰出力の fail-closed を実装しました。
- capture/live/committed/blobs の検査順と非対称性、`_blob` signature、disk drift 検査を維持しました。
- 共有 fixture、layer3 helper、artifact admission の2 fakeを batch 形へ追随させました。
- duration ledger は生成ツールの `--add-only` のみで更新し、`nodeid_count` は 19,745 から 19,935 になりました。

## 検査結果

| 範囲 | 実走結果 |
|---|---:|
| `test_t671_source_binding.py::*` | 295 passed |
| `test_artifact_admission.py::*` | 146 passed |
| `test_ccbench_spawn_sites.py::*` | 44 passed |
| `test_acceptance_schedule_order.py::*` | 79 passed |
| `test_plain_runner_coverage.py::*` | 3 passed |
| `test_campaign_lock_codec.py::*` | 113 passed |

合計 680 node が緑です。観測した赤は、drift 由来 0、その他の回帰 0 でした。

制約 meta-testでは、spawn-site inventory、自走 harness、ledger 90% coverage、62-path closure/file inventory がすべて通っています。

`test_layer3_report.py` は pytest 専用 allowlist 対象で、自走すると0 nodeのため緑とは数えていません。正規 runner が利用できず、任意 helper の変更は実装済み・未実走です。

## 実行基盤上の制約

指定の `tools/run_tests.py` は Pegasus dispatch の queue preflight で `rc=16`、`child_started=false` となり、計算ジョブは起動されませんでした。

指定 JUnit directory は sandbox から read-onlyで `EROFS` になったため、同じ295 nodeを `/tmp/author-t671-junit.xml` に出力し、そこから `--add-only` を実行しました。runner が生成した一時 dispatch directoryの4ファイルは削除済みで、再生成可能な一時物です。

## 静的確認

- `git diff --check`: 緑。
- `git diff --stat`: 6 files、1,366 insertions、31 deletions。
- 編集 pathは許可された6 pathのみ。index変更、commit、branch変更なし。
- `subprocess.run` は `_run_git` 内の1箇所だけです。
- `CONTRACT_LOADER_RELATIVE_PATHS` は順序込み62件で不変です。
- 4公開関数の signature はHEADと一致し、parserに `splitlines()` はありません。
- 公開 caller 3 moduleは `ident.py`、`artifact_admission.py`、`p3_b4_wiring_probe.py` のままです。

所有外の直接参照は次のとおりです。

- `_run_git` production利用: `mocc_trace_pair.py`、`mocc_trace_pair_anchor.py`
- `_run_git` monkeypatch/direct test: `test_artifact_admission.py`、`test_t671_source_binding.py`
- `_blob` direct test: `test_t671_source_binding.py`
- 共有 campaign-lock fixture consumer: `test_artifact_admission.py`、`test_autonomous_trial_completeness.py`、`test_bench_first_real_wal.py`、`test_campaign.py`、`test_campaign_import_invariant.py`、`test_campaign_lock_wal_consumers.py`、`test_critic.py`、`test_p3_autonomous_workload_trial.py`、`test_p3_b4_closed_critic.py`、`test_p3_b4_raw_record_producer.py`、`test_p3_exploration_namespace.py`、`test_p3_s4_loop.py`、`test_p3_s4_loop_sort.py`、`test_p3_s4_loop_trigger_gating.py`、`test_s1_direct_comparison.py`、`test_s1_report.py`、`test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`、`test_screening_driver.py`、`test_t126_qualification_artifacts.py`、`test_t671_source_binding.py`、`test_trial_registry.py`

## 総括

- Git blob取得を strictな2-process batchへ移行しました。
- 受理・拒否集合、62-path closure、公開API、disk検査を維持しました。
- 実走680 nodeは全緑で、drift赤・回帰赤とも0件です。
- layer3全体だけは正規 runner の基盤制約により実装済み・未実走です。