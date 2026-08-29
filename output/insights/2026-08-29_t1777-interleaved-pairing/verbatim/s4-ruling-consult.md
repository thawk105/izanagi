## 1. Q1 への推奨

推奨は **(b) の改良版**です。

> 1 workload を一つの exact-two-arm campaign とし、両 arm の build / verify を先に完了する。その後、一つの `bench_lock()` を保持したまま、5 rep ごとの arm block を AB / BA で局所均衡させる。

物理順序は、10 pair ごとに `A⁵B⁵ / B⁵A⁵` を一組とし、その組内の先後だけを凍結 seed で決めます。contrast は物理順によらず常に `static10 - adaptive` とします。親が提案した「5-rep ごとに fresh campaign を作る」実装は採りません。

1. 同番号間の時間隔

現行 balanced は `205 × 3.36 = 688.8秒` に、arm B の build / verify が加わります。5-rep block なら build / verify は測定前に済ませるので、同番号間はおおむね `5 × 3.36 = 16.8秒` と呼出し境界の処理時間です。約41分の1です。

write-heavy は約242秒から約17秒、read-heavy は約94秒から約17秒です。3.36秒は `stage3-lensB.md:15-25` の既測値に基づきます。

2. 新しい交絡

最重要の新交絡は、先行 arm の cache、熱、周波数状態が後続 arm に残る carryover です。AB / BA の局所均衡は単純な順序効果と線形 drift を相殺しますが、方向非対称な carryover までは除去しません。

それでも rep 単位 ABBA や無作為配置より5倍長い同一 arm run を持つため、cross-arm 遷移は約5分の1です。固定 ABBA の周期4との交絡も避けられます。代わりに block 内位置との交互作用が生じるため、pilot では `block_position=0..4` を必ず記録します。

この配置が測るのは「5-rep counterbalanced schedule 下の差」です。carryover の無い定常状態の直接効果とは同一視しません。

3. 実装面

選んだ実装では closure 4 member がすべて必要です。

- [`ident.py:36-54`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-interleaved-pairing/orchestrator/campaign/ident.py:36): 新しい `(study_id, pairing_design)` profile を閉じた集合に追加。
- [`wal.py:102-125`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-interleaved-pairing/orchestrator/campaign/wal.py:102): 同じ profile を独立に許可。
- [`loop.py:327-383`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-interleaved-pairing/orchestrator/campaign/loop.py:327): 現在は一 arm の `evaluate()` を完了してから次へ進むので、二 arm を先に prepare する coordinator が必要。
- [`pipeline.py:512-621`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-interleaved-pairing/orchestrator/campaign/pipeline.py:512): 現在は一 arm の全 reps を一つの lock 内で測る。両 arm 全 block を一つの lock 内で実行する block runner が必要です。build / verify / bench が一体なのも `pipeline.py:1027-1086,1288-1347,1502-1561` で分割が必要です。

さらに非 closure の driver は、profile、schedule、collector、submit selector を追加します。現在の入口は [`paper_story_a1_paired.py:3517-3626`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-interleaved-pairing/orchestrator/campaign/paper_story_a1_paired.py:3517)、study literal は同 `:76-159,1025-1046,1080-1118,3440-3444`、job 側は [`paper_story_a1_paired.sh:13-42`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-interleaved-pairing/tools/pegasus/paper_story_a1_paired.sh:13) です。

pair ごとの fsync journal は置きません。全 block 完了後に両 arm の `bench_done` と schedule receipt を出し、途中 crash や片側 commit は invalid に閉じます。これで journal I/O 自体の観測者効果を避けます。

4. 実行費用

旧 n をそのまま比較に使うと、block 数は `ceil(72/5)+ceil(205/5)+ceil(28/5)=62`、`measure_point` は124回です。現行6回から118回増えますが、ccbench rep 数と nominal workload time `610 × 3.36 = 2049.6秒` は同じです。

選んだ単一 campaign coordinator なら verify は現行同様に2回/workload、合計6回です。build API も trace/perf × 2 arm × 3 workload の12回です。build identity に campaign ID や perf reps は入りません（`buildcache.py:1287-1316`）。

一方、親の fresh-campaign block 実装では62 campaign × 2 arm = 124 verify、build API は248回になります。compile は大半が cache hit でも、cache 検証、preflight、settle、campaign 境界が新しい費用と交絡になります。

落とした候補:

- (a) 現行維持: 長時間 drift と adaptive-first が完全交絡したままです。
- (c) rep 単位 ABBA: 間隔は最短ですが、cross-arm carryover と周期4の環境変動を新たに強く取り込みます。
- (d) 均衡無作為: seed 固定は再現性だけを与え、実現した時間偏りや長い run を除きません。rep 単位なら carryover と呼出し費用もABBA並みです。
- fresh-campaign 版 (b): 配置の統計的狙いはよいものの、campaign 境界、settle、build / verify、lock 解放を62回持ち込みます。

## 2. Q2 への推奨

**pilot は挟みます。ただし pilot 用の簡易実装は作らず、本番用 mechanism を先に一度だけ完成させ、その同じ mechanism で pilot を走らせます。**

実装面の重なりはほぼ全部です。

- closure は4/4ファイル共通: `ident.py:36-54`、`wal.py:102-125`、`loop.py:327-383,465-474`、`pipeline.py:512-704,1027-1086,1502-1561`
- driver の実行核も共通: `paper_story_a1_paired.py:766-843,3517-3626`
- submit / job 経路も共通: 同 `:1025-1118,4530-4568`、job `:13-42,765-775`
- pilot と最終 study で異なるのは、study ID、policy / preregistration hash、reps、`k`、sigma、出力先などの profile 値です（driver `:76-159,661-758`）。

したがって behavioral implementation の重なりは実質100%、closure member の重なりも100%です。pilot の価値はコード試作ではなく、新配置の共分散、block 相関、carryover を実測して n を決めることです。これは Q3 に不可欠なので、重なりが大きくても省けません。

fresh-campaign の簡易 pilot は、build / verify と lock 解放が対の間へ入るため、本番 coordinator と異なる共分散を測ります。これを sizing pilot に使ってはいけません。

旧 v2 は変更せず別 study とする必要があります（`D1027.md:3-9`）。pilot profile も consumer と同時に作り、休眠 capability にしません（`D1028.md:1-7`）。

## 3. Q3 への推奨

### pilot

各 workload について、同じ新 mechanism で **60 pair** を一度測ります。

- 5 pair/block、12 block
- A-first 6 block、B-first 6 block
- 10 pair ごとに一方ずつを含め、組内順だけを凍結 seed で決定
- 120 arm reps/workload、全体で180 pair、360 arm reps
- `bench_max_rounds=1`、性能結果を理由にした再測定なし
- TPS、物理順、block index、block 内位置、開始・終了時刻を記録

### sigma の計算

各 pair について、

`d_i = static10_i - adaptive_i`

` s_pair = sqrt(sum((d_i - mean(d))^2) / 59)`

とします。v2 と同じ一側95%上限を使うなら、

`planned_sigma_tps = s_pair × sqrt(59 / chi2_0.05,59)`

です。`chi2_0.05,59 ≈ 42.34` なので係数は約1.181です。

現行 v2 が同じ方式であることは算術でも確認できます。n=5 の係数は

`sqrt(4 / chi2_0.05,4) = 2.372356`

であり、

- `43,649.1 × 2.372356 ≈ 103,551.1`
- `66,139.4 × 2.372356 ≈ 156,906.2`
- `25,453.5 × 2.372356 ≈ 60,384.7`

となり、`frozen_policy_v2.json:139,151,163` と一致します。

block 内相関も n の計画へ入れます。12個の5-pair block 平均の標本 SD を `s_block` とすると、

`effective_sigma_95 = sqrt(5) × s_block × sqrt(11 / chi2_0.05,11)`

です。係数の後半は約1.551です。最終 n の探索には、

`sigma_for_sizing = max(planned_sigma_tps, effective_sigma_95)`

を使います。policy では pair SD 用と平均分散用を別 field にして意味を混ぜません。

### n の選択

候補を `n = 30, 40, ..., 500` に限定します。10の倍数にするのは5-rep block の AB / BA を exact に均衡させるためです。

各 n について、

- `df=n-1`
- `k=t_0.975,n-1`
- `h=k × sample_sd / sqrt(n)`
- `B=0.03 × current-run adaptive mean`

をそのまま計算します。これは現実装 `paper_story_a1_paired.py:1769-1798` と同じ式です。

pilot の5-vector block を order 別に再標本化し、次の3条件を固定 seed で100,000回探索します。

- 真の差0: `abs(mean)+h <= B`
- 真の差 `+0.06 × adaptive mean`: `abs(mean)-h > B` かつ符号が正
- 真の差 `-0.06 × adaptive mean`: 同じく above-floor かつ符号が負

0、±6%は3% floor の0倍と2倍で、現行 headline sizing code でも同じ3条件と成功確率80%を採っています（`tools/size_paper_story_a1_headline.py:60-69`）。

3条件すべての成功率が80%以上となる最小 n を候補にし、独立 seed の1,000,000 trial で再計算します。9個の workload × condition セルについて、一側 Clopper-Pearson 下限を familywise 5%で補正し、全下限が80%以上なら n を凍結します。通らなければ10ずつ増やし、500でも通らなければ final study を発行しません。

pilot の観測値は final の推定へ混ぜません。

## 4. 親の判定への反論

1. 「現行の対応づけは分散を減らしていない」

**強い結論には不同意、観測記述には同意**です。

n=5 の観測標本では、3 workload とも対応差 SD が独立近似より25から33%大きい、という記述は正しいです。しかし母相関については言えません。Fisher-z の概算95%区間と無相関検定は次のとおりです。

| workload | r | 概算95%区間 | 両側 p |
|---|---:|---:|---:|
| write-heavy | -0.591 | [-0.968, 0.609] | 0.294 |
| balanced | -0.563 | [-0.966, 0.634] | 0.323 |
| read-heavy | -0.765 | [-0.983, 0.361] | 0.132 |

したがって言える上限は「この15対では分散削減を観測せず、有益な正の共分散を示す証拠もない」です。「真に分散を増やす」「原因は時間隔である」は言えません。

また「真の相関0なら3符号一致は1/8」は、3 workload の符号推定が独立という追加仮定を要します。同一 job が workload を順に処理する現行経路（driver `:3562-3565`）では、その独立性は示されていません。

2. 「本 wave では実装しない」

**不同意**です。consult 段なので今ここで書込みはしませんが、設計は次の順で前進させるべきです。

1. 上記5-rep counterbalanced block と schedule-specific estimand を決定する。
2. coordinator、collector、profile consumer、失敗時 invalid 化を同じ実装単位で作る。
3. pilot profile を別 study として発行し、60 pair/workload を測る。
4. sigma と n を独立 simulation で認証する。
5. final policy / preregistration を別 study ID で凍結する。
6. final profile の値だけを追加し、検査後に投入する。

3. 「必ず要るのは ident と wal」

**狭い意味では同意、一般化には不同意**です。

新 study/design は D1027 により旧 literal を流用できません。`ident.py:36-54` と `wal.py:102-125` は同じ旧 `(study_id, design)` を別々に固定しているため、両方の更新が必須です。ident だけ変えると `loop.py:334-335` から入った WAL context が拒否します。

ただし「loop / pipeline が要るのは rep 単位完全交互だけ」は誤りです。単一 campaign、両 arm 事前 verify、一つの lock という選定案で block 交互を行う場合も、現在の逐次 `evaluate()` と arm 単位 `_run_bench()` を分割するため両方が必要です。

逆に fresh campaign block なら loop / pipeline は不要ですが、現在の registry は campaign ID を exact unique triple に固定しています（`trial_registry.py:3889-3896`）。K campaign 案は非 closure の registry と collector まで変更が要り、単なる driver 変更ではありません。

## 5. 決めきれない点

- `measure_point` を6回から124回へ分割した実 wall 増分は未測定です。pilot で call ごとの wall と全体 wall を記録すれば決まります。
- 方向非対称 carryover のない直接 arm 効果は、この二 arm 配置だけでは識別できません。必要なら neutral washout を挟む診断、または複数 washout 長の比較が必要です。
- final の反復数は新配置の sigma と block 相関が無いため、現時点では決められません。上記60-pair pilot が決定情報です。
- 静的検査のみです。pytest、性能測定、投入は実行していません。

## 総括

- Q1: 単一 campaign、5-rep block、局所 AB / BA 均衡、一つの bench lock を推奨する。
- Q2: pilot は挟むが、簡易版を作らず本番 mechanism をそのまま使う。
- Q3: 60 pair/workload の pilot から pair SD と block 有効 SD を取り直し、認証 simulation で n を選ぶ。
- 親の fresh-campaign 実装は、verify、cache 検証、settle、lock 境界を不必要に増やすため採らない。
- n=5 は「今回の標本で悪化した」までで、母共分散や時間 drift の因果までは支持しない。
- ident と wal は必須だが、選定した単一 campaign 実装では loop と pipeline も必要である。
- final n 以外の配置択一は、これで決定できる。