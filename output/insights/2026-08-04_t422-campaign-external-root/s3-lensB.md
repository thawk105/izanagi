静的レビューの結論は、現状プランのままでは採用不可です。E2E で F98 を塞げない real 候補を 6 件確認しました。

## 所見

### 1. 8c の外側 `run_root` が worktree 内に残る

- 種別: 整合・実効性
- 深刻度: 致命
- 根拠: プラン自身が autonomous trial の `run_root` を今回の seam と別物として据え置いている [s2-plan.md:108](/work/1/SFC/tanab/dev-wave-jobs/t422-campaign-external-root/s2-plan.md:108)。CLI の未指定時は [p3_autonomous_workload_trial.py:1730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1730)、[p3_autonomous_workload_trial.py:1753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1753) で `ROOT/output/exploration/autonomous-trials/...` を選び、[p3_autonomous_workload_trial.py:1583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1583) から namespace、`raw/`、`proposals/`、`attempts.jsonl` を作る。現行 runbook も repo 内既定を指示している [phase3-s8c-autonomous-trial-runbook.md:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/docs/phase3-s8c-autonomous-trial-runbook.md:131)。
- 具体的な壊れ方: campaign の lock/WAL だけ外部化しても、8c 実走は worktree に別の `namespace.json` と trial 成果物を生成する。`git status` が汚れ、land 検査 [dev_wave_land.py:785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/tools/dev_wave_land.py:785) を通らない。
- 修正方向: `run_root` の既定も同じ外部 base に接続するか、全 wave launcher で外部 `--run-root` を必須化し、開始前に worktree 外であることを検証する。
- scope: 現プランの除外は E2E の landability と両立しない。D123 の既定を変えない方針なら、明示的な裁定パッケージ候補。

### 2. T-420 の実際の qsub 経路に env の設定主体がいない

- 種別: 整合・実効性
- 深刻度: 致命
- 根拠: smoke driver は `layout=None` のまま trigger を呼ぶ [smoke_driver.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py:48) ため、env が継承されれば factory を通る [p3_s4_loop_trigger_gating.py:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop_trigger_gating.py:604)。しかし qsub 手順は progress dir しか渡さず [README.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/README.md:31)、job script もそれだけを検査する [smoke_job.sh:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_job.sh:13)。Python 起動直前にも新 env の export はない [smoke_job.sh:422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_job.sh:422)。
- 具体的な壊れ方: runbook を読んだ人が手動で export した場合だけ成功し、既存の再走コマンドでは env 未設定の legacy fallback に戻って F98 を再現する。さらに explicit `output_root` 優先なので、env の存在確認だけでも不十分。
- 修正方向: qsub wrapper/job script が外部 base を生成・export し、解決後の `layout.root` が worktree 外かを fail-fast 検査して記録する。
- scope: T-420 再走は今回の受入対象なので scope 内。既存 frozen driver を変更できないなら、専用 launcher の追加を裁定パッケージ候補にする。

### 3. 回帰テストが campaign 起動を再現せず、lock/WAL を測らない

- 種別: 整合・実効性
- 深刻度: 高
- 根拠: 計画された land テストは `layout.ensure()` まで [s2-plan.md:169](/work/1/SFC/tanab/dev-wave-jobs/t422-campaign-external-root/s2-plan.md:169)。`ensure()` が作るのは namespace とディレクトリだけである [layout.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:315)。lock は identity 処理 [ident.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/ident.py:185) から atomic acquire [wal.py:797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:797)、WAL は最初の append 時 [wal.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:301) に初めて生まれる。既存テストには marker・lock・WAL まで確認する最小 campaign がある [test_campaign.py:3287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3287)。
- 具体的な壊れ方: factory/namespace だけ正しくても identity や WAL の sink が repo 側へ退行した場合にテストは緑のままになる。実測対象の `campaign.lock` 自体を作らないため、F98 再発検知として代表性がない。
- 修正方向: synthetic linked worktree 内で fake evaluator を使った最小 `run_campaign()` を完走させ、外部側の marker・lock・WAL と worktree clean を同時に検査する。

### 4. resume／再入時の root ドリフトを検出できない

- 種別: 整合・実効性
- 深刻度: 高
- 根拠: S4 の checkpoint/whiteboard は現在の layout 配下に固定される [p3_s4_loop.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop.py:357)、[p3_s4_loop.py:454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop.py:454)。各プロセスは env から root を再導出する [p3_s4_loop.py:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop.py:801)。trigger の resume 拒否も現在選ばれた root だけを見る [p3_s4_loop_trigger_gating.py:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop_trigger_gating.py:313)。
- 具体的な壊れ方: 初回が外部 root A、再入が未設定または root B なら、既存 checkpoint/campaign を見失って同じ campaign を二重作成する。未設定なら新しい marker/lock を worktree に作り、同一プロセス内の root 比較では検出できない。
- 修正方向: job/supervisor の永続 manifest に解決済み root を保存し、再入前に完全一致を必須化する。
- scope: durable locator を今回導入しないなら、「再入非対応」または locator/lock schema 設計を裁定パッケージ候補として明示する。

### 5. 「全 campaign 経路を塞ぐ」という brief の一般化がコードと一致しない

- 種別: 整合・実効性
- 深刻度: 高
- 根拠: `s6_sort_sweep` は env-aware exploration factory ではなく通常の `campaign_layout()` を使う [s6_sort_sweep.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/s6_sort_sweep.py:237)、[s6_sort_sweep.py:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/s6_sort_sweep.py:276)。`s8a_trigger_sweep` も同様 [s8a_trigger_sweep.py:336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/s8a_trigger_sweep.py:336)、[s8a_trigger_sweep.py:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/s8a_trigger_sweep.py:378)。D123 は sweep producer を意図的に対象外としている [decisions.md:5991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/docs/decisions.md:5991)。
- 具体的な壊れ方: 別 wave がこれら production launcher を計算ノードで再走すれば、env を設定していても通常 campaign root に lock/WAL を書く。「全 wave の campaign transport を解決した」という受入主張は成立しない。
- 修正方向: 保証範囲を「D123 exploration family」に狭めて対象外 launcher の wave 実行を禁止するか、official/sweep root 外部化を別裁定として設計する。
- scope: official/sweep の意味論変更は裁定パッケージ候補。brief の一般化だけを残して実装済み扱いしてはならない。

### 6. 正本文書が repo 内配置・hook 保護を主張したままになる

- 種別: 整合・実効性
- 深刻度: 中
- 根拠: プランは `output/README.md`、D123、8c runbook を原則変更しない [s2-plan.md:205](/work/1/SFC/tanab/dev-wave-jobs/t422-campaign-external-root/s2-plan.md:205)。一方、文書索引は `output/README.md` を output 構造の正本としている [docs/README.md:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/docs/README.md:50)。その正本は全成果物が repo の `output/` 配下にあり、campaign tree が hook 保護されると記述する [output/README.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/output/README.md:1)、[output/README.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/output/README.md:51)。実際の guard は repo 相対 tree だけを対象にする [guard_bash.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/hooks/guard_bash.py:96)、[guard_bash.py:780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/hooks/guard_bash.py:780)。
- 具体的な壊れ方: operator が正本どおり repo 既定を使って F98 を再発させる一方、外部 campaign が同じ hook で保護されるという誤った安全保証も残る。
- 修正方向: `output/README.md` と 8c runbook に抽象的な base-root 優先順位と外部 root は repo hook 保護外であることを記し、機械固有 `/work/...` は Pegasus runbook だけに置く。

## 攻撃したが破れなかった面

- 逆導出: [p3_autonomous_workload_trial.py:1043](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1043)、[p3_autonomous_workload_trial.py:1222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1222) の `layout.root.parent.parent` は `<base>/exploration` を正しく復元し、同一 base 内では completeness の期待形と一致する。破れたのは別管理の outer `run_root`。
- S4 の同一プロセス比較: [p3_s4_loop.py:679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop.py:679) は同じ factory の結果を比較しており、env がプロセス中に不変なら整合する。穴はプロセスをまたぐ再入。
- smoke driver 本体: [smoke_driver.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py:48) は無改変でも、正しい env が job に継承されれば外部 root へ向く。破れたのは qsub/job の運用配線。
- 書き込み棚卸し: whiteboard/checkpoint は layout 配下 [p3_s4_loop.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop.py:367)、trigger digest/provenance も layout 配下 [p3_s4_loop_trigger_gating.py:655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop_trigger_gating.py:655)。`env_scope_dir` は [layout.py:333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:333) にあるが D123 の対象 call graph からの利用はない。
- cache/一時物: T-420 build cache は `$TMPDIR` を渡す [smoke_driver.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py:51)、job も計算ノード側 scratch を設定する [smoke_job.sh:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_job.sh:96)。pipeline trace/perf 一時物も TMPDIR に作成・清掃される [pipeline.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/pipeline.py:742)、[pipeline.py:809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/pipeline.py:809)。`output/insights/` への新たな runtime writer は D123 経路から見つからなかった。
- 文書境界: 計画上の機械固有 path は Pegasus runbook にだけ置かれ、横断設計文書は抽象 contract のままなので、この境界自体は破れなかった。
- 引用照合: `layout.py:323`、`loop.py:96`、`p3_s4_loop.py:679`、`p3_autonomous_workload_trial.py:1043/1222`、`dev_wave_land.py:785` はプラン記載の主張と現物が一致した。

pytest・ビルドは実行していない。以上は静的読解のみ。

## 総括

- real 候補所見数: 6
- 最深刻: env を正しく設定しても 8c の outer `run_root` が worktree を汚す所見 1。
- プラン採否: 現状不採用。所見 1〜3 を scope 内で閉じ、resume と非 D123 campaign の境界を裁定してから段 4 に進めるべき。