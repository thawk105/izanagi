結論は **NO-GO** です。指定ファイルはすべて読取可能でした。編集・git 操作・pytest 実走は行っていません。

静的検算では、一次値の転記、8 sessions × 5 reps、estimand field、`time_window_clusters=1`、命名による consumer 非配線は実装・JSONと一致します。また、

- `SE_rel`: K=8 は 26.73%、K=15 は18.90%、K=25 は14.43%で正しい。
- UCL係数: 1.7972、1.4597、1.3165。K=25 の「1.33」は通常の二桁丸めなら1.32だが、保守丸めとしては軽微。
- `0.786% × 1.80 × √2 = 2.001%` は算術上正しい。

## 所見

1. **T425-ADV-01 — 時間窓Kとsession CVの推定量が混線している**

   - 主張: `0.786%` は一つの allocation/time-window 内の8 session-medianのCVである。一方、提案Kは独立時間窓数であり、窓内M=5 sessionをどう一つの窓観測へ集約するか未定義。したがってK−1自由度のUCLをどの分散へ適用するのか決まっていない。
   - 根拠: [rr5 JSON:33](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/scoping-out2/scoping_between_run_t48_skew0p9_rr5_rmw0.json:33) は8 sessionだが [同:55](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/scoping-out2/scoping_between_run_t48_skew0p9_rr5_rmw0.json:55) は `time_window_clusters=1`。packageはKを時間窓と定義しつつM=5を別に置く [ruling-package.md:52](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:52)、[同:75](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:75)。D145も同窓値を時間成分なしの下限とする [decisions.md:7052](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/docs/decisions.md:7052)。
   - 重大度: **blocker**
   - 裁定への誤誘導: K=8のUCLと「wired minimum支配」が、対象estimandを推定しているように見えてしまう。

2. **T425-ADV-02 — 「D134準拠」だが効果量・検出力による標本設計が存在しない**

   - 主張: 3%は判定境界であって効果量ではない。真のpair noiseを何%と仮定し、どの確率で3%の上下を識別したいかという対立仮説・目標powerがない。相対SEとUCL倍率の列挙はpower設計を代替しない。
   - 根拠: packageは「D134準拠」とするが [ruling-package.md:31](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:31)、K選択はSE/UCLだけ [同:33](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:33)。D134は効果量・目標検出力なしの固定標本数を拒否する [decisions.md:6552](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/docs/decisions.md:6552)。T-425自体も同要求を明記する [worklog (162):289](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/docs/archive/worklog-phase3-0804-162.md:289)。
   - 重大度: **blocker**
   - 裁定への誤誘導: ユーザーがK=8対K=15を統計的に導出済みの選択肢だと誧認する。

3. **T425-ADV-03 — official 8b/8c floor契約との接続条件が欠落している**

   - 主張: 8bの承認済みfloorはH1/H2だけでなく、12 cellの構成別per-pair tableであり、`sqrt(s_c²+s_stock²)`、n_sessions=8、reps=5である。提案のK窓・M=5・UCL方式は別formulaで、8b再凍結と承認が必要。逆にlayer-C scalarだけを意図するなら8cの対象別per-pair floorを満たさない。
   - 根拠: 8bの承認内容 [phase3-8b-descriptor-design.md:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/docs/phase3-8b-descriptor-design.md:325)、n/reps [同:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/docs/phase3-8b-descriptor-design.md:342)、実装式 [s8b_floor_stats.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/orchestrator/campaign/s8b_floor_stats.py:311)。8cは8bを正本とし変更に再凍結を要求 [phase3-8c-preregistration.md:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/docs/phase3-8c-preregistration.md:9)、H1/H2 floorとconsumerを前提条件にする [同:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/docs/phase3-8c-preregistration.md:109)。packageのU-6にはこの移行がない。
   - 重大度: **blocker**
   - 裁定への誤誘導: U-1〜U-4を承認すれば8cのfloor欄を正当に充足できるように見えてしまう。

4. **T425-ADV-04 — rr5をH1/H2標本設計の「悪い側」に使えない**

   - 主張: H1(rr80)/H2(rr20)は未実測であり、rr5をworst-case priorとする根拠がない。s4の「rr5は分散最大側」も、linux値ではrr50=1.067%がrr5=0.666%を上回り反証済み。
   - 根拠: [s4-ruling.md:5](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/s4-ruling.md:5)、[ruling-package.md:41](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:41)、同文書自身のH1/H2未実測留保 [同:47](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:47)。D145はworkload/config署名間の外挿を禁止する [decisions.md:7062](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/docs/decisions.md:7062)。D134もabort率とCVの単調関係を反証済み [同:6532](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/docs/decisions.md:6532)。
   - 重大度: **must-fix**
   - 裁定への誤誘導: H1/H2にも十分な余裕があるとの印象を与え、K=8推奨を過度に強く見せる。

5. **T425-ADV-05 — √2の由来は正しいが、必要な同分散・独立条件がない**

   - 主張: `√2` は独立な二測定が同じSDを持つときの差のSDでのみ成立する。構成cとstockでは平均・SDが異なり、同じ時間窓に置けばcovarianceも生じる。
   - 根拠: 一般式は `sqrt(σ_c²+σ_stock²−2Cov)`。現行official式も単一CVではなく各セルの絶対SDをRSSする [s8b_floor_stats.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/orchestrator/campaign/s8b_floor_stats.py:315)。D134もcovariance未観測時の安易なpaired/unpaired解釈を拒否する [decisions.md:6513](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/docs/decisions.md:6513)。
   - 重大度: **must-fix**
   - 裁定への誤誘導: 一つのbaseline CVから全構成対の3%支配を判断できるように見えてしまう。

6. **T425-ADV-06 — 時間分離成分による逆転点の説明が算術的に誤っている**

   - 主張: packageの「約2倍／約+1.2%ptで逆転」は成立しない。
   - 根拠: packageの式をそのまま解くと、`3%/(1.80√2)=1.1785%`。0.786%からは **1.50倍、+0.392%pt** で逆転する。独立な時間成分を分散加算するなら必要成分は `sqrt(1.1785²−0.786²)=0.878%`、現在値の **1.12倍** である。[ruling-package.md:44](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:44)
   - 重大度: **must-fix**
   - 裁定への誤誘導: 3%を超えるには非常に大きな時間ドリフトが必要だと誤認させ、K=8を安全側に見せる。

7. **T425-ADV-07 — K=8→15の再判定は事前記載だけでは95% UCLにならない**

   - 主張: K=8の推定値を見て継続・停止し、継続時に通常のK=15 UCLを使うのはoptional stoppingである。名目95%を維持するにはconfidence sequence、α配分、または独立pilot/confirmatory分離が必要。
   - 根拠: 分岐は [ruling-package.md:44](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:44)、増補先は [同:57](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:57)。さらにU-5の「事前登録K」 [同:91](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md:91) が、分岐前の8なのか分岐後の15なのか不明。
   - 重大度: **must-fix**
   - 裁定への誤誘導: 実際には較正されていない逐次判定を「95%」「事前登録済み」としてeligible判定へ使わせる。

8. **T425-ADV-08 — χ² UCLはsession-median CVの正確な95%限界ではない**

   - 主張: 係数自体は正しいが、χ²式がexactなのはi.i.d.正規標本のSDである。ここではmedian-of-5という順序統計量のCVで、CVの分母も推定平均。K=8では漸近正規性も弱い。
   - 根拠: session代表値がmedianであることは [pegasus_floor_scoping.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/orchestrator/campaign/pegasus_floor_scoping.py:132)。rr5の8値からの標本moment skewは約0.895で、正規性を保証する材料はない。小CVは平均分母の誤差を小さくする方向であり、それ自体は破れの原因ではないが、median分布・cluster相関を救わない。
   - 重大度: **must-fix**
   - 裁定への誤誘導: model-based近似を被覆保証付きの95% UCLとして扱わせる。

9. **T425-ADV-09 — 0.7 node-hour/窓の費用根拠が監査不能**

   - 主張: `8×0.7≈6`などの掛算は正しいが、0.7の導出がない。
   - 根拠: 今回は2点で387秒、すなわち0.1075 node-hour [README.md:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/output/insights/2026-08-04_t425-floor-scoping/README.md:20)。0.7はその6.51倍。旧official 12-cell・8 sessions・5 reps・EXTIME=5のraw時間 `12×8×5×5=2400秒=0.667h` には近いが、提案U-3はM=5なので `12×5×5×5=1500秒=0.417h`。build、retry、構成数を含む補正根拠が書かれていない。
   - 重大度: **must-fix**
   - 裁定への誤誘導: K=8/15/25の資源比較を、どのcell構成を走らせる費用か不明な数字で選ばせる。

10. **T425-ADV-10 — abort率と「独立session」の表示は意味を狭める必要がある**

   - 主張: 77.1%/67.3%の転記値は正しいが、8 between sessions全体のabort率ではない。単独within測定の代表repから取られている。またJSON notesの「8独立セッション」は時間窓独立性を意味しない。
   - 根拠: top-level abortは `within_point.abort_rate` [pegasus_floor_scoping.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/orchestrator/campaign/pegasus_floor_scoping.py:159)。runnerは中央値に近い一repのabortを採る [runner.py:488](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t425-floor-scoping/orchestrator/calibrator/runner.py:488)。JSONは「8独立」とK=1を同時に持つ [rr5 JSON:51](/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/scoping-out2/scoping_between_run_t48_skew0p9_rr5_rmw0.json:51)。
   - 重大度: **nit**
   - 裁定への誤誘導: abortと独立性をcohort全体の実測属性として読ませ、rr5を保守代表とする誤推論を補強する。

なお、scoping値をfloorまたは品質ゲートへ直接昇格・配線する実装は見つかりませんでした。外部out-dir制約、`scoping_between_run_*`命名、`eligible_for_compare=false`は整合しています。

## 総括

**NO-GO**

最重要所見は次の3件です。

1. **T425-ADV-01:** K時間窓のestimandと同窓8 session CVが別物で、UCLを適用する推定量が未定義。
2. **T425-ADV-02:** D134/T-425が要求する効果量・検出力設計がなく、K=8推奨は導出されていない。
3. **T425-ADV-03:** 提案方式がofficial 8b/8cのper-pair frozen protocolを満たすのか、再凍結して置換するのか未裁定。

この3件を閉じる前にU-1〜U-6を承認すると、標本数、95%被覆、8c充足、費用のすべてが誤誘導されます。