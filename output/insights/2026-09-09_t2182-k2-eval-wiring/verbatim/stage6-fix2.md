## 所見の対応表 (closed / partial / regressed)

| 所見 | 状態 | 理由 |
|---|---|---|
| M4 / M5 負例の単一理由性 | partial | 修正済みだが dispatch 障害で未実走 |
| M1 production 4 define 正例 | partial | 正例追加済みだが dispatch 障害で未実走 |

regressed はありません。

## 実装した内容

- [test_p3_s4_loop_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-fix2/orchestrator/tests/test_p3_s4_loop_job_contract.py:1008)
  - K2 負例の repo root を `tmp_path/repo` に変更。
  - `git`、`cmake`、`python3.10`、`qstat` sentinel を追加。
  - sentinel 非実行の確認を stderr 検査より先に配置。
- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-fix2/orchestrator/tests/test_p3_s4_loop.py:7890)
  - `dependency_prefix` なしの production 形を追加。
  - condition gate と campaign build の4 define が完全一致することを検査。
  - 既存の5 define 正例は維持。
- 禁止対象の実装、job body、docs は変更していません。commit もしていません。

## 実走結果

指定コマンドを実行しました。

```text
python3 tools/run_tests.py -rf orchestrator/tests/test_p3_s4_loop.py orchestrator/tests/test_p3_s4_loop_job_contract.py
```

結果は rc=16、`qstat -Q preflight rc=1`、`child_started=false` でした。テスト本体は起動していないため、実装済み・未実走です。実走 nodeid は0件、passed 件数もありません。

補助的な静的検査では、変更した2ファイルとも AST parse に成功しました。

## 変異を入れたときに観測されるもの

- 空 manifest の request-set detection を弱体化すると、K2 preflight を通過して `git` sentinel が実行され、先頭の sentinel 非実行 assertion が赤になります。
- K2 pair に対する proposal 必須検査を除去すると、`git` sentinel が実行されて赤になります。
- 空 classification の拒否を除去すると、`git` sentinel が実行されて赤になります。
- 空 de-novo claim の拒否を除去すると、`git` sentinel が実行されて赤になります。

## 総括

両所見へのテスト修正は完了していますが、指定 runner の dispatch infrastructure 障害により受入実走できていないため、状態は partial です。親で同じ2ファイルの実走が必要です。