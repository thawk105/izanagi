## 総括

R11・R12 に対応し、[test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix3/orchestrator/tests/test_p3_s4_loop_policy.py:697) の test helper だけを修正しました。T1〜T3 の期待値と production の admission 判定は変更していません。

## 変更内容 (file:line)

- [同ファイル:697](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix3/orchestrator/tests/test_p3_s4_loop_policy.py:697): 子の checkout 代役を 1 回、root を 1 つに変更。evidence と build の判定を genome の方策 flag に合わせました。T2 の強制終了は候補 build で起こします。
- [同ファイル:772](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix3/orchestrator/tests/test_p3_s4_loop_policy.py:772): source の作成を親の `_policy_pair_case` に移し、1 回だけ実行するようにしました。

## 代役が production と同じ流れになった根拠 (checkout 回数、evidence の判定、authority の有無)

driver の `main` は checkout を 1 回開き、同じ `sub` で候補から stock の順に評価します。修正後の代役も 2 回目の checkout を拒否し、両 build の `ccbench_dir` に同じ root を要求します。候補 genome には非 STOCK evidence と coder authority、方策 flag のない stock genome には STOCK evidence と authority なしを要求します。

## 実走した検査と結果 (未実走はそう書く)

`python3 -m py_compile` と `git diff --check` は成功しました。焦点 pytest は指定どおり未実走です。

## 未解決・判断が要る点

焦点走での T1〜T3 の結果は、親の計算ノード実走待ちです。