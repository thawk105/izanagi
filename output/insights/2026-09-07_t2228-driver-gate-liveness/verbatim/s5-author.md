## 実装した file と要点

- [t2228_driver_gate_liveness_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2228-author/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py)
  - 1 process で s1 → repro → sweep を順次実行。
  - driver ごとの自己完結 clone から production module を再 import。
  - `sys.setprofile()` で実 return object のみ観測。
  - driver 終了直後に JSON を atomic・create-only publish。
- [t2228_driver_gate_liveness_probe.pbs](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2228-author/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs)
  - `gen_S`、1 node、3時間、`bnode` 限定。
  - driver ごとに alternates のない node-local clone を作成。
  - Python を子 process として実行し、EXIT trap を維持。
  - repo 外への PBS stdout/stderr 指定例を記載。
- [test_t2228_driver_gate_liveness_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2228-author/orchestrator/tests/test_t2228_driver_gate_liveness_probe.py)
  - M1〜M7 を個別 test として実装。
  - production の `ConditionArmRecord`、`ConditionFamilyAdmission`、`schedule_for_role`、`_is_inert_value` を使用。
  - file 集合メタテストに対応する self-run harness を追加。

## 段 4 裁定の各要求への対応

- s1:
  - verified freeze を4 roleで展開し、18 cellの configuration、workload、対象 macro、値、inert 判定を実データから記録。
  - `write-heavy:backoff_fixed_best` と `write-heavy:p2_2_flag_opt` だけを `prepare_cell()` に通し、`run_role()` は呼ばない。
- repro:
  - 現行 pin `511c953` の関門前拒否を別項目で記録。
  - その後 `dff0f1e` へ切り替え、production context を一度だけ実走。
- sweep:
  - `WORKLOADS[0]` の写しを使い、指定された最小 screening を一度だけ実行。
  - admission return 時点で profiler を解除。
  - `aborted == 0` と `committed == 2` を成功条件に含めた。
- `ok` は全 driver とも初期値 `False`。規定条件を満たした場合だけ `True` に変更。
- 例外は型、message、実 `reason_code` 属性、cause/context を保存し、message 解析はしない。
- hostname、toolchain manifest、CMake identity、network 観測、scratch 容量、production 4 file の SHA-256、unestablished macro、campaign summary を記録。
- retry、引数緩和、cache 注入、別 root fallback、production monkeypatch は設けていない。
- production の受理・拒否集合は変更していない。production 4 file の差分検査は rc=0。

## 走らせた検査 (nodeid と rc)

- `orchestrator/tests/test_t2228_driver_gate_liveness_probe.py` 全体:
  - runner rc=16。
  - `qstat -Q` preflight 失敗で child 未起動。M1〜M7 は実行数0。
- `orchestrator/tests/test_t2228_driver_gate_liveness_probe.py` collect-only:
  - rc=16、同じく child 未起動。
- `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`:
  - rc=16、child 未起動。
- Python 2 file の AST parse: rc=0。
- Python 2 module の import確認: rc=0。
- PBS `bash -n`: rc=0。
- production 4 file の `git diff --quiet`: rc=0。
- 所有 path と production の状態確認:変更は新規3 fileのみ。

## 未実走・未確認

- M1〜M7 の pytest 実走は未実走。
- file 集合メタテストは実装上の self-run 対応まで確認し、実走は未完。
- 計算ノード上での3 driver実測と evidence JSON生成は未実走。
- PBS投入、3時間 walltime 内完走、実 toolchain/network 条件での結果は未確認。
- 正規 runner がキューを「観測不能のため可用」と扱った一方、dispatch preflight が失敗したため、直接 pytest は実行していない。

## 波及可能性の静的列挙

- caller:
  - `qsub` 側で exact HEAD、repo 外 evidence dir、repo 外 stdout/stderr を渡す必要がある。
- 共有入力:
  - `output/s1-freeze/measurement_freeze.json`
  - `tools/pegasus/policy.json`
  - gflags/glog source、third-party cache
  - ccbench の `511c953`、`dff0f1e`、freeze pin object
- consumer test:
  - `test_plain_runner_coverage.py`
  - `test_hooks.py` の Pegasus admission registry
  - acceptance duration ledger の coverage 検査
- 新 probe は admission registry 未登録のため、Pegasus login nodeからの直接実行は現状の hook に拒否される。計算ノードへの PBS 投入が実行経路。
- production caller、共有 fixture、registry は所有外なので変更していない。

## 総括

段4裁定に沿う probe、PBS、M1〜M7 test を所有3 pathへ実装しました。production、docs、既存テスト期待値は変更せず、commit・pushも行っていません。

ただし正規 test runner の dispatch infrastructure failureにより pytest と計算ノード実測は未実走です。このため、実装済みですが `closed` とは申告しません。