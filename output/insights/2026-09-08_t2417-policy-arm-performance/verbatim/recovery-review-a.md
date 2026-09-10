## 所見

1. [must-fix][恒真ゲート][テスト代表性] `median_tps` が生の `throughputs` に束縛されていません。

   - producerは測定列から中央値を算出し、両方を出力します。[t2187_adaptive_const_probe.py:4416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/tools/pegasus/probes/t2187_adaptive_const_probe.py:4416)
   - consumerは `median_tps` だけを読み、`throughputs` の存在、件数、値との一致を検査しません。[backoff_policy_performance_analysis.py:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/orchestrator/campaign/backoff_policy_performance_analysis.py:342)
   - fixtureは常に `throughputs=[median_tps]` を与えるため、この穴を隠しています。[test_backoff_policy_performance_analysis.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/orchestrator/tests/test_backoff_policy_performance_analysis.py:241)
   - 反例: 18成果物の主点p0について `median_tps` をp1値へ置換し、`throughputs` を削除しても全18件が受理されました。結果はp0/p1の推定0、CI `[0,0]`、点判定`equivalent`となり、H1は保存値の`accepted`から`rejected`へ変わります。
   - 影響: 受理集合内で登録済み推定値と仮説判定を任意に変更できます。保存結果との完全一致は現在のbytesだけを確認し、このconsumer欠陥を検出しません。
   - scope内です。最小修正は、`reps_per_job=1`に対応する生列をproducerと同じ規則で再検算し、正常値なら中央値一致、欠測なら生列と理由の対応を要求することです。生列の削除、中央値だけの変更を拒否する負例も必要です。
   - real根拠: 上記メモリ内反例が現行validatorを通過しました。既存1296行自体は全件で1標本と中央値が一致しており、既存値の破損はrefutedです。

2. [must-fix][恒真ゲート][テスト代表性][ドリフト] 登録済み実行順を宣言だけで受理し、成果物の行順を検証していません。

   - consumerは行を座標辞書へ格納して元の順序を捨てます。[backoff_policy_performance_analysis.py:488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/orchestrator/campaign/backoff_policy_performance_analysis.py:488)
   - fixtureは `cell_order` にpermutationを宣言しながら、行を全blockで常にp0、p1、p2の順に生成します。[test_backoff_policy_performance_analysis.py:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/orchestrator/tests/test_backoff_policy_performance_analysis.py:269)
   - 反例: rep 1の宣言はp0、p2、p1ですが、各測定点の行をp0、p1、p2へ並べ替えても受理されました。
   - 影響: 位置効果と一次持越しを均衡させたという中心的な順序証拠が偽でも解析へ入ります。数値自体は同じでも、受理された数値が登録順で測られた保証が失われます。
   - scope内です。最小修正は、`cells` の座標列が `workload → threads → 登録permutation` と完全一致することを検査し、fixtureも宣言permutationから行を作ることです。
   - real根拠: 改変成果物が受理されました。一方、既存18 JSONでは全blockの実際の行順が宣言と一致しており、既存測定の順序違反はrefutedです。

3. [must-fix][権限逸脱] machine-readableな解析結果から未認証隔離タグが消えています。

   - 入力では `not_certified`、`headline_eligible=false`、`correctness_status="uncertified"` を要求しています。[backoff_policy_performance_analysis.py:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/orchestrator/campaign/backoff_policy_performance_analysis.py:459)
   - しかし公開関数の返却値にはそれらを伝播していません。[backoff_policy_performance_analysis.py:839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/orchestrator/campaign/backoff_policy_performance_analysis.py:839)
   - 実際の保存結果は `analysis_status=complete` とH1 `accepted`を含む一方、4種の隔離fieldがすべて欠落しています。[analysis-result.json:6888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/output/insights/2026-09-08_t2417-policy-arm-performance/analysis-result.json:6888)
   - 影響: この解析結果単体を読むconsumerは、未認証値を機械的に除外できません。READMEとphase文書では未認証が明記されており、現時点のheadline混入はrefutedですが、「機械的隔離済み」という主張は解析成果物には成立しません。
   - scope内です。最小修正は返却値へ同じ隔離fieldを追加し、既存18 JSONを変えずに解析結果を再生成して、その存在を公開producer-consumerテストで固定することです。
   - real根拠: 現行の保存解析成果物そのものにfieldがありません。

## 反証できた攻撃面

- 既存18 JSONのSHA-256は保存解析結果の `inputs[]` と18件すべて一致し、18異なるhostname、1296座標、欠測ゼロでした。
- trace無効経路は、compile genomeの`BACKOFF_TRACE=0`、`buildcache.build(trace=False)`、`_t0` cache key、symbol/string負走査でproducer側に束縛されています。[t2187_adaptive_const_probe.py:4303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/tools/pegasus/probes/t2187_adaptive_const_probe.py:4303) 既存1296行の記録値も全条件を満たしました。
- cohort2認証は別label、別count cap、閉じた4 cell集合です。[t2187_adaptive_const_probe.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/tools/pegasus/probes/t2187_adaptive_const_probe.py:319) T-2417成果物は`performance_contract`の存在だけで両group公開経路から拒否されます。[t2187_adaptive_const_probe.py:2327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2417-policy-arm-perf/tools/pegasus/probes/t2187_adaptive_const_probe.py:2327)
- merge解決はT-2417の欠測処理とmainのnonmonotonic trace overflow処理を併存させています。build caller台帳の3910、4303も現在の実call siteと一致し、caller取り残しは確認しませんでした。
- `git diff --check 32603d...HEAD` は静的に問題なしでした。

## 総括

**NO-GO**です。既存18 JSONの値、trace無効記録、未認証の人間向け記述、mainとの経路分離には破損を認めませんでしたが、公開解析consumerの受理集合に、判定値を変更できる穴と順序証拠を無効化できる穴があります。さらに解析成果物自身が未認証隔離タグを失っています。三件とも新測定、認証拡大、headline昇格、一般化を伴わない局所修正です。

pytest、build、性能測定は未実走です。実施したのはdiff、既存成果物の読取検算、メモリ内反例だけです。残余限界として、保存されたsymbol/string負走査値を実binaryから再測定しておらず、同一主体がproducer、gate、成果物を同時改変できる一般的な信頼限界も解消対象にしていません。