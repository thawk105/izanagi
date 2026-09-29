## 変更点一覧 (file:line)

以下の行番号は、指定された checkout の現行ファイルを読んだ位置である。**実装前に base を確認すること。** `external/ccbench` の実際の `HEAD` は `681066606…` で、brief の「現 HEAD = `511c9538`」とは異なる。ただし、指定された Cicada・YCSB・runner のファイルについて `511c9538..HEAD` に差分はなかった。patch は `511c9538` の隔離 checkout から生成し、その pin と適用結果を記録する。

| 変更先 | 挿入位置と目的 |
|---|---|
| `patches/instr-cicada-version-lifetime.patch` | `511c9538` を preimage とする単一 patch。計器と長い tx の二つの macro を既定 0 で包む。 |
| `cc/cicada/transaction.cc:79–137` | `read_internal` の開始ポインタ、物理 hop 数、選択版の位置、先頭 8 版の候補を記録。成功・not found・deleted を区別する。`read:156–165` のローカル再読は版リスト探索として数えない。 |
| `cc/cicada/transaction.cc:196–288` | `update` の早期 abort 判定と blind write の走査を別 site として記録。RMW、`WRITE_LATEST_ONLY`、既存 write-set hit は探索なしとして別計数。 |
| `cc/cicada/include/transaction.hh:247–293` | validation precheck の各走査を計数。 |
| `cc/cicada/transaction.cc:481–530,543–593` | install の CAS 再試行を含む走査、read-set 検査、write-set 検査 (b) を各 site で計数。**install 数は CAS 成功後の `:530` で一度だけ**増やす。生成数、試行数、commit 数とは区別する。 |
| `cc/cicada/transaction.cc:806–843`、`include/transaction.hh:173–197` | GC 境界判定、detach 成功、切り離した各版の数と保持時間を記録。ロック取得失敗や古い queue entry の pop は回収に数えない。 |
| `cc/cicada/util.cc:281–323` | `MinRts` 公開時刻、公開間隔、境界の年齢を記録。 |
| `cc/cicada/transaction.cc:919–929` | `IZANAGI_CICADA_LONGTX` のときだけ、既存の壊れた `WORKER1_INSERT_DELAY_RPHASE` 節とは独立に、`thid_ == 1` と `FLAGS_worker1_insert_delay_rphase_us` による待機を置く。 |
| `include/ycsb.hh:55–84,97–106` | `makeProcedure` と同じ Zipf、乱数、read 比を用い、batch worker の**操作数だけ** `FLAGS_batch_max_ope` にする。 |
| `cc/cicada/ycsb_cicada.cc:34–52`、`common/runner.hh:267–332` | join 後に計器集計 JSON を一行出す接続点。可能なら runner の既存 hook／Cicada 側の呼出しで完結させ、共有 runner の変更を避ける。 |
| `patches/README.md:14,533–575,711–748` | 表行と専用節に preimage、二 macro、既定同一 witness、計数定義、限界を登録。`patches/ledger.json` は brief P2 の裁定どおり変更しない。 |

## patch 設計

`IZANAGI_CICADA_VLIFE` の状態は `TxExecutor` 内の条件付き field と、worker ごとの独立 counter に置く。`ReadElement` に全候補を持たせる必要はない。`read_internal` が先頭 8 版の `{wts, status, 上側の committed wts}` と選択版の物理位置を一時的に集め、その read の時点で K ごとの判定まで済ませる。既読集合については executor に下限 `L=max(既読 wts)` と上限 `U=min(各既読版の直上 committed wts)` を増分更新する。各新規 read で候補を高々 8 個調べれば、forwarding 判定の追加計算は **1 read 当たり O(8)、1000 操作で O(n)** となる。`ReadElement` の寿命や validation 時の `partial_sort` に依存しない。retry、abort、commit、read-only 早期 return でこの状態を正しくリセットする。

「物理位置」は、`tuple->ldAcqLatest()` から実際に `next` を辿った位置として計る。pending・aborted も含む。選択版を得るための hop 数と、validation が `later_ver_` から始めた際の hop 数は別の値である。並行 install があるため、全時点で不変な「絶対順位」とは呼ばず、**その探索が観測した鎖での位置**と記す。read、update、validation のヒストグラムは site 別に保ち、探索なし、null、retry も分母から消さない。

forwarding は update-tx の深い read を対象に、K ごとに先頭 K の committed かつ deleted でない候補 `v` を調べる。整数 timestamp `t` について `t ≥ max(wts(v), L, 元の読み取り timestamp+1)` かつ `t < min(次の committed 版の wts, U)` を満たすかを判定する。候補と境界は**対象 read 時点の観測値**として保存／判定する。pending の後の確定、後続 writer、write-set 制約、node-set 検証を無視するので、これは候補探索の楽観的見積りであり、実際に forward して commit できる割合の証明ではない。read-only tx は固定 `rts` で読むため、この比率から外し、read-only の探索数・深さ・件数を独立に出す。

GC の「生存版数」は `初期版数 N + CAS 成功 install 数 − detach した版数` を基本にする。`:315` の初期 DB 生成を省くと値が N だけずれる。INSERT、DELETE による record 回収、inline promotion／reuse を有効にする場合は、版の物理実体数と鎖に接続された論理版数を別指標にする。保持時間は `wts` からの年齢と上書き時刻からの年齢を別名で出し、`(rdtscp − (wts >> 8))/clocks_per_us` は clock boost を含むため厳密な実時間ではないと明記する。leader が走行中に生存数を読むなら worker 別 cacheline counter も atomic な snapshot が必要で、**非共有 counter を join 後に合算する設計とは分ける**。

終了出力は prefix `IZANAGI_CICADA_VLIFE_JSON ` に続く一行 JSON とする。schema version、全 worker 数、探索 site 別ヒストグラム、K 別の分子・分母、read-only 別数、install／detach、GC 境界・保持時間のヒストグラム、sample rate、欠測・overflow を含める。worker ごとの counter は worker 終了後に runner が join した `common/runner.hh:299` 以降で合算できる。汎用 runner に計器固有コードを直書きせず、Cicada だけが渡す終了 hook または Cicada 側で runner 戻り後に読める worker 別配列を使う。JSON は通常の結果表示 `:316–331` の後に一回だけ出す。

長い tx は、Cicada の TU だけで `IZANAGI_CICADA_LONGTX` 有効時に選ぶ補助関数／呼出しを `include/ycsb.hh:55–106` に条件付きで置き、`thid_ >= FLAGS_thread_num` に限って操作数を差し替える。全 protocol 共通 header の既存 `makeProcedure` 本体や他 protocol の既定前処理結果は変えない。`FLAGS_batch_rratio` や `batch_tuples` は使わず通常 YCSB と同じ read 比・キー分布に固定し、長い tx の要因を操作数に限る。`FLAGS_batch_th_num=1`、`batch_max_ope=1000`、`ycsb_max_ope=10` を明示する。batch worker を加えると総 thread 数は 49 になる点も条件表に載せる。

既定同一性は、追加する宣言・実行文・include をすべて literal `#if IZANAGI_CICADA_VLIFE`／`#if IZANAGI_CICADA_LONGTX` 内に入れ、各 `#endif` 直後の `#line` で preimage の論理行へ戻す形なら到達可能である。行依存の現物は `transaction.cc:337,853` の `ERR`、`util.cc:25,30,40–58` の `ERR`、`ycsb_cicada.cc:55` の `ERR`、共通 `ycsb.hh:146` の `ERR`。`transaction.hh:375` は `static_assert`、列挙された `version.hh`、`tuple.hh`、`common.hh`、`cicada_op_element.hh`、`time_stamp.hh`、`runner.hh` に直接の `__LINE__`／`__FILE__`／`ERR`／`assert()` は見つからなかったが、展開される include と compiler line marker も witness の対象にする。特に YCSB header の `#line` は他 protocol の TU にも効くので、**Cicada 以外の前処理比較も必要**である。`#line` により生の `-E` byte 列は line marker が増え得るため、比較対象は mocc 前例どおり論理行番号へ正規化した非空行列とし、加えて同じ toolchain／同じ長さの source・build path で `.text` を比較する。

## driver 設計

`orchestrator/campaign/vhash_cicada_vlife.py` は、前例の `silo_policy_coverage.py:308–399` の condition gate、NON_ADMISSIBLE build と `:556–587` の隔離 checkout／patch 適用、`s3_mocc_lock_coverage.py:89–118,147–255` の command・toolchain・依存物準備、`:439–486` の objdump／nm／strings witness を取り込む。プロトコル固有の target、flags、parse は新設する。`silo_policy_coverage.py:130–156` の厳格 parse 方針も使い、一行の欠落・重複・未知 field・負数・counter 不整合を拒否する。

`smoke` は同じ pin の stock、patch 既定、patch 有効の三 build を作る。stock と既定の正規化 `objdump -d`、`nm -C` の `izanagi`、`strings -a` の `izanagi`／`IZANAGI_` を比較・記録する。`WORKER1_INSERT_DELAY_RPHASE=1` は**stock の別 build**でコンパイル成否と診断を保存し、失敗を事前の事実として扱わない。stock build で N={1M,2M,4M} の maxrss を取り、同じ計算ノードの `lscpu` L3 と照合して、`maxrss > 4×L3` となる最小 N を選ぶ。該当なしなら自動的に 4M と決めず calibration 不成立とする。`CICADA_SPACE` は `genome.py:178–187`、CMake 変数への写像は `model.py:56–62,84–92` を使い、選んだ stock genome の全 5 軸値と cache args を raw に記録する。計器二 macro は genome 軸に混ぜない。

`measure` は宣言済み条件 ID の一部集合だけを受け、未知 ID、重複、範囲外の反復、異なる N／pin／toolchain、既存 raw の無断上書きを拒否する。各 run の stdout、stderr、rc、timeout、実 argv、build identity、condition gate、JSON 行、parse 後 counts を条件・反復ごとに raw JSON へ保存する。条件分割は 4 job に均等割りできるが、各 job の build と DB 初期化時間を smoke で測ってから 2 node 時間の上限を再計算する。

## 登録簿とテスト

`materializer_admission.py:46–55` の registry に `orchestrator.campaign.vhash_cicada_vlife._build_variant` を `NON_ADMISSIBLE` として登録し、driver は `silo_policy_coverage.py:363–375` と同様に build 前に要求する。依存物 install を自前関数として持つなら、それも「診断用依存物のみ」の登録を加える。

`condition_meaning_gate.py:65–90` の `DefineSpec` に二 macro を `ROUTE_CMAKE_CXX_FLAGS`、target `ycsb_cicada.exe`、patch path は同一、owner TU は各 branch を実際に含む TU として登録する。`:356` の branch witness は一 macro 一つの主 site とし、残りの `#if` site は companion site 一覧に**正確な件数**で登録する。macro を複数 TU に置くため、単一 owner の宣言だけでは全 branch を証明できない。patch 完成後に directive の正確な数を機械で数え、`:518–545` の総 site 数と一致させる。二 macro は既定 0 の `inert_values=("0",)` を指定する。二つが同時に必要な measure build は gate を macro ごとに一回ずつ通し、実 build argv との対応を残す。

在庫 pin は `test_condition_meaning_gate.py:47–102` の `_COMPILE_TIME_BRANCH_MACROS` と `_NEW_BRANCH_EXPECTATIONS`、`:1175–1199` の実 patch 照合、`:3539–3543` の **43／44 件**を同時更新する。`:3490–3510` の supply domain 集合にも二 macro を追加する。`test_p3_build_authority_cli.py:1249–1272` は materializer registry の在庫検査箇所として確認・更新する。`screening_driver.py:51,116–136` の `_CONDITION_DEFAULTS` は genome flags が対象であり、二つを `CICADA_SPACE` に足さない限り不要である。

`test_vhash_cicada_vlife.py` は login で走る純関数を中心に、JSON 一行の厳格 parse、worker 合算、ヒストグラムと総数の整合、K={1,2,3,4,8} の深部割合と条件付き forwarding 割合、read-only の分離、条件 ID の分割と重複・未知・欠測拒否を検査する。既定一致テストは `test_mocc_proof_surface.py:435–451` と同じ「隔離 preimage／patch の `g++ -E` を論理行番号へ畳んで比較」を Cicada の touched TU と、共有 `ycsb.hh` を読む非 Cicada TU に適用する。build／`.text` witness は smoke に置く。新テストは自走 `_run()`／`__main__` を付けるか、`orchestrator/tests/README.md:122` の pytest 専用 allowlist に明示追加する。`test_plain_runner_coverage.py:60–86` がこの選択を検査する。`acceptance_duration_ledger.json` は `conftest.py:1589–1629` の所要時間ヒントであり、テスト追加時の必須登録ではない。受入全走で実測した nodeid の時間を保守する際に追加する。

## 作図

`tools/plotting/plot_vhash_cicada_vlife.py` は raw JSON を唯一の数値入力とし、各条件・反復の整数分子／分母から図の値を再計算する。

1. **探索長分布**: read、blind update、validation の site 別 ECDF または対数 bin ヒストグラム。探索なしと失敗は注記して分母を明示する。
2. **K 反実仮想**: K 横軸に「K より奥の read 割合」と「奥の update-tx read のうち楽観的 forwarding 候補ありの割合」を別パネルで示す。read-only は別集計、分母 0 は欠測表示とする。
3. **GC**: `gc_inter_us` 横軸に `MinRts` 境界年齢の分布要約と、保持時間／生存版数を必要なら別パネルで示す。異なる意味の値を無説明の二軸にしない。

[FIGURE_CONVENTIONS.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/FIGURE_CONVENTIONS.md:23) に従い、3 反復には t 分布の 95% CI、PNG と PDF、各図の入力 SHA256・条件・主要数値を記した provenance JSON、保存前の bbox 重なり検査を備える。実寸の条件集合を使った fixture と、実データでの全モード生成確認が必要である。作図は計測ノードの外で行う。

## 投入経路

`dispatch_compute.py:155–160,1573–1577` の `generic-v1` は非空 argv を受け、dispatcher 自体は `admission_registry.json:64–69` で login `local-ok` である。ただし新規 `orchestrator/campaign/vhash_cicada_vlife.py` は現 registry に無く、`hooks/guard_bash.py:1274–1282` は未登録実行体を拒否する。**`--task generic -- python3 -m ...` が hook を通ると断定できない。** まず exact command を hook の dry probe／関連テストで確認し、必要なら新 module を registry に `dispatch-required` として登録し、計算ノードの site gate を確認する。計算ノードからの直接 Python 実行を代替経路にする場合も dispatcher の PBS allocation 内だけに限る。hook は自動適用の保証ではないため、login での直接 build・計測を driver 自身の site preflight でも拒否する。

## brief への反論

- **P1**: 二 macro の分離は妥当。ただし `FLAGS_batch_th_num=1` は総 49 threads、worker1 遅延は worker1 の**毎 tx**に入る。論文の「一つの長い tx」と同じ頻度とは限らないので、長 tx の発生回数・worker 別操作数を raw に残す。既存 `WORKER1_INSERT_DELAY_RPHASE=1` の失敗は smoke 実測まで未確定。
- **P2**: `ledger.json` を避ける判断は維持する。元依頼との相違を一次資料に記す。
- **P3**: driver と登録簿だけでは投入可とは言えない。新 module の Pegasus admission と hook を別途確認する。
- **P4**: 「物理位置」は並行変化する鎖の絶対順位ではない。観測開始ポインタからの位置とする。また提示された区間テストは、pending の後日 commit、後続 writer、対象キーの削除版、write-set／node-set 制約を落としている。したがって**forwarding 可能性の上限を証明した値ではなく、明示した制約を外した楽観的候補率**と表記する。元 timestamp より後へ進める条件と整数境界の包含関係をテストで固定する。
- **P5**: `install−GC` だけでは初期 N 版が欠ける。`gc_records()` による削除 record と inline/reuse も区別が要る。read-only commit は `transaction.cc:934–937` で早期 return し `mainte()` を通らないため、GC flag の全 worker 同期待ちが境界遅延を大きくし得る。これは条件の重要な機序として raw に残す。
- **P6**: 算術上は 24 条件×3 反復で正しい。ただし skew、read 比、長 tx 型を同時に変えると機序の切り分けは図のパネルと条件表に依存する。1000 ops の batch は abort/retry と `searchReadSet`／`searchWriteSet` の線形探索により、処理時間が 10 ops の単純な 100 倍ではない。2 node 時間の見積りは build、DB 初期化、3 種 N の calibration、gate、失敗再試行を含めて smoke 後に再計算する。
- **P7**: maxrss が 4×L3 を超える最小 N という選択規則は明確。ただし 4M でも超えない場合は基準未達、3 候補の初期化が時間／メモリ制限に当たる場合も未決として止める。選んだ N が論文の 1M と違えば、その相違を図と一次資料に出す。

## 総括

- patch は `511c9538` の隔離 checkout で作り、既定の論理前処理行と `.text` の同一性を証明する。
- 探索 site ごとの分布と、read 時点の候補から O(n) の forwarding 候補率を記録する。
- GC は初期版、install、detach、read-only による境界停滞を分けて数える。
- driver は厳格な raw JSON、三 build の smoke、条件部分集合の measure を持つ。
- 未解決事項は新 module の Pegasus admission、smoke 後の N と 2 node 時間の成立、楽観的候補率を「上限」と呼べる範囲である。