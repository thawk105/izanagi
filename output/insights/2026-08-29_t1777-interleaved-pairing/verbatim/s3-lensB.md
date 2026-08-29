## 所見

1. [severity: must-fix] [観点: 1]  
[攻撃シナリオ] 時間差交絡が実際に効いたことを同定する観測は無い。既存探索走には弱い兆候があるが、固定順序の1走だけなので、時間ドリフト、偶然、arm固有挙動を分離できない。  
[根拠 file:line または算術] `result.json:9-14` 自身が「shared time blocksではない」と限定し、repごとの時刻、温度、周波数を持たない。raw TPSから再計算すると、位置差SDと独立近似SDは write-heavy 43,649対34,940、balanced 66,139対53,030、read-heavy 25,453対19,186で、arm間の位置相関は順に -0.591、-0.563、-0.765。この兆候は `README.md:108-110` にもあるが、逆順走が無いため原因を同定しない。`runner.py:1119-1158` もrep時刻や熱状態を記録しない。  
[提案] briefの「交絡が効いている」を「識別不能な交絡リスク」に下げる。新study前に、小規模な順序反転またはcounterbalanced pilotで符号と大きさを確認する。

2. [severity: must-fix] [観点: 1]  
[攻撃シナリオ] `adaptive → static10` の固定完全交互では、static10が常にpair内2番目になる。差にはarm効果だけでなく、直前armのキャッシュ残留、周波数、熱、pair内順序効果が常に同じ向きで入る。時間差を縮めても別の完全交絡へ置き換わる。  
[根拠 file:line または算術] 現policyのarm順は `frozen_policy_v2.json:2-5`、briefは単にrep単位交互を選ぶ `brief.md:78-80`。各repは後処理後すぐ次を起動する `runner.py:1077-1082,1119-1158`。plan自身もAB/BA択一を未決としている `stage2-plan.md:146-148`。  
[提案] 実装前に順序を凍結する。最小案はABBA、またはpairごとにAB/BAを103対102へ事前に均衡させた固定seedスケジュールである。contrastの符号は常に `static10-adaptive` とする。

3. [severity: should-fix] [観点: 2]  
[攻撃シナリオ] briefは完全交互だけを検討し、時間差を十分縮めつつ切替回数と新交絡を減らす中間案を捨てている。  
[根拠 file:line または算術] balanced、実測3.36秒/repを使う比較は次のとおり。

| 配置 | 同番号間隔 | `measure_point`回数 | 順序・残留効果 |
|---|---:|---:|---|
| arm一括 | 約689秒 | 2 | 長時間ドリフトとarm順が完全交絡 |
| 固定AB完全交互 | 約3.36秒 | 410 | Bが常に2番目 |
| 5-rep block、AB/BA均衡 | 約16.8秒 | 82 | 615秒比で約41分の1、順序を均衡可能 |
| rep単位ABBA | 約3.36秒 | 410 | 線形順序効果を相殺、同arm連続が残る |
| 均衡無作為AB/BA | 約3.36秒 | 410 | 順序を分散するがスケジュール凍結が必要 |

3.36秒/repは事前登録 `README.md:44-45`、完全交互案は `stage2-plan.md:24-25`。  
[提案] 最初の候補を「5-rep blockをAB/BA均衡配置」に変える。完全交互を選ぶなら、中間案より優れる観測根拠を先に示す。

4. [severity: must-fix] [観点: 1]  
[攻撃シナリオ] planのpair単位lockはpair間へ別campaignを挿入できる。挿入された負荷の熱・周波数残留が次pairへ入り、205個のpairで異なる履歴を持つ。  
[根拠 file:line または算術] planは挿入を明示的に許す `stage2-plan.md:78-82`。現行は1 armの全repsを一つのlockで囲む `pipeline.py:587-621`。  
[提案] paired bench全体、すなわち両armの全2N repsを一つの既存`bench_lock()`区間に置く。pairごとのlock再取得と競合probe追加は不要。

5. [severity: survived] [観点: 3]  
[攻撃シナリオ] 親の「2 verifyから410 verify」は過大ではないか。  
[根拠 file:line または算術] 各campaignはgenomeごとに一度`evaluate()`を呼ぶ `loop.py:383-474`。A-1は2 genome `paper_story_a1_paired.py:3591-3594`、default verifyはlegacy一pass、reps=1 `pipeline.py:128-135,847-850,1338-1347`。したがってfresh campaignを205本作れば `205 × 2 × 1 = 410`、現行は `1 × 2 = 2`。ただし同一identityを205回呼ぶと最初の2 variant以外はterminal skipされる `loop.py:354-381`。410は205個の別identityを作る条件付きで正しい。  
[提案] 回数は維持し、「205個のfresh identityが必要」という前提を明記する。

6. [severity: should-fix] [観点: 3]  
[攻撃シナリオ] verify回数だけを205倍として「総費用爆発」と呼ぶと、実測wall費用を誤認する。compileも205倍にはならない。  
[根拠 file:line または算術] balancedのthroughput費用は両案とも `410 × 3.36 = 1,377.6秒`。verifyは成功時のnominal extimeが1秒 `pipeline.py:128-135` なので、現行約2秒、対案約410秒。単純合計は約1,379.6秒対1,787.6秒、約29.6%増であり205倍ではない。v2 build identityはcampaign IDやperf repsを含まない `buildcache.py:1287-1316`。同一cache rootなら820 build API呼出し中、空cacheでもfresh compileは最大4件、残り816件は検証付きcache hit `buildcache.py:2438-2494`。  
[提案] 「verify実行数205倍」と「推定総wall約30%以上増」を分ける。campaign初期化、cache検証、preflight費用は未実測と明記する。

7. [severity: survived] [観点: 3]  
[攻撃シナリオ] verify証明書を一度作り、205 campaignへ再利用すれば410回を避けられないか。  
[根拠 file:line または算術] capabilityはPID、lock、variant、operation、workloadへ束縛される `verifier/core.py:168-215`。別operationを拒否し、一度消費すると再利用できない `verifier/core.py:224-258`; `commit_receipt.py:309-332`。  
[提案] 修正不要。証明書再利用を対案の成立条件に数えない。

8. [severity: must-fix] [観点: 4]  
[攻撃シナリオ] v3がv2の`planned_sigma_tps`、n、到達確率をコピーすると、別配置の分散設計を旧配置のpilotで正当化する。  
[根拠 file:line または算術] 計画sigmaはarm一括探索走の位置差SDから導出された `README.md:38-48`。配置変更は `Var(B-A)=Var(B)+Var(A)-2Cov(A,B)` の共分散項とcarryoverを変える。n=205などはそのsigmaを使ったMonte Carlo結果 `README.md:28-45`。planには新配置でsigmaを取り直す工程が無い。  
[提案] 新配置のpilotからsigmaとnを再設計するか、v3では旧到達確率、旧planned sigma、`variance_plan_breach`を引き継がない。どちらかを事前登録前に選ぶ。

9. [severity: survived] [観点: 4]  
[攻撃シナリオ] 交互配置にすると平均、標本SD、`h=k*SD/sqrt(n)`を数学的に使えなくなるか。  
[根拠 file:line または算術] 各事前登録blockについて `d_i=static10_i-adaptive_i` を一つ作る限り、平均と分母`n-1`の標本分散は配置に依存しない。現実装もその算術だけを行う `paper_story_a1_paired.py:1769-1827`。df=`n-1`とkはnを固定する限り同じ。policyも推論ではなくdescriptive-only `frozen_policy_v2.json:110-123`。  
[提案] 式は維持できる。ただし名称を「位置対応差」から「事前登録block内の符号付き対差」へ変える。planned sigmaの再利用は所見8のとおり不可。

10. [severity: must-fix] [観点: 5]  
[攻撃シナリオ] mechanismとselectorだけをlandしても、現存artifactから新分岐を発火できず、D1028の休眠capabilityになる。  
[根拠 file:line または算術] 現validatorはtracked v2との全field一致を要求する `paper_story_a1_paired.py:745-758`。CLIも現study ID以外を拒否する `paper_story_a1_paired.py:3440-3444`。non-certifying markerも旧studyと旧designに固定 `ident.py:40-54`。D1028は投入器だけの先行を明示的に却下する `D1028.md:1-11`。stage2 planはこの欠陥を正しく認識している `stage2-plan.md:54-58,146`。  
[提案] ユーザー発行のv3事前登録、v3 policy、study profile、driver consumer、機構を同じland単位にする。事前登録はユーザーの手番 `D1224-D1225.md:25-28` であり、順序とsigmaも未決なので、揃うまでは実装をlandしない。qsubは本waveに含めなくてよい。

11. [severity: should-fix] [観点: 6]  
[攻撃シナリオ] pair journal、pair attempt topology、専用recovery、pairごとのfsyncは、配置変更より大きな新状態機械と観測者効果を作る。journal I/O自体がpair間の時間と周波数状態を変える。  
[根拠 file:line または算術] 新台帳とcodecは `stage2-plan.md:29-31`、専用collectorは`:37`、専用recoveryは`:31`。pairごとならbalancedだけで205回の同期追記となる。費用未実測はplan自身が認める `stage2-plan.md:149-150`。既存consumerは両armのexact stage、TPS長、commitを既に拒否側へ検査する `paper_story_a1_paired.py:2150-2187,2257-2288,2374-2415`。既存recoveryもsignal後active attemptの継続を拒否する `wal.py:1847-1866`。  
[提案] pair journal、`pair_attempt_id`、専用成功recoveryを外す。一つのlock下で決定論的scheduleを同期実行し、arm別TPS列を既存`bench_done`へ一度ずつ出す。crashは既存どおりstudy invalidへ閉じる。

12. [severity: should-fix] [観点: 7]  
[攻撃シナリオ] briefの「実測した615秒」は実測値ではなく、extimeだけのnominal積である。同番号間隔としてはさらに短く見積もっている。  
[根拠 file:line または算術] `205 × 3 = 615秒`はpolicyの入力値 `frozen_policy_v2.json:143-153,80-89`。同じ事前登録は実測3.36秒/repを記録するため `205 × 3.36 = 688.8秒` `README.md:44-45`。さらに現行はarm Aのbench/commit後にarm Bのbuild、verifyを行ってからbenchへ入る `loop.py:383-474`, `pipeline.py:1027-1146,1178-1451,1502-1561`。同番号間隔は約689秒より長い。  
[提案] 「615秒のnominal下限、既存実測換算で約689秒、実際の対間隔はbuild/verify分だけさらに長い」と直す。

13. [severity: survived] [観点: 7]  
[攻撃シナリオ] enforcement closureがexact 24 pathというbriefの棚卸しは古くないか。  
[根拠 file:line または算術] `campaign_lock.py:49-74` の列挙要素は行50から73の24件で、`loop.py`と`pipeline.py`は行53-54に含まれる。`contract_loader_binding.py:57-60,80-94` もexact 24を検証する。  
[提案] 修正不要。

14. [severity: survived] [観点: 7]  
[攻撃シナリオ] D1139後も批准集合との照合が残り、T-1777の着手条件は未解消ではないか。  
[根拠 file:line または算術] 現行経路はcommit blob、digest、live bytesだけを検証する `contract_loader_binding.py:348-383`。批准集合との照合呼出しはこの経路に無い。`artifact_admission.py:66-69` もscopeをexact 24としている。D1139の廃止対象と残存検査は `D1139.md:3-9` に一致する。  
[提案] 修正不要。briefの「着手条件解消」は成立する。

15. [severity: survived] [観点: 7]  
[攻撃シナリオ] `pairing_design`を変えても同じcampaign IDへ混ざるのではないか。  
[根拠 file:line または算術] driverはdesignを`search_config`へ入れる `paper_story_a1_paired.py:801-822`。campaign identityは`search_config`全体を正準化してhashする `ident.py:169-208`。したがってdesign変更で別campaignになる。  
[提案] 新しい混在防止gateは追加しない。新study/profileのclosed marker更新だけを行う。

## 総括

- 最重must-fixは所見2: 固定AB完全交互は、時間差交絡を順序・残留効果の完全交絡へ置き換える。
- 時間交絡の識別証拠は無く、既存5点走には負の位置相関という弱い兆候だけがある。
- 5-rep blockのcounterbalanced配置は、間隔を約41分の1にしつつ切替と実装量を抑えられる。
- 410 verifyという回数は正しいが、総wall費用は単純推定で約30%以上増であり205倍ではない。
- v2のplanned sigmaと動作確率は新配置へ流用できない。
- mechanismだけのlandは休眠capabilityになるため、ユーザー発行v3事前登録と同じland単位が必要。
- pair journalと専用recoveryは過剰であり、単一lockと既存WALで足りる。
- 静的検査のみで、pytestや性能測定は実行していない。
- 交互配置は本当にやる価値があるか: **固定AB完全交互には無く、counterbalanced block配置ならpilotで効果を確認する価値がある。**