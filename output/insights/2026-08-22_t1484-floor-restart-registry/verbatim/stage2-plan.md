# DW-S02 段2 plan（read-only）

## 1. brief の独立再確認

| brief の主張 | 一次資料での確認 | 判定 |
|---|---|---|
| §3.6 は crash 点1〜6で復帰可否が分かれる | `docs/phase3-8b-restart-runbook.md:283-313`。点1のみ fresh 再投入可、点2〜4は公開不可/再抽選バイアス、点5〜6は拒否・完了不能。`315-325` は v1 freeze pin と v2 生成器の依存を記載 | 正しい。ただし現状に実行可能な救出コマンドはない |
| R-5 は D496 と旧§9項8の優先順位を未決着とする | `docs/phase3-8b-restart-runbook.md:422-438`。現行本文は三択 `(a)(b)(c)` を残している | 旧本文として正しいが、D510/§10.5による更新が必要 |
| D496 決定3は落ちた構成を測り直し、終端を認めない | `docs/decisions.md:20618-20624`。R-5(c)と観測ゼロ時の鍵引き直しは `20642-20647` で却下 | 正しい |
| D510 決定4は5要件を定める | `docs/decisions.md:21243-21249`。全slot事前割当、追記専用、落ちた構成・同一反復だけ、exact理由、出力前分類、create-only受領証、単一rootを要求 | 正しい |
| §10.5 が同論点を既に上書きする | `docs/phase3-8b-descriptor-design.md:424-437` は旧§9を履歴として残し§10を優先、`518-543` はD496/D510型の事前割当registryを規定 | 正しい。R-5は§10.5を参照する形へ改めるべき |
| §10.6 は追随実装まで測定を認可しない | `docs/phase3-8b-descriptor-design.md:545-555`、`docs/decisions.md:21257-21260` | 正しい。8b追随実装も同じepoch gateを明記すべき |
| D649が8c側の実装所在を確定した | `docs/decisions.md:25916-25927`。`trial_registry.py` は8c attempt registryの実装済み箇所 | 正しい。ただし8bへの再利用可否を裁定したものではない。重複judge等の却下も `25954-25960` のT-1472 scopeに限られる |

## 2. registry・admission・freeze・oracle の照合

### `trial_registry.py` は8cドメイン固定

`AttemptSlotCapability` は `trial_id`、`arm`、`holdout`、`campaign_id`、schedule hash、8c prereg commitを束縛する構造であり、docstring自身がOSレベルの「出力を読む前」を証明しないと明記する。

- `orchestrator/campaign/trial_registry.py:371-404`
- 8c固定のschema/path/語彙は `:51-77`
- retry理由は `preempted`、`wall-timeout`、`node-failure`、`launcher-failure` の4種に固定される `:101-113`
- slot layout は `trial_id`、`arm`、`holdout`、`campaign_id`、連番を必須とする `:1869-1925`
- registry pathは `output/s8c-preregistration/attempt-registry.jsonl` 以外を拒否する `:2616-2630`
- genesisのschema/root/retry setも8c固定 `:2672-2726`

実際のAPIは次のとおり。

```python
create_attempt_registry_genesis(
    *, repository_root, manifest_path, manifest_sha256, freeze_id,
    slots, retryable_failure_reasons=..., registry_path=...
) -> Path
# :2672-2683

reserve_attempt_slot(
    *, repository_root, freeze_id, slot_id,
    prereg_content_commit, prereg_effective_commit,
    run_start_receipt_sha256, process_identity, started_at,
    registry_path=...
) -> AttemptSlotCapability
# :2984-2995

classify_attempt(
    capability, *, pre_observation_failure_reason,
    authority_id, authority_policy_sha256,
    external_evidence_sha256, classified_at
) -> dict[str, Any]
# :3134-3142

begin_attempt_observation(capability) -> dict[str, Any]
# :3247-3253

record_attempt_terminal(
    capability, *, terminal_status, raw_output_sha256,
    report_sha256, observation_sha256, primary_value,
    finished_at, failure_reason=None
) -> None
# :3314-3324

assert_attempt_registry_acceptance(
    *, repository_root, manifest_path, manifest,
    effective_binding, effective_commit,
    report_paths=(), registry_path=...
) -> tuple[dict[str, Any], ...]
# :3432-3441
```

genesisは「全slotを観測前に作る」設計であり、`reserve_attempt_slot` は同一構成の直後のretry slotだけを許す `:2684-2690,2996-3004`。ただし分類・観測開始・terminalの各APIは、内部event chainの整合性を検査するだけでOSレベルのread-first事実は保証しない `:3143-3150,3248-3253,3325-3331`。

`assert_attempt_registry_acceptance` も8cの `TrialManifest`、`manifest.trials`、8c effective bindingを前提にする `:3432-3494`。したがってliteralな8b流用はできない。

### 8b admissionの既存語彙と排他

8bのadmission keyは次の6要素で固定される。

- `orchestrator/campaign/s8b_holdout_admission.py:669-687`
- `freeze_sha256`
- `freeze_holdout_key`
- `configuration_id`
- `ccbench_pin`
- `env_tag`
- `observation_role`

`protocol_sha256` はkeyではなく証拠欄に限定される `:673`。claimは `root/claims/<digest>.claim` に置かれ、`O_CREAT|O_EXCL|O_NOFOLLOW` で排他的に作成される `:690-695,800-811`。

8b自身も予定attempt IDを全件生成している。

- `:1133-1141` — planned slotとretry slotを事前生成
- `:1264-1315` — 6要素key、claim、attempt IDを作成
- `:1333-1425` — fresh/resumeの同一性・create-only・観測開始後のbackfill拒否
- `:1467-1544` — ledgerの重複・欠落・同一run identityを検査
- `:3796-3841` — frozen attempt ticketを観測直前にcreate-only消費

共有物理rootはGit common dir配下の `izanagi/s8b-holdout-admission-v1` である `:76-79,427-444,486-500`。新registryはこの共有rootとの整合を保つ必要がある。

### 8bの失敗分類は現状では出力後

ここがbriefの重要な見落としである。

- `s8b_floor_campaign.py:4734-4738` で `session-start` を記録
- `:4773-4780` で `measure_fn` を実行
- `:4809-4822` でthroughputから理由を導出
- `:4824-4840` で `performance_anomaly`/partial等を含む最終理由を決定

`consume_attempt_ticket` が測定直前に実行される `s8b_floor_campaign.py:4499-4528` ことは、D510の「失敗分類を出力前に確定」する受領証とは別である。

statsの閉じた理由集合も `s8b_floor_stats.py:52-58` の

- `competing_process`
- `launch_failure`
- `nonfinite_or_partial_output`
- `performance_anomaly`

であり、後二者は性能出力から導出され得る。8cのretry理由 `trial_registry.py:104-106` をそのまま8bへ移すこともできない。

### novelty search

freeze生成時に検索合格を要求する `s8b_holdout_freeze.py:808-840`。`verify_document` は記録済みhitの空集合、snapshot hash、現在の再検索を再検証し、観測後にconjunction hitが生じれば意図的にfail-closedする `:985-1001,1075-1109`。

したがって、R-5のregistry復帰は「新しい未知freezeを作る」設計ではなく、観測前に作成済みの元freeze receipt/rootを使う継続として設計する必要がある。R-5(b)の新freezeは別のtrust-root設計である。

### oracleはfloorを使わない

`judge_oracle` の引数にfloorはなく、docstringもfloorを入力・tie-breakに使わないと明記する。

- `orchestrator/campaign/s8b_oracle_judge.py:452-464`
- 最大値・tie判定は `:682-705`
- CLI呼出しにもfloor引数はない `:740-765`

よってD496の「判定関数は既に対測定」は裏付けられ、R-5でoracle judgeを改修する必要はない。

## 3. P1の推奨

推奨は「`trial_registry.py`をliteralに流用しない。ただし機構パターンは参照し、8b専用registry/adapterを作る」である。

理由は次のとおり。

- schema version、保存path、ARMS/HOLDOUTS、holdout bindingが8c固定 `trial_registry.py:51-77`
- path自体が8c固定 `:2616-2630`
- slot schemaが8cの`trial_id/arm/holdout/campaign_id`固定 `:111-114,1869-1925`
- acceptanceが8c `TrialManifest`固定 `:3432-3494`
- retry理由語彙も8bと異なる `trial_registry.py:104-106`、`s8b_floor_stats.py:53-58`
- 現在8bからのimport結合はない `handoff.md:36-43`

汎用化する場合は、schema、root/path、key fields、retry vocabulary、slot parser、manifest型、acceptance consumer、receipt pathを全てパラメータ化する必要があり、既存8c consumer（`p3_autonomous_workload_trial.py:1261-1332,4398-4414,4679-4685`）とテストを壊し得る。

最低限の8b専用要素は次のとおり。

1. schema候補: `s8b-floor-attempt-registry/v1`。既存の` s8b-holdout-attempt-consumption/v1` `s8b_holdout_admission.py:90-96`とは別schemaにする。
2. admission key: 既存6要素をそのまま使う。`generation`を追加する場合も、free saltではなく初回genesisで事前登録する。
3. path候補: `shared_admission_root(repo) / "attempt-registries" / <freeze_sha256> / "registry.jsonl"`。初期bytes hashとcanonical pathを事前登録bindingへ保存する。
4. slot: `cell_id`、holdout、configuration、replicate/sequence、attempt ordinal、schedule hash、run-start receipt、process identity。
5. event: pre-observation classification、observation-start、terminal status、raw/report/observation hash、primary value。
6. retry理由: 8b専用の外部証拠由来のclosed setを新たに凍結する。statsの性能由来理由を無条件にretry理由へ入れない。
7. 既存claim/ticketとの結合: claim digest、registry slot、attempt ticket、journal `session-start`を相互参照させる。claim ledgerをregistryの代用品として扱わない。

## 4. P2と絶対規律2の確認

R-5(a)と§10.5は同一設計ではない。

- R-5(a)は復帰用generationでadmission keyを変え、観測ゼロrunだけを別runとして受理する identity workaround `docs/phase3-8b-restart-runbook.md:372-377`
- §10.5は元のfreeze identityを維持したまま、観測前に全slotを閉じた集合として作り、落ちた構成・同一反復の次slotだけを消費する `docs/phase3-8b-descriptor-design.md:518-543`
- D496は観測ゼロの鍵引き直しを不要とした `docs/decisions.md:20642-20646`

したがってR-5(a)は§10.5の同義語ではなく、§10.5より弱い別設計である。R-5本文では(a)を「歴史的なidentity workaround、§10.5の代替ではない」と明記し、現行推奨から外す。

D510の5要件に対する現在地は次のとおり。

| 要件 | 現状 | 必要な設計条件 |
|---|---|---|
| 事前割当 | 8b admissionはattempt IDを事前生成する `s8b_holdout_admission.py:1133-1141` | registry genesisで全slotを観測前に固定し、後出しslotを拒否 |
| 追記専用 | claim/ticketはexclusive create `:800-811,3819-3826` | registry eventもappend-only、observed slotの再利用不可 |
| exact失敗理由 | 8b statsにはclosed setがある `s8b_floor_stats.py:53-58` | 出力由来のpartial/performanceをretry分類へ直接使わず、外部証拠由来setを別途凍結 |
| 出力前分類 | 現行8bは理由の多くを`measure_fn`後に決定 `s8b_floor_campaign.py:4773-4840` | trusted launcherが性能出力を読む前に分類・create-only receiptを完了させる |
| create-only受領証・単一root | 8b claim/ticketはあるが、8b attempt registryはない | freezeごとに1つのregistry root、canonical path+initial hash、第二root拒否、全attempt報告 |

さらに、既存`trial_registry.py`自身がOSレベルのread-firstを保証しないと明記している `:376-379,3145-3150,3248-3253`。T-1337のレビューでもこの問題はscope外として残っている `docs/archive/worklog-phase3-0820-738.md:7-13,27-31`。したがって、現段階で「D510の5要件を完全に満たした」とは書かず、trusted launcherの信頼前提またはT-1435型のread API capability化をepoch gateの残件として明示する。

## 5. 他の一次資料・競合確認

- T-1179はcrash時のfreeze/admission再生成を必須とする `docs/archive/worklog-phase3-0816-595-596.md:990-995`
- T-1337はD496を維持するならfreeze-wide registryが必要とした `docs/archive/worklog-phase3-0818-643.md:592-596`
- T-1337/T-1353の実装済み範囲はregistryと**8c**起動・受入結線まで `docs/archive/worklog-phase3-0818-650.md:546-552,579-582`
- `docs/phase3.md:54-59` の「§9項8=crash再走なし」は旧履歴であり、descriptor §10の優先規則 `docs/phase3-8b-descriptor-design.md:427-433` と、更新済みT-901 `docs/phase3.md:773-780` を優先する
- admission registryを一度見送ったT-966も、再走需要発生時に再訪する条件だった `docs/phase3.md:1040`
- 競合候補は`docs/archive/worklog-phase3-0822-815.md:19-28` に記録された`trial_registry.py`/`p3_autonomous_workload_trial.py`変更波。現時点のworktree一覧では8b対象ファイルの未コミット差分は確認できなかったが、実装着手前に再度worktree/statusを確認する

## 6. R-5本文の旧→新案

### `docs/phase3-8b-restart-runbook.md:352-364`

旧状態表にはR-5行がなく、本文は「修理・設計択一は裁定へ返す」としている。

新案:

> R-5行を追加し、「D496決定3/D510決定4/§10.5に整合するfreeze-wide事前割当attempt registryを推奨。8b専用adapter、admission marker結線、trusted-launcher境界、epoch gateは未実装」とする。  
> 本waveはdocs-onlyであり、現HEADに実行可能な復帰コマンドが存在するとは記載しない。

### `docs/phase3-8b-restart-runbook.md:372-381`

三択は削除せず、歴史的検討として残す。

- `(a)` admission key salt: §10.5とは別物であり、現行推奨から除外
- `(b)` 新未知freeze: trust rootを変更する別設計。将来候補だが本推奨ではない
- `(c)` terminal化: D496 `docs/decisions.md:20623-20624,20642-20644` とD510 `:21243-21249` に反するため不採用

その直後に、現行推奨を「元freezeのidentityを保持し、観測前に登録した次slotだけをregistry経由で消費する」と記す。

### `docs/phase3-8b-restart-runbook.md:422-438`

旧文の「D496と§9項8の優先順位は未決着」を、次の骨子へ置き換える。

> 2026-08-18のD510およびdescriptor §10.5により、旧§9項8の再走全拒否は履歴として保持しつつ、現行設計はfreeze-wide事前割当attempt registryへ読み替える。  
> ただし現HEADはまだ実装・発効前であり、既存のfreeze-byte marker、claim排他、novelty searchを無条件に緩めない。復帰は、観測前に固定された元freeze receipt・単一registry root・次slot・外部証拠由来の分類が全て揃う場合だけ許す。  
> 観測後に新freezeを生成してnovelty searchを通すことはR-5(b)であり、本設計とは別である。oracle judgeはfloorを消費しないためR-5の変更対象に含めない。  
> trusted launcherのOSレベルread-first証明と8b consumerのepoch gateが未解決の間は、正式測定を認可せず、既存runをlegacy/exploratoryとして扱う。

## 総括

- briefのD496/D510/§10.5優先判断は正しいが、8b現行実装の失敗分類が測定後である点と、OSレベルread-first証明の欠如を補う必要がある。  
- R-5(a)のsaltは§10.5と別設計であり、推奨は元freezeを維持する8b専用事前割当registry。  
- `trial_registry.py`は8c固定のためliteral流用せず、既存8b admission root・claim・noveltyをregistryと束縛する。  
- 実装・trusted-launcher境界・epoch gateが閉じるまで、R-5更新は方針文書に留め、測定認可は行わない。