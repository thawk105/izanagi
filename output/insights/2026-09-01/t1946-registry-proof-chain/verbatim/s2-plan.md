## 前提の実測

対象は base `11b44e2d1ad4a62aa41aebc74daf8a9df9bb51e2`。必読 2 文書を読了した。pytest は実走しておらず、以下は静的検査結果である。

### P1: 前向き条件

- [実測] `orchestrator/campaign/s8b_floor_contract.py:34` は `RESULT_SCHEMA = "s8b-floor-result/v4"` の単一定数である。
- [実測] 同 `:81-87` の `_RESULT_KEYS` も単一集合で、`result_keys_for_mode()` は `:157-166` で schema を引数に取らない。
- [実測] `orchestrator/campaign/s8b_floor_stats.py:734-747` は、その単一 key 集合を検査した後、`artifact.schema == RESULT_SCHEMA` を要求する。
- [実測] `orchestrator/campaign/s8b_holdout_freeze.py:1429-1439` と `s8b_ratified_freeze.py:2333-2356,2385-2389` も同じ単一版前提である。
- [判定] `RESULT_SCHEMA` を v5 に置換するだけでは v4 は全て拒否される。親 provisional の「v4 は現行規則のまま」は、そのままでは成り立たない。
- [推奨] 版方式自体は採用する。ただし `LEGACY_RESULT_SCHEMA=v4`、`RESULT_SCHEMA=v5`、`READABLE_RESULT_SCHEMAS={v4,v5}` と schema 別 key 集合が必要である。
- [前向き境界] 新しい candidate を作る `build_v2_g1_candidate()` は `s8b_holdout_freeze.py:2047-2055` から `_validate_floor_inputs()` を通る。ここだけは `:1437` の current schema 等値検査を v5 のまま維持する。これにより新規 candidate の v4 downgrade を拒否できる。
- [後方互換境界] publish 済み ratified artifact の consumer は v4/v5 を読み分ける。schema を自己申告だけで無条件に併読するのではなく、「新規発行入口は current v5、publish 済み再検証入口は readable v4/v5」に分ける。

### P2: pin の閉包

- [実測] `attempt_registry_core.py:239-250` では各 row の hash が row 全体と previous hash を含む。`:253-259` の `previous_event_sha256()` は末尾 head を返すが、chain row が無い場合は zero SHA を返す。
- [実測] genesis は `:1497-1500` で `event_index=0`、previous zero を含む chained row になる。`:483-503` は空 slot 集合を拒否し、`:986-1004` は空 rows や非 genesis 先頭を拒否する。
- [実測] adapter の通常 reader は registry 不在を `s8b_attempt_registry.py:509-516,1101-1106` で拒否する。一方、admission 内の既存 raw reader は `s8b_holdout_admission.py:4969-4975` で不在を `b"", ()` に射影する。
- [判定] head 単独では不十分である。新しい inspector が空 rows に `previous_event_sha256()` を直接適用すると、不在と空を zero SHA へ潰せる。
- [推奨する exact proof] top-level `attempt_registry` を次の閉じた object にする。

  - `schema = "s8b-floor-attempt-registry-proof/v1"`
  - `registry_schema = "s8b-floor-attempt-registry/v1"`
  - `freeze_sha256`
  - `protocol_sha256`
  - `schedule_sha256`
  - `row_count`。正整数必須
  - `chain_head_sha256`

- `S8BAttemptBinding` は `s8b_attempt_profile.py:43-49,151-215` の freeze/protocol/schedule 3 値なので、freeze だけでなく 3 値全てを pin する。
- genesis の別 hash field は不要である。row 0 の schema/event/index/previous/event hash を検査し、chain head が genesis を推移的に commit するためである。
- registry 不在、空、非 canonical、chain 不連続、event hash 不一致、別 binding は proof を返す前に拒否する。これで zero SHA を正例として扱わない。

### P3: 検査位置

- [実測] pure verifier の境界は `s8b_floor_stats.py:682-716`。現在も live filesystem を読まず、外部 expected receipt と artifact を比較するだけである。
- [実測] live wrapper は `:1036-1082` で inspector を自ら呼び、その結果を pure verifier に渡す。
- [実測] holdout inspector は `s8b_holdout_admission.py:5687-5699` から始まり、`:5802` の read-only lock 内で実体を読み、`:6395-6425` で receipt を返す。
- [推奨] `verify_floor_artifact()` には I/O を入れない。v5 では `artifact.attempt_registry` の exact shape と、`expected_attempt_registry` との完全一致だけを検査する。v4 では両方を要求しない。
- live wrapper は v5 の場合だけ、admission module に追加する sibling inspector `inspect_floor_attempt_registry_evidence()` を呼ぶ。既存 `inspect_floor_holdout_admission_evidence()` の receipt に別台帳を混ぜない。
- producer も同じ registry inspector を呼んで field を組み立てる。その値は後段 live wrapper がもう一度実体から再導出するため、producer 引数の自己申告だけを信じる構造にはならない。

### P4: adapter 遮断

meta-test は `orchestrator/tests/test_s8b_attempt_registry.py:1553-1599` である。

検査本文は次のとおりである。

- `:1557-1561`: `ast.Import` の import 名末尾が `s8b_attempt_registry`
- `:1562-1569`: `ast.ImportFrom` の module 末尾、または alias 名が同名
- `:1570-1571`: `ast.Name` が同名
- `:1572-1577`: string constant が `s8b_attempt_registry` を含む
- `:1586-1592`: 対象は `s8b_floor_campaign.py` と `s8b_holdout_admission.py`
- `:1594-1599`: synthetic import が必ず検出される positive control

したがって、

- campaign または admission からの直接 import は、読み取り目的でも赤になる。
- floor_stats は現在の meta-test の対象外なので機械的には赤にならない。しかし `s8b_attempt_registry.py:4-16` の sole connection owner 契約には反するため採用不可である。
- 推奨経路は、admission が既に持つ `attempt_registry_core` / `s8b_attempt_profile` import (`s8b_holdout_admission.py:40-42`) と、canonical path 導出・raw reader (`:4960-4990`) を再利用すること。adapter を import しない。
- `registry_path()` 自体は `s8b_attempt_registry.py:468-490` で shared root を provision するため、read-only verifier から呼ぶと副作用も生じる。既存 admission の layout-based read-only path が適切である。

### P5: historical reverify

実経路は次である。

1. `s8b_ratified_freeze.py:3558-3568` の `reverify_published_freeze()`
2. `:3073-3095` の共通 `_launch_validate()`
3. result parse `:3195-3199`
4. top-level 検査 `:3253-3259`
5. live wrapper `:3260-3275`
6. ratified 固有 result 検査 `:3297-3302`
7. 現状の schema 単一等値検査は `:2385-2389`

v5 導入時は、手順 4、5、6 を schema-aware にする。v4 なら registry inspector を呼ばず、現在の holdout admission、journal、binary、統計検査をそのまま行う。これで既存 v4 の受理条件を増減させず、v5 だけ registry 束縛を追加できる。

なお repository-wide 検索では、production から `s8b_floor_attempt_launcher.launch_floor_attempt()` を呼ぶ箇所は無かった。定義は `s8b_floor_attempt_launcher.py:648-688`、実呼び出しは test 側だけである。したがって現状の production campaign は registry を作らず、新 v5 gate 導入後は fail-closed で停止する。

## 推奨プラン

1. `orchestrator/campaign/s8b_floor_contract.py:29-38,81-87,157-166`

   - current v5、legacy v4、readable 集合を分離する。
   - `_RESULT_KEYS_V4` を現行集合、`_RESULT_KEYS_V5 = _RESULT_KEYS_V4 | {"attempt_registry"}` とする。
   - `_RESULT_KEYS` は current v5 の alias とし、既存 import 面を壊さない。
   - `result_keys_for_mode(mode, *, schema=RESULT_SCHEMA, perf_preflight=None)` に変更し、v4/v5 ごとの exact 集合を返す。未知 schema は拒否する。
   - proof object の exact key validator `validate_floor_attempt_registry_proof()` を追加する。row count は正整数、全 digest は lowercase SHA-256、schema は exact literal とする。

2. `orchestrator/campaign/s8b_holdout_admission.py:4952-4990,5687-5700`

   - `_floor_registry_path()` の既存 layout 導出を freeze-wide helper として再利用する。
   - `inspect_floor_attempt_registry_evidence(repo_root, protocol, freeze_sha256, schedule)` を追加する。
   - `_locked_readonly` と no-follow regular-file 読み取りを使い、不在・空を `FloorHoldoutEvidenceError(category="unverifiable", reason="attempt-registry-missing")` へ倒す。
   - canonical JSONL、schema/event exact key、`event_index`、previous hash、各 `event_sha256`、genesis、full binding を検査する。
   - 検査後だけ `previous_event_sha256(rows)` を呼び、proof object を返す。
   - lifecycle transition の新しい一般 gate は追加しない。本 wave が見るのは registry identity、chain integrity、freeze/protocol/schedule binding に限定する。

3. `orchestrator/campaign/s8b_floor_stats.py:412-416,682-768,1036-1082`

   - `verify_floor_artifact()` に keyword-only `expected_attempt_registry=None` を追加する。
   - artifact schema を先に読み、schema を `result_keys_for_mode()` へ渡す。
   - v5 では exact keys により field 欠落を即拒否し、proof validator を通した reported/live object を完全一致比較する。
   - v4 では field を exact key 集合から禁止し、registry を要求しない。
   - live wrapper は v5 のときだけ新 inspector を呼び、その戻り値を pure verifier へ渡す。caller が expected registry proof を注入できる引数は live wrapper に作らない。
   - `:412-416,688-694,1045-1049` の保証境界を更新し、「pure verifier は proof 射影を比較するが registry 実在を保証しない。live wrapper が現在の registry を読む。session と registry lifecycle row の完全対応は本 wave の射程外」と明記する。

4. `orchestrator/campaign/s8b_floor_campaign.py:6426-6477,6584-6622,6650-6684`

   - normal 完走と finalize-pending の両方で、holdout receipt と registry proof を result assembly 前に取得する。
   - `assemble_result()` に required keyword `attempt_registry` を追加し、contract validator で正規化する。
   - result dict に `"attempt_registry": normalized_attempt_registry` を必須挿入する。
   - `_verify_result_with_live_admission()` が直後に再読するので、assembler へ渡された値だけを trust root にしない。
   - `result.md` に registry schema、row count、chain head、binding 3 値を表示する。
   - 影響する出力は `.result.json.pending`、`result.json`、`.result.md.pending`、`result.md` (`:6766-6777,6795-6796`)。manifest と journal の schema は変えない。新規 result raw SHA と、それを参照する将来の `floor_source.sha256` は変わるが、既存 bytes は書き換えない。

5. `orchestrator/campaign/s8b_holdout_freeze.py:1424-1440,1620-1630`

   - key 検査には artifact schema を渡す。
   - `result.schema == RESULT_SCHEMA` は残す。ここが新規 certified candidate の v5-only 前向き境界である。
   - live wrapper 呼び出しはそのまま中央入口を使う。
   - 新規 v4-shaped result を candidate に使えない負例を追加し、schema downgrade を閉じる。

6. `orchestrator/campaign/s8b_ratified_freeze.py:2333-2390,3253-3302`

   - top-level key 検査を artifact schema 別にする。
   - `_validate_result()` の current schema 等値を readable schema membership に変える。
   - v4 は現行 rules、v5 は proof field 必須とする。
   - `launch_validate()` と `reverify_published_freeze()` は publish 済み v4/v5 を読む。新規発行の v5-only は前項が担う。

7. test fixture 更新

   - `orchestrator/tests/s8b_floor_evidence_fixture.py:183-351` の隣に、canonical registry と独立 expected proof を作る helper を追加する。
   - `test_s8b_floor_campaign.py:734-784`、`s8b_v2_freeze_fixture.py:337-475`、`test_s8b_ratified_verify.py:459-475,609-617`、`test_s8b_ratified_freeze.py:966-1086,1225-1265` の current-v5 fixture に registry bytes と proof を追加する。
   - historical v4 fixture は schema を literal v4 に固定し、registry を作らない。

実装の land 前提として、現 production campaign に registry writer の接続が無い事実を親が認識する必要がある。本 wave 単体では「registry が無い新規 campaign は certified result を発行できない」が正しい fail-closed 動作になる。

## 却下した代案

- 単純な `RESULT_SCHEMA` の v5 置換  
  `s8b_floor_stats.py:745-748` と `s8b_ratified_freeze.py:2385-2389` が v4 を拒否するため却下。

- v4/v5 を全入口で無条件に併読  
  新規 producer が schema と field を v4 へ落として gate を消せる。新規 candidate 入口の v5-only 等値検査が必要。

- artifact path、日時、campaign ID の基準時点 allowlist  
  path/日時は identity の暗号学的根拠にならず、既存 artifact の完全な列挙も repo 内に無い。別の管理台帳も scope 外。current producer schema と publish 済み readable schema の分離の方が小さい。

- chain head 単独  
  空 rows と不在を zero SHA に潰す実装を作りやすく、binding も表示できないため却下。

- genesis hash、raw file hash、registry path まで全て重複 pin  
  valid chain head は genesis と全 row を既に commit する。path は freeze から一意導出される。重複 field は新しい不一致面だけを増やす。

- holdout admission receipt v1 へ registry field を混ぜる  
  v4 artifact の既存 receipt exact shape (`s8b_floor_contract.py:66-70,357-397`) を破壊し、二つの台帳の row count を混同させるため却下。

- campaign、admission、floor_stats から adapter を直接 import  
  campaign/admission は meta-test が赤。floor_stats は検査漏れだが sole owner 契約違反。既存 admission の read-only core/profile 経路を使う。

- `registry_path()` または `read_attempt_registry()` の直接利用  
  adapter import 違反に加え、shared root provisioning を伴う。historical read-only verifier の経路に適さない。

## 赤になる既存 test

直接赤になる pin は次である。

| test | file:line | 理由 |
|---|---:|---|
| `test_floor_campaign_directly_reexports_shared_leaf_objects` | `test_s8b_floor_contract.py:164-180` | v4 literal pin |
| `test_pure_verifier_rejects_legacy_result_schema` | `test_s8b_floor_stats.py:1321-1325` | error が「current v4 でない」から「readable v4/v5 外」へ変わる |
| `test_official_result_rejects_perf_preflight_receipt_fail_closed` | `test_s8b_floor_campaign.py:5963-6005` | direct `assemble_result()` に proof 引数が無い |
| `test_official_degraded_result_records_strict_perf_observation` | `test_s8b_floor_campaign.py:6008-6054` | 同上 |
| `test_producer_rejects_incomplete_binary_coverage[result-*]` | `test_s8b_floor_campaign.py:12760-12778` | required keyword を追加する場合、既存の先行 binary rejection を維持する引数更新が必要 |

transitive に赤になる fixture 面は次である。

- `test_s8b_floor_campaign.py:734-784` の成功 campaign helper。registry writer が production に無いため、これを使って completion へ到達する全 test は registry 不在で停止する。fixture が canonical registry を用意する一箇所の更新が必要。
- `s8b_v2_freeze_fixture.py:340-364,415-475`。`RESULT_SCHEMA` は v5 になるが proof field が無い。
- `test_s8b_ratified_verify.py:459-475,588-617`。同じく current 定数で v5 になるが proof と live registry が無い。
- `test_s8b_ratified_freeze.py:966-1086,1225-1265`。production emitter が registry 不在で止まり、さらに `:1069-1072,1249-1252` の admission root 再構築が registry まで削除する。
- `test_s8b_holdout_freeze.py:1702-1754` の bespoke candidate fixture。同じ current-v5 proof 欠落。

指定された他の pin の判定は次である。

- `test_s8b_floor_contract.py:367-383` は `_RESULT_KEYS` と `result_keys_for_mode()` を同時参照する coupled pin なので、両方を同じように誤変更すると赤にならない。node 名を維持したまま v4 exact と v5 exact を独立 literal で検査するよう強化する。
- `test_s8b_floor_stats.py:596` は literal v4 のまま残す。これは後方互換の正例になるため赤にしてはいけない。
- `test_s8b_floor_stats.py:677-679,767-769,936-956` は v4 fixture の exact-key error pin であり、v4 の文言を維持すれば赤にならない。
- `test_official_perf_closure.py:197,199,329` は `verify_floor_artifact` の記号名、`use_perf_from_receipt`、`result_keys_for_mode` 呼び出しを pin する。推奨案は関数名も両呼び出しも維持するので赤にならない。
- `acceptance_duration_ledger.json:11908,11934,11965,11969,11975` は既存 node 名の pin。既存 test を rename せず内容だけ更新し、新規 node は親の実測後に通常の duration ledger 更新へ流す。

## テスト計画

正例:

- `orchestrator/tests/test_s8b_holdout_admission.py::test_attempt_registry_inspection_returns_exact_binding_count_and_chain_head`
- `orchestrator/tests/test_s8b_floor_stats.py::test_verify_v5_accepts_matching_live_attempt_registry_proof`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_v5_result_records_live_attempt_registry_before_pending_publish`
- `orchestrator/tests/test_s8b_ratified_verify.py::test_v5_certified_reverify_accepts_matching_attempt_registry`
- 既存 `test_s8b_floor_stats.py::test_verify_accepts_consistent_artifact` は `:596` の v4 fixture のまま通す。
- `orchestrator/tests/test_s8b_ratified_verify.py::test_historical_reverify_accepts_v4_without_attempt_registry` を追加し、registry inspector を「呼ばれたら fail」にして v4 の非遡及を固定する。

負例は向きを分ける。

- artifact 欠落:  
  `test_s8b_floor_stats.py::test_verify_v5_rejects_missing_attempt_registry_field_even_with_live_proof`

- producer 欠落:  
  `test_s8b_floor_campaign.py::test_v5_producer_cannot_drop_attempt_registry_before_live_self_check`  
  field を落とした assembler を注入し、`.result.json.pending` が無いことまで確認する。

- live registry 不在:  
  `test_s8b_ratified_verify.py::test_v5_certified_reverify_rejects_missing_attempt_registry`

- artifact head 改竄、live は正常:  
  `test_s8b_ratified_verify.py::test_v5_certified_reverify_rejects_reported_chain_head_tamper`

- live registry 改竄、artifact は正常:  
  `test_s8b_holdout_admission.py::test_attempt_registry_inspection_rejects_row_hash_chain_tamper`

- 別 freeze の registry bytes を expected path に置く:  
  `test_s8b_ratified_verify.py::test_v5_certified_reverify_rejects_registry_bound_to_other_freeze`

- v4 downgrade を新規 candidate に使う:  
  `test_s8b_holdout_freeze.py::test_v2_candidate_rejects_legacy_v4_result_after_v5_cutover`

- v4 historical 回帰:  
  `test_s8b_ratified_verify.py::test_historical_reverify_accepts_v4_without_attempt_registry`

恒真化回避は、v5 exact key 欠落、producer 実経路の field 削除、live registry 不在の 3 層で示す。「field があれば比較」という分岐は置かない。

## 変異事前登録の候補

| 変異位置 | 変異 | KILL する test node id |
|---|---|---|
| `s8b_floor_contract.py:34` 周辺 | current schema を v4 に戻す | `test_s8b_floor_contract.py::test_floor_campaign_directly_reexports_shared_leaf_objects` |
| `s8b_floor_contract.py:157-166` | v5 key 集合から `attempt_registry` を除く | `test_s8b_floor_contract.py::test_result_v4_key_contract_is_mode_conditional_and_exact` |
| `s8b_floor_stats.py:734-748` | v5 missing field を許す | `test_s8b_floor_stats.py::test_verify_v5_rejects_missing_attempt_registry_field_even_with_live_proof` |
| `s8b_floor_stats.py:759-768` 付近の新比較 | reported/live proof 比較を削除 | `test_s8b_ratified_verify.py::test_v5_certified_reverify_rejects_reported_chain_head_tamper` |
| `s8b_floor_stats.py:1036-1082` | v5 でも registry inspector を呼ばない | `test_s8b_ratified_verify.py::test_v5_certified_reverify_rejects_missing_attempt_registry` |
| `s8b_holdout_admission.py:4969-4975` 周辺 | missing を zero-head proof に変える | `test_s8b_holdout_admission.py::test_attempt_registry_inspection_rejects_missing_and_empty_registry` |
| `s8b_holdout_admission.py:4983-4990` 周辺 | event hash 再計算または previous 比較を削除 | `test_s8b_holdout_admission.py::test_attempt_registry_inspection_rejects_row_hash_chain_tamper` |
| `s8b_holdout_admission.py:5044` 付近の新 binding 検査 | freeze binding 比較を削除 | `test_s8b_ratified_verify.py::test_v5_certified_reverify_rejects_registry_bound_to_other_freeze` |
| `s8b_floor_campaign.py:6584-6622` | producer から field を削除 | `test_s8b_floor_campaign.py::test_v5_producer_cannot_drop_attempt_registry_before_live_self_check` |
| `s8b_holdout_freeze.py:1437-1439` | current v5 等値を readable v4/v5 へ緩和 | `test_s8b_holdout_freeze.py::test_v2_candidate_rejects_legacy_v4_result_after_v5_cutover` |
| `s8b_ratified_freeze.py:2385-2389` | readable 判定を current v5 等値へ戻す | `test_s8b_ratified_verify.py::test_historical_reverify_accepts_v4_without_attempt_registry` |

## 親 brief への異議

- `brief.md:102-105` の schema provisional は、単一定数と単一等値検査の現状を考慮していない。単純版上げは非遡及にならない。
- `brief.md:106-109` の「空 registry と削除済み registry が head zero で区別不能」は、adapter reader を正しく使う限り現状では起きない。危険なのは admission raw reader `s8b_holdout_admission.py:4969-4975` の空射影を新 proof readerがそのまま使う場合である。
- `brief.md:110-117` の A2+A12 併用は方向は近いが、holdout receipt 自体へ registry identity を混ぜるべきではない。A2 が二つの inspector を調停する方が v4 receipt を保てる。
- `brief.md:114-117` の「遮断は書き込み所有権だけ」は誤り。meta-test は目的を区別せず direct import を落とす。stats は検査漏れなだけである。
- `brief.md:59-61` の A9/A10 だけでは full read 経路にならない。`registry_path()` と adapter reader は provisioning を伴い、read-only historical verifier へ直接持ち込めない。
- `brief.md:71-81` の pin 閉包には `s8b_holdout_freeze.py:1429-1439`、`s8b_ratified_freeze.py:2333-2390`、current schema を使う 3 系統の共有 fixture、admission root 再構築による registry 削除が不足している。
- 最大の不足は production writer の発火経路である。`s8b_floor_attempt_launcher.py:648-688` の production 呼び手は 0 件で、通常 campaign は registry を作らない。scope を守るなら、v5 導入後の通常 campaign が registry 不在で停止することを親 brief に明記すべきである。

## 総括

- 推奨は schema v5。ただし新規発行 v5-only と historical readable v4/v5 を分離する。
- proof は full binding、正の row count、chain head を pin し、genesis hash の重複 field は置かない。
- pure verifier は比較だけ、live wrapper が read-only registry inspector を呼ぶ。
- adapter 直接 import は避け、既存 admission の core/profile 読み取り経路を使う。
- pytest は未実走。現 production に registry writer の発火経路が無い点は land 前の明示事項である。