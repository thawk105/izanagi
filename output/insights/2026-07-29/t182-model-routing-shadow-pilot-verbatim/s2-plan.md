結論は、**検証ツールと合成テストの実装は修正付き GO、親 brief の P1/P2 による実 shadow pilot は NO-GO** です。段1実測では「軽量 model」が成立せず、`mini@xhigh` は model と reasoning の二軸変更、`luna@max` は sol より軽量ではありません。以下は read-only 静的調査だけに基づく計画で、テストは実走していません。必読物はすべて読め、worktree は clean でした。

## 1. `tools/codex_model_shadow.py` の CLI と構成

`tools/codex_model_shadow.py`（新規、予定行）は次の区画にします。

- `:1-28` — read-only、stdout-only、live inference 非呼出しを明記する docstring、schema/rc 定数。
- `:29-62` — sibling tool を bytecode 無生成で読む `_load_sibling_tool()`。
- `:63-91` — `_parser()`。
- `:92-170` — regular-file・相対 path・JSON exact-schema 検証。
- `:171-235` — full `session_id` による rollout index と台帳 adapter。
- `:236-282` — artifact validator、rollout 最終 message 束縛、finding marker 抽出。
- `:283-325` — finding 採点。
- `:326-420` — arm ごとの gate と receipt 組立て。
- `:421-470` — arm 横断 gate、identity limitation、wall-clock 解釈。
- `:471-510` — canonical JSON 出力と `main()`。

CLI は以下だけに限定します。

```text
codex_model_shadow.py --manifest PATH [--sessions-root PATH]
```

- `--manifest`: 必須。arm manifest。
- `--sessions-root`: 任意。既定は台帳と同じ `$CODEX_HOME/sessions`、未設定なら `~/.codex/sessions`。
- 出力は常に canonical JSON 1 object を stdout。
- `--output`、`--cwd-contains`、`--strict`、model 起動 option は設けない。
- production authoritative request は T-182 固有不変条件としてコード内で `gpt-5.6-sol` / `max` に固定し、CLI override を与えない。override は brief (d) を迂回できるためです。

rc は次の意味に固定します。

- `0`: 全 arm と採点が有効。`valid:true` receipt を stdout。
- `1`: manifest は解釈できたが、run 証拠が gate 不合格。`valid:false` receipt を stdout。
- `2`: CLI、JSON schema、型、path、入力読取の構成エラー。採点を作らず stderr。
- それ以外の rc は定義しない。予期しない例外も安定した rc=2 に畳む。

`tools/codex_worker_ledger.py:118-144,696-816` で import 可能な公開関数は実質 `main(argv)` だけです。しかし session-id selector がなく、`--cwd-contains` しかないため T-182 の同定には使えません。必要な parser はすべて private です。

- `_stream_rollout`: `tools/codex_worker_ledger.py:227-343`
- `_classify_outcome`: `:377-384`
- `_normalized_prompt_hash`: `:399-401`
- default root: `:111-115`

したがって推奨は、これらを qualified private import する薄い adapter を新規 tool 内の一箇所へ閉じ込め、合成契約テストで破損を検出する案です。token/hash 算出を複製しません。`_assign_retries()` は arm を retry と誤分類するため使いません。

`check_codex_output.py` は公開 `main()` (`tools/check_codex_output.py:142-152`) を in-process で呼び、stdout/stderr をメモリへ退避して実 rc を取得します。新 tool 自身は `subprocess`、`codex exec`、書込 mode、`Path.write_*` を一切持ちません。

## 2. arm manifest の exact schema

`tools/codex_model_shadow.py` 新規 `:92-170` で、未知 field を含めて exact-schema 検証します。任意 field はありません。

```json
{
  "schema_version": "codex-model-shadow-arm-manifest/v1",
  "pilot_id": "t182-stage3-consult-b",
  "frozen_prompt": {
    "file_path": "prompt.txt",
    "file_sha256": "<64 lowercase hex>"
  },
  "adjudication_labels": {
    "file_path": "adjudication-labels.json",
    "file_sha256": "<64 lowercase hex>"
  },
  "arms": [
    {
      "arm_id": "authoritative-sol-max",
      "authority": "authoritative",
      "requested_model": "gpt-5.6-sol",
      "requested_reasoning": "max",
      "session_id": "<canonical lowercase UUID>",
      "artifact_md_path": "authoritative-sol-max.md",
      "codex_cli_exit_code": 0,
      "wall_clock_ms": 49000,
      "concurrent_codex_process_count": 28
    }
  ]
}
```

型と制約は以下です。

- `schema_version`: 上記 literal。
- `pilot_id`, `arm_id`: 非空 ASCII identifier、arm 内で一意。
- `file_path`, `artifact_md_path`: manifest directory 基準の相対 path。absolute、`..`、symlink、non-regular file は拒否。
- `file_sha256`: raw file bytes の SHA-256。lowercase 64 hex。
- `authority`: `"authoritative"` または `"shadow"`。
- `requested_model`, `requested_reasoning`: 親が CLI に要求した値。非空文字列。
- `session_id`: full canonical UUID。短縮不可、arm 間で一意。
- `codex_cli_exit_code`: JSON integer、bool 不可。
- `wall_clock_ms`: 正整数。arm ごとの親 runner 観測値。
- `concurrent_codex_process_count`: 1 以上の整数。arm ごとの計測時タグ。
- `arms`: 2 件以上。authoritative ちょうど1件、shadow 1件以上。

入力 manifest には `model`、`reasoning`、`recorded_*` を置きません。rollout 由来値を親が転記すると二重正本になるためです。receipt だけに以下の明示名で派生させます。

- `requested_model`
- `requested_reasoning`
- `rollout_recorded_model`
- `rollout_recorded_reasoning`

この区別は `DW-O13` (`docs/dev-wave/operations.md:70-72`) と、台帳の実キー `model` / `reasoning` (`tools/codex_worker_ledger.py:271-280,580-608`) の二義化を避けます。

prompt には次の2行を各1回だけ含めます。

```text
T182_PILOT_ID: t182-stage3-consult-b
T182_ADJUDICATION_FILE_SHA256: <labels file sha256>
```

これにより、run 後に labels と prompt を同時に差し替えても rollout の prompt hash と一致しません。raw prompt bytes の hash と、台帳定義の whitespace-normalized hash は別 field として receipt に残します。

## 3. fail-closed 条件と実成果物 field

`probe-receipts.json` は1行JSONなので参照は `/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/probe-receipts.json:1` です。

| brief 条件 | 読む実 field | 判定 | 外側 rc |
|---|---|---|---:|
| (a) 同一 prompt | `sessions[].prompt_hash` | 全 arm で単一値、かつ frozen prompt を台帳定義で hash した値と一致。raw `file_sha256` と labels hash marker も一致 | 1 |
| (b) request/recorded 一致 | manifest `requested_model` / `requested_reasoning` 対 `sessions[].model` / `sessions[].reasoning` | 逐 arm 完全一致。`sessions[].turn_contexts >= 1`、selected rollout に `inconsistent_turn_context` issue がない | 1 |
| (c) 実行・成果物成立 | manifest `codex_cli_exit_code`; `sessions[].model_calls`, `cli_reported`, `outcome`; artifact md | exit=0、`model_calls>0`、`cli_reported>0`、`outcome=="completed"`、artifact checker rc=0、artifact 本文が rollout 最終 `agent_message` と一致 | 1 |
| (d) authoritative | manifest `arms[].authority`, `requested_*`; rollout `sessions[].model/reasoning` | authoritative ちょうど1、request=`gpt-5.6-sol/max`、(b) も成立 | 1 |
| (e) 交絡タグ | manifest `wall_clock_ms`, `concurrent_codex_process_count` | 欠損・型違反・0以下を schema error。count>1 は run 全体を落とさず wall-clock を比較不能にする | 2 |

特に (c) は、実在した fail-open を三重に殺します。

- nano `019fadd3-c15a-79e1-8783-f083061d4e3d`
- codex-mini `019fadd3-c19c-7a12-bbf0-ded998aed815`

両者は `sessions[].model_calls=0`、`sessions[].cli_reported=0`、`sessions[].outcome="fragment"` です。成果物が仮に500 bytes以上あっても前二条件で拒否します。親 brief の実測は `s1-brief.md:34-39`、TSV は `probe-receipts.tsv:2,5` です。

注意点として `sessions[].exit_code` は全件 `"unknown"` であり、process rc の証拠には使えません。台帳自身も rollout に exit code がないと記録しています (`output/insights/2026-07-29_t179-worker-ledger-verbatim/adjudication.md:14-16`)。したがって receipt では `manifest_recorded_codex_cli_exit_code` と名乗り、rollout 観測と偽りません。T-180 launcher receipt が land した後は、その receipt 参照へ差し替えるのが正道です。

## 4. session 同定

`tools/codex_model_shadow.py` 新規 `:171-235` は次の順で同定します。

1. manifest の full canonical `session_id` を allowlist とする。
2. `sessions_root/**/rollout-*.jsonl` を決定順で走査し、ledger `_stream_rollout()` で `session_meta.payload.session_id` を読む。
3. filename は候補診断にだけ使い、authority にしない。
4. 各要求 ID がちょうど1 file、meta ちょうど1行、meta ID 完全一致でなければ rc=1。
5. 同一 ID が複数 file、複数 arm が同一 ID、selected file の malformed JSON/usage/meta は rc=1。
6. 同定後に prompt hash、model/reasoning、artifact final-message を結合検査する。
7. receipt の path は `rollout_path_relative_to_sessions_root` とし、絶対 path を出さない。

`--cwd-contains` は CLI に存在させません。台帳の現行 filter は substring OR (`tools/codex_worker_ledger.py:727-752`) で、path 再利用・接尾辞衝突の限界は `docs/worklog.md:1894-1897` と `phase3.md:525-533` に確定済みです。cwd は診断値として出しても selector にはしません。

## 5. finding coverage / 誤検出

自由記述を run 後の親が fuzzy match する方式は採用しません。それでは arm を見た後に label や alias を緩められます。

labels file は `tools/codex_model_shadow.py` 新規 `:130-170` で次の exact schema にします。未知 field、weight、ignore、arm-specific label、alias は拒否します。

```json
{
  "schema_version": "codex-model-shadow-adjudication/v1",
  "pilot_id": "t182-stage3-consult-b",
  "findings": [
    {
      "finding_id": "F001",
      "adjudication": "real",
      "description": "事前登録した finding の定義",
      "basis": "親が凍結した裁定根拠"
    },
    {
      "finding_id": "N001",
      "adjudication": "refuted",
      "description": "誤検出 control の定義",
      "basis": "親が凍結した反証根拠"
    }
  ]
}
```

- 全 field 必須。
- `findings` は `finding_id` 順、ID 一意。
- `real` と `refuted` を各1件以上必須。
- labels file hash は全 arm の rollout prompt に埋め込む。
- labels file には arm ID を置けないため、arm ごとの恣意的裁定は不可能。

各成果物は fence 外に正確に1行、次の宣言を持ちます。

```text
<!-- codex-model-shadow-findings-v1: ["F001","N001"] -->
```

ID はソート済み・重複なし。欠損、複数 block、malformed JSON、未知 ID、重複 ID は「品質低下」ではなく無効 run、rc=1です。明示的な空配列 `[]` は曖昧ではないため有効で、coverage 0 とします。

採点は整数分数だけを出します。

- `TP = reported ∩ real`
- `FN = real - reported`
- `FP = reported ∩ refuted`
- `TN = refuted - reported`
- coverage = `{numerator: TP, denominator: TP+FN}`
- false-positive rate = `{numerator: FP, denominator: FP+TN}`

float、rounding、重み、閾値、文字列類似度は使いません。

これは閉集合 qualification です。未知の新規 finding を「誤検出」と断定するのも、run 後に real と追認するのも避け、未知 ID は採点不能として run を無効化します。したがって open-ended reviewer 能力の完全評価とは名乗れません。`check_codex_output.py` 自身も意味整合を scope 外と明記しています (`tools/check_codex_output.py:118-123`)。

## 6. receipt の正直さ

`tools/codex_model_shadow.py` 新規 `:326-470` の receipt では、generic な `model_identity` という名前を使いません。

各 arm に最低限、以下を出します。

```json
{
  "requested_model": "gpt-5.6-sol",
  "rollout_recorded_model": "gpt-5.6-sol",
  "requested_model_matches_rollout_recorded": true,
  "served_model_attested": false,

  "requested_reasoning": "max",
  "rollout_recorded_reasoning": "max",
  "requested_reasoning_matches_rollout_recorded": true,
  "reasoning_value_supported_attested": false
}
```

top-level に固定の limitation code を出します。

- `model-request-echo-not-served-attestation`
- `reasoning-request-echo-not-capability-attestation`

説明文も receipt に含めます。

- rollout-recorded model は requested slug の記録であり、served backend identity の attest ではない。
- rollout-recorded reasoning は要求値の記録であり、その値が model により実際に支持・適用された attest ではない。

これにより、mini の400応答が `gpt-5.4-mini-codex-1p-codexswic-ev3` を露出した一方、receipt の実キー `model` は `gpt-5.4-mini` だった限界 (`s1-brief.md:55-58`) を誤読できません。また `ultra` が sol/luna/terra で rc=0かつ `sessions[].reasoning=="ultra"` でも、`reasoning_value_supported_attested` は常に false です。

比較部分は次も固定します。

- `scope: "observational-shadow-only"`
- `policy_change_authorized: false`
- `replicates_per_arm: 1`
- `policy_inference_allowed: false`
- `changed_request_axes_from_authoritative`
- `wall_clock_status: "confounded"` if any concurrency count >1
- wall-clock winner、順位、比率は出さない

`mini@xhigh` は `changed_request_axes=["requested_model","requested_reasoning"]`、`luna@max` は `["requested_model"]` です。前者を model 効果として集計しません。

## 7. テスト一覧

`orchestrator/tests/test_codex_model_shadow.py`（新規）の予定構成です。

- `:1-45` — importlib による tool 読込。
- `:46-145` — `_write_rollout()`, `_valid_artifact()`, `_make_case()`。
- `:146-190` — fixed labels → hash marker付き prompt → relative manifest の生成。
- `:191-430` —以下の tests。

| nodeid 案 | 殺す欠陥 |
|---|---|
| `test_valid_shadow_manifest_emits_deterministic_receipt_and_rc0` | 正例の過剰拒否、非決定的 JSON |
| `test_tool_is_read_only_and_never_launches_codex` | 入力更新、subprocess/live inference の混入 |
| `test_prompt_file_and_rollout_hashes_must_all_match_a` | (a) を singletonだけで済ませ frozen prompt と結ばない実装 |
| `test_requested_model_and_reasoning_must_match_rollout_b` | request/recorded の混同 |
| `test_inconsistent_turn_context_is_invalid_b` | 最初の model/reasoning だけを黙って採る実装 |
| `test_zero_model_calls_and_cli_reported_are_invalid_c` | nano/codex-mini の実在 fail-open |
| `test_nonzero_cli_exit_noncompleted_or_validator_reject_is_invalid_c` | rc、終了、成果物 gate のどれかを省略 |
| `test_artifact_must_match_rollout_final_agent_message` | 別 session の md を結合する誤帰属 |
| `test_authoritative_count_and_request_are_fixed_d` | authoritative 0/2件、shadow の昇格 |
| `test_concurrency_and_wall_clock_fields_are_required_e` | 交絡タグ欠損の受理 |
| `test_confounded_wall_clock_is_not_ranked` | count=28 を比較可能な速度値にする誤表現 |
| `test_full_session_id_selects_exactly_one_rollout` | 短縮 ID、substring/cwd selector |
| `test_duplicate_or_missing_session_id_is_invalid` | 0件・複数 file の fail-open |
| `test_cwd_suffix_collision_cannot_change_selection` | `--cwd-contains` の再導入 |
| `test_labels_hash_must_be_embedded_in_every_rollout_prompt` | run 後の labels 差替え |
| `test_unknown_duplicate_or_multiple_finding_declaration_is_invalid` | fuzzy/重複/複数 declaration の黙認 |
| `test_explicit_empty_findings_is_valid_zero_coverage` | 0 finding と採点不能の混同 |
| `test_scores_use_exact_integer_fractions` | float rounding、誤分母 |
| `test_label_schema_rejects_ignore_weight_alias_and_arm_fields` | run 後に denominator を緩める拡張 |
| `test_receipt_never_attests_served_model_or_reasoning_support` | request echo を identity attest と呼ぶ回帰 |
| `test_ultra_echo_remains_unattested_even_when_rc0` | `ultra` 成功を capability 証明とする回帰 |
| `test_ledger_private_adapter_contract_is_exercised` | T-180 merge 後の private helper drift |
| `test_import_does_not_create_bytecode_cache` | read-only import による `__pycache__` |
| `test_invalid_cli_and_schema_return_rc2` | rc 意味の drift |

fixture はすべて `tmp_path` 内で生成します。固定日時 `2026-01-01T00:00:00Z`、固定 UUID、`/synthetic/t182` cwd、relative manifest path を使い、現行 commit hash、repo 絶対 path、実行時刻は期待値に焼き込みません。既存の書き味は `test_codex_worker_ledger.py:53-204,207-212` に合わせますが、別 test module の private helper は import しません。

本 planner は read-only のため、これらの test は未実走です。緑とは報告しません。これは `DW-O05` (`docs/dev-wave/operations.md:30-33`) に従うものです。

## 8. 編集面の所有と並行 wave

実装子1の排他所有は次の2ファイルだけです。

- `tools/codex_model_shadow.py` — 新規
- `orchestrator/tests/test_codex_model_shadow.py` — 新規

fixture file は追加せず test 内生成にします。`tools/codex_worker_ledger.py` は import のみで、T-182 patch に1 byteも含めません。

親だけが成果物3を次の新規 directory に作ります。

- `output/insights/2026-07-29_t182-model-routing-shadow-pilot/`
  - `prompt.txt`
  - `adjudication-labels.json`
  - `arm-manifest.json`
  - arm別 `.md`
  - `receipt.json`
  - scope・交絡・identity限界を記した親 report

実装子はこれら、docs、commit、実走を所有しません。これは `DW-S05-A/B/C` (`docs/dev-wave/workers.md:19-43`) と整合します。

path 所有は T-180/T-181 と素集合ですが、意味上の重複があります。

- **T-180** (`docs/phase3.md:534-536`): `tools/codex_worker_launch.py` と ledger `--manifest` を所有。session allowlist、process rc、wall-clock、launcher receipt は本来こちらの責務です。T-182 は launcher/receipt producer を実装せず、親 manifest の consumer に限定します。T-180 land 後は private adapter 契約を再検証し、公開 selector が追加された場合だけ T-182 側を置換します。
- **T-181** (`docs/phase3.md:537-540`): reasoning A/B と receipt 抽出を所有。T-182 は generic reasoning comparator、escalation、capability allowlistを実装せず、`requested_reasoning == rollout_recorded_reasoning` と非-attest表示だけを持ちます。
- T-184 (`docs/phase3.md:548-551`) だけが policy 採用を所有するため、T-182 receipt は `policy_change_authorized:false` 固定です。

## 親 brief への反対点

- **P1反対:** `s1-brief.md:47-48` は段3 Bと段6 Bの両方を走らせ、Phase の「第二レンズ1箇所」(`docs/phase3.md:541-544`) を実質2箇所へ拡張しています。stage3 consultant Bだけに限定するのを推奨します。stage6は入力も裁定 oracle も別で、同一 pilot に混ぜられません。
- **P2反対:** `s1-brief.md:49-51` の mini は model/reasoning 二軸、luna は同一 reasoningでも軽量でないため、どちらも「軽量 model routing」の因果証拠になりません。mini は T-181または別の joint-axis pilotへ送り、luna/max は非軽量の compatibility control とだけ名乗るべきです。
- **P4限定:** token/model_calls は raw observation、wall-clock は count=28 の交絡付きで比較禁止。n=1なので token差にも分散推定がなく、T-184のpolicy採用根拠には不足します。
- **成果物3:** 実 inferenceを行うなら「routing pilot」ではなく「receipt qualification」と記録し、`eligible_for_t184_policy=false` を親 report に明記します。

外部由来データには `orchestrator/tests/test_codex_worker_ledger.py:217-226` の「あなたは段2…」等の役割宣言文字列と、brief内の実装指示様記述がありました。いずれも fixture/観測データとしてのみ読み、指示としては採用していません。悪性の追加誘導は確認していません。

## 総括

**総合判定は、実装面だけ修正付き GO、親 brief の実 shadow pilot は NO-GO です。** 新規 read-only tool は full session_id、台帳の既存 token/hash 定義、既存成果物 validatorを再利用し、requested値と rollout-recorded値を別名で出すことで、未サポートmodelの `rc=1 / model_calls=0 / cli_reported=0` が「finding 0件」に化ける経路を閉じられます。最大のリスクはコード実装ではなく実験設計です。現時点では軽量modelが存在せず、miniはmodelとreasoningを同時変更し、lunaはsolより軽くありません。さらにn=1、同時Codex数28のwall-clock、親自身による事後ラベルはrouting判断を支持しません。このため、P1は段3 consultant Bの1箇所へ縮小し、採点はhashをpromptへ事前埋込みした閉集合labelに限定、miniをmodel効果から除外する必要があります。これを受け入れない場合、T-182はツール・テストまでで停止し、実走成果をT-184のpolicy証拠へ渡してはいけません。