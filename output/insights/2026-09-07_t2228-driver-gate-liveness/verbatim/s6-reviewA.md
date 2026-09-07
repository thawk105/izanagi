## ok=True の全経路

`ok=True` の代入は3箇所だけである。`_finish_result()` は新しい緑を作らず、`ok is True` の場合だけ `rc=0` にする。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:605-617,801,890,942`

1. s1: verified freeze の到達性判定が通り、`backoff_fixed_best` と `p2_2_flag_opt` の両 `meets_expected_gate_shape` が真なら緑。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:729-804`
2. repro: historical pin の call が完了し、例外なし、ccbench が historical pin かつ clean、`_gate_success()` が真なら緑。現行 pin 対照の成否は条件に入らない。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:839-890`
3. sweep: `run_workload()` が完了し、例外なし、`_gate_success()`、`committed == 2`、`aborted == 0` がすべて真なら緑。両数値は exact `int` を要求する。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:922-942,457-470`

- **must-fix O1:** `_s1_cell_success()` は record 数を各腕1件に固定するが、record の `terminal_status`、`arm`、request digest、admission の record ID 参照を検査しない。admission も `admitted is True` しか見ない。exact type は observer が上流で絞るが、発行元能力や canonical digest は未検査である。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:418-445,254-269`  
  影響: wrong digest、赤 record、または無関係な真 admission を含む観測が s1 の受理集合に入り、`s1.json.ok=true` と insight の「cell 関門通過」が偽になる。

- **must-fix O2:** `_gate_success()` は request digest ごとの supply/meaning を各1件、両 status を green、admission を exact typeかつ真として検査する一方、record の canonical digest、record ID、arm、macro、issuer capability、および admission 自身の canonical 内容を再検証しない。`any()` なので admission の総数も固定しない。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:380-415` production が本来行う完全性検査は `orchestrator/campaign/condition_meaning_gate.py:3964-4009` にある。  
  影響: production-invalid な未発行 record/admissionでも predicate 単体では緑になり、repro/sweep JSONの受理集合が「production が実際に発行した関門証拠」より広くなる。

- **refuted O3:** `_gate_success()` の request exact type、request digest 照合、同一 digest record の重複拒否は実装済みである。別 digest の追加 record は repro の 5/10、sweep の fixed=2 に必要なので、総 record 数を2件へ固定しないこと自体は裁定4とのズレではない。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:380-415`  
  影響: 同一 inert digest の重複は緑にならず、現行受理集合は変わらない。

## 観測の取りこぼしと取り違え

- **refuted P1:** request/supply/meaning は exact production typeと期待 driver IDの両方で絞られる。cloneごとに production moduleを再 importし、target code objectもそのbundleから取るため、別cloneや別driverの recordは通常混入しない。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:178-215,218-269`  
  影響: 現行3 driverの同期経路では別driver recordによる受理集合拡大はない。

- **must-fix P2:** admissionにはdriver IDがないため observer は全 admission を無条件に保存する。repro/sweepでは record ID の包含で軽減されるが、s1は O1 のとおり結び付きを検査しない。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:268-269,410-415,431-445`  
  影響: s1内に別family admissionが入る変更が生じると、`s1.json`が対象cellとは無関係な admissionを根拠に緑となる。

- **refuted P3:** profilerは admission return時に解除される。sweepでは関門呼出しが screening開始前にあり、後段計測は観測しない。repro/s1でも `__exit__()` が二重解除に耐える。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:249-282`; `orchestrator/campaign/backoff_sweep.py:378-418`  
  影響: 現行sweepの後段campaign recordを誤採取することはなく、受理集合は変わらない。

- **refuted P4:** `sys.setprofile()` は別threadを観測しないが、対象 production 呼出しはすべて同一threadの直列 comprehensions/callsである。対象4関数もPython関数でありC実装ではない。`orchestrator/campaign/backoff_sweep.py:107-158`; `orchestrator/campaign/s1_direct_comparison.py:266-300`; `orchestrator/campaign/backoff_repro.py:63-84`  
  影響: 現行経路でthread/C実装由来の取りこぼしはない。一般対応はscope外。

- **refuted P5:** target関数が例外で抜ければ `_measure_call()` の `completed` は偽となり、3 runnerとも `ok=True` 条件を満たさない。profile callbackは戻り値を置換しない。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:473-494,784-801,883-890,937-942`  
  影響: gate例外をreturn成功と取り違える緑はない。

## 例外の握り潰し

- **must-fix E1:** `BaseException` を捕捉しており、`KeyboardInterrupt`、`SystemExit`、`GeneratorExit`までdriver失敗やnetwork metadataとして直列化して実行を継続する。特にnetwork観測中の割込みは判定外metadataに吸収され、その後3 driverすべてが緑になりうる。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:488-494,505-521,802-804,891-893,943-945,1042-1051`  
  影響: 中止されたjobが追加driverを走らせ、JSONのdriver集合と例外値を変え、場合によっては全 `ok=true` のまま insight に採用される。

- **must-fix E2:** `current_pin_pre_gate_control.failed_before_gate` は「call未完了かつ観測returnが0件」しか見ず、期待する `assert_pinned_clean` 拒否の型・位置を確認しない。さらにこの対照全体がreproの `ok` 条件から除外されている。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:835-858,883-890`; productionの関門前境界は `orchestrator/campaign/backoff_repro.py:63-83`。  
  影響: 現行pin対照が成功した場合や、別setup失敗だった場合でも `repro.json.ok=true` となり、insightが「現行pinでは関門前拒否を実測した」と誤って参照できる。

- **refuted E3:** historical/sweep/s1の本走では、pre-gate、gate、post-gate cleanupのどこで失敗しても `completed=False` となる。観測済みrecordとexceptionが併記されるため、outer `try` 自体が赤を緑へ変えることはない。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:473-494,729-945`  
  影響: 判定はfail-closedのままで、受理集合は広がらない。

- **nit E4:** `drivers_completed_before_publish` は `_load_production()` やrunner起動前の失敗でも無条件にdriverを追加するため、実質は「attempted prefix」である。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:1040-1054`  
  影響: `ok` は偽のままだが、insightがこのfieldを完走集合として引用すると実行範囲を過大表示する。

## 恒真な検査

静的に各登録変異を追った結果は次のとおり。pytestは実行していない。

| 変異 | 静的結論 |
|---|---|
| M1 | `_base_result()`を直接呼ぶため、初期値を真にすれば行90で落ちる。恒真ではない。`orchestrator/tests/test_t2228_driver_gate_liveness_probe.py:73-91` |
| M2 | `_gate_success()`のsupply status検査を落とせば行105が落ちる。literal mutationは殺す。`...test_t2228_driver_gate_liveness_probe.py:94-105` |
| M3 | admissionの `admitted is True` を落とせば行121が落ちる。literal mutationは殺す。`...test_t2228_driver_gate_liveness_probe.py:108-121` |
| M4 | message中に `configure-timeout` を含めた上で `None` を要求するため、message推測変異は落ちる。`...test_t2228_driver_gate_liveness_probe.py:124-133` |
| M5 | `_sweep_accepts()`内の `aborted` 条件を落とす変異は行146が殺す。ただしrunner本体は通らない。`...test_t2228_driver_gate_liveness_probe.py:136-146` |
| M6 | create-onlyを上書きへ変えれば例外要求と既存内容保持が落ちる。`...test_t2228_driver_gate_liveness_probe.py:149-157` |
| M7 | inert countを定数0にすれば期待値1で落ちる。production `schedule_for_role` と `_is_inert_value` を通る。`...test_t2228_driver_gate_liveness_probe.py:160-198` |

- **must-fix T1:** M2/M3/M5のpositive fixtureは、両arm recordを直接constructorで作り、`record_digest="b"*64`、空evidence、issuer capabilityなしとする。production admissionなら `condition_meaning_gate.py:3964-4047` で拒否される入力を `_gate_success()` が緑扱いしている。`orchestrator/tests/test_t2228_driver_gate_liveness_probe.py:16-70,94-146`  
  影響: テストが緑でもproduction発行物との完全性やprofiler配線は保証されず、不正recordを受理するJSON acceptance regressionを捕まえない。

- **must-fix T2:** M5はhelperだけを呼び、登録位置であるsweep runnerを通らない。`_run_sweep()`側で `_sweep_accepts()` を迂回して `ok=True` にする「runnerがabortedを無視」の同義変異は現テストを通る。`orchestrator/tests/test_t2228_driver_gate_liveness_probe.py:136-146`; `tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:937-942`  
  影響: `summary.aborted=1` の実測JSONをrunnerが受理する回帰でもM5が緑のままとなり、sweepの受理集合が拡大する。

## 裁定 4 との突き合わせ

- **満たす:** 全driverの初期値は偽で、`_finish_result()`は exact `True` のみrc0。`probe.py:605-617`
- **満たす:** s1はverified freezeを読み、production `schedule_for_role()`を4 roleで実呼出しする。`probe.py:620-690,741-745`
- **一部不一致:** s1の2 cellとrecord数は正しいが、backoff cellのdigest、status、admission参照が未照合。`probe.py:418-445`
- **満たす:** `p2_2_flag_opt` は request、record、admissionが全て0件の場合だけ成功。`probe.py:425-430`
- **満たす:** repro historical runは完了、例外なし、pin/clean、inert record緑、真admissionを要求する。`probe.py:860-890`
- **満たす:** sweepは上記に加え exact `committed=2`、`aborted=0` を要求する。`probe.py:457-470,937-942`
- **不一致:** 実行設計で要求された現行pin関門前対照は記録だけで、成功条件に寄与しない。`s4-adjudication.md:106-109`; `probe.py:839-890`
- **満たす:** 通常のdriver例外では `ok=False`、`rc=1`、型、message、実属性reason code、cause/contextを保存する。`probe.py:285-312,615-617`
- **不一致:** `BaseException`まで握るため、中止要求をdriver結果として扱う。
- **nit:** PBSの `-o/-e` はsubmission例だけで、script自身は指定漏れを拒否しない。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:1-12,64-79`  
  影響: JSON受理集合は変わらないが、stdout/stderrがrepository内へ落ちるとinsightのrepo外evidence provenanceが不完全になる。
- **満たす:** 1 processでs1、repro、sweepの順に実行し、Pythonを`exec`せずshell trapを維持する。`probe.py:1033-1082`; `t2228_driver_gate_liveness_probe.pbs:279-291`

## must-fix 一覧

1. s1 recordをrequest digestとadmission record IDsへ結び、status、arm、macro、issuer/canonical integrityを検査する。
2. repro/sweepでもproduction発行recordとadmissionの完全性を再検証し、任意の未発行dataclassを緑にしない。
3. 現行pin対照が期待した関門前拒否であることを機械判定し、repro成功条件へ含める。
4. `BaseException`を通常のdriver失敗として握らず、中止系例外をprocess terminationとして伝播する。
5. M2/M3/M5のproduction-invalid fixtureを改め、observer経由のproduction発行物を使う検査を追加する。M5は `_run_sweep()` 自体を通す。

## 裁定へ返す候補

以下は本waveで実装せず裁定へ返す候補である。

- productionのrepro/s1へFetchContent baseを供給する修正。
- `sys.setprofile()`観測を別threadやC実装まで一般化する仕組み。現行3経路には不要。
- 3 driver aggregate manifest、完走gate、台帳の新設。
- s1の全configuration、全cell実走への拡張。
- PBS出力先を新しいsubmission wrapperやadmission registryで強制する一般化。

## 総括

**要修正。** 現行のhistorical repro/sweep predicateは主要なinert request、digest、green status、summary数を検査しているが、s1のrecord/admission結合、現行pin対照、production発行物を使わないM2/M3/M5、`BaseException`捕捉が受理根拠を弱めている。

pytestおよび計算ノード実測は実行していない。静的検査のみであり、M1〜M7や3 driverを緑とは報告しない。