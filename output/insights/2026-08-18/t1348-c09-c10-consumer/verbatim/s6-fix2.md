## 総括

`autonomous_trial_completeness.py:476-479` を修正し、相対 path を `run_root` に結合してから境界検査するようにしました。絶対 path は従来どおりです。

同形の相対 path は全4箇所（layer3 1、proposal 1、provider payload/envelope 2）で、共通 helper の修正により全て対応しました。

producer は `p3_autonomous_workload_trial.py:2238-2247` で絶対 `campaign_root` から layer3 path を構成します。一方、`layer3_report.py:192-197` の `artifact_refs` は campaign root 相対です。

変更前は相対 `reports/layer3_report.json` が process cwd 基準で解決され、正当な report まで root 外として拒否されていました。変更後は campaign root 基準で解決され、root 外・symlink・digest 不一致の拒否は維持されます。

`git diff --check` と AST parse は通過しました。pytest は親が実測するため未実行です。