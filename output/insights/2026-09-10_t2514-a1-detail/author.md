## 総括

**実装済み・未実走です。** 所有2ファイルだけを変更し、既存テストの全bytesが変更前のまま先頭に残ることを確認しました。docs編集・git add・commitは行っていません。

- [実装](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2514-a1-detail-author/orchestrator/campaign/paper_story_a1_paired.py:6705)：拒否時にgreenを含む全armとadmissionを原子保存。個別の保存Exceptionは固定label・型だけを元拒否へ追記し、後続保存を継続します。productionへ検証済み `raw_root` を配線しました。
- [追加テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2514-a1-detail-author/orchestrator/tests/test_paper_story_a1_paired.py:4264)：7関数・14ケース。canonical bytes/detail、冪等性・異digest共存、保存順序・cleanup、各保存例外、成功無副作用、fallback、could-not-run、BaseException伝播、配線を検査します。
- 静的確認：両ファイルのAST解析、`git diff --check`、禁止Unicode範囲の不在を確認しました。

実走はrepo rootで `tools/run_tests.py` を使用しましたが、焦点テストとmeta-testの両方が **`qstat -Q` preflight rc=1 → runner rc=16、child_started=false** で停止しました。テスト本体の赤・緑はありません。受入完了とは扱いません。

自ら列挙して実行を試みたmeta-testは以下です。

- `test_plain_runner_coverage.py` 全体
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `test_growth_test_holds_contract.py::test_s8c_candidate_fixture_consumers_and_remaining_nodes_are_collection_pinned`
- `test_pytest_collection_config.py::test_repo_pytest_ini_has_no_addopts_and_pins_testpaths`

所有外への波及は静的確認のみです。関門のproduction callerは同ファイル内の `_run_measurement_v3`、外側は `run_measurement` です。既存直接callerはroot省略で互換です。共有 `conftest.py` の `ratified_enforcement_source` を継承しますが、共有fixture変更はありません。consumer側では `test_paper_story_a1_job_contract.py` のv3測定構造検査と、上記collection・fixture閉包検査が確認対象です。T-2581所有ファイルは変更していません。

変異候補は次のとおりです。**oldはいずれもproduction内で出現1件と静的確認済み、変異実走は未実施**です。対応nodeのファイル接頭辞は `orchestrator/tests/test_paper_story_a1_paired.py::` です。

**M1：arm保存呼び出し削除**

```python
# old
                        _persist_v3_condition_gate_record(
                            output_path, record.canonical_json().encode("ascii"),
                        )
# new
                        pass
```

対応：`test_a1_detail_all_records_atomic_and_idempotent`。ほかに保存例外5ケース、準備例外4ケース、fallback検査も影響予定です。保存欠落への感度確認であり、kill数へ算入しません。

**M2：arm保存のException境界を狭める**

```python
# old
                    except Exception as exc:
                        failures.append(f"{label}[{index}]:{type(exc).__name__}")
# new
                    except OSError as exc:
                        failures.append(f"{label}[{index}]:{type(exc).__name__}")
```

対応：`test_a1_detail_save_exception_preserves_rejection` の全5ケース、および `test_a1_detail_preparation_exception_is_local[arm-digest]`・`[path]`。

**M3：admitted経路を誤拒否**

```python
# old
    if not admission.admitted:
        rejected = ",".join(
# new
    if True:
        rejected = ",".join(
```

対応：`test_a1_detail_success_and_omitted_root_have_no_side_effects`、既存 `test_f4_v3_backoff_gate_calls_real_family_before_measurement_M11[True]`。