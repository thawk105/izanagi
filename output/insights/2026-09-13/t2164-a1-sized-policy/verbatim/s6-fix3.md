## 総括
指定の hash 更新を所有 3 ファイルに適用しました。  
README の再計算値は指定値と一致しました。  
`load_policy(V3_SIZED_STUDY_ID)` は成功しました。  
テスト起動はインフラ障害で停止したため、**実装済み・未実走**です。

## 変更した file と要点

- `paper_story_a1_paired.py`：README hash と policy bytes hash の定数を更新。
- `paper_story_a1_paired.v3-sized.json`：`preregistration.sha256` だけを更新。
- `test_paper_story_a1_paired.py`：旧 README hash literal 1 箇所だけを更新。policy hash literal はありませんでした。

## 実走した検査

```bash
PYTHONDONTWRITEBYTECODE=1 IZANAGI_TASK_RUN_AUTO_RECORD=0 python3 tools/run_tests.py orchestrator/tests/test_paper_story_a1_paired.py -p no:cacheprovider
```

対象は同ファイルの全 nodeid。runner は rc=16、`child_started=false` で終了し、passed／failed 件数はありません。

別途、hash 整合と `load_policy` の成功を実測しました。

## 赤と、その帰属

`qstat -Q preflight rc=1` による dispatch インフラ障害です。テストの成否は未判定です。runner が生成した今回分の dispatch ファイルは除去しました。

## 実測した hash

README：

```text
6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2
```

README 定数・policy binding・テスト literal と一致。

policy bytes：

```text
a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a
```

`V3_SIZED_POLICY_SHA256`・loader が返す digest と一致。

## 旧 hash の残存検索

`rg --hidden --no-ignore` で worktree 全体を検索（`.git` 除外）。一致 0 件。所有 3 ファイル以外にも残存はありません。

## 親へ返す項目

実行可能な環境で対象テスト全体を再実走してください。commit・branch 操作・push はしていません。