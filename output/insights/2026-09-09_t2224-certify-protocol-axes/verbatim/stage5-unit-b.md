## 総括

`--protocol {silo,mocc,tictoc}` と既定 `silo`、receipt 記録、明示時だけの qsub env 伝播を実装した。  
単位 A の既存差分は読み取りのみで保持し、指定された 4 ファイル以外は編集していない。commit / push も未実施。  
静的検査は緑。ただし Pegasus の認証・メモリ制約で pytest child が起動せず、必須テストは未実走。したがって `closed` とは申告しない。

## 変更したハンク

- [tools/pegasus/submit_certify.sh:7](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-unit-b/tools/pegasus/submit_certify.sh:7)
  - 変更前: rratio のみ受理。
  - 変更後: protocol の usage、既定値、明示フラグ、exact whitelist を追加。
  - 理由: staging 作成前に未登録値を rc=2 で拒否するため。

- [tools/pegasus/submit_certify.sh:143](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-unit-b/tools/pegasus/submit_certify.sh:143)
  - 変更前: receipt に rratio のみ記録し、qsub env は常に2変数。
  - 変更後: pre-submit / submit receipt に実効 protocol を常時記録。明示時だけ protocol env を末尾追加。
  - 理由: job 側 `calibration.protocol` 再照合と、省略時 qsub argv 互換を両立するため。

- [test_pegasus_calibration_workload.py:35](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-unit-b/orchestrator/tests/test_pegasus_calibration_workload.py:35)
  - 変更前: silo 固定 literal と rratio 契約中心。
  - 変更後: submitter whitelist、shell case の実 parse、`SPACES` との独立照合、実 shell argv 導出、byte 互換検査へ拡張。
  - 理由: protocol 軸化後も既存 silo 契約を弱めず、非 silo の混入を検出するため。

- [test_pegasus_tools.py:1382](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-unit-b/orchestrator/tests/test_pegasus_tools.py:1382)
  - 変更前: fixture receipt / job result は rratio のみ。
  - 変更後: protocol fixture と job-result assert を追加し、protocol 不一致負例を新設。
  - 理由: 単位 A の必須 binding を既存負例と同じ強さで検査するため。

- [tools/pegasus/README.md:125](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-unit-b/tools/pegasus/README.md:125)
  - 変更前: silo 前提の rratio 操作のみ。
  - 変更後: 受理集合、既定、mocc 例、cicada の軸名不一致、silo 限定 `BACKOFF_FIXED` を記載。
  - 理由: launcher の実効契約と除外根拠を利用者へ示すため。

## 新設したテスト

- `test_submitter_accepts_exact_protocol_whitelist_and_records_it[{silo,mocc,tictoc}]` — 3値の受理、両 receipt、明示時 env を固定。
- `test_submitter_rejects_unregistered_protocol_before_side_effects[{cicada,ermia}]` — staging 前 rc=2 を固定。
- `test_submitter_omitted_protocol_is_silo_without_changing_qsub_argv` — 既定値と旧 qsub argv 全体を固定。
- `test_certify_shell_protocol_axes_match_independent_genome_spaces` — shell の実表と `SPACES.axes` の完全一致を検査。
- `test_certify_non_silo_defines_contain_no_axis_outsider[{mocc,tictoc}]` — 実 configure argv の軸外 define を拒否。
- `test_certify_derives_protocol_target_and_binary_path[{silo,mocc,tictoc}]` — target / binary path の導出を検査。
- `test_certify_keeps_backoff_fixed_and_condition_gate_silo_only` — define と gate の silo 限定性を固定。
- `test_default_silo_build_and_calibrate_argv_are_byte_compatible` — 旧 configure/build/calibrate argv を完全比較。
- `test_certify_submit_binding_requires_matching_calibration_protocol` — receipt と job protocol の不一致停止を検査。

## 実走した検査

実行ホストは `pegasus02`。

- `bash -n tools/pegasus/submit_certify.sh`: rc=0。
- `git diff --check`: rc=0。
- 変更した Python 2本の `compile(...)`: rc=0。
- `python3 tools/check_codex_agents.py`: rc=0。
- `python3 tools/check_docs.py`: rc=0、`check_docs: 違反なし`。
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/run_tests.py orchestrator/tests/test_pegasus_calibration_workload.py -rf`: rc=16、child node なし・未実走。
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/run_tests.py orchestrator/tests/test_pegasus_tools.py -rf`: rc=16、child node なし・未実走。
- 指定 `test_ccbench_spawn_sites.py` 2 node: rc=16、child node なし・未実走。
- `test_plain_runner_coverage.py` と duration-ledger 被覆率 meta-test: rc=16、child node なし・未実走。

直接の `python3 -m pytest` は Pegasus 規律により使用せず、必須 runner を使用した。停止原因は `qstat -Q` の `EACCTAUTH Unknown user-id`（rc=1）で、login-side headroom も 0 bytes だった。

## 波及の静的列挙

- 所有外 caller: 単位 A の `certify_calibration.sh` が、新しい `calibration.protocol` と明示時の環境変数を消費する。
- consumer: `collect_receipt.py` は submit receipt / job result を final receipt に包含するため、protocol が加法的に伝播する。
- acquisition 系: `make_acquisition_receipt.py` と schema は protocol 別 configure/build argv を受けるが、裁定どおり未変更。
- shared fixture: `test_pegasus_tools.py` の binding / job-result fixture は protocol 必須形へ更新済み。
- meta-test: pytest-only allowlist 上の既存 file 集合は不変。新規 node は duration ledger に未登録で、被覆率検査は未実走。
- `test_check_docs.py` / `test_hooks.py` の admission/path registry は引数内容を消費しないため静的には不変。