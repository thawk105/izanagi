# T-1934 段4裁定・plan v2

## 所見裁定

| 出所 | 所見 | real/refuted | 採否・scope |
|---|---|---|---|
| plan/A/B | `worker_occupancy` は連続worker所要でなく観測済み report duration の和で、残差へidleとcritical-worker不一致が混入 | real | 採用、診断の中心 |
| A | 残差は4成分の非負加算でない。最後のworkerをjとすると `R=a_j+g_j+F-(M-q_j)` | real | 採用、4成分分解不能を確定 |
| A | finalization全体が1秒未満 | realな反証 | 親P2を撤回。短いのはJUnit cutoff後tailだけで、内部Fは0〜残差の粗い界 |
| A | prewarm差は最大約10秒 | realな反証 | 親P2を撤回。real-repo成分と完全共線、因果値・上下界でない |
| A | login collectionはcritical path外 | realな反証 | 「terminal joinを支配しなかった可能性が高い」へ弱める。競合寄与は非同定 |
| A | 約49秒は共通bundle | realな反証 | 「prewarm無し2 shardで49秒前後の類似した混合残差」へ弱める |
| A | 指定資料だけではpytest/xdistのexact hook順が未確定 | refuted in part | 親が実環境のpytest 9.1.1/xdist 3.8.0 sourceを照合し、JUnit sessionstart後にDSession trylastがworkerを起動することを確認。ただしphase timestamp欠如は不変 |
| A | 6桁残差は過剰精度 | real | 以後ミリ秒までに丸める |
| B | 対象量は厳密にはpytest process wallでなくJUnit session残差 | real | 採用、名称を是正 |
| B | duration完全性はselected==finishedだけでは証明されない | real | 観測済み有効duration和と記録し、欠落不存在は主張しない |
| B | merge単体はserialも受理する | real・scope外 | production runnerのloadgroup必須とD838束縛を維持。修理はしない |
| B | 差分ゼロでも段7記録・最終受入・段8・段9は必須 | real | 採用。plan v1の終了手順を破棄 |

## 実装裁定

- 最大成分は一意に識別できない。collection、worker起動、prewarm、内部finalizationのどれも同じartifactに整合する反例がある。
- 現行mainで特定成分の反復再現がなく、単一所有pathも決まらない。
- よってユーザー条件「最大成分が再現可能で、局所的な修理が明確」を満たさない。段5・6を飛ばし、実装面の差分ゼロで `4→7→8→9` とする。
- 実装面が無いのでD95 author、変異事前登録、変異matrix、paired修理再測定は発火しない。

禁止は署名して固定する。skip、deselect、selection縮小、timeout緩和、独立collection/report/JUnit/loadgroup/freeze/oracle gateの省略を修理として受理しない。通る正例は、現行runnerの全受入で全shardがloadgroup、selected==finished、shard和==独立collectionを満たす走行である。

## 既存artifactで言える上限

- K=3のJUnit session残差は59.223/49.039/49.557秒。K=2は73.535/54.726秒。
- prewarmは両走ともshard-0だけで発火し、なしshardにも49〜55秒の混合残差が残る。ただし差はprewarm効果でない。
- JUnit cutoff後のrunner tailは約0.32秒、scheduler accounting endとの差は秒粒度で約0〜0.5秒。内部finalization全体は非同定。
- login独立collectionはK=3現物で7.98秒、最初のcompute JUnit session開始前にartifact化した。join支配は観測されないが競合寄与ゼロとは言わない。
- 旧tipの48-worker/full-collection/0-test 12.86秒は歴史的観測で、現行collection/launch/finalizationの界には使わない。

## plan v2

1. 実装面は変更しない。T-1933、別成分、恒久計装、新監視基盤へ進まない。
2. 親が既存5 shardのfield、件数、scheduler、selected/finished、consumer配置を再照合し、診断insightへ非識別モデルと撤回を記録する。
3. 実repo読取を含む必要検査と最終受入全走を `tools/run_tests.py` / acceptance lease経路だけで行う。paired性能比較は修理が無いため行わない。
4. worklog spool fragment、scope外handoff、検査結果を記録し、parent docs commitを作る。
5. 段8を一度だけ実行し、候補を既存正本と重複照合する。段9は共通landだけを使う。

## 成果物影響

誤って最大成分を選ぶと、correctness gateを弱めるか効果の無い修理をlandし、以後の全waveの受入根拠と所要を悪化させる。実装しない裁定はcertified選択、材料report、proof bytes、受理集合を変えず、診断の限界だけをdurableに残す。
