# [T-529] 裁定後 file:line 実装プラン

本稿は静的検査に基づく。テストは実行しておらず、結果は主張しない。

## 1. 実装境界

本 wave で実装する保証は次に限定する。

- `GENERATIONS` は候補集合、activation record は current 選択の権威とする。
- activation record の trust root は、実行中 worktree の `HEAD`、すなわち運用上「レビュー済み git commit」と扱う commit snapshot。
- 各 writer は process-local receipt を取得し、最初の永続書込み直前に同じ process 内の activation state と再照合する。
- receipt、serial、state hash は成果物・sidecar・campaign identity に永続化しない。
- source に g2 を追加しただけでは current にしない。HEAD の activation record が g2 を選び、後述の evidence 述語を通った場合だけ current にする。
- historical resolver は既存配線を維持する。[s8b_ratified_freeze.py:2769-2837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_ratified_freeze.py:2769)、[s8b_ratified_freeze.py:3234-3254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_ratified_freeze.py:3234)、[s8b_oracle_report.py:1637-1645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_oracle_report.py:1637) の current/live と historical/read-only の分離は変更しない。

次は明示的に範囲外とする。

- `loop.py:62-70,139-145` の `env_contract=None` 経路と、その certified writer 閉包。
- `p3_s4_loop.py`、`p3_s4_loop_sort.py`、`p3_kickoff.py`、T419 PBS wrapper、floor protocol authoring utility の入口化。
- silo promotion。`silo_ladder_rung1.py` は ability probe のままで、receipt を結線せず、「silo 昇格入口は未実装」と記録する。
- process 間・成果物間で同じ activation state を使ったことの事後証明。
- 署名、外部 ledger、鍵管理、reviewer identity の機械検証。

## 2. Activation record

### 2.1 置き場所と形式

新設する。

```text
orchestrator/campaign/env_contract_activation.py
orchestrator/campaign/env_contract_activations/00000001.json
tools/issue_env_contract_activation.py
```

`00000001.json` は canonical one-line JSON + LF とする。top-level exact key は次の5個。

| key | 制約 |
|---|---|
| `schema_version` | exact str `"env-contract-activation/v1"` |
| `activation_serial` | exact int、1以上、bool拒否 |
| `previous_activation_state_sha256` | serial 1のみnull。それ以外は直前recordのstate hash |
| `active_contracts` | env_tag昇順の非空list。`GENERATIONS` のenv集合と完全一致 |
| `activation_state_sha256` | 小文字hex64 |

`active_contracts` の各行は exact に次の3 keyを持つ。

```text
env_tag: str
env_contract_generation: exact positive int
contract_sha256: lowercase hex64
```

無修飾の `generation`、`migration_epoch`、`bundle_hash` は新形式に入れない。

`activation_state_sha256` は自身を除く4 keyを
`sort_keys=True, separators=(",", ":"), ensure_ascii=True`
で直列化したbytesのSHA-256とする。初期recordは次の一行になる。

```json
{"activation_serial":1,"activation_state_sha256":"5bacfa7cbf6713cc1b53dd2f34df57ce183815bad5fb238a3fcd200c10f41f9c","active_contracts":[{"contract_sha256":"1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7","env_contract_generation":1,"env_tag":"linux-baremetal"},{"contract_sha256":"e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01","env_contract_generation":1,"env_tag":"pegasus"}],"previous_activation_state_sha256":null,"schema_version":"env-contract-activation/v1"}
```

### 2.2 検証述語

`env_contract_activation.py:[新設予定 1-500]` に次を置く。

- `:1-55` — 定数、`ActivationStateError`、trust boundaryのdocstring。
- `:56-115` — immutableな`ActivationRecord`、`ActivationState`、process-local `ActivationReceipt`。
- `:116-185` — duplicate key、非有限数、UTF-8、exact key、canonical bytes検査。
- `:186-260` — `git --no-replace-objects` によるHEAD tree列挙とblob読出し。
- `:261-335` — filename/serial連番、predecessor、state hash、env集合のchain検査。
- `:336-430` — generation選択とcalibration evidence検査。
- `:431-470` — `load_activation_state()`。
- `:471-500` — receipt発行・再照合。

各recordについて次をすべて要求する。

1. `NNNNNNNN.json` と `activation_serial` が一致し、1から欠番なく連続する。
2. serial 1のpredecessorはnull、以後は直前recordのstate hashと一致する。
3. active行はenv_tag昇順・重複なしで、登録env集合と完全一致する。
4. 指定generationが`GENERATIONS[env_tag]`に存在する。
5. rowの`contract_sha256`がその`GenerationEntry.contract.contract_sha256`と一致する。
6. calibration pathがrepo-relativeで、HEAD上のregular blobとして存在する。
7. HEAD blobとworking calibration bytesのSHAがともに`calibration_ref.sha256`と一致する。
8. `attestation_mode="required"` は canonical registered path、filename digest prefix、v2 schema、env_tag、clock、effective-clock policy、`quality.status=="accepted"`を要求する。
9. `attestation_mode="none"` の例外はcontract hash
   `1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7`
   の一件だけ。別env、別field、successor、同じlegacy bytesの再利用へ一般化しない。

較正のcross-field検査は [env_attestation.py:1060-1133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/env_attestation.py:1060) と同じ述語を再利用し、別実装を作らない。

### 2.3 「JSONを書いただけでは活性化しない」構造

- record一覧とrecord bytesはworking treeからではなく、HEAD tree/blobから読む。未commitの`00000002.json`はissuerの提案物にすぎず、実行中stateには現れない。
- recordは新しいcontractを定義できず、既存`GENERATIONS`の行を選択するだけ。
- `REGISTRY`はraw JSONや世代列末尾から構築せず、全述語を通過した`ActivationState.active_entries`だけから構築する。
- recordがg2を選んでも、calibration blobがHEADにない、working bytesが違う、schema/cross-field/qualityが不正ならmodule初期化をfail-closedにする。
- g2をsourceへ登録したがrecordがg1のままなら、module importは成功しても`lookup()`はg1を返す。

`tools/issue_env_contract_activation.py:[新設予定 1-180]` は現HEAD chainを検証し、全envの次状態を明示入力させ、serial・predecessor・contract hash・state hashを導出して`O_EXCL`で次recordを作る。自動commitや自動activationは行わない。docstringに「生成物はreview/commit前には権威を持たない」と明記する。

## 3. Trust rootのコード表現

`env_contract_activation.load_activation_state()` のdocstringは、少なくとも次の水準に固定する。

> activation authorityの入力は、現在のHEAD commitに含まれるrecordとcalibration blobである。「レビュー済み」はmaintainer workflow上のtrust assumptionであり、この関数がreview event、reviewer identity、commit署名を検証するという意味ではない。本関数が検証するのは、同一commit snapshot内のrecord chain、登録generation、contract hash、calibration evidenceの整合だけである。publisherを実行した主体、schedulerの実記録、commitの外部真正性、過去commitへのrollback耐性、変更されたPython process内でのmodule再束縛耐性は保証しない。

したがって、次を主張しない。

- acquisition receiptがpublisherの実行を証明すること。
- commit hashだけでauthor/reviewerが認証されること。
- chain suffixの削除や古いreview済みcommitへのcheckoutを検出できること。
- `ActivationReceipt`が攻撃的なPython introspectionやmonkeypatchに耐えること。
- 異なるprocessの成果物が同じserial/state hashを使ったこと。

`ActivationReceipt` の公開fieldは
`activation_serial` と `activation_state_sha256` のみとし、非直列化のprocess tokenを内部に持つ。`as_dict()`やartifact用serializerは作らない。

## 4. `env_contract.py` のfuse置換

[env_contract.py:97-160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/env_contract.py:97) は編集禁止領域とする。field集合、`_canonical_obj()`、hash計算を変更しない。

変更点は次のとおり。

- [env_contract.py:278-326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/env_contract.py:278)
  - `_validate_generations_without_bootstrap_fuse`を意味に合わせて`_validate_generation_structure`へ改名。
  - `validate_generations()`は構造・連番・successor・全hash一意性だけを検査する。
  - `len(sequence) != 1` の無条件拒否を削除する。
- [env_contract.py:342-352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/env_contract.py:342)
  - 現行の`sequence[-1]` viewを次へ置換する。

```python
GENERATIONS = MappingProxyType(_build_registry())
validate_generations(GENERATIONS)
_CONTRACT_SHA256_INDEX = _build_contract_sha256_index(GENERATIONS)
_ACTIVATION_STATE = load_activation_state(GENERATIONS, repo_root=...)
REGISTRY = MappingProxyType({
    env_tag: entry.contract
    for env_tag, entry in _ACTIVATION_STATE.active_entries.items()
})
```

- [env_contract.py:383-390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/env_contract.py:383)
  - `lookup(env_tag)`のsignature、例外、公開戻り型は変更しない。
  - 直後へ次を追加する。

```python
def admit_current(env_tag: str) -> tuple[
    ExecutionEnvironmentContract, ActivationReceipt
]: ...

def issue_activation_receipt() -> ActivationReceipt: ...

def assert_current_activation(receipt: ActivationReceipt) -> None: ...
```

`admit_current()`は同じ`_ACTIVATION_STATE`からcontractとreceiptを取得する。`assert_current_activation()`はexact receipt type、process token、serial、state hashに加え、`REGISTRY`のenv集合と各contract hashが`_ACTIVATION_STATE.active_entries`と一致することを再確認する。diskやHEADは再読せず、保証をprocess-local snapshotに限定する。

[env_contract.py:329-380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/env_contract.py:329) の全世代hash indexと`resolve_by_contract_sha256()`は維持する。

## 5. 六つの入口への結線

| 入口 | receipt取得点 | 最初の書込み直前の再照合 | 最初の書込み |
|---|---|---|---|
| floor | [s8b_floor_campaign.py:2750-2764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_floor_campaign.py:2750) のlookupを`admit_current()`へ置換 | `:2858`、single-process分岐より前 | claim `:2881`、非claim経路のrun dir `:2920` |
| oracle driver | [s8b_oracle_driver.py:745-812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_oracle_driver.py:745) の`_prepare_v2_execution()`で取得し`_V2Plan`へ保持 | [s8b_oracle_driver.py:1189-1201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_oracle_driver.py:1189) | `_acquire_g12_claim()` `:1201`、claim不要時は`_ensure_campaign()` `:1224` |
| oracle report | [s8b_oracle_report.py:1744-1762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_oracle_report.py:1744) でglobal receipt取得 | `_write_create_only()`のrequired引数とし、[s8b_oracle_report.py:1727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_oracle_report.py:1727) 内で再照合 | `path.open("x")` `:1728` |
| P3 autonomous | [p3_autonomous_workload_trial.py:1831-1855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/p3_autonomous_workload_trial.py:1831) の`run_trial()`入口 | `:1963`、registered/exploratory分岐より前 | lifecycle `:1965`、run root `:1975` |
| T-126適格性 | [t126_driver.py:862-874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/qualification/t126_driver.py:862) のlookupを`admit_current()`へ置換 | `:898` | `QualificationRoot.issue()` `:899` |
| selector seal | [s8b_prediction_runner.py:1538-1553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_prediction_runner.py:1538) のclean HEAD確認後 | `:1586` | provider生成が呼ぶ`artifact_root.mkdir()` [s8b_prediction_runner.py:1092-1101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/s8b_prediction_runner.py:1092) |

oracle reportはglobal state receiptとするため、`run_contract`を持たないStage 0 legacy manifestも現行どおり処理できる。historical contractの解決結果をcurrentへ貼り替えず、receiptはあくまでwriter processのactivation stateだけを検査する。

各入口では`EnvContractError`を既存の境界例外へ翻訳し、既存CLIのrefused/error契約を保つ。

- floor → `FloorCampaignError`
- oracle driver → `OracleDriverError`から`status="refused"`
- oracle report → `ReportError`または既存rc 2経路
- P3 → `AutonomousTrialError`
- T-126 → `QualificationDriverError`
- selector → `PredictionRunnerError`

`silo_ladder_rung1.py`には上記APIの呼出しを追加しない。

## 6. Positive controlとnegative control

`orchestrator/tests/test_env_contract_activation.py:[新設予定 1-650]` に対となる試験を置く。

### 合法なactive g2

`test_head_committed_g2_record_becomes_current`:

1. current Pegasus g1 calibration bytesへJSONとして無害な末尾空白を加え、別SHAにする。
2. 新SHAに対応する
   `output/env/pegasus/calibration/registered/calibration-<sha[:16]>.json`
   をtemp git repoへ置いてcommitする。
3. calibration path/SHAだけを変えたPegasus g2を作り、g1/g2の2世代mappingを作る。
4. serial 1はg1、serial 2はPegasus g2を選ぶvalid chainとしてtemp repoへcommitする。
5. [test_env_contract.py:618-632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/tests/test_env_contract.py:618) と同じmodule属性patch seamで、検証済みstate、`GENERATIONS`、index、`REGISTRY`を一組で注入する。
6. 次を要求する。
   - `lookup("pegasus") is g2`
   - receiptの`activation_serial == 2`
   - receiptのstate hashがserial 2 recordと一致
   - `assert_current_activation(receipt)`成功
   - historical resolverはg1とg2を双方解決できる

`generation > 1`または`activation_serial > 1`を無条件拒否する実装では、この正例が失敗する。したがって旧fuseを名前だけ変えた実装と観測的に区別できる。

### recordを欠くg2

`test_registered_g2_without_record_cannot_become_current`:

- generation mapping、g2 calibration、commit snapshotは上記正例と同一にする。
- serial 2 recordだけを存在させず、serial 1をchain tipにする。
- loaderは成功するが、`lookup("pegasus")`はg1のままで、g2をcurrentとして受理しない。
- `REGISTRY=sequence[-1]`へ戻す変異はこの試験で失敗する。

別の負例として、serial 2 JSONだけ存在してcalibration blobが未commit・dirty・rejected・env/clock不一致の各ケースを拒否し、「record JSONだけ」を十分条件にしないことを固定する。

## 7. 既存テストの期待値変更

期待値を単純に緩めず、旧fuseの拒否を新しいauthority層の正負対へ置換する。

| 既存テスト | 改訂 |
|---|---|
| `test_env_contract.py:375-380` `test_registry_and_lookup_are_generation_tail_view` | `activation_state` viewの検査へ置換。末尾期待は削除し、initial recordのactive rowとのobject identityを要求 |
| `test_env_contract.py:427-480` | helper改名に追随。public validatorがstructural g2を受けることと、recordなしではcurrentにならないことを分離 |
| `test_env_contract.py:540-554` | 「valid g2でもfuse例外」を、valid g2 candidateの構造受理＋activation record欠落時の非current化へ置換 |
| `test_env_contract.py:557-589` | import順を`generation validation → full index → activation load → REGISTRY`として固定 |
| `test_s8b_ratified_verify.py:702-724` | 旧fuse例外の期待を削除し、検証済みactive g2 stateを注入した上で「historical read-onlyはg1受理、liveはg2束縛」を維持 |
| `test_s8b_floor_campaign.py:4393-4424` | tailから手組みしたg2 fixtureを、activation stateとREGISTRYを同時patchするfixtureへ変更 |
| `test_silo_ladder_rung1_driver.py:926-947` | runtime identity閉包にactivation moduleとrecord群を加える場合、そのexact集合へ更新。ただしreceipt呼出しは期待しない |
| `test_t126_pegasus_tools.py:1281-1307` | T-126 code identityにactivation module、record、検証依存を含める期待を追加 |

次のgoldenは変更しない。

- `test_env_contract.py:251-279` の既存2 env値。
- `test_env_contract.py:1109-1138` の両contract hash。
- `test_s8b_protocol_builder.py:47-63,91-105` のcanonical protocol bytes/hash。
- committed floor、freeze、oracle、selector、qualification、silo成果物のbytes期待値。
- artifact schemaのexact key集合。

各入口テストには、activation拒否を注入し、最初のwrite leafが一度も呼ばれないtripwireを追加する。対応する正常系では既存成功期待を保持したまま、receipt再照合がwriteより先に一度だけ呼ばれたことを確認する。

## 8. Identity閉包

新しいruntime依存を既存identity機構へ追加するが、新しいdurable activation receiptとは扱わない。

- [qualification/contract.py:38-66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/qualification/contract.py:38)
  - activation module、初期record、`env_attestation.py`、schema/policy依存を`REQUIRED_CODE_IDENTITY_PATHS`へ追加。
  - activation directoryの全HEAD recordが集合に含まれることをテストし、次serial追加時の漏れを拒否。
- [silo_ladder_rung1.py:254-280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/orchestrator/campaign/silo_ladder_rung1.py:254)
  - runtime identity入力へactivation module/recordを追加するだけとする。
  - receipt発行・再照合は追加せず、promotion保護を主張しない。
- [t419_probe_causality.py:3491-3497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-impl/tools/pegasus/probes/t419_probe_causality.py:3491)
  - dirty scopeへactivation module/record directoryを追加するだけで、T419を入口に数えない。

これらの既存source identity hashは、新しいrunがどのsource inputsを使ったかを束縛するものにすぎない。六入口のserial/state同一性を事後証明したとは扱わない。

## 9. 成果物bytesと受理集合

`output/`配下の既存fileは一つも編集しない。receiptを次のどこにも追加しない。

- floor protocol/result/execution receipt
- oracle manifest/WAL/observations
- P3 lifecycle/journal/report
- T-126 series result/receipt
- selector journal/freeze
- silo evidence

受理集合の変化は次のとおり。

| 変化 | 扱い |
|---|---|
| structurally validな複数generation mapping | 意図したdata層の拡大 |
| HEAD recordとvalid evidenceを持つactive g2 | 意図したlive current集合の拡大。g2正例で固定 |
| sourceへ追加しただけのinactive g2 | current集合は拡大しない |
| dirty/uncommitted record | authority入力にならず、currentを変えない |
| malformed chain、未commit/不一致calibration、rejected quality | 新しいfail-closed縮小 |
| linux mode-noneの任意successor | exact g1 contract hash以外は拒否 |
| unknown env、既存contract hash、既存artifact schema | 不変 |

世代が一本でinitial recordだけの現状では、`REGISTRY`、`lookup()`、両contract hash、protocol builder bytesが従来と一致する正例を置く。

## 10. 実装単位

### 単位A — authority、record、identity閉包

先行して実装する。

```text
orchestrator/campaign/env_contract.py
orchestrator/campaign/env_contract_activation.py                 [新設]
orchestrator/campaign/env_contract_activations/00000001.json    [新設]
tools/issue_env_contract_activation.py                           [新設]
orchestrator/qualification/contract.py
orchestrator/campaign/silo_ladder_rung1.py                       [identity閉包のみ]
tools/pegasus/probes/t419_probe_causality.py                     [dirty scopeのみ]

orchestrator/tests/test_env_contract.py
orchestrator/tests/test_env_contract_activation.py               [新設]
orchestrator/tests/test_s8b_ratified_verify.py
orchestrator/tests/test_t126_pegasus_tools.py
orchestrator/tests/test_silo_ladder_rung1_driver.py
orchestrator/tests/test_t419_probe_causality.py
orchestrator/tests/README.md
```

HEAD blobがtrust inputになるため、A内部では次の順を取る。

1. parser、initial record、issuerをinertな状態で用意。
2. initial recordを含むcommit snapshotを作る。
3. `env_contract.py`をそのrecordからcurrent導出するよう結線。
4. authority正負対と既存goldenを確認する。

production用にuncommitted recordを受理するtest bypassは作らない。

### 単位B — 六入口のprocess-local gate

AのAPI確定後に実装する。

```text
orchestrator/campaign/s8b_floor_campaign.py
orchestrator/campaign/s8b_oracle_driver.py
orchestrator/campaign/s8b_oracle_report.py
orchestrator/campaign/p3_autonomous_workload_trial.py
orchestrator/qualification/t126_driver.py
orchestrator/campaign/s8b_prediction_runner.py

orchestrator/tests/test_s8b_floor_campaign.py
orchestrator/tests/test_s8b_oracle_driver.py
orchestrator/tests/test_s8b_oracle_report.py
orchestrator/tests/test_p3_autonomous_workload_trial.py
orchestrator/tests/test_t126_qualification_driver.py
orchestrator/tests/test_s8b_prediction_runner.py
```

A/Bの所有ファイルは素集合である。BはAのreceipt APIへ依存するため、並列landせずA完了後に開始する。

## 11. 実装後の検証予定

親が `tools/run_tests.py` 経由で次を確認する。ここでは未実行である。

- authority/parser/chain/evidence/receiptの新規試験。
- active g2正例とrecord欠落g2負例。
- 六入口すべてのpre-write tripwireと既存成功経路。
- historical g1再検証とlive g2 admissionの分離。
- contract hash、protocol bytes、artifact exact schemaの既存golden。
- T-126、silo、T419のidentity閉包。
- 関連試験後に全受入、`check_codex_agents.py`、`check_docs.py`。
- commit後に`check_ai_provenance.py`。
- `git diff -- output/`が空であること、およびD203の禁止語が新規code/docstring/test名へ入っていないこと。

## 総括

本プランは、親のP1「T-574でD196のconsumer配線要件は充足済み」とP2「production g2 artifactがないことを本waveの停止理由にしない」に明示的に依存する。

- P1への依存箇所はfuse置換そのものと、既存historical resolverを前提にしたg2正例である。P1を退けるなら単位Aの`REGISTRY`切替はlandできない。
- P2への依存箇所は、production artifact pathの代わりにtemp git commitと既存module属性patch seamでactive g2を発火させるpositive controlである。`DW-G04`をproduction artifact必須と解釈するなら、本プランは設計記録に戻して停止する必要がある。

P1/P2を親のprovisional裁定どおり採る限り、六件のユーザー裁定、既存contract hash・成果物bytes不変、g2成功正例、record欠落負例、silo/legacy writerへの非過大主張を同時に満たす実装は成立する。