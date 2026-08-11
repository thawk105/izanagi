実装は完了しました。変更は所有 3 ファイルだけで、docs・実 repo の `output/`・commit は変更していません。

### 所見対応

| 所見 | 状態 | 対応 |
|---|---|---|
| F-2 | **partial** | closure の HEAD/worktree bytes 完全一致を要求し、dirty 正例を拒否期待へ反転。手動 smoke 成功、pytest 未実走 |
| F-3 | **partial** | v2 専用 4 module を遅延 import 化。依存 import 失敗下で v1 search/generate/verify/receipt を実行する subprocess test を追加。手動 smoke 成功 |
| F-4 | **partial** | production serializer 非依存の非 ASCII・key 順・数値表現・末尾 LF を含む raw bytes literal と SHA-256 literal を追加 |
| F-5 | **partial** | total/per-holdout 双方で `-0.0` を拒否。両 negative case の手動 smoke 成功 |
| F-6 | **partial** | MU-2 の死んだ namespace 分岐を削除、MU-5 authority gate を一箇所へ集約、MU-3 の symlink parent／既存 leaf test を分離 |
| F-7 | **partial** | 固定 candidate parent を dirfd・`O_NOFOLLOW` 下で安全作成。fixture の事前作成を削除。手動 smoke 成功 |

全行が `partial` なのは、実装子契約に従い pytest 未実走の所見を `closed` としていないためです。`regressed` はありません。

主な変更箇所は [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-fix-a/orchestrator/campaign/s8b_holdout_freeze.py:1119)、[test_s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-fix-a/orchestrator/tests/test_s8b_holdout_freeze.py:784)、[s8b_v2_freeze_fixture.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-fix-a/orchestrator/tests/s8b_v2_freeze_fixture.py:221) です。

### 検査と赤の内訳

- `git diff --check`: rc=0
- base `66ec0e0e` との v1 保護対象関数・定数 AST 比較: 完全一致
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- tmp root 手動 smoke: 全対象成功。ただしpytestの緑には数えていません。
- 焦点 pytest:
  `test_s8b_holdout_freeze.py -k 'v2_candidate or v1_apis_import_and_execute_when_v2_dependencies_fail_to_import' -rf`
  は wrapper rc=16、実行 node 0 件。
- 同範囲の `--collect-only` と `test_plain_runner_coverage.py -rf` も rc=16、実行 node 0 件。
- 原因はいずれも `qstat -Q preflight rc=1`。queue 投入はありません。
- pytest の観測赤は 0 件、infra failure が3件です。事前指定された期待赤集合は空です。

### 静的な波及可能性

- 所有外 production caller: `s8b_floor_campaign.py`、`s8b_oracle_driver.py`、`s8b_ratified_freeze.py`、`t080_freeze_migration.py`。
- v2 builder/generator の所有外 caller は現状なく、同 module の CLI からのみ到達します。
- 共有 fixture consumer: `test_s8b_oracle_manifest.py`、`test_s8b_oracle_driver.py`、`test_s8b_oracle_report.py`。既存共有 API は変更していません。
- 統合後の再走対象は holdout freeze、oracle manifest、ratified freeze、oracle driver/report/judge、plain-runner coverage です。

## 総括

F-2〜F-7 の A 側コードと回帰テストを実装しました。  
v1 保護本体・schema 定数は base と AST 完全一致です。  
変更は所有 3 ファイルのみで、実成果物・docs・commit はありません。  
pytest は環境 rc=16 のため未実走で、全所見を `partial` と報告します。