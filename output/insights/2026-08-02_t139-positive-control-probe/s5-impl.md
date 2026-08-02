現行の受理・拒否挙動は変更していません。ledger は exact-one のまま、`patches/*.patch` の未登録裸マクロは拒否され、probe が順序成立しても artifact や qualification として受理されません。単独性、nm、liveness、全標本順序のいずれかが不成立なら driver は非ゼロ終了します。

実装したのは使い捨て probe のみです。

- [3-arm patch](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/tools/pegasus/probes/t139_positive_control.patch:1)
- [probe driver](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/tools/pegasus/probes/t139_positive_control_probe.sh:1)
- [PBS job script](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/tools/pegasus/probes/t139_positive_control_probe.pbs:1)

driver は性能用 stock/mode1/mode2 と、全 arm の専用 `ADD_ANALYSIS` liveness build を分離します。性能 stock は pristine source、`stock-live` は報告専用の patched sourceであり、throughput には使いません。各 workload で5 repを `shuf` interleaveし、実順序を記録します。判定は全標本分離、すなわち `max(mode1) < min(mode2) < max(mode2) < min(stock)` 相当の二境界です。

所有外への静的な波及可能性は以下です。

- 既存 caller はなく、PBS → driver の新規専用経路だけです。
- `tools/pegasus/policy.json`、CCBench、gflags/glog、third-party clone は読み取り・scratch copyのみです。
- 現在の consumer test はありません。
- CCBench pinや `transaction.cc` の該当 contextが変わればpatch適用がfail-closedになります。
- 新規 raw 出力先は `output/env/pegasus/t139-positive-control-probe/$JOB_TAG` です。既存 rung1 treeには書きません。

## 総括

(a) 作成ファイルと行数:

- patch: 100行
- driver: 78行（100行以内）
- PBS script: 55行

(b) 置き場の根拠:

[test_p3_s4_loop.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_p3_s4_loop.py:943) が `patches/*.patch` だけを列挙し、ledger登録または固定allowlistを要求していました。そのため自動登録面外の `tools/pegasus/probes/` に置きました。`patches/**`、ledger、既存rung1 bytesは無変更です。

(c) 検査:

- `bash -n`：driver/PBS両方 `rc=0`
- `patch --dry-run`：現行CCBenchに対して `rc=0`
- 静的確認：対象TUは `transaction.cc` のみ、新規裸マクロは2個、禁止pathのdiffなし
- pytest/nodeid：0件。緑主張なし
- 未実施：submodule系test、CMake/build、nm実測、benchmark、PBS投入、全pytest、`check_codex_agents.py`、`check_docs.py`
- `shellcheck`：環境に存在せず未実施
- docs編集・commit・qsub：未実施

(d) serializable不変の論拠:

mode1は単一mutex、mode2はstorage＋key bytesの安定写像による2 mutexです。いずれも元のCASを同じlvalue・`expected`・`desired`で1回だけ直接実行します。mutex所有者はnonblocking CAS後すぐ解放し、record lockを待たないためmutex↔record-lockのdeadlock cycleは構成されません。一方、既取得record lockを持つ待機者の飢餓は排除できないため、全3 arm・両workload・全48 workerの専用liveness runを受理条件にしました。

(e) 親が投入前に確認すべきこと:

- CCBenchがpin `d706650…`かつcleanであること
- policy記載のgflags/glogと3 third-party sourceがpinned-cleanであること
- third-party rootを `qsub -v IZANAGI_THIRDPARTY_SOURCE_ROOT=/shared/...` で明示すること
- repo rootから投入し、同時benchmarkがないこと
- 実測後、nm witness、全288 worker-liveness行、`order.tsv`、`throughput.tsv`、`verdict.tsv`を確認すること
- 順序成立でも「正例artifact完成」や性能主張に昇格させないこと