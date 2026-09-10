## 総括

`tools/pegasus/certify_calibration.sh` のみを変更し、protocol 3 種の受理・軸表・target/path 導出・receipt 照合・結果記録を実装した。  
既存の nonce、rratio、legacy env、source/qsub binding の受理・拒否条件は変更していない。古い protocol 無し receipt は新たに拒否する。  
静的 probe では既定 `silo` の configure/build/calibrate argv 互換性を確認した。  
必須テストは dispatch infrastructure failure で未実走のため、実装済みだが `closed` とは申告しない。commit・push は行っていない。

## 変更したハンク

- [tools/pegasus/certify_calibration.sh:162](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-author/tools/pegasus/certify_calibration.sh:162)
  - 変更前: protocol env を読まず、常に silo。
  - 変更後: 未設定時のみ `silo`、exact whitelist `{silo,mocc,tictoc}`。空文字・その他は `write_failure 2 submit_binding` 後に停止。
  - 理由: D-1/D-4 の受理契約。

- [tools/pegasus/certify_calibration.sh:196](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-author/tools/pegasus/certify_calibration.sh:196)
  - 変更前: submit receipt は `ycsb_rratio` まで照合。
  - 変更後: `calibration.protocol` と実効 protocol の exact string 照合を追加。欠落も拒否。
  - 理由: submit/job の binding を緩めず protocol まで延長するため。

- [tools/pegasus/certify_calibration.sh:546](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-author/tools/pegasus/certify_calibration.sh:546)
  - 変更前: silo define、`ycsb_silo.exe`、binary path、condition gate を直書き。
  - 変更後: 1 protocol 1 block の静的 `case` 軸表、`ycsb_${CALIBRATION_PROTOCOL}.exe` と対応 path の導出。`TRACE=0` は全 protocol に含め、`BACKOFF_FIXED` と gate は silo 限定。
  - 理由: D-2/D-3。現行 pin に存在しない macro を新 protocol へ広げない理由も4行コメントで記録。

- [tools/pegasus/certify_calibration.sh:864](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-author/tools/pegasus/certify_calibration.sh:864)
  - 変更前: job result の calibration は workload のみ。
  - 変更後: workload を維持して `calibration.protocol` を追加。
  - 理由: D-6 の結果記録契約。

## 実走した検査

node はすべて `pegasus02`。

- protocol validation fragment probe: rc=0
  - unset → `silo`
  - `silo` / `mocc` / `tictoc` → 受理
  - 空文字 / `ermia` → rc=2、`submit_binding`
- protocol別 argv fragment probe: rc=0
  - 全 protocol の define、target、binary path が指定表と一致。
  - gate は silo のみ発火。
  - silo の configure/build ordered argv は旧配列と完全一致。calibrate blockは未変更で、実効 binary pathも同一。
- 変更した2つの Python heredocに対する `compile(...)`: 各 rc=0
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- `bash -n tools/pegasus/certify_calibration.sh`: hook が job script 実行と判定して拒否。未実走。
- syntax node＋指定 define-sink nodeを `tools/run_tests.py` 経由で実行: rc=16。`qstat -Q` preflight failure、child未起動。
- 受入全走 `python3 tools/run_tests.py`: rc=16、child未起動。

## 期待赤と回帰の切り分け

単位 B 未実装に伴う事前列挙済みの期待赤:

- `test_job_rechecks_the_submission_workload_and_records_it`
- `test_calibrate_failure_survives_err_trap_and_writes_job_result`
- `test_certify_submit_binding_uses_narrow_request_id_normalization` の accepted case
- `test_certify_submit_binding_requires_matching_calibration_rratio`

旧 literal・fixture・receipt に必須 `protocol` が無いための赤である。テスト child 自体が起動しなかったため、期待赤も回帰赤も実観測は0件。rc=16はテスト失敗ではなく infrastructure failure。

## 波及の静的列挙

- caller `tools/pegasus/submit_certify.sh`: 現状は protocol を伝播・receiptへ記録しないため、単位A単独ではjob側の再照合で拒否される。単位Bの予定変更が必須。
- shared fixtures `orchestrator/tests/test_pegasus_tools.py`: receipt fixtureへ `calibration.protocol`、job-result harnessへ `CALIBRATION_PROTOCOL`、期待 checks dict へ新キーが必要。
- consumer test `orchestrator/tests/test_pegasus_calibration_workload.py`: 旧 job-result literalとsilo固定契約の更新が必要。
- gate test `orchestrator/tests/test_ccbench_spawn_sites.py`: condition gate呼出しはbuildより前に残したが、指定nodeは未実走。
- `tools/pegasus/collect_receipt.py`: job resultを最終receiptへそのまま包含するためprotocolも伝播する見込みだが、専用assertは未確認。
- acquisition receipt writer/schema: configure/build argvのprotocol別内容を受ける。裁定どおり未変更で、単位Bのconsumer test対象。