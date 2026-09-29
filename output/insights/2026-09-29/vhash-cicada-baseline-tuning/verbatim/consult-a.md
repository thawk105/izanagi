## 所見

- **F1｜must-fix｜brief P5・P7、plan 5・6・事前登録案。** GC=10 µs で選んだ上位3点だけを GC sweep に進めるため、残る21点が別の GC 間隔で最速になる可能性を検査できない。根拠: `s1-brief.md:26-28`、`plan.md:35,39,68-70`、`request-md_11.txt:16-17`。**放置すると:**「24点と GC の組の最良設定」「最良から一定幅内の全設定」という成果物が、未測定の組を含む全空間の結論に見える。**推奨:** 現予算では「GC=10 で選抜した候補内の観測最良」と明記する。全空間の最良を名乗るには残りの genome×GC も測る設計と予算が要る。

- **F2｜must-fix｜brief P8、plan 3・未解決論点。** `#ShowOptParameters()` は macro の印字であり、全 define の実効性の証明ではない。PROMOTION は OPT が0でも印字される一方、その作用点は `#if INLINE_VERSION_OPT` の内側にある。待機時間 `_US` は印字されず、TRACE も同じ行にない。根拠: `external/ccbench/cc/cicada/util.cc:326-336`、`external/ccbench/cc/cicada/transaction.cc:128-135,923-927`、`external/ccbench/cc/cicada/include/transaction.hh:199-215`、`plan.md:31,76`。**放置すると:** genome や待機条件の binding を過大に主張し、別条件の性能値を最良設定へ混ぜる。**推奨:** 印字照合は「表示された macro 値の照合」と呼ぶ。fresh build の cache に加え、対象 target の実際の compile command で `TRACE=0`、`ADD_ANALYSIS=0`、各 genome define、待機型の `_US=1000` を照合し、未照合ならその条件を無効にする。PROMOTION の実効分岐は OPT との組で説明する。

- **F3｜must-fix｜brief P5・P7、plan 5・6。** J1 の選抜と J2 の確認は分かれたが、J2 の候補は条件別 job に割られ、各候補が独立した時刻・node で再現される設計は固定されていない。3 rep は同一 session 内の反復であり、24点からの選択バイアスも解消しない。根拠: `plan.md:35,39,55-59`、`ruling-D19.md:3-9`。**放置すると:** 偶然高かった候補を「確認済みの最良」とする。**推奨:** J1 を探索、J2 を選抜済み候補の確認と明記し、J2 では候補と対応 control を独立 job・投入時刻に反復配置する。予算上できなければ「探索で得た観測最良」に留め、確認済みとは書かない。

- **F4｜should｜brief P6・P7、plan 6。** job 間の control CV は単一構成の比率尺度であり、二候補の正規化 throughput 差の分布ではない。`score_best×(1−cv_w)` は記述的な幅として事前固定できるが、「同等」「floor 以内」「差がない」の根拠にはならない。根拠: `ruling-D145.md:5-17`、`ruling-D1639.md:8-17`、`plan.md:39,70,77`。**放置すると:** 同等集合と採否の意味が変わる。**推奨:** 表示名を一貫して「観測した control CV 幅内の候補集合」とし、24点すべてが入れば全点を列挙する。control が最大なら control を best と報告する。いずれも優劣や統計的同等性の証明としない。

- **F5｜should｜brief P1・P6、plan 1・6・7。** 診断目的で Cicada を測る根拠はあるが、D1373 の trace hook 関門を通っていない値を between-run floor として生成・登録・流用する根拠はない。複数投入束でも時間窓や node の共通要因を含みうる。根拠: `ruling-D1373.md:3-11`、`ruling-D145.md:5-24`、`ruling-D2083.md:4`、`plan.md:7,39,41`。**放置すると:** 一次資料の「ばらつき」が公式 floor や compare 閾値として読まれ、未達の floor 取得義務が閉じたように見える。**推奨:** 現在の専用 insight と診断 JSON に置き、`between_run_noise_*`、calibration の公式 floor、`compare.noise_cv`、採否には接続しない。値には control の構成、job 数、投入時刻 cluster 数、host 数を付ける。関門を理由に**診断測定自体を止める必要はない**が、`request-md_11.txt:16,21` が求めた floor は未取得と明記する。

- **F6｜should｜brief P2・P3、plan 2・3。** worker 1 の 1 ms 待機は `commit()` 冒頭にある人工的な撹乱条件で、`genome.py` も最適化軸から除外している。48 worker 全体の「読み取り後に待つ tx」一般を表すわけではない。根拠: `external/ccbench/cc/cicada/transaction.cc:919-942`、`orchestrator/campaign/genome.py:172-197`、`plan.md:25`。**放置すると:** 長い tx での最良設定を一般的な長時間 read phase の結果として主張する。**推奨:** この型を「worker 1 の commit 前に固定待機を入れた診断 workload」と定義し、通常3種や100操作型と別に報告する。最適化 genome の軸には入れず、待機 define の実効 binding を F2 の方法で確認する。

- **F7｜should｜brief P4・P5、plan 4・見積り。** 較正 run は perf 付きになりうるのに、性能比較用 throughput への非流用が明文化されていない。また J0 自体が最大111 run・2 build の大きな job で、仮の20分上限を支える単価はまだ無い。根拠: `.claude/agents/calibrator.md:15-24`、`plan.md:29,33,51-59`、`request-common.txt:22-27`。**放置すると:** 計器入りの値が最良設定の順位に流入するか、2 node 時間制約を満たせない計画を投入する。**推奨:** perf 付き run の throughput は較正記録専用とする。比較順位・図は perf 無し、TRACE=0、ADD_ANALYSIS=0 の走だけから再計算する。J0 の短い単価確認から残りの上限を再見積もりし、120 node 分以上なら後続を投入しない。

- **F8｜should｜brief P5・P6、plan 3・5・6。** genome 群が job に固定割付けされるため、genome と node・投入時刻が交絡する。同時刻 control 比は job ごとの共通ドリフトを減らせるが、候補固有の node との相互作用は除けない。build、DB load、直前 run の熱状態も順序依存になる。根拠: `plan.md:29,35,39`、`ruling-D145.md:5-8`、`.claude/agents/calibrator.md:29-33`。**放置すると:** job 固有の好条件が最良 genome または小さいばらつきとして現れる。**推奨:** rep 間で候補順を回し、control を各 job の始めだけでなく測定列に挟む。load・静定時間と run 順を記録する。上位候補は J2 で node と時刻をまたいで再配置する。workload ごとに N が違う結果を workload 間の throughput 優劣として比較しない。

- **F9｜should｜brief P4、plan 4・事前登録案。** perf 無しの場合の RSS 下限は飽和を示さず、perf 有効でも8M までの有限系列から「以後も変化しない」とは示せない。根拠: `orchestrator/calibrator/analyze.py:27-46,78-104`、`plan.md:33,67`。**放置すると:** 選んだ N が cache miss 飽和点として一次資料に断定される。**推奨:** 「観測範囲内の飽和候補」または「RSS 下限による選択」を分け、各 N の miss 率・RSS・採用理由を載せる。perf 不可なら飽和未判定と書く。

- **F10｜must-fix｜brief P1・成果物、plan 総括。** 最良設定の正しさ検査はこの計画に無い。さらに現行 trace patch では `INLINE_VERSION_OPT=1` かつ `PROMOTION=1` の組を検査できないという既知の障害がある。根拠: `s1-brief.md:16`、`request-common.txt:30-33`、`plan.md:17,82`。**放置すると:** 未検証の診断値が論文の主 baseline の確定性能や serializability の裏付けとして使われる。**推奨:** 一次資料と図の各結論に「正しさ未検証の診断値」を付け、headline・採否に使わない。後続で選抜された各設定を別の trace build と検査器に通し、compile 不能な組は修復と再検査まで未検証とする。

## brief / plan で正しいと確認した点

- 24点の正準空間と OPT=0・PROMOTION=1 の data path 上の冗長性は、`orchestrator/campaign/genome.py:91-103,172-205` と作用点の `#if` に整合する。
- batch flag で YCSB に長短 tx を混ぜない判断は妥当。ただし `batch_th_num` は総 thread 数を変えるので「完全に dead」という brief P2 の表現は強すぎる。根拠: `external/ccbench/cc/cicada/util.cc:18-21`、`external/ccbench/include/ycsb.hh:55-75`。
- plan は mocc 専用 policy helper の直接流用、perf 不在時の `find_saturation`、floor の名称について brief の弱点を修正している。根拠: `plan.md:10-14,23,33,39`。
- plot を計測機外で作り、生出力と再生成器を残す方針は妥当。根拠: `s1-brief.md:30`、`plan.md:41-45`。

## 総括

この設計で得られるのは、予算内で測った Cicada 候補の**正しさ未検証の診断的な順位と曲線**である。実装前に、全 genome×GC の最良とは呼ばない範囲、J2 の独立確認、define の実効 binding、perf 付き値の隔離を固定すべきである。Cicada の公式 between-run floor と、論文の主比較に使える検証済み baseline は、この wave の成果とは別に未達として残す。