## 総括

R1〜R4 と sized policy を実装しました。
状態は **実装済み・未実走**です。closed とは申告しません。
凍結 README・証明書・受領証の hash は不変です。
最終差分は所有する 3 file のみで、commit・branch 操作はしていません。

## 変更した file と要点

- `orchestrator/campaign/paper_story_a1_paired.py`：十進文字列受理、float の正値・有限検査、D1452 の型込み照合、policy・事前登録 pin。
- `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`：指定値で新規作成。pilot との差分が指定項目だけであることを静的確認。
- `orchestrator/tests/test_paper_story_a1_paired.py`：既存負例を保持し、実 policy 正例・登録値改変・精度・不正値・bytes pin 等のテストを追加。

## 実走した検査

```bash
PYTHONDONTWRITEBYTECODE=1 IZANAGI_TASK_RUNS_ROOT=/tmp/a1-sizing-certificate-task-runs python3 tools/run_tests.py orchestrator/tests/test_paper_story_a1_paired.py -n 4 -p no:cacheprovider --basetemp=/tmp/a1-sizing-certificate-pytest
```

対象 nodeid 範囲：同テストファイル全体。
結果：runner **rc=16**、pytest 未起動。実走 nodeid なし、passed / failed とも **0 件**。

AST 構文解析、`git diff --check`、指定差分・凍結 hash の静的確認は成功しました。

## 赤と、その帰属

`qstat -Q` が rc=1 となり dispatch に失敗しました。実行基盤の障害で、テストによる実装判定は未取得です。
自動生成された dispatch 証跡は `/tmp/a1-sizing-certificate-dispatch-0a5fd33f852dd73548ab4836dc56c890` へ移動済みです。

## 実測した hash

policy bytes と `V3_SIZED_POLICY_SHA256` は、ともに次の値で一致しました。

```text
1586347d6c6c6b9d45b9bfacaa0dd4bb299652046b3667079efe56280f8e872d
```

## 親へ返す項目

- 実行基盤復旧後のテスト全体実走と変異受入。
- sized 本走の source 契約・staging・binding・amended build 受理形の整備は範囲外のままです。本走起動可能とは申告しません。