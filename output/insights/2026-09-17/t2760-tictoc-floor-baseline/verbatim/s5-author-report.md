## 総括

- T-2760 を実装。2ファイル・5 hunk、191行追加、新規テスト6件。
- 素の runner：**34 passed / 0 failed**。
- pytest：直接実行は hook 拒否、wrapper は dispatch 障害で未実走。
- 現行 source で tictoc が build 前に拒否されることを素の runner で確認。
- 所有外のコード・docs・submodule は未編集。commit・git 状態変更操作なし。
- runner が所有外の `output/pegasus-dispatch/` に診断 receipt 3件を自動生成。
- pytest・変異 matrix 未確認のため、**closed とは申告しません**。

## 変更一覧

| file:line | 変更 |
|---|---|
| `orchestrator/campaign/between_run_floor.py:72` | 根拠コメントと tictoc baseline を追加 |
| `orchestrator/tests/test_between_run_floor.py:15`、`:27` | `re`、`space_for` を import |
| 同 `:256` | 実 source の tictoc hook 不在を assert |
| 同 `:881` | 指定の6テストを追加 |

静的比較で、既存 baseline entry、実装の全関数、module docstring の不変を確認。既存テスト関数の変更は指定された assert 1行のみ。`git diff --check` は成功。

## 実走

| コマンド | 結果 |
|---|---|
| `python3 orchestrator/tests/test_between_run_floor.py` | **34 passed / 0 failed** |
| `python3 -m pytest orchestrator/tests/test_between_run_floor.py -q -p no:cacheprovider` | PreToolUse hook が起動拒否 |
| `python3 tools/run_tests.py orchestrator/tests/test_between_run_floor.py -q -p no:cacheprovider` | rc=16、`qstat -Q preflight rc=1`、pytest 子未起動 |

以下は素の runner で実走・成功した新規6件の対応 nodeid。接頭辞 `P` は `orchestrator/tests/test_between_run_floor.py::`。

| ID | nodeid（`P` に続く部分） |
|---|---|
| T1 | `test_t2760_baselines_are_points_of_their_registered_genome_space` |
| T2 | `test_t2760_tictoc_baseline_matches_ccbench_cmake_cache_defaults_at_pin` |
| T3 | `test_t2760_parse_cli_args_accepts_tictoc_and_rejects_unregistered_protocol` |
| T4 | `test_t2760_protocol_output_stem_names_tictoc_without_colliding` |
| T5 | `test_t2760_tictoc_floor_rejected_before_build_or_measure_without_trace_hook` |
| T6 | `test_t2760_hook_bearing_source_routes_tictoc_baseline_through_main` |

既存28件も全件成功。M4・M7 の既存 killer はそれぞれ `Ptest_mocc_floor_rejected_before_build_or_measure_without_trace_hook`、`Ptest_hook_bearing_source_routes_mocc_baseline_through_main`。

検索で特定した次の meta-test 3件も wrapper から実行を試みましたが、同じ dispatch 障害で**全件未実走**です。

- `orchestrator/tests/test_s8b_floor_campaign.py::test_production_use_perf_keyword_call_sites_are_a_closed_set`
- `orchestrator/tests/test_floor_pair_driver.py::test_module_source_has_no_frozen_fallback_or_publish_bypass`
- `orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`

## 変異 anchor 表

対象はすべて `orchestrator/campaign/between_run_floor.py`。killer は上表の完全 nodeid に対応し、**変異適用後の実走結果ではなく期待値**です。

| M | 行 | old（置換前文字列） | 変異／期待 killer |
|---|---:|---|---|
| M0 | 76 | `# 現行 pin には trace hook が無く、下の D1373 関門が build 前に拒否する (実測の開通は別件)。` | コメント変更。SURVIVED 期待 |
| M1 | 77–83 | 下記 entry 全体 | 削除。T3、T6 |
| M2 | 78 | `"BACK_OFF": 1,` | 0へ。T2 |
| M3 | 80 | `"NO_WAIT_OF_TICTOC": 0,` | 1へ。T1、T2 |
| M4 | 316 | `if not _protocol_source_has_trace_hook_evidence_only(protocol):` | 恒偽へ。T5、既存 mocc 拒否テスト |
| M5 | 218 | `protocol_part = "" if protocol == "silo" else f"_{protocol}"` | tictoc でも空文字へ。T4 |
| M6 | 297 | `if protocol not in BASELINES:` | 恒偽へ。T3 |
| M7 | 315 | `baseline = BASELINES[protocol]` | `BASELINES["silo"]` へ。T6、既存 mocc 経路テスト |

M1 の old（インデント込み）：

```python
    "tictoc": Genome("tictoc", {
        "BACK_OFF": 1,
        "NO_WAIT_LOCKING_IN_VALIDATION": 1,
        "NO_WAIT_OF_TICTOC": 0,
        "PREEMPTIVE_ABORTS": 1,
        "TIMESTAMP_HISTORY": 1,
    }),
```

## 波及可能性

| 対象 | 静的確認 |
|---|---|
| 所有外 caller | Python ファイル検索では、この module の `BASELINES`／`BASELINE`／`_parse_cli_args` を参照・import する所有外 caller は未検出 |
| `test_screening_driver.py` | consumer は glob と canonical genome の protocol を照合。将来生成される tictoc JSON が候補になる。schema は不変 |
| `test_layer3_report.py` | protocol と測定条件による floor 選択に関係。今回は実 floor を生成していない |
| `test_s8b_floor_campaign.py` | `use_perf` 呼出し集合を固定。対象呼出しは変更なし |
| `test_pegasus_floor_scoping.py` | scoping 出力と floor consumer glob の分離を検査。命名規則は変更なし |
| `test_floor_pair_driver.py` | `between_run_floor` への依存禁止を source 文字列で固定。対象 module は未変更 |
| duration ledger | 既存28件の nodeid を掲載。新規6件は未掲載で、全 collection の90% coverage 検査に関係 |

## 未実走・懸念

pytest 焦点走、meta-test 3件、consumer スイート、M0〜M7 の変異 matrix、受入全走は未確認です。性能測定は実施していません。

直接 pytest はログインノードでの実行を禁止する PreToolUse hook に拒否されました。正規 wrapper も `qstat -Q` preflight で停止しており、テスト失敗とは区別しています。