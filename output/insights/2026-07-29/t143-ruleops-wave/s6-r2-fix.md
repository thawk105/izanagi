第2裁定の accepted 7 finding をすべて実装し、指定検証は全件成功しました。今回編集したのは所有範囲内の2ファイルだけです。commit・docs・output・submoduleには触れていません。Codex hook は未配線として手動で保護契約を遵守しました。

### finding 対応表

| Finding | 対応 |
|---|---|
| RA-2 | emit直前にHEAD、non-shallow、replace refs、graftsを再検査。途中変化3種をHEAD不変のまま拒否 |
| RA-8 | tracked/custom ledgerのHEAD entryを`1,048,576 bytes`以下かblob read前に検査 |
| RA-9 | real-checkoutにcontrolled candidateをcommitし、blob・hit・pickaxe commitを独立Git照会とliteralから構築 |
| RB-2 | raw pickaxe cacheをsnapshot内のtoken単位へ変更。candidate別control filteringを後段化。global token unionを履歴照会前に検査 |
| RB-5 | production `inspect`は独立oracleとの比較だけに使用し、ledger expectedへ再利用しない |
| RR-1 | receipt headの実在、祖先関係、candidate blob、後続変更pathを検査。全receipt pathをledger-wide allowlist化 |
| RR-2 | ledger pathとreceipt、guard、node module、insight sourceのaliasを無条件拒否。別path custom ledgerは受理 |

主な実装位置は [tools/ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:34)、回帰検査は [test_ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:452) です。

### 変更ファイル

- `tools/ruleops.py`
- `orchestrator/tests/test_ruleops.py`

`tools/run_tests.py`、`tools/check_docs.py`、対応する既存テストには第2修正として追加編集していません。

### 検証結果

- `test_ruleops.py`: 80 passed、58.17秒
- `test_run_tests_preflight.py`: 83 passed、0.36秒
- `test_check_docs.py`: 125 passed、11.81秒
- plain runner coverage: 3 passed
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check -- <所有6パス>`: 違反なし
- staged差分・commit: なし

最大許容packageは実checkout上で、candidate 2件、各query 1件、signal token union 6件を実構築しました。runner preflight child実測は **2.375秒**、rc=0で60秒未満です。

### 受理・拒否境界

| 修正前 | 修正後 |
|---|---|
| candidate最大8、query最大4 | candidate最大2、query最大1、ledger-wide token最大6 |
| emit前はHEADだけ再確認 | HEADと3履歴境界を再確認 |
| HEAD ledger blobをsize確認前に取得可能 | oversize HEAD entryをpayload取得前に拒否 |
| pickaxe cache keyにcontrol集合を含む | raw historyはtokenごと一度だけ取得 |
| receipt headはOID形式のみ | 実在祖先commit、candidate blob、epoch pathを検査 |
| ledger/candidate alias中心 | 全evidence pathとのledger aliasを拒否 |
| E2E expectedがinspect由来 | controlled content＋独立Git/literal oracle |

index/staged-tree binding、D97 classifier、preflight task-run記録、mutation producer、削除・apply・approval・safety claimは変更していません。

### 親が同期するdocs項目

- candidate上限 `2`
- candidateごとのquery上限 `1`
- ledger-wide signal token union上限 `6`
- HEAD ledger blob上限 `1,048,576 bytes`と先読拒否
- emit前のnon-shallow／replace refs／grafts再検査
- read-only Git closed setへの`merge-base`、`diff-tree`追加
- receipt headの祖先・tree blob・epoch allowlist契約
- 複数candidateが同じpre-receipt headを共有できる二段commit境界
- ledger/evidence alias全面拒否
- 新reason: `signal-token-limit`、`ledger-evidence-alias`、`receipt-head-missing`、`receipt-head-non-ancestor`、`receipt-candidate-blob`、`receipt-epoch-path`

開始前から存在した親所有のdocs、README、output artifact差分はそのまま残っており、今回新たな所有外変更はありません。残作業は親によるdocs同期とfocused re-reviewです。mutationは第2裁定どおり再レビュー完了までblockedです。

## 総括

accepted 7 findingはコード・独立negative・最大package実測で閉鎖しました。指定検証は全緑、最大runner childは2.375秒、所有外の新規変更・commit・hook発火主張はありません。