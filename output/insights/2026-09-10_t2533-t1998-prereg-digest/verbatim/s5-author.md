## 前提と読んだ資料

指定された以下の資料はすべて読めた。読めなかった path はない。

- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s4-adjudication.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/artifacts/AUTHORITATIVE-VALUES.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s1-brief.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s2-plan.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s3-lensA.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s3-lensB.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1790.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1874.md`
- [t1998_stock_inline_pair.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-unit-a/orchestrator/campaign/t1998_stock_inline_pair.py)
- [test_t1998_stock_inline_pair.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-unit-a/orchestrator/tests/test_t1998_stock_inline_pair.py)
- [t1998-balanced-stock-inline-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-unit-a/docs/t1998-balanced-stock-inline-preregistration.md)
- `orchestrator/campaign/b10_backoff_shape_sweep.py` の parser / loader 周辺

## 変更した file と内容

- [t1998_stock_inline_pair.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-unit-a/orchestrator/campaign/t1998_stock_inline_pair.py:65)

  - canonical path、marker、schema version を scalar `str` 定数として追加。
  - D1790 の measurement/current SHA を独立した scalar `str` として追加。
  - 重複 key、非有限値、field 閉集合、型、hex 長を検査する厳密 parser を追加。
  - [load_preregistration:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-unit-a/orchestrator/campaign/t1998_stock_inline_pair.py:364) に ancestry、regular non-symlink、worktree/blob 一致、current SHA を要求する loader を追加。
  - [consumer の ratio 直前:1269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-unit-a/orchestrator/campaign/t1998_stock_inline_pair.py:1269) に、指定順の 3 gate を追加。既存比較は移動・変更していない。

- [test_t1998_stock_inline_pair.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2533-unit-a/orchestrator/tests/test_t1998_stock_inline_pair.py:52)

  - fixture の job body、gitlink、環境契約、両 arm source digest を正本値へ変更。
  - `repository_commit` は実行時の `git rev-parse HEAD` を使用。
  - 実 Git blob から contract-loader binding を構築し、旧 commit 負例も stub なしで生成。
  - 下記 6 test を追加。

docs と acceptance ledger は変更していない。

## 追加したテスト

- `test_old_job_body_digest_is_rejected_from_reservation`

  旧 digest を artifact 側だけに置き、既存 `launcher-script-identity-mismatch` / `reservation.binding.script_sha256` を単独で確認。

- `test_baseline_source_digest_drift_is_rejected`

  baseline の `source-identity-unbound` 比較と arm 帰属を確認。

- `test_document_identity_mismatch_is_rejected_after_artifact_checks`

  artifact と渡された identity を alternate gitlink で整合させ、文書由来 identity gate だけを発火。

- `test_measurement_commit_without_preregistration_blob_is_rejected`

  文書導入前かつ現行 contract-loader bytes を持つ実 ancestor を使い、measurement-time blob gate だけを発火。

- `test_load_preregistration_rejects_worktree_blob_mismatch`

  current 文書 bytes を作業木へ置き、異なる committed blob を持つ実 Git repo で loader の byte equality gate を確認。

- `test_load_preregistration_returns_document_identity_from_real_head`

  実 repo の `HEAD` から正本どおりの全 identity と実行時 commit が返ることを確認。

target 側 drift は既存 `test_preregistered_source_digest_drift_is_rejected` と重複するため追加していない。別の current-arm 正例も既存正例と重複するため追加していない。2 定数の値が異なることを要求するテストは D1790 に反するため書いていない。

## 実走した検査

- `python3 tools/run_tests.py -q <対象8 nodeid>`

  rc=16。`qstat -Q` preflight 失敗で `child_started=false`、pytest は未起動。追加 6 node、既存 launcher provenance、既存正例はすべて「実装済み・pytest 未実走」。

- pytest ではない直接 test-function 確認

  追加 6 node、既存 launcher provenance、既存正例、source identity 正例、typed trace 正例、unstable 両 armの計 12 呼出しが成功。

- parser の pytest ではない自走確認

  重複 key、余剰・欠落 field、schema 不一致、非 `str`、不正 hex64、block 0 個・2 個の計 8 負例を拒否。最初の準備用 harness 2 回は import path／変異位置の誤りで検査不成立となり、修正後に成功。

- `git diff --check`：成功。
- Python `compile(...)` による両変更 file の構文検査：成功。
- `python3 -m ruff check ...`：`ruff` 未導入のため未実走。
- 凍結文書の working tree / `HEAD` blob SHA：双方 `464e3af5…719c`。
- 最終 `git status --porcelain`：変更は所有する 2 file のみ。

## 受理・拒否挙動の変化

変更前は、artifact と呼出側が手組みした identity が相互一致すれば、canonical 文書を経由せず受理できた。

変更後は既存 artifact 比較がすべて通った後に、次も要求する。

1. 現行文書 bytes が current SHA と一致する。
2. 文書由来 identity と渡された identity が `repository_commit` 以外で完全一致する。
3. artifact の `repository_commit` にある文書 blob が measurement-time SHA と一致する。

したがって coherent な別 identity、文書導入前 commit、文書 drift は新しい別々の code で拒否される。既存 launcher 負例は従来どおり `launcher-script-identity-mismatch` / `reservation.binding.script_sha256` が先に発火する。

## 所有外への波及

- consumer の全 caller は、実行 repo に exact current 文書と Git blob が存在する必要がある。
- consumer 呼出しごとに current document 読取りと `git show` が発生する。
- test module の collection は Git repo の `HEAD` 解決に依存する。
- `_write_producer` は file-local fixture であり、共有 fixture は変更していない。
- 新 nodeid は acceptance ledger 未登録。段 6 の実走結果に従って親が判断する。
- docs、`acceptance_duration_ledger.json`、producer、submitterには変更なし。
- rc=16 で生成された dispatch receipt 一式は exact path から除去済み。

## 総括

D1790 の 2 SHA を独立した一値 pin として実装した。  
strict parser と fail-closed loader を consumer module 内へ追加した。  
既存拒否の順序を保ったまま、ratio 直前に 3 段の文書束縛を追加した。  
必須 6 node は実装済みで、直接確認は成功した。  
pytest は dispatch infrastructure の rc=16 により未実走であり、closed とは申告しない。