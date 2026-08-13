## 追加したテスト

`orchestrator/tests/test_s8b_binary_admission.py::test_validate_rejects_external_ccbench_pin_mismatch`

`orchestrator/tests/test_s8b_binary_admission.py::test_validate_rejects_external_contract_sha256_mismatch`

## 単一理由の根拠

- ccbench pin: honest record が通常検証を通ることを先に確認しています。receipt と record は変更せず、呼び出し時の `expected_ccbench_pin` だけを変更します。outer SHA、policy、source、subject、binding、genome、src token の検査を通過後、ccbench pin 外部照合 gate で指定メッセージが送出されます。
- contract SHA: 同じく honest record の通常検証を先に確認し、`expected_contract_sha256` だけを変更します。ccbench pin には正しい値を渡すため先行 gate を通過し、直後の contract 外部照合 gate で指定メッセージが送出されます。
- 両テストとも record、receipt、binding、subject の field は変更せず、outer SHA も再計算していません。

## 実走結果

同一の `python3 tools/run_tests.py` 呼び出しへ上記 2 nodeid を指定しました。

- ccbench pin mismatch: `rc=16`
- contract SHA mismatch: `rc=16`

`qstat -Q preflight rc=1` により pytest collection 前に dispatch infrastructure failure で停止しました。未実走のため緑とは申告しません。

## 総括

対象ファイルへ負例テストを 2 本追加しました。  
変更は外部期待値を差し替えられる `_validate()` helper と新規テストだけです。  
構文解析、NFC、結合文字不在、`git diff --check` は確認済みです。  
既存テストの期待値、production code、docs は変更していません。  
`git add` と commit は行っていません。  
開始時から存在した未追跡 wave artifact には触れていません。