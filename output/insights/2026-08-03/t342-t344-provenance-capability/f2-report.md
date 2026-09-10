F2 の所有範囲内で 4 test file を更新しました。docs・production・index・commit・branch は変更していません。

### 対応表

| 型・件数 | 状態 | 対応 |
|---|---:|---|
| `test_build_site_gate.py` 旧 constructor・48 errors | closed（静的） | clean・現行 pin の stock evidence から capability を導出し、context/evidence を build API へ伝播 |
| `test_screening_driver.py` 旧 constructor・48 errors | closed（静的） | machine receipt fixture と現行 contextへ移行。tail-repair の既存 attempt も正規 receipt topology 化 |
| screening config policy 欠落・1 failed | closed（静的） | 比較する両 config に同じ policy を束縛 |
| `wal.replay` lambda signature・1 failed | closed（静的） | `admission_policy` keyword のみ受け入れ、従来どおり空 replay を返す |
| guided online digest・1 failed | closed（静的） | receipt を捏造せず、forward-only 契約に沿う明示的な pre-policy fixture に変更 |
| real-repo collection・1 failed | closed（因果上・静的） | 原因だった2 test moduleのcollection errorを解消。対象ファイル自体は未変更 |
| guided identity・3 failed | partial | policyだけ足すと receiptless terminal WALになるため未修正 |
| transport・4 failed | partial | 所有外 `p3_autonomous_workload_trial.py` のno-build config不備。テスト側迂回は撤回 |
| P3 namespace・1 failed | partial | 所有外 `p3_s4_red.py` がraw layoutを新consumerへ渡すproduction回帰 |
| plain-runner・1 failed | partial | 所有外の新規3 testにself-runnerがなく、docs allowlistも編集禁止 |
| regressed | 0 | assert削除・緩和・skip・xfailなし |

合計は closed 100件、partial 9件、regressed 0件です。

変更ファイル:

- [test_build_site_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f2/orchestrator/tests/test_build_site_gate.py:84)
- [test_screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f2/orchestrator/tests/test_screening_driver.py:39)
- [test_screening_opt_in.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f2/orchestrator/tests/test_screening_opt_in.py:44)
- [test_guided.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f2/orchestrator/tests/test_guided.py:79)

### 受理・拒否の意味

- 旧 stock constructor: 任意 commit の自己申告へ広げず、clean・現行 repo pin・stock tokenを満たす正例だけを受理。login/suspect拒否は変更していません。
- Screening: 両 campaignへ同一 policyを足したため、ID差は従来どおり screening軸だけに由来します。
- Replay lambda: seamの範囲は変えず、新keywordだけを受け取ります。
- Tail repair: receiptless COMMITを正例にせず、正規 `BUILD_START → BUILD_DONE → COMMIT` を置いたうえで、tail修復とprefix保持を検査します。
- Guided digest: 歴史的pre-schema受理を明示し、新schema receiptをfixtureで捏造していません。

### 検査

pytest nodeidの実行結果はありません。次を計算ノードへdispatchしましたが、pytest開始前に `qstat -Q preflight rc=1` で失敗し、実行数は0件でした。

```text
test_build_site_gate.py
test_screening_driver.py
test_screening_opt_in.py
test_guided.py
test_claude_transport.py
```

成功した静的検査:

- 変更・所有 test fileの `python3 -m py_compile`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- `git diff --check`

未実行: 所有pytest全nodeid、full suite、CCBench build、campaign実走、mutation。

### 直さず報告した項目

- [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f2/orchestrator/campaign/p3_autonomous_workload_trial.py:1245): no-build時にcontextを落とすためtransport 4件がpartialになります。driver/CLI所有外です。
- [p3_s4_red.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-f2/orchestrator/campaign/p3_s4_red.py:169): `AdmittedCampaign`ではなくraw layoutをconsumerへ渡しています。
- Guided 3件: 過去build receiptを持たないreplay WALを新topologyへ正直に移行するschema判断が必要です。偽receiptは作りませんでした。
- plain-runner: `test_artifact_admission.py`、`test_build_admission.py`、`test_p3_build_authority_cli.py`は所有外。README allowlistはdocs編集禁止です。
- 固定goldenなど、期待値誤りを疑う項目はありません。

## 総括

1. 96件のconstructor errorは、caller自己申告ではなくevidence由来capabilityへ移行しました。
2. policy・replay・tail topologyは検査意味を維持し、assertや受理条件を緩めていません。
3. 所有外production修正またはschema裁定が必要な9件は迂回せず残しました。

残存する想定赤は transport 4件、guided 3件、P3 namespace 1件、plain-runner 1件です。