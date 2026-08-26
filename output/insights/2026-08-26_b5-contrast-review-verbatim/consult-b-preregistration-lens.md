## 所見

1. **重大度 = must-fix — LLM と対照で探索可能空間が揃わず、「必要性」を識別できない。**  
   random は「各 site の有限な replacement production 完全一覧」に閉じる一方、LLM を同じ typed contract に閉じる規定がありません。[草案 §4](/home/SFC/tanab/.claude/jobs/49e37960/tmp/codex/b5-llm-necessity-contrast-materials/09-plan-v1.md:78) LLM を閉じなければ「広い空間 vs 有限部分空間」の比較、閉じれば完全列挙器を構成できて発火条件 1 の「完全列挙器を持たない」と衝突します。これは T-140 レビューが既に特定した「非列挙性・構成的安全保証・同一支持集合対照」の三すくみです。  
   **成果物影響:** LLM だけが生成可能な variant が certified 選択に入り、材料レポートは探索器の優越を探索空間差による勝利と取り違え、試行台帳の値が正しくても B-5 受理集合と参照が無効になります。

2. **重大度 = must-fix — B=10/A=30/3600秒は D39 の継承ではなく実質改訂。停止条件も現行実装に存在しない。**  
   D39 は「10 iteration **または** 3600秒」という上限で、収束・逆方向枯渇による停止も持ちます。[D39](/home/SFC/tanab/.claude/jobs/49e37960/tmp/codex/b5-llm-necessity-contrast-materials/04-D39.md:28) 草案は最大30原提案から Tier0 通過後10 slotを必ず埋める契約であり、10 iteration と同値ではありません。最大30提案は探索機会の拡大なので「制約方向のみ」とも自称できません。さらに現行 driver は `converged` / `reverse-exhausted` を実際に返し、`performance_early_stop=False` は実挙動由来でない literal です。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/orchestrator/campaign/p3_s4_loop.py:644) この改訂には D52 と同じく、改訂類型の明記とユーザー承認が必要です。  
   **成果物影響:** 系列ごとの提案数・slot数・endpoint が変わるため certified 選択も score も変わり、現行 iteration 台帳と新 B/A 台帳を同一予算として比較できません。

3. **重大度 = must-fix — 現在 commit 時点の既知結果台帳がなく、既存 HARKing 境界と同水準でない。**  
   現行事前登録は改訂時点で、D50 の +61〜99%、F段 iteration、既知軸実測、fresh CV などを具体的に列挙しています。[現行事前登録](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/docs/phase3-main-experiment.md:249) 草案は将来の trigger 偵察台帳しか要求せず、B/A/N・workload・random 分布を決めた2026-08-26時点の既知情報を申告していません。最低限、D46/D50、F段、S-1〜S-3確定結果、T-140陰性、axis-proposer全提案束を「現在台帳」に載せ、発火時にはその後の差分台帳を追加すべきです。偵察の生成方法、調べる軸数、選択規則、偵察候補の formal 再利用禁止も未定義です。  
   **成果物影響:** certified 値自体は変わりませんが、材料レポートの分類が「結果既知の登録追試」から exploratory へ落ち、発火 commit・grid・axis の provenance 参照が受理不能になります。

4. **重大度 = must-fix — endpoint の性能判定が探索中の最大1 sessionを再利用し、独立な性能検証相がない。**  
   系列 score は10候補の単回計測の最大値で、その同じ score を検定に使います。[草案 §6–7](/home/SFC/tanab/.claude/jobs/49e37960/tmp/codex/b5-llm-necessity-contrast-materials/09-plan-v1.md:162) N_floor=8 は CV算出だけ、N_verify=8 は correctnessだけなので、最大値選択による winner’s curse と高分散候補優遇を除けません。現行事前登録の「偵察→独立な分布比較」に合わせ、endpoint 固定後の独立 N_eval と paired stock から score を再推定すべきです。また `floor_cmp` は「24 endpoint の CV の最大」なのか「poolした CV」なのか不明で、後者なら variant 間差をノイズと混同します。  
   **成果物影響:** endpoint source hashは同じでも報告 gain・paired difference・Holm p値・B-5受理集合が変わり、高分散な誤選択が certified winner として残り得ます。

5. **重大度 = must-fix — 追記は段6(c)(d)を確定せず、発火時へ再繰延している。実行機構も大半が不在。**  
   production一覧、具体grid、axis IDはいずれも発火記録で将来埋めるため、現時点で(c)(d)は閉じません。実コードの棚卸しは次のとおりです。

   | 要素 | 現況 |
   |---|---|
   | random generator / typed mutation contract / Tier0 | 不在。`Tier0` 実装は sort sweep の将来要件を述べるコメントだけ |
   | sweep driver | backoff、sort、trigger-gating が実在。ただし全て軸固有で、B/A/hash順を強制しない。trigger sweep は完全列挙かつ preliminary |
   | 共通 certification consumer | `pipeline.evaluate()` が実在し、trace/perf別buildを扱える |
   | B/A共通予算台帳 | 不在。S1・8b・8cの用途固有台帳はあるが、3アーム共通slot/proposal台帳ではない |
   | 時間分離block・schedule照合 | S-1に2 block、別CLI process、schedule hash・ledger prefix照合の先例あり。ただしB-5用ではない |
   | B-5 report/stat consumer | 不在。既存S1/8b/8c reportはschemaも仮説族も異なる |
   | 固定B完走 | 現行LLM driverはsafe-loop stopを継承するため未実現 |

   使い回せるのは pipeline とS-1のschedule/ledger様式です。新規に少なくとも generator/IR、Tier0、3アームdriver、freeze、B/A ledger、report/stat consumerが必要で、規模は中〜大です。  
   **成果物影響:** 現在は新しい台帳値・選択値・report行を一件も生成できず、将来手作業で走らせても条件3を満たさない結果はB-5受理集合へ入りません。

6. **重大度 = must-fix — 実験規模は少なくとも十時間台、実wallは百時間級で、3600秒完走可能性が未証明。**  
   詳細は費用見積りのとおりです。特に correctness protocol が未固定で、既存3秒traceの verifier wall は140.66秒から433.33秒まで開きがあります。後者なら1系列10 slotのverificationだけで約4,333秒となり、3600秒上限内のB=10完走が物理的に不可能です。sweep-ceiling、paired stock、build、最大3,240 Tier0提案も総上限外です。  
   **成果物影響:** 一部または全 workload が一律に判定不能となり、台帳は大量の incomplete を記録し、certified候補が存在してもB-5レポートの受理集合は空になります。

7. **重大度 = should-fix — DW-G05上、このまま正本へ追記する価値はない。**  
   発火条件が全て偽なので、追記前後で現在の certified 選択、材料レポート値、試行台帳値、論文素材§8の「B-5未取得」は変わりません。変わるのは将来の手動参照規約だけですが、その規約が所見1〜6の衝突を含み、(c)(d)も閉じません。現段階では非拘束の設計メモに留め、具体軸・実装・費用pilotが揃った発火 commit で正本化する方がよいです。  
   **成果物影響:** 今commitしても値・受理集合はゼロ件不変で、正本参照だけが未実装・未成立の規約へ増え、将来のreport consumerが誤った契約を参照する危険が増えます。

## (c') 事前自認との衝突についての結論

trigger-gating については、この設計で B-5 を主張できません。D48により偵察空間とcoder空間が同一で完全列挙可能であり、D52が「LLMは機械列挙を上回れない」と事前自認しています。草案の発火条件1はこの軸を排除するため、そこはD52と整合します。

ただし (c') は全ての将来軸に対する一般定理ではありません。将来の非列挙軸なら形式的矛盾は避けられます。それでも現設計が示せるのは「この固定予算・固定編集面で、二つの事前登録済み非LLM生成器より高いscoreだった」までであり、「LLMでなければ到達できない」という必要性ではありません。

B-5を残すなら、次のいずれかが必要です。

- 主張を「凍結したrandom/sweep対照に対する条件付き優越」へ狭め、論文§8の「必要性」と区別する。
- LLMと非LLMを同一の候補支持集合へ閉じ、軸発見・候補生成・探索方策を別々にablateする。ただし有限contractへ閉じるとD52の非列挙条件を再裁定する必要があります。
- D52の系レベル設計へ戻り、軸内探索でなく軸発見・オンボーディングまで含む非LLM対照を設ける。

現草案のままではB-5成立とは書けません。

## 費用見積り

trace-disabled benchの設定時間だけでも次の量です。

- 主探索: `108系列 × 10 slot × 5 reps × 3秒 = 16,200秒` = **4.5時間**
- floor: `(108 endpoint + 108 paired stock) × 8 session × 5 reps × 3秒 = 25,920秒` = **7.2時間**
- 合計: **11.7時間**。makeDB、settle、再測、build、Tier0、LLM、paired stockの探索時測定、sweep-ceilingは含みません。

correctnessはさらに、

- slot verification: `1,080回`
- endpoint N_verify: `108 × 8 = 864回`
- 計 **1,944 trace+verify**

です。既存実測は3秒trace 1件あたり verifier wall **140.66秒**、rr95例では **433.33秒**です。[S2校正](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.md:8) [rr95校正](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/output/env/linux-baremetal/calibration/s1_verify_extime.json:1) 単純外挿すると verifierだけで約 **76〜234時間**、bench込みで約 **90〜250時間**、すなわち直列wallは **10²時間級**です。

RECORDS=1M自体は規律4違反ではありません。linux-baremetalでもPegasusでも、working set ≥ L3×4を満たす最小値として校正されています。[校正結果](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.md:8) 問題は系列・floor・verifyの乗算です。

縮小候補は次です。

- sweep-ceilingはB-5判定族外なので、別waveへ送れば判定力を全く変えません。
- 草案がN=12の根拠をp値解像度だけに置くなら、3 block×3系列のN=9でも最小p=`1/512 < 0.05/6`です。25%削減できます。ただしpowerはN=12でも未保証なので、発火前の効果量非依存感度解析が必要です。
- 同一stockのfloor標本を系列ごとに複製する必要性を再検討できます。S-1型のblock別共通stockへまとめればfloor精度を保ったまま削減余地があります。
- RECORDSは勝手に下げず、発火環境のcalibrationがより小さい値を選んだ場合だけ変更すべきです。

## 支持する箇所

- 発火条件1は2026-07-10の軸適格性を緩めず、D52の「非列挙code-fragment軸」へさらに絞っています。
- anomalyにもslotを消費させ、A未達をrandom敗北でなく判定不能にする方針は支持します。
- sweep-matched / sweep-ceiling分離、非有意を同等性へ読み替えない規則、全workload報告も既存正本と整合します。
- 「結果既知のtriggerを受けた比較」と限定し、純粋confirmatoryと呼ばない方針自体は正しいです。
- 2 campaign blockはS-1の既存機構で表現可能です。別process＋開始時刻記録という既存の操作的定義を明示的に継承すべきです。

## 親の段 1 実測への指摘

- **ランダム変異入口が不在**という結論は正しいです。
- **「評価回数・bench時間の両予算が実在」も個別機構の存在としては正しい**ですが、B-5の3アーム共通budget consumerが実在する、という一般化はできません。
- **「固定世代・性能早期停止禁止が実在」は誤りです。** report fieldはliteralで、実driverは `converged` / `reverse-exhausted` を継承します。
- sweep棚卸しは不完全です。`s8a_trigger_sweep.py` も実在しますが、preliminary・完全列挙・headline対象外なのでB-5実行可能性は改善しません。[trigger sweep](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/orchestrator/campaign/s8a_trigger_sweep.py:1)
- **(c)(d)自体が休眠**という判断は正しいです。[phase3.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/docs/phase3.md:354)
- **「未確定穴は(c)(d)だけ」は過大一般化**です。B-5固有のTier0、共通driver、B/A ledger、schedule、report/stat consumer、固定B停止、独立性能検証相も未確定です。
- **「唯一の候補T-140が段階B差し戻し・裁定待ち」は現行repoと矛盾します。** T-140は2026-07-28に実測後、択(c)で軸廃止済みで、再開条件は大きい`max_ope` workloadだけです。[phase3.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/docs/phase3.md:157) [一次資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b5-llm-necessity-contrast/output/insights/2026-07-28_t140-setsize-distribution.md:71)
- 他の**実体化済み適格軸**は見つかりませんでした。ただし候補概念はT-140だけではなく、D48のmember-read拡張予約やaxis-proposer束のread-internal spin、tuple false-sharing/Tidword、epoch/GC等があります。いずれも未オンボードで、現時点の発火軸ではありません。

## 総括

草案は既存の保守的判定作法を多く継承していますが、B-5の根幹である同一探索空間を成立させていません。  
D39予算の継承という説明、固定停止の実在、T-140の現況に明確な事実誤認があります。  
(c)(d)は閉じず、実行機構も大半が未実装、費用は直列で百時間級です。  
現在の成果物値は追記前後で何も変わらず、B-5は引き続き未取得です。  
したがって、この版を拘束力ある正本へ追記することには反対します。  
具体軸・同一支持集合・HARK台帳・独立性能検証・総予算を確定した発火時改訂として再設計すべきです。