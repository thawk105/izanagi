## 総括

判定は **NO-GO**。段 2 プランのまま段 5 へ進めてはならない。

blocker は 2 件ある。

1. t080 host cache は、実 repository を worker ごとに再観測していた経路を、cache payer が作った凍結値へ置換する。cache key は live source、HEAD、submodule HEAD、Git-visible output を束縛せず、11 consumer も real-repo 排他台帳に入っていない。
2. snapshot 3 node の削除は、親の追加実測が明示した「共有実装と独立実装の対を残す」裁定に反し、独立 oracle を失う。

一方、worker の selected-file collection は段 2 が不採用としており、この判断は正しい。採用対象 L1-A/B/C は全量 collection を維持するため、現行の shard 間 universe 検査を直接は弱めない。ただし `_canonical_item` 一回化と worker digest 本数には補強が必要である。

L4 の autonomous 1 node と F176 1 node は、現行 source 上では同じ module、同じ入力、同じ production call、同じ assertion であり、実行被覆の差は確認できなかった。ただし `measurements.md` の「削除候補ゼロ」と矛盾するため、親の裁定なしに削除へ進めるべきではない。

必読 5 文書と対象 repo はすべて読めた。file 書き込み、pytest 実走、commit、branch 操作は行っていない。

## 閉包 gate の検出力への攻撃

現行 gate の検出対象は次のとおり。

- `assignment_closure_gate`
  - selected 間の nodeid 重複を拒否する。
  - selected の和集合が observed records の nodeid 集合と exact 一致しない場合を拒否する。
  - 同一 file、同一 `xdist_group`、宣言済み real-repo conflict edge が複数 shard に分かれる場合を拒否する。
  - 根拠: `tools/acceptance_shards.py:445-474`。

- `_observed_universes_gate`
  - shard ごとの `ItemRecord(nodeid,file,group)` の順序付き tuple が完全一致することを要求する。
  - nodeid だけでなく file と group の差も検出する。
  - 根拠: `tools/acceptance_shards.py:487-492`、発火箇所 `:651-657`。

- `_login_universe_gate`
  - login node の独立 collect-only nodeid multiset と shard universe の nodeid multisetを比較する。
  - file と group は比較しない。
  - 根拠: `tools/acceptance_shards.py:495-496`、発火箇所 `:661-663`。

- `_finished_gate`
  - `pytest_runtest_logfinish` で得た nodeid multiset と selected multiset を比較し、未実行、重複実行、別 node 実行を拒否する。
  - 根拠: `tools/acceptance_shards.py:499-500`、`:672-677`。

- `validate_report_evidence`
  - collection と selected が空でないことを要求する。
  - report 内の全 `worker_collection_digests` が、report の full `ItemRecord` 列から再計算した digest と一致することを要求する。
  - occupancy の worker 名、entry field、正の item 数、有限かつ非負の duration、item 総数と selected 数の一致を検査する。
  - selected が universe 内なら、`group_to_workers` の group 集合を selected records から再導出する。
  - group worker が実在 worker の非空部分集合で重複しないこと、JUnit path の exact 一致、terminal field の exact 集合と合計数を検査する。
  - 根拠: `tools/acceptance_shards.py:518-600`。

- `worker_collection_digests`
  - 各 worker は full records digest と selected digest を返す。`gw0` だけが full records と selected を返す。
  - controller は受信した records digest と selected digest がそれぞれ一値であり、full payload authority がちょうど 1 件であることを要求する。
  - 根拠: `tools/acceptance_shards.py:913-925`、`:928-952`。
  - 限界: production gate は digest の本数を 48 本に固定していない。`validate_report_evidence` は nonempty と値一致しか見ない。48 本を要求するのは追跡下の分析 consumer である `output/insights/2026-08-24_t1618-xdist-controller-cost/prepare_inputs.py:546-549`。

- `merge_reports`
  - 14 field exact schema、schema version、shard count/index、pytest rc、report と process rc の一致を検査する。
  - shard index と process index の exact 集合、observed universe、login universe、selected exact partition、assignment closure、finished、scheduler、rc 範囲を順に検査する。
  - 根拠: `tools/acceptance_shards.py:603-700`。
  - merge 後の JUnit は test 数を merged universe 件数と一致させる。根拠: `tools/acceptance_shards.py:704-739`。

### selected-file collection を採った場合の具体的な消失経路

段 2 はこの案を不採用としているため、現計画では発生しない。再開した場合は blocker になる。

攻撃入力は、collection が import 順、worker ID、shard 環境、または一時的な filesystem 状態に依存する test module である。

1. 軽量 preflight が一度だけ universe を作る。
2. その一度の観測で `test_x` が欠落する。
3. 同じ欠落 universe から shard file list と期待 node 集合を発行する。
4. worker は担当 file だけを collect し、発行済みの欠落集合と exact 一致する。
5. `selected == collected == finished`、partition、terminal count はすべて縮小後の集合に対して成立する。
6. login collection をその preflight で兼用すると、`test_x` は静かに消える。

現行では各 shard の worker が full universe を独立に観測するため、一 observer だけの欠落は shard 内 digest または shard 間 universe の差になる。根拠は `tools/acceptance_shards.py:826-852`、`:913-952`、`:651-663`。

また、selected nodeid だけの exact 検査では、worker が観測した `file` または `xdist_group` の差を検出できない。group marker が worker 固有に消えると node 集合が同じでも排他実行が変わりうる。補償 gate は nodeid だけでなく full `ItemRecord` を比較しなければならない。

### 現行 gate 自体の限界

source から test を削除し、ledger key と件数も同じ変更で消した場合、全 145 collector は縮小後 universe に一致する。この種の意図的な削除は closure gate では検出できない。`merge_reports` は「現行 universe が一貫して閉じている」ことを検査するが、「過去に存在した test が残っている」ことは検査しない。削除の正当性には別の node inventory または独立 oracle が必要である。

## 3 shard 独立導出への攻撃

現行の正確な構造は、controller collection ではなく次である。

- 3 shard それぞれの 48 worker が full universe を collect する。
- shard ごとの observed universe 本体は `gw0` が供給し、残り worker は full record digest で照合される。
- login node が別に collect-only を行う。
- 合計は 144 worker collection と login collection 1 回である。
- 根拠: `measurements.md:80-96`、`tools/acceptance_shards.py:913-952`、`:1243-1248`、`:1335-1351`。

採用対象の L1-A、L1-B、L1-C は full collection を維持すると明記されている。根拠: `s2-plan.md:128-170`、`:331-336`。したがって通常の安定した pytest Item に対して、3 shard の独立導出は失われない。

selected-file 案では、観測主体を 144 worker から数個の preflight に落とすため、次が失われる。

- worker 固有の collection 欠落。
- worker 固有の file 解釈差。
- worker 固有の `xdist_group` 差。
- import 順依存が full suite と部分 suite で変わる欠陥。
- 同一 shard 内で、gw0 以外の worker が異なる records を見たことの検出。

「3 preflight が同じ manifest を作った」ことは、「48 worker 全員が同じ universe を見た」ことの代替にならない。3 preflight が同じ環境依存欠陥を踏めば、相互一致は共通原因による一致になる。

提案は、段 2 の結論どおり selected-file collection を再開しないこと。再開するなら D634/D711 の supersede に加え、独立 login full collection、shard ごとの full `ItemRecord` producer、各 worker の full record 観測を置換できる証拠が必要である。担当 node 集合との一致だけでは同じ検出力にならない。

## fixture 共有の状態漏れ・恒真化への攻撃

### (a) 破壊的変異が次 test へ漏れる経路

具体例は submodule Git metadata である。

- t080 の test は返却 tree の known/holdout bytes を変更する。根拠: `test_s8b_oracle_driver.py:1476-1482`。
- submodule の checkout を別 commit へ動かす test もある。根拠: `test_s8b_oracle_driver.py:1494-1506`。
- receipt の変更、commit、revert、削除も行う。根拠: `test_s8b_oracle_driver.py:1802-1811`、`:1821-1825`。

cache base を `copytree(..., symlinks=True)` するだけでは、submodule 内の `.git` file が cache base の `.git/modules` を指したままになる実装がありうる。この場合、copy A で submodule HEAD を変えると copy B と cache base の HEAD も変わる。

段 2 は、regular file inode、bytes、Git HEAD、submodule HEAD、document deepcopy を別 copy と cache base に対して確認し、hardlink、共有 Git metadata、document 共有の変異を殺すと明記している。根拠: `s2-plan.md:200-223`。この部分は有効な非恒真 control であり、全件が実装されれば上の直接漏れは検出できる。

ただし publish 後の cache base 自体には完全性 seal が計画されていない。同一 uid の test が cache path を発見して書き換えられる限界も明記されている。根拠: `s2-plan.md:225`。最低限、publish 後を read-only 化し、copy 前に manifest digest を再検証し、検証値を cache 内の同じ mutable documentから作らないことを提案する。

### (b) live repository の再観測が凍結値へ変わる経路

これは blocker である。

builder は live repository から次を読む。

- `ROOT/orchestrator` 全体: `test_s8b_oracle_driver.py:1025-1029`
- Git-visible output: `:1031`
- known axes と実 receipt: `:1033-1058`
- current operational source: `:1077-1080`
- CCBench source と pin: `:1089-1095`

段 2 の basis key は `distinct_basis_blob`、final key は 4 引数だけであり、HEAD、source digest、output snapshot、submodule HEAD を含まない。根拠: `s2-plan.md:194-210`。最初の payer が時刻 T0 に作った base は、時刻 T1 の別 workerが live repository を再観測する代わりに再利用する。

さらに、11 direct consumer は `test_s8b_oracle_driver.py:941-1009` に固定されているが、real-repo resource inventory `conftest.py:258-390` にはこの 11 node が入っていない。したがって cache payer の live read は real-repo writer と排他的である保証がない。

攻撃シナリオは次のとおり。

1. payer が T0 に live source と output を cache へコピーする。
2. 別 worker の real-repo test が T1 に source、index、output、または submodule状態を一時変更する。
3. 後続 t080 node は live repository を読み直さず T0 cache を使う。
4. 変更が current builder の独立再観測で露見するはずだった場合でも、全 consumerが T0 の凍結値を使って通る。

提案は、D1104 と同型の unchanged-input gate を設けること。D1104 は共有評価の前後で HEAD OID を独立に比較して凍結の代償を補っている。根拠: `docs/decisions.md:37285-37306`。t080 では HEAD だけでは足りず、dirty bytes、Git-visible output、実 receipt、submodule HEAD を含む exact input snapshot を payer 前に束縛し、cache hit ごとに live input が不変であることを再確認する必要がある。これが高価すぎるなら host cache は不採用とする。

### (c) 独立 oracle の両辺が同じ共有値になる経路

攻撃実装は、cache manifest に記録した document、HEAD、digest を、cache product の実値と test の期待値の両方へ渡す形である。cache builder が誤った tree と誤った manifest を同時に作れば、`actual == expected` が恒真になる。

段 2 は cache control の期待値を literal sentinel、`git rev-parse`、`git status --porcelain`、path、inode から独立に作り、cache manifest から作らないと明記している。根拠: `s2-plan.md:216-223`。この禁止を守る限り、cache 隔離 test の直接恒真化は防げる。

既存 t080 test にも literal golden と独立 Git blob 観測がある。根拠: `test_s8b_oracle_driver.py:149-278`、`:1378-1424`、`:1543-1559`。

ただし二段 builder 分割全体について、旧 builder と新 builder の kill 集合を比較する計画がない。cache 隔離 test が緑でも、basis/final 分割が t080 verifier の意味を変えていないとは限らない。提案は、cache を無効にした旧相当 fresh build と host-cache build を同一入力に対して比較し、登録済み t080 変異の kill 集合、receipt bytes、Git tree、HEAD、submodule HEAD、document bytes を一致させること。比較の右辺を新 cache builder から作ってはならない。

## 恒真な保証の指摘

### `_canonical_item` の呼出し回数保証

[should-fix]

「呼出し回数が `len(items)` ちょうど」は高速化が発火したことしか保証しない。records、selected、loads の期待値も新 helper から導出すると恒真になる。

さらに現行は `_canonical_item` を records 作成時と identity map 作成時に二度呼ぶ。根拠: `tools/acceptance_shards.py:771-775`、`:832-843`。stateful な `nodeid` property または `iter_markers()` を持つ Item は、現行では二観測の不一致により deselect、finished、login、worker digest のいずれかで拒否されうるが、一回化後は最初の値がそのまま全経路へ流れて通る。

提案は、Item の path、nodeid、marker が安定していることを明示契約にするか、stateful synthetic Item の負例を置くこと。records の期待値は literal `ItemRecord` 列または変更前版から固定し、新 helper の出力を右辺へ使わない。

### prewarm の barrier 保証

[should-fix]

「最後の collection barrier 前に完了」は、同じ collection callback 内で thread を join する候補集合に構造的に含意されやすい。単なるイベント列の事後比較では、結果を早期 publish する変異、join timeout を無視する変異、thread 例外を遅れて落とす変異を殺せない。

提案は、意図的に停止する prewarm、scheduler の最初の dispatch spy、thread 例外、session 中断を組み合わせ、prewarm 未完了または失敗時に 1 test も開始しないことを観測すること。既存の同期例外伝播 test は `test_real_repo_serialization.py:4437-4547` にあるが、thread 化後の因果関係を直接は証明しない。

### host cache の root 相違保証

[should-fix]

「7 root がすべて異なる」は各 test の `tmp_path` が異なれば自動的に成立し、state 非共有の証明にはならない。inode、bytes、Git HEAD、submodule HEAD、document の破壊的 control は非恒真なので、root path test ではなくこちらを採否 gate にするべきである。

### `wall = busiest worker + residual`

[should-fix]

`residual` を `wall - busiest worker` と定義したうえで同式が成立すると述べるのは恒真であり、collection が原因だとは示さない。根拠: `measurements.md:6-18`。段 2 が `R_worker` と `R_outside` を走ごとに分ける設計へ修正した点は妥当である。根拠: `s2-plan.md:18-51`。

## 削除候補の被覆検証

### autonomous duplicate

現行 source では削除による実行被覆の減少は確認できない。

- `test_p3_role_invalid_partial_passes` は `_role_invalid_trial(tmp_path)` の結果を `_verify` へ渡す。`test_autonomous_trial_completeness.py:2019-2021`。
- `test_pre_raw_failure_allows_missing_raw_response_pointer` も完全に同じである。`:2274-2276`。
- 同じ module 内なので module 定数も同じであり、`_verify` は同じ production function を呼ぶ。`:2000-2003`。

実行命題は同じである。ただし境界を明示する名前は後者なので、削除するなら generic な `test_p3_role_invalid_partial_passes` を削除し、意味を表す後者を残す方が保守上安全である。

### F176 duplicate

削除による実行被覆の減少は確認できない。

- 両 parameter は入力 `"NO-GO。GOの条件を満たさない。"`、decision `"NO-GO"`。
- 両 test は `TOOL.score_text` に同じ prefix と本文を与え、`valid is True` と decision exactを検査する。
- 根拠: `test_codex_reasoning_ab.py:13236-13254`、`:13257-13317`。

param ID 以外は同一命題である。

### snapshot 3 node

[blocker]

現行 checkout だけを見ると、両 module の helper body は同一であり、`ROOT` も同じ repository root である。根拠:

- `test_s8b_oracle_driver.py:30-31`、`:565-653`
- `test_real_repo_serialization.py:34-36`、`:719-815`

しかし必読の親実測は、land 直前の peer が oracle-driver 側を共有 helper 実装へ移し、real-repo 側を旧独立実装として残すため、両方を独立 oracle の対として残すと明示している。根拠: `measurements.md:98-118`。

段 2 はこれに反して helper を一本化し、oracle 側 3 node を削除する。根拠: `s2-plan.md:258-268`、`:353-356`。

攻撃シナリオは次の二択になる。

- peer topology を保ったまま oracle 側を削除すると、共有 helper を直接踏む 3 positive control が消える。
- real-repo 側も共有 helper へ移すと、独立実装の両辺を同じ authority に畳み、helper と test を同時に弱める変更に耐えなくなる。

提案は 3 node を削除しないこと。peer 着地後に共有実装側と独立実装側を両方残す。速度を削る場合は helper 本体だけを改善し、独立 oracle を消さない。

### 親資料内の矛盾

`measurements.md:116-118` は削除候補ゼロと結論する一方、現行 source には上記 autonomous の約 1 秒 duplicate と F176 duplicate がある。段 2 の静的検査結果と親資料の scan 対象 tip または抽出条件が一致していない。2 node の削除可否は静的には安全側だが、親の authority と矛盾したまま段 5 へ渡してはならない。

## 親の実測の一般化への反証

### regime の不一致

[should-fix]

- wall archive は login node と Pegasus 計算ノードの双方を含むとだけ書かれ、tip、K、host、cold/warm cache ごとの層別が示されていない。根拠: `measurements.md:3-6`。
- collection の 87.57 秒対27.44 秒は microbenchmark であり、3 shard、144 worker、実 prewarm、全 hook、実 test frontier が共走する本番 regime ではない。さらに shard-2 の部分 collection は import 順依存で失敗することが後段で確認されている。根拠: `measurements.md:20-33`、`:190-220`。
- t080 の 73.64 秒は専有計算ノード、`-n 0`、同一 key 4 param 直列である。受入は 5 key、11 node、48 worker、filesystem 競合ありであり、100から120秒への投影は同 regime ではない。根拠: `measurements.md:35-49`、`:148-164`。
- peer の snapshot 実測は別 branch の n=1 である。L1/L2 と「独立に効く」とするには、同じ output traversal と filesystem contention を共有しないことの証拠がない。根拠: `measurements.md:120-127`。

### 中央値で隠れるばらつき

[should-fix]

全体 wall は中央値324.3秒に対し、p25 274.3、p75 378.0、p90 433.1、最大663.4であり、IQRだけで約104秒ある。根拠: `measurements.md:14-17`。L1 の約55秒や L3 の11.6秒はこのばらつきより小さい。

目的値を中央値とすること自体はよいが、候補の秒数を archive の非対中央値から差し引いてはならない。同一 branch、同じ K、同じ worker 数、同じ host block の before/after 対で、各対の差を先に作る必要がある。段 2 の最終測定条件 `s2-plan.md:404-411` はこの点を正しく修正している。

collection の表と t080 直列表には反復数と分散がない。87.57から27.44秒、73.64秒、100から120秒を中央値効果として一般化できない。

### 140 秒外す反実仮想模型

[should-fix]

親は `max(C,W/48)` 模型を絶対値には使わず相対比較だけに使うとしている。根拠: `measurements.md:51-59`。しかし D531 は junit duration が共走競合を含み、割付を変えると duration 自体が変わるため、定所要時間模型を採否根拠に使わないと明示している。根拠: `rulings-d531-d532.md:3-14`。

140秒の誤差が allocation に対して共通の加法定数だという証拠はない。collection、worker tail、idle gap、filesystem contention は allocation と cache 共有によって変化するため、相対差でも相殺される保証がない。

したがって「模型は絶対値には使わず相対比較にだけ使える」は過度な一般化である。11.6秒は再検討候補を作る参考値までであり、採否には使えない。段 2 が L3 を不採用とした判断は妥当である。

### 数値の内部不整合

[should-fix]

`measurements.md:12` の shard-2 は `W=4957`、`W/48=101.4` と書かれているが、4957/48 は約103.3である。101.4は brief の旧値4867と整合する。上書き資料自身の W または W/48 が誤っているため、L3 の再計算前に一次資料へ戻って訂正が必要である。

また `measurements.md:33` は controller も collection すると書く一方、`:80-90` は xdist source により controller collection が無いと訂正している。後者を正とし、前者と、brief の147回という説明を今後の根拠に使ってはならない。

`measurements.md:175` の wall 200から230秒予測は、後段で安全上不採用となった selected-file L1 と、削除候補ゼロへ訂正された L4 を含む途中模型であり、現計画の予測値としては失効している。

## pin 閉包の漏れ

検索した key は path だけでなく、function nodeid、parameter ID、group 名、schema field、digest 本数、件数である。

### 既に計画へ入っている pin

- 14 field exact schema: `tools/acceptance_shards.py:61-66`、`test_run_tests_shards.py:79-110`。
- observed、closure、finished、login、report evidence controls: `test_run_tests_shards.py:774-937`。
- default suite root: `test_run_tests_shards.py:301-356`。
- manifest 禁止: `test_run_tests_shards.py:1385-1393`。
- dispatch と login collection の順序: `test_run_tests_shards.py:1403-1423`。
- group 名 exact: `test_real_repo_serialization.py:249-257`。
- tracked consumer の14 fieldと48 digest: `prepare_inputs.py:501-558`。
- duration workerinput exact payload: `test_acceptance_schedule_order.py:1084-1164`。
- t080 6 function、11 node: `test_s8b_oracle_driver.py:933-1009`。
- t080 default selection、setup 到達: `test_real_repo_serialization.py:1112-1154`。
- t080 literal golden: `test_s8b_oracle_driver.py:149-278`。
- ledger schemaと `nodeid_count`: `test_update_acceptance_duration_ledger.py:306-326`。

### 漏れている pin

1. [should-fix] production merge gate は worker digest の本数を固定しない。

   攻撃シナリオ: group/file record が異なる worker の payload だけを controller収集から落とすと、残った digest が全て一致し、report evidence は通る。根拠: `tools/acceptance_shards.py:928-952`、`:533-540`。提案: scheduler が `loadgroup` なら configured worker 数との exact 一致、`serial` なら1本を要求し、worker ID 集合も閉じる。

2. [blocker の一部] t080 host cache の11 consumerが real-repo reader inventoryに無い。

   builder は live ROOT と CCBench を読むが、11 node の exact list `test_s8b_oracle_driver.py:941-1009` は `conftest.py:258-390` と独立 golden `test_real_repo_serialization.py:50-161` に存在しない。cache payer を共有するなら、live input bindingを追加するか、11 nodeを両 inventory に追加して shard/conflict closureを再設計する必要がある。

3. [should-fix] temp root 境界 test が pin 閉包の列挙から抜けている。

   `test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary` は builder と wrapper の双方、ambient `tempfile.gettempdir()` を実 repo output 配下に向けた場合の無書込を固定する。根拠: `test_s8b_oracle_driver.py:1356-1371`。host cache root の祖先導出を変える場合の必須 pin である。

4. [blocker の一部] 削除の独立 inventory がない。

   ledger の5 keyと `nodeid_count` を同時に削れば、closure gate と ledger schemaは縮小集合に対して通る。`test_update_acceptance_duration_ledger.py:360-404` の exact suite hash は `test_real_repo_serialization.py` には効くが、oracle-driver、autonomous、codex-reasoning suite は対象外である。snapshot 3 node の独立 oracle 保存は ledger 以外で pin すべきである。

5. [確認済み] real-repo 側 snapshot を削除または移動すると frozen suite pin が赤になる。

   `test_real_repo_serialization.py` の ledger node set は42件と hashで固定されている。根拠: `test_update_acceptance_duration_ledger.py:360-404`。段 2 が real-repo 側を残す判断はこの pin に対して正しい。

6. [確認済み] autonomous と F176 の exact nodeid を ledger 外で固定する meta-test は見つからなかった。

   現行の機械 pin は `acceptance_duration_ledger.json:2568-2579` と `:5767-5768`。ledger 更新後は削除を拒否する別 gate はない。

7. [確認済み] snapshot 3 node は failure ledger に逐語参照が残る。

   `docs/failures.md:17755-17774`、`:18084-18124`。これは歴史記録であり、削除時に赤くなる機械 pin ではない。node 削除後も過去事実として残すべきである。

## 所見一覧 (severity 付き)

1. **A-01 blocker: t080 host cache が live repository の再観測を未束縛の凍結値へ置換する。**
   - 攻撃シナリオ: payer の cache 作成後に real-repo test が source、output、receipt、submoduleを変更する。後続11 nodeは live状態を再読せず旧 baseを使い、独立再観測なら露見した変更を見逃す。
   - 根拠: `test_s8b_oracle_driver.py:1025-1095`、`s2-plan.md:194-210`、`conftest.py:258-390`。
   - 提案: exact live-input snapshotを束縛し、各 cache hit 前に不変 gateを発火させる。できなければ L2を不採用。

2. **A-02 blocker: snapshot 3 node 削除が独立 oracle を失う。**
   - 攻撃シナリオ: peer topologyで共有 helper側の3 controlを削除するか、real-repo側も同 helperへ寄せ、helperとtestを同時に弱める。旧独立 traversalが残っていれば殺せた変更が通る。
   - 根拠: `measurements.md:98-118`、`s2-plan.md:258-268`、`:353-356`。
   - 提案: 3 nodeを削除せず、共有実装と独立実装の対を維持する。

3. **A-03 should-fix: `_canonical_item` 一回化が stateful Item の二観測不一致を消す。**
   - 攻撃シナリオ: `nodeid` または `xdist_group` markerをアクセスごとに変える Itemは、現行では recordsとselectionの不一致で止まるが、一回化後は最初の値で自己整合して通る。
   - 根拠: `tools/acceptance_shards.py:742-775`、`:826-852`。
   - 提案: Item安定性を明示契約にし、stateful負例と変更前版由来の独立期待値を追加する。

4. **A-04 should-fix: worker digest gate が48本を productionで要求しない。**
   - 攻撃シナリオ:異なるrecordsを返した worker payloadだけを収集対象から落とすと、残りの digest一値条件が通る。
   - 根拠: `tools/acceptance_shards.py:928-952`、`:533-540`。
   - 提案: loadgroup時のconfigured worker ID集合とdigest本数をexact固定する。

5. **A-05 should-fix: host cache隔離testだけでは二段 builderの意味等価性を証明しない。**
   - 攻撃シナリオ: basis/final分割がreceiptとdocumentを同じ誤値から生成すると、cache隔離、inode、lock、key testは全て通りうる。
   - 根拠: `s2-plan.md:194-223`、既存独立 golden `test_s8b_oracle_driver.py:149-278`。
   - 提案: no-cache fresh buildとのbytes、Git状態、document、登録変異kill集合の差分testを置く。

6. **A-06 should-fix: 親実測を本番wall効果へ一般化しすぎている。**
   - 攻撃シナリオ:専有 `-n 0`、単発collection、混在host archiveの値をK=3、144 worker本番へ移し、効果の無い案または逆効果の案を採る。
   - 根拠: `measurements.md:3-59`、`:120-175`、`:190-231`、D531 `rulings-d531-d532.md:3-14`。
   - 提案:同一branch、host block、K、worker数の対測定だけを採否authorityにする。

7. **A-07 should-fix: pin閉包がhost cacheのreal-repo readerと削除nodeを独立に固定しない。**
   - 攻撃シナリオ:11 t080 consumerが未分類のままlive repoと競合し、5 ledger keyをnode countと一緒に消すと全closure gateが縮小集合を受理する。
   - 根拠: `conftest.py:258-390`、`test_real_repo_serialization.py:50-161`、`test_update_acceptance_duration_ledger.py:360-404`。
   - 提案:live-input binding、reader inventory、snapshot oracle node inventoryを同一変更単位で追加する。

8. **A-08 should-fix: 親資料の数値と削除結論が内部不整合である。**
   - 攻撃シナリオ:誤った shard-2 W、失効済み200から230秒予測、削除候補ゼロという結論を次段がauthorityとして使う。
   - 根拠: `measurements.md:12`、`:116-118`、`:170-175`、現行 duplicate `test_autonomous_trial_completeness.py:2019-2021,2274-2276`。
   - 提案:一次資料へのjoin、対象tip、抽出条件を明記して訂正する。

## 未解決・要親裁定

- L2 t080 host cacheは、live-input unchanged gateと旧新kill集合一致が設計されるまで不採用とするか。推奨は不採用のまま差し戻し。
- L4 snapshot 3 nodeは親実測の明示結論どおり残すか。推奨は残す。
- autonomous duplicateとF176 duplicateは、現行静的検査では削除可能だが、`measurements.md` の「候補ゼロ」と矛盾する。対象tipとscan条件を親が確定する必要がある。
- `_canonical_item` 一回化でstateful Itemを契約外とするか、安定性 gateを追加するか。推奨は負例追加。
- worker digest本数を現waveで閉じるか、別waveへ分離するか。現waveが「48 worker独立観測を維持」と主張するなら同waveで閉じるべきである。
- selected-file collectionはD634/D711をsupersedeしても現行144 observer相当の検出力を復元できない。推奨は段2どおり再開しない。
- shard-2の `W=4957` と `W/48=101.4` のどちらが正しいか、一次artifactから親が訂正する必要がある。