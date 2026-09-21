静的に照合した実装プランです。ファイル変更・テスト実行・codec の動的実測は行っていません。行番号は現状のソースを指します。

以下では `C/` = `orchestrator/campaign/`、`T/` = `orchestrator/tests/` とします。P1〜P7 は採用し、P4・P6・P7 の具体化を下記で固定します。

## 1. side channel の file と schema

**挿入場所:** `C/p3_s4_loop.py:1505` の `return state_from_dict(json.load(f))` 後、`:1508` の `# ==== mutation-red 汎用ゲート` 前に、base 専用 helper 群を置きます。

先例は `C/p3_s4_loop_trigger_gating.py:257` の `_provenance_path`、`:427` の `_append_provenance_entry`。trigger module 自体は import しません。

保存先は P3・P7 どおり、次とします。

```text
<campaign root>/reports/p3_s4_loop_provenance.json
```

top-level は、最小 header と iteration keyed entries にします。trigger 固有の情報源・firewall・gate record は移植しません。

```json
{
  "schema_version": "p3-s4-loop-provenance/v1",
  "axis": "silo-backoff-magnitude",
  "entries": {
    "1": {
      "iteration": 1,
      "variant": null,
      "build_attempt_id": null,
      "initial_proposal_sha256": null,
      "wal_refs": [],
      "outcome": "dry-pass"
    }
  }
}
```

| field | 型・値域 |
|---|---|
| `iteration` | exact `int`、1 以上。`entries` のキーはその十進文字列表現。bool は不可 |
| `variant` | 非空 `str` または null。既存の `out.get("variant")` を保存し、再計算しない |
| `build_attempt_id` | WAL payload 由来の非空 `str` または null。独自 ID を生成しない |
| `initial_proposal_sha256` | lowercase 64 hex または null |
| `wal_refs` | `list[str]`。各要素は `wal:` + lowercase 64 hex。WAL 出現順 |
| `outcome` | `certified` / `aborted` / `rejected` / `dry-pass` / `duplicate` / `duplicate-skip` / `rejected-preprocess` |

以下の `i` は消費後の `state.iteration`、`H` は読み込んだ proposal document の canonical hash、直接 API 呼出しで未提供なら null、`R(A)` は attempt A の record refs です。

| outcome／経路 | iteration | variant | build_attempt_id | initial_proposal_sha256 | wal_refs | outcome |
|---|---:|---|---|---|---|---|
| 新規 certified | i | `pipeline.variant_id` | 今回の commit に対応する A | H | R(A) | `certified` |
| 新規 aborted | i | out の variant | 今回の abort／start の A | H | R(A) | `aborted` |
| ID 未確定の aborted | i | null | null | H | `[]` | `aborted` |
| diff quarantine reject。no-build の reject も同じ | i | `diffq-*` | 今回書いた reject の A | H | R(A) | `rejected` |
| dry-pass | i | null | null | H | `[]` | `dry-pass` |
| certified の重複再利用 | i | 再利用先 variant | 再利用された commit の A | **今回の** H | R(A) | `duplicate` |
| aborted の重複再利用 | i | 再利用先 variant | 再利用された abort の A | 今回の H | R(A) | `aborted` |
| B-5 duplicate-skip | i | null | null | H | `[]` | `duplicate-skip` |
| drive 内の rejected-preprocess | i | null | null | H | `[]` | `rejected-preprocess` |
| pair mode 候補側 | i | 上記各経路と同じ | 同左 | H | 同左 | 候補の outcome |

重要な境界は次のとおりです。

- `C/p3_s4_loop.py:2296` の `if b5_mode and summary.skipped > 0:` は、現状 `variant=None` を返します。side channel のために skipped variant を推測しません。
- `:1896` の `_resolve_duplicate` の失敗側は `aborted` です。新しい `duplicate-aborted` enum は作りません。
- snapshot 拒否などで `aborted` の variant は分かるが使用 attempt を特定できない場合は、`build_attempt_id=null, wal_refs=[]` として不足を残します。別 attempt を選んで穴埋めしません。
- CLI の proposal 読込み失敗は `:3509` の例外処理から `return 3` に進み、drive に入りません。この場合は iteration 未消費なので entry もありません。drive 内の `rejected-preprocess` と区別します。
- stock、`stopped-before`、outcome を返す前の例外について、消費済み iteration を捏造しません。

**P6 の実装規則:** `_wal_attempt_provenance(layout, out)` を base に追加します。

1. `certified` / `duplicate` は、判定経路が返した `out["records"]["commit"]["build_attempt_id"]` を優先します。
2. `aborted` は使用した abort の ID、terminal 前の中断なら使用した start の ID を取ります。証拠不足を別 attempt の「最後の start」で救済しません。
3. `rejected` は今回の `record_diff_reject` が末尾に追加した同 variant の abort/start ペアから取ります。`:985`〜`:997` は毎回新しい ID を両 record に記録します。
4. `wal.read_records(layout)` の**元の record 全体**について、variant と attempt ID の両方が一致するものを出現順に列挙します。

```python
"wal:" + agent_outputs.canonical_sha256(vars(record))
```

`C/wal.py:2867` の `records_by_stage` は最後勝ちで、`:2888` では receipt payload も取り除きます。したがって **ref の hash 入力には使用しません**。複数の `verify_done`、receipt を含む commit、過去の同 variant の別 attempt を区別します。

新規 certified/rejected など、ID が存在するはずの経路で対応 start が欠落・競合していれば記録不能として停止します。既存の certified/reject 判定そのものは変更しません。

## 2. 書き込み位置と順序

**主挿入点:** `C/p3_s4_loop.py:2873`、前アンカー `_run_one_iteration_resolved(...)` の閉じ括弧、後アンカー `save_loop_state(layout, state)`。

```python
out = _run_one_iteration_resolved(...)
entry = {
    "iteration": state.iteration,
    "initial_proposal_sha256": initial_proposal_sha256,
    "outcome": out["outcome"],
    **_wal_attempt_provenance(layout, out),
}
_append_provenance_entry(layout, state.iteration, entry)
save_loop_state(layout, state)
```

順序を次に固定します。

```text
入口停止判定
→ iteration 加算
→ 既存の評価・重複解決・whiteboard 射影
→ provenance の公開
→ checkpoint 保存
→ B-5 早期 return または既存 digest 処理
```

- `:2876` の `if b5_mode and out["outcome"] in {"duplicate-skip", "rejected-preprocess"}:` より前なので、両経路も記録されます。
- `:2844` の `pre = check_stop(state)` → `:2846` の入口停止用 `save_loop_state` は現状を維持します。P5 に従い、この経路で provenance header も作りません。
- provenance helper の例外を握り潰さず、`save_loop_state` を `finally` に置きません。書込み失敗時、disk 上の checkpoint は以前のままです。
- 既に書かれた WAL と in-memory state の変更は巻き戻しません。保証するのは「provenance 未公開の iteration を checkpoint に確定しない」です。
- provenance と checkpoint は二つの file であり、二重書込みを一括 transaction にする保証はありません。provenance だけ公開された中断は項目 4 の merge で扱います。

先例は trigger `:1149` の `provenance_entry = {` → `:1158` `_append_provenance_entry` → `:1159` `L.save_loop_state` です。

## 3. proposal の canonical hash の配管

**変更点 A:** `C/p3_s4_loop.py:2717`、前アンカー `assert_no_ability_probe_material(d)`、後アンカー `return planner, coder, prior`。

既存の capture に、検証済みの元 document を追加します。

```python
capture.update(
    proposal_bytes=proposal_bytes,
    proposal_document=d,
    planner_output=d["planner"],
    coder_output=d["coder"],
)
```

capture 更新は現状どおり検証完了後です。K2 の取り込み後に dataclass から document を再構築せず、`:2631` などで parse した `d` を使います。

**変更点 B:** `:3496` の loader 呼出し直前と `:3508` の直後。

```python
proposal_capture = agent_record if agent_record is not None else {}
planner, coder, prior_rev = load_proposal_file(
    ...,
    capture=proposal_capture,
)
initial_proposal_sha256 = canonical_b4_proposal_sha256(
    proposal_capture["proposal_document"]
)
```

`:3507` の条件付き capture を上記に置換します。`--agent-inputs` のない通常 CLI でも hash が得られ、journal は引き続き opt-in のままです。file を再読込みしないので、読込み後の file 差替えにも影響されません。

**変更点 C:** `:2734` の `agent_record` 付近に keyword-only 引数を追加し、`:3521` の `drive_iteration(...)` 呼出しから渡します。

```python
initial_proposal_sha256: str | None = None
```

- `None` は「document の canonical identity がこの呼出しでは提供されていない」。空 document や dataclass の hash で補完しません。
- 非 null は exact string / lowercase 64 hex を検査します。
- 既存の位置引数・戻り値は変えません。直接呼ぶ既存 caller は省略でき、その entry は hash=null です。
- `canonical_b4_proposal_sha256` は `:526`〜`:542` を再利用します。`:531` の receipt key 除去により、B-4 の receipt 束縛検査と proposal identity は両立します。
- hash は B-4 marker の有無によらず計算します。`1` と `1.0` の相違など、既存 canonical identity の意味も維持します。
- sort / trigger の独自 `drive_iteration` へ引数や writer を展開しません。共有 `_resolve_duplicate` の評価ロジックも変更しません。

## 4. 書き込みの堅さ――P4 / P7

**実装場所:** 項目 1 の `C/p3_s4_loop.py:1505`〜`:1508` 間に `_load_provenance` / `_write_provenance` / `_append_provenance_entry` を追加します。

**公開方法は tmp + fsync + replace を採用します。**

1. 保存先と同じ directory に一意な tmp を `O_CREAT | O_EXCL` で作る。
2. JSON を `allow_nan=False` で encode して書く。
3. `flush()` → file `fsync()`。
4. `os.replace(tmp, destination)`。
5. directory を `fsync()`。
6. 失敗時の tmp を `finally` で片付け、例外は伝播する。

根拠は trigger `:283`〜`:296` の可変 report の atomic replace と、`:361`〜`:380` の source preimage の排他的 tmp・file fsync です。source preimage の `os.link` による最終 file の非上書き公開は、毎 iteration 更新する report には採用しません。

**同 iteration は上書き merge とします。**

- 他 iteration と header を保持し、対象 iteration の六つの field を今回の entry で更新します。
- 同じ entry の再追加では意味も canonical bytes も変わりません。
- provenance 保存後・checkpoint 保存前に中断した場合、再実行が `certified` から `duplicate` へ変わり得ます。差分の一律拒否は、この正常な回復経路を塞ぎます。
- これは trigger `:430`〜`:438` の契約を採用する判断です。source preimage の「異なる内容なら拒否」は移植しません。
- 同一 campaign の単一駆動を前提とし、atomic replace を並行 writer 間の merge 排他保証とは呼びません。既存 checkpoint の `:1487`〜`:1489` と同じ前提です。

**破損時は退避して停止します。**

- JSON decode 不能、UTF-8 不正、header / entries / entry の型不正を、空 report に置換して続行しません。
- 元 bytes を `<path>.corrupt.<epoch>` に保全し、衝突時は一意 suffix を付けます。既存退避 file を上書きしません。
- 退避後は例外で停止し、checkpoint を更新しません。退避操作そのものが失敗した場合も停止します。
- 原本不在かつ未処理の `.corrupt.*` がある場合、次回を新規 report と扱って自動再初期化しません。復旧対象であることをエラーに含めます。
- 同 iteration の有効な entry 差分と、file 破損は区別します。

P7 の「意味は provenance 系、堅さは source-preimage 系」をこの組合せで採用します。base に source preimage artifact は追加しません。

## 5. 参照点の定義の置き場――P1

**配置:** 新設 `_wal_attempt_provenance` の docstring を `C/p3_s4_loop.py:1505`〜`:1508` 間に置き、module docstring `:33` の「fixture proposal…」段落より前から参照させます。resolver や reference field は作りません。

docstring には次の定義を明記します。

> D2194 項 3 に基づき、参照点は同一 campaign の precursor iteration より前の最後の whiteboard `success` に対応する certified attempt とする。iteration から variant / build_attempt_id への対応には本 report を使う。重複提案は既存評価を再利用するため、whiteboard の行順と評価の系譜は同一ではない。
> `reference_snapshot_hash` は当該 attempt の WAL `commit` record 全体、`reference_receipt_hash` は同 attempt の `bench_done` record 全体を、`agent_outputs.canonical_bytes` により canonical 化した sha256 とする。値は接頭辞なしの 64 hex であり、本 report の `wal_refs` は同 digest に `wal:` を付ける。
> 祖先なし、同着候補、対応 record の非一意、承認済み `PerfConfig` または `env_tag` の一致を確認できない場合は不適格とする。別の祖先や別基準へ切り替えない。実走前は `design_not_feasible`、実走後は protocol violation とする。

一致条件の出所も続けて書きます。

- 承認済み `PerfConfig` の `records / threads / workload` の**全 key** / `extime / reps` を比較対象とする。
- `bench_done.payload.run_cmd` は threads・records・extime・workload の rratio / skew / rmw の証拠、record の `env_tag` は環境 tag の証拠。
- `reps` と workload の `ycsb_max_ope` は run_cmd では確認できない不足として残す。`len(tps)` や default 値による推測を全 field 一致と呼ばない。
- snapshot の throughput と bench receipt は、同じ certified attempt に対応する既存 WAL を使う。

根拠アンカーは `C/agent_outputs.py:69` の `canonical_bytes` と `:77` の `canonical_sha256`、射影された `prereg-s5.1.1-reference.md:1` の「共通参照点」です。

親の insight / decisions fragment に同じ定義と発効時点を記録します。凍結事前登録本文、bootstrap 集合、analysis manifest producer は変更しません。

## 6. caller の修正

**変更場所:** `C/p3_b4_prerun_caller.py:16` の import 群、`:65`〜`:83` の `try` / `except`。

前アンカーは `checkpoint = json.loads(...)`、後アンカーは `rejected = []` です。

```python
decoded = campaign_lock.decode_campaign_lock_bytes(
    (root / "campaign.lock").read_bytes()
)
if not isinstance(checkpoint, dict):
    raise ValueError("checkpoint must be a JSON object")
...
trial = decoded.identity.get("trial")
```

`decoded.identity["trial"]` の無条件添字より `.get("trial")` を推奨します。**codec の v1 branch は trial 必須を検査していない**ためです。`.get` なら既存の `unknown trial` 判定で `CampaignInputUnreadable` に写せます。添字を採るなら `KeyError` の明示変換が必要です。

`CampaignLockCodecError` は `C/campaign_lock.py:404` で `ValueError` を継承しています。したがって既存 `except (..., ValueError, RecursionError)` が捕捉し、`:83` の

```python
raise CampaignInputUnreadable(root, str(exc)) from exc
```

へ到達します。codec 専用の fallback や v1/v2 判別を caller に追加する必要はありません。

**v1 受理についての静的結論:**

- `C/campaign_lock.py:901`、前アンカー `value = _loads(...)`、`:930` の reserved-key 検査後、`:934` の `identity = value` が v1 です。
- schema のない JSON object を identity として保持します。v1 には v2 の exact identity keys / canonical wire の制約を追加していません。
- duplicate JSON key、非有限値、reserved field などは既存 codec が拒否します。
- 親が示した tracked 3 campaign の v1 形はこの読取り経路に乗る見込みです。**この段では実物を decoder に渡す実測はしていません。** 親の回帰テストで確認します。

**fixture の v2 化:** `T/test_p3_b4_prerun_caller.py:19` の `_campaign`、`:27` の lock 書込みから `:34` の checkpoint 書込み前を置換します。

```python
identity = {
    "trial": trial,
    "search_config": {...},
    "ccbench_commit": "fixture-commit",
    "search_tag": "fixture",
    "spec_content": "synthetic campaign",
}
lock_text = build_v2_campaign_lock(
    campaign_lock.canonical_json(identity)
)
```

`T/campaign_lock_test_support.py:23` の helper を利用します。inner は canonical JSON **文字列**、outer は helper が返した文字列をそのまま保存し、追加の `json.dumps` や末尾改行を入れません。

`:232` の `broken == "trial"` は、valid v2 identity 内の trial を `"unknown"` にして再 encode する形へ変更します。これにより codec 不正ではなく、caller の `_DRIVERS` 拒否を検査できます。別ケースとして trial 欠落の v1、壊れた v2 authority、非 canonical inner/outer を追加します。

## 7. test 案

**配置アンカー:** `T/test_p3_s4_loop.py:7053` の checkpoint 継続 test と `:7095` の dry-pass test 周辺に drive 検証、`:7978` の duplicate fixture 周辺に attempt 検証、`:9254` の live CLI test 周辺に hash 配管検証を追加します。

| 追加 test 名 | 主な assertion |
|---|---|
| `test_base_provenance_records_each_outcome` | 項目 1 の各 entry が六つの exact key と表の値に一致。`entries["1"]["iteration"] == 1` |
| `test_base_provenance_rejects_same_variant_use_distinct_attempts` | 同じ diffq variant を二回 reject し、ID が異なる。各 `wal_refs` がその回の start/abort のみ |
| `test_base_provenance_duplicate_reuses_selected_attempt` | duplicate の ID が採用された commit の ID。別 attempt の ref は含まない。WAL record 数は増えない |
| `test_base_provenance_keeps_all_attempt_records` | 複数 `verify_done` と receipt 付き commit の全 record hash を保持 |
| `test_base_provenance_preserves_whiteboard_projection` | `vars(entry)` と `whiteboard_for_planner` が `{"iteration":1,"direction":"increase","magnitude":"small","result":"success","delta_pct":None}` に一致 |
| `test_base_provenance_precedes_checkpoint` | checkpoint spy 内で provenance entry が既に読める。呼出し順が `["provenance", "checkpoint"]` |
| `test_base_provenance_failure_keeps_checkpoint` | writer が `OSError` を投げると checkpoint bytes が不変。新規なら checkpoint 不在 |
| `test_base_provenance_merge_is_idempotent` | 同 entry 二回で bytes 不変。他 iteration を保持。同 iteration の `certified → duplicate` 更新が一行に収まる |
| `test_base_provenance_corrupt_report_stops` | 不正 JSON／不正型で例外、`.corrupt.*` に元 bytes、checkpoint 不変、黙った `{}` 再開なし |
| `test_base_provenance_publish_failure_preserves_old_report` | replace 前の write/fsync/replace 失敗で旧 report が完全なまま。tmp 清掃 |
| `test_base_provenance_skips_stock_and_entry_stop` | stock と `stopped-before` で report を新設・更新しない |
| `test_base_provenance_records_b5_early_returns` | `duplicate-skip` / drive 内 `rejected-preprocess` で entry が存在し、`critic_digest_generated is False` |
| `test_pair_candidate_has_one_provenance_entry` | pair 実行後、候補側の一行のみ。stock の record を refs に混ぜない |
| `test_main_provenance_hash_without_agent_inputs` | `--agent-inputs` なしでも `H == canonical_b4_proposal_sha256(document)`、journal は作らない |
| `test_main_provenance_hash_uses_loaded_document` | loader 後に proposal file を変更しても、渡される hash は読み込んだ document の値 |
| `test_base_provenance_hash_excludes_receipt_key` | receipt key を除いた canonical hash と一致。空白・key 順序変更で同じ値 |
| `test_direct_drive_provenance_hash_defaults_to_null` | 引数省略の既存 API 呼出しが動き、hash は null |

whiteboard の不変検証では、`project_whiteboard` と `whiteboard_for_planner` の呼出し中に provenance reader を poison し、side channel を参照しないことも検査します。既存 `:9380` 付近の `_assert_agent_input_ast_isolated` の root 群も維持します。

loader を stub 化する既存 CLI test は、新しい capture を実際に満たす stub に更新します。capture 欠落を production 側の空 hash fallback で救済しません。`:9362` の `test_agent_loader_capture_only_after_validation` の `capture == {}` は維持します。

**caller tests の追加位置:** `T/test_p3_b4_prerun_caller.py:81` の success-only test と `:214` の unreadable parametrization 周辺。

| test 名 | assertion |
|---|---|
| `test_v2_campaigns_reach_empty_issuer` | top-level に trial がない v2 三 driver が読める。`reason == "design_not_feasible"`、`candidate_count == 0`、issuer 一回 |
| `test_v2_rejected_campaign_reports_missing_sources` | `reason == "scheduled_input_sources_missing"`、不足 12 件、issuer 未呼出し |
| `test_v1_campaigns_remain_readable` | legacy v1 を各 driver で読める。codec の許す非 canonical v1 も区別して扱う |
| `test_invalid_lock_is_campaign_input_unreadable` | invalid UTF-8、duplicate key、非有限値、v2 authority/schema/inner/outer 不正で `reason == "campaign_input_unreadable"`、rc=2 |
| `test_unknown_v2_trial_is_campaign_input_unreadable` | valid v2 の未知 trial が caller の分岐で拒否される |
| `test_missing_v1_trial_is_campaign_input_unreadable` | `KeyError` を漏らさず、既存 error payload に写る |

**drift を避ける構成:**

- pure merge / atomic writer / canonical hash のテストは、v2 campaign 作成に依存しない小さい fixture で組みます。
- v2 lock を作る drive / caller / admission 統合テストは、実装を commit した独立 checkout で親が実行します。
- helper は `T/campaign_lock_test_support.py:10` の `_binding_from_recorded_head` により HEAD blob を使います。未 commit の production bytes を正当化するために binding 検査を緩めません。
- 変異は drift 非依存の注入群と、変異を commit した独立 clone 群に分けます。loader drift による赤を機能変異の KILL と数えません。
- 本回答に列挙したテストはすべて予定であり、実走結果ではありません。

## 8. 既存 pin・目録への影響と更新方法

| 対象・file:line・アンカー | 本案の影響／更新方法 |
|---|---|
| `T/test_campaign.py:5408` `expected_inventory`、`:5418` の base `run_campaign: 2` | **更新不要の見込み。** report writer は certified writer の新しい `run_campaign` 呼出しではありません。候補・stock の二箇所を維持 |
| `T/test_official_perf_closure.py:44` `_REVIEWED_PERF_FILES`、`:60` base path、`:831` `test_official_perf_surface_inventory_is_exact` | **更新不要の見込み。** profiler 呼出し・perf predicate・authority 経路を追加しない。参照点の PerfConfig 定義は docstring に限定 |
| `T/test_p3_exploration_namespace.py:416` `"p3_s4_loop": DriverContract` | `ast_layout_calls=11`、`ast_run_campaign_calls=2`、runtime=1 を維持。helper は渡された layout を使い、追加の `exploration_campaign_layout` を呼ばない |
| `T/test_p3_b4_wiring_probe.py:324` `test_source_segment_helper_matches_stdlib_for_all_static_ifs`、`:329` `len(static) == 49` | base の既存 import で実装すれば module 数は増えない見込み。trigger helper を import しない。call graph は変わるので inventory tests は実行対象 |
| 同 `:702` `test_inventory_names_real_producers_and_excludes_probe_consumers` | outcome/checkpoint の producer 名を変えないため literal 目録の追加は不要。新 helper を理由なく certified producer に登録しない |
| `T/test_p3_b4_closed_critic.py:604` `_independent_projection_sha256`、`:617` base path | **projection hash は変わる。** base file は全 driver の共通 closure に入る。`:655` の bytes から動的算出する fixture を使い、旧 digest を固定した証拠を流用しない |
| `C/campaign_lock.py:124` contract-loader closure の base path | **blob digest は変わる。** path 集合の追加は不要。commit 後の HEAD から新しい fixture authority を作る。既存 lock の hash を書き換えない |
| `T/acceptance_duration_ledger.json:2` `duration_seconds_by_nodeid`、末尾 `nodeid_count` | 新 nodeid は増えるが、秒数を推測して登録しない。親の実測後、既存 `tools/update_acceptance_duration_ledger.py:278` の生成経路で更新する必要がある場合だけ反映 |
| `T/test_p3_s4_loop.py:9254` live CLI、`:9362` capture、`:10573` pair fixture | capture と新しい keyword 引数を扱う stub の調整候補。評価・checkpoint・journal の既存 assertion は維持 |
| `C/artifact_admission.py:949` `_validate_trigger_provenance` | **変更しない。** base provenance の admission 検査追加は scope 外 |
| 凍結事前登録 §5 の projection hash 欄 | 親の実測では未記入。今回の hash 変更を理由に本文・欄を編集しない |

ここでの「更新不要」は静的な変更面に基づく見込みです。実装時のテスト結果に合わせて pin を機械的に追従させず、呼出し数や依存集合が増えた場合は、その差分の必要性を先に確認します。

## 9. 変異負例候補と等価対照

新設行はまだ番号がないため、**現在の挿入位置 + 変更する一行のアンカー**で指定します。下表の KILL は期待であり、未実測です。

| ID | file:line／一行変異 | 落とす test・期待する差 |
|---|---|---|
| S1 | `C/p3_s4_loop.py:2873` 挿入部の `_append_provenance_entry(...)` を削除 | `test_base_provenance_records_each_outcome`：report/entry がない |
| S2 | 同挿入部で checkpoint を先に実行する一行順序変異 | `test_base_provenance_precedes_checkpoint`、`...failure_keeps_checkpoint`：順序逆転／checkpoint 前進 |
| S3 | `:1505` 後の WAL filter から attempt ID 条件だけ削除 | `test_base_provenance_rejects_same_variant_use_distinct_attempts`：別 attempt の refs が混入 |
| S4 | 同 helper の commit 由来 ID 選択を最新 start の ID に置換 | `test_base_provenance_duplicate_reuses_selected_attempt`：再利用 commit と異なる ID |
| S5 | 同 helper の `canonical_sha256(vars(record))` を `canonical_sha256(record.payload)` に置換 | `test_base_provenance_keeps_all_attempt_records`：literal expected refs と不一致 |
| S6 | 同 helper で対象 records を stage keyed dict に圧縮する一行へ置換 | 同 test：先行 `verify_done` が消える |
| S7 | 同 merge helper の既存 entries 読取りを `entries = {}` に置換 | `test_base_provenance_merge_is_idempotent`：他 iteration が消える |
| S8 | 同 loader の破損時 `raise` を `return {}` に置換 | `test_base_provenance_corrupt_report_stops`：例外なし／記録の黙殺 |
| S9 | 同 writer の `os.fsync(stream.fileno())` を削除 | `test_base_provenance_publish_failure_preserves_old_report` の fsync 注入：期待した停止が起きない |
| S10 | `:3508` 後の canonical hash 計算を `hashlib.sha256(proposal_bytes).hexdigest()` に置換 | `test_base_provenance_hash_excludes_receipt_key`：receipt・整形差分が hash に混入 |
| S11 | `:3507` の capture を再び agent-inputs 指定時だけに限定 | `test_main_provenance_hash_without_agent_inputs`：通常 CLI の document/hash が欠落 |
| S12 | `:2873` の writer 呼出しを `if not b5_mode:` の条件付き一行へ変更 | `test_base_provenance_records_b5_early_returns`：早期 return の記録が消える |
| C1 | `C/p3_b4_prerun_caller.py:73` の decoded identity 読取りを raw lock の `.get("trial")` に戻す | `test_v2_campaigns_reach_empty_issuer`：`unknown trial: None` |
| C2 | 同 `:67` の codec 呼出しを raw `json.loads` に置換し v2 inner を手動読取り | `test_invalid_lock_is_campaign_input_unreadable`：不正 authority／非 canonical v2 を受理 |
| C3 | 同 `:67` 後に `if decoded.is_v1: raise ValueError(...)` を一行追加 | `test_v1_campaigns_remain_readable`：legacy 互換を破壊 |
| C4 | 同 `:82` の catch tuple から `ValueError` を削除 | `test_invalid_lock_is_campaign_input_unreadable`：codec 例外が CLI 外へ漏れる |
| C5 | 同 `:73` の `.get("trial")` を `["trial"]` に置換 | `test_missing_v1_trial_is_campaign_input_unreadable`：未変換 `KeyError` |

**等価対照 E1:** 新設 helper の

```python
agent_outputs.canonical_sha256(vars(record))
```

を

```python
hashlib.sha256(agent_outputs.canonical_bytes(vars(record))).hexdigest()
```

に置換します。`C/agent_outputs.py:77` の定義そのものと等価なので、全 expected refs が同じでテストが通ることを期待します。

変異の注入前に対応 test が緑であることを親が確認し、注入後の赤が表の assertion に到達した結果かを記録します。import error、capture stub 不備、contract-loader drift は当該性質の KILL と区別します。

## 総括

- P1〜P7 を採用し、base 専用 report を評価後・checkpoint 前に公開する。
- proposal は一度読んだ document、WAL refs は variant と attempt ID の両方で結ぶ。
- 同 iteration は回復可能な上書き merge、破損・公開失敗は checkpoint を進めず停止する。
- caller は既存 codec に一本化し、v2 fixture と v1 回帰を用意する。
- 静的検査のみ。凍結本文・評価判定・planner 射影・admission・bootstrap 集合は変更しない。
