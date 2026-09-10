# 変異 matrix 本走の raw 台帳 — 軸 driver の env contract admission

`DW-O19` に従い、統合 commit `bdce16f` の**後**に tracked file へ本走した。
harness は `/home/SFC/tanab/.claude/jobs/0fdf038e/tmp/axis-env-contract-jobs/mutation_harness.py`、
raw 結果は同 dir の `mutation-matrix.json` と `mutation-run.log`。

## 走行条件

- 対象 (変異先): `orchestrator/campaign/p3_s4_loop_trigger_gating.py`
- 判定 (テスト): `orchestrator/tests/test_p3_s4_loop_trigger_gating.py` (`-rf`)
- 変異と復元は **login node** で行い、pytest だけを `tools/run_tests.py` 経由で
  Pegasus gen_S 計算ノードへ dispatch した。外側の job walltime で親が殺されて
  `finally` の復元が走らない事故 (F32) を構造的に避けるための配置である。
- `flock` の単一走行 guard を持ち、取得失敗で abort する (`DW-M05`)。
- 置換ごとに累積後の anchor 一意性を assert し、注入をディスク内容で確認する (`DW-M04`)。
- 復元は `git checkout --` の後に**内容比較** (`read_text() == 元ソース`) で検査する。
  恒真になりうる `git diff` は使わない (`DW-M05`)。

## 結果

```
mutations=25  killed=25  survived=0  timeout=0  anchor_error=0  canonical_matched=25
baseline: rc=0 / failed=0
restore : identical_to_original=True
```

**baseline は緑** (前 wave の erratum のように scratch copy 由来の baseline 失敗が
混入していないことを確認済み)。復元後の内容は元ソースと byte 一致。

| ID | 変異 | 結果 | 新規赤 node 数 | canonical 期待 kill | 一致 |
|---|---|---|---:|---|---|
| M1 | reject helper の admission 除去 | KILLED | 4 | `test_reject_sink_refuses_pegasus_without_wal` | yes |
| M2 | allow-all | KILLED | 6 | `test_reject_sink_refuses_pegasus_without_wal` | yes |
| M3 | always-false (過剰拒否) | KILLED | 14 | `test_reject_sink_other_writes_two_contract_tagged_records` | yes |
| M4 | lookup 結果の無条件破棄 | KILLED | 7 | `test_contract_sentinel_flows_to_run_campaign` | yes |
| M5 | 空 numactl の誤展開 | KILLED | 1 | `test_empty_numactl_contract_flows_as_empty_list` | yes |
| M6 | `EnvContractError` の fallback | KILLED | 4 | `test_lookup_error_propagates_before_campaign_and_wal` | yes |
| M7-R | measurement admission 除去 | KILLED | 2 | `test_measurement_sink_rejects_pegasus_before_campaign_and_wal` | yes |
| M8-R | 既定 site を固定 `OTHER` 化 | KILLED | 4 | `test_default_path_rejects_pegasus_from_site_policy` | yes |
| M9 | selector drift (`ENV_TAG="pegasus"`) | KILLED | 3 | `test_environment_module_surface_and_default_seams` | yes |
| M10a | syntax callsite の helper 迂回 | KILLED | 2 | `test_reject_sink_refuses_pegasus_without_wal` | yes |
| M10b | diff-quarantine callsite の helper 迂回 | KILLED | 2 | `test_reject_sink_refuses_pegasus_without_wal` | yes |
| M10c | auditor callsite の helper 迂回 | KILLED | 2 | `test_reject_sink_refuses_pegasus_without_wal` | yes |
| M11 | reject が contract tag を捨てる | KILLED | 4 | `test_reject_sink_other_writes_two_contract_tagged_records` | yes |
| M12 | reject helper だけ lookup error fallback | KILLED | 2 | `test_reject_lookup_error_propagates_without_wal` | yes |
| M13 | late guard (WAL 書込み後に admission) | KILLED | 5 | `test_reject_sink_refuses_pegasus_without_wal` | yes |
| M14 | 実 selector 時だけ `L.CLK` | KILLED | 4 | `test_same_selector_contract_flows_to_run_campaign` | yes |
| M15 | 実 selector 時だけ `L.NUMA` | KILLED | 3 | `test_same_selector_contract_flows_to_run_campaign` | yes |
| M16 | env-var selector | KILLED | 2 | `test_driver_env_tag_assignment_is_literal_constant` | yes |
| M17 | 既定 seam 条件の `L.CLK` | KILLED | 4 | `test_driver_has_no_legacy_env_attribute_references` | yes |
| M18 | 既定 seam 条件の `L.NUMA` | KILLED | 3 | `test_driver_has_no_legacy_env_attribute_references` | yes |
| M19 | 既定 seam 条件の reject tag | KILLED | 3 | `test_driver_env_names_are_scoped_to_admission` | yes |
| M20 | env-var で selector を差し替える | KILLED | 2 | `test_driver_admission_guard_and_lookup_are_exact` | yes |
| M21 | env-var で guard を無効化する | KILLED | 2 | `test_driver_admission_guard_and_lookup_are_exact` | yes |
| M22 | import alias + `_current_site` 条件 | KILLED | 4 | `test_driver_has_no_legacy_env_imports` | yes |
| M23 | `_current_site` 条件の reject tag | KILLED | 3 | `test_driver_env_names_are_scoped_to_admission` | yes |

各変異の逐語 old/new は harness の `MUTATIONS` が正本であり、上表の note はその要約である。

## 過剰決定の扱い (`DW-M03`)

新規赤 node 数が 1 を超える変異が多い。これは構造検査 (R10〜R15) と挙動テストが
同じ変異で同時に赤くなるためである。**canonical kill は挙動側**とし、構造検査は冗長 gate として扱う。
`canonical_matched=25` は、事前登録した canonical 期待 node が 25 件すべてで
実際に新規赤 node 集合に現れたことを意味する — 「別の理由で赤くなっただけ」ではない。

単一理由に近いのは M5 (新規赤 1 件)、M7-R / M10a / M10b / M10c / M12 / M16 / M20 / M21 (各 2 件) である。
M3 の 14 件は過剰拒否変異の性質上、admission に到達する全経路が同時に赤くなるためで、
これは冗長ではなく変異の到達範囲そのものを表す。

## 事前登録の erratum (初回結果は消さない — `DW-M02`)

- 段 4 の初回登録 M7 / M8 は**帰属不成立**だった。M7 は fixture の `_lookup` が
  `pytest.fail` を投げるため campaign 到達前に赤くなり、「measurement guard が効いた」kill に
  ならなかった。M8 は関数 identity の `is` 比較だけを見ており挙動 kill でなかった。
  段 6 で M7-R / M8-R へ再照準し、fixture を正常 lookup へ、identity pin を
  diagnostic sensitivity pin へ分離した上で登録し直した。
- 段 4 の M3 の kill 元宣言 (「clean dry-pass」) は誤りだった。clean dry-pass は admission に
  到達しないため kill 元になりえない。正しい kill 元は site matrix と reject 正例である。
  実装子とレビュー D が独立に同じ訂正を出した。
- 段 4 の登録は 8 件だったが、段 6 のレビューと焦点再レビュー 2 巡を経て 25 件になった。
  増分の大半は「production 既定 seam で走っているかを条件にする」族 (M16〜M23) であり、
  値ベースの sentinel だけでは閉じられない。
