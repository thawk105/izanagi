## 差分の要約

変更は裁定で許可された4ファイルだけで、staged・未追跡ファイルはありません。

- [s8b_ratified_freeze.py:3558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8b_ratified_freeze.py:3558): g1限定の選択 identity APIを86行追加。
- [s8c_result_judge.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8c_result_judge.py:25): 新API import、共通loader、verify/publishへの配線。21行追加、3行削除。
- [test_s8b_ratified_verify.py:872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8b_ratified_verify.py:872): g1 mismatch・valid g1・g2 no-opの42行を追加。
- [test_s8c_result_judge.py:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8c_result_judge.py:437): fixture追随とverify/publish test。113行追加、10行削除。

禁止された `s8b_holdout_freeze.py`、oracle manifest/driver群、`p3_autonomous_workload_trial.py` は無変更です。`git diff --check` は成功しました。

## 所見

1. **対象 [test_s8c_result_judge.py:1692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8c_result_judge.py:1692)**  
   **何が誤りか:** `foreign = _verified_floor(...)` が selection assertionをforeign ratifiedへ束縛した後、[同:1710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8c_result_judge.py:1710) はloaderだけを別の `SimpleNamespace` へ差し替えています。したがって publish時はbinding比較 [s8c_result_judge.py:2209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8c_result_judge.py:2209) に到達せず、fixtureのidentity assertionが失敗し、広い `pytest.raises(_ResultTableError)` が別理由の例外を受理します。既存testが偽緑になる追随です。  
   **放置時の成果物影響:** 書けない。productionのbinding比較自体は残っていますが、その削除・破損をこのtestが検出できず、受入証拠が不正確になります。  
   **判定:** **must-fix**。  
   **推奨する直し方:** current documentも `_patch_ratified_floor()` でloaderとselection assertionを同じratifiedへ束縛し直し、例外文を `floor receipt is not from the current ratified freeze` まで固定してください。

## g2 不変性の判定

**破れていない。**

- loaderが返す `RatifiedFreeze.generation_number` はplainなdataclass fieldで、[load_ratified_freeze:1412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8b_ratified_freeze.py:1412) がresolution由来の組込み`int`を格納します。
- 新APIはexact型検査後、[s8b_ratified_freeze.py:3572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8b_ratified_freeze.py:3572) で非g1を即returnします。`Path(root)`、source読取、namespace列挙、fd openはいずれもその後です。
- s8cの両経路は従来どおりloaderを先に呼び、g2では新APIが無観測で戻ってから従来のbinding処理へ進みます。
- [g2 test:1461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/tests/test_s8b_ratified_verify.py:1461) も実体のloader-produced g2を使い、最初のsource inspectionをsentinel化しています。

手作りでfieldを破壊した `RatifiedFreeze` はloader契約外であり、実在g2の反例にはなりません。

## 恒真判定

| 新APIの分岐 | 実際に拒否される入力 | 判定 |
|---|---|---|
| exact型検査 | `object()`、`SimpleNamespace`、`RatifiedFreeze` subclass | `floor-artifact-invalid`。恒真でない |
| `generation_number != 1` | loader-produced g2 | 拒否せずno-op |
| source record/path解決 | 欠落field、絶対path、official run形式でないsource path | `floor-selection-unverifiable`。恒真でない |
| generation blob/hash/protocol解決 | 別root、欠落blob、記録hash不一致、invalid protocol、解決不能なhistorical contract | `floor-selection-unverifiable`。恒真でない |
| eligibility underivable | earlier resultはあるがmanifest/journal/admission導出が壊れている | `floor-selection-eligibility-underivable` |
| rule mismatch | より早いderived-eligible runがある | `floor-selection-rule-mismatch` |
| その他の選択検証失敗 | namespace欠落・symlink・列挙不能、selected namespace不一致 | `floor-selection-unverifiable` |
| 正常系 | valid g1で、より早いeligible runがない | `None`で成功 |

値の同一性も静的に成立しています。

- `selected_rel` と `selected_path_info` はlaunchと同じgeneration record・同じparserから導出されています。
- protocolは同じgeneration blobです。loaderがG/H/worktree一致を [s8b_ratified_freeze.py:1033](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8b_ratified_freeze.py:1033) で固定済みです。historical resolverはcurrent contract拒否を持ち込まず、protocolの返却値自体は同じvalidatorのdocument由来です。
- `v1` はlaunchと同じ `ratified.document`。
- [新APIの呼出し:3625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8b_ratified_freeze.py:3625) は `validate_selected_certificate` を指定せず、[既定値:1930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-residual3-impl/orchestrator/campaign/s8b_holdout_freeze.py:1930) はFalseのままです。

## 既存テストの期待値変更

assert反転、期待例外変更、skip/xfail追加、test削除はありません。

ただし実質的な期待値緩和が1件あります。所見1の `test_publish_requires_current_ratified_floor_receipt` は、fixture追随不足により本来のcurrent-binding mismatchではない `_ResultTableError` でも通る状態です。

## 既裁定との抵触

- **D1325:** loader-produced g2は新規I/O・namespace列挙・例外なし。抵触なし。
- **D1312:** `_verify_generation_semantics` と `reverify_published_freeze` の本体は無変更。historical testも内容不変で、新APIからhistorical経路への配線はありません。
- **D1311:** earliest derived-eligible規則、再導出bit、namespace条件を既存helperの同じ引数で使用しています。
- **D1313 / D1241:** 追加行に `current launch validation`、`current admission`、`certified`、`certifying` または同義の上限解除表現はありません。
- **規律2:** production差分はg1の受理集合を狭める方向だけで、既存gateを緩和・黙殺する変更はありません。
- **段4の編集範囲:** 許可4ファイルだけです。

production実装について既裁定へのmust-fix抵触は検出しませんでした。所見1はテスト証拠のmust-fixです。

## 残る不確実性

- pytestは実走しておらず、緑とは判定しません。
- 所見1を直すまでは、既存current-binding invariantの回帰検出を信用できません。
- protocol/historical resolverと実際のadmission台帳を含む例外変換は静的確認のみです。親による指定nodeidとconsumer全走が必要です。

## 総括

productionのg2・loader・historical不変性は静的には維持されています。  
新APIの選択引数と `validate_selected_certificate=False` もlaunch側と一致します。  
受理集合を広げる変更やD1313の上限密輸は検出しませんでした。  
ただし既存publish testに別理由で通る偽緑が1件あり、これはmust-fixです。  
fixtureを修正したうえで親が実走するまで、段6をcleanとは扱えません。