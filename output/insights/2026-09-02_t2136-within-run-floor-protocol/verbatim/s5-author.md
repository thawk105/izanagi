## 変更前の挙動

- certify 成果物は genome を記録せず、schema は genome 付き文書を拒否していた。
- 層 3 は calibration 直下だけを走査し、contract pin と registered calibration を参照しなかった。
- genome 付き候補の根拠は一律 `canonical-floor-genome` だった。

## 実装した内容

- [cli.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2136-author/orchestrator/calibrator/cli.py:373)
  - receipt の build argv から canonical genome を導出。
  - protocol 登録、全軸、追加 define、TRACE=0、target、binary basename、整数性、重複を検査。
  - binary SHA 照合後、benchmark 前に一度だけ導出。
  - certify の preflight・accepted・rejected 全成果物へ同じ genome を記録。
  - 非 certify 出力は genome 不在のまま維持。
- [schema_v2.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2136-author/orchestrator/calibrator/schema_v2.py:742)
  - legacy shape と genome 付き shape の二つだけを exact 受理。
  - canonical 順序、整数、重複、空 body、予約名 `TRACE` を検査。
  - legacy の `CalibrationV2.genome` は `None`。
- [layer3_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2136-author/orchestrator/campaign/layer3_report.py:343)
  - v2 lock から ever-active contract pin を解決。
  - 候補を「直下 glob と exact pin」の和集合とし、実 path で重複排除。
  - registered 全 glob はせず、between-run は直下限定を維持。
  - pin の repo/env 境界、通常 file、SHA-256 を fail-closed 検査。
  - receipt 有無による三つの protocol match basis を分類。
- 禁止対象、docs、既存成果物、layer3 schema は未変更。

## 追加・変更したテスト

- [test_calibrator_certify.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2136-author/orchestrator/tests/test_calibrator_certify.py:431): M1〜M4、mocc、全軸、TRACE、malformed argv、非 certify 不記録。
- [test_schema_v2.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2136-author/orchestrator/tests/test_schema_v2.py:172): M5、二つの exact shape、TRACE を含む canonical 負例。
- [test_layer3_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2136-author/orchestrator/tests/test_layer3_report.py:3029): M6〜M9、pin SHA/path、registered 非 glob、linux-baremetal 実 CV 保全。
- M10 の既存 `genome-absent-legacy-record` 期待値は変更していない。
- 期待値は独立 literal と実在 artifact bytes を使用した。

## 実走した nodeid と結果

pytest の実走 nodeidはありません。

`tools/run_tests.py` から焦点 nodeid、編集対象3ファイルの collect、内容/AST meta-test を3回試行しましたが、いずれも pytest child 起動前に rc=16 となりました。

- login-node予約台帳をsandboxから更新不能
- `qstat -Q` が認証またはsocket接続エラー
- dispatch childは一度も起動していないため、緑とは報告しない

非pytest診断では、compile、M1〜M9相当のproduction helper統合、実contract pin、meta-test関数、`git diff --check` が成功しました。

## 未実走のもの

- 編集対象3テストファイルのpytest全走
- `test_env_attestation.py` の固定bytes回帰
- `test_env_contract.py`、`test_ccbench_spawn_sites.py` のmeta-test
- 下記consumer閉包
- repository全受入、docs/Codex agent checker

## 波及可能性の静的列挙

- schema consumer: `test_env_attestation.py`、`test_env_contract*.py`、`test_execution_guard.py`、Pegasus/S8b/T126/T419関連テスト。
- layer3 consumer: admission diagnosis、official perf closure、autonomous workload、S8b oracle、S8c receipt、T126、trial registry関連テスト。
- 共有fixture: certify receiptのbuild argvとbinary名、layer3のv2 authority/env-tag整合を更新。
- 将来のPegasus v2 campaignはactive g1 pinのCV `0.011705837968885854`を新規候補にする。既存成果物は再生成していない。
- 非silo値の公式投入にはlauncher一般化、再取得、contract generationとactivationが引き続き必要。

## 総括

T-2136の配線実装とM1〜M10のテスト追加は完了していますが、pytestは環境上起動できていないため「実装済み・未実走」です。

既存registered 2件のSHA-256はそれぞれ `753f535a…`、`94a4b79f…` のままです。commitは作成していません。