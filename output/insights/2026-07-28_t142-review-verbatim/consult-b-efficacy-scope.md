結論は、**案 B は本 wave では実装せず、floor／適応的 top-K／選択不変性のどれを保証対象にするかを裁定パッケージとして返すべき**です。過去 WAL 上、案 B の観測上の削減量は 0 でした。

## 所見

1. **案 B の観測上の S2 削減量は 0**

   - **(a) 攻撃対象:** brief P2/P3、plan「結論」「案 B」「期待効果」。
   - **(b) 現物根拠:** `output/campaigns/*/runs/wal.jsonl` 全 30 WAL を静的集計した。単位を `build_start` 評価試行とすると 476 試行、`(campaign, variant)` では 204 候補。ABORT 15 件の内訳は `build-error` 12、`non-serializable` 1、`trace-timeout` 1、`screen-slower-than-floor` 1で、bench 起因は 0。bench の hard-fail reason は実装上 [pipeline.py:280](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:280)、[pipeline.py:286](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:286)、[pipeline.py:305](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:305)、[pipeline.py:315](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:315)、[pipeline.py:324](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:324)。P3 の S2 構成 80 候補中、78 候補が S2 と bench に到達し、78/78 が bench 成功、0/78 が bench reject。対象 autonomous では 6 候補中 S2 ありは 3 件で、全件 COMMITした。[sort WAL:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/runs/wal.jsonl:3)、[trigger WAL:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl:3)。
   - **(c) 成立条件と影響:** 同じ L/B/S 結果を仮定する反実仮想では、対象 3 件の S2 実時間合計 344.823 秒、bench 合計 7.426 秒に対し、案 B が省く S2 は 0 件・0 秒。約 8 倍短縮には bench hard-fail 率がおよそ 98～99% 必要だが、観測値は 0/78。現在の分布が将来候補の近似なら実装価値はない。
   - **(d) 自己判定:** **real（過去実測）**。将来分布への外挿だけ speculative。

2. **案 B の「良い候補」は性能上の良さを一切判定していない**

   - **(a) 攻撃対象:** brief P2、plan「結論」「案 B」。
   - **(b) 現物根拠:** 外部相談原文は「価値の低いものを含む全走は良い候補に絞る」とする。[external consultation:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/insights/2026-07-27_external-consultation-scope-and-axes.md:33)。一方 `_run_bench()` は `unstable` や `settled=False` を棄却せず、値を返して COMMITへ進める。[pipeline.py:333](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:333)、[pipeline.py:725](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:725)。実 WAL にも `settled:false` のまま COMMITした候補がある。[base WAL:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl:14)。
   - **(c) 成立条件と影響:** 「良い」を「legacy green かつ測定処理が壊れなかった」と定義すれば形式上は成立する。しかし性能・floor・順位を見ないため、歴史データでは事実上全候補が「良い」。これは価値による二層化ではなく、稀なインフラ失敗時の short-circuit にすぎない。
   - **(d) 自己判定:** **real**。

3. **COMMIT 集合の完全不変と大幅短縮は、現行受理規則のままでは両立しない**

   - **(a) 攻撃対象:** brief の裁定条件、plan「案 A′」「案 C」「リスクと未決点」。
   - **(b) 現物根拠:** 現行 pipeline は全 verify と bench が成功すれば、性能 floor を問わず COMMITする。[pipeline.py:700](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:700)、[pipeline.py:729](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:729)。一方、最終成果物の契約は全 certified 候補集合そのものではなく、certified な選択結果・stock/tie・全試行台帳である。[roadmap.md:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/roadmap.md:22)、[roadmap.md:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/roadmap.md:25)。
   - **(c) 成立条件と影響:** `L∧B∧S` を満たし得る候補から floor/top-K で S2 を省けば、現在の COMMIT 集合は必ず縮む。完全不変を守る解釈は案 B のような「既知の必要条件 false でだけ省く」ものしかなく、効果がない。大幅短縮を求めるなら、保証対象を「全 COMMIT 集合」から「最終 selected/stock/tie が不変」へ変更するユーザー裁定が必要。
   - **(d) 自己判定:** **real（論理的非両立）**。

4. **plan の真理値表は判定基準の可換性しか示さず、実走上の受理集合等値を示していない**

   - **(a) 攻撃対象:** brief P3、plan §5「受理集合不変の機械的提示」。
   - **(b) 現物根拠:** D58 設計自身、verify と bench の順序交換で熱状態・測定窓が変わるため on/off ablation が必要と明記する。[bench-first design:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/insights/2026-07-14_bench-first-screening-design.md:70)、[bench-first design:74](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/insights/2026-07-14_bench-first-screening-design.md:74)。S2 と bench は同じ排他資源を逐次利用する。[pipeline.py:668](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:668)。
   - **(c) 成立条件と影響:** `L(v),B(v),S(v)` が順序非依存の固定 oracle である場合だけ `L∧S∧B=L∧B∧S` が実候補集合の証明になる。実際には bench failure、S2 path coverage、時間ドリフトが順序依存し得る。campaign ID 分離は混在を防ぐが、等値を証明しない。plan の証明は「受理述語不変」と限定すべき。
   - **(d) 自己判定:** **real（証明射程の不足）**。実際に候補判定が反転する頻度は speculative。

5. **brief P1 は「進化探索」の適用先を現行 p3 ループへ無根拠に写している**

   - **(a) 攻撃対象:** brief P1、plan「p3 loop 系 3 driver」。
   - **(b) 現物根拠:** roadmap は population・世代更新・選択・変異等を実装するまで現行 loop を進化探索と呼ばないと定める。[roadmap.md:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/roadmap.md:116)、[roadmap.md:455](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/roadmap.md:455)。現行 p3 は human-supervised loop であり、無人の進化探索ではない。[phase3.md:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/phase3.md:21)。population-based search は Phase 3.5 の条件付き将来項である。[roadmap.md:435](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/roadmap.md:435)。
   - **(c) 成立条件と影響:** 裁定文の「進化探索」が将来の population loop を文字どおり指すなら、現 plan は対象を誤っている。現在の sequential loop も含む俗称だったなら、その読み替えを裁定として明記する必要がある。
   - **(d) 自己判定:** **real（文書上の scope 不一致）**。ユーザーの語意は speculative。

6. **base driver への配線は T-142 と S2 新規導入の二軸変更**

   - **(a) 攻撃対象:** plan §3「p3 loop 系 3 driver」。
   - **(b) 現物根拠:** base の `default_cfg()` は legacy-only。[p3_s4_loop.py:493](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/p3_s4_loop.py:493)。実 lock にも `verify` がなく、WAL は verify 1 本だけ。[base campaign.lock:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/campaign.lock:1)。sort と trigger は既に `legacy+s2`。[sort driver:165](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/p3_s4_loop_sort.py:165)、[trigger driver:324](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/p3_s4_loop_trigger_gating.py:324)。
   - **(c) 成立条件と影響:** base で tiering を有効にすると、評価順序だけでなく約 115 秒の S2 自体を新設する。bench reject 0 の観測下では、約 14.5 秒の legacy+bench loopを約 130 秒へ遅くし、T-142 の短縮目的と逆になる。S2 追加は別タスクとして裁定すべき。
   - **(d) 自己判定:** **real**。

7. **実装計画は、正当な D36 負債と T-142 に不要な一般化を混載している**

   - **(a) 攻撃対象:** plan §3 `verification_policy.py`、wal helper、中央 `_commit()`、AST 更新、§4 positive control 6 種。
   - **(b) 現物根拠:** D36 は共通 AND helper を明示要求している。[decisions.md:909](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/decisions.md:909)、[decisions.md:912](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/decisions.md:912)。現物 `records_by_stage()` は最後勝ちで AND に使えないと自ら警告する。[wal.py:586](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/wal.py:586)。`_resolve_duplicate()`、critic、replay はそれぞれ COMMIT 存在を信頼しており独立 consumer 例が複数ある。[p3_s4_loop.py:575](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/p3_s4_loop.py:575)、[digest.py:209](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/critic/digest.py:209)、[replay.py:129](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/replay.py:129)。一方 campaign ID は既に全 `search_config` をハッシュし、lock 全体を照合する。[ident.py:83](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/ident.py:83)、[ident.py:150](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/ident.py:150)。
   - **(c) 成立条件と影響:** wal AND helper は D36 と複数 consumer により DW-G03 を満たす正当な既存負債だが、T-142 の順序交換に必須ではない。新 policy module、専用 preimage helper、中央 COMMIT refactorまで同 wave に載せる根拠は弱い。また S2-red→COMMITなし、未 COMMIT bench の critic 除外、verify による ID 分離は既存テスト済み。[test_campaign.py:2179](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/tests/test_campaign.py:2179)、[test_critic.py:101](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/tests/test_critic.py:101)、[test_campaign.py:166](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/tests/test_campaign.py:166)。DW-G02/G03 は局所化と独立 2 例を要求する。[core.md:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/dev-wave/core.md:51)、[core.md:56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/dev-wave/core.md:56)。
   - **(d) 自己判定:** **real**。

8. **欠けている consumer は layer3 material report。ここは実際に未認証 TPS を露出する**

   - **(a) 攻撃対象:** brief P3、不変条件 4、plan §3「critic と consumer」、positive control 6。
   - **(b) 現物根拠:** `layer3_report` は COMMIT の有無に関係なく全 `bench_done` を `runs` に射影する。[layer3_report.py:359](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/layer3_report.py:359)。`runs` schema は TPS・median・LI をそのまま正式フィールドに持ち、certified/commit 状態を持たない。[layer3_schema.json:12](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/layer3_schema.json:12)。未 COMMIT bench を受け入れる既存テストもある。[test_layer3_report.py:413](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/tests/test_layer3_report.py:413)。D58 screening campaign はこの理由で layer3 対象外のまま、拡張時は schema 再凍結とされている。[phase3.md:408](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/phase3.md:408)。
   - **(c) 成立条件と影響:** 案 B の `legacy green → BENCH_DONE → S2 red → ABORT` では、COMMIT のない TPS が layer3 の通常 `runs` に並ぶ。critic の `load_workload()` が遮断しても正式レポート側は遮断できない。plan の sentinel test は layer3 まで含めないため、不変条件 4を満たさない。
   - **(d) 自己判定:** **real・実装するなら blocker**。

9. **s8b oracle と S1 direct は配線対象ではないが、中央 refactor の既定経路番人として明示が必要**

   - **(a) 攻撃対象:** plan §3 `evaluate()` 全体 refactor、§4 テスト計画。
   - **(b) 現物根拠:** s8b oracle は `pipeline.evaluate()` を直接呼び、legacy+S2、公式 bench、binary/env contractを同時に使う。[s8b_oracle_driver.py:1335](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/s8b_oracle_driver.py:1335)。その report は物理順序 `verify_done → bench_done` を固定する。[s8b_oracle_report.py:1092](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/s8b_oracle_report.py:1092)。S1 develop は S2 を使う一方 `do_bench=False`。[s1_direct_comparison.py:745](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/s1_direct_comparison.py:745)。
   - **(c) 成立条件と影響:** evaluation-order が明示 opt-in なら両者の本番変更は不要。ただし既定経路の順序が一行でも漏れて変われば、s8b は protocol violation、S1 は `do_bench=False` 組合せ違反になる。既存 oracle/S1 テストを「無関係」とせず明示的な off-path 回帰として残すべきで、新しい production 配線は不要。
   - **(d) 自己判定:** **real（検証面）**。実際の破壊は speculative。

10. **bench-fail∩S2-red の頻度は 0 ではなく、WAL からは識別不能**

   - **(a) 攻撃対象:** plan §6「critic 信号」。
   - **(b) 現物根拠:** 現行順序では S2 red が即 return し、その候補は bench に到達しない。[pipeline.py:661](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:661)、[pipeline.py:697](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:697)。campaign WAL に S2-red は 0 件で、唯一の `non-serializable` は legacy-only の red fixture。[red WAL:6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/runs/wal.jsonl:6)。ただし D36 の positive control は「legacy 緑・S2 赤」の実在可能性を機械実証済み。[decisions.md:903](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/decisions.md:903)。規律 3 は毎 iteration の構造化信号を要求する。[CLAUDE.md:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/CLAUDE.md:71)。
   - **(c) 成立条件と影響:** 旧順序は S2-red 候補の bench outcome を打ち切るため、共同頻度は右打ち切りで推定不能。観測できるのは「bench hard-fail 0」「S2-red 0」であり、交差確率 0 の証拠ではない。案 Bだけなら観測上の信号損失も 0 なので production 設計変更は不要だが、docs は「頻度不明」と書く必要がある。floor/top-K で省略が常態化する場合は docs だけでは不足し、機械的 audit/promotion 方針が要る。
   - **(d) 自己判定:** **real（識別不能性）**。将来の共同頻度は speculative。

11. **D58 番人テストの置換は境界を弱める**

   - **(a) 攻撃対象:** brief P4、plan §4「既存テストの意図的更新」。
   - **(b) 現物根拠:** 現テストは `loop.py` に `ScreeningConfig` と `screening=` が存在しないことを直接固定する。[test_screening_opt_in.py:19](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/tests/test_screening_opt_in.py:19)。D58 は LLM loopを適用外とし、拡大・棄却規則変更には別裁定を要求する。[decisions.md:2279](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/decisions.md:2279)。案 B は既存 `ScreeningConfig`/floor 分岐とは別 modeであり、D58 分岐を変更しない。[pipeline.py:604](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/orchestrator/campaign/pipeline.py:604)。
   - **(c) 成立条件と影響:** T-142 が許可したのは受理述語不変な順序 short-circuitであって、D58 floor screening の LLM loop 配線ではない。したがって既存番人は残し、T-142 の default-off 番人を追加すべき。置換すると、将来 floor を無裁定で配線する回帰を見逃す。
   - **(d) 自己判定:** **real**。

## 修正提案

新事実で裁定前提が崩れた場合はユーザー再裁定へ戻せる。[core.md:82](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-python-gate/docs/dev-wave/core.md:82)。今回の「bench reject 0/78」はその新事実に当たる。

| 択 | 保証対象 | 必要な前提 | 実装コスト・効果 |
|---|---|---|---|
| 案 B を no-op 化 | 全 COMMIT 集合 | 厳格条件を最優先し、短縮ゼロを受け入れる | コード変更なし。現時点の推奨 |
| 案 A′: legacy→bench→floor→S2 | 最終 selected/stock/tie | COMMIT 集合不変を放棄、certified baseline・同一 workload/env・fresh floor、D58 適用先拡大裁定 | 中。遅い候補が多ければ効果大。layer3/critic/baseline 再アンカーが必要 |
| 案 C: deferred/promotion | 潜在的 certified 集合 | deferred の意味、resume、promotion、最終 drain を裁定 | 大。全件 drain すれば総時間削減はゼロ |
| 適応的 top-K／dominance certificate | 最終 selected/tie | 選択規則・noise floor・tie 帯を事前凍結 | 中～大。性能順に S2 を走らせ、S2-green 候補より残候補が全て明白劣位になった時点で停止。固定 K ではなく、上位が S2-red なら自動拡張する |

推奨裁定は次です。

- 保証対象を「全 COMMIT 集合」から「最終 selected/stock/tie」へ変更できるか、ユーザーへ返す。
- 変更できるなら、固定 top-K ではなく適応的 promotion＋選択不変 certificate を第一候補にする。
- 変更できないなら T-142 は no-op 終了とし、案 B は実装しない。
- base driver の S2 追加は別タスクに分離する。
- それでも案 B を実装するなら sort/trigger の 2 driverだけに縮小し、D58 番人を温存し、layer3 の未認証値遮断を必須差分にする。D36 共通 AND helper は別の負債閉鎖として扱う。

pytest・ファイル編集・状態変更は行っていません。