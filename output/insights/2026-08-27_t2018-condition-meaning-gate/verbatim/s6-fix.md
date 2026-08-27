## 総括

裁定された fix を3ファイルの未 staged 差分として実装しました。staged snapshot の SHA-256 は pre-fix patch と完全一致し、git add・commit・merge・rebaseは行っていません。

| 区分 | 結果 |
|---|---|
| closed | 0。pytest未実走のためclosed申告なし |
| partial | must-fix 1〜8は実装・静的監査済み |
| regressed | 未判定 |

## Fix

- RESULT_IDENTIFIERをexact doubleへstatic_assertし、uint64_tによるdouble bits注入を拒否。
- 3入力をroot dirfdから各component O_NOFOLLOWで辿り、全fd確保後に読み取り。before/after/path identityとSHA-256をevidenceへ保持。
- compilerをversion前・version後・compile後にdev/inode/size/mtime/ctime/SHA-256で再照合。
- compiler証明の残余限界とversionが自己申告である点をdocstringへ明記。
- F707でcompiler seam呼び出しを即失敗化。
- duplicate markerを正しいdecoder 2blockだけの単一理由負例へ変更。
- bare supplyをsupply-value-mismatchへ分類。
- duplicate/missing/unknown row、compile/run timeout・rc・stderrを別node化。
- result-kind、parent symlink、compiler drift負例を追加。
- generic adapterのcaller-supplied protocol textという主張限界を[source_digest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2018-condition-meaning-author/orchestrator/campaign/source_digest.py:1899)へ明記。

## 受理と拒否

Supply armはBACKOFF_FIXEDが同名cache routeから要求値とexact一致する場合だけevidenceを返します。missing mappingはmacro-not-supplied、bare・wrong route・wrong valueはsupply-value-mismatchで拒否します。

Meaning armはcaptured decoderのRESULT_IDENTIFIERがexact doubleで、各contextのobserved bitsが期待bitsと一致する場合だけ受理します。Supply armの結果は参照せず、型違い、marker重複、非finite、row異常、process失敗、compiler drift、pointwise mismatchを独立拒否します。

通る正例はBACKOFF_FIXED=5、start=1/2、両方のbitsが`4014000000000000`です。

## 検査

- `git diff --check`: 異常なし。
- staged diff SHA-256: pre-fix snapshotと同一の`c138ff3428f85420b7f8ee1bc7771940cef0568a3b86a374dba02ef7b71b2465`。
- 未 staged変更は[condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2018-condition-meaning-author/orchestrator/campaign/condition_meaning_gate.py:1)、[source_digest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2018-condition-meaning-author/orchestrator/campaign/source_digest.py:1899)、[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2018-condition-meaning-author/orchestrator/tests/test_condition_meaning_gate.py:1)のみ。
- production caller検索: 0。

## 未実走・赤

次のwrapper検査はいずれも`rc=16 / child_started=false`でした。

- 新test file全体
- sort wrapperの共有parser焦点node
- source_digest adapter焦点node
- collect-only

原因は`qstat -Q preflight rc=1`です。pytest childは一件も起動していないため、緑・既存赤とも申告しません。

## 所有外波及

driver integrationは引き続きnoneで、現行1000点は未保護です。sort wrapper、fixture、driver、docs、patch、ledger、grid、encodingは未 staged fixで変更していません。

テストwrapperがignoredな`output/pegasus-dispatch/`へ失敗receiptを生成しましたが、限定patchには含まれません。既存のuntracked `output/insights/...`には触れていません。
