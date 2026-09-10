[実測] 判定は **NO-GO** です。production 実装の主要経路は裁定どおりですが、M14 の必須実台帳テストがなく、M10 と M13 の変異帰属も別 gate に遮られています。

## blocker

### 所見 1 — M14 の段6実台帳テストが欠落している

(a) [実測] 現物には fake inspector 版しかなく、裁定が必須とした「同一 root の有効な二世代 A/B、artifact/proof=B、外部引数=A」の実台帳 test がありません。現在の test は live wrapper の正常受理も同じ test 内で確認していません。

(b) [実測] fake test は [test_s8b_floor_stats.py:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:883)。inspector の差替えは `raising=False` の [同:920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:920)。期待 freeze も artifact から取る [同:953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:953)ため、その field は外部引数から独立していません。production の外部 binding 導出自体は [s8b_floor_stats.py:1150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:1150)に正しくあります。

(c) [推測] 放置すると、wrapper が reported proof の世代 B を path 選択に使う退行を起こしても、実 filesystem 上で「外部 A に反して B を受理する」という受理集合の拡大を直接検出できません。

(d) [推測] 所有 file `orchestrator/tests/test_s8b_floor_stats.py` に二世代実台帳 test を追加してください。正しい実装が A/B 不一致を拒否し、reported binding を流用する mutant だけが B を受理する形にし、fake test には外部引数と一致する live-wrapper 正例も置きます。既存属性なので inspector の monkeypatch は `raising=True` 相当に直します。

## must-fix

### 所見 2 — M10 は recovery policy gate に遮られる

(a) [実測] 合成 v1 は exact 二段 path に置かれていますが、`_profile()` の test 固有 recovery authority で作られています。schema guard を消しても、後段の profile 再構成が production scheduler authority を使用するため、`recovery_policy_sha256` 不一致で拒否が残ります。

(b) [実測] fixture は [test_s8b_attempt_registry.py:3455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:3455)、test profile は [同:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:81)。v1 profile の再構成は [s8b_attempt_registry.py:747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:747)、後段の recovery digest gate は [同:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:803)です。

(c) [推測] 放置すると M10 は赤になっても reason が `generation-unsupported` から `replay-invalid` へ変わるだけで、schema guard が受理集合を閉じている証明になりません。

(d) [推測] 所有 file `orchestrator/tests/test_s8b_attempt_registry.py` で、合成 v1 profile を `scheduler.AUTHORITY_ID` と `scheduler.AUTHORITY_POLICY_SHA256` から作り、schema guard 削除後は後段 replay まで成功する入力へ再照準してください。

### 所見 3 — M13 の tripwire は inspector に到達しない

(a) [実測] v5-only guard を削除して v4 artifact を分岐内へ入れても、artifact に proof がないため `validate_attempt_registry_prefix_proof(None)` が先に拒否します。monkeypatch した inspector は呼ばれません。

(b) [実測] test は [test_s8b_floor_stats.py:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:848)。遮る validator は [s8b_floor_stats.py:1142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:1142)、対象 guard は [同:1133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:1133)です。

(c) [推測] 放置すると M13 の赤は proof shape gate の赤であり、「v4 が registry I/O を起動しない」という防壁の実効性を証明しません。

(d) [推測] 所有 file `orchestrator/tests/test_s8b_floor_stats.py` で、この test に限り validator を有効 proof を返す seam にし、guard 削除時だけ inspector tripwire へ到達させてください。正しい v4 経路の `[]` 正例は維持します。

### 所見 4 — unit2 の v5 test が統合後も production validator を置換している

(a) [実測] `_v5_artifact()` は全 v5 pure/live test で `validate_attempt_registry_prefix_proof` を手書き validator に差し替えています。統合後は production symbol が実在するのに `raising=False` も残っています。

(b) [実測] 手書き再実装は [test_s8b_floor_stats.py:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:646)、全体差替えは [同:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:696)。production validator は [attempt_registry_core.py:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:284)に実在します。

(c) [推測] 放置すると stats と core の結合経路が production validator を呼ばなくなっても、unit2 の v5 tests は手書き validator で通り得ます。

(d) [推測] 所有 file `orchestrator/tests/test_s8b_floor_stats.py` から通常時の validator monkeypatch を除去し、production literalと production validator で v5 fixture を検証してください。故意の lower-layer seam test だけ局所 monkeypatch に残します。

### 所見 5 — 一部の負例が複数 gate で拒否される

(a) [実測] `test_attempt_registry_prefix_rejects_genesis_binding_substitution` は明示的 binding mismatch を消しても `core.load_attempt_registry(... expected_binding=...)` が拒否します。また `test_v5_rejects_proof_binding_mismatch[freeze|protocol]` は header 相互束縛を消しても reported/independent 全field比較が拒否します。

(b) [実測] 前者は [test_s8b_attempt_registry.py:3483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:3483)と production [s8b_attempt_registry.py:957,974](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:957)。後者は [test_s8b_floor_stats.py:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:827)と production [s8b_floor_stats.py:777,801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:777)です。

(c) [推測] 放置すると assertion された reason の順序は固定できますが、対象 gate 単独の受理集合効果としては帰属できません。

(d) [推測] 所有 file `test_s8b_attempt_registry.py` と `test_s8b_floor_stats.py` で、これらを診断 node と明記するか、D1522 の条件を満たす局所 seamと正例対照で対象 gate だけへ再照準してください。M1 missing-key と M7 short-prefix は裁定済み診断扱いなので、変異観測へ昇格させないでください。

## nit

### 所見 6 — M2 の登録 nodeid が広すぎる

(a) [実測] 登録 node は schema literal、registry schema literal、4 digest、row_count の三種類の gate を一つの parametrized function にまとめています。具体的な truthy 変異対象として一箇所に存在するのは shared `_digest` の条件だけです。

(b) [実測] old は [attempt_registry_core.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:367)の `if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:`。node は `test_attempt_registry_prefix_proof_rejects_each_field_type[...]` です。

(c) [推測] 放置しても mutation は digest parameter で kill されますが、M2 が7 fieldすべての型防壁を一つの置換で証明したように読めます。

(d) [推測] 所有 file `test_attempt_registry_core_s8b_profile.py` または変異台帳で、M2 の観測を `[freeze_sha256-1]` など digest parameter に限定し、literalと row_count は M3/M17または別診断へ分けてください。

## 変異帰属表

| ID | old 逐語の所在 | 観測 nodeid | 帰属 / 遮る層 | 再照準 |
|---|---|---|---|---|
| M1 | [attempt_registry_core.py:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:295) `if actual_keys != ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS:` | `test_attempt_registry_core_s8b_profile.py::test_attempt_registry_prefix_proof_rejects_extra_key` | [実測] 成立。extra key は後段に影響しない | [実測] なし。missing-key は診断のまま |
| M2 | [attempt_registry_core.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:367) `if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:` | `...::test_attempt_registry_prefix_proof_rejects_each_field_type[freeze_sha256-1]`ほか digest 4件 | [実測] digest 型変異として成立。全7 fieldという登録表現は過広 | [推測] digest parameterへ nodeid を限定 |
| M3 | [attempt_registry_core.py:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:325) `if type(row_count) is not int or row_count < 1:` | `...::test_attempt_registry_prefix_proof_rejects_zero_row_count` | [実測] 成立 | [実測] なし |
| M4 | [attempt_registry_core.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:334) `if chain_head_sha256 == _ZERO_SHA256:` | `...::test_attempt_registry_prefix_proof_rejects_zero_head` | [実測] 成立。zero は hex64 gate を通る | [実測] なし |
| M5 | [s8b_attempt_registry.py:974](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:974) `return core.load_attempt_registry(payload, ...)` | `test_s8b_attempt_registry.py::test_attempt_registry_prefix_rejects_malformed_tail_after_n` | [実測] 成立。N=3 prefix は valid、invalid JSON は tailだけ | [実測] なし |
| M6 | [s8b_attempt_registry.py:974](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:974) 同じ full replay call | `...::test_attempt_registry_prefix_rejects_broken_chain_after_n` | [実測] 成立。tail row は canonical shapeで、自身の hashも再計算済み | [実測] なし |
| M7 | [s8b_attempt_registry.py:1039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1039) `if len(rows) < row_count:` | `...::test_attempt_registry_prefix_rejects_n_beyond_live_rows` | [実測] 事前登録外。削除後は [同:1043](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1043) の添字アクセスが拒否を残す | [実測] 変異件数に含めない |
| M8 | [s8b_attempt_registry.py:1043](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1043) `rows[row_count - 1]["event_sha256"] != chain_head_sha256` | `...::test_attempt_registry_prefix_rejects_reported_head_tamper` | [実測] 成立。genesis変更後に全3行を再chainし、full replay 成功を直接assert | [実測] なし |
| M9 | [s8b_attempt_registry.py:1043](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1043) `rows[row_count - 1]` | `...::test_attempt_registry_prefix_inspection_accepts_valid_later_append` | [実測] 成立。N=3 proof後にproduction classificationを追加 | [実測] なし |
| M10 | [s8b_attempt_registry.py:941](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:941) `genesis.get("schema_version") != ...V2...` | `...::test_attempt_registry_prefix_rejects_synthetic_v1_at_generation_path` | [実測] 不成立。後段 recovery policy/profile gate が遮る | [推測] scheduler authorityで合成 v1 を再生成 |
| M11 | [s8b_floor_contract.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_contract.py:96) `_RESULT_V5_KEYS = _RESULT_V4_KEYS \| {"attempt_registry"}` | `test_s8b_floor_contract.py::test_result_v4_key_contract_is_mode_conditional_and_exact` | [実測] 成立。v5=v4∪field を直接比較 | [実測] なし |
| M12 | [s8b_floor_stats.py:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:801) `if reported_attempt_registry != independent_attempt_registry:` | `test_s8b_floor_stats.py::test_v5_rejects_reported_prefix_head_tamper` | [実測] 成立。pure verifier直接、headerとshapeは valid | [実測] なし |
| M13 | [s8b_floor_stats.py:1133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:1133) v5-only `if` | `...::test_live_v4_does_not_call_attempt_registry_inspector` | [実測] 不成立。proof validatorが inspector より先に遮る | [推測] validatorを通す局所 seam後に inspector tripwire |
| M14 | [s8b_floor_stats.py:1150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:1150) `expected_binding = ...S8BAttemptBinding(...)` | `...::test_live_v5_calls_inspector_and_compares_reported_to_independent_proof` | [実測] fake seam上の引数帰属は成立。ただし裁定必須の実台帳 node が欠落 | [推測] 同一root二世代 A/B の実台帳 nodeを追加 |
| M15 | [s8b_floor_contract.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_contract.py:88) `_RESULT_V4_KEYS = frozenset({...})` | `test_s8b_floor_contract.py::test_result_v4_key_contract_is_mode_conditional_and_exact` | [実測] 成立。pilot/official各v4集合で literal absence を直接assert | [実測] なし |
| M16 | [s8b_floor_stats.py:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:777) `reported_attempt_registry["freeze_sha256"] != artifact["freeze_sha256"]` | `...::test_v5_rejects_artifact_header_freeze_tamper` | [実測] 成立。artifact headerだけを変更し、proof/expectedは同一 | [実測] なし |
| M17 | [attempt_registry_core.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:310) `if registry_schema != ATTEMPT_REGISTRY_PREFIX_REGISTRY_SCHEMA:` | `...::test_attempt_registry_prefix_proof_rejects_wrong_registry_schema` | [実測] 成立 | [実測] なし |
| M18 | [s8b_attempt_registry.py:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:889) `root = admission.shared_admission_root(Path(repo_root))` | `test_s8b_attempt_registry.py::test_attempt_registry_prefix_inspection_is_read_only_by_construction` | [実測] 成立。実呼出しmoduleの provisioning、`_entry_paths`、exclusive lock、fsyncをtripwire化 | [実測] なし |

## 正例・read-only・所有範囲・波及

- [実測] N=1/3/4/5 は [test_s8b_attempt_registry.py:3191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:3191) で `_v2_registry_capability_case`、`_reserve_v2`、`_classify`、`begin_attempt_observation` を使用しており、stubや手書き行ではありません。
- [実測] valid append は [同:3244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:3244) で N=3 proof後に production classificationを追加しています。
- [実測] read-only tripwire の module属性は実際の呼出し経路と一致します。bytes/inode snapshot は [同:3541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:3541) で `root.rglob("*")` 下の全 regular fileを対象にしています。
- [実測] 現物差分は production 4/test 4の指定8 fileだけで、保存 patchとのSHA-256も一致しました。8 fileはAST parse済みです。
- [実測] 4 test fileの差分に既存行削除は0件です。不変 pinの既存assertionは変更されず、追加だけです。
- [実測] 所有外callerは `result_keys_for_mode` の既定 schemaがv4、live wrapperもv4でregistry分岐を通らないため、既存v4挙動は静的に不変です。共有fixture3箇所もすべて `RESULT_SCHEMA`、すなわちv4を生成します。
- [実測] `test_official_perf_surface_inventory_is_exact` は call名と個数だけをASTで数え、関数signatureを固定していません。そのため今回のkw-only `schema`追加では静的なinventory差分は生じません。
- [実測] 新規test file、docs、`acceptance_duration_ledger.json` の変更はありません。direct-import禁止meta-testはcampaignとadmissionだけを走査し、今回その2 fileにimport追加はありません。
- [推測] pytestと`test_check_docs`系は本レビューでは未実走なので、最終的な緑判定は親の実測が必要です。

## 段3レンズB 所見5〜9

| 所見 | 判定 | 根拠 |
|---|---|---|
| 5 consumer閉包 | [実測] **partial** | [実測] v4 defaultと所有8 fileは維持されたが、105/31/9/3/8件のfixture family回帰は未実走で、unit報告にも完全な別計上がない |
| 6 不変pin | [実測] **closed** | [実測] pinを含む4 test fileは既存行削除0件 |
| 7 `registry_schema` literal | [実測] **closed** | [実測] core validatorのexact literalとwrong-schema直接nodeが実在 |
| 8 N=1/3/4/5到達可能性 | [実測] **closed** | [実測] production adapter経路で4状態とvalid appendを構成 |
| 9 変異帰属修正 | [実測] **partial** | [実測] M1/M7/M12は反映。M10は再照準不全、M14はfakeのみで実台帳版欠落 |

## 総括

- [実測] blocker 1件、must-fix 4件、nit 1件。
- [実測] 単体で帰属成立は15/17変異です。M7は登録外です。
- [実測] 裁定の段6要件まで満たした完了数は、M14実台帳版を除いて14/17です。
- [実測] 不成立はM10とM13、M14はpartialです。
- [実測] production主要実装、N=1/3/4/5、valid append、read-only path、v4互換は静的に整合しています。
- [実測] pytestは実走していません。
- [推測] 判定は **NO-GO**。M10/M13再照準とM14実台帳test追加後に再レビューが必要です。