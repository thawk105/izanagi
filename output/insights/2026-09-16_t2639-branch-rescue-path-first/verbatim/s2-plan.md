## 読んだ資料

射影された次の 4 資料を読めました。

- `prompts/brief.md`
- `prompts/D922-verbatim.md`
- `prompts/D1231-verbatim.md`
- `prompts/D720-verbatim.md`

上記の基点は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2639-branch-rescue-path-first/` です。

許可された実装・テストの関連箇所も確認しました。以下の行番号は現在のファイルに対するものです。

- `tools/check_branch_landed.py`
- `tools/check_branch_rescue.py`
- `orchestrator/tests/test_check_branch_landed.py`
- `orchestrator/tests/test_check_branch_rescue.py`

追加で、要求された実在 path の調査として `git ls-files -z` を実行し、既存 object の batch **メタデータ**応答を読みました。ファイル変更、commit、pytest、性能測定は行っていません。

**結論：S1 と通常 blob fragment の S2 は実装可能です。削除 fragment への新しい fallback は I7 との整合を論証できないため除外します。**

## S1 のプラン (file:line)

**現行位置**

| 箇所 | 現行動作 |
|---|---|
| `tools/check_branch_landed.py:731` | `_find_exact_state` |
| 同 `:738–740` | main tip の exact-state 一致を先に受理 |
| 同 `:741–747` | path 履歴を `candidate_limit + 1` 件列挙、OID を検査 |
| 同 `:749–755` | 候補ごとに `_tree_entry` を呼ぶ |
| 同 `:756–763` | 一致がなければ上限超過／不一致を返す |
| 同 `:694–710` | path を検証した tree entry を四要素同時比較 |

**変更単位**

1. `:731` の直前に `_batch_check_path_candidates` を追加する。
2. `:738–747` の tip 優先、候補列挙、OID 検査は維持する。
3. `:749–755` を、batch で絞った候補だけ `_tree_entry` で照合するループに置換する。
4. `:756–763` の判定条件・理由・candidate count は維持する。

疑似コードは次の形です。

```python
# tip と候補列挙は現行どおり
if required.missing or required.object_type != "blob" or unsafe_batch_path(path):
    # 現行の ls-tree ループ
else:
    for chunk in chunks(candidates, 1024):
        rows = batch_check_and_validate_all_rows(chunk, path)
        for commit, row in zip(chunk, rows):
            if row.is_missing:
                continue
            if (row.oid, row.object_type) != (
                required.oid, required.object_type
            ):
                continue
            observed = _tree_entry(git, commit, path, len(required.oid))
            if _entry_matches(required, observed):
                return matched(commit, candidate_count=len(candidates))
# 現行の上限超過／不一致処理
```

**プロトコルと順序検査**

標準 `--batch-check` では、入力 `<commit>:<path>\n` ごとに次が返ります。

- 存在：`<oid> <type> <size>\n`
- 不在：`<入力そのまま> missing\n`

成功行には入力 commit がありません。したがって、**標準形式を `zip` するだけでは、成功行の順序違いを検出できません。**

順序検査を満たすため、安全な path では次の tagged format を使います。

```text
引数:
--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)

入力:
<full-commit-oid>:<path> <連番>

成功出力:
<oid> <type> <size> <連番>

不在出力:
<full-commit-oid>:<path> missing
```

この形式では、不在行には連番が残らないことを、既存 repo 上の読み取り probe で確認しました。成功行は連番、不在行は期待する commit/path 式との完全一致で位置を検証します。

各 chunk の**全出力を検証してから**一致を受理します。

- 最終 LF、行数、余剰行を検査する。
- 成功行の OID、type、非負整数 size、連番を検査する。
- 不在行は期待する式と ` missing` の完全一致だけ許す。
- 順序違い、欠落、未知形式、decode 不能は `AssessmentError`。
- `assess` の `:1920–1933` で `indeterminate` にする。壊れた応答を「候補なし」へ変換しない。

**path の扱い**

`%(rest)` を使うと空白で入力が分割されるため、path を引用して解決しようとしてはいけません。

| path の性質 | 提案 |
|---|---|
| ASCII 空白・タブなどの whitespace を含む | 現行の `ls-tree -z` ループへ退避 |
| LF／CR を含む | 行プロトコルへ投入せず、同じく現行ループ |
| `:` を含む | full commit OID の直後の最初の `:` だけを境界とし、path 内の `:` は保持 |
| 非 ASCII の有効 UTF-8 | bytes に UTF-8 encode して保持。ASCII decode を path に適用しない |
| 非 UTF-8 | 現行の `_parse_raw_diff:625–629` の fail-closed を維持 |

現在の追跡 path **25,475 件**では、空白・非 ASCII・LF／CR／タブは見つかりませんでした。一方、実在する危険例はあります。

```text
output/env/pegasus/calibration/job-staging/0:867863.nqsv/allocation-unavailable.json
```

この path の tagged batch 応答は正常でした。したがって、`split(":")` による分解は禁止です。この調査は現在の index に限り、全履歴や未追跡 path の不存在証明ではありません。

**mode・非 blob・削除**

- batch は mode を返さない。OID/type が一致した**同じ commit**を `:694` の `_tree_entry` で再取得し、`:704` の `_entry_matches` を必ず通す。
- symlink の object type は **blob**。`120000` と `100644` の差は最後の mode 検査で落とす。
- `required.missing` と tree／gitlink は現行ループを維持する。特に gitlink の参照先 object がローカルにない場合、`cat-file` の不在と tree entry の不在を同一視しない。

**上限・残時間・process 数**

- batch 1 回は最大 **1,024 候補**。検索上限とは別定数にする。
- 既定では列挙が最大 1,025 件なので、必要なら 2 回になる。「常に 1 回」は提案しない。
- 現行は `limit + 1` 番目も正例探索する。その順序と正例優先を維持する。
- `Git.run:205–247` の既存 `input_data` を使い、新しい subprocess 経路を作らない。
- `command_count` は batch 1 回で 1 増加。mode 確認の `ls-tree` も従来どおり数える。
- timeout は既存の `min(COMMAND_TIMEOUT_SECONDS, remaining)`。batch ごとに更新される。
- 大量行の組立・parse 中も `remaining()` を確認し、期限切れを `truncated` にする。

M2 の 361 件・0.09 秒では、5 秒に約 56 倍の余裕があります。ただし 1,024 件への単純比例による約 0.26 秒は**推定**です。cold cache、pack、path 深さ、負荷の分布を測るまでは、5 秒で常に十分とは断言できません。

また、OID/type 一致・mode 不一致が多数なら、mode 確認は依然多数必要です。高速化の最悪ケースとして測ります。

**`_find_object_any_path`**

`tools/check_branch_landed.py:767–780` は既に `git log --find-object ... --max-count=1` **1 回**です。候補ごとの `ls-tree` はありません。

`cat-file <oid>` はローカル object の存在しか示さず、main 到達可能性を代替できません。変更対象から外します。`:1325–1333` の発火条件も維持します。

## S2 のプラン (file:line)

**処理順序**

`tools/check_branch_landed.py:1317–1323` の spool 用 placeholder は残し、receipt 処理の後に必要な場合だけ探索します。

`:1352–1362` の直後に、次を満たす fallback を追加します。

- receipt の読み取り・fragment identity の解析が成功した。
- registry が error でない。
- receipt が不一致。
- `state.required.missing` が false。
- required が通常ファイル blob（mode `100644`／`100755`）。

receipt の parse error、blob サイズ上限、fragment 解析エラーを exact-state の成功で覆い隠しません。非通常ファイルと削除は既存挙動を維持します。

**I2 を守る関数分離**

`:1278–1284` の `_spool_decision` は receipt 経路として維持し、その直後に正例専用関数を追加します。

```python
def _spool_exact_positive_decision(search, receipt_reason):
    if search.outcome == "matched":
        return _decision("landed", search.reason), False
    if search.incomplete:
        return _decision("indeterminate", search.reason), True
    return _decision("indeterminate", receipt_reason), False
```

この関数は `state.change`、`state.old`、`any_path` を受け取りません。候補数 0 を負証拠へ変換する分岐を持たせません。

- spool は `_regular_decision:1287` を呼ばない。
- fallback 不一致では既存の receipt 理由を保持する。
- `_find_exact_state` の例外は SearchResult の error／truncated として証拠へ記録し、上記関数へ渡す。
- `_regular_decision:1297–1305` の `not-landed` 条件は一切変更しない。

**削除 fragment**

`:1338` の次の処理は維持します。

```python
receipt_entry = state.old if state.required.missing else state.required
```

削除の receipt 証明対象は引き続き **old blob の内容**です。

削除への新しい exact fallback は今回除外します。

- `state.required` の missing を探索すると、単なる main tip の不在で受理できる。
- `state.old` を探索すると、分岐前の共通履歴だけで成功し得る。削除という required state の到達を証明していない。
- 後者を `exact-tree-state` として required state の証明に見せることも不適切。

どちらも I7 を保った拡張とは論証できません。receipt による既存の削除正例は維持します。

**evidence の層と decisive**

`:1397–1414` の配列順序は維持します。

1. `exact-tree-state`
2. `folded-receipt`
3. `any-path-object-observation`

`:148–158` の `SearchResult.as_json()` 自体は通常経路との互換性のため変更せず、spool の evidence を組み立てる際に `decisive` を上書きします。

| spool の結果 | exact decisive | receipt decisive |
|---|---:|---:|
| 正式 receipt 一致 | false | true |
| exact fallback 一致 | true | false |
| fallback timeout／parse error | true | false |
| fallback 完了・不一致 | false | true |
| receipt／fragment の integrity error | false | true |
| 削除など fallback 対象外 | false | true |

不一致行の `decisive: true` は**未着地の証拠ではなく、その indeterminate 理由を選択した層**を示します。実際の outcome と decision reason を併記します。

`:1377` の無条件 `True` は上表の条件式へ変えます。二層同時 decisive を防ぎ、非決定観測は常に false のままにします。

**pending probe と出力一覧**

`:1363` の条件に「最終 unit verdict が `indeterminate`」を加えます。

- exact fallback で解決した fragment は probe しない。
- 未解決 fragment は従来どおり補助手掛かりを出す。
- `ledger_probe` の結果を decision 関数へ渡さない。
- `_aggregate_verdict:1515–1539` は変更しない。

一覧の扱いは次のとおりです。

| 出力 | 方針 |
|---|---|
| `unproven_paths`（`:1900`） | 定義維持。全 unit が解決した path は消える |
| `receipt_missing_paths`（`:1908`） | 定義維持。exact で着地証明できても receipt 不一致なら残る |
| `unresolved_fragment_candidates`（`:1767–1837`） | pending から作る構造は維持。exact 解決済み fragment は除かれる |

`receipt_missing_paths` と `unproven_paths` が同じ集合とは限らなくなります。

`check_branch_rescue.py:1501–1568` はこれらの配列を解釈せず、verdict・conclusive・rc 等を検査しています。**consumer 実装の変更は不要**です。新しい出力を実 checker 経由で受け取る統合テストを追加します。

## S3 のプラン (file:line)

**値はこの段で決めません。** 親の段 6 で、以下の順に導出します。

1. 同じ対象 OID・main OID・候補上限で変更前後を比較する。
2. M1 の 2 branch、M3 の正負例に加え、通常ファイル、receipt 正例、receipt 不一致、mode 不一致多数、履歴上限超過を分ける。
3. cold／warm 相当と反復数を記録し、総時間、phase 時間、process 数、候補数、一致順位、残余理由を取得する。
4. timeout と「証拠がない」を分離する。後者は時間を増やしても解決しない。
5. 候補上限と batch サイズを先に選び、その後に assessment 予算を選ぶ。

| 変更候補 | 導出手順 |
|---|---|
| landed `:35` `DEFAULT_HISTORY_CANDIDATES=1024` | 対象 path の候補分布と最初の exact 一致順位を測る。上限増加で新たに証明できる unit 数と費用を比較する |
| landed `:33` `DEFAULT_TIMEOUT_SECONDS=60.0` | S1/S2 後の単独 assessment の完了時間分布と余裕から決める |
| rescue `:34` 既定 8 秒 | Python 起動・JSON 出力も含む実 child 完了時間から決める |
| rescue `:2096` 上限 60 秒 | 長い assessment を完了させる実需がある場合だけ引き上げる |

**到達可能性の制約**

- landed CLI は `:1945–1951` で **300 秒以下**しか受けない。rescue 上限だけ 300 秒超へ上げる案は不可。
- landed 候補数 CLI は `:1979` で **1～100,000**。
- rescue は `:1520` で `min(指定値, overall_remaining)` に制限される。
- rescue 全体予算は `:2094` で **1～900 秒**。後続 commit に必要な予算が実際に残るかを測る。
- COMMAND timeout 5 秒は別の制限。assessment 予算増加では解消しない。
- rescue が渡す timeout と外側 subprocess timeout は同値で、起動・終了処理の時間差がある。単独 checker の時間だけから既定を決めない。

既存の `test_history_match_at_candidate_33_wins_before_65_plus_truncation:850` は 1024 を固定しています。定数を変更する場合だけ、親が採用した**具体値との等値 assertion**へ更新します。単なる正数検査へ緩めません。

## テスト計画 (nodeid)

以下の `L::` は `orchestrator/tests/test_check_branch_landed.py::`、`R::` は `orchestrator/tests/test_check_branch_rescue.py::` の省略です。追加 nodeid は提案名です。

**S1 の追加**

| nodeid | 必須 assertion |
|---|---|
| `L::test_batch_exact_history_match_preserves_witness` | landed、従来と同じ matched commit／candidate count |
| `L::test_batch_rejects_candidate_differing_only_in_mode` | 同じ OID/type でも mode 不一致なら不受理 |
| `L::test_batch_rejects_candidate_differing_only_in_type` | parser/helper fixture で type 不一致を除外 |
| `L::test_batch_rejects_candidate_differing_only_in_oid` | OID 不一致を除外 |
| `L::test_batch_validates_all_rows_before_accepting_match` | 先頭一致・後続壊れでも indeterminate |
| `L::test_batch_invalid_stdout_is_indeterminate[short]` | 行数不足 |
| `L::test_batch_invalid_stdout_is_indeterminate[reordered]` | 成功行連番または不在式の順序違い |
| `L::test_batch_invalid_stdout_is_indeterminate[malformed-missing]` | missing 行混在時の式不一致 |
| `L::test_batch_missing_without_exact_match_is_indeterminate` | 正常 missing と非一致 blob の混在で正例なし |
| `L::test_batch_missing_and_exact_match_is_landed` | 正常 missing があっても別候補の四要素一致を受理 |
| `L::test_batch_path_handling[colon]` | 実在例と同型の path を保持 |
| `L::test_batch_path_handling[utf8]` | 非 ASCII path を保持 |
| `L::test_batch_path_handling[space]` | legacy fallback で意味維持 |
| `L::test_batch_path_handling[newline]` | 行注入を起こさず legacy fallback |
| `L::test_batch_chunk_limit_and_command_count` | 1 回最大 1024、実呼出し回数と計数一致 |
| `L::test_batch_timeout_is_indeterminate` | 残時間・command timeout の双方を検査 |
| `L::test_batch_preserves_missing_tree_and_gitlink_states` | これらは従来経路を使用 |
| `L::test_batch_preserves_merge_introduced_state` | raw post-image だけでは拾えない merge 状態を保持 |

「type だけ違う」は実 object では同じ OID に別 type を持たせられないため、隔離した helper fixture で検査します。symlink／通常ファイルの差を type 差と呼ぶテストにはしません。

**S2 の追加**

- `L::test_spool_exact_history_without_receipt_is_landed`  
  M3 正例と同型。main 履歴で exact、その後削除。receipt 不一致でも landed。
- `L::test_unlanded_pure_add_spool_stays_indeterminate`  
  候補 0、pure add。`not-landed` を明示的に禁止し、pending probe を維持。
- `L::test_spool_fallback_has_one_decisive_layer`  
  上表の各分岐で decisive が一層だけ。
- `L::test_spool_exact_resolution_updates_unresolved_lists`  
  receipt missing は残り、unproven／unresolved からのみ消える。
- `L::test_spool_fallback_does_not_call_regular_decision`  
  `_regular_decision` を失敗 stub にしても spool が処理できる。
- `L::test_spool_exact_match_does_not_override_receipt_parse_error`  
  exact が存在しても壊れた registry を隠さない。
- `L::test_unreceipted_spool_deletion_has_no_exact_fallback`  
  main 不在・old blob 到達可能の双方で新規受理しない。
- `L::test_spool_fallback_probe_result_never_changes_verdict`
- `R::test_real_checker_spool_exact_fallback_is_complete`
- `R::test_real_checker_unlanded_spool_remains_rc2`

**既存テストの期待値**

S1/S2 によって、現在あるテストの verdict・reason assertion を変更する必要は見つかりませんでした。特に次は厳密な期待値を維持します。

- `L::test_rehomed_fragment_without_receipt_is_indeterminate_and_probed`
- `L::test_receipt_identity_mismatch_does_not_prove_fragment`
- `L::test_receipt_missing_fields_make_exact_hash_indeterminate`
- `L::test_one_invalid_receipt_bullet_invalidates_registry`
- `L::test_malformed_receipt_is_integrity_indeterminate`
- `L::test_receipt_blob_limit_is_reported_on_receipt_evidence`
- `L::test_receipted_spool_deletion_is_landed_from_old_blob`
- `L::test_content_and_mode_from_different_commits_do_not_compose`
- `L::test_same_blob_with_regular_file_instead_of_symlink_does_not_match`
- `L::test_history_candidate_limit_is_indeterminate_not_negative`
- `L::test_history_match_at_candidate_33_wins_before_65_plus_truncation`
- `L::test_exact_receipt_keeps_ledger_corpus_lazy`
- `L::test_ledger_corpus_uses_one_cat_file_batch`
- `L::test_probe_failure_does_not_move_exact_verdict`
- `R::test_m07_indeterminate_assessment_forces_rc2`

S3 で候補既定値を変更した場合だけ、前述の candidate-33 テストの定数 assertion が変わります。意味上の正例・負例は変えません。

正常な `missing` の混在を**無条件に** indeterminate とするテストは採りません。それは M3 正例および S1 の意味保存と矛盾します。壊れた混在と、正常だが exact 証拠のない混在を負例にします。

## 受理集合が広がる箇所とその論証

| 箇所 | 広がりと安全性 |
|---|---|
| S1 の高速化 | 制限時間内に処理できる正例が増える。必ず main 到達可能候補の同じ commit/path を `_tree_entry` で再確認するため、新しい証拠種別はない |
| S2 の通常 fragment | receipt 不一致でも四要素同時一致を受理する。D922 点 2(a) の証拠であり、path 不在・本文部分一致・identity だけでは受理しない |
| S3 の探索／時間上限増加 | 従来打ち切られた位置にある exact 証拠を発見できる。証拠条件、closure、集約、ref 再確認は維持する |

順序が壊れた batch をそのまま証明に使わず、最終的には候補 commit 自身の tree entry を比較します。mode と OID を別 commit から合成する経路はありません。

S2 でも unit 一件の成功を branch 全体の成功へ短絡しません。`:1533–1536` の全 unit の連言を維持します。

次は論証できないため採りません。

- 削除 fragment を main の path 不在だけで受理する。
- 削除 fragment を old blob の共通祖先での存在だけで受理する。
- receipt identity の一致だけで内容を受理する。
- parse error／timeout を不一致へ丸めて探索を続ける。
- probe や別 path の同一 object を正例へ昇格する。

## 親 brief への反論

| 対象 | 検査結果 |
|---|---|
| P1／M5 | 一次資料を優先する方針は妥当。ただし archive 原本は今回の射影外で、記載の正否は独立確認できない。「4 commit」と「3 件 indeterminate」は異なる母数なので同一視しない |
| P2 | 通常 fragment への exact fallback は D922(a) に合う。ただし exact 履歴は**fold 完了そのもの**の証明ではない。「内容状態が到達可能」と記述すべき |
| P2 の代案却下理由 | identity を索引にするだけなら証拠条件は必ずしも変わらない。最終 sha/schema 検査を省いて identity だけで受理する変更が違反。今回不要なので実装しない |
| P3／M2 | 121 倍は 10.92/0.09 の局所比較。end-to-end の倍率ではない。候補列挙を含めれば約20倍で、さらに mode 確認などが加わる |
| M1 | 2 branch の結果から「常に rc=2」は導けない。別 path 観測や exact 不在は、高速化だけでは解決しない |
| M2 | subprocess 費用が有力なのは支持されるが、0.09 秒は mode 証明を含まない。費用の全てが起動時間だとまでは証明していない |
| M2b | raw post-image への置換を避ける判断は支持。ただし「18種類の状態が欠落」と「18 merge commit を欠落」は同義ではない |
| M3 | exact **blob** 5 件だけでは四要素の正例実測として不足。mode/type/path の確認が必要。候補 0 の負例は indeterminate であり、未着地確定ではない |
| M4 | 記載定数はコードと一致。ただし landed CLI の300秒上限、rescue の全体予算、外側 timeout も制約 |
| M6 | D1231 と整合する。一方、「rescue rc=2 のため削除 gate が止まる」という因果説明は、§2 が rc を使わないという説明と整合しない。運用上の停滞との区別が必要 |
| M7 | 許可された consumer には直接の verdict 利用を確認した。ただし文字列参照検索だけで間接呼出しを含む凍結閉包の不存在までは証明できない。今回その全域監査はしていない |

加えて、通常ファイルは既に `:738` で main tip を先に照合しています。今回の実装は「通常ファイルを path 一次判定へ新設」するものではなく、**既存の履歴 fallback の高速化と、spool への限定的な適用**です。

brief の「非 blob（tree／symlink）」も修正が必要です。symlink は object type が blob であり、区別するのは mode です。

## 裁定パッケージ候補 (scope 外の real な所見)

1. **削除 spool の exact 証明義務**  
   現行 `:1338` は old blob の receipt を使います。missing state／old state のどちらを新しい exact fallback の対象にするかは、削除の意味と I7 を整理する必要があります。今回は変更しません。

2. **親子 timeout の終了余裕**  
   rescue `:1514` の子 deadline と `:1520` の外側 timeout は同じ指定値です。Python 起動・JSON 出力時間により、子の期限処理が返す JSON より先に親が kill する構造です。定数測定には織り込みますが、予算分割の再設計は別件とします。

3. **rescue rc と削除停止の因果説明**  
   D1231 が §2 接続を明示的に除外しています。改善の効果指標を「削除可否」ではなく、可視化完了率・未解決理由・所要時間に合わせる必要があります。rc や cleanup 本文は変更しません。

## 総括

S1 は **tagged batch による候補絞り込み＋同一 commit の mode 再確認**、S2 は **通常 fragment の receipt 不一致に対する正例専用 fallback**とします。

削除・非通常ファイル・integrity error の既存扱いは維持します。S3 の値は、親の段 6 で到達可能な CLI 範囲と実測分布から決めます。

ファイル変更・テスト実走はしていません。既存の判定期待値を緩める必要はありません。