結論として、案 B が静的に保てるのは「既存 S2-on・`do_bench=True`・L/B/S を固定 oracle と仮定したときの COMMIT 論理式」までです。現行プランは `certified` 状態、WAL/replay、実測 fitness、critic・レポート出力まで含む受理集合等値を示せておらず、T-142 の条件を満たす形には未到達です。

## 所見

1. **`certified` 集合と COMMIT 集合を同一視している**

   - (a) 攻撃対象: brief P2/P3、plan §2 案 B・§5。
   - (b) 現物根拠: COMMIT が唯一の採用点なのは [model.py:20–26](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/model.py:20)。一方 `evaluate()` は全 verify 後、bench 前に `res.certified=True` とし、bench 失敗時もこれを戻さない [pipeline.py:661–720](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:661)。テストも「certified だが測定不能で aborted」を正規状態としている [test_campaign.py:1728–1739](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/tests/test_campaign.py:1728)。
   - (c) 成立条件と影響: `L=true,S=true,B=false` では旧順序は correctness-certified になった後に不採用だが、新順序は B で止まり S2 未実行なので certified になれない。真理値表の「両方 reject」は、異なる observable state を潰している。さらに `do_bench=False` は B なしで COMMIT する [pipeline.py:703–709](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:703)、[test_campaign.py:1671–1677](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/tests/test_campaign.py:1671)ため、`C0=L∧S∧B` は現行 `evaluate()` 全体の certified/COMMIT 定義ではない。
   - (d) 自己判定: **real**。

2. **L/B/S は順序非依存の固定関数ではない**

   - (a) 攻撃対象: plan §2 真理値表・§6、brief P2。
   - (b) 現物根拠: bench は machine-wide lock、外部 PID probe、settle、CV に応じた再測定を行う [pipeline.py:262–360](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:262)。S2 も別 lock・別 probe 区間である [pipeline.py:661–696](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:661)。再測定は測定値に応じて settle と回数・採用 round が変わる [stability.py:58–90](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/calibrator/stability.py:58)。settle 自体も「campaign 冒頭で一度だけ」で、連続 run 間に入れない契約である [runner.py:60–79](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/calibrator/runner.py:60)。
   - (c) 成立条件と影響: bench→S2 と S2→bench では、lock 待ち、probe 時刻、熱・load 残像、trace の並行スケジュールが異なる。`unstable/high_variance/settled=false` は B=false ではなく COMMIT 可能な付帯状態である [pipeline.py:725–736](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:725)。fitness は critic 内で降順化され fastest を決める [digest.py:192–219](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/critic/digest.py:192)、[digest.py:446–452](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/critic/digest.py:446)ため、COMMIT基準が同じでも選択・次提案の出力集合は同じとはいえない。D36 自身も S2 の薄い赤が seed でゼロ化し得ると記録している [decisions.md:926–928](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/decisions.md:926)。
   - (d) 自己判定: **real**。特定候補が実際に逆転するかは未計測だが、固定関数仮定が現物と合わないことは real。

3. **retryable abort と再評価を含む時系列が真理値表から脱落している**

   - (a) 攻撃対象: plan §5 層1/2/4・§6。
   - (b) 現物根拠: `bench-probe-error` と `verify-probe-error` は retryable である [model.py:104–150](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/model.py:104)。`run_campaign()` はこれらを terminal 集合から除いて再評価する [loop.py:76–92](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/loop.py:76)。replay は任意の過去 COMMIT/ABORT を sticky state に畳む [wal.py:566–583](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/wal.py:566)。
   - (c) 成立条件と影響: 新順序では bench 成功後に S2 probe error、旧順序では bench 前に同 error、という WAL prefix 差が生じる。再開後には BENCH_DONE の有無、再測定値、最後の terminal reason が異なる。単発の `L/B/S` positive control は、この multi-attempt 状態機械を証明しない。
   - (d) 自己判定: **real**。

4. **base の p3 loop は現状 S2-offであり、tiered opt-in は別の受理述語を導入する**

   - (a) 攻撃対象: brief P1/P2、plan §3「p3 loop 系3 driver」。
   - (b) 現物根拠: base driver の `default_cfg()` に `verify=legacy+s2` はない [p3_s4_loop.py:493–506](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/p3_s4_loop.py:493)。`run_campaign()` が S2 を足すのは当該キーがある場合だけ [loop.py:54–60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/loop.py:54)。sort と trigger は既に S2-onである [p3_s4_loop_sort.py:165–185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/p3_s4_loop_sort.py:165)、[p3_s4_loop_trigger_gating.py:324–343](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/p3_s4_loop_trigger_gating.py:324)。
   - (c) 成立条件と影響: base で tiered を有効にするには同時に S2 を新設するため、既存 `L∧B` から `L∧S∧B` へ受理述語が縮む。「新設した S2-on/order-off」と比較しても、基準コミットの受理集合不変は証明できない。
   - (d) 自己判定: **real**。

5. **規律3との衝突を brief が「legacy だけ毎回」で暗黙に読み替えている**

   - (a) 攻撃対象: brief 不変条件3、plan 結論・§6。
   - (b) 現物根拠: 絶対規律3は verifier を毎 iteration 回し、構造化結果を次手へ渡すと定める [CLAUDE.md:71–74](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/CLAUDE.md:71)。D36 は legacy では検出できず S2 だけが検出する違反を実証済み [decisions.md:887–907](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/decisions.md:887)。critic が S2 red を読むには実際の verify ABORT payload が必要である [digest.py:222–254](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/critic/digest.py:222)。
   - (c) 成立条件と影響: 「legacy 緑、実行すれば S2 赤、bench 失敗」の候補は、旧順序なら S2 の構造化 red、新順序なら bench 系 abort の件数だけになる。T-142 がこの診断機会の喪失まで明示的に許したのかは worklog 文言だけでは確定しない。少なくとも「不変」とは書けない。
   - (d) 自己判定: **real**（信号喪失は real、裁定上許容するかは人間判断）。

6. **真理値表 helper は恒真で、S2 workload の実体を証明しない**

   - (a) 攻撃対象: brief P3、plan §5 層1/2/3。
   - (b) 現物根拠: 現行 `passes` は caller が渡した任意の `(tag, workload)` を無検査で追加する [pipeline.py:423–426](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:423)。実走にはその workload の flags を使う一方、WAL/COMMITには caller の tag だけを焼く [pipeline.py:539–599](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:539)、[pipeline.py:699–733](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:699)。正式 S2 flags は別途固定されている [pipeline.py:61–84](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:61)。
   - (c) 成立条件と影響: 小さい workload を `"s2"` と名付けても、tag 集合だけの `all_required_passed()` は緑になる。さらに `L∧S∧B == L∧B∧S` の全組合せテストは論理交換則そのもので、`evaluate()` との結線を検査しない。D36 の「S2縮小なし」を機械保証するには、tag でなく flags/extime/numactl を独立に照合する必要がある。
   - (d) 自己判定: **real**。

7. **AST 番人の充足形がまだ恒真化・迂回可能**

   - (a) 攻撃対象: brief P3/P4、plan §4・§5 層3。
   - (b) 現物根拠: 現在の AST テストは `evaluate` 内の、正確に `wal.log(..., STAGE_COMMIT, ...)` という構文だけを数える [test_campaign.py:1905–1960](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/tests/test_campaign.py:1905)。現在の opt-in 番人も `loop.py` の文字列不在だけを見る [test_screening_opt_in.py:19–22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/tests/test_screening_opt_in.py:19)。
   - (c) 成立条件と影響: `emit=wal.log`、stage literal `"commit"`、別 helper、別 module、あるいは `_commit()` が一度も live 経路から呼ばれない形は、構文条件次第で素通りできる。plan は「変異で赤になる形」とするが、実 mutant 注入・kill 判定・CLI→cfg→lock→evaluate の live control を具体化していない。
   - (d) 自己判定: **speculative**（実装前なので最終 AST 形は未確定。ただし現行番人の弱さは real）。

8. **WAL helper を新設しても replay と attempt 対応が閉じない**

   - (a) 攻撃対象: plan §3「WAL consumer helper」・§5 層4。
   - (b) 現物根拠: `wal.replay()` は COMMIT payload の `verify_configs` を見ず、存在だけで committed にする [wal.py:566–583](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/wal.py:566)。`run_campaign()` はその状態を先に skip する [loop.py:76–96](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/loop.py:76)。また `load_workload()` は variant の最新 BENCH_DONE と「どこかに COMMIT がある」を別々に集約する [digest.py:198–215](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/critic/digest.py:198)。
   - (c) 成立条件と影響: legacy-only COMMIT を持つ tiered WAL は helper到達前に永久 skip される。さらに「過去の正規 COMMIT→後発の未認証 BENCH_DONE→ABORT」では、単なる commit-valid helperだけでは後発値との誤結合を止められない。helper は variant 単位でなく、env・attempt区間・その COMMITに先行する verify/bench を対応付ける必要がある。
   - (d) 自己判定: **real**。

9. **取り残される consumer が具体的に残る**

   - (a) 攻撃対象: brief P3、plan §3「critic と consumer」・§5 層4。
   - (b) 現物根拠:
     - loop材料レポートは「任意の COMMIT 有無」だけで reject を決める [layer3_report.py:314–365](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/layer3_report.py:314)。
     - `replay.load_landscape()` は任意 COMMITと最後の verify/bench を集約する [replay.py:113–145](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/replay.py:113)。
     - p2 レポートも任意 COMMITで ranking 対象にする [p2_2_report.py:63–91](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/p2_2_report.py:63)。
     - s6/s8 の replay・report は COMMIT存在だけを certified とする [s6_sort_sweep.py:351–357](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/s6_sort_sweep.py:351)、[s8a_trigger_sweep.py:394–400](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/s8a_trigger_sweep.py:394)。
     - plotting と freeze も COMMIT presenceを消費する [plot_backoff.py:133–140](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/tools/plotting/plot_backoff.py:133)、[s1_known_axes_freeze.py:170–198](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/s1_known_axes_freeze.py:170)。
     - 対照的に `s1_report` は既に必要 verify 集合を検査する [s1_report.py:274–301](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/s1_report.py:274)。
   - (c) 成立条件と影響: T142 の直接 live consumer は少なくとも `wal.replay`、p3 duplicate、critic、`layer3_report`。残りは generic/別 campaign consumer だが、D36 が「wal/replay の共通 helper 1箇所」を要求している [decisions.md:909–915](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/decisions.md:909)以上、適用除外を明記せず放置できない。`guided.py` の replay専用 COMMITは `verify_configs` を持たない [guided.py:117–127](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/guided.py:117)ため、profile別の明示除外も必要。
   - (d) 自己判定: **real**。

10. **案 A′ 不採用の結論は正しいが、「受理集合」の解釈は狭すぎる**

   - (a) 攻撃対象: plan §2 A′・§6、brief P2。
   - (b) 現物根拠: repoの `STAGE_COMMIT` は採用点、ABORTは不採用点である [model.py:20–26](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/model.py:20)。T-154(3) は新しい検査が実際に通る入力を減らす意味で「受理集合を狭める」と使う [worklog.md:137–140](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/worklog.md:137)。D58材料も「生き残り集合の一致」は screening の目的と矛盾すると明記する [bench-first-screening-design.md:196–206](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/insights/2026-07-14_bench-first-screening-design.md:196)。
   - (c) 成立条件と影響: repo語彙は「潜在的に certified になり得る集合」だけでなく、gate通過・COMMIT・on/offで実際に生き残る集合を指している。したがって、最低でも (i) correctness-certified集合、(ii) COMMIT集合、(iii) 選択・報告出力集合を分ける必要がある。A′ は floor により (ii)(iii) を確実に縮めるため不採用結論自体は維持される。
   - (d) 自己判定: **real**。

11. **親の「約85%・約8倍」は局所条件付きで、案 B の効果根拠にはならない**

   - (a) 攻撃対象: brief 実測、plan 結論・§6。
   - (b) 現物根拠: 親対象 WAL の2点は両方とも bench成功後にCOMMITしている [対象WAL:3–6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl:3)、[対象WAL:9–12](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl:9)。別の同一 read-heavy campaign では S2 が約318.3秒・bench約18.2秒の点 [別WAL:9–11](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-8a237e8c/runs/wal.jsonl:9)と、S2約74.6秒・bench約77.3秒の点 [別WAL:51–53](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-8a237e8c/runs/wal.jsonl:51)が共存する。後者は `rounds=2, settled=false` でもCOMMITしている。同じ p3 loop 系の sort 1点は S2約117.6秒・bench約2.46秒で局所値を補強する [sort WAL:3–6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/runs/wal.jsonl:3)。
   - (c) 成立条件と影響: 30 WALの read-only 集計では benchを伴うS2点は n=78、S2比率中央値79.8%、S2省略時の理論倍率中央値4.95倍、範囲1.85～9.15倍だった。ただし campaign/config混合値であり一般化用ではない。より本質的には、親 n=2 は両方 B=true なので案 B ではS2を一度も省略せず、観測上の削減はゼロ。さらに p3 loop は `bench_max_rounds=1` を渡しておらず [loop.py:136–140](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/loop.py:136)、既定は3 [pipeline.py:372–385](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:372)なので、「max_rounds=1系」ではなく単に観測 round が1だっただけである。新順序はS2-red候補に従来不要だったbenchを追加するため、正味効果は `bench失敗率×S2削減 − S2失敗率×bench追加` で評価すべき。
   - (d) 自己判定: **real**。

12. **brief P2 の「D58機構をLLM loopへ再利用」は裁定範囲を越える**

   - (a) 攻撃対象: brief P2、plan §2 A/A′。
   - (b) 現物根拠: D58 はLLM loopを明示的に適用外とし、適用先拡大・棄却規則変更を別裁定事項にしている [decisions.md:2275–2282](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/decisions.md:2275)。T-142裁定は受理集合不変という条件しか付していない [worklog.md:467–474](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/worklog.md:467)。
   - (c) 成立条件と影響: T-142は受理集合不変な順序short-circuitの新裁定とは読めるが、D58 floor terminal rejectのp3適用許可とは読めない。planがA/A′を退け、別mode・別reasonにした方向は正しい。
   - (d) 自己判定: **real**。

攻撃後も残った判断は、P1の「対象は進化探索loopであり開発pytest全走ではない」と、stale verdictをbench前に消す必要性です。前者は元材料が明示的に「進化探索の毎ループ」と書く [external-consultation:33–34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/insights/2026-07-27_external-consultation-scope-and-axes.md:33)。またS2-red後の workload帰属は既存 `_abort(..., workload_tag=tag)` と `load_rejections()` で保てます。

## 修正提案

1. T-142の不変対象を三つに分けて裁定する。

   - `V`: 全必須verifyを実観測した correctness-certified集合
   - `A`: 正規COMMIT集合
   - `O`: fitness・critic・whiteboard・report・後続提案を含む出力集合

   案Bが静的に示せるのは、限定条件下の「Aの判定述語」までと明記する。V/Oや実行結果同一までは主張しない。

2. 初回scopeを既にS2-onのsort/trigger、`do_bench=True`に限定する。base p3 loopへのS2追加は別軸・別裁定に分離する。

3. S2保証をtag集合検査から実体検査へ上げる。campaign.lock由来の独立required集合、tag一意性、S2 flags/extime/numactl完全一致を評価開始前に確認する。

4. WAL helperを attempt/env-aware にし、COMMITと同じ区間のverify/benchだけを返す。これを `wal.replay`/terminal skip、duplicate、critic、`layer3_report`へ先に配線する。その他consumerは「共通helperへ移行」か「campaign profile上の明示除外」のどちらかを列挙する。

5. 機械保証には実 mutant を入れる。最低限、S2呼出し削除、偽 `"s2"` workload、required=observed化、alias/literal COMMIT、helper迂回、CLI非配線、missing-tag COMMIT、COMMIT後の未認証BENCH_DONEを注入し、各 mutant が単一理由で赤になることを確認する。

6. retry/crash系列をテストする。`bench_done→S2 probe abort→retry→commit`、`bench_done→crash→resume`、競合tenantが二つのlock区間間で出現する系列を含める。

7. 規律3との例外を人間裁定で明記する。許容するなら、bench abortに「S2未実行・未認証」を構造化してcriticへ返し、S2 anomalyを観測したかのような値は絶対に生成しない。

8. 性能主張はbench失敗率とS2-red率を同一候補列で測るpaired ablationまで保留する。現 n=2 から「85%・8倍」をT-142の期待効果へ流用しない。

静的検査のみ、HEADは `78eedcb3027e1c79ea6f2ad977b108d8b4fd9273`。pytest実走・ファイル編集・状態変更は行っていません。