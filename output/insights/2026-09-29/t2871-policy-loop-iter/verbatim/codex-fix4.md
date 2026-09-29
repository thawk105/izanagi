## 総括

R13・R14 に対応し、指定されたテスト 1 ファイルの代役だけを修正しました。**実装済み・未実走**です。

## 変更内容 (file:line)

- [test_p3_s4_loop_policy.py:733](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix4/orchestrator/tests/test_p3_s4_loop_policy.py:733): `applied` の終了時に対象 source file の元の bytes を復元します。
- [test_p3_s4_loop_policy.py:750](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix4/orchestrator/tests/test_p3_s4_loop_policy.py:750): 候補・stock それぞれの `run_campaign` 呼出しで模擬 pipeline を新しく開きます。
- [test_p3_s4_loop_policy.py:772](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix4/orchestrator/tests/test_p3_s4_loop_policy.py:772): 子 process ごとに pristine source を新しい checkout dir へ複製します。

## 代役が production と同じ流れになった根拠 (checkout 回数、evidence の判定、authority の有無)

driver の `main` は子 process 内で checkout を 1 回開き、同じ `sub` で候補、stock の順に評価します。代役もその回数を assert し、次の子 process には別の複製を渡します。evidence 代役は候補に非 stock token、stock に `STOCK` を返します。build 代役は候補だけに coder authority があり、stock にはないことを assert します。admission、auditor gate、実際の `loop.run_campaign` は変更していません。

## 実走した検査と結果 (未実走はそう書く)

`python3 -m py_compile orchestrator/tests/test_p3_s4_loop_policy.py` は成功しました。pytest と計算ノードの焦点走は**未実走**です。

## 未解決・判断が要る点

判断が要る点はありません。T1〜T3 の成否は親による焦点走で確認が必要です。