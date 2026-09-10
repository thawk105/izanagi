## 1. pin 閉包 (分類つき表)

分類は次の意味で用いる。

- **(i) live copy**: g2 移行に合わせて変更する。
- **(ii) 独立 golden**: 移行対象ではない。用途を確認して維持または明示的に改訂する。
- **(iii) 凍結 snapshot・歴史記録**: 変更しない。

検索対象は指定どおり `orchestrator/`、`tools/`、`hooks/`、`docs/`、`output/env/`、`output/s8b-freeze/` に限定した。`output/insights/` は除外した。`tools/` と `hooks/` には対象 3 値の出現はなかった。

### g1 contract hash `e576e9cd…`

| 出現 | 分類 | 処置 |
|---|---:|---|
| `orchestrator/campaign/env_contract_activations/00000001.json:1` | (iii) | serial 1 の権威記録。変更禁止 |
| `orchestrator/tests/test_env_contract.py:74` | (ii) | `EXPECTED_GENERATION_HASHES` の g1 golden。維持 |
| `orchestrator/tests/test_env_contract.py:1136` | (ii) | 関数を g1 golden として改名し、`:1125` の対象だけ `GENERATIONS["pegasus"][0]` へ変更。hash 自体は維持 |
| `orchestrator/tests/test_env_contract_activation.py:42` | (ii) | serial 1 の独立 bytes golden。維持 |
| `orchestrator/tests/test_s8b_floor_campaign.py:5917` | (ii) | 既封印 chain の歴史 golden。維持 |
| `output/s8b-freeze/floor_protocol.json:1` | (iii) | 凍結 protocol。変更禁止 |
| `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:12,570` | (iii) | 凍結実測記録。変更禁止 |
| `docs/phase3-8b-restart-runbook.md:42` | (iii) | 2026-08-10 時点の実測表。行自体は維持し、後段に g2 発効の supersession を追記 |
| `docs/archive/worklog-phase3-0719.md:45` | (iii) | 歴史記録 |
| `docs/archive/worklog-phase3-0806-256-261.md:10` | (iii) | 歴史記録 |
| `docs/archive/worklog-phase3-0807-278-279.md:414` | (iii) | 歴史記録 |
| `docs/archive/worklog-phase3-0807-285.md:251` | (iii) | 歴史記録 |

### activation head `f7807285…`

| 出現 | 分類 | 処置 |
|---|---:|---|
| `orchestrator/campaign/env_contract.py:375` | (i) | `398b1920…` へ変更 |
| `orchestrator/campaign/env_contract_activations/00000001.json:1` | (iii) | serial 1 の state hash。変更禁止 |
| `orchestrator/tests/test_env_contract_activation.py:37,40` | (ii) | serial 1 の独立 state/bytes golden。維持 |

### g1 較正 SHA `753f535a…` と content-addressed path

| 出現 | 分類 | 処置 |
|---|---:|---|
| `orchestrator/campaign/env_contract.py:256,258` | (iii) | g1 の歴史 registry entry。削除・変更禁止 |
| `orchestrator/tests/test_env_contract.py:64-65` | (i) | 既知例外集合から削除 |
| `orchestrator/tests/test_env_contract.py:278,281` | (i) | current lookup golden を g2 path/SHA へ変更 |
| `orchestrator/tests/test_env_contract.py:1133-1134` | (ii) | g1 contract golden として維持。`:1124-1125` を g1 明示参照へ変更 |
| `orchestrator/tests/test_env_attestation.py:1299-1300` | (ii) | g1/g2 両登録較正を受理する独立 leaf test。維持 |
| `orchestrator/tests/test_s8b_floor_campaign.py:5914` | (ii) | 既封印 chain の歴史 golden。維持 |
| `orchestrator/tests/test_silo_ladder_rung1_evidence.py:73` | (ii) | `HISTORICAL_SILO_EVIDENCE_IDENTITY`。維持 |
| `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:508,517` | (ii) | g1 実測 hostname の独立 positive control。契約 current pin ではないため維持 |
| `docs/decisions.md:17896` | (i) | g2 較正、実在 positive nodeid、充足へ更新 |
| `docs/pegasus-runbook.md:711` | (iii) | 2026-07-19 の g1 登録事実は維持。直後に g2 current を追記 |
| `docs/phase3-8b-restart-runbook.md:94` | (iii) | g1/g2 の歴史比較。維持 |
| `docs/failures.md:3032` | (iii) | F97 の原因較正。維持し、`:3038-3040` の後へ解決記録を追記 |
| `docs/archive/worklog-phase3-0719.md:43` | (iii) | 歴史記録 |
| `docs/archive/worklog-phase3-0806-256-261.md:1937` | (iii) | 歴史記録 |
| `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json` | (iii) | filename 自体が content address。削除・改名禁止 |
| `output/env/pegasus/calibration/attempts/0_867876.nqsv/final-receipt.json:10` | (iii) | 発行履歴 |
| 同 `publish.json:3`、`job-staging/0:867876.nqsv/calibrate.stdout:14` | (iii) | 発行履歴 |
| `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:13,16,569` | (iii) | 凍結実測記録 |

`t419-probe-causality` 配下はすべて (iii) の実験記録であり、変更しない。完全な行集合は次のとおり。

| ファイル | 行 |
|---|---|
| `0_888740.nqsv/manifest.json` | `67,69,70,95,102,106,118,177,181,193` |
| `0_888740.nqsv/result.json` | `3,11,12,14,73,77,89,82596,82598,82599,82624,82631,82635,82647,82706,82710,82722` |
| `0_889279.nqsv/manifest.json` | `70,72,73,98,105,109,121,227,231,243` |
| `0_889279.nqsv/result.json` | `3,11,12,14,73,77,89,470376,470378,470379,470404,470411,470415,470427,470533,470537,470549` |
| `0_889310.nqsv/manifest.json` | `71,73,74,99,106,110,122,252,256,268` |
| `0_889310.nqsv/result.json` | `3,11,12,14,194,198,210,581275,581277,581278,581303,581310,581314,581326,581456,581460,581472` |
| `0_889400.nqsv/manifest.json` | `72,74,75,100,107,111,123,267,271,283` |
| `0_889400.nqsv/result.json` | `3,11,12,14,1026,1030,1042,679211,679213,679214,679239,679246,679250,679262,679406,679410,679422` |

追加の path pin 閉包として、旧 protocol は `orchestrator/tests/test_frozen_artifacts.py:41-49,90-123` で bytes hash `261cec1c…` と key membership を凍結されている。したがって旧 path の置換は不可である。live 固定参照は `certified_writer_admission.py:206-210`、`s8b_floor_campaign.py:160,793-794`、`tools/pegasus/floor_campaign.sh:947-965`、`s8b_holdout_freeze.py:46,1287-1299`、`s8b_prediction_runner.py:79,1438-1451` に残る。

## 2. env_contract.py の編集

必要な production 編集は次の 2 定数だけである。

- `orchestrator/campaign/env_contract.py:373`
  - `_ACTIVATION_HEAD_SERIAL: int = 2`
- `orchestrator/campaign/env_contract.py:374-376`
  - `_ACTIVATION_HEAD_STATE_SHA256` を `398b192013e0e3996ca225454049a14cb2866ef256b581fc3dfbfda02476bed8` へ変更

加えて `orchestrator/campaign/env_contract_activations/00000002.json:1` を create-only で追加する。canonical bytes は次の 1 行と末尾 LF である。

```json
{"activation_serial":2,"activation_state_sha256":"398b192013e0e3996ca225454049a14cb2866ef256b581fc3dfbfda02476bed8","active_contracts":[{"contract_sha256":"1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7","env_tag":"linux-baremetal","generation":1},{"contract_sha256":"1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c","env_tag":"pegasus","generation":2}],"previous_activation_state_sha256":"f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed","schema_version":"env-contract-activation/v1"}
```

根拠は以下。

- canonical JSON は `env_contract_activation.py:113-127`、state hash は `:130-164`。
- decoder は exact canonical JSON + LF を `:167-186` で要求する。
- chain、遷移、terminal head、ever-active union は `:332-422`。
- 発行 CLI も `tools/issue_env_contract_activation.py:194-212` で同じ bytes を作る。
- `GENERATIONS` は `env_contract.py:245-304` ですでに g1/g2 を持ち、g2 reviewed hash も `:275-282` にある。ここは触らない。
- `env_contract_activation.py` 自体にも変更不要。

## 3. 既知例外の空化

現状の壊れ方は明確である。

- `test_env_contract.py:62-67`: 1 件集合を空にする。
- `:841`: `len(...) == 1` が即失敗する。
- `:864-865`: 空集合なら全 current required calibration に `assert passes` を課す。これは残すべき本体である。
- `:867-868`: active registry 2 件、required 1 件の全走査確認。維持。
- `:869`: `self_failures == KNOWN...` は空集合との完全一致になり、「例外なし」を検査する。維持。
- `:885`: policy equality の別テストが例外数 1 に不当に依存して失敗する。

正しい書き換えは次の形である。

1. `:62-67` を immutable な空集合、例えば `frozenset()` にする。
2. `:839-840` を「current registry の全較正が自己整合し、synthetic 負例は落ちる」趣旨へ改名する。
3. `:841` を単に消さず、`assert KNOWN_SELF_INCONSISTENT_CALIBRATIONS == frozenset()` として性質 (c) を明示する。
4. `:842-869` は維持する。特に `:864-865` と `:869` が、空集合を真面目な「全件合格」として検査する。
5. `:871-881` の 3080.0 synthetic 帯外標本は維持する。述語自体が恒真化していないことを固定する。
6. `:885` は削除する。policy equality test と既知例外数は独立であり、ここで空集合 assertion を重複させない。

## 4. source identity pin

`orchestrator/qualification/contract.py:38-76` は一見すると path 列挙だけであり、`:64-65` に literal bytes hash はない。しかし実効 pin は bytes hash である。

- `contract.py:528-536`: `code_identity` の exact path set と各 SHA-256 形式を要求。
- `t126_driver.py:355-380`: 各 path の disk bytes を SHA-256 化し、記録 commit の Git blob SHA と比較。
- `t126_driver.py:383-392`: Git blob bytes の SHA-256 を計算。
- `t126_driver.py:395-434`: hash map を series preimage の `code_identity` へ格納。
- `contract.py:490-576`: preimage 全体を hash して `qualification_series_id` を作る。
- `qualification/identity.py:112-144`: 歴史 series は記録 commit の Git blobから再検証する。

したがって結論は「`:64-65` 自体は path list、下流で各 path の bytes hash を pin」である。

現在の静的 SHA-256 は以下だったが、literal golden としての出現は指定 6 ルート内にない。

- `env_contract.py`: `237b4403e6ef9d9f3d91305904890a6790e4b38fb681f5a19dcae34333f1992e`
- `env_contract_activation.py`: `679b6ef0d356d6d1d7377eee3846793757b7bc9a2e0b91f26f07d5d69741ef6b`

`env_contract.py` の編集により、新しい T126 実走は次を再発行する必要がある。

- 新しい `series-identity.json`
- 新しい `qualification_series_id`
- それに従属する submission、attempt identity、marker、result

`env_contract_activation.py` は未変更なのでその leaf digest は変わらない。activation record directory は `test_t126_pegasus_tools.py:1441-1460` で明示的に identity set から除外されている。既存 T126 成果物は `identity.py:137-144` が記録 commit の旧 blobを読むため、書き換えず歴史検証できる。

## 5. current 束縛経路の一覧と移行後挙動

| 経路 | g2 活性化後 |
|---|---|
| `s8b_floor_campaign.py:446-462,538-543` historical protocol | 記録 g1 hash を `resolve_by_contract_sha256` で解くため生存 |
| `s8b_floor_campaign.py:465-535,4626` live protocol | current g2 と記録 g1 を比較するため旧 protocol を拒否 |
| `s8b_floor_campaign.py:629-659` builder | g2 hash と現在の `511c9538…` を持つ新 protocol を組み立てる |
| `certified_writer_admission.py:177-214` | 固定旧 path を current 検査するため floor 投入を拒否 |
| `wal.py:1040-1085` | lock 記録 hash を歴史 resolver で解くため g1 WAL 検証は生存 |
| `s8b_ratified_freeze.py:974-979` | env tag の存在だけを見るため生存 |
| `s8b_ratified_freeze.py:2802-2813,3272-3279` | `launch_validate` は current g2 と照合し、g1 freeze を拒否 |
| `s8b_ratified_freeze.py:2816-2833,3282-3292` | `reverify_published_freeze` は歴史 g1 で再検証し生存 |
| `s8b_oracle_report.py:1257-1299,1713-1716` | manifest 記録 hash を歴史 resolver へ渡すため生存 |
| `reflux_source_closure.py:471-508` | authority manifest の記録 hash を歴史 resolver で解くため生存 |
| `autonomous_trial_completeness.py:245-275` | campaign lock の記録 hash を歴史 resolver で解くため生存 |
| `ident.py:276-324` | 記録 serial までの chain prefix を検証するため g1 activation tuple は生存 |
| `ident.py:327-386` | live resume は current-bound cfg と旧 g1 lock が不一致となり拒否。さらに `:365-373` の loader bytes 照合でも旧 `env_contract.py` binding は拒否される |
| `ident.py:465-480` | 新規 lock は g2 hash、serial 2、`398b…` を記録 |
| `silo_ladder_rung1.py:1584-1660` | 記録内の整合だけを見る歴史 `validate_evidence` は生存 |
| `silo_ladder_rung1.py:262-285,3541-3572` | old snapshot の current binding は、record 2 追加・loader bytes 変更・g2 calibration/hash の全てで拒否 |
| `silo_ladder_rung1.py:1956-2003,3777,4457-4486` | 新規取得・新規 binding は g2 を使う |
| `s8b_holdout_freeze.py:1275-1300` | 固定旧 floor protocol を current lookup に照合するため新しい freeze producer は拒否 |
| `s8b_prediction_runner.py:1438-1451,1542-1549` | builder が g2/`511c…` bytes を再導出し、旧 committed g1/`d706…` bytes と不一致になり seal を拒否 |
| `qualification/t126_driver.py:505,521,882-892` | current contract は g2。semantic fields は同じだが source identity が変わるため新 series が必要 |
| `certified_writer_admission.py:370-382` | T126 protocol の environment fields は g1/g2 で同じなので照合は継続し、較正だけ g2 になる |
| `pipeline.py:644-655` | g2 由来 object は通り、保持済み g1 object は exact current contract 不一致で拒否 |
| `pegasus_floor_scoping.py:77-79` | g2 較正 path を返す |
| `p3_s4_loop_trigger_gating.py:94-101,324-347,599` | Pegasus compute 分岐は g2 を bind/authorize。OTHER 分岐は linux-baremetal のまま |
| `s8b_oracle_driver.py:871` | Pegasus 実走 authorization は g2 |

その他の直接 `lookup` / `authorize` 経路は以下で、いずれも `ENV_TAG = "linux-baremetal"` なので本移行では値が変わらない。

- `s1_direct_comparison.py:295,794`
- `s6_sort_sweep.py:201,280,369,376`
- `sanity_silo.py:57`
- `p2_2.py:145`
- `backoff_repro.py:103,114`
- `backoff_sweep.py:87,102,109,121,174`
- `demo.py:58,67`
- `p3_s4_loop_sort.py:274,307,330,399,513`
- `p3_s4_loop.py:796,916,960,1049,1142`
- `s8a_trigger_sweep.py:297,380,471,478`
- `p3_s4_red.py:163,169,179`
- `p3_kickoff.py:107,112,119`

## 6. (P1)〜(P5) の検査

### P1

**意味論として成立するが、現行の運用経路のままでは成立しない。実在する起動循環がある。**

- 旧 protocol は `test_frozen_artifacts.py:41-49,90-123` で変更不能。
- 新 protocol builder は current g2 を使う (`s8b_floor_campaign.py:629-659`)。
- `freeze_protocol` は旧固定 path へ書く (`:793-794`) が、writer は create-only (`:686-722`) なので既存 file に上書きできない。
- public writer は実 repo の `output/s8b-freeze/` と `output/env/` を拒否する (`:725-743`)。
- admission は旧固定 path しか読まない (`certified_writer_admission.py:206-210`)。
- PBS job も旧固定 path を hardcode する (`floor_campaign.sh:947-965`)。

したがって g2 活性化後、**現存する official floor 投入経路だけでは次の床値測定を起動できない**。predecessor を許すべきではないが、P1 だけで「後続段が測ればよい」とするのは不完全である。

受理集合を広げない解決順は次のとおり。

1. 活性化前に versioned protocol path の束縛機構を追加する。
   - `certified_writer_admission.py:27-31,177-214`
   - `submit_floor.sh:7-75,331-372,466-495`
   - `floor_campaign.sh:428-463,947-965,1091-1127`
   - receipt v2 に exact `protocol_path` と raw `protocol_sha256` を含め、source commit の Git blob、safe relative path、current contract をすべて照合する。
   - v1 も必ず同じ current gate を通し、g2 後に g1 を通す例外は設けない。
2. serial 2 record と head を原子的に活性化する。
3. g2 活性化後に human 手番で新しい immutable protocol を generation-specific path へ発行する。旧 file は変更しない。
4. 新 receipt がその exact path/hash を束縛して floor v2 を投入する。
5. 新 protocol は旧 `FROZEN_MANIFEST` を書き換えず、別の generation golden で凍結する。

新 protocol の canonical path 規約は現行 repo に見つからなかったため、D96 手続の新決定で固定する必要がある。ここは author が推測して命名してはならない。

### P2

**成立する。** `REGISTRY` は active view (`env_contract.py:615-628`) なので g2 後の Pegasus required entry は g2 だけである。g1 は `GENERATIONS` と ever-active に残るが、current self-consistency 例外ではなくなる。

### P3

**成立する。** 旧 activation record、較正、floor protocol、silo evidence、probe-causality、T126 歴史 series は変更不要である。新 floor protocol は追加世代として発行し、旧 bytes を置換しない。

### P4

**成立する。再実装不要。**

- acquisition 前の自己比較は `orchestrator/calibrator/cli.py:719-731`。
- 計測後の自己比較と accepted/rejected 決定は `:762-791`。
- attempt/publish policy 同一性は `:800-810`。
- publish 後 bytes の再読込自己比較は `:835-845`。
- predicate 本体は `:408-425,484-524`。

g2 artifact の `quality.status=accepted` は `calibration-94a4b79fa31bba3c.json:1599-1601`、実ファイル SHA は `94a4b79f…` と一致した。

### P5

**成立する。** `s8b_approved.py:67` と現在の Git gitlink はともに `511c9538e4e8efa54b45cda62e72389ed3b706ec` である。activation commit でこの値を再編集する必要はない。後続の g2 protocol builder が `s8b_floor_campaign.py:639` へ焼く。

g2 較正 receipt の `d706650c…` (`calibration-94a4b79fa31bba3c.json:40`) は較正取得時の歴史記録であり、変更しない。

## 7. commit 順序

推奨順は次のとおり。

1. **運用 seam commit**
   - versioned protocol path/hash を receipt、static admission、job scriptへ通す。
   - predecessor contract は許さず、常に `validate_protocol_against_current` を使う。
2. **activation commit**
   - `00000002.json`
   - `_ACTIVATION_HEAD_SERIAL = 2`
   - `_ACTIVATION_HEAD_STATE_SHA256 = 398b…`
   - 関連テスト、決定記録、docs の current 状態更新
3. **human artifact commit**
   - g2/`511c…` の新 protocol bytes
   - generation-specific bytes golden
4. 後続段で floor v2 を投入する。

record と head は同一 commit が必須である。

- record だけ先行すると、loader は terminal serial 2 を読み、期待 serial 1 との比較 `env_contract_activation.py:408-416` で拒否する。
- head だけ先行すると、terminal serial 1 と期待 serial 2 が同じ箇所で拒否される。
- 発行 CLI も `issue_env_contract_activation.py:143-152` で同一 commit と process restart を要求している。

author の working tree では片側を先に編集する短い赤窓が避けられないが、その状態でテストや commit を確定しない。配備後は既存 process の authority cache を残さず再起動する。

## 8. テストで固定すべき性質

| 性質 | 既存または改訂先 |
|---|---|
| (a) g2 が active | 機構の既存正例 `test_env_contract_activation.py:1564-1571`。production 状態は `test_env_contract.py:378-384` を linux g1 / Pegasus g2 の明示 assertion へ改訂 |
| serial 2 bytes/head が production と一致 | `test_env_contract_activation.py:440-457` を、serial 1 bytes の単独 leaf 検証と production full chain serial 2 検証へ改訂 |
| (b) g1 が ever-active に残る | 既存 `test_env_contract.py:592-600`。g2 後も g1 が解決できることで production chain を担保 |
| g1 歴史 resolver の遅延較正検証 | 既存 `test_env_contract_activation.py:1855-1888,1891-1930` |
| g1 floor 歴史検証 | 既存 synthetic `test_s8b_floor_campaign.py:7325-7345,7429-7467` |
| (c) 既知例外が空 | `test_env_contract.py:839-881` を前節の形へ改訂。新規重複テスト不要 |
| predicate が恒真でない | 既存 synthetic 帯外標本 `test_env_contract.py:871-881` |
| (d) live admission が g1 protocol を拒否 | 既存 synthetic fresh/resume 負例 `test_s8b_floor_campaign.py:7470-7509,7616-7662` |
| 実 committed g1 protocol は歴史 OK / live 拒否 | `test_s8b_floor_campaign.py:7325` 付近へ 1 本追加し、実 `output/s8b-freeze/floor_protocol.json` に両 validator を適用する |
| g1/g2 contract hash golden | `test_env_contract.py:1124-1153` を g1 と g2 の独立 golden 2 本として維持。g1 側は `GENERATIONS[0]` を参照 |
| current lookup が g2 calibration | `test_env_contract.py:270-282` の path/SHA を g2 へ更新 |
| g2 は ever-active | `test_env_contract.py:618-621` を拒否から positive resolution へ反転 |
| registered だが never-active の拒否理由 | `test_env_contract_activation.py:1933-1939` を synthetic registered g3 へ変更し、g2 への依存を除去 |
| fork 後 lookup | `test_env_contract_activation.py:1984-2032` の独立期待値を Pegasus g2 hash へ変更 |
| issued suffix と source head の分離 | `test_env_contract_activation.py:1595-1638` を explicit head1/head2 fixture に分離し、存在しない production g3 を作らない |
| source identity closure | 既存 `test_t126_pegasus_tools.py:1441-1478`。record directory が含まれないことも維持 |
| 新 protocol path の単一束縛 | `test_pegasus_floor_tools.py:36-58,807-813,1882-1884,2035-2055` と `certified_writer_fixtures.py:110-149` を receipt v2 へ追随 |
| path seam の負例 | traversal、symlink、uncommitted blob、hash 不一致、receipt/job path 不一致、g1 protocol の current 拒否を追加 |

## 9. 未確認・リスク

- pytest、build、checker は一切実行していない。緑は主張しない。
- `00000002.json` はまだ存在せず、その bytes/hash は親 brief の実測値を採用した。
- versioned floor protocol の exact canonical path と、その user approval / freeze authority は現行実装・決定記録から確認できなかった。実装前に新 D で固定が必要。
- `docs/decisions.md` の次番号は現状 D431 の次だが、land 時の競合を確認して採番する。追記位置は現状 `:17939` 以降。
- `env_contract.py` 編集後の新しい source SHA と T126 series ID は実装 bytes が確定するまで未確認。
- 旧 campaign lock は歴史 tuple/WAL 検証には使えるが、live resume は source binding drift または g1/g2 不一致で拒否される。これを「全歴史経路が生存」と報告してはならない。
- source identity の一般語による初回探索 1 件は出力上限で打ち切られたため証拠に採用せず、上記結論は対象ファイルと exact hash の限定再検索で確認した。
- worktree への書込みはなく、`git status` は既存の untracked `output/insights/2026-08-16_t419-generation-migration/` だけだった。
- Web 検索は使用していない。

## 総括

- g2 活性化本体は serial 2 record の追加と head 定数 2 件の前進だけである。
- registry の g1/g2 定義と activation 機構は変更しない。
- record と head は必ず同一 commit に置き、配備後に process を再起動する。
- g1 は ever-active として残り、WAL、oracle report、reflux、歴史 floor 検証は生存する。
- current-bound floor、ratified launch、resume、silo current binding は意図どおり拒否へ転じる。
- 既知例外は空化できるが、全 active 較正の走査と synthetic 負例を維持する。
- `env_contract.py` の bytes 変更により、次の T126 は新しい series identity が必要になる。
- P1 の縮小は正しい一方、固定旧 protocol path により次の床値投入経路が実際に閉じる。
- versioned protocol path/hash seam を先に実装し、その後に活性化、人手での g2 protocol 発行、床値 v2 測定の順に進めるべきである。