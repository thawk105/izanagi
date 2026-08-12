## 総括

実装子 B のコード・テスト変更は完了しました。commit・docs 編集はしていません。

主な実装:

- 単一 registry を `DIRECT_MATERIALIZER` / `CODER_ENTRYPOINT` で型付き拡張。
- coder entry point 6 件を登録。`QUARANTINE_GATED` は未導入。
- 既存 direct-materializer projection と診断 dict schema を維持。
- registered helper を追加し、flag 指定時だけ未登録 site を `BuildAdmissionError` で拒否。
- site を process-local authority/context に束縛。receipt・WAL・cache identity・COMMIT・freeze は不変。
- production 6 CLI を registered helper に置換。red/kickoff の正例は維持。
- AST 母集合を tracked Python 全 474 件へ拡張し、registered call site と registry を完全一致検査。
- autonomous driver を `_DRIVERS` に追加。
- `getattr` / `importlib.import_module` による authority 動的解決を検出。

変更前後の受理集合:

- 変更前: flag 付き既存 6 entry point は通過。任意 caller も低位 helper を直接呼べた。
- 変更後: 登録済み 6 entry point は従来どおり通過。red/kickoff も通過。未登録 site を registered helper に渡した場合だけ token 発行前に拒否。
- 低位 helper は単体 fixture 用に残存。同一 process caller の直接利用限界も残存。
- downstream artifact admission は変わらず、成果物隔離や認証境界は成立していません。そこは T-841 の範囲です。

除外 registry は exact 10 件です。

- `test_artifact_admission.py`: admission consumer fixture
- `test_build_admission.py`: 低位 helper 自体の単体 fixture
- `test_buildcache_v2.py`: buildcache fixture
- `test_campaign.py`: pipeline fixture
- `test_p3_autonomous_workload_trial.py`: CLI を迂回する run_trial fixture
- `test_p3_build_authority_cli.py`: 両 helper の閉包テスト自身
- `test_p3_exploration_namespace.py`: iteration 用 reusable context
- `test_p3_s4_loop_trigger_gating.py`: trigger iteration fixture
- `test_s1_direct_comparison.py`: historical comparison fixture
- `output/.../smoke_driver.py`: 実在する歴史 runnable smoke fixture

静的な波及確認:

- `s5_permutation_coverage.py`、`s2_verify_calibration.py`、`s3_lock_coverage.py`、`t152_write_intent_coverage.py`: 診断 dict の exact schema と direct key 集合は不変。
- `s8b_materialization.py`、`test_s8b_floor_campaign.py`: coder site を除外した direct projection を維持。
- autonomous の所有外 unit fixture向け低位 helper compatibility exportも維持。
- `p3_s4_loop_sort.py` の historical source pinは repinしていません。
- 実装子 A 所有の3ファイルは既存差分を保護し、編集していません。

検査状況:

- `git diff --check`: 成功。
- 所有10ファイルの `py_compile`: 成功。
- pytest: **未実走**。以下はいずれも pytest 起動前に `rc=16` で停止しました。
  - 焦点2ファイル
  - AST closure単独 nodeid
  - collect-only
- 原因: Pegasus user slice が14 GiB天井を超過し、dispatchも `qstat -Q ... EACCTAUTH` で利用不能。
- よって緑 nodeid、M9/M10/M11 の実走 KILLED、検査削除による赤消失は申告しません。
- 実装子 A の既知赤3件も今回は未観測です。これ以外の回帰赤も、pytest未起動のため未判定です。

変異の単一理由性は静的には次の形です。

- M9: 未登録 site の拒否欠落だけで token/pipeline 経路へ進む。
- M10: scan集合と `git ls-files '*.py'` の不一致で最初に落ちる。
- M11: exact除外 path の suffix/nested decoy が誤除外される理由だけで落ちる。

いずれも実走確認待ちです。