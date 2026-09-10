## 所見

- 見出し: must-fix — 計画どおりの到達経路は、現物へのリンクを明示しない限り閉じない
- 根拠: [s2-plan.md:134](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:134) は「`t2187_stage2_thread_axis.{png,pdf,provenance.json}` に現物がある」と basename を書くだけで、[同:139](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:139) も「figures 台帳の節から辿る」とするだけである。一方、実際の directory は [three-constants insight:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants.md:165) の「本文へ埋め込んだ図 3 枚」、[同:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants.md:166) の ``output/insights/2026-09-02_cicada-adaptive-three-constants-figures/`` である。
- 影響: 逐語どおり実装すると、新しい節は `docs/paper-story/figures/` 内の存在しない basename とも読め、検索式は通っても直接参照が閉じない。
- 提案: 次の経路を実リンクとして固定する。`docs/paper-story/README.md` の「今後の基準線」→ `figures/README.md` の新節 → `../../../output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.{png,pdf,provenance.json}`。PNG、PDF、provenance をそれぞれ Markdown link にする。

- 見出し: must-fix — 「現在は図へ到達不能」という DW-G05 は事実より強い
- 根拠: 現行の [paper-story/README.md:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/README.md:104) は「一次資料は `output/insights/2026-09-02_cicada-adaptive-three-constants.md`」と指し、その一次資料の [91-93 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants.md:91) は `t2187_stage2_thread_axis.png` を実際に埋め込んでいる。図台帳からも [figures/README.md:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/figures/README.md:203) →同 insight→図、という二段経路が既にある。
- 影響: 採用変更が新しく生むのは「初めての到達可能性」ではなく、調整済み対照図としての直接指定と fig2b/fig2c の代用禁止である。現状の説明では存在しない欠陥を修正理由にしている。
- 提案: DW-G05 を「現行は一次資料経由で辿れるが、論文側の図台帳に調整済み対照として登録されず、基準線段落から直接選べない」へ狭める。

- 見出し: must-fix — docs 2変更には実効性があるが、worklog fragment は成果物影響上は nit
- 根拠: [s2-plan.md:182](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:182) は図台帳へ「PNG/PDF/provenance の所在、同軸の系列」を追加し、[同:183](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:183) は論文入口の参照と fig2b/fig2c の使用指示を変える。一方 [同:184](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:184) の新規 worklog は決着を記録するだけである。
- 影響: 図台帳変更は参照集合、paper-story 変更は論文執筆者の選択を実際に変える。worklog は certified 選択、レポート値、図台帳参照、論文主張のいずれも変えないため nit。
- 提案: 2 README は must-fix とする。worklog は repository 運用上必要なら作るが、ユーザー要求を満たす成果物としては数えない。

- 見出し: 既存図を論文図へ昇格させない境界は実在欠陥に対応しており、scope 外の仮想 gate ではない
- 根拠: [provenance:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:10) は `"not_certified": "trace-disabled performance runs only; no serializability check was run"`、[three-constants insight:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants.md:172) は「論文図の場所には置いていない」、[同:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants.md:173) は「論文図として使える段階にない」と明記する。
- 影響: 昇格条件と未認証境界を落とすと、未検査値が variant 採用または certified 性能結論へ流入しうる。
- 提案: この限定は維持する。新 gate、validator、mutation test は不要であり、[s2-plan.md:186](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:186) と [同:218](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:218) の不変更判断は妥当。

## 親 brief 自身への所見

- 見出し: 実測確認 — 5セルは provenance にあるだけでなく、threads モードですべて実際に描かれる
- 根拠: provenance の `primary_values` は `"cell": "none"` [167行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:167)、`"s0.5-u2560"` [615行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:615)、`"s1-u2560"` [1063行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:1063)、`"s1-u640"` [1511行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:1511)、`"s100-u10"` [1959行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:1959) を持つ。生成器は [plot_t2187_adaptive_consts.py:768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_t2187_adaptive_consts.py:768) で全 `cell` 名を取り、[同:773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_t2187_adaptive_consts.py:773) で全名を順序へ返し、[同:799](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_t2187_adaptive_consts.py:799) から各系列を回して [同:821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_t2187_adaptive_consts.py:821) の `axis.plot` に渡す。
- 影響: 5セル×3 workload×8 threadの120系列点は集計専用ではなく、6 panelそれぞれの対応軸に描かれる。既存PNGは「実際の対照として同じ図に並べる」という視覚的要求を満たす。
- 提案: 新規描画は不要。新節で `s1-u2560` が調整済み adaptive であることを明示する。

- 見出し: 親の「docs から図そのものへの参照0件」は、限定付きなら真だが、提示コマンドの実測値は誤り
- 根拠: [s1-brief.md:47](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/verbatim/s1-brief.md:47) は除外指定なしの `git grep ... -- docs/` で「0件」とするが、実際には [docs/archive/worklog-phase3-0902-1209-1210.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/archive/worklog-phase3-0902-1209-1210.md:18) に ``output/insights/2026-09-02_cicada-adaptive-three-constants-figures/`` がある。
- 影響: nit。archiveを除く生きたdocsへの直接参照が0件という結論は再現したが、brief記載のコマンドと数値は一致しない。また直接参照0件から「到達不能」は導けない。
- 提案: plan [49行](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:49) と同じ archive 除外式へ直し、「直接参照0件」と限定する。

- 見出し: 「T-2186差し替え完了」は10単位の着地としては真だが、「調整済みへ置換完了」ではない
- 根拠: 10単位の現行実体は、#1 [plot_backoff.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_backoff.py:73) と [同:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_backoff.py:74)、#2 [test_plot_backoff_ci.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_plot_backoff_ci.py:162)、#3 [backoff_sweep_report.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/backoff_sweep_report.py:141) と [同:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/backoff_sweep_report.py:197)、#4 [test_backoff_consumers.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_backoff_consumers.py:156)、#5 [backoff_sweep.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/backoff_sweep.py:4) と [同:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/backoff_sweep.py:191)、#6 [tools/plotting/README.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/README.md:15)、#7 [FIGURE_CONVENTIONS.md:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/FIGURE_CONVENTIONS.md:61)、#8 [patches/README.md:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/patches/README.md:159)、#9 [figures/README.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/figures/README.md:79) と [同:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/figures/README.md:186)、#10 [paper-story/README.md:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/README.md:63) と [同:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/README.md:93) に着地している。しかし差し替え記録自身は [75-77行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_default-adaptive-baseline-replacement.md:75) で「同じ図に並べるところまでではない」と明記する。
- 影響: #1は調整済みへ置換せず既定を無backoff 1本へ減らし、#3-#10は主に機構一般化を撤回したもの。したがってT-2186だけを根拠にT-2239をscope外へ出すと依頼が縮む。今回のplanは既存T-2187図を使ってT-2239を残しているため、直接リンクを直せば総体として閉じる。
- 提案: briefの「差し替え完了」を「10単位のliving default・主張是正は完了。同図への実対照はT-2187現物で別途閉じる」と限定する。

- 見出し: carry前提条件1を実装しない結論は正しいが、「3定数producerが実在しない」は一般化しすぎ
- 根拠: [s1-brief.md:37](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/verbatim/s1-brief.md:37) は「3定数を出す producer が実在しない」とするが、[t2187_adaptive_const_probe.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/pegasus/probes/t2187_adaptive_const_probe.py:290) から [299行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/pegasus/probes/t2187_adaptive_const_probe.py:299) は3定数を genome に出す。一方、対象図は [plot_t2187_adaptive_consts.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_t2187_adaptive_consts.py:39) の専用source schemaと [同:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_t2187_adaptive_consts.py:40) の専用provenance schemaを使い、v2の [BASELINE_BY_GENOME:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_backoff_figure_provenance.py:24) を通らない。
- 影響: nit。carry前提条件1は未実装だが、今回参照する図には不要なのでscope縮小ではない。誤りはproducer全体とv2 surfaceを混同した説明だけである。
- 提案: plan [160-176行](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:160) の限定説明をbriefにも反映する。

## 総括

- must-fix:

  - 新しい2段のdocs経路を、節名やbasenameだけでなく解決可能なMarkdown linkで閉じる。
  - DW-G05を「到達不能」から「既存の間接経路しかなく、論文側で実対照として直接指定されていない」へ修正する。
  - T-2186完了の射程を、10単位のliving default・主張是正までと明記する。

- nit:

  - worklog fragmentは成果物影響を持たない。
  - briefに記載された除外なし検索の「0件」。
  - 「3定数producerが存在しない」という過度な一般化。計画側は既に正しく限定している。

依頼は、上記の明示リンク修正を入れれば満たされる。既存PNGは無backoff、既定adaptive、`s1-u2560`の調整済みadaptiveを同じ各panelのthread軸へ実際に描いており、新規描画は不要である。ただし閉じるのは「同じ図に実対照を並べ、論文側から明示的に参照する」ところまでで、certifiedな論文性能結論やvariant採用までは閉じない。

自信が低いのは「正式な対照」がcertified paper figureへの昇格までを意味するかという語義だけである。その強い意味なら本planは未達だが、D1506とユーザーの「同じ図に並べる」という具体的境界に沿う限り、未認証を明示した直接参照で要求を満たすと判断する。テストは実走していない。