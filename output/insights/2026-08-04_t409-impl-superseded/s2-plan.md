# [T-409] 段 2 実装プラン

必読入力はすべて読めた。以下は read-only の起草であり、ファイル変更・pytest 実走は行っていない。`axis_trigger_gating.py`、`s8a_trigger_sweep.py`、`s1_known_axes_freeze.py` は全計画で bytes 不変とする。

## 1. recognizer 新規モジュール

新設: `orchestrator/campaign/trigger_gate_language.py:1`

公開面は次に固定する。

```python
TRIGGER_GATE_LANGUAGE = "trigger-gate-language/v1"

class GateLanguageRejectCode(str, Enum):
    INVALID_TYPE = "invalid-type"
    RESOURCE_LIMIT = "resource-limit"
    INVALID_CHARACTER = "invalid-character"
    INVALID_TOKEN = "invalid-token"
    INVALID_GRAMMAR = "invalid-grammar"
    UNSET_NOT_TRUE = "unset-not-true"

@dataclass(frozen=True)
class GateLanguageResult:
    passed: bool
    reason_code: GateLanguageRejectCode | None

def check_trigger_gate_implementation(
    implementation: str,
) -> GateLanguageResult:
    ...
```

配置案:

- `:1-45`: 上記定数、enum、dataclass、4096 byte／512 token／深度64、8 member の閉集合。
- `:46-120`: 逐次 scanner。space/tab のみ捨て、word は maximal-munch、punctuator は `== != && || ::` を最長一致する。単独 `! & | :` は `INVALID_TOKEN`。
- `:121-230`: 凍結 BNF どおりの再帰下降 parser。`or → and → primary` の順で AST を構築し、Python `eval` は使わない。
- `:231-270`: private `_evaluate(ast, member)`。公開 checker は `kUnset` だけを評価し、偽なら `UNSET_NOT_TRUE`。
- `:271-320`: 公開入口。判定順を厳密に `type → raw size → character → token count → parse/depth → semantic` とする。

結果・例外・ログへ入力本文、未知 word、token 値、offset、行・列を保持しない。内部例外も種類だけを閉じた reason code へ落とす。深度65は parse/depth 段なので `INVALID_GRAMMAR`、byte/token 超過だけを `RESOURCE_LIMIT` とする。

## 2. SourceEvidence と封印 receipt

### SourceEvidence

`orchestrator/campaign/source_digest.py:85-182` を後方互換な二形態にする。

- 非 trigger source は従来どおり `source-evidence/v1` と従来の exact keys を保つ。
- trigger marker または `BACKOFF_TRIGGER_GATING` flag が存在する source は `source-evidence/v2` とし、次を追加する。

```python
trigger_gate_language: str
trigger_gate_implementation_sha256: str
```

`resolve_evidence():836-876` では `cc/silo/transaction.cc` の実 bytes を `parse_template_file()` で読み、hole 行をそのまま復元して checker を実行する。flag が trigger を要求するのに marker/hole が欠落・破損していれば非 trigger 扱いにせず reject する。合格時だけ raw ASCII implementation の SHA-256 と文法版を v2 evidence に入れる。

この v1/v2 分岐により、trigger 以外の既存 admission/cache identity は変えない。

### TriggerGateReceipt

`orchestrator/campaign/build_admission.py:29-34,181-250` に追加する。

```python
TRIGGER_GATE_RECEIPT_SCHEMA = "trigger-gate-receipt/v1"

@dataclass(frozen=True, slots=True, init=False)
class TriggerGateReceipt:
    _body_json: str
    _issued: bool
    ...

def issue_trigger_gate_receipt(
    source: SourceEvidence,
) -> TriggerGateReceipt:
    ...

def require_trigger_gate_receipt(
    value: object,
    *,
    expected_source: SourceEvidence,
) -> TriggerGateReceipt:
    ...

def validate_trigger_gate_receipt(
    value: object,
    *,
    expected_source: SourceEvidence | None = None,
) -> Mapping[str, object]:
    ...
```

receipt body の exact fields:

```json
{
  "schema": "trigger-gate-receipt/v1",
  "issued": true,
  "trigger_gate_language": "trigger-gate-language/v1",
  "implementation_sha256": "<64hex>",
  "source": {"...": "SourceEvidence v2 body"},
  "receipt_sha256": "<canonical body SHA-256>"
}
```

発行関数は `source_root` の実 hole をもう一度読み、checker、implementation hash、SourceEvidence equality を再検査してから `_SEAL` と `_issued=True` を与える。永続 body の `"issued": true` だけでは runtime 発行を代替できず、build 境界は exact `TriggerGateReceipt` を要求する。

`derive_build_admission():424-483` は `trigger_gate_receipt=` を追加する。

- SourceEvidence v2 なら sealed receipt 必須。
- v1 なら receipt 提示を拒否。
- 非 trigger は従来 `build-admission/v1` body のまま。
- trigger は `build-admission/v2` とし、従来 fields に `"trigger_gate_receipt"` を加える。

これにより非 trigger admission SHA は変えず、trigger だけを新 policy に移す。

### 文法版の格納 field

| 境界 | 実在 preimage/body に追加する field |
|---|---|
| SourceEvidence v2 | `trigger_gate_language`, `trigger_gate_implementation_sha256` |
| TriggerGateReceipt | `trigger_gate_language` |
| legacy `cache_key():130-148` raw preimage | `trigger_gate_language=...`, `trigger_gate_receipt_sha256=...` |
| `_v2_identity():246-266` | `trigger_gate_language`, `trigger_gate_receipt_sha256` |
| WAL `build_start` payload | `trigger_gate_language`, `trigger_gate_receipt`, `trigger_gate_receipt_sha256` |
| campaign `search_config` | `trigger_gate_language` |
| S8B trigger binding | `trigger_gate_language`, `trigger_gate_implementation_sha256` |

receipt、cache、WAL には implementation 本文を格納しない。

## 3. materializer/build 配線

| 呼出面 | 検査する値 | 差し込み位置 |
|---|---|---|
| `p3_s4_loop_trigger_gating.py:358-402` | `CoderProposalTriggerGating.implementation` | `_quarantine_and_audit()` 冒頭。新 checker →旧 blacklist→`L.quarantine()`→auditor。reject は source write 前 |
| `p3_s4_loop.py:184-221` | `quarantine(..., implementation=...)` | marker/source が trigger の組なら、ファイル読出し・`render_hole`・write より前に checker。no-touch の S8A caller もここで被覆 |
| `s1_verify_extime_calibration.py:329-357` | `target["gate_predicate"]` | `with applied(...)` より前に checker。evidence 後に receipt を発行し `derive_build_admission()` へ渡す |
| `s1_direct_comparison.py:485-561` | `variant["gate_predicate"]` | `patchharness.applied()` より前。旧 `check_syntax_contract()` も残す。`PreparedCell` には解決済み SourceEvidence を保持 |
| `s8a_trigger_sweep.py:419-459` | 既存の局所 `impl` | 本体 bytes は変更せず、上記 generic `quarantine()` と downstream source check で被覆 |
| `patchharness.py:234-251` | proposal field ではなく context 内の実 source hole | `applied()` の enter 時点では body 内でさらに変更可能なので receipt を発行しない。docstring を「body 内で v2 evidence/receipt を確定しない build は拒否」に更新 |
| `pipeline.py:572-626` | `ccbench_dir/cc/silo/transaction.cc` の実 hole | `resolve_evidence()` 後に receipt 発行、admission へ束縛。proposal 名を推測しない |
| `buildcache.py:562-686,789-923` | admission 内 receipt と current SourceEvidence | cache lookup/configure より前に要求し、cache hit と build 後にも source を再読して receipt と照合 |
| `s8b_floor_campaign.py:973-1050` | materialize 済み `PreparedCell.source_evidence` | review receipt と build admission の前に trigger receipt 発行 |

`patchharness` 単体には final bytes の確定点がないため、そこで patch text を gate 入力とみなさない。任意 patch が直接 hole を変えても、`source_digest.resolve_evidence()` と `buildcache` が実 source bytes から receipt を作れなければ build へ進めない。

`pipeline.evaluate():554-614` の pre-build reject は `reason="trigger-gate-reject"` と閉 enum 値だけを WAL に出し、例外要約へ source 本文を含めない。

## 4. cache / WAL / S8B の再検査

### Cache

`buildcache.py:320-433,645-686,817-903` に明示的な旧 artifact migration を置く。

1. 新 trigger key が miss したときだけ、current v2 SourceEvidence/admission から旧 v1 projection と旧 key/preimage を決定論的に再構成する。
2. 旧 sidecar/completion の admission、commit、genome、`source_bytes_sha256`、tracked diff、binary SHA を旧 schema で厳密検証する。
3. 旧 `source_root` が残るならそこ、なければ同じ materialization recipe で再構成した source bytesを読み、旧 evidence digest と一致させた上で checker を実行する。
4. 合格時だけ、新 key の staging へ同じ binary bytes と新 receipt/preimage を atomic publishする。旧 entry は変更しない。
5. 不合格、source bytes 不在、digest 不一致は cache reuse を rejectし、新 entryを作らない。「receiptありとして扱う」fallback は置かない。

非 trigger key は完全不変にする。

### WAL / campaign identity

`ident.py:28-44,125-156` に `search_config["trigger_gate_language"]` の binding helper を追加する。

- `search_config["axis"] == "silo-backoff-trigger-gating"` なら `bind_admission_policy()` が自動挿入するため、bytes 不変の S8A driver も新 campaign ID になる。
- S1 mixed campaign は `s1_direct_comparison.config_for():206-230` で明示挿入する。
- 値の既存不一致は上書きせず拒否する。
- migration 専用 helper はこの key を落とした旧 config/layout を導出するが、通常 resume には使わせない。

`pipeline.py:620-626` の新 `build_start` は receipt body、版、SHA を持つ。`build_done`、attempt-bound `abort`、`commit:962-975` は `trigger_gate_receipt_sha256` を伝播する。

`model.py:112-123` と `wal.py:584-747` は attempt state に trigger receipt SHA を追加し、current lock が grammar field を持つ場合は次を強制する。

- `build_start` に3 fieldが存在する。
- receipt body、receipt SHA、BuildAdmission 内 receipt が完全一致する。
- receiptless attempt は `build_done` / `commit` を持てない。
- 後続 attempt record の SHA が start と違えば reject。

旧 campaign WAL は通常 replay で混ぜず、`loop.py:152-256` と `screening_driver.py:147-195` の旧-layout migration だけで読む。旧 terminal の build admission/source evidence と再構成した実 source bytesを照合し、checker 合格時だけ新 receipt付き標準 attempt recordsとして新 WALへ再発行する。各 recordには旧 campaign/record canonical SHAを `reinspection_of` として残す。不合格・source不在は current `trigger-gate-reject` abort とし、旧 terminal skipには使わない。途中 crash は deterministic migration attempt ID で prefix を検証して再開する。

S1 の `s1-session` ledger も `s1_direct_comparison.py:626-803` で同じ扱いとし、旧成功 session を source再検査なしに `next_index` へ数えない。

### S8B resume

`PreparedCell` と binding を次のように拡張する。

- `s1_direct_comparison.py:98-103,557-561`: `source_evidence` を保持。
- `s8b_materialization.py:117-151`: trigger cell の binding preimage に `trigger_gate_language` と `trigger_gate_implementation_sha256` を加えてから `binding_sha256` を計算。
- 非 trigger binding は現行5 fieldsのまま。

`S8B` の portable receiptへ絶対 `source_root` を含む TriggerGateReceipt 本体は入れない。代わりに portable binding が版と implementation hash を保持し、cache 内の BuildAdmission が sealed receipt 本体を保持する。

` s8b_floor_campaign.py:1118-1199,3004-3078,3192-3240`:

- 新 binding は version/hash/binding SHAを厳密検証。
- 既存 manifest の trigger binding 欠落は legacy branch だけで受け、freeze entryから各 cellを再 materializeして実 source checker、旧 binding subset、binary/store SHAを照合する。
- 合格時のみその resume中に受理。不変 create-only manifestへ追記・上書きせず、次回 resumeも再検査する。
- 不合格・source再構成不能は即 reject。

`s8b_oracle_driver.py:1320-1380` も floor manifest の legacy binding を同じ source再検査後にだけ受ける。単なる missing-field許容は置かない。

## 5. role 契約と B-10 同一変更単位

`.claude/agents/coder-v4-autonomous-trigger-gating.md:82-115` は次へ狭める。

- 読める member は8件を裸名で列挙するが、数値 initializer の例示を除く。
- literal は `true` / `false` のみ。
- operator は assignment の `=`、比較 `== !=`、論理 `&& ||`、scope `::`、括弧、終端 `;` のみ。
- 単独 `!`、数値・文字・文字列 literal、呼出し、member access、再代入、comma、ternary、alternative token、コメント、改行を禁止。
- space/tab 以外の空白を禁止。
- `kUnset` 評価が必ず true。
- `SYNTAX_CONTRACT_FORBIDDEN` の5識別子節は defense-in-depth として残す。

同 `:146-148` は「allowlist recognizer → 旧 blacklist → diff quarantine → auditor → source-bound receipt/build」に更新する。

live runtime 契約も同時に更新する。

- `p3_autonomous_workload_trial.py:190-242`: `ROLE_CONTRACTS["coder"]`、`GATING_SPEC`、`DESIGNATED_SOURCE_CONTEXT`。
- 同 `:562-580,1387-1395`: preview に安全な `trigger_gate_language: {passed, reason_code}` を追加し、旧 `forbidden_identifiers` も残す。
- `docs/phase3-s8a-trigger-runbook.md:63-88`: 親が同じ文法・順序へ追随。

role lockstep の手順:

1. role source と `manifest.json:820-961` の `projection_instructions` を同じ契約へ変更。
2. role bytes SHA と、manifest role entry の canonical JSON SHAを計算。
3. `review_ledger.py:15-47` の対象 `SOURCE_FILE_SHA256` と `ROLE_MANIFEST_SHA256` を明示レビュー更新。
4. frontmatter description、I/O schema、共通 template は変更しないため `DESCRIPTION_SHA256`、`SCHEMA_SHA256`、`DEVELOPER_INSTRUCTION_TEMPLATE_SHA256` は不変。
5. `ROLE_SPEC.render_adapter()` の期待出力をレビューして `.codex/role-adapters/coder-v4-autonomous-trigger-gating.json` 全体へ適用する。`--write` は使わない。
6. adapter では `developer_instructions`、`review_ledger.source_file_sha256`、`review_ledger.role_manifest_sha256`、`semantic_digest`、`source.sha256` が変わる。
7. `tools/check_codex_agents.py:216-263` が source body exact 1回、rendered byte parity、13 role全単射、native active 0件を満たせば緑。

## 6. B-6 材料主張境界

`layer3_report.py:39-40,190-202,451-470` と `layer3_schema.json:1-58` に、新規 report の `claim_boundaries` を追加する。

trigger campaign では固定値を出す。

```json
{
  "scope": "trigger-gating",
  "classification": "finite-policy-selection",
  "headline_synthesis_evidence": false
}
```

schema は v4へ上げ、既存 v2/v3 artifact は歴史的 readerでのみ受け、再生成しない。`p3_autonomous_workload_trial.py:1183-1191` の `claim_scope` にも同じ境界を入れる。親所有の新 D fragmentには「高々有限 policy 選択であり、D50の有効自由度は3 bit、headline synthesis evidenceではない」を明記する。

## 7. must-fix 8件の閉じ方

| must-fix | closure |
|---|---|
| A2-1 | bare `!` tokenを持たず、`!=` の最長一致だけ許可 |
| A2-5 | 7境界ベクタを exact reason code付きで固定 |
| A2-8 | 上限の数え方・判定順・64/65 depthを単体テスト |
| A2-15 / B-1 | proposal、generic quarantine、calibration、patchharness後段、pipeline、buildcacheを二重防壁化 |
| B-2 | SourceEvidence v2、campaign identity、cache preimage、WAL、S8B bindingへ版を束縛し、旧実体を再検査 |
| B-4 | role/runtimeを数値なし契約へ変更し、`izanagi_gate_pass = 1;` を拒否テスト |
| B-6 | Layer3/autonomous reportと新 Dに finite-selection / non-headline 境界 |
| B-10 | role、manifest、review ledger、adapterを一変更単位にし parity checkerで閉じる |

## 8. テスト配置

### 新規 pure language test

`orchestrator/tests/test_trigger_gate_language.py:1`

- A2-5: `: :`、`= =`、`! =`、`& &`、`&&&`、`===`、`|| |`。空白がtokenを結合しないことと exact reason codeを固定。
- longest-match positive: `:: == != && ||`。
- resource order:
  - 4096 byte accept / 4097 `RESOURCE_LIMIT`
  - 512 token accept / 513 `RESOURCE_LIMIT`
  - depth64 accept / 65 `INVALID_GRAMMAR`
  - size超過＋不正文字は resource、範囲内不正文字＋token過多は character。
- semantic: `false`、非Unsetのみ、`reason != kUnset` は `UNSET_NOT_TRUE`。
- 128 subsets: `kUnset` と残り7 memberの各部分集合から式を生成し、全128式が public checkerを通ること、private AST evaluatorが8理由×128件で集合 membershipと一致すること。
- positive-controls: 全26件の分類を確認し、1/3/5/41/43/45/47/49/51行の9式だけを trigger positiveとして全通過。散文1件・sort16件は domain selectorから除外。
- reject corpus: `= 1;`、複数文、`pro_set_.pop_back()`、式内代入、loop、return、global fitness参照、コメント、LF/CR、Unicode、lone surrogate。

### B側 integration tests

- `test_p3_s4_loop_trigger_gating.py:1093-1228`: checker reject時に quarantine/write/auditor/run_campaign未到達、旧 blacklist残存、ログ非リーク。
- `test_s1_verify_extime_calibration.py:80-115`: `gate_predicate` を `applied()` 前に拒否し、合格時は receipt付き admission。
- `test_s1_direct_comparison.py:251-418,540-560`: field名、改行reject、PreparedCell evidence、旧session再検査。
- `test_s8a_trigger_sweep.py:92-104`: production moduleは無変更のまま全生成 predicateが文法合格。
- `test_build_admission.py:100-280`: constructor偽造、`issued=false`、body/SHA/source/version改変、v1非trigger互換。
- `test_buildcache_v2.py:560-970`: missing receiptのcache/build拒否、preimage fields、旧cache合格migration、不合格/bytes不在reject、非trigger key不変。
- `test_campaign.py:667-816,1630-1680`: WAL receipt topology、旧WAL再検査、migration crash-prefix、pipeline actual-source check。
- `test_s8b_materialization.py`: trigger bindingだけ版/hash追加。
- `test_s8b_floor_campaign.py:973-1229,2990-3240`: fresh binding、legacy resume pass/reject、manifest非上書き。
- `test_s8b_oracle_driver.py:1320-1380`: legacy floor bindingを未検査で受けない。
- `test_p3_autonomous_workload_trial.py:400-430`: runtime grammar、preview schema、claim boundary。
- `test_layer3_report.py`: v4 claim、triggerでheadline=false、v2/v3 historical reader。
- `test_codex_agents.py`: role source/manifest/adapter parityと数値禁止文言の埋込み。

既存 fake SourceEvidence は v1 defaultのため非trigger testへの波及を抑える。trigger fixtureだけv2 evidenceとreceiptを明示する。checked-in freezeのsha回帰テスト追加は[T-442]へ残す。

## 9. 段5の所有分割

実装子Aの素集合:

- `orchestrator/campaign/trigger_gate_language.py`
- `orchestrator/tests/test_trigger_gate_language.py`

実装子Bの素集合:

- receipt/source/cache/WAL/identity: `build_admission.py`, `source_digest.py`, `buildcache.py`, `ident.py`, `model.py`, `wal.py`
- 配線: `pipeline.py`, `loop.py`, `p3_s4_loop.py`, `p3_s4_loop_trigger_gating.py`, `patchharness.py`, `s1_verify_extime_calibration.py`, `s1_direct_comparison.py`
- S8B: `s8b_materialization.py`, `s8b_floor_campaign.py`, `s8b_oracle_driver.py`
- producer/report: `p3_autonomous_workload_trial.py`, `layer3_report.py`, `layer3_schema.json`
- role単位: role md、manifest、review ledger、adapter JSON
- 上記既存 integration test群

集合は交差しない。BはAの公開 APIへ依存するため、投入順はA→Aの純粋テスト確認→B。Aは既存ファイルを変更せず、BはAの2ファイルを修正しない。新 D・runbook・worklog fragmentは親所有とする。

## 10. 段4変異 matrix 候補

| 変異 | 検出テスト |
|---|---|
| checkerを常時pass | reject corpus |
| bare `!` を復活 | `test_bare_bang_is_invalid_token` |
| Hを跨いでpunctuator結合 | A2-5 `: :`, `= =`, `! =`, `& &` |
| longest-matchを1文字優先 | valid `:: == != && ||` |
| size/character順を逆転 | mixed-failure order matrix |
| token上限を数えない／EOFを数える | 512/513 boundary |
| depth checkを無効化 | 64/65 boundary |
| `kUnset` semantic check削除 | `false`・non-Unset-only |
| `&&`/`||` precedence破壊 | 128 truth-table＋混合式 |
| receiptをchecker失敗でも発行 | build admission reject test |
| `_issued`/exact type検査削除 | forged receipt test |
| cache preimageから版/SHAを除去 | trigger key collision test |
| old cacheを再検査なしでpromote | invalid legacy cache test |
| WAL missing receiptをterminal扱い | replay topology test |
| legacy WALをsourceなしでmigrate | migration no-source test |
| S8B legacy bindingを無条件受理 | legacy resume invalid predicate |
| role/manifest/ledgerの一つだけ更新 | `check_codex_agents.py` parity test |
| reportをheadline=trueにする | Layer3 claim-boundary test |

## 総括

- 新 recognizerは凍結BNF・順序・上限・閉 reason enumをそのまま実装する。
- proposal fieldは `implementation` と `gate_predicate` を面ごとに明示し、buildでは実sourceだけを見る。
- sealed receiptをBuildAdmissionへ内包し、cache/WAL/identityへ文法版を束縛する。
- 旧cache/WAL/S8Bはsource bytes再検査に合格した実体だけ移行し、cold invalidate／未検査overlayは作らない。
- 非triggerのSourceEvidence、admission、cache keyはv1のまま保つ。
- 旧blacklistは残し、freeze pin対象3ファイルは変更しない。
- 最大リスクは旧artifact再構成不能、WAL migrationのcrash冪等性、S8B portabilityである。
- 親は計算ノードで関連＋全テスト、role parity、docs、provenance、no-touch 3ファイルのSHA不変を検証する。