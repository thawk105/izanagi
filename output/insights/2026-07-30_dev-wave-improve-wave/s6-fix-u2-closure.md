結論は **NO-GO（1項目 partial、実走未了）** です。current bytes は大部分を閉じましたが、qsub timeout時の unique job-name 自動照合は未実装です。

### 変更ファイル

実装・設定:

- [tools/run_tests.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/run_tests.py)
- [tools/pegasus/test_dispatch.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py)
- [tools/pegasus/submit_tests.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/submit_tests.py)
- [tools/pegasus/run_tests_job.sh](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/run_tests_job.sh)
- [tools/pegasus/test_dispatch_policy.json](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch_policy.json)

テスト:

- [test_pegasus_test_dispatch.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_pegasus_test_dispatch.py)
- [test_pegasus_tools.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_pegasus_tools.py)
- [test_run_tests_nproc.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_run_tests_nproc.py)
- [test_run_tests_preflight.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_run_tests_preflight.py)
- [test_run_tests_task_run.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_run_tests_task_run.py)

[tools/pegasus/policy.json](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/policy.json) は変更成果物ではなく、HEADとbyte-exactに復元済みです。

今回さらに収束させた問題は、task-run optional eventのproducer/validator不一致、初期化済みsubmodule gitlinkの誤inventory、qsub中signalで`SUBMIT_UNKNOWN` finalを残さない窓、accounting lines digestの未再計算です。

### 段6裁定 U2

| # | 裁定項目 | 判定 | 根拠 |
|---|---|---|---|
| 1 | 既存policy復元・別dispatch正本 | closed | HEAD SHAと一致。新正本のexact key検査は [load_policy](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py:461) |
| 2 | execution closure・開始前/終了後検証・job symlink拒否 | closed | [closure生成/検証](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py:1777)、[runner終了時検証](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/run_tests.py:990)、[symlink test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_pegasus_test_dispatch.py:758) |
| 3 | local Git config・attributes無害化 | closed | [config検査](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py:789)、[attributes検査](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py:1323) |
| 4 | aggregate/per-file/copy後/cleanup/spool/retention | closed | [preclone quota](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py:1401)、[gitlink branch test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_pegasus_test_dispatch.py:638)、spool/retention実branch tests |
| 5 | NQSV stderr accounting | closed | [accounting validator](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py:2898)、[欠落・別ID test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_pegasus_test_dispatch.py:817) |
| 6 | qstat allowlist・transient・absolute deadline | closed | [parse_qstat](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py:2829)、[monitor](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py:3712) |
| 7 | qsub補償状態機械・resume | partial | timeout/signalは`SUBMIT_UNKNOWN`、既知ID後はqdel、resumeは再qsubしない。ただしunique job-name自動照合が未実装 |
| 8 | runner/final exact schema・status domain | closed | [runner validator](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py:2964)、[final validator](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/test_dispatch.py:3289) |
| 9 | qsub/receipt/journal hash chain | closed | qsub request/result、policy/job/manifest、spool、accounting、WAL headをfinalまで検証 |
| 10 | closed env・interpreter・host/affinity/task-run | closed | [interpreter選択](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/submit_tests.py:42)、[closed env](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/tools/pegasus/submit_tests.py:220)、[task-run branch test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_pegasus_test_dispatch.py:1125) |
| 11 | safe ADDOPTS/core option・外部入力拒否 | closed | argv parserと [実branch test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_pegasus_test_dispatch.py:677) |
| 12 | resource exact比較・fake test実効化 | closed | [qsub exact test](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u2/orchestrator/tests/test_pegasus_test_dispatch.py:725)、exact scheduler/raw canonical filesystem、signal/timeout/accounting実branch tests |

`absent` はありません。

### 所有閉包

- U2指定所有面だけを編集。
- U1所有の未追跡 `tools/pegasus_policy.py`、`orchestrator/tests/test_pegasus_policy.py` は読み取りのみ。
- docs、insight、freeze、provenance、親owner、submoduleは未編集。
- commit / push / staging更新は未実施。

### 静的確認

通過:

- `/usr/bin/python3.10` による所有Python全8ファイルのAST parse
- Python 3.10 `-I -B` isolated import：runner / dispatcher / submitter
- `pyflakes`：対象8ファイル
- local call-signature静的照合
- `bash -n tools/pegasus/run_tests_job.sh`
- dispatch policy canonical JSON・exact 31 keys
- `git diff --check`
- `policy.json` HEAD byte比較：rc=0
- SHA-256：HEAD/currentとも `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac`
- resource literal検索：dispatch資源値は新policyだけ

未実走:

- pytest
- build
- qsub/qstat/qdel
- compute-node targeted/full/mutation/acceptance

### 残must-fix

qsub timeoutまたはID未取得終了時に、hash-bound unique job nameを使ってscheduler上の候補を自動照合する処理がありません。現在は安全側に`SUBMIT_UNKNOWN`を封印し、resumeによる自動再qsubを拒否してmanual reconciliationを要求します。段6裁定を完全にclosedにするには、この照合と多件・不明時のfail-closed branch testが必要です。

## 総括

current bytes はschema破断と明白な到達不能運用分岐を収束させ、U2裁定12項目中11項目を静的にclosed、1項目をpartialとしました。実走未了かつunique job-name照合未実装のため、live投入判定は引き続き **NO-GO** です。
