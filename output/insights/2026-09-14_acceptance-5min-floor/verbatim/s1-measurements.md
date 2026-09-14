# 親が 2026-09-14 に実測した事実 (再測定不要。疑ってよい)

一次資料は repo 外の shard 成果物である。wave `t2067-efg-residual` の 04:28 起動、
tested-main `abbef52d5686b4e83ac018db9133689f12694e1f`。

- session root: `/work/1/SFC/tanab/.izanagi-acceptance-shards/2f9872c56f62324056496756037371b4`
- 各 shard の `junit.xml` と `report.json` を親が直接読んだ。

## 1. shard 別の wall と仕事量

| shard | wall | 直列和 | 実効並列 | 最大単体 | errors | failures | tests |
|---|---|---|---|---|---|---|---|
| 0 | 438.521 秒 | 13,075 秒 | 29.8 倍 | 310.2 秒 | 10 | 1 | 7794 |
| 1 | 132.994 秒 | 2,865 秒 | 21.5 倍 | 60.2 秒 | 0 | 0 | 7793 |
| 2 | 255.3 秒 | 7,522 秒 | 29.5 倍 | 158.7 秒 | 0 | 0 | 7792 |

- 全 shard の直列和 = 23,461.8 秒 / 351 file / 23,379 node。
- 仕事量の配分は 56% / 12% / 32% である。
- worker は各 shard 48 本。

## 2. shard-0 の wall の内訳 (`session_timeline` より)

- `collection_finished` から最初のテスト開始まで **49.2 秒**。
  shard-1 では同じ区間が 0.1 秒である。
- テスト実行窓 (最初の開始 → 最後の終了) **313.6 秒**。
- wall 438.5 秒との差 約 76 秒は、最後のテスト終了より後の区間である。

## 3. 実 repo ロックの実態

`real_repo_lock_intervals` は取得**後**に記録されるので、待ち時間ではなく保持時間である。

| shard | ロック区間 | 保持合計 | 和集合 | 窓に占める割合 | 最長 1 本 |
|---|---|---|---|---|---|
| 0 | 163 本 | 1,662.8 秒 | 285.6 秒 | 91.1% | 188.4 秒 |
| 1 | 0 本 | 0 秒 | 0 秒 | 0% | — |
| 2 | 0 本 | 0 秒 | 0 秒 | 0% | — |

- 保持合計 1,662.8 秒 / 和集合 285.6 秒 = 平均 5.8 本が同時に保持している。
  ロックは `read` = `LOCK_SH` / `write` = `LOCK_EX` を区別しており、読みは共有される
  (`orchestrator/tests/conftest.py` の `_real_repo_flock_until`)。
  したがって**ロックは純粋な直列鎖ではない。**
- 実 repo テストを持つのは shard-0 だけである。shard-1 と shard-2 は 0 本。

## 4. 単体で重い node

300 秒以上は 2 件。

- 310.2 秒 `orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]`
- 303.8 秒 `orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`

100 秒以上が 37 件、60 秒以上が 86 件。上位 10 件は 288〜310 秒で、すべて
`test_s8b_oracle_driver` である。次いで `test_p3_b4_producer_auth_experiment` 277.1 秒、
`test_p3_b4_raw_record_producer` 233.3 / 231.9 秒、`test_s8b_floor_campaign` が 197〜225 秒の帯に 9 件。

## 5. file 単位の重さ (3 shard 合算の直列和)

| 秒 | 全体比 | node 数 | file |
|---|---|---|---|
| 3468.8 | 14.8% | 502 | `test_s8b_floor_campaign` |
| 3414.1 | 14.6% | 134 | `test_s8b_oracle_driver` |
| 1573.9 | 6.7% | 50 | `test_p3_b4_producer_auth_experiment` |
| 968.1 | 4.1% | 216 | `test_run_tests_preflight` |
| 841.0 | 3.6% | 189 | `test_s8b_ratified_verify` |
| 783.5 | 3.3% | 366 | `test_check_ai_provenance` |
| 779.4 | 3.3% | 51 | `test_t1259_qsub_env_delivery_probe` |
| 749.5 | 3.2% | 25 | `test_t139_submission_path` |
| 655.8 | 2.8% | 50 | `test_p3_b4_raw_record_producer` |
| 643.3 | 2.7% | 122 | `test_related_work_search` |

上位 15 file で全体の 67.8% を占める。

## 6. 直近 57 走の分布

同 session root 群を mtime 降順に 60 件走査し、`junit.xml` の `testsuite` 属性を集計した。

- shard-0: n=57 中央値 **345.2 秒** 最小 268.9 秒 最大 798.3 秒
- shard-1: n=58 中央値 175.2 秒 最小 127.6 秒 最大 556.3 秒
- shard-2: n=54 中央値 228.6 秒 最小 202.2 秒 最大 429.1 秒

**訂正 (親の誤記):** 当初ここに「57 走のどれ 1 つとして 300 秒を下回っていない」と書いたが、
同じ表の最小値 268.9 秒と矛盾する。正しくは **中央値 345.2 秒で、300 秒を切った走も存在する**。
D1918 は 2026-09-10 時点で最遅を shard-2 と記録しており、最遅 shard の identity は
時期によって移動している。

**訂正 2 (親の誤記):** 当初 §2 に「最後のテスト終了から wall 終端まで約 76 秒」と書いたが誤り。
report.json の境界と junit の timestamp / time から再計算した正しい分解は
**開始側 55.74 秒 / dispatch 49.17 秒 / 実行 313.61 秒 / 終了側 20.01 秒**である。

## 7. 計算ノード job のハング (本日 2 件、いずれも shard-0)

- `996124.nqsv`: pytest は 04:40:31 に完了し `result.json` は完備 (`child_rc: 1`)。
  その後 05:16 / 05:18:51 / 05:19:19 の 3 回で Accumulated CPU Time が **6093.72 秒から
  1 ミリ秒も増えず**、Elapse だけ 2679 → 2749 → 2777 秒へ伸びた。05:19 に親が `qdel`。
- `996191.nqsv`: 同型。CPU **6055.24 秒**で停止、Elapse 733 → 760 秒。05:19 に `qdel`。
- 親側の収集は PBS の `.o` / `.e` を待つため、job が死ぬまで待ち手は返らない。
  job の walltime は `#PBS -l elapstim_req=01:00:00` = 3600 秒なので、
  放置すると 1 走が 1 時間ノードを占有する。
- `qdel` した走行は赤ではなく infra として戻った (`rc=70` /
  `normalized_child_rc=16` / `reason=dispatch-attestation-missing`)。受領証は出ず、再走が要る。
  これは所有 session の独立確認による。

## 8. 赤の中身 (所有 session の独立確認)

- 10 errors: `test_t1259_qsub_env_delivery_probe` の autouse fixture で
  `git ls-files --others --exclude-standard -z` が 30 秒 timeout。
- 1 failure: `test_pegasus_floor_tools.py:1428` の
  「diagnostic timeout did not interrupt the syscall」。
- 別 attempt: `test_run_tests_preflight` の RuleOps preflight subprocess が 60 秒 timeout (rc=15)。
  同 tip の単独再走は緑。
- 共通点は「実 repo に対する subprocess へ短い timeout を掛けたテスト」であり、
  login node の負荷で伸びる I/O である。所有 session 観測時の load average は 72 / 94 / 81、
  親の 05:15 観測では **133.44** であった。

## 8b. 非帰属の赤が走行ごとに入れ替わる (所有 session 2 者の独立確認)

**これは 5 分という上限とは別の、より大きい損失でありうる。** 赤が出るたびに帰属判定と再走が要り、
1 回の再走は queue 待ちを別にしても 8〜15 分である。

- 同一 wave の 3 attempt で落ちた test に**重複が無い**。
  - attempt 2: `test_t1259_qsub_env_delivery_probe.py` の setup error 6 件 +
    `test_env_contract_activation.py` の 1 件
  - attempt 3: `test_pegasus_floor_tools.py::test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]`
    の 1 件のみ。本文は `AssertionError: diagnostic timeout did not interrupt the syscall`。
    5 秒 sleep する `os.write` を診断 timeout が中断できるかを見る純粋な時間依存 test
    (`floor_job_checkpoint.py` の `_bounded_boolean_child` 経路)。
  - 別 wave の attempt: `test_run_tests_preflight` の RuleOps preflight subprocess が 60 秒 timeout。
- **いずれも単独再走では緑** (3 passed / rc=0)。
- 観測時の load average は 72 / 88.56 / 94 / 133.44 と幅がある (96 core 機)。
- 再現しやすい候補として所有 session が挙げた 3 file:
  `test_pegasus_floor_tools.py` / `test_t1259_qsub_env_delivery_probe.py` /
  `test_env_contract_activation.py`。
- 共通の形は「実 repo に対する subprocess または syscall へ**壁時計の短い上限**を掛け、
  その上限が守られることを test が検査している」ものである。上限は 5 秒 / 30 秒 / 60 秒と異なる。
  負荷が上がると上限が守られず赤になる。**検査対象は上限そのもの**なので、
  上限を伸ばすと検査が恒真化しうる (F の型 [恒真ゲート] に注意)。

## 9. 親が読んだ実装上の事実

- `orchestrator/tests/test_s8b_oracle_driver.py` の `_t080_stub_free_e2e_repo` は
  docstring に「36MB / 2300 ファイルの copytree + `git submodule add` + 子 python での
  draft→finalize→commit→verify で **1 回 15〜22 秒**」と書いている。
  **実測の単体 290〜310 秒とは 1 桁以上違う。** この差の行き先は親も特定していない。
- 同 helper は process 内で引数ごとに base を 1 回だけ組み、各テストへ
  `shutil.copytree` で独立コピーを渡す。base は `atexit.register(shutil.rmtree, ...)` で
  片付ける。xdist の worker ごとに base は組み直される。
- `tools/acceptance_shards.py` の `allocate` と `create_session` は
  `shard_count not in {2, 3}` を `ShardError` で拒否する。
  `tools/acceptance_launcher.py` も `shard_count not in {1, 2, 3}` を拒否する。
- 実 repo テストは 1 単位として分割不能に束縛されている
  (`test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`)。
