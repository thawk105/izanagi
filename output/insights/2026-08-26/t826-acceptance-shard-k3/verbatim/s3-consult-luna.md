## 総括

最大の blocker は、plan が `tools/run_tests.py` を変更する一方、現 launcher が main と tip の runner bytes の不一致を pytest 起動前に拒否する点である。要求された受入全走と receipt をこの wave 自身では作れない。  
期待 wall 170.7 秒も成立しない。同じ模型でも次の直列 group 156.2 秒が律速となり、同じ残差を使えば約 240.8 秒、短縮は 21.6% まで下がる。  
さらに login collect-only の bytecode 書込み、実 repo を書く負例、lock metrics の worker 集約欠落があり、排他閉包も未完成である。  
K 引上げ自体には価値があるが、現 plan のままの実装は非推奨である。real-repo 細分化と runner/K 契約改訂を分割し、前者の閉包修復を先に行うべきである。  
以下は静的検査結果であり、pytest、collection subprocess、受入全走は実行していない。

## 所見

### F1. この wave は自身の受入 receipt を発行できない

- 重大度: blocker
- 根拠: `s2-plan.md:270-277` は `tools/run_tests.py` を編集対象に含む。一方 `tools/acceptance_launcher.py:436-439` は `tested_main` と `tested_tip` の runner blob が異なるだけで `LauncherFailure` にする。親 brief は受入全走 1 回を必須成果物としている (`s1-brief.md:55-58`)。なお D524 本文は tip runner を許すとしており、実装とも不整合である (`docs/decisions.md:21657-21666`)。
- 失敗する具体シナリオ: K domain を変更して commit すると main/tip の `run_tests.py` が異なる。`tools/dev_wave_wait.py acceptance` は pytest を起動する前に `tested-main and tested-tip runner blobs differ` で停止する。
- 成果物影響: acceptance receipt が発行されず、受入全走の証拠も land 条件も満たせない。K 改修は runner bootstrap/receipt 契約を先に直す別 wave へ分離する必要がある。

### F2. zero-write 閉包は login collection と負例自身で破れる

- 重大度: blocker
- 根拠: plan は bytecode 抑止を shard child 環境だけへ入れる (`s2-plan.md:46-52`)。しかし login collect-only は別 process として同時実行され、`_dispatch_environment()` のまま pytest を起動する (`tools/run_tests.py:1402-1445`)。さらに outer launcher bootstrap は既存の `PYTHONDONTWRITEBYTECODE` がある場合しか抑止しない (`tools/acceptance_launcher.py:51-60`)。plan の zero-write 負例は `GIT_OBJECT_DIRECTORY` を外して実 repo fingerprint を変える記述になっている (`s2-plan.md:200-202`)。
- 失敗する具体シナリオ: compute shard の bytecode を抑止しても、並走する login collection または outer runner import が repo 内へ `__pycache__` を作る。別シナリオでは negative control 自身が親 object database へ到達不能 object を残す。
- 成果物影響: 「実 repo への同時書込みを一切許さない」という親不変条件を破る。ignored bytecode と unreachable Git object は通常の status fingerprint に現れず、受入が通ったまま共有 repo を変更しうる。
- 必要修正: bytecode 抑止は launcher bootstrap より前から outer/login/compute の全 process に適用する。書込み負例は実 repo でなく独立 temp repository/object store 上で行う。

### F3. 170.7 秒の見積りは次の直列 group を落としている

- 重大度: must-fix
- 根拠: plan の Q5 は `max(86.1, 42.77) + 84.61 = 170.7` とする (`s2-plan.md:222-234`)。同じ実走には `s8c-preregistration-candidate` 156.17 秒、`s8c-predicate-snapshot` 64.3 秒が存在する (`output/insights/2026-08-26_t1814-shard-time-balance/README.md:80-94`)。
- 失敗する具体シナリオ: real-repo capacity が86.1秒まで下がっても、156.17秒の group は1 worker直列のまま残り、critical term は156.17秒になる。
- 成果物影響: 同じ残差84.61秒を使うと wall は240.78秒、307.29秒からの短縮は66.51秒、21.64%である。親の44.46%より利得が70.11秒小さい。

### F4. 台帳全体の倍率1.9を real-repo 成分へ掛ける根拠がない

- 重大度: must-fix
- 根拠: 台帳総和は7874.186秒、実走総和との比は1.344倍と1.888倍である。一方 real-repo 鎖は台帳236.7秒に対し実走222.68秒で0.941倍、最長 node は台帳94.0秒に対し42.77秒で0.455倍である (`s1-anchors.md:54-60`)。共通 key の実測倍率 p95 も走ごとに2.24から4.75まで動く (`README.md:109-125`)。
- 失敗する具体シナリオ: real-repo 成分だけが全体より大きく膨張すれば86.1秒を超える。逆に観測された鎖のように縮めば real-repo はさらに軽くなり、156.2秒 group の支配が強まる。
- 成果物影響: 170秒にもK=4 plateauにも一意な向きの補正をかけられない。成分別実走 join がない限り期待値と呼べない。

### F5. K=8 の導出と default K が未確定である

- 重大度: must-fix
- 根拠: `ceil(4 × 1.9) = 8` という導出 (`s2-plan.md:170-172`) は、全成分を一様に1.9倍するなら plateau のKを変えない。非一様なら8が上限になる保証もない。また plan は「既定値は4でよい」とするが、D724 は既定K=2を明記している (`docs/decisions.md:28347-28365`)。
- 失敗する具体シナリオ: 一様倍率ならK=4以降の割付順は同じで、K=8を開けても利得がない。非一様または未台帳 node が一成分へ集中すれば、plateau は3にも9以上にもなりうる。defaultを4へ変えるなら既存 default-K2 tests が赤になる (`test_run_tests_shards.py:410-432,458-478,568-626`)。
- 成果物影響: 不要な最大8 job投入、queue skew、失敗面を正当化できない。逆にdefaultを2のままにすると通常受入経路では親が主張するK=4利得が発火しない。

### F6. K domain の参照閉包に parse境界、決定文書、marker consumer が残っている

- 重大度: must-fix
- 根拠: plan が列挙した literal gate に加え、`_consume_internal_shard_spec()` は `int()` により先頭ゼロ・符号・空白を正規化してしまう (`tools/run_tests.py:301-335`)。`_plugin_spec()` も JSON の count/index を `InternalSpec` へ無検査で入れる (`tools/acceptance_shards.py:715-732`)。Q4 が要求する先頭ゼロ拒否は共有整数 predicate だけでは実現できない。D710/D724 は domain `{2,3}`、既定2、K≧4却下を明記する (`docs/decisions.md:27901-27927,28347-28399`)。
- 失敗する具体シナリオ: author が列挙済み7 literalだけを共有定数へ置換すると、内部 argv `"02"` は2として通る。default4へ変えると上記の default-policy tests が焦点走で赤になる。決定 fragment をD358だけにすると productionと決定正本が矛盾したままになる。
- 成果物影響: internal shard spec の閉集合契約が破れ、完了文書も成立しない。D710とD724の明示改訂が必要である。
- 補足: report index、report loader、JUnit path/merge、session directory、dispatch intent は `range(K)` または `shard-{index}` で一般化済みである。`run_acceptance_nproc_study.py` のK=2は固定 study armなので変更不要。receiptがKを証明しない点はD724が明示的に受容した既知限界であり、log SHAだけからland側がKを検査できるわけではない (`docs/decisions.md:28397-28399`)。

### F7. real-repo marker の既存テストと契約文書が変更閉包から落ちている

- 重大度: must-fix
- 根拠: plan は主に `test_real_repo_serialization.py:1380-1448` の record testを挙げる (`s2-plan.md:107`)。しかし同fileには、全resource nodeが `real-repo` markerを持つことを要求する `_assert_real_repo_suffix_contract` (`:1161-1217`) と exact marker/count検査 (`:1328-1377`) がある。READMEも「real-repo markerでshard閉包を保つ」と契約化している (`orchestrator/tests/README.md:261-265`)。
- 失敗する具体シナリオ: productionだけをplanどおり変更すると、focused `test_real_repo_serialization.py` が marker不一致で赤になる。テストを単純削除すると、affinity stampの過不足を独立に検査する防壁も失う。
- 成果物影響: focused test段階でlandが止まるか、検査を弱めればresource nodeが別hostへ漏れる退行を見逃す。既存marker gateを「全resource affinity、process memoだけmarker」へ置換し、READMEも更新すべきである。

### F8. lock metrics は workerからcontrollerへ届かず、timeout標本も打切りを落とす

- 重大度: must-fix
- 根拠: lock取得は各xdist workerの `pytest_runtest_protocol` 内で起きる (`conftest.py:1826-1843`)。現 worker payload はcollection digestとgw0のrecords/selectedしか送らない (`acceptance_shards.py:850-889`)。plan はreportへmetricsを足すとだけ記し、workeroutputとcontroller集約経路を定めていない (`s2-plan.md:204-218`)。また `Qmax` を「全取得成功」の最大とするため、245秒 timeoutした打切り標本が母集合から消える。
- 失敗する具体シナリオ: controller reportのmetricsが常に空、または一部worker分だけになる。writer starvationでtimeoutした取得を除外し、成功分だけの小さいQmaxから新timeoutを決める。
- 成果物影響: timeout再設定機構が実環境で一度も有効な証拠を作れないか、短すぎるtimeoutを採って受入を偽赤にする。
- 必要修正: workerごとの attempts/successes/timeouts/wait-max/hold-maxをworkeroutputへ載せ、controllerが全workerをexact mergeする。`timeout_count == 0` と対象resource nodeの取得被覆を採用条件にする。

### F9. nodeid台帳の大半は壊れないが、historical duration key 1件だけは静かに未知化する

- 重大度: nit
- 根拠: markerを外す対象は86 nodeだが、現行もcollection wrapperのpost-yieldでそのsuffixを除去している (`conftest.py:1702-1718,1811-1815`)。したがって最終nodeidは変更前後で同じである。静的集合照合では次の結果だった。

  - real-repo inventory/process memo/receipt memo/oracle memo: `file::function` normalizerを使用 (`conftest.py:623-639,762-795`)。
  - growth hold: 86 node中29件が交差するが、basename/functionへ正規化してcollection前段で照合する (`conftest.py:1491-1496`)。
  - flaky hold:完全nodeidだが対象86 nodeとの交差は0件 (`conftest.py:1499-1503`)。
  - fold gate:対象86 nodeとの交差は0件 (`fold_gate_nodes.py:47-143`)。
  - duration ledger:62件はcanonical key、23件は元から未知、1件だけhistorical `@real-repo` keyである。該当は `test_sort_swo_oracle...explicit_binding@real-repo = 0.19`。
  - ledger updaterはgroup suffixを除去する (`tools/update_acceptance_duration_ledger.py:27-31,254-286`)。
  - shard inventory/reportは実markerと一致するsuffixだけを除去する (`acceptance_shards.py:679-705`)。
  - acceptance red/flake receiptはcollectionとの最長exact matchでsuffixを解釈する (`check_acceptance_reds.py:589-631`)。最終nodeidが同じなので変化しない。

- 失敗する具体シナリオ: markerを外した後、duration resolverがaffinityをhistorical fallback候補として読まなければ、上記0.19秒の1件だけがunknown costになる。
- 成果物影響: certified集合、hold、fold、receiptには影響しない。投入順の1件だけが静かにdefault costへ落ちる。planのfallback改訂に専用のmutation testを付ければ閉じる。

### F10. ABBA各2走では30秒級の効果を主張できない

- 重大度: must-fix
- 根拠: plan はK=2 serial/splitをA/B/B/Aとし、その後のK=2/K=4は走数を明記しない (`s2-plan.md:262`)。同一tip・同一割付のwallは307.29/275.02秒で、2点からの標本標準偏差は22.82秒である (`README.md:96-105`)。
- 失敗する具体シナリオ: K2 splitの再計算利得31.3秒や、split K2→K4の約35.2秒がcompute node差だけで再現または消失する。2/armでは効果とnode交絡を分離できない。
- 成果物影響: D358を改訂する性能証拠にならず、効果のない複雑化をlandするか、有効な変更を誤って棄却する。
- 必要測定: 独立正規近似、両側5%、power 80%という粗い設計では31.3秒差に9走/arm、35.2秒差に7走/armが必要になる。2点からの分散推定なのでこれは下限的な計画値であり、compute nodeをblockしたpaired pilotで差分分散を得た後に再計算すべきである。

## 親 brief への反論

- (P1) refuted: SH/EX flockは登録済みnodeのsetup/call/teardownしか覆わない。collection/import、login collect-only、inventory外fixture、候補Git object writerを覆わない (`conftest.py:1826-1848`)。
- (P2) real: lock pathはrepo realpathをhashした `/tmp` fileであり、同一host/filesystem viewに限定される (`conftest.py:981-1007`)。登録済みresourceを同一shardへ留めるaffinityは必要である。ただしinventory完全性は別途必要である。
- (P3) refuted: T-991のstatus 2経路は直っているが、92 node inventoryは既存集合内部のpartition一致しか証明しない (`conftest.py:576-620`)。後発candidate object writerとcollection/import書込みを含まない。
- (P4) refuted: K2は観測最遅workerを使えば276.0秒であり272秒ではない。K4は156.2秒の別groupを入れると、同じ残差模型でも240.8秒になる。170秒は期待値ではない。
- (P5) refuted: 残差は39.2から84.6秒まで動き、一次資料自身が定数扱いを禁じている (`README.md:47-57`)。K増加はcollection回数、worker開始、fixture再実行、I/O競合を変えるためK不変とも言えない。
- (P6) refuted: K=4 plateauは92.5%被覆の台帳投影にすぎない。実joinでは15,878/17,160が共通で、現行集合の1,282 nodeが未台帳、台帳側にも31 stale keyがある (`README.md:109-125`)。K>4でもaffinity成分を割らず他成分だけを分割できるため、直ちにcross-host lockを要するわけでもない。

## 期待利得の再計算

同一a1k2走の観測値を固定する仮想計算に限定する。

```text
baseline wall                     = 307.29
R0 = baseline - real-repo chain   = 84.61

real-repo capacity proxy
  = 2174.1 / 48 × 1.9
  = 86.06

post-split critical term
  = max(
      86.06,   # real-repo component capacity
      42.77,   # observed longest former real-repo node
      156.17,  # s8c-preregistration-candidate
      64.3     # s8c-predicate-snapshot
    )
  = 156.17

conditional wall
  = 84.61 + 156.17
  = 240.78

conditional saving
  = 307.29 - 240.78
  = 66.51 seconds
  = 21.64%
```

親の170.67秒、44.46%短縮と比べ、同じ残差を使った時点で利得は70.11秒減る。`s8c-preregistration-candidate` が現在載るshard自身の残差58.98秒を使えば215.15秒になるが、これは現在のK2 shardを再利用した条件値でありK4予測ではない。

より正直な式は次である。

```text
C_real = (2174.1 × f_real + U_real) / 48

wall = max over shards/groups of
       (worker/group start delay
        + max(156.17, C_real, longest item, LPT tail)
        + collection/finalization overhead)
```

`f_real` はreal-repo成分固有の台帳倍率、`U_real` は未台帳nodeの同成分仕事量である。`f_real <= 3.448` かつ `U_real` が小さい間は156.17秒groupが床になる。全体倍率1.9からこの条件は証明できない。

この模型が成立しない条件は、worker開始時刻の不揃い、group開始遅延、`pending <= 2` のprefetch窓、controller/worker collectionの直列部分、file/affinity componentのLPT裾、module fixtureのworker別再実行、reader波とwriter待ち、I/O・memory競合、shardごとの非同期開始・終了、K変更でduration自体が変わる場合である。D531とD713の警告どおり、上記は下界でも期待値でもなく仮想capacity指標である。

測定は最低でも次を分ける必要がある。

- K2 old-serial 対 K2 split: 主効果は約31秒なので、現ノイズ推定では約9走/arm。
- split K2 対 split K4: 修正後の差は約35秒なので、約7走/arm。
- 各走で各shardのpytest wallとその最大、job Elapseとその最大、group開始時刻と直列所要、worker occupancy、collection/start/finalization残差、lock wait/hold/timeoutを記録する。
- queue待ちと外側wallは記録するが主効果から除外する。compute nodeをblockまたは層別化し、同一tip・同一受理集合・同一worker数・同一hold状態で交互実行する。

## 未確認事項

- K=4/6/8の実走component分布と、Kごとの実pytest wall、job Elapse。
- 未台帳1,282 nodeがどのaffinity/file componentへ入り、どれだけの仕事量を持つか。
- split後の156.2秒group、module fixture、worker開始遅延、残差の実分布。
- 全workerから集約したreal-repo lock待ち・保持・timeout分布とwriter starvationの有無。
- outer/login/compute全processでbytecode書込みがゼロになること。
- candidate fixtureをtemp object storeへ移した後の検出力同値性。
- modified `run_tests.py` を持つtipが正規のacceptance receiptを発行できるrunner/launcher契約。
- 受理集合、growth/flaky hold、fold gate、receipt nodeid集合の実走不変性。