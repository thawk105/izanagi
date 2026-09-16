## 読んだ資料

必読の5資料はすべて読めました。加えて、許可された実装2本・対応テスト2本、cleanup command、到達不能object台帳、`docs/failures.md` の関連箇所を確認しました。

以下の略記を使います。

- `L`：`tools/check_branch_landed.py`
- `R`：`tools/check_branch_rescue.py`
- `TL`：`orchestrator/tests/test_check_branch_landed.py`
- `TR`：`orchestrator/tests/test_check_branch_rescue.py`
- `S4裁定`：`prompts/stage4-adjudication.md`
- `作者報告`：`artifacts/dev-wave-t2639-branch-rescue-path-first/stage5-author.md`

**静的レビューです。テスト実走・変更・commitはしていません。** 数値結果は親の提示事実として扱います。

## 壊しても赤くならないテスト (real)

**real — S4の不変性テスト2本は、説明の注入が届かなくても緑になります。**

対象：

- `TR:1732` `test_unit_details_do_not_change_assessment_decisions`
- `TR:1748` `test_unit_details_do_not_change_rescue_rc_or_decision_inputs`

両者は `_unproven_unit_details` を差し替えますが、差替え前後で**実際に説明が変わったことをassertしていません**。`R:1628` を固定dictに置き換えて呼出しを消しても、この2本の比較は成立します。

ただし、`_run_tool` は別processではなく `TOOL.assess` を直接呼ぶため、現実装ではmonkeypatchが届きます（`TR:186`）。「process境界で注入が無効」という批判は **refuted** です。問題は到達証明の欠落です。

是正は、注入呼出しと返された説明の具体値を確認した上で、既存判定の不変を比較する範囲です。別の実checkerテストは説明消失を検出するので、**S4全体が無検査という意味ではありません**。

**real — mergeテスト単独ではbatch経路の消失を検出できません。**

`TL:359` `test_batch_preserves_merge_introduced_state` は実在するmergeの四要素とwitnessを照合しますが、batch呼出しを確認しません。`L:783` の `batch_safe` を常にfalseにしても、旧ls-tree走査で同じ証明が成立します。

これはmerge状態を失う変更への有効な回帰テストですが、batch到達の証明には数えられません。batch消失自体は、後述の入力消費・command数テストが検出します。

## 機構を通っていると確認したテスト (refuted)

以下は「狙った経路を通らず、性質だけで緑になる」という批判を **refuted** とします。前節の2本を除く16関数を列挙します。

| テスト・根拠 | 静的に確認した検出対象 |
|---|---|
| `TL:359` `test_batch_preserves_merge_introduced_state` | tipから消したmerge導入状態を実履歴から証明。witness・四要素・候補数を固定。batch固有の限界は前節 |
| `TL:392` `test_batch_validates_all_rows_before_accepting_match` | witnessを先頭に置き、後続行だけ破損。入力消費を確認し、先頭一致で早期受理する変更を検出 |
| `TL:414` `test_batch_failure_never_becomes_negative` | 通常/spool双方でbatch到達を確認。command timeout・解析中deadline・parseを注入し、理由まで照合 |
| `TL:452` `test_batch_chunk_limit_and_command_count` | 実batchの入力件数 `[1024,1]`、5 commands、1025番目のwitnessを固定 |
| `TL:476` `test_batch_empty_input_is_an_error` | helperを直接呼び、空入力の例外コードとGit未起動を確認。assessment経由の試験ではない |
| `TL:485` `test_batch_preserves_nonregular_legacy_path` | batchを禁止stubにし、missing/tree/gitlink/symlinkの旧経路と参照順を確認。実ls-tree解析の試験ではない |
| `TL:1730` `test_batch_path_handling` | tip不一致のfixture、具体的witness・四要素、batch入力を照合。空白類は入力0件で退避を確認 |
| `TL:1749` `test_batch_invalid_stdout_is_indeterminate` | 10種類の破損応答と入力消費を確認し、`path-batch-parse-error` を要求 |
| `TL:1778` `test_batch_rejects_candidate_state_difference` | batch消費を確認。modeはwitnessのls-tree結果、type/OIDはbatch結果を変更し、未証明を確認 |
| `TL:1805` `test_spool_exact_history_without_receipt_is_landed` | regular判定を禁止し、実exact探索のwitness・四要素を照合。両証拠層を未一致stubにすると赤 |
| `TL:1823` `test_unlanded_pure_add_spool_stays_indeterminate` | 候補0の未解決spoolでprobe呼出しを確認し、結果をmatched/not-matchedへ変更 |
| `TL:1857` `test_spool_exact_does_not_hide_integrity_errors` | exact witnessがある状態でregistry破損・blob上限・fragment破損を発生。判定理由と証拠層を照合。ただしreceiptはbaseline赤 |
| `TL:1883` `test_unreceipted_spool_deletion_has_no_exact_fallback` | 削除状態のfallback呼出しを禁止し、missing四要素とindeterminateを確認 |
| `TR:1641` `test_real_checker_unlanded_spool_details` | 実Git＋実landed checker。未着地の具体的説明とrescueへの伝達、履歴追加後のlandedを確認 |
| `TR:1685` `test_unproven_details_are_bounded_and_count_all_reasons` | 実整形関数に101unitを渡し、100件制限・全101件集計・欠落理由・具体的証拠を照合 |
| `TR:1710` `test_missing_child_unit_details_never_claim_complete` | subprocess timeoutを実assessment経路へ注入。JSONのunit欠落・列挙不足も別caseで確認 |

**refuted — probe不変性は発火しない試験ではありません。** `TL:1841` の消費確認に加え、結果は `L:1813` の集約へ届きます。`L:1594` の無効化されたprobe受理条件を有効にすれば、`[matched]` が赤になると予測できます。

## 既存期待値の緩和の有無

**refuted — 既存assertの削除・反転・緩和・skip化はありません。**

差分の削除行を全件確認しました。テスト2ファイルには、diffヘッダー以外の削除行がありません（`stage5.patch:3`、`:388`）。実装側の削除は候補走査・fallback条件・証拠のdecisive指定に限定されています（同`:569`、`:625`、`:644`、`:653`）。

さらにpatchから変更前をメモリ上で復元し、AST比較しました。

- landedテスト：既存66関数、変更・欠落0。
- rescueテスト：既存70関数、変更・欠落0。
- 追加：13＋5＝**18テスト関数、parametrize展開で49 node相当**。

作者報告`:45` の「既存関数は変更していない」は裏付けられます。

## 赤 1 件の裁定への判定

**real — 親の「registry errorなら証拠層にもregistryの理由を運ぶ」を支持します。**

原因は明確です。

1. `_receipt_match` はrecords不在なら `folded-receipt-absent` を返す（`L:1012`）。
2. `_spool_decision` はregistry errorを優先して、正しいregistry理由をunit判定へ返す（`L:1323`）。
3. 証拠層は前者の `receipt_reason` を使い続ける（`L:1408`、`:1444`）。

結果として「JSON破損によるerror」と「receipt不在」という説明が同居します。S4はこの証拠層をそのまま転送するため、人へ運ぶ理由が誤ります（`R:1535`）。

- **目的との整合：** S4裁定`:55` のunit理由と`:56` の証拠層理由を正しく運ぶ修正です。
- **scope：** 判定契約を変えず説明を訂正する範囲なので、scope内です。
- **期待値を現行へ変更する代案：** 今回は却下します。誤った説明を正解として固定し、S4の検査を弱めます。
- **`TL:1851` との両立：** そこは正常registryでreceiptが無いcaseです。error時だけ理由を補正すれば `folded-receipt-absent` は維持できます。なおこの行は今回追加されたテスト内であり、変更前から存在した行ではありません。

blob上限・fragment解析失敗は別の例外理由を持つので、それらまでregistry理由へ一律置換する修正は支持しません（`L:1403`）。

## 変異 N01〜N09 の期待 node 予測

以下、`TL::`・`TR::` は前述の**テストファイルpath＋`::`**です。予測でありKILLEDの実測報告ではありません。また変異の具体的patchが無いため、赤node集合の完全一致までは確定できません。

| 変異 | 期待nodeと判定 |
|---|---|
| N01 | **条件付き予測。** `TL::test_unlanded_pure_add_spool_stays_indeterminate[matched]`、`[not-matched]`。ただし実効点は `L:1338`。旧 `_spool_decision` の `L:1328` だけ変えるとfallbackが上書きし、この負例は赤になりません |
| N02 | **予測可能。** `TL::test_batch_rejects_candidate_state_difference[mode]`。`L:794` の同commit再取得・四要素確認を迂回すると受理される |
| N03 | **予測可能、登録説明は訂正要。** `TL::test_batch_invalid_stdout_is_indeterminate[reordered]`。連番検査を外すと実witnessが受理されるため赤。ただし再確認層が残り、「誤commitの偽証」を示す変異ではなく、異常protocolの受理を示す変異（`L:794`） |
| N04 | **予測可能、登録説明は訂正要。** 例：`TL::test_batch_failure_never_becomes_negative[parse-False]`、`[parse-True]`、`[command-timeout-False]`、`[deadline-True]`。候補なしへ丸めてもspoolはindeterminateのままになり得ます。赤の根拠は具体的reason/outcomeの喪失であり、「必ず非indeterminateになる」ではありません |
| N05 | **登録どおりの検出は予測不能。** 専用関数は2引数、regularは3引数です（`L:1331`、`:1341`）。名前だけ差替えるとTypeError。3引数へ合わせても `any_path=None` なら `any-path-object-search-not-run` のindeterminateとなり、登録のnot-landedには届きません（`L:1351`）。`TL::test_spool_exact_history_without_receipt_is_landed` の禁止stubは赤にできますが、登録した誤判定の証拠にはなりません |
| N06 | **修正後なら予測可能。** `TL::test_spool_exact_does_not_hide_integrity_errors[receipt]`。`L:1418` のregistry error除外を外せばexact成功が判定を上書き。現状はbaseline赤なので変異検出へ帰属不可 |
| N07 | **意味を限定すれば予測可能。** `TL::test_batch_path_handling[colon]`。path内のコロン以降を失う分割で正例が失われる。単なる構文例外による赤は登録目的と区別が必要 |
| N08 | **予測可能。** `TR::test_real_checker_unlanded_spool_details`。説明fieldの消失・空欄化を具体値比較が検出 |
| N09 | **予測可能。** `TR::test_missing_child_unit_details_never_claim_complete[timeout]`。子JSON不在なのにcompleteをtrueにすれば赤 |

**real — N05は現登録から外して実効点へ再照準すべきです。** N01も変異点を明記しない登録では不十分です。根拠はS4裁定`:109` の「確認できない変異は登録せず実効gateへ再照準する」です。N03/N04はテストを緩めず、何を検出する登録なのかを正確にしてください。

## 依頼の達成度 (解けた / 解けていない)

**refuted — 高速化は名目だけではありません。** 親の固定OID実測は、判定・閉包・unit内訳を維持した改善を示します。

| 固定OID | Git子process | 所要 |
|---|---:|---:|
| `aae713e1de…` | 2005 → 92（95.4%減） | 26.55 → 11.35秒（57.3%減） |
| `559bcbc29c…` | 1190 → 244（79.5%減） | 51.29 → 32.77秒（36.1%減） |

数値の出典は親メッセージで、今回読める実測artifactのfile:lineはありません。高速化経路は `L:788` に対応します。

**real — spoolと理由伝達は部分的に解けています。**

- receiptがなくても実履歴に四要素一致があれば証明できる（`L:1418`、`TL:1805`）。
- 未着地spoolはindeterminateを維持する（`TL:1823`）。
- 親のt2515実走では、206.8秒、rc=2のまま、説明の `complete: true`、未証明3unit、`{"exact-state-not-proven":3}` が出た。単なる集約理由からunit別説明へ進んでいます（伝達箇所 `R:1628`）。

**real — 「常に不完全を返すgateをやめる」という元の問題全体は未解決です。**

残余3unitは未証明のままで、assessmentのcompleteはfalse、rescueはrc=2です（`R:1627`、`:2067`、`:2137`）。説明側のcomplete=trueは、着地証明の完了を意味しません。

**refuted — rc=0を受入条件から外したこと自体は不当ではありません。** S4裁定`:26`、`:61`、`:87` が証拠・rc契約維持と残余を明示しています。ただしこれはwaveの成功範囲の限定です。元依頼の全面達成とは報告できません。

また、親の実走はtimeout=60指定です。cleanup標準入口は予算指定なしなので、その運用で不完全が減った証明はまだありません（`.claude/commands/cleanup-branches.md:36`）。

**refuted — 不要frameworkの追加は確認しませんでした。** batch検証、spool専用判定、100件の説明制限は裁定の目的に対応しています（S4裁定`:41`、`:47`、`:60`）。新台帳・自動記帳・削除gateは差分にありません。

## 漏れている consumer・波及

**real — S4は最小契約を満たしても、spoolの探索事情を落とします。**

正常receipt不在＋exact不一致ではexact層が非decisiveとなり、S4から除外されます（`L:1426`、`R:1540`）。したがってrescueだけでは、spoolの候補0と、複数候補を調べた不一致を区別できません。別path観測も非decisiveなので転送されません（`L:1467`）。

これは「決定的証拠層」を要求したS4裁定`:56`への違反とはしません。ただし人が次の調査を選ぶ材料としては不足です。必要なら既存の探索結果を非決定の説明として運ぶ範囲で補い、新たな証拠昇格やframeworkは不要です。

**real — 所要台帳以外に、次の具体的検査consumerを確認対象へ含める必要があります。**

- `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
- `test_plain_runner_coverage.py`
- `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`

作者報告`:78`では列挙していますが、`:84`によればpytest未起動です。親の焦点走にも含まれていません。

49 node相当の追加による被覆低下は確認対象です。過去には少数追加で90%を割っています（`docs/failures.md:24061`）。**現在の台帳・収集メタテスト本体は許可範囲外なので、今回必ず赤になるとは断定できません。** 実測JUnitからの台帳更新が既存の是正経路です（同`:24075`）。

**real — 台帳のhash consumerについて作者報告は説明が不正確です。**

`R:1625` の `report_sha256` は**子landed checkerのstdout**のhashです。S4でrescueのdictへ説明を追加したこと自体では変わりません。S1/S2による子reportの変更では変わり得ます。

対応する人手記帳consumerは `docs/unreachable-object-ledger.md:21` の `assessment_report_sha256` と`:60`の作業者です。説明追加を理由に、このhashをrescue全体のhashへ読み替えてはいけません。

**real — 人への最終伝達はまだ運用上の確認が必要です。** cleanup §5は理由等の報告を求めますが、新しいunit別説明の扱いは明記されていません（`.claude/commands/cleanup-branches.md:76`）。JSONへ載ることと、最終報告へ届くことは別です。

指定範囲外のconsumerは検索していません。したがって「漏れなし」とは結論しません。

## 総括

**現状は受入不可です。** 親の焦点走に赤1件があり、変異baseline緑・全走緑という受入条件を満たしていません（S4裁定`:78`）。

是正の中心は次の3点です。

1. registry errorの正しい理由を証拠層へ伝える。期待値は緩めない。
2. S4不変性テスト2本に注入の到達確認を加える。
3. N05を再照準し、N01/N03/N04の変異点と検出対象を明確にする。

**高速化・spoolの正例証明・未証明理由の伝達には実体があります。残余unitとrc=2は解消しておらず、その限界を明記した部分達成として評価します。**