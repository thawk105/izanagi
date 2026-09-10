## 総括

F-1〜F-4 を指定範囲内で修正しました。commit / push はしていません。テストは dispatch infrastructure failure により子が起動せず、**実装済み・未実走**です。`closed` とは申告しません。

## F-1〜F-4 の変更したハンク

### F-1

- [certify_calibration.sh:589](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-fix1/tools/pegasus/certify_calibration.sh:589)
  - 変更前: 可変 `"$BUILD_TARGET"` を使う単一 `build_argv`。
  - 変更後: silo / mocc / tictoc の3分岐とし、各行に literal target を配置。
  - 理由: build-sink 検出条件を満たす。silo の展開後 token 列は従来と同一。

- [certify_calibration.sh:596](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-fix1/tools/pegasus/certify_calibration.sh:596)
  - 変更前: `BINARY` を別途組み立てた `BUILD_TARGET` から導出。
  - 変更後: 実際の `build_argv[4]` から直接導出。
  - 理由: build target と binary basename の食い違いを構造的に防止。

- [test_pegasus_calibration_workload.py:268](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-fix1/orchestrator/tests/test_pegasus_calibration_workload.py:268)
  - 変更前: shell 全体から `ycsb_silo.exe` literal が消えたことを要求。
  - 変更後: 3 protocol が各自の literal target をちょうど1つ持ち、他 protocol の literal を持たないことを検査。
  - 理由: literal 3分岐を許容しつつ検査を強化。

### F-2

- [test_pegasus_calibration_workload.py:208](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-fix1/orchestrator/tests/test_pegasus_calibration_workload.py:208)
  - 変更前: define の名前集合のみ検査。
  - 変更後: D-2 と同じ独立 literal 表に対し、protocol ごとの全 define を値込みで完全一致検査。
  - 理由: 値の反転や変更を検出するため。

- [test_pegasus_calibration_workload.py:235](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-fix1/orchestrator/tests/test_pegasus_calibration_workload.py:235)
  - 変更前: `SPACES` の軸名との一致だけ。
  - 変更後: shell から得た軸値を、`SPACES[protocol].enumerate()` 内のいずれかの `Genome.flags` と完全一致させる。
  - 理由: no-wait 制約など、軸名だけでは分からない制約外 genome を拒否するため。

### F-3

- [test_pegasus_calibration_workload.py:171](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-fix1/orchestrator/tests/test_pegasus_calibration_workload.py:171)
  - 変更前: silo 固定の `_silo_calibrate_argv()`。
  - 変更後: build 由来 binary を受け取る `_calibrate_argv(binary)`。`calibrate_argv` 構築前の `BINARY=` が一意であることも検査。
  - 理由: build 後の再代入による伝播破壊を検出するため。

- [test_pegasus_calibration_workload.py:297](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-fix1/orchestrator/tests/test_pegasus_calibration_workload.py:297)
  - 変更前: 最終 `--binary` は silo の byte互換テストだけで観測。
  - 変更後: 3 protocol すべてで、最終 `calibrate_argv --binary` と build 由来 `BINARY` を比較。
  - 理由: mocc / tictoc の最終伝播を閉じるため。

### F-4

- [README.md:170](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-fix1/tools/pegasus/README.md:170)
  - 変更前: 成功時だけ post-attestation と `job-result.json` を生成。
  - 変更後: post-attestation は成功時だけ、`job-result.json` は calibrator の成否にかかわらず生成。
  - 理由: 現行実装と一致させるため。

`submit_certify.sh` と `test_pegasus_tools.py` には段6で追加編集していません。

## 追加した検査が恒真でない理由

- literal build 分岐検査: mocc の target を `ycsb_silo.exe` に変えると、mocc 分岐が自分の literal を持たず赤になる。
- exact 値表: tictoc の `NO_WAIT_OF_TICTOC=0` を `1` に変えると完全一致で赤になる。
- `SPACES` 制約: 同じ変更で no-wait が `(1,1)` となり、列挙されたどの `Genome.flags` とも一致せず赤になる。
- 最終 binary 伝播: build 後に `BINARY` を silo path へ再代入する、または `calibrate_argv --binary` を固定 path に変えると赤になる。

## F-5 変異の再照準提案

- M1: clean fixture にコピーした `submit_certify.sh` の whitelistへ `ermia` を追加し、その変更をfixture commitへ含めてから `--protocol ermia --dry-run` を実行する。dirty-tree gateに遮られず、ermia が staging / qsub 構築へ到達したことだけを理由に kill できる。
- M8: [submit_certify.sh:20](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-fix1/tools/pegasus/submit_certify.sh:20) の `PROTOCOL_EXPLICIT=0` を `1` に変異する。省略時 receipt は silo のままなので不一致で先に落ちず、qsub exportへ protocol tokenが増えた byte互換違反だけで赤になる。

いずれも実装していません。

## 実走した検査

成功:

- `bash -n tools/pegasus/submit_certify.sh`: rc=0
- `git diff --check`: rc=0
- 両 test file の Python AST parse: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- 静的検索で build-sink 条件を満たす3行を確認

未実走:

- `bash -n tools/pegasus/certify_calibration.sh`: hook が dispatch-required 実行体として拒否。
- `test_pegasus_calibration_workload.py` 単独走: runner rc=16、`qstat -Q` が unknown user-id、`child_started=false`。
- `test_pegasus_tools.py` 単独走: 同上。
- 元の赤だった `test_production_build_sinks_include_certify_calibration_script`: 同上。
- collect-only 試行も同じ理由で子未起動。

失敗時に生成された4件の一時 dispatch directoryは削除済みです。

## 波及の静的列挙

- `submit_certify.sh`: `certify_calibration.sh` の直接 caller。protocol env・receipt bindingは段5のまま。
- `orchestrator/calibrator/cli.py`: receiptのbuild target、binary basename、protocolを消費する。今回の target と binary の束縛強化が波及する。
- `tools/pegasus/make_acquisition_receipt.py`: `build_argv` をreceiptへ保存する。silo token列は不変、非siloは各literal targetになる。
- `tools/pegasus/collect_receipt.py`: `job-result.json` のconsumer。失敗時にも存在する実装契約は変更せず、READMEだけを整合。
- `test_pegasus_tools.py`: shell syntax、submit binding、失敗時job-resultを共有fixtureで検査する。
- `test_ccbench_spawn_sites.py`: 今回の3 literal行をbuild sinkとして検出するconsumer。
- `test_hooks.py` / `test_check_docs.py`: path分類・admission registry・README整合のconsumer。分類自体は変更なし。
- `acceptance_duration_ledger.json`: 今回追加した5 test nodeの所要時間登録先になり得るが、所有外かつ指定5件外なので編集していない。