## 原因 1

[test_p3_b4_closed_critic.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_closed_critic.py:158) に、起動器の `_driver_configs` と同じ marker 付き on/off cfg を作る試験 helper を追加しました。

これを以下へ適用しました。

- certified 共通環境: [test_p3_b4_closed_critic.py:767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_closed_critic.py:767)
- M05: [test_p3_b4_closed_critic.py:952](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_closed_critic.py:952)
- admission 順序: [test_p3_b4_closed_critic.py:979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_closed_critic.py:979)
- M18: [test_p3_b4_closed_critic.py:2001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_closed_critic.py:2001)

helper の campaign id 一致 assertion は [test_p3_b4_closed_critic.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_closed_critic.py:130) にそのまま残しています。

`marker-without-mode` は、拒否対象 cfg を marker 不在のまま維持し、context 鋳造用 cfg だけを marker 付き on arm に変更しました。[test_p3_s4_loop.py:2774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_s4_loop.py:2774)

## 原因 2

[wal.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/wal.py:445) で lock の `identity` と `search_config` を fail-closed に抽出するようにしました。欠落や型不正は `B4LauncherAuthorizationError` に変換され、生の `KeyError` は漏れません。

[wal.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/wal.py:463) の driver 判定でも、`search_tag` または `trial` 欠落を同じ拒否へ変換します。

[test_p3_b4_launcher.py:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_launcher.py:381) に、marker はあるが driver field が欠ける lock の負例も追加しました。既存期待値は変更していません。

## 原因 3

[p3_b4_closed_critic.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_closed_critic.py:108) で protocol module の path を定義し、[p3_b4_closed_critic.py:642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_closed_critic.py:642) で全 driver 共通の projection entries に加えました。

独立算出と exact-set も追随しています。

- 独立算出: [test_p3_b4_closed_critic.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_closed_critic.py:613)
- exact-set: [test_p3_b4_closed_critic.py:1704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_closed_critic.py:1704)

## 赤 8 件の帰属

親の診断と異なるものはありませんでした。

- `test_m18_certified_factory_has_no_executable_seam_and_resolves_fixed_claude`: 原因 1。marker 付き on cfg と production context の campaign id が一致します。
- `test_admission_keyword_and_binding_failures_precede_executable_artifact_provider`: 原因 1。同じ marker 付き cfg で context を鋳造してから既存の順序検査へ進みます。
- `test_certified_admission_model_mismatch_queries_once_and_writes_failure_terminal`: 原因 1。certified 共通環境が marker 付き cfg を返します。
- `test_certified_admission_rejects_projection_and_prompt_before_query`: 原因 1。projection、prompt 両 subcase とも marker 付き cfg になります。
- `test_m5_certified_factory_has_no_runner_seam_and_binds_subprocess_run`: 原因 1。marker 付き cfg と context の束縛が一致します。
- `test_repository_checked_record_with_nonempty_cells_and_three_matching_expectations_yields_certified_pair_using_fake_runner`: 原因 1。certified 共通環境の on/off cfg と context が一致します。
- `test_production_context_does_not_weaken_six_receipt_rejections[marker-without-mode]`: 原因 1。拒否対象は marker 不在、context は marker 付き on campaign に正しく束縛されます。
- `test_existing_unclassifiable_lock_rejects_commit[{}]`: 原因 2。`search_config` 欠落が指定の authorization 拒否になります。

## 受理集合の変化

- 原因 1 は試験入力だけの変更で、production の受理集合は変えていません。
- lock 不在だけが引き続き非 B-4 です。[wal.py:418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/wal.py:418)
- 実在するが分類形を欠く lock は、fail-open または生例外から authorization 拒否へ変わりました。
- protocol module の bytes が全 driver の projection hash に反映されます。旧 projection hash の admission は一致しなくなる、指示どおりの変更です。
- identity 生成を担う 3 driver と protocol 定数は未編集です。read-only probe で通常 base、通常 sort、marker 付き on/off 6 件が全 golden と一致しました。trigger 通常 8 件を含む既存 identity 経路にも変更はありません。
- sidecar 上書き、receipt 一回消費、既存 6 拒否、WAL schema は変更していません。

## 実走した検査

指定コマンドを実行しましたが `rc=16` でした。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
```

`child_started=false` のため、赤 8 nodeid と projection exact-set nodeid を含む全 pytest は未実走です。`wal.py` の contract-loader drift 判定にも到達しておらず、緑とは報告しません。

補助確認では次が成功しました。

- 編集 5 file の AST parse
- `git diff --check`
- 通常 base / sort と marker 付き 6 identity の golden
- 全 driver manifest の protocol entry
- 2 種の malformed lock の authorization 拒否
- lock 不在の非 B-4 判定

## 総括

原因 1 から 3 の修正を、許可された 5 file のみに入れました。  
既存 assertion と期待値は緩めず、追加したのは malformed driver lock の負例だけです。  
`git add`、commit、merge、rebase、push、qsub は実行していません。  
pytest 実走のみ、Pegasus queue preflight 障害により未完了です。