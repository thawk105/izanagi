## 変更点一覧 (file:line)

行番号は現行ファイルの位置。patch の変更箇所は、patch 内の行番号と対応する Cicada 原典の行番号を併記する。

| ファイル | 計画する変更 |
|---|---|
| [instr-cicada-version-lifetime.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/patches/instr-cicada-version-lifetime.patch:4) | `transaction.hh` の統計・状態、`transaction.cc` の gflag・`begin()`・read・`mainte()`・commit・公開観測・JSON を拡張する。patch 対象は引き続きこの二つの file のみ。 |
| [vhash_cicada_vlife.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:40) | 条件表、argv、schema 2 の厳密 parse、集計を追加。既存 24 ID と schema 1 の読取りを残す。 |
| [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/condition_meaning_gate.py:527) | patch 確定後に実際の `#if` 数を再計数し、VLIFE の owner TU と companion header の pin を同時更新。 |
| [test_vhash_cicada_vlife.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/tests/test_vhash_cicada_vlife.py:25) | schema、条件直積、分解、inert witness の純関数テストを追加。 |
| [plot_vhash_readonly_share.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/tools/plotting/plot_vhash_readonly_share.py) | 新規。raw JSON から図４枚と各 PNG・PDF・provenance を生成。 |
| [patches/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/patches/README.md:845) | 計器の schema 2、条件制御、D-C の限界を記載。`patches/ledger.json` は D18 第４類専用で entry 数１の契約があるため変更しない。 |

## patch 設計

**種別制御。** `DEFINE_int32(izanagi_ronly_pct, -1, ...)` は owner TU の `transaction.cc`、既存 `#if IZANAGI_CICADA_VLIFE` 内に置く。`DEFINE_int32(izanagi_long_kind, 0, ...)` は同 TU の既存 `#if IZANAGI_CICADA_LONGTX` 内に置く。起動時または最初の `begin()` で前者を `-1,0…100`、後者を `0,1,2` に限定し、不正値は停止する。既存 `ronly_ratio` は [common.hh:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/external/ccbench/cc/cicada/include/common.hh:64) にあるが、YCSB の生成には使われていないため、別名の診断 flag とする。

`transaction.hh` の VLIFE member に `vlife_new_procedure_ = true` を追加する。`begin()` の初回だけ、**既存の batch 拡張と sort の後**に操作種別を確定し、この flag を false にする。成功した `commit()` の ro と update の両経路で true に戻し、`abort()` と失敗した commit では戻さない。[ycsb.hh:102–163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/external/ccbench/include/ycsb.hh:102) は手続き生成後に retry label へ入り、失敗時は同じ `pro_set_` で `begin()` を再実行するため、この区別で retry の再抽選を防げる。`-1` では抽選も操作書換えもせず、md_2 と同じ YCSB 生成を保つ。

0〜100 では初回に tx 単位で抽選し、ro 選択なら全操作を READ、update 選択なら既存の読み書き分布を保ちつつ少なくとも１操作を WRITE または `ycsb_rmw` に従う RMW にする。待機型の worker 1 には `izanagi_long_kind=1/2` を最後に優先適用し、操作数型の batch worker にも同じ指定を適用できるようにする。指定 `0` は全 worker で生成のまま。書換え後に全操作から `is_ronly_`、`pro_set_.front().ronly_`、`pro_set_.front().wonly_` を再計算する。`wonly_` は RMW を単純な WRITE と取り違えないよう、現行 [ycsb.hh:55–79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/external/ccbench/include/ycsb.hh:55) と同じ「READ があれば false」の定義に合わせる。両 flag の既定値では操作を書き換えず、既存 batch 拡張もそのままなので md_2 の生成経路と一致する。

**D-C の観測。** `mainte()` の [transaction.cc:883–888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/external/ccbench/cc/cicada/transaction.cc:883) で実際に flag が 0→1 となる時刻を記録し、その呼出し元を通常 update、長い update、abort に分類する。ro commit の [transaction.cc:934–937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/external/ccbench/cc/cicada/transaction.cc:934) では `chkClkSpan(gcstart_, now, gc_inter_us * clocks_per_us)` と `GCFlag[thid_]==0` を**観測だけ**し、条件を満たす最初の ro commit 時刻を `cf` とする。実際の raise が先なら、その時刻を `cf` とする。ro 経路から flag と `gcstart_` は変更しない。

thread 別の `cf_us`、`raise_us`、`cf_kind`、公開世代を `transaction.hh` の固定長静的配列に置く。worker 自身だけが書く統計カウンタは従来どおり通常の整数でよいが、leader が走行中に読む時刻・種別・世代は atomic とし、release/acquire で揃える。公開直後に worker が次世代を書き得るため、世代付き二重 slot を使い、leader は**今回の世代**を読む。単一 slot を公開後に読む実装は競合で誤帰属する。[transaction.cc:962–964](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/external/ccbench/cc/cicada/transaction.cc:962) の既存 `leaderWork()` 前後の `GCFlag[0]` 1→0 判定を保ち、公開時刻、前回公開時刻、各 thread の今回の時刻を集計する。初回公開、欠損・世代不一致、時刻逆転は通常の分母へ混ぜず別計数する。

有効な公開間隔ごとに、整数 µs の同じ時刻座標で

`I = (max(cf_i) − previous_publish) + (max(raise_i) − max(cf_i)) + (publish − max(raise_i))`

を計算し、それぞれ `dc_cf_wait_sum_us`、`dc_ro_gap_sum_us`、`dc_leader_wait_sum_us` と件数を出す。第一項には `max(cf_i)` を与えた tx の種別別件数・和を付ける。abort は commit ではないので独立種別とし、長い ro も区別する。等時刻 tie は thread ID 順など固定規則を明記する。

**厳密和と read。** 既存ヒストグラムに加え、公開ごとの境界年齢 `gc_boundary_sum_us/count`、公開間隔 `gc_publish_sum_us/count`、ro `begin()` 時の `ro_snapshot_age_sum_us/count` とヒストグラムを置く。各値は event ごとの整数 µs を加算し、負値・overflow は別計数する。時刻を先に整数 µs に揃えれば D-C の三項が公開間隔へ厳密に足し戻る。snapshot 年齢は `rts_` を設定した直後の `rdtscp − (rts_ >> 8)` で測り、retry も試行として数える。

read の [patch:377–404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/patches/instr-cicada-version-lifetime.patch:377) で ro の `readonly_deep[5]` に加え `readonly_candidate[5]` を数える。ro 成功 read も `vlife_lower_/upper_/reads_` に反映する。update 側の既存 `deep/candidate`、`deep_read_zero/candidate_read_zero` の定義と値は変えない。ro の既読０件の解析が必要なら `readonly_deep_read_zero` と `readonly_candidate_read_zero` を**対で**追加し、分母のない片側だけは作らない。候補率は観測鎖上の値で、固定 snapshot のまま適用できる候補ではない。

計器 JSON は `schema_version:2`。既存 field に `readonly_candidate`、必要なら ro zero の２配列、`ro_snapshot_age_us[42]` とその sum/count/negative、GC 二種の sum/count、D-C 三項の sum/count、cf 種別別 count/sum、D-C invalid/negative、`build` の flag 値を追加する。field 名・単位・配列長を driver と README に一つの表で固定する。

**inert と分岐 pin。** 追加コードは既存の VLIFE/LONGTX guarded block に収め、`mainte()` に必要な VLIFE block だけ新設する構成なら、暫定 witness 数は `transaction.cc` VLIFE **34**、LONGTX **3**、`transaction.hh` VLIFE **9**。これは実装配置に依存する設計目標で、最終値は patch の `+#if` を数え、condition gate の前処理 witness で確定する。`#line N` は追加 block の直後に**元の次行の番号**を復元し、既存の [test_vhash_cicada_vlife.py:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/tests/test_vhash_cicada_vlife.py:395) で include 行・論理行・前処理を stock と比較する。smoke で `.text`、`.rodata`、`nm`、`strings` も再実測する。別 TU に branch を置くと現行 meaning gate が観測できない。

## driver 設計

[vhash_cicada_vlife.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:41) の既存 24 条件を維持し、新 ID を例えば `R{0,25,50,75,95}-{none,wait1msU,wait10msU,wait10msR}-gc{10,1000,100000}` の直積で60個追加する。二つの stock 生成 anchor は既存 ID `B-none-gc10`、`B-wait10ms-gc10` を選ぶので合計62 ID、３反復で186走。新条件は `ycsb_rratio=50`、skew 0.9、10 ops、48 worker とし、`izanagi_ronly_pct` と `izanagi_long_kind` を [同:283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:283) の `_flags()` から渡す。旧 ID では `-1/0` を渡す。N は新 patch の smoke で再較正する。

[同:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:82) の parse は計器行 schema 1 と 2 を明示的に分岐し、各 schema の field 集合、配列長、非負性、`candidate≤deep`、sum/count の整合、D-C 三項の足し戻しを fail-closed に検査する。旧 md_2 raw を読むため schema 1 は残す。ただし新 wave の measure と作図は schema 2 を必須にし、schema 1 の新指標をゼロとして扱わない。外側の raw JSON の schema は既存１でもよいが、producer の変更が明確になるよう２に上げるなら smoke 検証も両版を明示的に扱い、**新 measure は新 patch SHA の smoke のみ**受理する。過去 smoke は SHA 不一致で使えない。

[同:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:168) の summarize は、K 別に `ro_deep / ro_reads`、`ro_deep / (ro_deep+update_deep)`、`ro_candidate / ro_deep`、GC 二種の `sum/count`、ro snapshot 年齢の `sum/count`、D-C 三項の `sum/count` と `sum(ro_gap)/sum(interval)` を返す。ゼロ分母は `None`。D-F は同一 gc 値・長い tx 種別の反復同士を揃えて `Lag(r,L)−Lag(r,none)−Lag(0,L)+Lag(0,none)` と公開回数/秒について計算し、反復ごとの差を図と一次資料で扱う。

`--conditions` は現行 [同:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:559) のカンマ区切りを使う。62 ID を順序固定で約12〜13件ずつ５組に分け、各 job に明示して別 `--out` を与える。anchor を一組に含め、ID 重複・欠落を job manifest と図の merge で拒否する。smoke の inert witness 自体は新 patch にも適用できるが、旧 smoke JSON は patch SHA が違うため流用できず、全 witness を取り直す。

## 登録簿とテスト

[condition_meaning_gate.py:83,380,527,557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/condition_meaning_gate.py:527) の macro 登録は既にあり、新 macro は不要。前述の配置なら VLIFE `34/9`、LONGTX `3/0` を目標にし、実 patch の branch 数と前処理結果で pin を決定する。[materializer_admission.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/materializer_admission.py:108) の `NON_ADMISSIBLE` 登録は維持し、新 driver を作らない限り entry 追加は不要。[screening_driver.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/screening_driver.py:73) の既定０も維持する。

純関数テストには schema 1 後方読取りと schema 2 の欠損・余分・重複・負値拒否、worker 合計、ゼロ分母、D-C の三項恒等式と無効世代拒否、D-F の交互作用式、60 条件の直積・旧24・anchor２件・argv flag を入れる。さらに retry の種別固定、ro/update metadata、abort の cf 分類、同値再公開、初回公開除外、stock 前処理一致を確認する。read-only 候補のテストは「固定 snapshot には適用不可」という解釈まで明記する。

grep で見つかった同時修正候補は [test_condition_meaning_gate.py:108–112,439,492,1550,1596,3519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/tests/test_condition_meaning_gate.py:108) の件数 pin、[test_p3_s4_loop.py:8555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/tests/test_p3_s4_loop.py:8555) の patch token allowlist、[test_vhash_cicada_vlife.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/tests/test_vhash_cicada_vlife.py:365) の begin block 文字列分割である。[test_ccbench_spawn_sites.py:81–84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/tests/test_ccbench_spawn_sites.py:81) の起動箇所数と [test_p3_build_authority_cli.py:161,182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/tests/test_p3_build_authority_cli.py:161) の driver/materializer pin は、起動関数と登録名を増やさなければ値を変えない。変更後に再 grep する。

## 作図

新しい `tools/plotting/plot_vhash_readonly_share.py` は raw の各走を再 parse し、条件表・patch SHA・反復数・入力間の重複を検査してから描く。

1. **深い探索:** 横軸 ro 指定率、gc interval と長い tx を系列または小パネルにし、K 別の `ro_deep/ro_reads` と `ro_deep/(ro_deep+update_deep)` を別パネルへ描く。実現した ro 比率と ro snapshot 年齢も注記し、指定率を実現率と取り違えない。
2. **境界の遅れ:** 境界年齢の厳密平均と既存２倍 bucket の p50 を別パネルで示す。公開回数/秒と snapshot 年齢を併記し、平均と bucket 上界を同じ統計量として扱わない。
3. **分解:** D-F の ro 差、長い update 差、交互作用を gc 値ごとの棒にする。D-C の `cf待ち / ro gap / leader待ち` は同じ走内の別パネルにし、二つの分解を足し合わせない。
4. **見積り:** (a) K 別 ro 候補率と固定 snapshot 不要率 `1−f` に対する制限付き機会量、(b) `ΣΔ_ro/Σ公開間隔` と公開間隔を描く。どちらも実装成功率や真の反実仮想境界と表示しない。

[FIGURE_CONVENTIONS.md:24,65,87,96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/tools/plotting/FIGURE_CONVENTIONS.md:65) に従い、３反復の不確かさ、PNG/PDF、保存前の fail-closed レイアウト検査、実寸 fixture、各図の入力パス・SHA256・campaign ID・条件・主要数値を含む `.provenance.json` を実装する。計測ノードの外で実 raw による全図生成を検証する。

## 投入経路

md_2 と同じ `tools/pegasus/dispatch_compute.py --task generic -- python3.10 -m orchestrator.campaign.vhash_cicada_vlife measure --conditions <組> --smoke-json <新smoke> --out <別々のraw>` で足りる。事前に新 patch の smoke を計算ノードで通し、その SHA と較正 N を全５ job に束縛する。５ job は互いに別ノードへ置き、md_11・md_14 と同居させず、各走の競合 probe と host 名を残す。

md_2 の本計測は**各 job** が６条件×３反復と build を含み Elapse 約125秒だった。今回の５組は各12〜13条件なので、単純外挿は各約250〜300秒、５ job 合計約1,250〜1,500秒。新しい atomic 観測と smoke・build の余裕を加えても暫定見積りは約0.5〜0.8 node 時間。ただしこれは md_2 の実測からの外挿で、親 brief の「186走×７秒＋build５本×３分」は保守的な別計算（約0.62 node 時間）である。投入前に smoke 実測で更新し、合計２ node 時間以上なら停止する。

## brief への反論

- **P2:** 0% と95% の指定率は「各新規手続きの抽選率」で、３秒内の実現 ro 試行率・commit率とは一致しない。長い worker の固定種別、abort/retry、ro と update の所要差が効く。指定率、試行率、commit率を別々に記録する。`ronly_ratio` を渡すだけでは YCSB を制御できない。
- **P4 D-C:** `cf` は「ro commit でも**同じ現在の** timer 条件を見た場合」の局所的な一次近似として有効だが、真の改変実行を再現しない。ro が実際に flag を上げれば `gcstart_` の更新時刻、次の GC work、leader の公開時刻、後続 snapshot と衝突が変わる。また実 flag は abort からも上がり、leader 自身の flag が公開条件に入る。したがって abort と leader の区別、世代競合、未公開末尾の打切りを記録し、`Δ_ro` を「ro に帰属した確定因果効果」と呼ばない。
- **P4 D-F:** ro 比率を増やすと update tx 数・install 版数も減り、境界年齢は公開頻度以外からも動く。D-F は条件間の**総差と交互作用**であって「ro のせい」の識別ではない。update commit/s、install/s、abort率、実現 ro率を各セルで併記する。長い ro と長い update は同じ待機時間でも commit率が違うため、両者の対比も機序の手掛かりに限る。
- **P5(a):** 固定 snapshot の ro に選択的 forwarding を適用すると意味を変える。`rts_=MinWts−1` の安定 snapshot から前進する場合は、ro でも read-set の整合検証、serialization timestamp と GC 保護の更新が必要になる。先頭 K 版の候補率は「既に観測した鎖・既読区間・先頭 K 版に限る」介入の楽観的機会量であり、**あらゆる実装で避けられる深い探索の上限ではない**。また `(1−f)×候補率` は固定不要性と候補性の独立を仮定したモデル値で、相関があれば上限ではない。固定不要 tx を直接識別できない本計測では、f の感度曲線と、その仮定・対象範囲を明記する。
- **P3/P6:** 60条件と２ anchor は主効果を見るには十分だが、古さ軸の `gc_inter_us` は指定値であり、実際の snapshot 年齢は公開遅れの結果でもある。ro snapshot 年齢の直接測定は必須。0%、95% で極端なセルには深い read または公開の分母が乏しくなる可能性があるため、ゼロ分母を欠測表示し、条件を後から選別しない。２ node 時間見積りは上記の範囲なら妥当だが smoke 後に再計算する。

## 総括

- 新規手続きだけの種別抽選と、世代付き atomic 観測を同じ二つの patch 対象 file に実装する。
- D-C は同一走内の局所近似、D-F は条件間の総差として明確に分ける。
- ro 候補率は固定 snapshot を変えてよい場合の制限付き機会量として報告する。
- schema 2 と新 smoke を必須にし、md_2 の raw・24条件・schema 1 の読取りを保存する。
- 未解決事項は実 patch の最終 branch witness 数、smoke 後の所要時間、固定 snapshot 不要な tx の実際の割合 `f`。