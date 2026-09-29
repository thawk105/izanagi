## 所見

- **B1｜must-fix｜brief (P4)(P5)、plan 事前登録・J2。** 較正で workload 別に選ぶ `N` は 1M を超え得る一方、後続の VHash / forwarding 比較条件は 48 thread・1M・skew 0.9・rr50・GC `{10,100,1000}`。plan はその共通動作点での Cicada 測定を確約していない。根拠: `plan.md:33-35,65-69`、`request-md_11.txt:15-18`、`docs/paper-story-vhash/2026-09-29.md:448-480,525-530`。**放置時:** 較正済みの最良値でも論文の構成 A に直接重ねられず、baseline の取り直しが要る。**推奨:** 較正で選んだ `N` の探索結果とは別に、共通の 1M・rr50・GC 3 点について選定候補と対照を同時期に測る条件を事前登録する。1M が較正基準を満たさなければ、その差を明記して論文側の条件も再検討する。

- **B2｜must-fix｜brief (P5)(P7)、plan J1/J2・「Best」。** 24 genome を比較するのは GC=10 だけで、他の GC 値へ進むのは上位 3 点だけである。GC=10 で 4 位以下の genome が GC=100 などで最速になる可能性を、この設計は排除できない。根拠: `plan.md:35,39,68-70`、`docs/paper-story-vhash/source-memo-2026-09-29.md:1397-1405,1541-1551`。**放置時:** 「最適化と GC を最良に調整した Cicada」という一次資料の主張が探索範囲を超え、弱い baseline を選び得る。**推奨:** 結果名をまず「GC=10 で選抜した候補中の最良」と限定する。論文用の最良を名乗るなら、少なくとも主要な rr50 の GC `{10,100,1000}` では全 24 点を評価するか、他の genome を除外できる事前規則と検証走を設ける。

- **B3｜must-fix｜brief (P5)、plan 見積り。** 20＋4×15＋4×9＝116 node 分は実測ではなく仮の walltime 上限である。J0 は最大 111 run、J1 は 420 run、J2 は最大 300 runで、名目 3 秒だけで 41.55 node 分を使う。さらに待機型は別 build なのに J1 は各 job「7 build」と計上しており、5 workload 全件を走らせる場合は最大 14 build 分が必要になる。DB は各プロセスで生成される。根拠: `plan.md:23,25,35,49-59`、`external/ccbench/cc/cicada/ycsb_cicada.cc:23-40`。**放置時:** 2 node 時間未満という投入条件を誤判定し、最良設定やばらつきの測定が途中で欠ける。**推奨:** J0 で通常型・100 操作型・待機型の build、DB load、実走を別々に測り、各 job の追加対照と依存準備も含めた上限を再計算する。超過時はまず待機型の全 genome 走と GC の極端な追加点を縮め、rr50 の比較可能な条件と各点の反復を優先する。削減後の対象範囲を結果を見る前に固定する。

- **B4｜should｜brief (P2)(P3)、plan 長い tx。** 100 操作型は全 worker の全 tx を長くし、待機型は worker 1 だけを `commit()` 冒頭で待たせる。両者は stock で実行可能な別条件だが、「長い tx」の代表性は未確認である。特に 1 ms 待機の実効性を表示 flag だけでは確認できない。根拠: `external/ccbench/include/ycsb.hh:55-75`、`external/ccbench/cc/cicada/transaction.cc:919-942`、`plan.md:25,76`、`docs/paper-story-vhash/source-memo-2026-09-29.md:1452-1466`。**放置時:** GC や throughput の差を長い tx の効果として解釈できず、一次資料の適用範囲が過大になる。**推奨:** J0 で待機あり／なしの対照を置き、完走、経過時間、throughput、maxrss の変化を確認する。効かなければこの型を外す。100 操作・rr95 と 1 ms は根拠のある探索値ではなく固定した試験条件として報告し、長さ一般への外挿を避ける。

- **B5｜should｜brief (P6)(P7)、plan ばらつき・集合。** plan は floor への配線を避けている点は正しい。ただし J0/J1/J2 の異なる投入時刻を混ぜた control CV を一つの `cv_w` にし、それを候補間の「観測 CV 幅内の集合」の境界に使う。control の変動と二候補の差は別の量であり、時間窓 cluster も少ない。根拠: `plan.md:12-13,39,70,77`、`ruling-D145.md:5-17`、`ruling-D1639.md:13-17`。**放置時:** 同等集合の構成員が任意の幅に左右され、「差がない候補」と誤読される。**推奨:** workload・`N`・build 条件ごとに job 数と投入時刻別 CV を示し、集合は探索用の記述的候補リストと明記する。論文用の同等性や採否には使わず、必要なら候補同士を独立セッションで直接比較する。

- **B6｜should｜brief (P4)、plan 較正。** perf 不在時に RSS 下限で選ぶ修正は必要だが、RSS は cache miss 飽和の証明ではない。また `run_sweep` の早期停止は観測済み末尾の平坦さで判断するので、それより大きい `N` でも平坦という証明にはならない。根拠: `orchestrator/calibrator/analyze.py:27-46,78-104`、`orchestrator/calibrator/sweep.py:91-131`、`plan.md:10,33,67`。**放置時:** 採用 `N` を「飽和最小点」と過大に記し、最良設定のスケール依存を隠す。**推奨:** perf 不在時は「D15 の RSS 下限採用」、早期停止時は「観測範囲内の飽和候補」と記す。8M までの全点が必須という扱いにはせず、採用理由と未観測範囲を残す。

- **B7｜must-fix｜brief (P8)、plan 実行時照合。** `#ShowOptParameters()` に出るのは `WORKER1_INSERT_DELAY_RPHASE` の有効／無効だけで、`WORKER1_INSERT_DELAY_RPHASE_US=1000` の値は出ない。plan の「delay macro 値を期待値と比較」はその出力から実行できないことを、plan 自身も未解決と記す。根拠: `external/ccbench/cc/cicada/util.cc:326-336`、`external/ccbench/cc/cicada/transaction.cc:923-925`、`plan.md:31,76`。**放置時:** 待機時間を誤った build が正しい条件として混入し、待機型の最良値と図が変わる。**推奨:** 表示行では有効 flag だけを照合し、1000 µs は configure 引数・CMakeCache・binary digest と J0 の待機あり／なし実走で束縛する。実行時表示で値を検証したとは書かない。

- **B8｜should｜brief (P8)(P9)、plan 実装・図。** plan が `_load_policy` と `_common_configure_args` の mocc 専用性を退けた判断は正しい。一方、残る `_resolve_toolchain`・`_prepare_dependencies` も別 wave の private helper であり、直接 import は変更に弱い。図 2 種、PNG/PDF/provenance と実寸 Figure 検査は図規約に沿うが、driver を汎用 framework にする理由にはならない。根拠: `orchestrator/campaign/s3_mocc_lock_coverage.py:120-167,224-271`、`plan.md:14,43-47`、`tools/plotting/FIGURE_CONVENTIONS.md:65-90,96-114`。**放置時:** helper の変更で測定開始が止まる一方、実装費が増えて肝心の実測が遅れる。**推奨:** private helper の利用を薄い一箇所に閉じ、現 pin の policy・configure 条件を固定して検査する。図は依頼された throughput と GC 曲線に絞り、既存の描画・layout 検査を再利用する。

- **B9｜should｜brief (P5)、plan 工程。** J0 後に費用を再計算する停止点はあるが、「待機型が成立しない」「perf が使えない」「1 run が長い」場合に J1/J2 のどの条件を残すかは決まっていない。根拠: `plan.md:33-35,59,71,73-78`、`request-common.txt:22-27`。**放置時:** J0 の結果を見てから都合よく条件を削り、最良設定や一次資料の主張が後付けになる。**推奨:** J0 判定表を先に固定する。待機型不成立ならその型のみ欠測として残す。perf 不在なら RSS 下限採用と明記する。予測・walltime 上限のいずれかが合計 120 分以上なら後続を投入せず、優先順位に沿った縮小案を提示する。

## brief / plan で正しいと確認した点

- stock source と既存 floor driver を変えず、trace・計器なしの性能値を「未検証の診断値」に留める境界は妥当。`s1-brief.md:13-18`、`plan.md:7,17`、`request-common.txt:26-33`。
- `CICADA_SPACE` の 24 正準点、promotion の冗長組を除く理由、batch flag を長短 tx 混合の根拠にしない判断は source と合う。`orchestrator/campaign/genome.py:91-103,172-205`、`external/ccbench/include/ycsb.hh:55-75`。
- GC 格子は後続比較の `{10,100,1000}` を含み、計測機外の作図、同時刻対照、J0 で単価を測る順序も妥当。`plan.md:35,43,51-59`、`request-md_11.txt:28-31`。
- Pegasus の既存較正 11 件と Cicada 0 件は、親が確認済みの棚卸し事実として扱える。plan の「本射影だけでは未確認」は慎重だが、一次資料には棚卸し範囲を添えればよい。`s1-brief.md:9-11`、`plan.md:19`。

## 総括

現 plan は有用な診断探索になるが、そのままでは **GC も含めた Cicada の最良設定**と、後続の 1M・rr50 条件に直接使える構成 A を確定できない。最優先は共通動作点の確保、GC=10 での候補選抜が持つ限界の解消、待機型の build 数を含む 2 node 時間の再見積りである。正しさ検査が整うまで、得た性能値を論文の確定的な主比較値にはしない。