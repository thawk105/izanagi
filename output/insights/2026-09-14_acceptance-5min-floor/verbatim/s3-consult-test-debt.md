## 総括

削除可能と静的に証明できたのは、**T3の完全重複1 node**です。  
採用件数は T1=0、T2=0、T3=1、T4=0、T5=0。重複計上していません。  
削減は test 本文2行、対応する台帳エントリ1行。別途、台帳件数を1か所更新します。  
候補は assertion の一致から抽出し、所要による選別はしていません。  
`orchestrator/tests` の378 Python file、15,662個の `test_` 関数をASTで走査しました。  
全件の意味的な依存閉包を監査した結果ではなく、**他の負債が存在しないという結論ではありません**。編集・pytest実行はしていません。

## T1 死んだ pin

**独立した削除候補は0件。** 次の不在 pin は実在しますが、削除根拠はT3の重複です。不在だけを理由に両方消すことは提案しません。

| nodeid | file:line | 不在を示した検索 | 撤回のD番号 |
|---|---|---|---|
| `orchestrator/tests/test_related_work_search.py::test_postprocessing_tier_api_remains_outside_executor_scope` | `orchestrator/tests/test_related_work_search.py:1978` | `rg -n 'validate_tier_analysis' orchestrator tools` はtest内の1582・1979行だけに一致。productionの `orchestrator/related_work_search.py` には不在 | 該当する撤回決定を確認できず |

この assertion は symbol を再導入すれば赤になります。単独では検出力があり、恒真ではありません。

## T2 恒真

**採用0件。**

- ASTで検出した定数 assertion 161か所はすべて `assert False`。`assert True`、非空tuple/list/set自体のassertion、空のtest本体はありませんでした。
- これで自己構築値の検査や、複雑な含意による恒真が不存在とは証明できません。
- 親の記憶に対応する決定は **D1580**。候補生成条件から恒真になるguardについて、既存実装は削除しないと明記しています。**D1518**も候補gateとしての恒真化と、実装・環境のdrift検出を区別しています。いずれもtest削除の根拠にはできません。

削除候補を採用していないため、削除を支持する変異例もありません。

## T3 完全重複

**採用1件。**

| 残すnodeid | 消すnodeid | subsumeの根拠 |
|---|---|---|
| `orchestrator/tests/test_related_work_search.py::test_tier_enforcement_remains_outside_registration_executor_scope` — `:1581` | `orchestrator/tests/test_related_work_search.py::test_postprocessing_tier_api_remains_outside_executor_scope` — `:1978` | 両者の全assertion集合は同じ一要素 `{not hasattr(search, "validate_tier_analysis")}`。したがって削除側の集合 ⊆ 残存側の集合が等号で成立する |

現物は [残す定義](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_related_work_search.py:1581) と [消す定義](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-5min-floor/orchestrator/tests/test_related_work_search.py:1978)。

両方とも引数・decorator・個別fixtureがなく、本文は以下の1文だけです。

```python
assert not hasattr(search, "validate_tier_analysis")
```

`search` は同じfileの19行目でimportする同一production moduleです。module側に `__getattr__` はなく、対象symbolへの動的設定も検索ではありません。共通autouse fixtureはsite・環境変数・layout状態の隔離で、このsymbolや両node名による分岐を持ちません。

例えばproduction moduleへ `validate_tier_analysis = None` を追加すれば、**残す側だけで同じ違反を検出できます**。両者に固有の検査や副作用はありません。この2本が検査するのは文献検索executorのAPI境界であり、禁止された正しさ・freeze・provenance・受入gateではありません。先行solの37 nodeにも含まれません。

## T4 撤回済み機構

**採用0件。**

撤回決定、production不在、残存testの検出力ゼロをすべて確認できたものはありません。

`orchestrator/tests/test_t810_harness_schema.py::test_ready_event_surface_is_removed`（同file:333）は、旧イベントを現行validatorが拒否することを検査します。「removed」という名前でも、現行の入力拒否を守る負例なので外しました。

## T5 その他の負債

**採用0件。**

helper共有化などについて、同値性とconsumer閉包を証明した提案はありません。本文の類似だけで負債認定していません。

## 削除の実行手順

削除対象の完全列挙は次の1 nodeです。file全体は削除しません。

```text
orchestrator/tests/test_related_work_search.py::test_postprocessing_tier_api_remains_outside_executor_scope
```

同じ変更単位で行う変更は以下です。

| path・現行行 | 変更 |
|---|---|
| `orchestrator/tests/test_related_work_search.py:1978` | 1978–1979行の関数定義と本文を削除 |
| `orchestrator/tests/acceptance_duration_ledger.json:2602` | 上記nodeidのキーを削除 |
| `orchestrator/tests/acceptance_duration_ledger.json:23109` | `nodeid_count` を23105から23104へ更新 |

両test名の参照検索では、定義と台帳の計4か所だけが一致しました。台帳の残す側キー（2646行）は維持します。

台帳consumerは `orchestrator/tests/conftest.py:1502` のschema検査と `:1542` のloaderです。件数整合は `test_update_acceptance_duration_ledger.py:319` が検査します。これらの実装・assertion変更は不要です。

削除後の焦点走集合は、残存assertionと、変更した実台帳を直接読むconsumerから次の3 nodeを引きます。

```text
orchestrator/tests/test_related_work_search.py::test_tier_enforcement_remains_outside_registration_executor_scope
orchestrator/tests/test_update_acceptance_duration_ledger.py::test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations
orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection
```

実行時は `python3 tools/run_tests.py` にこの集合を渡します。その後、通常の変更完了検査として `check_codex_agents.py` と `check_docs.py` を実行します。**今回はいずれも未実行です。**

## 候補から外したものと、外した理由

| 対象 | 理由 |
|---|---|
| 先行solのG1–G22、計37 node | 指示どおり削除候補から除外 |
| `test_s8b_selector_freeze.py:744,765` のv1 freeze依存test | freeze検査として明示的な対象外。条件付きskipから永久に死んだtestとは判断できない |
| `test_audit_dangling_commits.py:1189` の `test_removed_changed_files_api_cannot_reintroduce_per_commit_fork` | API再導入を検出する負例。残存testによるsubsumeを証明できず除外 |
| `test_env_contract.py:161,167` の本文重複 | parameter集合が異なる。非正数と非整数型という異なる入力を検査している |
| `test_s6_sort_sweep.py:297` と `test_s8a_trigger_sweep.py:387` の本文一致 | `W` のimport先が異なる。同じ入力文字列でも別production関数を検査する |
| その他のfile間本文一致 | module global・fixture・呼出先を含む同値性と依存閉包を確定できなかったため除外 |
| snapshot、proof、provenanceに関係する本文一致 | 禁止対象に該当するため候補化しない |

## 読めなかった file / 確かめられなかったこと

- 指定必読の `rulings-verbatim.md` は読めました。
- 任意調査の `pyproject.toml` は存在しませんでした。実在する `pytest.ini` を確認しました。
- 動的collection、parameter展開後の総node数、pytest結果、実変異による赤は未確認です。
- 全15,662関数の意味的な恒真性・subsumeは未証明です。確定成果は上記の完全重複1 nodeに限定します。