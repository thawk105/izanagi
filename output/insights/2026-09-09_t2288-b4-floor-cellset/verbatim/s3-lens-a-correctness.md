## (γ) の正当化の判定

- **real 候補 — (γ) は正当化できず、採用不可。** calibration artifact は `saturated=false`、`lower_bound_selected=true` で、balanced workload における `maxrss >= 4 x L3` の最小点を `records=1,000,000` としたものにすぎない。[calibration artifact:1603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1603) [calibration artifact:1685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1685) D15 はさらに、飽和点が workload、特に skew に依存するため calibration を代表 workload でキーし、単一 calibration を全 workload に使う案を明示的に却下している。[docs/decisions.md:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:222) [docs/decisions.md:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:235)
  成果物への影響: rr50 の選択点を rr5・rr95 の校正済み点として扱い、certified 選択と floor レポートの受理集合を根拠なく拡大する。

- **real 候補 — maxrss は純粋な table-size 定数ではない。** table 初期化個数自体は `ycsb_tuple_num` だけで決まるが、`ru_maxrss` は workload 実行終了後に読む process peak RSS である。[ycsb.hh:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/external/ccbench/include/ycsb.hh:179) [result.cc:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/external/ccbench/common/result.cc:633) read は値を deep copy し、write は新しい `YCSB` payload を確保し、RMW は両方を行うため、rratio・rmw・max_ope は実行時の resident peak に作用し得る。[ycsb.hh:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/external/ccbench/include/ycsb.hh:59) [ycsb.hh:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/external/ccbench/include/ycsb.hh:121) [tuple_body.hh:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/external/ccbench/include/tuple_body.hh:26)
  成果物への影響: 同じ records が偶然選ばれたことを workload 非依存の working-set 証明として台帳へ残してしまう。

- **real 候補 — `noise_floor.cv` も workload 依存だが、floor の量とは別。** artifact の CV は balanced の連続 10 rep による `kind="within-run"` であり、D15 は noise CV の workload 依存を実測済みとする。[calibration artifact:1577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1577) [docs/decisions.md:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:228) D19 のとおり、これは一測定の品質ゲートであり、driver が測る時間分離された between-run floor の代用品ではない。[docs/decisions.md:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:331)
  成果物への影響: final floor の値へ CV を直接流用はしないが、balanced での `quality.status=accepted` を別 workload の校正品質まで保証するものとして誤読させる。

- **real 候補 — 規律 4 の充足は未証明。** `1m` が rr5・rr95 でも L3 下限を満たす可能性はあるが、その測定は存在せず、D15 はまさに代表 workload ごとの校正を要求している。
  成果物への影響: 実際に下限割れする cell まで受理可能になり、cache 競合が弱い楽観的な D と floor が certified 成果物へ入る。

## より狭い案の有無

- **real 候補、ただし正しさには不十分 — (γ') は実在する。** calibration workload が cell 集合の一要素であるという検査は、balanced cell を含む今回の形と b10 を通しつつ、単一 cell rr5 と無関係な rr50 calibration などを拒否するため、(γ) の真部分集合である。plan は単一 cell・全 cell 不一致まで拡張すると自認しており、それでも (γ') を検討していない。[s2b-plan.md:19](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:19)
  成果物への影響: (γ) のままでは、成果物の workload 集合に calibration workload が一件も含まれない authority JSON まで発行対象になる。

- **refuted 候補 — workload key を削れる形の (γ'') は成立しない。** skew はアクセス先分布と miss-rate 系列を変え、rratio は READ/WRITE を選び、rmw は blind write と read-copy-write を切り替える。[ycsb.hh:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/external/ccbench/include/ycsb.hh:62) [ycsb.hh:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/external/ccbench/include/ycsb.hh:65) [ycsb.hh:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/external/ccbench/include/ycsb.hh:70) さらに `ycsb_max_ope` も一 transaction の確保・接触量を変えるが、calibration workload object に存在せず、D1696 により人手確認項目として残されている。[floor_pair_driver.py:775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:775) [docs/decisions.md:51702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:51702)
  成果物への影響: records に効かないと証明済みの key はなく、縮約した一致条件も校正済み動作点の受理を誤って広げる。

## 受理集合が意図より広がる経路

- **real 候補 — 偶然 records が一致する任意 workload の再利用。** 変更後は env、clocks、threads、records、accepted だけが残るため、rr20、rr50、空 workload、別 skew の calibration でも `records=1m` が一致すれば rr5 または rr95 の単一 cell を通せる。[floor_pair_driver.py:1153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1153) [floor_pair_driver.py:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1181)
  成果物への影響: calibration workload が authority artifact に記録されないまま、cell workload 集合だけが正規 identity として残る。[issuer.py:913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:913)

- **real 候補 — calibration workload の shape 自体も無検査になる。** calibration/v2 は workload を任意の `dict[str,str]` として受理し、exact YCSB key 集合や非空性を要求しない。[schema_v2.py:705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/calibrator/schema_v2.py:705) 現行 equality は cell 側の exact 3-key objectとの比較によってこれを拒否するが、(γ) はその最後の拒否を消す。
  成果物への影響: `workload={}` や異種 key の tracked accepted calibration も同じ records なら floor producer の受理集合へ入る。

- **refuted 候補 — plan は単一 cell と全 cell 不一致を形式上は見落としていない。** plan の拡張集合はこの二経路を明記している。[s2b-plan.md:30](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:30) 問題は集合記述の不足ではなく、その集合を許してよいという判定である。
  成果物への影響: 記述と実装の差ではなく、記述済みの危険な入力がそのまま certified 候補になる。

- **refuted 候補 — 2 window 間の calibration 差替えは塞がっている。** 両 window は同じ spec hash と plan hash を header に持ち、finalize は全 header を現在の spec から再導出して exact 比較する。[floor_pair_driver.py:2241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:2241) [floor_pair_driver.py:2676](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:2676) calibration ref を変えれば spec bytes/hash が変わるため、一つの summary へ混載できない。
  成果物への影響: この経路では異なる calibration の campaign が一つの floor 値へ合成されることはない。

## fail-open 経路

- **refuted 候補 — binder に例外の飲み込みはない。** binary 検査と calibration loader の広い `except Exception` は、いずれも `FloorPairBindingError` として再送出する。[floor_pair_driver.py:1135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1135) [floor_pair_driver.py:1153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1153)
  成果物への影響: verifier の部分失敗が黙って success へ変換される経路は確認できない。

- **real 候補 — 拒否二行を説明二行へ置換する文面は D1374 型の過大表示になる。** 提案コメントは全 `saturation.records` を working-set/L3 下限と説明するが、driver は `lower_bound_selected` を要求せず、calibration は `saturated=true` の miss-rate 選択も許す。[s2b-plan.md:201](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:201) [floor_pair_driver.py:1173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1173) つまり実検査を落とした位置へ、その検査を不要にする保証が存在するかのような説明を置く。
  成果物への影響: review と台帳が workload 独立性を検査済みと誤認し、不一致 calibration の authority artifact を正当化する。

- **refuted 候補 — runtime の fatal と標本失敗は sticky。** fatal 後は全後続 session が `not_run_after_fail_closed` となり、標本内の droppable failure も後続 side に伝播し、finalize が因果を再検査する。[floor_pair_driver.py:2275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:2275) [floor_pair_driver.py:2609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:2609)
  成果物への影響: 部分失敗だけを除いて小さい floor を生成する新経路は本変更からは生じない。

## 既裁定との不整合

- **real 候補 — D15 を直接緩める。** D15 は代表 workload で calibration をキーし、「単一 calibration」を虚偽として却下している。[docs/decisions.md:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:222) [docs/decisions.md:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:241)
  成果物への影響: 既裁定が拒否した受理集合を floor producer だけで復活させる。

- **real 候補 — D1641 と §5.1 の校正済み `PerfConfig` 条件を緩める。** D1641 は calibrator の出力を採るとし、事前登録は workload がその driver の校正済み `PerfConfig` の workload 集合に属することを要求する。[docs/decisions.md:50335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:50335) [preregistration.md:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/phase3-b4-reflux-ablation-preregistration.md:374)
  成果物への影響: rr5・rr95 cell の workload 値が calibrator 出力でないのに校正済み集合として扱われる。

- **real 候補 — §5 の単数欄から「一 calibration でよい」は導けない。** 同欄は path/hash を置く一セルであるだけで、semantic cardinality を一件に固定していない。解除条件は「calibrator が決めた値へ差し替えるまで記入しない」であり、§11.2 は PerfConfig 全項目と workload 集合を先に一意化するよう求める。[preregistration.md:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/phase3-b4-reflux-ablation-preregistration.md:163) [preregistration.md:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/phase3-b4-reflux-ablation-preregistration.md:238) [preregistration.md:1098](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/phase3-b4-reflux-ablation-preregistration.md:1098)
  成果物への影響: 文書レイアウトを根拠に、未成立の workload 校正を成立済みとして扱う。

- **real 候補 — D1060 の向きと逆。** plan は「既存 accepted calibration 一件で今日から作れる」を選択理由にしているが、D1060 は既存値や `default_perf()` を根拠に欄を開けないと定める。[s2b-plan.md:219](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:219) [docs/decisions.md:36505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:36505)
  成果物への影響: B-4 用として承認されていない既存 rr50 値が、到達可能性を理由に権威参照へ昇格する。

- **real 候補 — D1696 は workload gate の削除を認可していない。** 人手責任へ残した九項目には extime、reps、max_ope 等が列挙される一方、既に機械照合されていた workload は含まれない。[docs/decisions.md:51702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:51702)
  成果物への影響: 「validator を拡張しない」という裁定を「既存 validator を弱めてよい」へ反転する。

- **real 候補 — D1759 の producer 版境界を潜脱する。** plan は SPEC だけ v4へ上げ、issuer が pin する summary producer は v3のままにするが、同じ summary/v3 の受理 domain は v3-spec から v4-specへ入れ替わる。[s2b-plan.md:241](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:241) [issuer.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:39) D1759 は意味の変わる producer を同一版で受理しないための裁定である。[docs/decisions.md:53418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:53418)
  成果物への影響: 同じ `floor-pair-summary/v3` がコード世代により異なる calibration 意味を持ち、台帳の版参照だけでは受理意味を識別できない。

- **refuted 候補 — D1377 と floor §5.1 の直接緩和はない。** caller 指定 floor は依然なく、既存 3%・within-run CV を final floor へ流用する変更でもない。[docs/decisions.md:43885](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:43885) [preregistration.md:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/phase3-b4-reflux-ablation-preregistration.md:228)
  成果物への影響: この二点の既存 fail-closed 性は維持されるが、PerfConfig 側の別の緩和を救済しない。

- **refuted 候補 — D1530 単独では直接衝突しない。** driver と issuer consumer は既に接続されている。ただし上記 D1759 に従い producer 版変更が必要なら、その issuer pin も同一変更単位に含めなければ D1530 型の空回りになる。[docs/decisions.md:47512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:47512)
  成果物への影響: 現 plan のままでは summary 版の意味不整合が production resolver まで伝播する。

## 規律 2 の境界

**real 候補 — 禁止署名:** `Accept(C,c) = accepted(C) and env/threads/clocks/records一致` として `C.workload == c.workload` を消す変更は、到達可能性のために D15 の正しさ gate を弱める規律 2 違反である。[CLAUDE.md:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/CLAUDE.md:53) 成果物への影響: 未校正 cell が certified floor の最大値計算へ入る。
**refuted 候補、通る正例:** balanced rr50 calibration と、env・threads・clocks・records・workload が exact 一致する balanced cell は現行 gate のまま受理でき、正しさ gate の緩和を伴わない。成果物への影響: calibration が実測した範囲だけが受理集合と権威参照に残る。

## 親の実測値の検証

- **real 候補 — b10 は実際に workload を束縛していない。ただし provenance の key 欠落だけでは証明にならない。** 実 admission は `load_calibration` で env、threads、clocks、selection、cache warning を検査するだけで、`perf_for` が別途各 prereg workload を差し込む。[b10_backoff_shape_sweep.py:1820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/b10_backoff_shape_sweep.py:1820) [b10_backoff_shape_sweep.py:1964](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/b10_backoff_shape_sweep.py:1964) report 経路も三系列の calibration object が同一であることを要求する。[b10_backoff_shape_sweep.py:3512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/b10_backoff_shape_sweep.py:3512) ただし当該 provenance 自身が `official_certification=false` であり、D15 と異なる実装先例は B-4 の正当性根拠にならない。[b10 provenance:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json:2)
  成果物への影響: b10 は「同様のコードが存在した」証拠にはなるが、B-4 の certified 受理集合を広げる権威にはならない。

- **real 候補、表現修正要 — registered calibration は二件で、両方 rr50/t48。** 二つの registered JSON はともに accepted、threads 48、rratio 50 である。[753 artifact:1599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1599) [94a artifact:1599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1599) ただし tracked file 全体では同 bytes の accepted attempt copy も二件あるため、「accepted file が二件」ではなく「registered/unique calibration が二件」が正確である。
  成果物への影響: rr5・rr95 の校正根拠がないという結論は変わらない。

- **real 候補 — resolver 配線と sentinel 挙動は親の主張どおり。** material report は resolver を呼び、resolver は逐語 `未記入` だけを `None` とし、それ以外は文法・path・hash・artifact schema を fail-closed で検査する。[material_report.py:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_material_report.py:211) [issuer.py:1216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:1216) `None` は分析側で `floor_domain_error` になる。[analysis_contract.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_analysis_contract.py:323)
  成果物への影響: malformed pin が材料レポートへ floor 値として流れる経路はなく、未記入時の evidence-only 状態も維持される。

## 総括

**(γ) は reject すべきであり、段 5 へ渡せる plan ではない。** 最大の反証は D15 自身が「飽和点は workload 依存」「代表 workload でキーする」「単一 calibration は虚偽」と既裁定している点で、plan の中心論拠と正面衝突する。

(γ') は (γ) より狭く b10 形を表現できるため、「今日到達できること」だけを目的とするなら不必要な拡大を減らす。しかし rr5・rr95 cell 自体の calibration を証明しないため、規律 2 と規律 4を満たす最終解にはならない。静的検査のみで、pytest・測定・編集・commit は実施していない。