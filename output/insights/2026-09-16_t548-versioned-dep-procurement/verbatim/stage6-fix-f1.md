## 総括

B1・B3・P-1 と M1 再照準を実装しました。所有内の 6 ファイルだけを変更し、commit はしていません。**実 job は未実走で、closed とは申告しません。**

**修正内容**

- **B1:** [submit:167](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-f1-shell/tools/pegasus/submit_silo_ladder_rung1.sh:167)、[job:364](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-f1-shell/tools/pegasus/silo_ladder_rung1.sh:364)  
  正常入力でも scratch に両依存がなく停止 → gflags/glog を別配列で列挙し、既存と同じ clone・pinned-clean 検証・scratch コピーを通します。FetchContent は 3 本のままです。
- **B3:** [mocc:1528](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-f1-shell/tools/pegasus/mocc_trace_pilot.sh:1528)  
  cache のみ準備した投入が hydrate 前に停止 → compiler gate 後、gflags 段前に hydrate し、その `.source_root` から両依存を解決します。hydrate は 1 回。既存の timeout・stderr 保存・絶対 path 検査を維持しました。
- **P-1:** [test:925](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-f1-shell/orchestrator/tests/test_pegasus_thirdparty_fetch.py:925)  
  実装の受理・拒否は変更せず、未検査だった「root 未指定→rc=2・stdout 空・stderr 1 行・env 名あり」「env 指定→rc=0・root 一致」を本物の `tool.main` で復元しました。

**期待 nodeid**（すべて今回実走して通過）

- M1、新設：`orchestrator/tests/test_pegasus_thirdparty_fetch.py::test_build_dependency_sources_rejects_url_without_git_suffix`
- M1 正例、新設：`orchestrator/tests/test_pegasus_thirdparty_fetch.py::test_build_dependency_sources_real_policy_exact_shape`
- M3、既存：`orchestrator/tests/test_pegasus_thirdparty_fetch.py::test_build_dependencies_reject_mutated_cache[shallow-shallow-verify-gflags]`
- M10、新設：`orchestrator/tests/test_silo_ladder_rung1_driver.py::test_silo_build_dependencies_reach_scratch_before_dependency_stage`
- M11、既存 node の mocc 分岐を訂正：`orchestrator/tests/test_pegasus_tools.py::test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench`
- P-1、新設：`orchestrator/tests/test_pegasus_thirdparty_fetch.py::test_verify_cache_root_must_be_explicit_or_environment`

変異本走はしていません。

**追補 1 による期待値訂正**

`assert job.count(resolution) == 1` を維持し、mocc だけ resolution を変更しました。

| 旧期待 | 新期待・拒否の維持 |
|---|---|
| `THIRDPARTY_SOURCE_ROOT="${IZANAGI_THIRDPARTY_SOURCE_ROOT:-$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src}"` | `THIRDPARTY_SOURCE_ROOT="$THIRD_PARTY_SOURCE_ROOT"`。新解決行の欠落・重複を拒否 |
| 両依存の assignment が各 1 回 | 同じ assert を維持。欠落・重複・別 path を拒否 |
| resolution → assignment → configure | 維持し、hydrate → `.source_root` 読取 → resolution → 存在検査 → HEAD 照合も要求 |
| 旧行のない正しい hydrate 経路まで拒否 | この誤拒否だけを訂正。旧 env／checkout staging 解決の残存は明示的に拒否 |

cache 必須・絶対 path・stderr 保存・timeout・hydrate 1 回も検査します。他の 14 本の期待値は変更していません。

**実走結果**

すべて指定の `PYTHONPATH=. python3 orchestrator/tests/<file>.py`。表の範囲は各ファイルの自走 harness 全体です。

| ファイル | 結果 | rc |
|---|---:|---:|
| `test_pegasus_tools.py` | 69 passed | 0 |
| `test_silo_ladder_rung1_driver.py` | 92 passed | 0 |
| `test_pegasus_thirdparty_fetch.py` | 105 passed | 0 |
| `test_plain_runner_coverage.py` | 3 passed | 0 |
| `test_ccbench_spawn_sites.py` | 47 passed | 0 |
| `test_hooks.py` | 474 passed、既存 skip 1 | 0 |
| `test_silo_ladder_rung1_evidence.py` | 1 passed、期待赤 1 | 1 |
| `test_p3_s4_loop.py` | 148 passed、想定外の赤 115 | 1 |

- **期待赤との一致:** `test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` が `pbs_job` SHA 不一致で失敗。evidence・golden は未編集です。
- **想定外の赤／未解消の回帰検知:** p3_s4 は fixture 引数不足の `TypeError` が **112 件**、`PEGASUS_LOGIN` での `ExecutionGuardError` が **3 件**。[全ログ](/tmp/t548-f1-p3-s4.log)。途中報告の「115 件が TypeError」を訂正します。harness・期待値は変更していません。
- 新設 mocc assert の初回実走では、全文の `print(value)` を数えるテスト側の誤りが 1 件ありました。hydrate 節内へ限定して修正し、再実走は通過しました。

**波及・未実走範囲**

- silo の receipt／`third_party_heads` consumer は従来の FetchContent 3 本を維持。scratch に両依存が追加されます。
- mocc の FetchContent consumer は、移動した同じ hydrate 出力を使用します。共有 Git fixture は未変更です。
- 凍結 evidence の shell binding は親による別対応が必要です。
- `test_mocc_trace_job_contract.py` は自走 harness がなく、未実走です。実 job 投入・計算ノード・GitHub clone・実 build・親の全走も未実施です。
- **削除した test 関数：0 件。** `test_hooks.py` は実走のみで未編集。所有外の編集はありません。