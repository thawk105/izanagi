## 方針と参照記法

**replica は案 (i) の本物の `tools.acceptance_shards` plugin を推奨する。ただし、P6 の hook 順序、xdist の配布順、C の解釈、固定費の分解方法を修正する。** 本 wave の結論は「同一 tip の replica 条件における反復実測」とし、実受入全体の改善を実証したとは書かない。

指定資料を静的に読解した。pytest・selftest・計測は未実施、ファイル変更はない。

以下の略記は指定 worktree 内の実ファイルを指し、`T:918` のように行番号を付す。

| 略記 | ファイル |
|---|---|
| T | `orchestrator/tests/test_s8b_oracle_driver.py` |
| F | `orchestrator/tests/conftest.py` |
| AS | `tools/acceptance_shards.py` |
| RT | `tools/run_tests.py` |
| DC | `tools/pegasus/dispatch_compute.py` |
| LS | `/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/scheduler/loadscope.py` |
| LG | 同ディレクトリの `loadgroup.py` |
| V | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2710-b5-wall-decomposition/verbatim/` |

計測前に親が実 tip、台帳・probe の hash、ccbench checkout、使用 interpreter・xdist、実効 argv、計測に関係する env と temp 配置を記録する。同一 tip だけで fixture 入力が完全固定になるわけではない。T:794–824 は untracked を含む Git-visible output を列挙するため、測定期間中は insight の書込みなど当該 checkout の入力変更を避ける。新しい閉包機構は作らない。

## P1：replica の忠実度と方式選択

| 面 | 実受入 shard-0 child | 推奨 replica |
|---|---|---|
| 起動 | RT:1495–1532 の pytest child | 同じ pytest target・worker 数・dist に観測 plugin を追加 |
| 選択 | AS:895–920 の `records_from_items` → `allocate(records,3)` → shard-0 | 同じ production plugin を実行 |
| 除外 | 親資料では恒久除外 token は現在 0。RT:1511–1516 | 同じく除外なし。runner 所有 token を捏造しない |
| 台帳 | F:1679–1701 の controller 読込・workerinput 配布 | 既存 conftest をそのまま使用 |
| 並べ替え | F:2263–2275 の wrapper 復帰後、unit cost 降順 | A は同一。B だけ後段で変更 |
| xdist | loadgroup、48 worker | 同一 version・option。scheduler は変更しない |
| 観測 | AS:948–972、1097–1188 の report | 本物の report に probe JSONL を併置 |
| 実行環境 | tests dispatch と runner の実効 env | generic の clean env から runner が probe 用 env を設定。差を明記 |
| 外部負荷 | 3 shard の複数ノード実行 | shard-0 の 1 ノードのみ |
| 証跡 | 受入の shard 成果物・統合判定 | 計測用成果物。受入証跡として利用しない |

**案 (i)** は選択・report・既存 conftest の shard 状態確認を維持できる。AS:1198–1217 の `create_session(repo,3)` を各走で呼び、`PLUGIN_SPEC_ENV` に session root、count=3、index=0 を入れる。

現物の env 名は **`IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1`**（AS:51）。`operational-facts.md:6` の文字列 `…PLUGIN_SPEC` は訂正し、コードでは必ず定数を参照する。

制約は次のとおり。

- `create_session` の配置先は main repo の親の固定 shared root。出力先引数はない（AS:1202–1213）。
- `shared_root_for_repo` も同じ root を導く（AS:231–236）。
- `_validate_shared_root` は repo 内・control container 内を拒否する（AS:214–228）。`create_session` は root の symlink も拒否する。
- `_plugin_spec` 自体は JSON の key 集合を確認して `InternalSpec` を作るだけで、この配置制約を検査しない（AS:797–814）。実 runner はさらに session の親・shard dir を確認する（RT:1475–1487）。この差を利用した配置の迂回は採らない。
- replica session は既存 corpus に一時混入する。親は作成した session の path を記録し、pytest 終了後、失敗時も含めて **自分の session だけ** job dir へ退避する。測定中の既存 corpus 集計からもこの集合を除く。退避後の report 内の元 path は書き換えず、移動先との対応を添える。

**案 (ii)** は corpus を汚さず、C の実選択集合を自然に記録できる。一方、report の正規化・phase 合算・worker 別占有を再実装する必要がある。さらに spec 無しでは F:2122–2125 の shard 閉包確認が実行されず、F:2173–2178 の controller collection 判定も実受入と異なる。したがって本 wave では (i) を優先する。

**93 session との照合**は、同じ定義の 4 値について A の各走・中央値・歴史分布内 percentile を示す。歴史資料の丸め精度も残す。

| 指標 | 93 session の min / median / max（秒） |
|---|---:|
| wall：JUnit testsuite time | 310.8 / 369.0 / 677.1 |
| 最大占有：report の worker duration 最大 | 243.8 / 293.6 / 578.0 |
| 固定費：wall − 最大占有 | 65.0 / 67.2 / 103.3 |
| 最長 node：JUnit testcase time 最大 | 200.0 / 273.6 / 557.7 |

根拠は `V/sessions-shard0-since-0917-0900.md:99–105`。4 値すべてがそれぞれ min–max 内なら「観測範囲内」と記す。これは同等性の合格判定ではない。広い周辺分布への包含だけでは、同時 3 shard・env・観測 overhead の差を排除できない。範囲外でも都合のよい再走で置換せず、差を報告する。

## P5：実物へ委譲する観測 wrapper

module 名を決め打ちして再 import せず、worker の collection 済み item から実際の `item.module` を取得し、`__file__` で T と照合する。T:961 の共有 base 参加と T:6838 の `enforce_held_functions` を通常の pytest import に任せる。

`pytest_configure` は recorder の初期化だけとし、T を import しない。`pytest_collection_finish` で対象 module を特定する。**M の `pytest_runtest_setup(tryfirst=True)` で wrapper を設置し、teardown 終了後に復元する**方式を推奨する。M 以外の cache 検査などへ wrapper を持ち越さない。setup 失敗時にも復元できるよう、protocol 終了側に復元処理を持たせる。

| 観測対象 | wrap する実属性 | 内容・根拠 |
|---|---|---|
| builder | `item.module._build_t080_stub_free_e2e_repo` | 元 callable を 1 回呼び、その返り値を返す。定義 T:1364、共有 get からの呼出し T:929 |
| shared get | `item.module._T080SharedBases.get` | class 属性の通常関数として `self,key` をそのまま委譲。既存 instance を置換しない。T:918–940 |
| helper | `item.module._t080_stub_free_e2e_repo` | 外側の inclusive interval。T:964–1001 |
| base 複製 | `item.module.shutil.copytree` | 実体は共有 `shutil` module の属性。helper 直下の T:1000 の呼出しだけ採録し、再帰呼出しや builder 内 T:1380、T:869 を二重計上しない |
| verifier | `item.module.migration.verify_receipt` | T:93 の module alias 経由なので属性 wrap で直接呼出しを捕捉できる。定義は `t080_freeze_migration.py:2284` |

`copytree` は helper の実行 context と直呼出し位置、再帰 depth で限定する。`shutil` module 全体を proxy に交換しない。

**上の 5 wrapper だけでは lock 待ちを厳密に分離できない。** `get − build` には lock file open、marker 読書き等も含まれる（T:919–940）。P5 に狭い観測を 1 個追加し、`item.module.fcntl.flock` を、対象 get の context 内かつ T:922 の `LOCK_EX` 呼出しに限定して計時する。実 `flock` を同じ引数で 1 回呼び、追加の lock 操作をしない。寿命 lock の T:901、906、910 は対象外とする。

これにより、

- base 取得 = get inclusive
- lock 待ち = 対象 `flock` の経過時間
- build = get 配下 builder inclusive
- 取得その他 = get − lock 待ち − build

を記録できる。追加観測を採らない場合は「lock 待ち＋取得管理残差」と表記し、純粋な lock 待ちとは呼ばない。

JSONL は worker・pid ごとの file とし、最低限次を持つ。

```text
run_id, condition, nodeid, worker, pid,
phase, event, span_id, parent_span_id,
t_start, t_end, monotonic_start, monotonic_end,
call_index, outcome
```

`phase` は setup/call/teardown、`event` は helper/get/flock/build/copytree/verify 等。epoch と monotonic を区別し、duration は monotonic 差で計算する。多重 wrapper の inclusive 時間は単純加算しない。M の少数イベントを保持して node 終了時にまとめて書き、計測中の共有 FS 書込みを減らす。

controller は全 node の `pytest_runtest_logreport` で `report.worker_id/start/stop/when/duration/nodeid/outcome` を記録する。AS:948–972 と同じ phase 合算を再計算し、本物の report と照合する。到着順ではなく start で worker 内の実行順を復元する。

wrapper は引数・返り値 identity・例外を保持し、再試行・コピー省略・cache 変更・assert の変更をしない。実物を呼ぶことと overhead がゼロであることは別で、観測 overhead は未実測の限界として残す。子 subprocess 内の verifier 呼出しは親 process の属性 wrapper では捕捉できず、builder 内時間などに含まれる。

## P2：条件、argv、選択

共通 argv は以下とする。`<targets>` は配列として渡し、param の角括弧を shell に解釈させない。

```text
python3.10 -B -m pytest <targets>
  -n <N> --dist loadgroup
  -p t2710_probe_plugin -p no:cacheprovider
  --junitxml=<run>/junit.xml
  --basetemp=<run-local>/pytest
```

A/B/C はさらに `-p tools.acceptance_shards` を付け、JUnit は作成した session の `spec.junit_path` に出す。job dir の plugin を読めるよう、計算ノード側 runner が子 env の `PYTHONPATH` を設定する。`-o` は不要。`--no-loadscope-reorder` は F:1850–1851 により既存台帳 reorder まで無効にするため使わない。

| 条件 | targets / N | 選択 |
|---|---|---|
| S1 | ccbench-current の完全 nodeid / 1 | nodeid 直指定。production shard plugin は無効 |
| S | M の完全 11 nodeid / 11 | nodeid 直指定。production shard plugin は無効 |
| A | `orchestrator/tests` / 48 | production allocate の shard-0 |
| B | 同上 / 48 | A と同じ集合、unit 順だけ変更 |
| C | 同上 / 48 | A の選択完了後、ccbench-current の完全 nodeid 1 個だけ追加 deselect |

M の正本は T:1293–1317 の 6 function と param 集合。g7 の本体は T:4753。substring で M を選ばない。

S1/S を直指定すれば F:1995–2003 の complete-suite 条件に該当しない。既存 hold はそのまま作用する。A/B/C は full collection を維持し、F:2255–2262 の確認後に選択する。CLI の `--deselect` は使わない。F:1965–2004 の complete 判定を変え、production allocator に渡す universe まで変えうるためである。台帳 reorder の可否は別に F:1828–1875 で決まり、「deselect したから reorder も止まる」とは扱わない。

C の deselect は worker の `pytest_collection_finish(trylast=True)` で行い、`pytest_deselected` を通知する。production plugin の `selected` は **元の A 集合のまま保存**し、書き換えない。別の probe 出力に `allocated_selected` と `executed_selected` を記録する。

したがって C の本物の report は selected と finished が一致しない診断成果物になる。受入の merge・受領証には使わず、実占有と実行集合は probe JSONL から計算する。AS:1129–1133 が未実行 node を `unobserved` に数える点も明記する。

C の代替案は、single_defects の known-artifact・holdout-artifact・unknownness-layer2 の 3 param を除く C′。これは縮約候補そのものの負荷感度に近いが、最長 node は残り、被覆を失う。**既定は C のみ、C′ は算術 model とする。** 両方を 1 回ずつ試す案は D357 の反復条件を満たさない。

## P6：B の並べ替えと実 scheduler の確認

**通常の `pytest_collection_modifyitems(trylast=True)` では conftest の後にならない。** F:2193 は `wrapper=True, tryfirst=True` で、並べ替えは `yield` 後の F:2263–2275 にある。

B の変更点は **worker の `pytest_collection_finish(trylast=True)`** に置く。別 hook のこの段階なら collection-modifyitems の wrapper が復帰済みであり、同じ hook の priority 競争に頼らず後段を確保できる。

ただし、現物の scheduler はさらに次を行う。

1. scope ごとに unit 化する（LS:367–372、LG:55–59）。
2. 既定では **unit の node 数の降順**へ安定ソートする（LS:374–379）。
3. 全 worker にまず 1 unit を配る（LS:396–398）。
4. pending item 数が 2 以下の worker に追加 unit を配る（LS:330–336、400–402）。

したがって「全 worker に必ず 2 unit」「worker k の相方は必ず 48+k」は成立しない。

B は次の手順で実装する。

1. A と同じ選択・conftest reorder 完了後の items を取得する。
2. F:1704–1708 と同じ scope で unit 化し、unit 内順を保存する。
3. unit cost は F:1792–1821 と同じ既知 duration 合計・未知 cost 規則で求める。未知 cost の基準は A の並べ替え時の値を保持する。
4. LS:374–379 の安定ソートを適用した **実 workqueue `Q_A`** を作る。
5. `Q_A` の先頭 48 unit は固定する。残りから `(cost, 元順位)` 昇順の最小 48 unit を取り、49〜96 位に置き、残りは元順を保存する。
6. 得た `Q_B` を collection 順として flatten し、scheduler の node 数ソートを再適用して `Q_B` が保存されるか照合する。

手順 6 が成立しない場合、collection reorder だけでは親の指定する workqueue を作れない。scheduler の差し替えや flag 変更で達成したことにせず、実 collection の unit cardinality を添えて「P6 の指定形はこの集合では実現不能」と返す。同じ cardinality の範囲での pairing は別案として区別する。現 collection に対する成立可否は未実測。

成立時も、初期配布の予測は pending item 数を含めて再現する。実測では最長 node の worker、その前後の node、相方時間、3 個目以降の有無を JSONL で確認する。B の 49〜96 位が軽くなった事実だけを wall 改善の証拠にしない。

## P2・D357：反復、job 割り、時間と temp

親案の **4 compute job を逐次実行**する形を採る。

| job | 逐次実行する条件 | 暫定実行時間 | walltime |
|---|---|---:|---:|
| 1 | S1×3、S×3 | 30〜54 分 | 90 分 |
| 2 | A、B、C | 21〜27 分 | 60 分 |
| 3 | B、C、A | 21〜27 分 | 60 分 |
| 4 | C、A、B | 21〜27 分 | 60 分 |

S1 は 4〜8 分/走、S は 6〜10 分/走を**予約用の未実測見積**とする。S は 11 worker 間の共有 base 待ち・複数 key の build を持ち、S1 の 11 倍とも、競合ゼロとも置けない。

A/B/C は、親の「実行 6〜8 分＋collection 約 1 分」を予約用に 7〜9 分/走と置いた。一方、93 session の JUnit wall は既に collection 等を含むため、その 369 秒へ再び 1 分を足して実測推定値にしない。既存最大 wall は約 11.3 分であり、各 60 分予約に余裕を持たせる。

dispatch は指定経路とする。

```text
python3.10 tools/pegasus/dispatch_compute.py
  --task generic --walltime <上表>
  --queue-wait-timeout <親が定める秒>
  --overall-grace <親が定める秒>
  -- python3.10 -B <job-dir>/probe/t2710_probe_runner.py run <条件列>
```

generic の request env allowlist は空（DC:155–160）。probe 設定は argv で渡し、計算ノード側 runner が pytest child env を構築する。clean は必要な基底 env を選んで継承する実装であり、「環境変数が一切ない」ではない（DC:1661–1671）。

各走は新しい pytest subprocess とし、次を分ける。

- `TMPDIR`：`<node-local-task-root>/<run-id>/tmp`
- `--basetemp`：同 run root 内の専用 `pytest` directory
- JUnit、JSONL、session root：走ごとに新規

`TMPDIR/TEMP/TMP` は repo の output 外に置く。T:37–59 は ambient temp と、T:976 は helper の tmp_path を検査する。`--basetemp` 自体は禁止されていないが、pytest が消してよい専用 directory に限る。

共有 base は T:946–954 の testrunuid を含む hash で区別され、最後の worker が T:903–916 で削除する。run ごとの temp 分離は異常終了残骸の再利用も防ぐ。前の pytest の全 worker が終了してから次へ進み、残骸があれば path と終了状態を記録する。生きた worker の tree を削除しない。

D357 に従い、自分の別 wave・別計測 job も重ねない。メモリ上の都合による条件分割は逐次 job として行い、複数ノードへの同時投入を既定にしない。Latin square は順番の偏りを減らすが、host 差・時間変動・OS cache を除去するものではない。

## P4：分解表と差の定義

shard 表は各走を 1 行とし、以下を固定する。

| 列 | 定義 |
|---|---|
| condition / run / host / 順位 | 条件と実行位置 |
| wall `W` | JUnit testsuite time。外部 process wall は別列 |
| 最大占有 `O` | worker ごとの全 report phase duration 合計の最大 |
| 固定費残差 `F` | `W − O` |
| 最長 node `L` | 全 node の setup+call+teardown 最大 |
| 相方残差 `P` | `O − L` |
| 直列和 `D` | 全 node の phase duration 合計 |
| 平均負荷 | A/B/C は `D/48`。S/S1 は実 worker 数で別表示 |
| 最忙 worker の実内訳 | nodeid、各 duration、順番、item 数 |
| terminal | selected / finished / failed / skipped、rc |

`P=O−L` が実際の「相方」と一致するには、最長 node が最忙 worker 上にあることが必要。そうでなければ算術残差と実相方を別に示す。93 session でも例外 node があるため、ccbench-current を無条件に最長と置かない。

node 表は **M の 11 node すべて**について以下を出す。

```text
condition, run, nodeid, worker, base_key,
setup, call, teardown,
helper_inclusive, get_inclusive,
lock_wait, build_inclusive, get_other,
copytree_top,
verify_call_1 … verify_call_k,
helper_other, call_other
```

helper/get/build/verify の包含関係を span tree で処理し、call の加法分解では重複 interval を除く。`get` 内の build 中に verifier が捕捉された場合、それを base と本体へ二重計上しない。

P4 の「node 固定費」は、`get + copytree + teardown` という運用上の名前として出せるが、lock 待ちや first builder の負担は走・割付で変わる。定数ではない。setup と helper の deepcopy 等も省略せず残差に明示する。

各条件の **3 走の値と指標ごとの中央値**を併記する。中央値同士を足して合計中央値を作らず、各走で先に分解・model 計算する。

A/B/C は各 Latin-square job 内の `B−A`、`C−A` と、それぞれの差の中央値を出す。条件別中央値の差も別列とする。単発 10% 未満の差から改善を主張しない（D357）。

**A−S は「実行 regime 差」または「追加 workload・worker 数に伴う観測差」と呼ぶ。** 48 対 11 worker、仕事集合、cache builder の担当、順序が違うため、純粋な競合の因果効果ではない。S 内にも共有 base 競合がある。

## P3：分割・縮約・pairing の model

各式は run ごとに評価し、その後で 3 走の中央値を取る。記号は実測後に埋める。

ccbench-current node `c` について、正例 verify 2 回を `V₁,V₂`、欠陥側 3 回を `V₃,V₄,V₅` とする。呼出しは T:1845、1850、1876、1898、1904 にある。

分割後の 2 node を次で model 化する。

```text
d_positive = setup_p + get_p + copy_p + helper_other_p
             + V₁ + V₂ + other_p + teardown_p

d_defect   = setup_d + get_d + copy_d + helper_other_d
             + V₃ + V₄ + V₅ + mutation_d + other_d + teardown_d

L_split = max(max_{i≠c}(d_i), d_positive, d_defect)
D_split = D − d_c + d_positive + d_defect
W_split_model = max(L_split, D_split/48) + F
```

正例・欠陥側の `get/copy/setup/teardown` は分割で追加されうる。共通 base build の実作業は 1 回でも、待ち時間は両 node に現れうる。現在の helper 時間を半分ずつ配らない。

`mutation_d` は T:1855–1890 の Git 操作等。verify の start/end 間の区間から正例前後・欠陥生成側の残差を分け、分離不能な部分は未知量として感度を示す。この分割は未実装なので、式の前提に受理集合の同値性を置いた参考 model であり、同値性を証明した設計案とはしない。

3 param 縮約では削除対象を `R` として、

```text
L_reduce = max_{i∉R}(d_i)
D_reduce = D − Σ_{i∈R} d_i
W_reduce_model = max(L_reduce, D_reduce/48) + F
```

とする。ccbench-current が残るため、固定 duration model ではその床を直接下げない。D357 のとおり duration 合計は保存される仕事量ではなく、削除後の競合・build 担当変更も未反映である。縮約を採用する提案にはしない（D2068、D2128）。

pairing は B の実測を第一資料とする。参考式は、

```text
O_pair_model =
  max(d_critical + d_new_partner,
      その他 worker の予測占有)
W_pair_model = O_pair_model + F
```

で、他 worker への律速移動を含める。

**C は数学的な改善上限ではない。** node 除外が base build 担当・競合・順序を変えるため、`W_A−W_C` は「最長候補 node を除いた診断条件との差」。固定 duration・固定他条件の仮定下だけで理想化した ceiling の参考になる。分割・縮約の実装効果に置き換えない。

固定費約 66 秒については、controller の `pytest_collection_finish` だけで worker 起動・collection・集約を独立に分けられない。controller は worker collection を所有しない（F:1987–1994）。AS:1090–1092 は worker 側 collection finish の最大を集約している。

本 wave では外部起動/終了、controller sessionstart/sessionfinish、worker sessionstart/collection_finish、全 test start/stop を記録して、

- 起動から最初の test 開始まで
- test 実行区間
- 最後の test 終了から session/process 終了まで
- worker ごとの collection 完了までの経過

を示す。起動と collection の重なり、worker 間 skew、test 間の空白があるため、`W−O` をこの 3 成分だけの正確な和とは主張しない。残差も残す。

## selftest の範囲

親が login で行う `--selftest` は軽量な純粋処理と合成 callable に限定する。M の node は実走しない。held module は selftest の通常 Python process から import しない（T:6838、`V/operational-facts.md:18`）。

入れる確認は次の 4 群とする。

1. **wrapper の委譲契約**：引数保持、元 callable を 1 回だけ呼ぶ、返り値 identity 保持、例外の再送出、nested span の重複排除、復元。実 verifier の正しさを合成 callable の結果で証明したとは書かない。
2. **B の unit 操作**：item multiset・unit 内順の保持、top-48 固定、選んだ最小 48 の cost 順、残りの安定順、LS の cardinality sort 再適用後の結果、pending item 数による追加配布。mixed-scope の合成例を含める。
3. **選択再現**：保存した collection records に production `allocate` を適用し、A/B の controller 側 selected と一致すること、C は厳密に指定 1 node 差であること。実 collection の記録が無い初回は合成確認までとし、本走出力後に実 records で再計算する。
4. **JSONL**：必須 field、有限 timestamp、start≤end、run/worker/pid の整合、span 対応、phase 合算、report/JUnit との集計照合。

これは probe の限定 selftest であり、repo の pytest/build を login から直接起動する手順ではない。実物への設置と呼出し捕捉は compute 本走の対象 module・元 callable・span 記録で確認する。

## insight と裁定パッケージ

README の節構成は次を推奨する。見出しはすべて H2 とする。

1. 依頼・不変条件・結論
2. 実行条件と replica の忠実度
3. 反復結果と 93 session との照合
4. shard 層の分解
5. M 11 node の分解
6. pairing の配布確認と対比較
7. 最長候補除外の診断結果
8. 分割・縮約の model と感度
9. 次の諮り直し用パッケージ
10. 残存限界・未実測事項
11. 再計算方法・成果物対応
12. 総括

裁定パッケージは次の形式とし、採用済み判断にしない。

| 択 | 受理集合に触れるか | 効果の実測値 / model 値 | 費用 |
|---|---|---|---|
| 分割 | 同値性未証明。第22回項3の再裁定対象 | 上記 `L_split/W_split_model`。直接実測なし | test 分割設計、追加 copy/setup、後続の同値性確認・反復受入 |
| 縮約 | 触れる。被覆を失うため現裁定では採らない | `L_reduce/W_reduce_model`。C と混同しない | 採否再裁定。現 wave で削除実装なし |
| pairing | 集合を保持する設計 | B−A の3組、中央値、実相方の変化 | 後続 reorder 実装・必要な検査・実受入での効果確認 |
| 何もしない | 触れない | A の分解と継続する wall | 実装費なし、毎受入の時間費用は継続 |

decisions fragment は **0**。測定設計の親判断とユーザーの採用裁定を混同しない。worklog は 1。failures は新規事故があった場合だけ、条件・期待と観測・job/run/tip・原因・測定への影響・処置・未解決範囲を書く。単に B の効果が小さいことや model の不確実性を事故にしない。

## author・review の所有と予算

段 5 は **author 1 本が 3 file を一括所有**する。

| file | 所有内容 |
|---|---|
| `t2710_probe_plugin.py` | 観測 wrapper、条件別選択、B reorder、worker/controller 記録 |
| `t2710_probe_runner.py` | 条件列、session 作成、env/temp、pytest subprocess、成果物退避、selftest 入口 |
| `t2710_probe_analyze.py` | phase/span 集計、対比較、歴史分布照合、model 表 |

3 file は親が実走前に repo 外へ退避し、repo から除く。probe の逐語・hash は insight に保存する。author を分割して同じ plugin と集計仕様を並行編集する必要はない。

段 6 review は **数値の独立再計算 1 本**とする。特に、report duration と JUnit の定義、中央値の計算順、nested span の二重計上、C の allocation/実行集合差、B の実配布、最忙 worker と最長 node の一致を確認する。fix は指摘が実在した場合だけ追加する。

全体の子は plan 1、consult 2、author 1、review 1 の **5 本＋必要時 fix**。本 plan 内では子を起動していない。

## 親 brief への異議と D357 の射程

- **P1 は限定付きで採用。** replica A×3 は、条件を固定すれば「replica A の同一 tip・同一条件3走」を満たす。しかし実受入全体の D357 適合実測に代用できない。実受入 wall の改善を主張するなら、実受入形で各比較条件を同一 tip で3走以上取る必要がある。今回の実装ゼロ・設計資料という成果なら replica に限定して完了可能。land の1走は受領証であり較正の補助観測まで。
- **P2 の C は診断条件。** 最長 node 除外を分割・縮約効果の無条件な上限とする表現を修正する。
- **P3 の算術 model は採用。** 共通 base の初回担当変更、複製の重複、他 node への律速移動を含む前提を明記する。
- **P4 は名前を修正。** shard 固定費は残差、node 固定費は変動する fixture・終了処理費であり、一定値ではない。A−S は競合の因果効果ではない。
- **P5 は追加観測が必要。** 純粋な lock 待ちには T:922 の flock 観測が要る。5 wrapper だけなら管理時間と分離不能。
- **P6 は実装位置と queue model を修正。** collection-finish 後段を使い、LS:374–379 の cardinality sort と LS:332 の追加配布条件を織り込む。
- **前提資料を訂正。** 93 session の例外最長 node は `test_historical_oracle_nonadapter_reaches_current_semantics`（V の一覧:68、104）。brief:31 の g7 と一致しない。single_defects の verify 回数は ccbench-current=5、known-artifact=2、holdout-artifact=2、unknownness-layer2=1（T:1898–1921）。env 名も前述の定数に訂正する。
- **追加 scope は限定。** 観測と集計の修正だけとし、fixture 高速化、成分変更、hold 復帰、8条件整備、production gate・台帳追加は行わない（D2068、D2121、D2128、第22回項3）。

## 総括

**replica 方式は (i) を推奨する。** 本物の acceptance plugin で選択・report・既存確認を維持し、計測 session は終了後に job dir へ退避する。C の report は元 allocation を保持した診断資料として扱う。

**条件は S1/S/A/B/C 各3走、compute は4 job の逐次実行を推奨する。** job 1 は S1×3＋S×3、残りは A/B/C の Latin square。予約用見積は実行合計 **93〜135分程度、queue 待ち別**、walltime 予約は **90＋60×3＝270分**。S1/S の時間は未実測である。

親 brief の主要修正は、B の hook 順序と scheduler の cardinality sort、純粋な lock 待ちの観測追加、C の「上限」表現、A−S の因果解釈である。**replica×3 と歴史分布への包含だけで、実受入全体の D357 適合や改善を証明したとは言えない。**

予算は **Codex 子5本＋必要時fix、計測4 compute job・15 pytest走**。別途、段9の land 前受入1 session を行う。実受入3反復は今回の既定予算に加えず、結論を replica における実測・model・未採用の裁定パッケージへ限定する。