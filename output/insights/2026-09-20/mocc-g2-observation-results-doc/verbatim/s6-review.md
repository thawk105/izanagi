## 所見

静的照合と独立再計算を実施した。pytest・build は実行していない。生 trace は336 fileの集合・サイズを確認し、B1/082のC行を照合したが、全件の再hashは行っていない。

以下、「稿」は [2026-09-20-mocc-g2-observation-conditions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-g2-observation-results/docs/paper-story/results/2026-09-20-mocc-g2-observation-conditions.md)、「原job」は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/` を指す。

1. **must-fix — 観点7・15：§4項3、§0.4。「thread idが成果物に無い」は誤り。**

   稿は「G2 cycle の thread id・実行順序・読み値の出所照合」をまとめて不存在としている。しかし、保全されたB1/082の生traceに次がある。

   | 原job内のfile | 現物のC行 |
   |---|---|
   | `arm-B/B1/runs/082-e9-instr-nowit/trace/trace_33.log` | `C 406139 33 42 176 4 6` |
   | 同 `trace/trace_0.log` | `C 406140 0 42 177 6 4` |

   保存source `verbatim/mocc-transaction-e9e477ca.cc.txt` の `writePhase()` は、C行を `txid thid_ epoch tid …` の順に出力する。したがって、このcycleのthreadは **406139→33、406140→0** と照合できる。

   **修正案:** thread idを不存在の列挙から外し、「verifier JSONには含まれないが、生traceのC行に記録されている。本稿では対応表を作成していない」とする。実行順序・読み値の出所の未同定は別に残す。放置すると、執筆者が保全済み証拠の情報量を誤って過小記述する。

2. **should-fix — 観点1・5・9：§2、§5項17、§6.3で出所の分類が正確でない。**

   §2項5の数値自体は一致するが、出所表の「事前登録・主張範囲・標本根拠 → `s4-ruling.md` 項3・6・7、親briefの訂正」だけでは足りない。

   | 値・表現 | 現物 |
   |---|---|
   | 0.058対0の0.83、0.05対0の0.72 | `s4-ruling.md` 項6にある |
   | 部分抑制0.058対0.02の0.30、各α=.025の約0.70 | 同文書には数値の記載がなく、記録insight README §4にある |
   | 基準率の由来7/120・2/40 | 同文書にはなく、記録insight README §4にある |

   また、§5項17の「本稿の値は**全部 runner が走行時に出した JSON の書写**」は、dispatch時刻・Elapse、検出力、独立計算したFisherなどには成立しない。

   **修正案:** s4本文の直接記載、記録insightの設計説明、今回の再計算を分けて出所表へ記す。§5項17は「G2構造の表は走行時のverifier/run JSONから転記し、生traceからの再検証は行っていない」などへ限定する。放置すると、計算値や説明文まで事前登録の直接記載・runner出力として引用される。

3. **should-fix — 観点9・10：§5項16のD1373による現況断定は、提示された根拠を超える。**

   該当文は「現行pinのcheckoutでは……D1373の関門でbuild前に拒否される状態のまま」。

   `docs/decisions.md` D1373の現物は、**実際にコンパイルされるsourceを読んで判定する契約**と2026-09-01時点の説明である。T-2779のresult JSONは当該floor関門の実行記録ではない。これらから、稿作成時点の実checkoutでの拒否を確認したことにはならない。

   **修正案:** この現況文を削り、「本観測はbetween-run floorの生成可否を検査・変更したものではない」とするか、実checkout・判定器・拒否結果の一次証拠を追加する。放置すると、未検査の現況を本観測が確かめた事実として執筆することになる。

4. **should-fix — 観点12、P1：§0.2の系列配置の説明は、先例の論拠が不足する。**

   [README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-g2-observation-results/docs/paper-story/README.md) の規則は「1結果（1 protocol または1 campaign群の完走）」。A-1の先例は非認証である一方、表にもcampaign WAL・登録済み解析が明示されている。**非認証という共通点だけでは、今回の単位が規則に適合する説明にならない。**

   ただし、本試行には事前に固定した標本・比較・欠測規則があり、これを「単一の観測protocol」と明示すれば規則違反とは断定しない。

   **修正案:** 「s4-rulingで定めた単一の観測protocolを4 blockで完走した1結果」と記し、A-1の類推を配置の根拠から外す。その解釈を採らない場合は、results外の観測材料として置く必要がある。

5. **should-fix — 観点11・15：§3.6の引用用例文が4 blockを1 blockに読ませる。**

   稿の例文は「同一 cell・**同一 block の3 arm ×各120走**」。

   現物は `arm-B/B1〜B4/result.json` の各blockで **各arm30走**、4 block合算で各120走である。

   **修正案:** 「同一cellで、各block内に3 armを配置した4 block、各arm合計120走」とする。放置すると、この例文だけを結果節へ移した際に、1 node・1 binaryの120反復として読まれる。

6. **nit — 観点15：§1.2の診断armの `observational_only: true` の意味を一文補うとよい。**

   現物の`bindings.arms`と表のtrue/falseは一致する。runnerではこのfieldをrun/discriminator記録へ保持しており、それ自体がverifier verdictを書き換える処理ではない。§0.1はfalseや`certified:true`の限界を説明する一方、trueの意味は明示していない。

   「診断介入の観測専用という位置づけを記録するfieldであり、個別verifier判定とは別」と補足できる。現状も全体の非certifying限定は明確なのでnitに留める。

所見のない観点・照合済み部分は以下のとおり。

- **観点1：数値・hexの転記に不一致なし。** 4 block＋smoke、7走のJSON、原patch、runner、arms、diff、dispatch logs、insight・summary・errataのSHA/byte数、pin・outer commit・収載commitを照合。出所表現の問題は所見2・3。
- **観点2：不一致なし。** `runs[].verifier.status`を再集計し、通常のblock別kは **1/2/1/1**、診断は **0/0/0/0**、backoffは **0/2/0/0**。各分母30、合算120。CPは独立した二項分布の裾確率反転で掲載精度まで一致。Fisherは **0.029950744134314918 / 0.2230864755405355**。
- **観点3：不一致なし。** 7走のcycle、key下4桁、全`u_ver/v_ver`、round、commit数をverifier/run JSONと照合。位置は`order.index(arm)+1`で **1/3/3/3/2/3/2**。
- **観点4：不一致なし。** 5 dispatchのCreated/Started/Ended/Elapse、4 resultのUTC時刻、JST換算を照合。Elapse合計 **8,911 S**、smoke **116 S**。
- **観点5：主比較・主表示・欠測規則・主張範囲に意味の不一致なし。** §2項6の引用句もs4項7と一致。mtimeは **15:26:11 JST**、自己記載は15:30で、双方ともsmoke投入前。ただしmtimeは凍結・改変不能の証明ではなく、§4項10の限定を維持すべき。補足数値の出所は所見2。
- **観点6：不一致なし。** 列挙されたbinding値は4 blockで一致。各armのbinary SHAは4種類。通常とbackoffのsource SHAは同一。
- **観点7：thread id以外の検査対象に不一致なし。** 非G2の353 run directoryすべてで`trace/`不在。bindingsにverifier file別digestなし。result/run記録・stdout/stderrに数値seed記録なし。witness-on armなし。
- **観点8：不一致なし。** 限定 **10＋8＝18項**、§4 **12項**、本走 **360走**、G2 **7走×48＝336 file**、manifestと現物サイズ合計 **1,981,789,619 byte**。
- **観点9：§6.5のX/P命題は版だけに依存しない。** `result.json.bindings.arms[*].patches`と記録insight §2から独立に確認できる。D1373の現況文は所見3。
- **観点10：所見3を除き不一致なし。** D2148項13、D2150項1、D2159、規律1/2/7と、非certifying・根因未確定・旧束縛保持・本観測による昇格なしの限定は整合する。
- **観点11：効果・不在・根因を過剰に結論する表現なし。** CP/pから同等性やfamily全体の有意性を導いていない。例文の実験単位は所見5。
- **観点12：append-only・一次資料使用・statusを研究の成否へ拡張しない扱いは整合。** 図なし。配置の論拠は所見4。
- **観点13：P2に規律1違反なし。** commit数は`commit_count`と一致し、診断生値と明示され、throughput比・signal/commit率へ転用されていない。注記は十分。
- **観点14：P3の基本方針は妥当。** §2・§4項12・§5項13が設計仮定と再照合未実施を明示する。検出力も独立計算で **0.831467 / 0.721809 / 0.302390 / 0.701730**となり丸め値と一致。直接の出所は所見2のとおり修正する。
- **観点15：witnessコードを含むpin／env off、outer verifier、位置分布は記載済み。** 欠落・誤記は所見1・5・6。§0.4やSHA表について、削除しなければ結果節が誤るという根拠はなく、削除要求はしない。
- **観点16：README行の値・限定・status記述に追加の不一致なし。** 対象／protocol statusの欄分けは他行と一致し、稿にない結果命題を加えていない。配置説明は所見4と連動する。

## 親の brief への異議

[HANDOFF.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-g2-observation-results/HANDOFF.md) に対する判定は以下のとおり。

- **P1：論拠に異議あり。** A-1が非認証であることだけでは系列配置を正当化できない。単一の事前登録観測protocolとして説明する修正を推奨する。
- **P2：異議なし。** 診断生値としてのcommit数掲載は規律1と両立する。表・範囲の値も一致する。
- **P3：方針に異議なし。ただし出所の混同を直す。** s4の直接記載と、記録insightにある基準率の由来・追加検出力を区別する必要がある。
- **親の実測要点は再照合範囲で一致。** ただし「機械照合ALL OK」は、thread idの不存在やD1373の現況断定など、散文の正確さまで保証しない。

## 総括

**must-fix 1件、should-fix 4件、nit 1件。着地は止める。**

保全traceに存在するthread idを「成果物に無い」と断定しているため、少なくとも所見1を修正してから凍結すべきである。