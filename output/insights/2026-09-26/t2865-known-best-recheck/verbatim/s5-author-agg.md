## 実装

[recheck_aggregate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-recheck-unit-agg/t2865-recheck-probe/recheck_aggregate.py) を作成しました。driver の関数を再利用して job ごとの束縛照合と判定を行います。新しい計測結果への適用は、結果がまだないため未実走です。

## 実走

作業木 U で以下を実行しました。いずれも rc=0 です。

- `python3 t2865-recheck-probe/recheck_aggregate.py --repo-root "$PWD" --self-check-original "$PWD/output/env/pegasus/calibration/silo_function_policy_recon/compare"` — 元 8 job の 16 点が既存集計と完全一致。
- `python3 t2865-recheck-probe/recheck_aggregate.py --repo-root "$PWD" --self-check-negatives "$PWD/output/env/pegasus/calibration/silo_function_policy_recon/compare"` — source evidence 欠落、fixed10 define 不成立、verify 不成立の3負例がすべて PASS。
- `--new` に元の `compare-0.json`・`compare-1.json`・`compare-6.json` を渡す確認 — rc=0。3点とも PIN 不一致と `(hostname, started_at)` 重複により `indeterminate`。出力は `/tmp/t2865-recheck-aggregate-smoke.json` に置きました。

## 所有外への波及

`git status --porcelain --untracked-files=all` は `?? t2865-recheck-probe/recheck_aggregate.py` のみを示しました。commit は作成していません。

## 総括

指定の1ファイルを実装し、旧結果との完全一致と負例を実走で確認しました。