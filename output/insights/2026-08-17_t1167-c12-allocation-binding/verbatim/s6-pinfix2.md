## 総括

`_PRE_WAVE_ORIGINLESS_BASELINE` の残り **3 occurrence** を新値へ更新しました（同ファイル [test_reflux_originless_compatibility.py:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_reflux_originless_compatibility.py:234)）。

- `journals/*/*/launch_admission/activation_report_digest_sha256`
- `lifecycle/*/activation_report_digest_sha256`
- `reports/*/launch_admission/activation_report_digest_sha256`

既に更新済みだった `acceptance/activation_report_digest_sha256` と合わせ、4 key path すべてが新値になっています。

旧値の全件検索結果:

```sh
old='386492ad216ec0bef7d264188a9823359300080f4e095e1d2619ea474d54eb79'

rg --hidden --no-ignore -o -F "$old" \
  orchestrator/tests/test_reflux_originless_compatibility.py | wc -l
# 0

rg --hidden --no-ignore -o -F "$old" orchestrator \
  --glob '!orchestrator/tests/test_reflux_originless_compatibility.py' | wc -l
# 0
```

新値は対象ファイル内で **4 occurrence** です。

4 箇所が同時に動く理由は、登録済み launch admission が `effective_preregistration.report_digest_sha256` を一度取り込み（[trial_registry.py:1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/trial_registry.py:1364)）、共通 admission record に投影するためです（[trial_registry.py:1415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/trial_registry.py:1415)、[trial_registry.py:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/trial_registry.py:1440)）。

その同じ値が以下へ書かれます。

- journal の `run-start.launch_admission`: [p3_autonomous_workload_trial.py:3078](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:3078)、[p3_autonomous_workload_trial.py:3089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:3089)
- report の `launch_admission`: [p3_autonomous_workload_trial.py:2296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:2296)、[p3_autonomous_workload_trial.py:2321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:2321)
- lifecycle start row: [trial_registry.py:1723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/trial_registry.py:1723)、[trial_registry.py:1731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/trial_registry.py:1731)
- acceptance receipt: [trial_registry.py:2683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/trial_registry.py:2683)、[trial_registry.py:2688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/trial_registry.py:2688)

前 turn の誤りは、truncation の明示を認識しながら、表示された差分を実質的な全件集合として扱ったことです。さらに「既存 fixture 値は保持する」という一般則を優先し、4 view が同じ admission digest を共有する生成経路を追跡しませんでした。部分出力ではなく、旧値の occurrence 全件検索と producer-to-consumer の静的追跡を先に行うべきでした。

指示どおり pytest・git 操作・docs/output 編集は行っていません。