静的照合の結果、**P1 の実装範囲と総 wall 倍率の分母は縮め直すべきです。一方、read-heavy が k≤4.06 で収まらないという反証は成立しません。**

以下、`JOB` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle`、`PILOT` は `output/insights/2026-09-20/t2797-b5-contrast`、`B8` は `output/insights/2026-09-21/t2807-b8-effective`、`CAL` は `output/env/pegasus/calibration` を指します。repo 内の path は作業木相対です。書込み・テスト・測定投入はしていません。

1. **must-fix — 「投入経路が repo に実在」を完了条件に加えた根拠がない。**

   **根拠:** `JOB/brief.md:7`、`JOB/brief.md:34`、`JOB/codex/s2-plan.md:68`、同 `:156`、`JOB/request.md:9`、`docs/b5-generator-contrast-preregistration.md:541`、`JOB/verbatim/d2202.md:11`。

   §12 が要求するのは実行資材の bytes・hash・実装所在であり、すべての運用 script の repo 内製品化ではない。B-8 は repo 外 runner を束縛している。D2216 の「この段で扱う」も、registered 用 dataclass・複数 CLI・stage submitter 一式を要求していない。

   削減案は次の順がよい。

   - **残す:** driver の purpose/cohort 切替と job body の受け渡し。現 driver は `purpose="pilot"` 固定で、既存 report は purpose 一致を要求するため、これは実在する接続不足である（`b5_generator_contrast.py:573`、`b5_generator_contrast_report.py:200`）。
   - **縮める:** 固定 schedule と job ごとの env/argv を作る小さい投入 script。repo 外で保全し hash を束へ記載できる。既存 job body・submit-tree 契約を使う。
   - **縮める:** 試走 prompt 生成器の path・workload・系列・試走ラベルのパラメータ化と、要求済みの model ID 抽出。template 群の再構成や汎用 CLI 化は必須でない。
   - **送れる:** repo 内 launcher の使い勝手改善。ただし、承認後に実験構成を変える必要がないよう、実際に使う最小投入資材は今回固定する。

   repo 外へ置いても実装面であることは変わらず、Codex author 契約の免除にはならない（`docs/ai-provenance.md:46`）。

   **成果物への影響:** 放置すると、束の実値を増やさない CLI・fixture・登録記述更新が完了条件になり、本走承認までの作業を増やす。

2. **must-fix — 新しい配置検査が一箇所紛れている。ただし schedule のテスト全般を scope 外とする攻撃は不成立。**

   **根拠:** `JOB/codex/s2-plan.md:34`、`orchestrator/campaign/b5_generator_contrast.py:710`、`orchestrator/campaign/b5_generator_contrast_report.py:213`、`JOB/brief.md:36`。

   registered producer に `block == (series-1)//4+1` の拒否条件を足す案は、新しい runtime 検査である。現 consumer が同条件を既に検査する。固定 schedule が正しい座標を生成すれば接続は成立するので、今回 producer 側の追加拒否は削れる。

   一方、plan の schedule 件数・6順序・同時 LLM 数のテストは、実装した生成処理の確認であり、新しい本走 gate とは区別すべきである。plan `:339` は runtime 検査を作らないと明記している。model ID も `:211` の抽出・記録であり、予定 ID との照合による投入拒否は提案していない。

   **成果物への影響:** 配置検査を追加すると、従来 report が規約不適合として記録する入力を producer が台帳生成前に拒否する、新たな挙動が入る。

3. **must-fix — N-e の危険性評価は extime と対象差を補正する必要がある。**

   **根拠:** `JOB/brief.md:25`、`B8/README.md:94`、同 `:132`、`B8/verbatim/verify-records.txt:2`、同 `:12`、`docs/b5-generator-contrast-preregistration.md:285`。

   B-8 の balanced 約220秒／read-heavy 約496秒は、**3秒ではなく10秒 trace** の verifier 実測である。`B8/verbatim/summary-final.json` の `chosen_extime` も10。B-5 の動作点 trace は3秒なので、そのまま5倍して session 費へ入れてはいけない。plan `:439` の訂正は正しい。

   さらに「write-heavy は検査が最も軽い」は対象をまたぐ一般則ではない。B-8 では write-heavy 約295秒が balanced 約219秒を上回る（`B8/README.md:131`）。B-5 試走での選択理由を全候補・現行検査器へ一般化できない。

   出所を分けた費用の材料は次のとおり。

   | workload | 実測 | 換算・試算 |
   |---|---|---|
   | write-heavy | B-5 の非競合7 session は499〜510秒。その他の「固有費」は lock 待ち推定を差し引いた値 | 510秒を計画値に使えるが、Tier0追加前・限られた候補 |
   | balanced | 旧3秒較正は fixed5 が1,581,009 commit／116.44秒、無backoffが4,178,321 commit／332.32秒 | B-8由来の25〜31µs/commitなら verifier 約40〜130秒/trace |
   | read-heavy | B-8 の10秒 trace は約1,969万〜1,995万 commit／492.5〜500.6秒 | 時間比例なら3秒で約591万〜598万 commit、25〜31µsなら約148〜186秒/trace |

   較正の根拠は `CAL/a2_perf_verify_cost_t48_skew0p9_rr50_rmw0.json:46`、同 `:58`、同 `:85`、同 `:97`。write-heavy は `PILOT/README.md:197`。

   **試算:** build・legacy・bench・その他に計60秒、trace走行に各3.4秒を置くと、
   `C = 60 + 5×(3.4 + verifier秒)` から balanced 約275〜725秒、read-heavy 約815〜1,005秒/session。60秒は試走内訳から置いた仮定であり、周辺 I/O と Tier0 の確定上限ではない。

   **成果物への影響:** 補正しないと、別実験の10秒検査費を3秒検査費として計上し、k・総 wall 上限・束の成立可否を誤る。

4. **should — plan の k=2 は成立する換算例があるが、十分性の根拠はまだ弱い。**

   **根拠:** `JOB/codex/s2-plan.md:457`、同 `:490`、同 `:492`、`JOB/verbatim/d2215-d2217.md:61`、`CAL/a2_perf_verify_cost_t48_skew0p9_rr5_rmw0.json:44`、同 `:56`。

   前項の高い側の換算値を使い、**試算として** H=7,800秒、job setup=600秒を置くと次になる。候補・stock の session 費を同じに置く近似である。

   | workload | session費 | 非LLM系列：16 session | LLM系列：左＋H | block-stock：5 session |
   |---|---:|---:|---:|---:|
   | write-heavy | 510秒 | 8,760秒 | 16,560秒 | 3,150秒 |
   | balanced | 725秒 | 12,200秒 | 20,000秒 | 4,225秒 |
   | read-heavy | 1,005秒 | 16,680秒 | 24,480秒 | 5,625秒 |

   この換算なら k=2 の W=42,518秒、W_stock=10,894秒に収まる。

   ただし、B-8 の25〜31µs/commitは対象横断の上限ではない。指定された旧較正では約67〜80µs/commitである。read-heavy の換算commit数に80µsを当てる**感度試算**では session 約2,471秒、LLM系列約47,936秒、stock約12,268秒＋setupとなり、k=2は不足、k=3なら収まる。旧単価を現行の予測値にする根拠もないので、これはストレス例に留める。

   また `within_run.median≈10.24M tps ×3秒` を trace commit 数とみなすのは不可。較正の binary は trace-disabled である（`CAL/between_run_noise_t48_skew0p9_rr95_rmw0.json:13`）。

   k上限での実際の W は86,312秒、W_stockは22,115秒。setupを除きH=7,800秒、共通session費という近似なら、系列側は約4,907秒/session、stock側は約4,423秒/sessionが境界になる。plan の4,700秒例で stock 側が先に破綻する指摘は正しい。ただし4,700秒自体は実測値ではない。

   **成果物への影響:** 換算を保証扱いすると allocation-exhausted と score 欠測を過小評価する。逆に高費用の仮定だけで「成立不能」とすると、本走へ進める構成を不必要に止める。

5. **must-fix — 総 wall 倍率の分母569時間は、試走実測ではなく外挿である。**

   **根拠:** `JOB/codex/s2-plan.md:509`、`PILOT/README.md:194`、`docs/b5-generator-contrast-preregistration.md:528`、`JOB/verbatim/d2200-head-item1.md:44`。

   試走の job Elapse 総和は **61,261秒＝17.016944時間**。共有lock待ちと job 内の親待ちを含む。この raw 値を総 wall 倍率の基準として明記するのが、§11 とD2200の計上対象に最も忠実である。

   `61,261×1773/53≈569.265時間` は全sessionを同率で増やした外挿で、実測ではない。試走ではstockが5/53、本走では45/1773で構成比も違う。job種別を保った外挿なら、
   `36×(17,286+17,269+21,259)+9×5,447`
   ＝571.7575時間になる。いずれも参考予測としてはよいが、raw基準への倍率と混ぜない。

   - 600時間の上限なら、raw試走比 **35.259倍**。
   - 丸い倍率 **36倍なら612.61時間**。
   - plan の「約1.054倍」を使う場合は、必ず「session比例外挿値への倍率」と呼び、raw比も併記する。

   前項の換算例では1773 sessionの固有費＋36系列の親待ち＋117 jobのsetupが約465.2時間。612.61時間との差約147.4時間を追加費用の余裕とする案は作れる。ただし失敗・retry・再測定の全組合せを保証する値ではない。

   **成果物への影響:** 同じ「倍率2」でもraw基準では34.03時間、plan基準では約1,138.53時間となり、承認する費用上限が約33.45倍違ってしまう。

6. **must-fix — P4 は「機械記録手段」を満たしても、exact model の事前固定を満たしたとは言えない。**

   **根拠:** `JOB/brief.md:43`、`JOB/codex/s2-plan.md:245`、`docs/b5-generator-contrast-preregistration.md:190`、`JOB/verbatim/d2200-head-item1.md:16`。

   過去の応答IDが `claude-opus-5` だったこと、role定義のhash、将来のtranscript抽出器は、aliasの解決先を固定しない。planはこの限界を正しく書くが、**限界を併記するだけで「発効可能」とするのは別問題**である。

   対処は新しいmodel照合gateではない。予定exact IDを指定する実際の起動方法が固定できるなら、その構成を束へ記録する。できないなら「alias起動のままで§4.1の固定要件が未充足」を阻害事実として再提示する。記録器の汎用化より先に判断すべき項である。

   **成果物への影響:** 放置すると、束に書いたモデル構成と実走構成が異なり得るのに、モデル固定済みとして承認へ送ってしまう。

7. **should — N-f の数値は正しいが、P5 の一般化は限定が必要。**

   **根拠:** `JOB/brief.md:28`、同 `:46`、`CAL/between_run_noise_t48_skew0p9_rr{5,50,95}_rmw0.json:20`、`JOB/verbatim/d28.md:3`、`JOB/codex/s2-plan.md:386`。

   指定された10 rep列から独立に再計算した `rep1 / median(rep2..10) −1` は、rr5 **+7.0138%・最大**、rr50 **−3.3512%・最小**、rr95 **+2.6023%・最大**。N-fへの数値攻撃は不成立である。

   ただし無backoffの各10 rep列から、B-5全候補のwarm-up不要までは導けない。D28のrun冒頭区間の破棄と、独立した5 runの第1 run除外も異なる操作である。「1件でも1%ならwarm-up変更が要る」は因果判定として強すぎる。planの「感度基準であり原因の証明ではない」という訂正を採るべきである。

   `PILOT/README.md:185` の「median採用なのでfitnessは動かない」も一般には誤り。planが報告する53 sessionの最大差0.6960%は、現行構成を維持する限定的根拠として扱い、全workloadへの保証にしない。

   **成果物への影響:** 過度な一般化は、不要なsession定義変更、または未確認workloadまでwarm-up影響なしとする記述につながる。

## 総括

- **削れる実装:** repo内registered launcher一式、prompt toolの全面再構成、producerへの配置拒否追加。固定schedule・最小投入script・試走prompt生成器の最小差分・model記録手段を束縛すればよい。driverのpurpose/cohortとjob bodyの受け渡しは残す。
- **研究前進の順序:** exact model固定の可否と費用基準を先に確定し、既存資料の採取と(b)(c)を終え、最小接続差分と実行資材を固定して再提示する。汎用CLI整備を前提にしない。
- **k・総wallの推奨:** 現行B-8単価を用いる換算条件では、**k=2、raw試走Elapse総和の36倍＝612.61時間**を候補にできる。ただしread-heavyのB-5 trace費・適応stock費は未実測で、完走保証とは書けない。高費用感度例を計画値として採るならk=3が必要になる。**k≤4.06で成立不能という実測事実は見つからなかった。**
- **P1:** 部分反対。接続不足の解消には賛成、repo内製品化の必須化には反対。
- **P2:** 賛成。静的な9 stage表と手順なら十分簡潔。4組ずつ3 armを順に走らせる代替でもp≤4を満たすが、逐次段数が増えるため最短とは言えない。stage同期自体を過剰とする攻撃は不成立。
- **P3:** purpose受け渡しに賛成。launcherの拡張規模は縮小。
- **P4:** 記録手段に賛成。aliasの事後記録だけで固定要件充足とする扱いには反対。
- **P5:** 現行5 rep維持に限定付き賛成。warm-up原因の断定を削る。
- **P6:** 記録のみの方針に賛成。初回投入後skipではB過少計上が残り、reportの件数照合とsidecar回収では検出されず、score欠測になるというplanの追跡はコードと整合する（driver `:367`・`:647`、report `:297`・`:313`・`:432`）。
- **P7:** 方針に賛成。extime補正、単価の対象差、stock側上限、raw倍率を明記する。
- **P8:** 賛成。親起動の自動化は不要。
- **P9:** 賛成。draftの構成値を固定し、承認後はstatus変更と承認情報追加。briefの「statusだけ」はD2202の省略表現として訂正する。
- **その他の不成立項目:** Tier0・node-local lock・p=4・2,700秒・D2217のwalltime式をplanが作り直している証拠はない。campaign ledger field追加、model ID照合gate、実行順・block間隔のruntime検査もplanには見当たらない。