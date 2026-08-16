現行受理挙動: read-only probe で実在 g2 は構造判定・composite とも `True`、head serial 1・activation record 1 本を維持しました。  
現行拒否挙動: 今後の successor は自己整合、method、content-addressed path、typed receipt のいずれかを満たさなければ `False` になります。

## 実装内容

- 構造判定 `_is_valid_activation_successor` は無変更です。
- [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-seam-checknet/orchestrator/campaign/env_contract.py) に composite callback を追加しました。
- 通常 loader、`ident.py` の production 2 箇所、issue tool を composite へ変更しました。
- registered catalog ∪ ever-active の走査を 3 件、required 2 件で固定しました。
- 未 active g2 drift 負例と、4 面それぞれ単一理由の負例、実在 g2 正例を追加しました。
- `_verify_entry_calibration`、歴史 resolver、runtime attestation、activation head／record、凍結 bytes は変更していません。
- docs 編集・commit はしていません。

CFAB executable fixture は、実在 g2 の production composite 事前確認だけを追加しました。凍結 invocation kwargs は汎用構造 callback のままとし、positive／negative の宣言 digest 一致を確認済みです。

既存期待値の変更は指定された3件だけです。別途、artifact を持たない 65-env 合成 scale test は専用 composite テストと分離する fixture monkeypatch を追加しましたが、期待結果は変更していません。

## 検査結果

pytest の実走緑は 0 件です。以下の selector を `tools/run_tests.py` で投入しましたが、テスト開始前に `rc=16` となりました。

- `test_env_contract.py::test_registry_effective_clock_self_failures_are_exact_known_exception`
- `test_env_contract.py::test_registered_never_active_g2_clock_drift_is_detected`
- `test_env_contract_activation.py::test_activation_admission_rejects_each_missing_basis`
- `test_env_contract_activation.py::test_real_pegasus_g2_passes_activation_admission_without_advancing_head`
- `test_env_contract_activation.py::test_production_loader_passes_source_head_constants_to_leaf`
- `test_env_contract_activation.py::test_issue_main_passes_production_successor_adapter_by_identity`
- `test_env_contract_activation.py::test_real_pegasus_g2_serial2_is_accepted_and_switches_lookup`

内訳は、bounded local の予約台帳 `/run/user/31609` を sandbox から更新できず、dispatch も `qstat -Q` の UID 認証失敗で停止、です。pytest assertion の赤は未観測で、上記はすべて「実装済み・未実走」です。

静的確認は AST parse 6/6、`git diff --check`、結合文字なし、所有6ファイルのみの変更です。新規・改名 test file はないため plain-runner のファイル集合は不変です。

所有外への波及候補は、`ident.verify_recorded_activation_tuple` を呼ぶ `artifact_admission.py`、campaign-lock consumer tests、`test_calibration_freeze_authority_execution.py`、issue tool の合成 65-env fixture です。

## 総括

- composite activation admission の4面を実装しました。
- production 3経路はすべて composite へ統一済みです。
- 実在 g2 は非変更 probe で通過し、head serial 1を維持しました。
- catalog 検査網は2件から3件へ拡大しました。
- activation record、凍結成果物、docs は未変更です。
- pytest は環境 `rc=16` のため実装済み・未実走です。
- 残る赤はテスト assertion ではなく実行基盤だけです。