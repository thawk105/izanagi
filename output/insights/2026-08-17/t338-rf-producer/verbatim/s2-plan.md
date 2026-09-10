## 実装プラン

### S1: RF attempt registry

新規ファイルは `orchestrator/qualification/rf_attempt_registry.py` とする。T-126 台帳を複製せず、汎用の永続化部品だけを再利用する。

- `L1-L55`: event、attempt、snapshot の閉じた dataclass。
  - `RfAttemptRegistrySnapshot(series_id, parent_series_id, terminal_attempts, last_event_sha256)`
  - event type は `series_open`、`attempt_intent`、`qsub_observed`、`attempt_terminal`、`series_terminal` の固定集合。
- `L56-L150`: `replay_rf_attempt_registry(events, *, series_id, parent_series_id) -> RfAttemptRegistrySnapshot`
  - index、前イベント hash、event hash、series 一致を全件検証。
  - attempt ID の重複、未登録 attempt への観測、二重 qsub、二重 terminal、循環・未来参照を拒否。
  - replacement は同一 slot の `pre_performance_infra_failure` だけを許す。
- `L151-L330`: `RfAttemptRegistry`
  - `claim_attempt(..., cluster_slot_or_null, parent_attempt_id, replaces_attempt_id, intent_ref, nonce) -> str`
  - `record_qsub_result(..., attempt_id, allocation_id, submitted_at_monotonic_ns, qsub_result) -> None`
  - `close_attempt(..., attempt_id, reason_code, performance_started_marker, environment_observations, failure_evidence) -> None`
  - `seal_stage() -> RfAttemptRegistrySnapshot`
- `L331-L390`: `require_receipt_bijection(snapshot, attempts) -> None`
  - terminal registry と receipt `attempts[]` の ID 集合を完全一致させ、欠落・余分・値の差を拒否。
- 永続化は `orchestrator/qualification/atomic_publish.py:24-123` の create-only atomic publish を利用する。
- canonical JSON の既存接続点は `orchestrator/qualification/contract.py:111-121` だが、同ファイルは編集しない。
- T-126 専用 capability は `orchestrator/qualification/artifacts.py:231-247` に束縛されているため流用しない。
- 台帳自身は qsub を呼ばず、投入 gate、投入権限、適格性判定を一切持たない。

新規テストは `orchestrator/tests/test_t338_rf_attempt_registry.py`。

- `L1-L100`: 正常な intent → qsub → terminal → seal。
- `L101-L240`: gap、hash 改ざん、重複 ID、未登録 qsub、未 terminal seal、循環 link。
- `L241-L330`: completed/anomaly attempt の replacement、異なる slot の replacement、receipt との非全単射を拒否。
- 既存テストは変更しない。

### S2: 受領証 producer

現 scope では永続 writer まで実装しない。新規 `orchestrator/qualification/rf_receipt.py` は、純粋な組み立てと pinned schema 検査に限定する。

- `L1-L55`: `load_pinned_rf_receipt_validator(repository_root: Path) -> Draft7Validator`
  - `orchestrator/preregistration/approval_payload.py:166-171` が読む D282 payload から receipt schema の BlobRef を取得。
  - path、size、sha256 を検証後、Draft-07 validator を構築。
- `L56-L145`: `prepare_rf_receipt_bytes(fields_without_attempts, *, registry, repository_root) -> bytes`
  - caller が `attempts` を渡した場合は拒否。
  - S1 snapshot の terminal attempts を唯一の入力として注入。
  - `require_receipt_bijection`、pinned schema 検査、canonical serialization の順で処理。
  - 不明 field を削除・無視せず、そのまま closed schema に拒否させる。
- file publish、qsub 呼び出し、submission gate、受理状態、適格性、validator identity/result は設けない。
- `orchestrator/preregistration/__init__.py:1-5` も変更せず、公開 API に追加しない。

永続 publisher は次の署名を将来用の接続契約として設計文書に残すが、本 wave では実装しない。

`publish_rf_receipt(destination: Path, fields_without_attempts, *, registry: RfAttemptRegistrySnapshot, binding: PreregBinding) -> PublishedReceipt`

理由は `output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:719-726` が persistent writer に keyword-only `PreregBinding` と preregistration snapshot、measurement head の照合を要求する一方、現状は `PreregBinding` と resolver が未実装だからである。binding 無しの writer は作らない。

### S3: 否定検査

新規 `orchestrator/tests/test_t338_rf_receipt.py`。

- `L1-L70`: D282 の path、size、sha256 を `orchestrator/tests/test_t139_approval_payload.py:41-45,106-125` と同じ pin から確認。
- `L71-L150`: exact 18 root fields、3 arm、12 attempt fieldsを持つ schema-shape fixture。
- `L151-L250`: root および attempt 内の以下を一件ずつ追加し、closed schema rejection を確認。
  - 適格性 field
  - pairing 成否
  - 受理状態
  - validator identity
  - validator result
- `L251-L320`: unknown field を silently strip する変異、caller-supplied attempts、registry 欠落・余分 attempt を拒否。
- `L321-L380`: `declared_use_class="dry"` でも qsub/marker 制約が免除されないことを確認。
- fixture は schema 形状検査専用と明記し、「受領証」「conformance vector」「pilot evidence」と呼ばない。

依存順序は DW-G01 probe → S1 registry → S2 純粋組み立て → S3 否定検査。probe が赤なら stage 4 に戻し、S2 永続化へ進まない。

## 設計択一の答え

### (P1) 新規 RF module を作り、永続化 primitive だけ再利用する

`attempt_ledger.py` の直接再利用も全面複製も採らない。

根拠は次の通り。

- `orchestrator/qualification/attempt_ledger.py:192-207` は schema と lineage を T-126 固有値に固定している。
- `orchestrator/qualification/attempt_ledger.py:169-173,211-296` は「initial 一回と retry 最大一回」の二者 FSM である。
- `orchestrator/qualification/attempt_ledger.py:121-152` の terminal outcome は T-126 qualification 判定を表す。
- state は `orchestrator/qualification/attempt_ledger.py:39-53` にあり、RF receipt が必要とする slot、raw qsub result、performance marker、parent/replacement lineage を保持しない。
- D162 は `docs/decisions.md:8042-8044` で T-126 二者 artifact の RF 三 arm への再解釈を禁止している。
- 一方、D229 は `docs/decisions.md:10760-10765` でコード再利用自体は許している。

RF の三 arm は各 attempt の三件化を意味しない。一本の performance allocation/schedule が `stock`、`mode1`、`modeX` を含む。したがって incompatibility の本質は arm 数ではなく、T-126 固有 FSM、判定 outcome、欠けている receipt lineage である。

### (P2) schema-valid な形は作れるが、投入なしの真実な一 attempt 受領証は作れない

構文上は `attempts: []` が許される。`receipt-schema-v1.json:1297-1300` には `minItems` がないためである。ただし、これは D282 の terminal receipt semantics を満たした意味にはならない。

attempt を一件入れる場合、`receipt-schema-v1.json:1092-1139` により最低限、次の12 fieldが必要である。

- `attempt_id`
- `cluster_slot_or_null`
- `reason_code`
- `replaces_attempt_id`
- `parent_attempt_id`
- `allocation_id`
- `submitted_at_monotonic_ns`
- `intent_ref`
- `qsub_result`
- `performance_started_marker`
- `environment_observations`
- `failure_evidence`

例えば `cluster_slot_or_null: null`、`reason_code: pre_performance_infra_failure`、`performance_started_marker: null` は構文上可能だが、`qsub_result` は `receipt-schema-v1.json:1004-1011` に従う実際の qsub 結果でなければならない。`declared_use_class="dry"` による免除条件も存在しない。qsub を呼ばずに値を合成すれば raw fact ではなくなる。

さらに `record-items-v2.md:573-585` は semantic validator に verification allocation 一件を要求する。したがって、`pilot_submission=forbidden` のまま作れるのは schema-shape fixture と純粋 assembler までである。S2 は persistent producer から、pinned schema に対する非永続の組み立て・拒否検査へ縮小すべきである。

### (P3) DW-G01 probe

使い捨て probe は repo 外の `/home/SFC/tanab/.claude/jobs/0250d6a0/tmp/wave-t338/s5-p2-probe.py`、100行以内とする。

入力:

- repo root
- candidate JSON
- durable intent、qsub raw、allocation evidence の path 一覧を持つ facts JSON
- S1 registry snapshot
- `submission_count`

出力は stdout の一個の JSON object とする。

- `schema_pin_valid`
- `schema_valid`
- `pointer_valid`
- `registry_bijection`
- `binding_valid`
- `submission_count`
- `semantic_minimum`
- `go`

probe は D282 pin の hash、Draft-07 validation、全 fileRecord の path/size/hash、registry と attempts の完全一致、PreregBinding、verification allocation 一件を確認する。probe 自身は qsub を呼ばない。

本実装へ進める緑条件は、全 boolean が true、`submission_count == 0`、かつ架空の qsub result が一件もないこと。単なる `schema_valid=true` は緑ではない。現状は PreregBinding と実測 allocation がないため赤になる見込みだが、probe は未実走であり結果を緑とは扱わない。

## 変異事前登録の候補

D229 決定 (8) の三変異を必須候補にする。

- failed submission を registry と receipt の双方から消す。
  - durable intent または qsub event が残る変異は S1 seal/bijection が kill する。
  - launch 側から intent ごと消す変異は、将来の PBS driver 接続なしには kill できない。
- 新しい `parent_series_id` を自己宣言して累積 alpha をリセットする。
  - receipt と registry の片側改ざんは S1 が kill する。
  - lineage 全体を整合させた改ざんは `record-items-v2.md:652-667` の full-history validator が必要。
- correctness anomaly を completed/clean と宣言する。
  - schema だけでは kill できない。raw output を再計算する独立 semantic validator が必要。

追加の必須候補:

- D282 pin でなく working-tree schema を読む。
- closed-schema error を key 削除で回避する。
- caller-supplied `attempts` で registry を上書きする。
- event index/hash chain の検証を外す。
- dangling、循環、未来 parent/replacement link を許す。
- completed、anomaly、別 slot の attempt を replacement 可能にする。
- `dry` を qsub field の免除として扱う。
- qsub result や performance marker を producer が合成する。
- 将来 writer が PreregBinding 無し、または measurement head 不一致で publish する。

各変異は実装後に単一理由で kill できることと mask の有無を確認してから登録する。

## risk と未解決

- 親 scope は approval resolver、PreregBinding、semantic validator を外しているが、`record-items-v2.md:719-726` は persistent writer にそれらとの結合を要求する。完全な S2 は現 scope と両立しない。
- schema は空の `attempts` や `allocations` を構文上許す。schema 適合を D282 semantic 適合と報告してはならない。
- S1 は qsub driver 非接続なので、台帳外 submission が存在しないことまでは証明できない。
- hash chain は中間改ざんと gap を検出するが、外部に固定された tip がなければ末尾切断を単独では証明できない。
- 累積 alpha lineage と anomaly 再判定は独立 validator の責務であり、S1-S3 の closed-schema test だけでは代替できない。
- approval manifest に pin された正式 conformance vector がないため、テスト fixture を適合証拠として扱えない。
- schema、`contract.py`、`s8b_floor_*`、既存テストは非接触とする。
- 静的調査のみで、pytest や probe は実走していない。緑の検査結果はない。

## 総括

S1 は T-126 台帳の複製ではなく、RF 固有の新規 registry として実装し、atomic create-only 部品だけを再利用する。  
S2 は現 scope では pinned schema の純粋 assembler までに縮小し、永続 writer は PreregBinding 導入後へ送る。  
投入なしでも空 attempts の schema-shape fixture は作れるが、実 attempt 一件を持つ真実な terminal receipt は作れない。  
DW-G01 probe は schema 合格だけでなく、raw facts、registry 全単射、binding、semantic minimum を緑条件にする。  
D229 の三変異のうち後二件の完全 kill には、scope 外の full-history semantic validator が必要である。