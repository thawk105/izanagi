## 総括

blocker 1 は **real [実測]**。ただし「全 attempt で必ず衝突」ではなく、launcher の pre-probe が competing になった到達可能枝で衝突する。既存受理集合を保つ既設 seam / 2 段 API は無い。  
blocker 2 も **real [実測]**。campaign retry 軸は `measurement_ordinal`、registry recovery 軸は `attempt_ordinal` であり、現契約と fixture は後者へ誤って束縛している。  
したがって「現契約と既存 fixture を一切変えずには plan が成立しない」という総論は変わらない。ただし 9 file の内訳、v5 alias 変更、変異 4/5/8/12/13 は訂正が必要である。  
pytest、campaign、性能測定は実行していない。

## 所見 A-1 — blocker 1 の発火条件

**real [実測]**

- v2 は marker 非 null を `_checked_reservation_policy()` が要求する: `orchestrator/campaign/s8b_floor_attempt_launcher.py:577-584`。
- registry も marker 無しを `s8b_attempt_registry.py:2510-2517` で拒否する。
- launcher は `_reserve():985-990` を pre-probe `:997` より先に実行する。
- marker は `consume_attempt_ticket()` が file と ledger を `s8b_holdout_admission.py:4388-4392` で永続化した後、`:5034-5058,5094-5103` の再検証を経て発行される。
- launcher の probe が competing なら capture は `s8b_floor_attempt_launcher.py:1004-1018` で実行されず、terminal の `probe_before.competing=True` が残る。
- holdout inspector は marker 非 nullかつ completed session の pre-probe competing が true のとき、`s8b_holdout_admission.py:6733-6741` で `attempt-ledger-coverage-mismatch` を発火する。

campaign の現行値は固定 false ではない。`_run_session()` は `strict_probe()` の実結果を `s8b_floor_campaign.py:6243-6256` で読み、既存の competing branch を成果物へ記録する。既存正例も「全 session が pre-probe competing なら attempt row は 0」を `test_s8b_holdout_admission.py:3998-4006` で受理している。

「必ず反する」は字義上は過大で、`competing=False ∧ markerあり` は inspector が受理する。だが competing は実行時に到達可能なので、blocker 自体は real である。

成果物影響: 該当枝では holdout admission receipt が作れず、result の self-check と certified 到達が停止する。

推奨: competing branch を消したり inspector を緩めたりせず、launcher が clean pre-probe を確定してから消費・予約する設計を裁定する。

## 所見 A-2 — 既存 seam / 2 段 API

**real [実測]**

既存の production seam では解けない。

- `floor_post_probe_capability()` は launcher 私有の固定 probe を発行するだけ: `s8b_floor_attempt_launcher.py:339-350`。
- production 入口はその capability を `:1189-1215` で要求し、reservation supplier や marker supplier を受け取らない。
- dependency 注入可能なのは test 専用 `_launch_floor_attempt_for_test():1218-1262` だけである。
- campaign の外側 probe 後に marker を作る案も、launcher が再度 probe するため、その二回の間の競合を閉じない。

成果物影響: 既存 API の組合せだけでは、pre-probe competing の既存受理と全 production attempt の registry 化を同時に満たせない。

推奨: 新しい launcher-owned 2 段処理が必要。これは既存 seam の利用ではなく API 設計変更である。

## 所見 A-3 — blocker 2 と 5 軸の意味

**real [実測]**

v2 `slot_id` は `s8b_attempt_profile.py:159-168,238-245` により次の 5 軸である。

1. `slot_id[0]`: `freeze_holdout_key`
2. `slot_id[1]`: `configuration_id`
3. `slot_id[2]`: `repetition`
4. `slot_id[3]`: `measurement_ordinal`
5. `slot_id[4]`: `attempt_ordinal`

`series_key()` は最初の 4 軸で、`attempt_ordinal` はその series 内の recovery 軸である: `s8b_attempt_profile.py:247-256`。

一方、campaign 契約は planned に `retry_ordinal=None`、retry に `1..retry_slots_per_cell` を要求する: `s8b_floor_contract.py:248-270`。holdout 側も planned を ordinal 0、retry を campaign retry ordinal として `round-1` とともに導出する: `s8b_holdout_admission.py:4979-5000`。adapter はこれを `slot.measurement_ordinal` へ渡す: `s8b_attempt_registry.py:2367-2370`。

しかし terminal leaf は以下を要求する。

- `retry_ordinal` は null 不可の非負整数: `s8b_terminal_evidence.py:760-768`
- `retry_ordinal == slot_id[4]`: `:1140-1157`

さらに production registry は `slot.attempt_ordinal != 0` を `s8b_attempt_registry.py:2534-2538` で拒否する。したがって:

- planned: `None` は leaf の型検査で拒否
- retry: `1/2` は production で常に 0 の `slot_id[4]` と不一致

となる。

成果物影響: planned と retry のどちらも production sealed terminal へ運べず、registry terminal と result v5 proof を完成できない。

推奨: `retry_ordinal = None if measurement_ordinal == 0 else measurement_ordinal` という erratum が最小である。

## 所見 A-4 — plan が見落とした second consumer

**real [実測]**

terminal leaf だけではない。adapter/replay 側も `campaign_record.retry_ordinal == slot.attempt_ordinal` を `s8b_attempt_registry.py:1394-1429` で独立に要求する。

既存 fixture も両方の誤束縛を固定している。

- terminal fixture: `slot_id=(...,7,0,2)` と `retry_ordinal=slot_id[4]`: `test_s8b_terminal_evidence.py:124-142,159-169`
- registry fixture: `kind="planned"` なのに `retry_ordinal=slot.attempt_ordinal`: `test_s8b_attempt_registry.py:367-388`
- issuer/replay の負例も retry ordinal transplant を pin: `test_s8b_attempt_registry.py:4300-4372`

成果物影響: leaf だけ訂正しても terminal 発行時または durable replay 時に同じ成果物が拒否される。

推奨: ordinal 裁定後は `s8b_terminal_evidence.py` と `s8b_attempt_registry.py`、両 test file を同じ変更単位で直す。

## 所見 A-5 — v5 のための新 alias

**refuted [実測]**

`PRODUCTION_RESULT_SCHEMA` の新設は必須でない。既に:

- `RESULT_SCHEMA_V5` と readable set: `s8b_floor_contract.py:35-40`
- v5 exact key 集合: `:88-100`
- schema 引数つき key 導出: `:170-187`
- v5 pure/live verifier: `s8b_floor_stats.py:753-819,1155-1193`
- 対応 fixture: `test_s8b_floor_contract.py:187-194,416-435`

が存在する。campaign が production branch だけ `_floor_contract.RESULT_SCHEMA_V5` を選べば足りる。

成果物影響: contract alias を増やさず production result だけ v5 にでき、既存 v4 consumer と alias の値は不変に保てる。

推奨: `s8b_floor_contract.py` と `test_s8b_floor_contract.py` は C3 の変更対象から外す。

## 9 file 見積りの検査

**plan の 9 file 集合は refuted [実測]。ただし推奨設計を採る場合、code/test/ledger の件数だけは偶然 9 に戻る。**

削れる file:

- `orchestrator/campaign/s8b_floor_contract.py`
- `orchestrator/tests/test_s8b_floor_contract.py`

不足している file:

- `orchestrator/campaign/s8b_attempt_registry.py`
- `orchestrator/tests/test_s8b_attempt_registry.py`
- 受理集合を維持する launcher 2 段化を選ぶなら:
  - `orchestrator/campaign/s8b_floor_attempt_launcher.py`
  - `orchestrator/tests/test_s8b_floor_attempt_launcher.py`

推奨設計での最小 code/test/ledger 集合は次の 9 件である。

1. `orchestrator/campaign/s8b_floor_campaign.py`
2. `orchestrator/campaign/s8b_floor_attempt_launcher.py`
3. `orchestrator/campaign/s8b_terminal_evidence.py`
4. `orchestrator/campaign/s8b_attempt_registry.py`
5. `orchestrator/tests/test_s8b_floor_campaign.py`
6. `orchestrator/tests/test_s8b_floor_attempt_launcher.py`
7. `orchestrator/tests/test_s8b_terminal_evidence.py`
8. `orchestrator/tests/test_s8b_attempt_registry.py`
9. `orchestrator/tests/acceptance_duration_ledger.json`

ただし契約本文は追記訂正方式なので、ordinal erratum の新規文書を数えれば変更一式は最低 10 file である。C3b の値域 receipt と README はさらに別である。

波及確認:

- `test_ccbench_spawn_sites.py:895-910,2642-2720` は campaign の行番号 4707/8636 を exact pin する。編集しない方針は成立するが、変更後もその前方の物理行数を保存する必要がある。
- terminal evidence の public signature/import pin は既存 `test_s8b_terminal_evidence.py` 内で閉じる。
- perf AST inventory は新しい perf 判定を作らなければ追加 file を要求しない。
- `s8b_holdout_freeze.py:1431-1442` と `s8b_ratified_freeze.py:2399-2408` は依然 v4 alias を要求する。C3 の編集対象ではないが、v5 result は D2 まで両 consumer に到達できない。

成果物影響: C3 は v5 result を自己検査できるが、holdout/ratified freeze への参照は D2 まで未接続のままである。

## 親 brief の 3 前提の検査

### P1-1 F660 不発火

**real [実測]。ただし「発火実測」ではなく静的確認である。**

main 側登録簿には `floor_campaign.sh` が `dispatch-required`、`submit_floor.sh` が `local-ok` として存在する: `tools/pegasus/admission_registry.json:70-74,340-344`。現 checkout と main のこの 3 file の diff は 0 だった。

guard は exact path の登録を `hooks/guard_bash.py:614-629,1205-1215` で参照する。submitter は wave checkout の HEAD、clean tree、job script blob を `submit_floor.sh:220-283` で束縛し、repo root から qsub する: `:647-666`。job body も同じ HEAD を `floor_campaign.sh:743-786` で再検査し、その checkout の campaign を `:1175-1220` で起動する。

成果物影響: 既存 2 path を通常どおり使い、実装後に commit 済み clean tree から投入する限り、F660 は C3b を分割させる理由ではない。

推奨: brief の表現を「main 登録簿と guard の静的確認。hook 発火や qsub 成功は未実測」と限定する。

### P1-2 5 file 仮定

**refuted [実測]**

marker chronology は launcher、ordinal は leaf と adapter の双方へ届く。campaign/contract/test 2 本だけでは閉じない。

成果物影響: 5 file で止めると competing branchか durable terminal replayのどちらかが未接続になる。

推奨: C3a/C3b 分割は維持し、C3a の code/test/ledger 上限を上記 9 fileへ改める。

### P1-3 到達経路 0 だから凍結面を動かさない

**推論は refuted [実測]、結論は維持可能。**

契約 v3.1 の「到達経路 0」は C1b 単独時点の事実である: `contract-v3.1.md:35-46,455-459`。C3 の目的そのものが production caller を新設することなので、その事実を変更後へ一般化できない。現状の grep では production caller は 0 件だったが、C3 後は 0 ではない。

一方、凍結 23 件を動かさない結論は、v5 が既に readable schema であり、campaign が新規 result にだけ v5 を選び、global v4 alias と既存 frozen bytesを変えないことから別に導ける。

成果物影響: 既存 frozen bytes は不変にできるが、新規 v5 result の consumer 到達は D2 まで 0 のまま。この制限を「既存 certified artifact が変わらない」と混同してはいけない。

推奨: `git diff --stat` は非衝突確認に限定し、reachability、schema compatibility、受理集合の根拠には使わない。

## 変異候補の帰属検査

ここでの real は期待 node へ単独帰属可能、refuted は候補が不成立または過剰決定、という意味である。

| # | 帰属判定 | 検査 |
|---:|---|---|
| 1 | **real [推測]** | launcher call count を downstream 検証前に直接 spy すれば単独帰属できる。成果物影響: certified path が旧 measure seamへ退行する。 |
| 2 | **real [推測]** | registry plan helper の exact slot set を直接比較すれば単独帰属できる。成果物影響: 特定 round/retry の予約が不可能になる。 |
| 3 | **real [実測]、条件つき** | helper を直接検査すればよい。integration だけだと marker identity `s8b_holdout_admission.py:5198-5216` でも落ちるため過剰決定になる。成果物影響: authorization と registry repetition が不一致になる。 |
| 4 | **refuted [実測]** | `schedule_row_sha256` は `_SCHEDULE_KEYS={seq,round,cell_id}` の digestで、measurement ordinal は `slot_id[3]` に別束縛される: `s8b_floor_contract.py:87,223-229`、`s8b_attempt_profile.py:238-245`。成果物影響: test 名が存在しない保証を主張する。 |
| 5 | **refuted [実測]** | `gate-input-values` producer は repo に存在せず、C3b の手作業成果物しか plan されていない。変異させる production locus が無い。成果物影響: receipt の production provenance を機械保証できない。 |
| 6 | **real [実測]、条件つき** | exact issuer 拒否を assert すれば成立する。generic campaign failure だけでは他の marker mismatch と区別できない: `s8b_holdout_admission.py:5159-5171`。成果物影響: registry reservation 前に停止する。 |
| 7 | **real [推測]** | journal と launcher return の cross-link は現状無いため、byte equality の専用 test は独立価値がある。成果物影響: registry 証拠と result session が別内容になる。 |
| 8 | **refuted [実測]** | 「every emitted session terminal」は広すぎる。pre-probe competing は既存契約上 marker/attempt row 0 が正例: `test_s8b_holdout_admission.py:3998-4006`。成果物影響: 正当な competing session を拒否する。`every consumed non-competing session` へ限定すれば再候補化できる。 |
| 9 | **real [推測]** | production schema の exact assertion は独立している。成果物影響: registry proofを持たない v4へ退行する。 |
| 10 | **real [実測]、条件つき** | exact reason `attempt-registry-prefix-head-mismatch` を pin すれば成立する。generic self-check failure だけでは過剰決定: `s8b_attempt_registry.py:1077-1084`。成果物影響: result が実 registry prefixを参照しない。 |
| 11 | **real [推測]、ordinal 裁定後のみ** | 現在は「変異」ではなく既存 baseline そのもの。erratum 適用後に planned/retry 対を直接検査すれば有効。成果物影響: retry terminal が recovery 軸へ逆戻りする。 |
| 12 | **refuted [実測]** | live inspector は意図的に historical prefix を受理する: `s8b_attempt_registry.py:1057-1061,1077-1084`。finalize は pending bytes の決定性を要求する: `s8b_floor_campaign.py:6997-7008,7030-7049`。無条件 recapture は別 run の追記で bytes を変え得る。成果物影響: finalize-pending の冪等 publishを壊す。 |
| 13 | **refuted [実測]** | launcher API は `classified_at` callable を 1 本だけ受け、classification と terminal に `s8b_floor_attempt_launcher.py:1046,1079` で使う。campaign だけに「別 callable」へ変異させる locus が無い。成果物影響: 現候補のままでは何も検査しない。 |
| 14 | **refuted [実測]** | duplicate session は holdout inspector `s8b_holdout_admission.py:6601-6605`、terminal 済み slot の resume は `s8b_attempt_registry.py:3638-3641` でも拒否される。どの gate が kill したか分離しない test は過剰決定。成果物影響: duplicate が入れば既に artifact-invalid になる。 |

## 段 4 へ回す設計択一

### 択一 1 — pre-probe competing と marker

- **(a) launcher-owned 2 段処理。推奨。** 固定 pre-probe を先に実行し、clean の場合だけ issuer-backed admissionから markerを消費・検証して reserve/capture する。pre-probe competing は markerもregistry terminalも作らない明示的 unconsumed branchにする。
- **(b) marker無しの v2 `not-consumed` registry terminalを新設する。** proof coverageは強くなるが、契約 v3.1 の「E1 は not-consumed を出さない」を改版する大変更。
- **(c) markerありの pre-probe competingをholdout inspectorで受理する。** 既存受理集合を広げるため却下。

### 択一 2 — campaign retry ordinal

- **(a) erratumで `slot_id[3]` に束縛する。推奨。** `measurement_ordinal==0` は planned の `None`、`1..N` は retry ordinal。leaf、adapter、両 fixtureを同時更新する。
- **(b) §1.5 を維持し `attempt_ordinal` をcampaign retry軸へ転用する。** registryのrecovery series semanticsと `attempt_ordinal!=0` 拒否を全面変更するため非推奨。
- **(c) nullableな専用 `campaign_retry_ordinal` をslot/claimへ追加する。** 意味は明瞭だがschema、codec、genesis、receipt全体へ波及する。

### 択一 3 — production result schema

- **(a) campaign が既設 `RESULT_SCHEMA_V5` を直接選ぶ。推奨。**
- **(b) `PRODUCTION_RESULT_SCHEMA` alias を追加する。** 動作上不要で2 file増える。
- **(c) global `RESULT_SCHEMA` をv5へ変更する。** holdout/ratified consumerをD2前に壊すため却下。

### 択一 4 — 単位分割

- **(a) C3aを上記9 code/test/ledger + ordinal erratum、C3bをfresh campaignと値域receiptに分ける。推奨。**
- **(b) C3を延長して実装、commit、Pegasus実走まで1単位で行う。** F660には当たらないが、blocker裁定と実測が混在する。
- **(c) D2 consumer変更までC3へ混ぜる。** 依存順と責務境界を崩すため却下。