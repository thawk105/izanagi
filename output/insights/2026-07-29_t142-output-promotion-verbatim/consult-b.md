必須指定資料はすべて全文読了できた。現行コード、全30本の WAL、calibration、実レポート、既存テストを静的照合した。結論は **NO-GO**。編集・pytest 実走はしておらず、緑は主張しない。

## Findings

### 1. [BLOCKER / real] 現行 driver では唯一の省略枝が数学的に到達不能

plan の省略条件は `slower && !near_floor` だけである（[plan.md:39](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:39)）。一方、実 driver は `reps=2`（[p3_s4_loop.py:509](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop.py:509)）で、`compare()` は floor 超の差でも Mann–Whitney の `p<0.05` でなければ `no-difference` に戻す（[stability.py:281](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/calibrator/stability.py:281)）。

n=2 対 n=2 では、完全分離しても現実装の両側正規近似・連続補正は `p≈0.245`、群内 tie があっても最良側で約 `0.194` である。したがって `faster/slower` は出ない。完全分離で初めて `p<0.05` になり得るのは n=4 であり、それも必要条件にすぎない。

実成果物でも、

- sort は初回候補1件なので必ず promotion（[sort WAL:5](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/runs/wal.jsonl:5)）。
- trigger は初回候補と、そこから僅か +0.31% の2件目だけ（[trigger WAL:5](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl:5)、[同:11](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl:11)）。

よって親が G04 根拠とした実 path では **3/3 promotion、0/3 skip、削減0%** である。exact floor が存在しても変わらない。

- 成果物影響: 省略による certified 選択・正式レポート・proof chain の値は変わらず、別 campaign identity と機構だけが全試行台帳へ増える。逆に `legacy→bench→S2` への順序変更は、既存裁定が指摘する非可換性により S2 verdict を変え得るため、効果ゼロなのに certified 選択だけ変わるリスクが残る。
- 最小修正／停止条件: 実装停止。まず実 driver の measurement design を使う生死試験を行う。`reps≥4`、比較規則変更、または MW gate 廃止はいずれも測定・受理意味論変更なので追加裁定が必要。現状は DW-G01/G02/G04（[core.md:45](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/dev-wave/core.md:45)）および規律5（[CLAUDE.md:81](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/CLAUDE.md:81)）に反する。

### 2. [BLOCKER / real＋一部 refuted] exact floor は本当に無い。ただし既存 calibration 部品はある

「plan が既存 exact floor を見落とした」という疑いは **refuted**。全30 WAL、env calibration、s8b freeze を照合した結果は次のとおり。

| 座標 | 現行 sort/trigger | 最も近い既存 between-run |
|---|---:|---:|
| env | linux-baremetal | linux-baremetal |
| records | 100,000 | 1,000,000 |
| threads | 4 | 48 |
| workload | rr50 / skew0.9 / rmw=false | rr50 / skew0.9 / rmw=0 |
| extime | 1 | 3 |
| reps/session | 2 | 5 |
| sessions | 未較正 | 8 |

既存値は [between_run_noise…json:2](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr50_rmw0.json:2) と同ファイルの [records/threads/run_cmd:8](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr50_rmw0.json:8)、[session設計:33](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr50_rmw0.json:33) に固定されている。Pegasus 登録値は env が違い、しかも within-run のみ（[calibration…json:1568](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1568)）。s8b も Pegasus、extime=5、reps=5 の別 protocol である（[floor_protocol.json:1](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/s8b-freeze/floor_protocol.json:1)）。

100k/t4/extime1/rr50 に一致する既存 bench は8件あったが、8件とも別 variant・別 command groupで、同一 variant の反復は0件。between-run CV は算出できない。

ただし plan は再利用可能なコード経路を過小評価している。

- 汎用計算器 `between_run_noise_floor()` は既にある（[stability.py:97](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/calibrator/stability.py:97)）。
- 実機 producer もあるが、1m/t48/extime3/reps5へ hard-code されている（[between_run_floor.py:44](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/between_run_floor.py:44)、[同:53](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/between_run_floor.py:53)）。
- env別 resolver も既にあり、records/threads/workload の不一致を明示できる（[layer3_report.py:213](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/layer3_report.py:213)）。ただし extime/reps は未照合。
- D58 loader は workload だけなので流用不可（[screening_driver.py:34](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/screening_driver.py:34)）。

さらに campaign lock 自体が workload/extime/reps を持たない（[sort lock:1](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/campaign.lock:1)）。現状では run command だけが完全座標を保持する。

- 成果物影響: strict fail-closeなら全候補S2となり、四成果物に削減効果はない。workloadだけの既存 loaderを誤用すれば偽 `slower` で真の selected/tie を正式レポート・proof chainから欠落させる。
- 最小修正／停止条件: 新 `promotion.py` の独自 resolver より先に、既存 producer/helperを使った小さい calibration waveを行う。成果物には env、pin、calibration genome/対象母集団、records、threads、正規化 workload、extime、reps、sessions、source hash を明示する。D19 が示す genome/abort率依存もあるため、単一 stock floorだけで全生成候補を覆うのか、高-abortを曖昧側へ送るのかも凍結が必要。

### 3. [BLOCKER / real。planが88%を無条件期待値にした、は refuted] 88%は対象 S2 の削減率ではない

集計スクリプトは全 campaign の全 numeric COMMIT を数え、raw median の record high だけを new-best とする（[measurement-scripts.md:64](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-28_t142-review-verbatim/measurement-scripts.md:64)、[同:72](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-28_t142-review-verbatim/measurement-scripts.md:72)）。S2実行、`verify_configs`、floor、tie、near-floor、unstable、対象driverを一切照合していない。

全30 WALの再集計結果は、

- numeric COMMIT: 426
- S2 `verify_done`: 111
- numericかつ `verify_configs` にS2を持つCOMMIT: 78
- その78件に限定した raw new-best: 18、したがって raw skip上限は60/78 = **76.9%**
- 実対象sort/trigger: **0/3 = 0%**

である。したがって「376回のS2を省けた」は、実在S2試行111件より大きく、S2未導入・legacy-only campaignを大量に含む反実仮想ラベルである。

plan 自身は外挿禁止を明記している（[plan.md:154](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:154)）ため、「planが88%をそのまま期待値にした」は refuted。ただし親の投資根拠として88%を残すのは real な誤誘導である。

- 成果物影響: certified 選択自体ではなく、正式レポート／proof chain の効果量主張と、全試行台帳から導く分母・削減秒数が誤る。
- 最小修正／停止条件: 88%と12.2時間をGO根拠から削除し、「全numeric COMMITに対するraw counterfactual上限」と改名する。対象候補列を事前固定した all-S2/adaptive paired pilotで、`eligible / promoted / skipped / S2秒 / 総wall秒` を別々に測る。

### 4. [BLOCKER / real] tie意味論が未裁定で、online skipはOを保存できない

現物には二つの非同値な規則がある。

- p2 report: winner と各候補を直接比較（[p2_2_report.py:149](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p2_2_report.py:149)）。
- replay: no-difference の推移閉包（[replay.py:176](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/replay.py:176)）。

後者では `A~B, B~C, A≁C` の橋渡しが起きる。CをAとの直接比較だけで不可逆に落とせば、最終tie集合は保存できない。新Dを書くことはD96の手続充足にすぎず、どちらを「ユーザーが求めるO」とするかの裁定を代替しない（[D96:4271](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/decisions.md:4271)）。

- 成果物影響: certified selected/tie集合が直接変わり、正式レポートとproof chainが別結論になる。全試行台帳は残っても、正式選択から真のtie候補が落ちる。
- 最小修正／停止条件: 追加ユーザー裁定が必要。推移閉包を維持するなら adaptive skip は停止。direct-winnerを採るなら、`100–98–96` 型と全到着順 permutation を境界vectorにし、最終selectorとonline gateの集合一致を検査する。

### 5. [BLOCKER / real] p3に formal selected/stock/tie consumer が存在しない

現行 layer3 schema は selected/stock/tie を持たず（[layer3_schema.json:6](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/layer3_schema.json:6)）、renderer は全 `bench_done` を `runs` へ並べる材料射影だけである（[layer3_report.py:356](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/layer3_report.py:356)）。phase docも selected/baseline/stock/tie を将来仕様として記すだけ（[phase3.md:419](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/phase3.md:419)）。

s8b oracle は実在するが別経路であり、`screen_outcome=="not_enabled"` を要求する（[s8b_oracle_judge.py:54](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/s8b_oracle_judge.py:54)）。T-142のsort/trigger WAL consumerではない。

- 成果物影響: T-142だけでは「final Oを保存した」を検査も証明もできない。formal selected/stock/tieは依然不存在で、proof chainは材料runまでしか結べない。
- 最小修正／停止条件: real selectorを先に実装・凍結するか、保証対象を `O_run` の認証済みrun射影だけへ狭める。後者は親briefの保証変更なので追加ユーザー裁定が必要。将来consumerのための試行一般化・schema一般化は規律5により今waveから外す。

### 6. [GO-BLOCKER / real。CLI不存在説は refuted] 実entrypointはあるが、発火する現役carrierがない

CLI自体は実在し、過去にユーザー経路から使われている（[sort runbook:133](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/phase3-s5-sort-runbook.md:133)、[trigger runbook:78](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/phase3-s8a-trigger-runbook.md:78)）。したがって dead API そのものではない。

しかし、

- sort iteration 2 は見送りで完了（[phase3.md:271](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/phase3.md:271)）。
- trigger 100k/t4探索はクローズし、単独再ホストしない（[phase3.md:370](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/phase3.md:370)）。
- 次の8b pathは別oracleで、親briefも不変を要求する。
- 両runbookは新flagを有効化する将来手順を持たない。

親briefの過去2 campaignは「S2-on loopが動いた」証拠ではあるが、exact floorもskip候補もなく、promotionの発火条件を満たすartifact pathではない。DW-G04の根拠には不足する。

- 成果物影響: 現役carrierがなければ certified選択・正式レポート・proof chain・全試行台帳のいずれも変わらない。したがってコード側対応はG05上 must-fixではなく backlog。
- 最小修正／停止条件: promotionを実際にONにする次campaign ID、runbook、対象候補列、formal output consumerをbriefへ先に記す。書けなければ設計メモ／裁定パッケージで停止する。

### 7. [MAJOR / real] `STAGE_NOT_PROMOTED`＋schema v3＋attempt一般化は最小でない

既存D58には既に以下がある。

- terminal非採用を表す `STAGE_ABORT`（[model.py:20](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/model.py:20)）。
- resume時に非retryable abortを再実走しない状態（[model.py:130](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/model.py:130)）。
- 正常な未認証棄却を表す専用reason（[pipeline.py:76](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/pipeline.py:76)）。
- identity/reasonだけをcriticへ射影する `ScreenRejection`（[digest.py:141](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/critic/digest.py:141)）。
- 未認証数値を隠す実WAL回帰（[test_bench_first_real_wal.py:69](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_bench_first_real_wal.py:69)）。

D58の閾値規則そのものはpromotionへ流用できないが、状態・resume・正常棄却・critic redactionは再利用できる。`STAGE_ABORT + reason="s2-not-promoted"` と専用reason分類なら、verifier-redと混同せず第三のgeneric WAL stageを増やす必要はない。

また v3 は機序仮説層用に予約済み（[layer3_report.py:12](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/layer3_report.py:12)、[phase3.md:415](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/phase3.md:415)）。selection consumer不在のまま予約を奪うと、正式レポートschemaとproof hashだけが変わる。

attempt parserは、将来正式runを試行単位で束縛するときには実在する correctness 要件である。現行 `replay()` はvariant単位でterminalを累積するだけ（[wal.py:566](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/wal.py:566)）。ただしconsumerも発火pathもない今waveへ先払いする理由にはならない。

- 成果物影響: 新stageは全試行台帳のwire grammarとconsumer閉包を変え、v3は正式レポートschema・source refs・proof hashesを変える。certified選択の値を改善する実効性は現状ゼロ。
- 最小修正／停止条件: 今waveは裁定パッケージだけで停止。将来のpilotは既存ABORT＋新reason、既存redaction、既存identity pattern、既存calibration helperまでに限定し、layer3対象外とする。実skipとformal selectorが生きた後に、attempt束縛とschemaを独立waveで扱う。

### 8. [MAJOR / real] 325/9 baseline と新テストの検出力が混同されている

`325 passed / 9 skipped` は親の過去測定値であり（[parent-brief.md:21](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/parent-brief.md:21)）、本レビューでは再実走していない。

既存suiteが既に検査するものは、

- COMMIT/ABORT terminal
- D58 screening境界（[test_campaign.py:1915](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_campaign.py:1915)）
- S2 all-pass/red/配線（[test_campaign.py:2200](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_campaign.py:2200)）
- criticの未COMMIT除外（[test_critic.py:101](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_critic.py:101)）
- layer3のfloor照合・双射・reject

である。

特に既存layer3テストは未COMMIT benchを `rejects` に載せることだけを検査し、`runs==[]` を要求しない（[test_layer3_report.py:413](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_layer3_report.py:413)）。したがって baseline の「被覆」は漏洩防止ではなく、現行漏洩を許したままの被覆である。planの `runs==[]` 強化は純増検出力を持つ。

一方、提案テストには次がない。

1. 実 `default_perf(reps=2)` で `slower` 枝へ到達できるか。
2. actual CLIがexact floor artifactを読むか。
3. sort/triggerのユーザー経路でS2 call数が本当に減るか。
4. live campaignで自然候補のskipが1件以上発生するか。
5. formal selected/stock/tie consumerの結果がall-S2対照と一致するか。
6. 順序変更後もS2 verdictがpaired対照と一致するか。

synthetic比較行列とmutationはすべて緑でも、productionのn=2が全件`no-difference`であることを検出できない。

- 成果物影響: false-greenにより、全試行台帳でS2削減0件、formal Oは未実装のままなのに、正式レポート／proof chainで機構完成を主張し得る。
- 最小修正／停止条件: GO前の受入vectorは、(a) exact全座標一致と各1座標不一致、(b) actual configでclear-loserがS2未実行、初回/no-difference/near-floor/unstableはS2実行、(c)再開時に正常棄却を再実走しない、(d)同一候補列のall-S2対照とselected/tie/proof refsが一致、(e)実wall秒が正に減る、である。現状は(b)(d)(e)を満たせない。

## 総括

**NO-GO。追加ユーザー裁定なしで実装へ進める最小案はない。**

今waveの最小scopeはコード変更ゼロで、裁定パッケージへ次を追記して停止すること。

- 現行 `reps=2` では省略枝が到達不能。
- exact floorは実在しないが、既存calibration producer/helper/resolverは再利用可能。
- 88%は全COMMIT混合集計で、S2対象限定の期待値ではない。実対象では0/3。
- sort/triggerは過去entrypointとして実在するが、現役carrierではない。
- formal selected/stock/tie consumerは未実装。

再GOには、先行実測と追加ユーザー裁定の両方が必要である。

- 先行実測: intended env・100k/t4・rr50/skew0.9/rmw・extime1・採用repsに完全一致するbetween-run calibration、actual candidate列でのpaired liveness／walltime確認。
- 追加裁定: direct-winnerか推移閉包tieか、`reps≥4`等の測定設計、再開するlive campaign、Oをselected/tieまで保証するか`O_run`へ狭めるか。
- 推移閉包tieを維持する、またはlive carrierを指定しない場合は、T-142は「価値ある安全な省略域なし」でcloseするのが最小である。