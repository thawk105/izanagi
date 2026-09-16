## 前提の検算 (brief・plan の記述と現物のずれ)

指定資料は読めた。静的確認のみで、編集・git 状態変更・pytest・build・benchmark は実施していない。以下の略記を用いる。

- `brief`：[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2644-ss2pl-wfg-connect/s1-brief.md)
- `plan`：[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2644-ss2pl-wfg-connect/artifacts/dev-wave-t2644-ss2pl-wfg-connect/s2-plan.md)
- `patch`：[ss2pl-lock-protocol-study.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2644-ss2pl-wfg-connect/patches/ss2pl-lock-protocol-study.patch)
- `runner`：[run_ss2pl_lock_study.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2644-ss2pl-wfg-connect/tools/pegasus/run_ss2pl_lock_study.py)
- `dispatch`：[dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2644-ss2pl-wfg-connect/tools/pegasus/dispatch_compute.py)

**1. 現 plan のままでは generic 子の PBS 確認で停止する。**

- **所見：** 最優先の不成立点は `PBS_JOBID` の輸送欠落。plan は実走 entry で環境変数を要求するが、generic の clean env はそれを削除する。
- **現物の根拠：** `plan:225–227`、`runner:3039–3042`。`dispatch:154–159` は clean env・空 allowlist、`:349–360` の保存対象に `PBS_JOBID` はない。`:1623–1633` でも復元しない。
- **成立条件：** 実 PBS job ID を子へ届ける具体的な経路が必要。親の shell で export するだけでは届かない。
- **影響：** clone、build、benchmark の前に停止し、検証器へ到達しない。
- **是正案：** 段 4 で輸送方式を確定する。既存 dispatcher が作る `compute-visible.json` を当該 submission の絶対パスで probe に渡し、その実 job ID を occasion に使う方式なら、新しい台帳や dispatcher mode は不要。環境変数必須という plan の記述も、この実値の取得方式に合わせる。架空の ID は設定しない。

**2. brief の実測事実は、今回の完走を保証しない。**

- **所見：** 各実測の射程を分ける必要がある。また射影された原報告は「高競合点で 6 node」と記すが、その 6 node の逐語 graph 自体は含まない。
- **現物の根拠：** `brief:46–50,66–72,82–84`。`verbatim-report-cycle.md:3–14` は高競合点の表と、本命点の 2 node・片側の辺までの抜粋。`runner:2947–2964` の thirdparty 検査は pin/cleanliness、`:814–817` は patch 適用可能性を確認する。
- **成立条件：** hydrate/pin 一致はソース束縛、prefix 実在はパス存在、apply-check は適用可能性、QUE 0 はその時点のキュー状況として扱う。
- **影響：** これらから依存解決・link・計算時間・今回の閉路成立まで保証すると、未到達や未観測を見落とす。
- **是正案：** 改版後の実 gate/build/run を根拠にする。過去の 6 node 報告は動作点選定の理由に限定し、今回の D791 証拠の代用にしない。`runner.hh:98–100` のアンカー誤りは plan の訂正どおり `:296–299` に直す。

## 1 走の到達性の鎖

**3. clone→gate→configure→build は、plan の独立 stock clone が必須。**

- **所見：** 主経路の設計は成立する。ただし `clone_network_free(canonical, ...)` の `canonical` は dict ではなく `Path(canonical["path"])` と明記すべき。
- **現物の根拠：** `runner:782–817,1928–2043,2091–2148`。`condition_meaning_gate.py:807–843` は stock/source 同一を拒否し、`:1864–1900` は requested/control の configure を行う。`plan:229` は引数を略記している。
- **成立条件：** pinned-clean canonical、未作成の clone 先、patch 適用済み source、未適用 stock、4 軸 gate の admission、configure 成功、target build 成功、compile definitions と binary SHA の収集が順に必要。
- **影響：** stock の代用、dict の直接渡し、古い build directory の再利用のいずれでも benchmark 前に停止する。
- **是正案：** production と同じ `Path(canonical["path"])` を両 clone 呼出しへ渡し、UUID attempt 下の別 directory を使う。gate と `_configure` の両方へ同じ依存 prefix/root を渡す。

**4. hang 時の stdout 必須入力は、plan の修正で揃う。終端 metrics は不要。**

- **所見：** brief の「5 件目」以外に、phase1 admission が要求する未補修の終端出力は見つからなかった。ただし file flag 不在の現状では workload 表示前に失敗する。
- **現物の根拠：** `patch:2196–2198,2653–2662`、`external/ccbench/include/ycsb.hh:206–211`、`runner:2173–2208,2507–2567,2856–2872`。
- **成立条件：** 各入力の扱いは次のとおり。

  | 入力 | hang 時の状態／必要な対応 |
  |---|---|
  | requested/observed cache、compile definitions | build receipt 由来。正常な build 完了が前提 |
  | 4 軸の `ShowOptParameters()` 行 | 現状は join 後で欠落。plan の起動時呼出しが必要 |
  | `#FLAGS_ycsb_*` 5 行 | DB 構築・watchdog 起動前に `endl` 付きで出る |
  | workload 行の形式 | `#FLAGS_name:\tvalue` は parser の regex に一致。0 と 0.0 等は canonical 化される |
  | binary SHA | 終了後も binary が存在し、build 後に変わっていないこと |
  | WFG snapshot 3 枚 | 現状は stdout にない。compact event と holder 証拠の追加が必要 |
  | 終端 throughput/abort/actual_extime | phase1 は `require_metrics=False` なので不要 |
  | `#ss2pl_thread_commit_counts` | `require_thread_commits=False` なので不要 |
  | durable final file | plan 上は副次成果物。欠落しても stdout 判定の代用・必須条件にしない |

- **影響：** 起動時軸行、出力先 flag、stdout event のいずれかを落とすと、admission または閉路受理に到達しない。
- **是正案：** `chkArg()` 直後の WFG 条件付き `ShowOptParameters()`、既存 workload 表示、trial 固有 flag を採用する。metrics/thread commits を追加要求しない。

## stdout の回収

**5. 64 KiB 超は、それだけでは pipe deadlock の理由にならない。**

- **所見：** `communicate(timeout)` は待機中も stdout/stderr を回収する。全出力が pipe 容量内に収まることは必要条件ではない。一方、plan に総量の見積りがない。
- **現物の根拠：** `runner:2684–2716`、`plan:65–86`、`patch:2264–2282,2494–2521`。compact schema を用いた文字列長計算では、48 nodes/48 edges、12 桁 hex、短い counter の例で次となる。これは実 C++ 出力の実測ではない。

  | held entry 総数 | 1 枚 | 3 枚 |
  |---:|---:|---:|
  | 48 | 15,137 bytes | 45,411 bytes |
  | 100 | 17,425 bytes | 52,275 bytes |
  | 432（各 node 9 件の保守的見積り） | 32,033 bytes | 96,099 bytes |

  起動行はさらに数百 bytes 程度。100 records の排他保持では安定した実 holder 総数は records 数に制約されるが、registry の過渡状態まで含む厳密な上限には使わない。
- **成立条件：** 親が回収を継続すること。親の停止・極端な scheduling 遅延などで未読 bytes が容量に達した場合に子の write が block する。実 pipe 容量を常に 64 KiB とも仮定しない。
- **影響：** 「3 枚が 64 KiB を超えるから必ず停止」「以下だから安全」のどちらも誤り。
- **是正案：** 回収の根拠を `communicate()` の並行 drain に置く。P6 の「計 3 枚」は訂正し、閉路変化があれば停止までの総出力が増えることも明記する。

**6. flush 済み行の回収と、完全な 3 行の生成は別条件。**

- **所見：** stdout 一次案は妥当。ただし SIGTERM は watchdog だけを残さず、process 全体を終了させる。
- **現物の根拠：** `runner:2689,2699–2705` は新 session と process-group signal。`patch:2523–2546,2664–2689` は watchdog が同一 process 内の thread で、stop が benchmark 後にある。workload 表示と既存軸関数は `endl` を使用する。
- **成立条件：** 改行までの `fwrite` と `fflush` が完了し、他 writer が行を破断していないこと。SIGTERM/KILL 中の最後の行や、未 flush の `cout` 内容は失われ得る。
- **影響：** watchdog の終了処理や `ss2pl_wfg_stop()` に回収を頼ると、hang 時の証拠が欠落する。
- **是正案：** snapshot コピー後に registry mutex を解放し、plan の writer 排他と flush を実施する。自然終了時の main 出力は `cout_mutex` で一括排他されるとは限らないため、その場合まで「必ず非混在」と主張しない。

## 計算ノード環境

**7. scratch と interpreter/toolchain を具体値にする必要がある。**

- **所見：** `<scratch-root>` と `<job-dir>` が未確定。wave job directory と dispatcher submission directory を区別しないと書込みに失敗する。
- **現物の根拠：** `plan:211–218`。`dispatch:273–281` は submission directory を read-only mount、`:1622,1670–1673` は cwd を投入元 repo にする。`runner:33` が import する `condition_meaning_gate.py:58` は `slots=True` dataclass。
- **成立条件：** probe は `python3.10 -B` で起動し、scratch/output は submission directory 外へ置く。generic は `PYTHONPATH`、`LD_LIBRARY_PATH`、`TMPDIR` 等をそのまま保存しない。
- **影響：** Python 3.9 なら import 段階、read-only 配下なら mkdir/結果保存段階で停止する。
- **是正案：** `--scratch-root` は wave job directory 下の専用 scratch に固定する。condition gate 自身の `TemporaryDirectory` は別途通常 `/tmp` を使う点を記録する。selftest も明示的に Python 3.10 で起動する。

**8. prefix/pin が揃っても、40 分で完走する根拠にはならない。**

- **所見：** plan の「保証できない」は正しいが、「数分〜数十分」は未測定。configure は target 用の 1 回だけではない。
- **現物の根拠：** `runner:1947–1956,1992–2029,2129`。gate は各軸について requested/control の configure を行う。`condition_meaning_gate.py:302,1868–1900` は個別処理の 120 秒 timeout。runner の clone は各 300 秒、configure は 600 秒、build は 1,800 秒。
- **成立条件：** clean PATH 上の `c++`/`cmake` が利用可能で、prefix に必要な package/config/library が揃い、全前段＋60 秒走行＋収集が 2,400 秒未満に収まること。
- **影響：** build が上限近くまで使えば、PBS が Python の例外処理や結果保存より先に終了させ得る。
- **是正案：** prefix は既存の `-DCMAKE_PREFIX_PATH=gflags;glog`、thirdparty は既存の 3 本の `FETCHCONTENT_SOURCE_DIR_*` と disconnected 引数に渡す。clone/gate/configure/build/run の所要を分けて残し、時間不足は当該段階の未完了として扱う。既存 stage deadline を使う場合も、benchmark の 60 秒より短い残時間で切られたものを D791 の hard timeout に読み替えない。

## probe と production の差

**9. 実走 probe は下位 production 経路を測れるが、study 全体は測らない。**

- **所見：** plan の実走には関数 stub がない。差は入口の再構成と周辺処理の省略にある。F29 の記録は以下まで具体化すべき。
- **現物の根拠：** `plan:225–280`、`runner:3026–3130,2846–2903,531–550`。
- **成立条件：**

  | 差分／模擬箇所 | `accepted_cycle` への影響 |
  |---|---|
  | clocks/jobs/PBS 確認、occasion の組立てを probe で再実装 | schema 上は閉路判定に使わないが、実行場所・到達性を変え得る。PBS 問題は要修正 |
  | stock/patch clone、gate、build、trial は実関数 | stub しなければ対象経路そのもの |
  | high-contention 1 trial だけ選択 | 各 trial の述語は同じ。12 trial と観測機会・結果分布は異なる |
  | 性能 build/inert witness/isolation/plot を省略 | 同じ snapshot に対する述語は変わらない。実行順・温度・外乱は発生状況を変え得る |
  | production の stage deadline/cleanup/全体 receipt 検証を省略 | 同じ証拠の判定は変わらないが、完走・保存・全体受入の意味が異なる |
  | Python unit test の `_run_process` 差替え | stdout、timeout、returncode を合成するため受理値を直接決め得る |
  | `--selftest` の合成 snapshot | parser/述語の確認だけ。C++、signal、flush、build は未検証 |

- **影響：** probe 成功を full controls、I1、D790、実 subprocess 回帰の成功まで拡張すると過大報告になる。
- **是正案：** この表相当の差を probe 結果の説明に残す。selftest 分岐は依存 path の strict resolve・PBS 確認・書込みより前に置き、実走用 argparse 引数を selftest でも必須にしない。

**10. plan が求める「実 stdout の確認」は、現在の trial 戻り値だけではできない。**

- **所見：** `_run_phase_trial()` は stdout/stderr 本文を返さない。例外時は snapshot や hash も受け取れない。
- **現物の根拠：** `runner:2859–2868,2885–2902` は本文を内部保持し、戻り値には hash と抽出済み証拠だけを入れる。`plan:268,308,365–367` は例外時保全や実出力確認を想定する。
- **成立条件：** production trial をそのまま呼ぶだけなら、保全できるのは戻り値と durable file。壊れた stdout 行は `_json_events()` に捨てられる。
- **影響：** 「閉路未観測」と「event の行破断・schema 不一致」を事後に切り分けられない場合がある。
- **是正案：** 段 4 で既存 trial scratch への stdout/stderr 保全を今回の収集変更に含めるか確定する。含めない場合は、probe が逐語 stdout や失敗時 admission 入力を保全できるという記述を削る。durable 1 枚を stdout 3 枚の代用にしない。

## runner 変更の閉包

**11. phase1 の追加 blocker は見当たらないが、JSON 型の確定が必要。phase2 は依然失敗する。**

- **所見：** top-level event 案なら conflict 読取りと整合する。layout 欠落は非致命的。`wfg_output` は現 trial/admission field と衝突しない。
- **現物の根拠：** `runner:2291–2332,2476–2504,2507–2567,2873–2902`。condition gate receipt は `:2039–2043` で JSON 値に変換済み。
- **成立条件：** `conflict_count` は非負整数、receipt の path は `str`、SHA は文字列、file 本文は JSON decode 後の値、例外は type/message の文字列にする。`Path`、raw bytes、例外 object を直接入れない。
- **影響：** 型が曖昧なままだと計測後の `json.dump` で失敗する。phase2 は正常終了しても `acquisition_paths` 不在で `ContractError` となる。
- **是正案：** `wfg_output` の型を確定し、`invalid_json` には UTF-8 decode 失敗も含める。phase1 一走には `validate_phase_matrix()` を呼ばない。同関数は 12 trial を要求する。phase2 では DLR1 の `publish_wait` が無効で、terminal file も stdout counter event の代用にならないことを明記する。

## 変異の帰属

**12. 変異表には KILLED の帰属を直すべき行がある。**

- **所見：** C++ 変異を固定 Python fixture で検出できないという plan の限定は正しい。一方、counter drift の期待 node と、旧 mode 名の個別拒否の一般化は不正確。
- **現物の根拠：** `plan:180,288–308`。`runner:2358–2392,2441–2472` は `.get()` で mode を比較する。
- **成立条件：** 各変異について成立する期待は次のとおり。

  | 変異候補 | 静的に成立する帰属 |
  |---|---|
  | fixture の `compatible` 削除 | 正例の受理 assertion が赤 |
  | `held_locks` 削除 | 主張枝を追加しなければ正例が赤 |
  | `wait_lock_id` 旧名化 | edge lock と一致せず正例が赤 |
  | edge 端点の旧名化 | holder/waiter lookup 失敗で正例が赤 |
  | holder lock ID/mode 不一致 | 一致する別 held entry がなければ正例が赤 |
  | 2 枚目 counter 増加 | **正例**が赤。拒否を期待する counter-drift 負例は赤になる理由がない |
  | read/read 化 | request/node/holder/held の整合も保って read/read にすれば正例が赤 |
  | runner の flag 削除 | fake process が受け取った argv から flag を必須抽出すれば配線 test が赤 |
  | path 固定 | 2 回の path 非一致 assertion が赤 |
  | file JSON/SHA 収集削除 | 両 field を明示比較すれば赤 |
  | 性能 argv への flag 追加 | 実性能関数の argv を観測する test なら赤 |
  | fixture の起動軸/workload 行削除 | 終端行や別 fixture が補完しなければ admission 正例が赤 |
  | C++ emit/field/held 削除 | 固定 fixture test は検出しない。実出力で観測する必要がある |
  | C++ 起動軸呼出し削除 | hang 実走では admission 失敗。自然終了時は終端行が補完し得る |
  | C++ mode 正規化削除 | read/read 辺を含む実閉路に限り差が現れる |

- **影響：** counter-drift 負例を KILLED node に指定すると、変異が生存しても異常ではない。また node/edge 両方の `request_mode` だけを同時に旧名化すると、`None == None` となり、write holder の正例は受理され得る。
- **是正案：** KILLED node を正例側へ訂正する。旧 field 一括拒否と各 field 個別拒否を同一視しない。検証器を変更しない今回、その既存限界を記録する。

**13. `_extract_snapshots` の受理形変異が表から抜けている。**

- **所見：** 今回選ぶ top-level 枝を失う変異は Python test で確実に検出できるが、すべての受理形変更を検出できるわけではない。
- **現物の根拠：** `runner:2347–2355`、`plan:176,288–306`。
- **成立条件：** 固定 fixture を top-level `event:"wfg_snapshot"` のまま実抽出器へ通し、snapshot 数 3 と受理を assert すること。
- **影響：** top-level 枝削除は赤になるが、未使用の nested 枝削除や、現 fixture を引き続き受け入れる変更は生存する。
- **是正案：** 「top-level 枝を削除して nested-only にする」を具体的変異として記載する。C++ emit 削除で `accepted_cycle=None` となっても、未観測を許す probe の exit code は必ずしも赤にならないため、観測差と KILLED を分ける。

## 実装子へ渡す確定値 (段 4 へ返す)

**14. serializer の大半は確定している。残る選択肢を閉じる。**

- **所見：** plan の schema、mode、held 範囲は実装可能な粒度。terminal tick の任意性、probe の置き場、scratch/PBS/本文保全が未確定。
- **現物の根拠：** `plan:43–72,90–103,118–151,204–282`、`brief:60–64`、`patch:523–527,2432–2492`。
- **成立条件：** 段 4 では次を明示する。

  | 項目 | 推奨確定値 |
  |---|---|
  | cycle schema/event | `ss2pl-wfg/v2` / `wfg_snapshot`、top-level nodes/edges |
  | cycle tick | C++ `uint64_t`、JSON integer、最初の観測 tick を 1、閉路なし tick も加算 |
  | terminal tick | `null` に固定。「付ける場合」は残さない |
  | durable cycle | 最後に emit した同一文字列。再 snapshot しない |
  | node 範囲 | 選択閉路の thread のみ |
  | `held_locks` 範囲 | 同一 snapshot 内の各対象 worker の held 全件 |
  | mode | `IMPL=1 && KIND=0` は全箇所 `"write"`、その他は既存 read/write |
  | 起動軸行 | YCSB main の `chkArg()` 直後、WFG 条件内で既存関数を呼ぶ |
  | file receipt | `wfg_output`、path は string、raw bytes は SHA 算出だけに使用 |
  | probe 配置 | plan に合わせ job directory に直接作成するか、brief の repo 一時配置を採るか一本化 |
  | scratch | wave job directory 下。dispatcher submission directory 外 |
  | argv | `python3.10 -B`、既定 5 workload 値のうち tuple=100/skew=0、48 threads、extime=10、timeout=60 |
  | canonical clone 引数 | `Path(canonical["path"])` |
  | PBS identity | 当該 submission の既存 compute marker を読む具体的引数・パスを確定 |
  | stdout/stderr 保全 | trial scratch に保全するか、probe の確認範囲を戻り値までに限定 |

- **影響：** 未確定のまま分担すると、probe と runner の接続・成果物収集で実装者間の解釈が割れる。
- **是正案：** この表を段 4 の確定事項として実装子へ返す。排他 mode 正規化は実 lock の意味を表す修正として採用し、Python の受理条件は変更しない。

## 総括

- **所見：** plan の主要な接続案は成立するが、**現状のままでは generic 子に `PBS_JOBID` が届かず、1 走へ到達しない**。次に重要なのは stdout 本文の保全範囲と、40 分枠の時間予算である。
- **現物の根拠：** `dispatch:349–360,1623–1633`、`plan:225–282`、`runner:2684–2716,2846–2903`。
- **成立条件：** 実 job ID の輸送、書込み可能な scratch、Python 3.10、実 gate/build、起動軸・workload 行、完全な stdout event が揃うこと。
- **影響：** 未修正なら前段停止、修正後も未観測・証拠欠落・時間切れを区別しなければ、接続の成否を誤判定する。
- **是正案：** 段 4 で上記確定値と変異帰属を修正してから実装へ進める。本レビューでは実走成功も、閉路受理成功も確認していない。