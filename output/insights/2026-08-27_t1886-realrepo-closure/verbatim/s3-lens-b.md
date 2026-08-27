## 総括

最重所見は、T-1886 の「新しい細分化」が D1008 で既に実装され、D1103 では K=3 が単体テスト床へ到達したと裁定済みなのに、本 wave の新規効果として扱っている点である。  
ledger は suffix 正規化後 258.92 秒だが、parametrize ID も正規化すると 93 instance・266.32 秒で、欠落 family は 0 件になる。  
ただし ledger には走行 regime・相・outcome・shard 来歴がなく、266.32 秒も現在の排他鎖長や wall 短縮量ではない。  
D358(a)(b) は生存、(c) は重複自体は生存するが却下理由としては D1008 が反証済み。テストや A/B は実行していない。

## 所見

### 1. BLOCKER: T-1886 に新しい介入がなく、効果を本 wave へ帰属できない

- **所見:** brief は「単一 `real-repo` group の新規細分化」を成果としているが、現行コードは process memo 4 本以外の suffix を既に除去している。plan もこれを認識し、実装を閉包補修へ置き換えている。したがって本 wave が実装する新しい性能介入がない。

- **根拠 file:line:** `brief.md:5-9,40-41,73-74`、`s2-plan.md:3-6,11-18,304-310`、`orchestrator/tests/conftest.py:1702-1718,1811-1823`。さらに D1008 は資源別 RW lock と suffix 除去を既決定している (`docs/decisions.md:35294-35336`)。D1103 は現行 `real-repo` が 40 worker へ分散し、K=3 が単体テスト床へ到達したと実測済み (`docs/decisions.md:37240-37254`)。

- **成果物影響:** レポートの「本 wave による細分化前後の短縮量」は正当な新規値を持たず、T-1886 の台帳状態を本 commit で「達成」とすると既存 D1008 の効果を二重計上する。certified 選択集合自体は変わらない。

- **提案:** 段4で T-1886 を「D1008/D1103 により先行達成・本 wave では追加介入なし」と整理し、wave を T-1936 の閉包補修へ縮退する。新しい性能効果も要求するなら、D1008 より先へ進む具体的な操作をユーザー裁定で先に定める。

### 2. ledger 算出は erratum 後も parametrize instance を落としている

- **所見:** erratum の 258.92 秒は suffix のみ正規化した値として再現した。しかし「ledger に無い」2 family は、実際には計5個の parametrized key として存在する。instance-aware 合計は次のとおり。

| access | map family | ledger instance | 合計 |
|---|---:|---:|---:|
| `(read, read)` | 52 | 54 | 221.641 s |
| `(read, None)` | 28 | 29 | 40.922 s |
| `(None, read)` | 6 | 6 | 3.567 s |
| `(read, write)` | 3 | 3 | 0.000 s |
| `(None, write)` | 1 | 1 | 0.190 s |
| 合計 | 90 | 93 | **266.320 s** |

共有 lock の instance は 266.130 秒、writer は 0.190 秒なので「ほぼ全量が共有」という向きは維持される。

- **根拠 file:line:** erratum の欠落主張は `brief-erratum.md:3-13`。`test_m3_focus_artifact_directions` は3 key・7.40秒 (`acceptance_duration_ledger.json:4073-4075`)、protocol builder は2 key・0秒 (`:13132-13133`)。suffix 付き writer は `:14854`。runtime 正規化も `]` より後の `@` だけを suffix とする (`conftest.py:1258-1300`)。

- **成果物影響:** 分析レポートの合計は **258.92 → 266.32秒**、ledger 欠落 family 数は **2 → 0**、対応 instance 数は **90 family → 93 instance** に変わる。ledger ファイルそのものや certified 選択結果は変わらない。

- **提案:** 集計単位を「登録 family」と「ledger instance」に分ける。対応付けは path basename、function の parametrize suffix、末尾の loadgroup suffixを別々に正規化し、複数 instance を全て加算する。

### 3. ledger だけでは setup/call/teardown、skip、shard regime を判定できない

- **所見:** ledger schema は nodeid、秒、件数しか持たず、commit、host、toolchain、K、shard、outcome、setup/call/teardown の内訳がない。したがって 0.0 を「速い」「skip」「未実行」のどれとも ledger 単体では確定できない。login で slow writer 3本が skip されたことは erratum の親実測からのみ言える。

- **根拠 file:line:** schema は `acceptance_duration_ledger.json:1-2,17672-17675`、validator も非負有限 duration だけを見る (`conftest.py:1131-1168`)。現在の shard telemetry は全 `pytest_runtest_logreport` の duration、すなわち発生した setup/call/teardown report を加算する (`acceptance_shards.py:799-809,913-926`) が、それがこの ledger の生成元だったという来歴は格納されない。D1052 も来歴不在と分析用途限定を明記する (`docs/decisions.md:36280-36290`)。

- **成果物影響:** レポートに「writer 3本は0秒」や「この K=3 受入の鎖は266.32秒」と書くと未証明値になる。compute regime では writer 3本の所要が未知なので、排他比率と予測 wall も未確定のままである。

- **提案:** ledger 値は「来歴なしの分析値」と明記する。性能主張には別 evidence として commit、K、host/toolchain、各 node outcome、相別 duration、selection digest を保存する。ledger schema の変更は D1052 を覆す裁定なしには行わない。

### 4. D600 を満たす A/B は plan の「1組」では不足し、しかも現状は既存 D1008 を再測定するだけ

- **所見:** suffix strip 有効対無効は対象を実際に除外するため因果的 A/B にはなる。しかし plan/brief は1組だけで、走間変動を分離できず、さらに介入自体が既存 D1008 なので本 wave の増分効果を示さない。

- **根拠 file:line:** `brief.md:71-74,125-126,139-142`、`s2-plan.md:304-310`。D600 は occupied span を因果指標として拒否し、実際の除外 A/B と複数 paired run を再訪条件にする (`decisions-verbatim.md` D600)。D1008 には既に対象21 nodeの直列145.79秒対並列54.83秒と結果集合一致がある (`docs/decisions.md:35329-35331`)。

- **成果物影響:** 1組だけならレポートの短縮秒・倍率は provisional に留まり、certified 選択結果や着地根拠には使えない。T-1936 の閉包補修を T-1886 の短縮量として記録することもできない。

- **提案:** T-1936 単独へ縮退するなら性能 A/B を成果条件から外す。なお新規細分化が別途裁定された場合の最小計画は、同一 compute allocation で5本程度の非skip SH nodeを事前固定し、最終 tip対「suffix strip だけを無効化した control」を `AB/BA` の2 pairで比較する。全 arm は `tools/run_tests.py`、xdist/loadgroup のまま実行し、`-n0` は使わない。各 arm 75秒、全体285秒の hard capとし、selection・outcome集合不一致またはtimeoutなら効果主張を棄却する。

### 5. D358 は (a)(b) 生存、(c) は「存在」と「却下理由」を分ける必要がある

- **所見:**  
  (a) 生存。real-repo node から `GIT_OPTIONAL_LOCKS=0` なしで起動される Git が複数残る。  
  (b) 生存。plan 自身が brief 外の `current_commit_snapshot` を追加発見しており、閉包は実装・負例完了前には確定しない。  
  (c) worker 跨ぎ再構築は存在するが、wall を悪化させる却下理由としては D1008 が「構築費は並列に払われ累積しない」と実測で退役させている。

- **根拠 file:line:** protocol builder の `git ls-tree` は環境指定なし (`test_s8b_protocol_builder.py:70-80`)。known axes (`s1_known_axes_freeze.py:186-193`)、measurement freeze (`s1_measurement_freeze.py:104-113`)、Codex helper (`tools/codex_reasoning_ab.py:428-453,3598-3611`) も同様。plan の判定は `s2-plan.md:220-268`、追加穴は `:112-120`。D1008 の fixture 実測は `docs/decisions.md:35343-35350`。

- **成果物影響:** (a)(b) を退役済みと記録すると、共有 reader 同士または登録外 fixture と writer の競合で pytest rc、failures、certified 着地可否が変わりうる。(c) を生存する速度 blocker と記録すると、レポートのボトルネック説明だけが誤る。

- **提案:** 最終 decision fragment は `(a)=alive`, `(b)=implementation verifiedまでalive`, `(c)=重複は存在するがD1008によりwall却下理由としてsuperseded` と分離する。P6 の「(a)(c)失効」は採用しない。

### 6. D1035 の差分は条件内だが、複数 shard group 化は条件外

- **所見:** plan の最終案である common-dir lock key、T810 SH、candidate setup EX・yield SH、全 long-lived fixture の canonical `real-repo` shard group統合は、排他を強めるか同値に保つため D1035 の内側である。排他を弱める操作は名指しできない。ただし brief の「access classごとの複数 group」をそのまま実装すると条件外になる。

- **根拠 file:line:** plan の lock設計は `s2-plan.md:85-95,122-172`。allocator は file と marker groupだけを unionし、資源衝突を知らない (`acceptance_shards.py:288-320`)。K=3では別 componentを別 shardへ置きうる (`:323-385`)。closure gateも file/group閉包しか検査しない (`:388-410`)。shard pluginは suffix strip前の markerを記録する (`:679-705,762-789`)。

- **成果物影響:** 別 group名へ分けた競合 node が異なる compute process・hostへ配置されると `/tmp` flock は届かず、`assignment_closure` が緑でも pytest rc・failures・terminal countsが競合順で変わる。

- **提案:** shard層では全競合 nodeを canonical `real-repo` 一群へ残し、同一 shard確定後にだけ runtime suffixを除去する plan を維持する。`_validate_real_repo_shard_state` を fixture nodeまで広げ、別group名による細分化は採らない。

### 7. `tools/run_tests.py` を触らない判断は妥当で、目的達成の阻害要因ではない

- **所見:** D838 の blob同一性により変更すれば land不能となる。一方 runnerの役割は loadgroup指定までで、nodeid suffix、lock、shard markerは conftestとshard pluginで制御できる。T-1936 の閉包補修は runner変更なしで達成可能である。

- **根拠 file:line:** land gate は tested main/tipのrunner blob一致とreceipt hashを要求する (`tools/dev_wave_land.py:1065-1087`)。runnerは `-n` と `--dist loadgroup` を追加するだけ (`tools/run_tests.py:550-572`)。内部 shardも同じ command builderを使う (`:1479-1533`)。D1103もK=3注入を waiter側へ置きrunner既定を変えない (`docs/decisions.md:37224-37236`)。

- **成果物影響:** runnerを1 byteでも変えると acceptance receiptが拒否され、certified commitの着地値は passからrejectへ変わる。触らなければ本 wave の成果物値に悪影響はない。

- **提案:** `tools/run_tests.py` は完全凍結する。A/B controlも runner option追加ではなく、同一runnerを使う conftest側の比較 tipで作る。

## 既裁定の見落とし

`decisions-verbatim.md` 外で本 wave を直接縛るのは次の3軸である。

- 資源別RW lock・suffix strip・fixture重複費の評価: D1008 (`docs/decisions.md:35294-35354`)
- provenanceのない所要台帳を分析用途へ限定: D1052 (`:36280-36290`)
- K=3の配置条件、既存細分化の実測、単体床到達: D1103 (`:37224-37283`)

この3件を段4の裁定パッケージへ必ず入れないと、T-1886の新規性、D358(c)、測定対象の三点を誤る。

## scope 外だが real な裁定パッケージ候補

### 全 unprotected Git 経路を T-1936 に含めるか

- **所見:** brief の3穴を閉じるだけでは、ユーザー指定の D358(a) 退役条件を満たせない。
- **根拠 file:line:** `test_s8b_protocol_builder.py:70-80`、`s1_known_axes_freeze.py:186-193`、`s1_measurement_freeze.py:104-113`、`tools/codex_reasoning_ab.py:428-453,3598-3611`。
- **成果物影響:** 退役扱いなら decision/reportのD358状態が誤り、共有lock下のGit副作用が競合した場合は certified pytest rcも変わる。
- **提案:** 実装へ自動拡張せず、(A) 全 live Git経路へ optional-lock抑止を入れてT-1936を拡張する、または (B) D1008がD358(a)をsupersedeしたとして未抑止経路を受容する、の二択をユーザー裁定へ返す。

## nit

- brief の T810・predicates anchor drift は `s2-plan.md:20-24` で既に訂正されており、成果物値への追加影響はない。
- `tools/run_tests.py:2675-2677` の警告文は現在の suffix strip後の意味とずれているが、D838により本 waveでは変更しないのが正しい。