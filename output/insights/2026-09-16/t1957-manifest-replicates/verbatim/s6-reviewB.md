## must-fix

- **M8の事前登録と実際の失敗箇所が不一致。** 裁定§5は「registration load の exact-key」を期待するが、`orchestrator/tests/test_trial_registry.py:8769` の `trial["n"]` が先に `KeyError` を送出する。期待nodeは赤くなるが、`:8772` のloaderには到達しない。
  **成果物影響:** そのままでは変異結果を「読込時の必須キー検査を実証した」と誤帰属する。期待する失敗箇所の記録を訂正する必要がある。

## consumer 取り残し

**射影内では、今回の変更によって赤くなる未追随箇所を特定できなかった。リポジトリ全体の全数確認は未完了。** 「列挙された絶対パスだけを読む」という制約に従い、射影外は検索・読取していない。

以下はworktree相対パス。直接構築とhelper経由を確認した。

| file:line | 確認した経路と未追随時の失敗 |
|---|---|
| `orchestrator/tests/test_trial_registry.py:170,5484` | 直接の `TrialSpec(...)` は2箇所。両方に `n=2` がある。欠落なら必須引数不足。 |
| 同`:181,218` | manifest trial辞書・registration trial辞書とも `n` を保持。欠落なら `_parse_trials` のexact-keyで拒否。 |
| 同`:328,1610` | `test_p2… → _registered_repo → _manifest_value` の2段経路は更新済みfixtureへ到達。 |
| 同`:5016,5023` | `test_m6a… → _valid_registry_row → _registration_value` も追随済み。 |
| `orchestrator/tests/test_p3_autonomous_workload_trial.py:7221,10363` | 独立したmanifest trial辞書2箇所とも `n=2` を追加済み。 |
| `orchestrator/tests/test_reflux_origin_binding.py:434,188,315` | `test_fixture_scope_positive… → case → _manifest_value` の2段経路は更新済み。実際の登録は`:365` の `append_trial_registration` を使う。 |
| 同`:84` | 手書き `_registration_value` も `n` を保持。ただし射影内に呼出箇所はなく、稼働するconsumerとしては数えられない。 |
| `orchestrator/tests/test_reflux_originless_compatibility.py:1239,1252` | 各test → `_bundle` (`:48`) / `_origin_enabled_bundle` (`:133`) → `p3_test.t325_registered_trial.__wrapped__`。**差分外の間接consumer**だが更新済みfixtureへ到達する。 |

originlessの固定baselineについても、manifest SHA・measurement head・registry由来値を`:335–366,382`で正規化している。schema変更でdigestが変わることだけを理由に赤くなるとは判定できない。

`_write_registry` のpath名問題はない。`test_trial_registry.py:231` はcanonical JSON＋改行を書き、`trial_registry.py:957 → :621 / :883` は通常ファイル・内容を検査する。`manifest.json` という名前や拡張子による分岐はない。

## 変異 15 件の帰属検査

`R`＝`orchestrator/campaign/trial_registry.py`、`T`＝`orchestrator/tests/test_trial_registry.py`。以下は静的判定であり、変異本走の結果ではない。裁定の省略表記 `[manifest-zero]` 等は `test_t1957_rejects_n` を補って照合した。

| id | 作れる／作れない | 期待node | 帰属 |
|---|---|---|---|
| M1 | 作れる。R:770直前、Mapping確認後 | 実在：両sourceの`missing` | 補完後は受理され、期待例外が出ない。狙った検査に帰属する。 |
| M2 | 作れる。R:786 | 実在：両sourceの`float` | `3.0`が通過する。**boolケースも型エラーから下限エラーへ変わり赤くなる**ため、赤集合はfloatだけではない。 |
| M3 | 作れる。R:788 | 実在：両sourceの`one` | 全cellが1なので一致検査に遮蔽されない。 |
| M4 | 作れる。R:788–789 | 実在：両sourceの`zero/negative/one` | 各入力は全cell同値。下限検査の欠落に帰属する。 |
| M5 | 作れる。R:800–801 | 実在：両sourceの`cell-split/holdout-split` | 分割入力が受理される。 |
| M6 | 作れる。R:800–801をholdout別検査へ変更 | 実在：両sourceの`holdout-split` | holdout内は同値なので通過する。`cell-split`は引き続き拒否される。 |
| M7 | 作れる。R:791 | 実在：`test_t1957_six_cell_n_round_trip` | T:8762のP2で失敗。加えてsplit負例も値が2に潰れて赤くなる。 |
| M8 | 作れる。R:842削除 | 実在：round-trip | **T:8769のKeyError。登録されたloader帰属は成立しない。** 既存`test_p2_first_and_second_registration_append_pass`も、省略された登録行の再読込で赤くなりうる。 |
| M9 | 作れる。R:842 | 実在：round-trip | T:8769のP3で失敗。既存fixtureの通常値は2なので、その経路では固定値化を検出できない。 |
| M10 | 作れる。R:1583削除 | 実在：`test_acceptance_rejects_registry_canonical_tuple_mutation[n]` | T:6769に`n`がある。loaderを通さずdataclassを変更して比較するため、cell一致検査に遮蔽されない。 |
| M11 | 作れる。R:55 | 実在：`test_t1957_schema_versions` | 定数assertに帰属。manifestの旧版負例も期待どおりではなくなるため、赤集合は単独ではない。 |
| M12 | 作れる。R:56 | 実在：schema-versions | **既存T:5058のduplicate-key testも赤くなる。** fixtureがv2を生成し、`:5063`のv3置換が空振りする。全走で最初の赤だけを採ると帰属を誤る。 |
| M13 | 作れる。R:820 | 実在：`manifest-v2-with-n` | 当該入力が受理される。`manifest-v2-genuine`もschemaエラーからmissing-keyエラーへ変わり、メッセージ照合で赤くなる。 |
| M14 | 作れる。R:788 | 実在：round-trip | `n=3`の初回loadで失敗。**既存T:1569の正例も`n=2`で先に失敗しうる。** 過剰拒否controlとしては成立するが専属帰属ではない。 |
| M15 | 作れる。R:800 | node指定なし、SURVIVED期待 | `{item.n for item in trials}` は**実装内に1箇所**。両形式とも整数値の集合を作るため、この置換は等価。 |

**実在しない期待nodeは見つからなかった。** ただしpytest collection自体は実行していない。全走の実際の実行順・停止設定も未確認であり、「最初の赤」を上表の期待nodeと同一視してはならない。

## meta-test 適合

- **新規関数は4個ではなく3個。** 差分全体の追加定義は `test_t1957_schema_versions`、`test_t1957_six_cell_n_round_trip`、`test_t1957_rejects_n` のみ。
- 負例は明示ID付きの2 source × 12 case。新規26ケースに加え、既存canonical-tuple testへ`[n]`を1ケース追加している。
- `test_trial_registry.py:2252` のtop-level関数名一意性検査に対し、AST照合で重複は0。3関数ともtop-levelの `test_` 名である。
- 射影内に、これらの関数の所要台帳・命名・件数を別途拘束する検査は見つからなかった。他のAST検査はproducer実装や発行経路を対象としている。
- 外部collection設定・台帳検査は射影外なので未確認。
- **提供された差分全体に、既存testの削除・改名はない。** 削除された関数定義行も0。

## nit / backlog

- origin-bindingの未使用 `_registration_value` は、必須の `prereg_content_commit` / `prereg_effective_commit` を持たない。現在の呼出経路での回帰ではなく、将来再利用した際の潜在不具合。
- 登録`n`と実際の反復slot集合の一致は、この差分では実装されていない。保存・読込・identityの検査結果を、反復束縛の完成として扱えない。
- 全consumerの2段追跡と外部meta-testの確認は、射影範囲では完結できない。未確認を「取り残しなし」に置き換えないこと。

## 総括

M8の失敗箇所の事前登録は訂正が必要。
期待nodeの不在は検出せず、M15の置換対象は1箇所。
射影内のfixtureは追随しているが、全repoのconsumer監査は未完了。
新規testは3関数で、既存testの削除・改名はない。
静的検査のみ実施し、pytest・変異本走は実施していない。