## 所見一覧

1. [実測] `_atomic_update` の lock 分割自体は成立する。`_locked()` は毎回 `os.open()` した別 fd に `flock(LOCK_EX)` を掛けるため非再入であり、再取得すれば自己待機する。plan の `with admission._locked(root) as lock → marker.use(lock=lock, action=lambda active_lock: _atomic_update_locked(active_lock, ...))` は、exact type、seal、active、exact root、int fd、regular-file の全条件を満たす。`orchestrator/campaign/s8b_holdout_admission.py:699-726,5115-5137,5140-5227`
   
   判定: refuted。成果物影響: 二重 lock による停止や、lock 外での台帳更新は生じない。
   
   推奨: plan の呼び順を維持する。v2 recovery `attempt_ordinal>0` は B1 capability が証明しないため通らないが、plan は `attempt_ordinal=0` 限定を明記しており、これは意図した拒否である。`orchestrator/campaign/s8b_holdout_admission.py:4961-5001`

2. [実測] `_PRELOCK_SNAPSHOT_HOOK` の test は実在し、2 worker が同じ lock 前 bytes を読んでから直列化される意味を検査している。外殻で path を読み、hook を一度呼んでから lock を取れば意味は保存される。`orchestrator/tests/test_s8b_attempt_registry.py:1492-1529`, `orchestrator/campaign/s8b_attempt_registry.py:984-1004`
   
   判定: refuted。成果物影響: authoritative read は引き続き lock 内で行われ、競合した start が二重記録されない。
   
   推奨: marker wrapper と通常 wrapper の双方で hook をちょうど一度、lock 前に呼ぶ。

3. [実測] `marker.use()` の `action` が例外を投げても、外側の `_locked()` は `_active=False`、unlock、fd close を必ず行う。registry staging は、生成途中の例外なら `_write_staging()`、生成後なら `_atomic_update()` の `finally` が unlink する。replace 後の例外では authoritative bytes は新 bytes のままで staging は残らない。`orchestrator/campaign/s8b_holdout_admission.py:718-726,5227`, `orchestrator/campaign/s8b_attempt_registry.py:686-725,1028-1048`
   
   判定: nit。成果物影響: 通常の例外では台帳は old/new の完全な一方になり、staging は残らない。ただし unlink 自体の失敗時は cleanup 例外となり、staging が残りうる。
   
   推奨: 既存 atomic fault test に加え、`marker.use(action=_atomic_update_locked)` の合成 test で「例外後に lock を再取得可能」「staging なし」を固定する。`orchestrator/tests/test_s8b_attempt_registry.py:1187-1244`

4. [実測] real / blocker: sealed terminal の「再導出」は、採用済み信頼境界を満たしていない。plan は `valid`、`excluded_reason`、`session_median` という sealed record 内の自己申告値から status/reason を導出するが、現物ではそれらを campaign が組み立てている。前 wave 裁定は launcher 所有の probe、classification receipt、throughputs、exec failures、rep evidence から再導出し、自己申告値は比較対象にだけ使うよう要求している。`s2-plan.md:164-169,401-405,451`, `refs/s4-adjudication-r2.md:89-108`, `orchestrator/campaign/s8b_floor_campaign.py:6077-6165,6182-6217`
   
   判定: real / blocker。成果物影響: producer が raw factsと整合しない `valid` / `excluded_reason` を sealed record に入れても、terminal row と同じ自己申告から比較すれば通る。誤った retryable status、台帳値、report session、最終選択を同時に自己整合させられる。pure verifier自身も raw session の真正性は別層だと明記している。`orchestrator/campaign/s8b_floor_stats.py:409-416`
   
   推奨: projection API の入力を launcher 所有の raw facts と固定 policy に変え、sealed record の `valid`、`excluded_reason`、`session_median` は再導出結果との比較にだけ使う。

5. [実測] `S8B_RETRYABLE_FAILURE_REASONS` の空集合効果は、plan が挙げた「test pin と retryable null matrix」だけではない。全参照点は、定義・profile 組立、adapter の exact-profile gate、genesis の集合一致、genesis builder の既定値、retryable membership、terminal-failure non-membership、後続 ordinal の認可である。`orchestrator/campaign/s8b_attempt_profile.py:395,440-457`, `orchestrator/campaign/s8b_attempt_registry.py:386-423`, `orchestrator/campaign/attempt_registry_core.py:689-701,952-975,1081-1119,1285-1289,1458-1483`
   
   判定: real。成果物影響: 非空化は retryable-failure を広げる一方、その4理由を持つ terminal-failure を拒否するため、raw core の方向は「広がる」だけでなく混合である。また通常 terminal から次 ordinal を開ける状態も変わる。
   
   推奨: v1 定数は空のまま残し、plan どおり別の v2 定数にする。v2 について retryable 正例だけでなく「同じ4理由を terminal-failure として拒否する」負例も追加する。既存の直接 pin は4 assertionである。`orchestrator/tests/test_attempt_registry_core_s8b_profile.py:296-302,792-802`

6. [実測] v1/v2 並存、2段 path、5軸 slot、非-generation sibling の無視は、plan が認めるとおり受理集合を広げる。既存 v1 schema/profile/layoutを別 symbolとして残すため、正規1段 v1 bytes は壊れない。`s2-plan.md:125-187,382-391`, `orchestrator/campaign/s8b_attempt_profile.py:367-395`
   
   判定: refuted。成果物影響: v1 claim、legacy marker、4軸 recovery reader の既存参照は維持できる。
   
   推奨: v1/v2 を一つの readable profile に混ぜず、schema peek 後に別 profileへ dispatchする方針を維持する。

7. [実測] canonical 1段 v1 API を「不変」とする記述には例外がある。live root には2段 v1があり、現行コードは1段 pathしか見ないため相互に干渉しない。A1' の横断列挙後は、その2段 v1を発見して unknown recovery policy として拒否するので、同じ `db07b575...` freeze に対する正規1段 v1 mutationは新たに停止する。`orchestrator/campaign/s8b_attempt_profile.py:378-386`, `orchestrator/campaign/s8b_attempt_registry.py:451-482`, `/work/1/SFC/tanab/izanagi/.git/izanagi/s8b-holdout-admission-v1/floor-attempt-registries/db07b575390d1e6e76763c9dc7f5be9e07e270e101cd763eabc973b77e59cb41/d388477f0272b8d41fbc0e82956841cf5eff45f68b0c8fd40e74dc1bb6dae920/registry.jsonl:1`
   
   判定: real。成果物影響: この fixture freeze の受理集合は安全側に狭まり、新しい start は記録不能になる。既存 bytesの書換えはない。
   
   推奨: 「canonical v1 不変」を「競合する既知/未知 generation がない root では不変」に限定する。fixture authorityを新 trust rootへ昇格しない fail-closed 方針は妥当である。

8. [実測] real / blocker: v2 public adapter を受ける exact-profile gate が plan の境界から落ちている。現行 `_assert_profile()` は必ず v1 factoryを再構築し、v1 schema/layout/codec の object identityを要求する。create/read/reserve/resume/state検査の5 call siteがこの gateを通るため、このままでは全 v2 profile が path処理前に拒否される。`orchestrator/campaign/s8b_attempt_registry.py:315-448,497,1063,1096,1130,1794`
   
   判定: real / blocker。成果物影響: A2' の v2 generation、reserve、terminal、resume が全て到達不能となり、新規台帳も certified chain も作れない。
   
   推奨: `_assert_profile` をschema別 exact validatorへ変更することをA2'境界に明記する。新しい `terminal_row_validator` と `retryable_terminal_opens_next_attempt` も exact比較へ加える。そうしないと `dataclasses.replace(v2_profile, terminal_row_validator=None)` 等が通る。plan の call-site inventoryはこの5件を0件扱いで落としている。`s2-plan.md:49-93,189-252`

9. [実測] real / blocker: adapter の row lookup は4軸固定で `measurement_ordinal` を比較しない。`_rows_for_event()` の11 call siteがこの helperを使う。例えば `(h,c,0,0,0)` と `(h,c,0,1,0)` はv2 coreでは別 slotだがadapterでは同じ slotになり、後者のclassificationが前者の既存rowを拾う。`orchestrator/campaign/s8b_attempt_registry.py:766-808,1208-1226,1313-1349,1596-1607,1835-1855,1965-1967,2033-2042`
   
   判定: real / blocker。成果物影響: planned measurementと同一roundのretry measurementが別 claim pathを持っても、classification、observation、terminal、resumeの台帳参照が衝突し、誤参照または停止する。
   
   推奨: `_row_is_for_slot` / `_rows_for_event` にprofileを渡し、codecの完全なslot identityで比較する。異なる `measurement_ordinal`、同じ `attempt_ordinal=0` の2 lifecycleをadapterで完走する正例を追加する。plan は変更範囲に `:766-839` を含めるだけで、境界signatureとtestを固定していない。`s2-plan.md:11,282-374`

10. [実測] plan が明記した個別件数は、`TransitionPolicy=2`、`DomainProfile=2`、`load_attempt_registry=7`、core terminal=3、adapter terminal=1、`_atomic_update=6`、`registry_path` production=0で一致した。ただし `assert_registry_rows` はplanの11件に加え、`trial_registry.py` が callableとして渡す2件があり、実測13件である。`s2-plan.md:270-280`, `orchestrator/campaign/trial_registry.py:2224-2248,3437-3474`
   
   判定: real。成果物影響: seeded replay抽出で既存wrapperの戻り値や例外順を変えると、8c trial台帳の検証値と受理が変わる。
   
   推奨: consumer表を「plan 11 / 実測13」へ直し、2つの8c facade経路を回帰対象へ加える。加えて inventory未記載は `make_s8b_domain_profile` production 2件、`S8B_REGISTRY_LAYOUT` production 4参照、前項の `_rows_for_event` 11件である。`orchestrator/campaign/s8b_attempt_registry.py:339,453,837,847`, `orchestrator/campaign/s8b_holdout_admission.py:5363-5369,5602`

11. [実測] 指定された残りの production consumer では、`p3_b4_analysis_ledgers.py` と `p3_b4_raw_record_producer.py`、`p3_b4_prerun_issuer.py` は共通 `canonical_json_bytes` だけを使い、今回のprofile/layout APIを呼ばない。launcherはadapter reserve/terminal各1件、holdoutはlegacy layout/factory/load各1件、schedulerはcore load 1件である。`orchestrator/campaign/p3_b4_analysis_ledgers.py:14-26`, `orchestrator/campaign/p3_b4_raw_record_producer.py:36`, `orchestrator/campaign/p3_b4_prerun_issuer.py:36`, `orchestrator/campaign/s8b_floor_attempt_launcher.py:454-469,637-644`, `orchestrator/campaign/s8b_scheduler_accounting.py:319-350`
   
   判定: refuted。成果物影響: 上記3つのp3 producer/ledgerに今回のschema変更による直接の参照切れはない。
   
   推奨: 変更不要。8c generic core回帰だけを維持する。

## 親 brief 自体の所見

1. [実測] DW-O09 のうち、`FROZEN_MANIFEST`にregistry pathがないこととtracked `registry.jsonl` が0件なのは正しい。しかし「pinはpath側にもkey側にもない」は広すぎる。root pathは直接testでpinされ、claim filenameはslot payloadのSHA-256、capability digestはschemaとbindingのSHA-256から導出される。acceptance ledgerにも関連nodeidが345件ある。`orchestrator/tests/test_frozen_artifacts.py:41-88`, `orchestrator/tests/test_attempt_registry_core_s8b_profile.py:347-355`, `orchestrator/campaign/s8b_attempt_registry.py:825-839,1317-1324`, `orchestrator/campaign/attempt_registry_core.py:262-273`, `orchestrator/tests/acceptance_duration_ledger.json:2197`
   
   判定: real。成果物影響: claim path、capability参照、test node参照はschema/slot変更で変わる。凍結成果物のbytes pinは変わらない。
   
   推奨: 「FROZEN_MANIFESTとtracked artifactのpinは0」に限定する。関連role/xdist mappingとdataclass object hash利用は見つからなかったが、digest由来keyは存在すると記録する。

2. [実測] DW-O10 の書込み列挙は主体を混ぜている。adapterはregistry、claim、receipt、stagingを書き、provisioning経由で `ledger.lock` も作りうるが、consumption markerは書かず読むだけである。markerと `attempt-ledger.jsonl` はadmissionの `consume_attempt_ticket()` が書く。`orchestrator/campaign/s8b_attempt_registry.py:686-763,1028-1047,1401-1437,1458-1476`, `orchestrator/campaign/s8b_holdout_admission.py:655-695,4349-4392`
   
   判定: nit。成果物影響: `output/` の凍結成果物は書かないという結論は維持されるが、crash時に残りうる共有root file種のinventoryが不正確である。
   
   推奨: adapter-owned、admission-owned、provisioning-ownedに分け、`ledger.lock` と `attempt-ledger.jsonl` を明記する。

3. [実測] live root の値はbriefどおりである。freeze directoryは `db07b575...` の1本、2段v1 registryは193行、catalogは96行で、registryはfreeze 1 + start 96 + seal 96、terminal/recoveryなしである。`/work/1/SFC/tanab/izanagi/.git/izanagi/s8b-holdout-admission-v1/floor-attempt-registries/db07b575390d1e6e76763c9dc7f5be9e07e270e101cd763eabc973b77e59cb41/d388477f0272b8d41fbc0e82956841cf5eff45f68b0c8fd40e74dc1bb6dae920/registry.jsonl:1`, `/work/1/SFC/tanab/izanagi/.git/izanagi/s8b-holdout-admission-v1/floor-attempt-registries/db07b575390d1e6e76763c9dc7f5be9e07e270e101cd763eabc973b77e59cb41/consumption-catalog.jsonl:1`
   
   判定: refuted。成果物影響: 本番freezeのcertified選択には直接影響せず、同fixture freezeの横断replayだけがfail-closedで停止する。
   
   推奨: 書換えず、同shape fixtureで列挙と拒否を固定する。

4. [実測] 編集面の重なりは再現した。`worktree-dev-wave-t524-slot-experiment-unit` は `attempt_registry_core.py` の `_parse_genesis` 直後へ29行追加しており、本waveのcore編集位置に近い。現在のprocess照合では稼働codex/claudeは0件だった。`orchestrator/campaign/attempt_registry_core.py:654-738`, `brief.md:115-117`
   
   判定: refuted。成果物影響: 現時点の値や受理集合は変わらないが、統合時にhunkずれの可能性がある。
   
   推奨: 実装開始時に対象branchを再base比較する。

5. [実測] submodule前提は現在のworktreeでは古い。recursive statusはccbench、shirakami、googletestの3件すべてrevision付きで、googletestは `f8d7d77...` に展開済みである。`.gitmodules:1-4`, `external/ccbench/.gitmodules:1-3`, `external/ccbench/third_party/shirakami/.gitmodules:1-3`
   
   判定: nit。成果物影響: registry成果物には影響しないが、「recursive init rc=1」を現行開始条件には使えない。
   
   推奨: briefを「当時の観測」と限定し、実装wave開始時に再測する。

6. [実測] B1 spool fragmentはworklog 1件、decisions 1件とも健在で、未landであることとcapability契約を保持している。`docs/spool/worklog/2026-09-02-dev-wave-t2107-t1851-b1-1.md:1-44`, `docs/spool/decisions/2026-09-02-dev-wave-t2107-t1851-b1-2.md:44-78`
   
   判定: refuted。成果物影響: 後続fold時の参照は失われていない。
   
   推奨: 段7でmain側rotation後のdigestだけ再確認する。

## 分割判定への所見

1. [実測] A1'を「v1 productionを維持し、v2 public mutationを明示拒否する加法的checkpoint」とする分割は静的には成立する。既存v1 symbol、legacy recovery path、schedulerの4軸readerを残せば、現行nodeを必然的に赤にする具体入力は確認できなかった。`orchestrator/campaign/s8b_holdout_admission.py:5363-5622`, `orchestrator/campaign/s8b_scheduler_accounting.py:319-350`, `s2-plan.md:36-43`
   
   判定: refuted。成果物影響: A1'単独では新規certified成果物を発行せず、既存v1台帳値と参照を維持できる。
   
   推奨: A1'ではv2 profileをpublic create/read/reserve/resumeへ渡さないことをtestで固定する。

2. [実測] A1'/A2'の分割方針は維持できるが、A2'境界は未完成である。前節の3 blocker、すなわちtrusted raw factsでないterminal projection、v1固定 `_assert_profile`、4軸固定row lookupを閉じない限り、「A2'でA全契約完成」は成立しない。`s2-plan.md:38-43,282-374`, `orchestrator/campaign/s8b_attempt_registry.py:315-448,785-808`
   
   判定: real。成果物影響: A1'は整合しても、A2'でv2が全拒否またはmeasurement slot誤参照となり、台帳配線とcertified proofが完成しない。
   
   推奨: 分割は維持し、A2'の固定境界へ3 blockerのsymbol、引数、比較規則、正負testを追記してから実装へ送る。

3. [実測] 1 wave非分割案を採らない判断には現物上の根拠がある。直接test面153 node、adapterだけでもv1型のhard-coded参照が20箇所あり、core/profile/adapterの共有hunkも広い。`s2-plan.md:5-16,30-39`, `orchestrator/campaign/s8b_attempt_registry.py:121-1769`
   
   判定: refuted。成果物影響: 1 waveへ戻すとfix 3巡以内の収束根拠がなく、受理集合と参照の同時誤修正リスクが増える。
   
   推奨: A1'/A2'の2分割を採る。

4. [実測] land前提の違反はない。planはA1'とA2'を含む全checkpointをunlandedで保持し、配線とproof consumer完成後のみ同一変更単位でlandするとしている。受入全走をA単独のland条件にもしていない。`s2-plan.md:41-45,473-477`, `refs/decisions-verbatim.md:90-105`
   
   判定: refuted。成果物影響: writer-onlyまたはverifier-onlyの先行landによる恒真保証は生じない。
   
   推奨: この条件を段9まで維持する。

## 総括

- [実測] blockerは3件である。`s2-plan.md:164-169,282-374`
- [実測] 最重は、sealed terminalがlauncher所有のraw factsではなくcampaign自己申告値を再読する点である。`orchestrator/campaign/s8b_floor_campaign.py:6077-6217`
- [実測] 他2件はv1固定 `_assert_profile` によるv2全拒否と、4軸row lookupによるmeasurement ordinal衝突である。`orchestrator/campaign/s8b_attempt_registry.py:315-448,785-808`
- [実測] lock分割、pre-lock hook、例外時のlock/staging処理は成立する。`orchestrator/campaign/s8b_holdout_admission.py:698-726,5115-5227`
- [実測] A1'/A2'分割とunlanded checkpoint方針は維持可能だが、A2'境界へ3 blockerの修正を追記する必要がある。`s2-plan.md:36-45`
- [実測] sandboxはread-onlyとし、pytestは実行していない。静的検査のみであり、緑は報告しない。