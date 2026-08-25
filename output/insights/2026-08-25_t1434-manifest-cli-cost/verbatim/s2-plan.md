## (a) の変更閉包

現物との差分として、`supervise_pair` は [tools/codex_reasoning_ab.py:7181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:7181) の現在の署名に `task_manifest` を持っていない。`_validate_schedule(schedule)` も [同:7227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:7227) で既定 manifest のまま呼ばれているため、ここは新規追加が必要である。

| file:line | 変更 |
|---|---|
| `tools/codex_reasoning_ab.py:493-550` | `_find_rollout` / `_verify_rollout_sha` に manifest 由来の expected SHA を明示的に渡せる契約を足す。外部経路では `SESSION_IDS` / `ROLLOUT_SHA256` を参照しない。既定経路の互換引数は残す。 |
| `tools/codex_reasoning_ab.py:820-893` | `derive_independent_golden(..., task_manifest=TASK_MANIFEST)` と `_snapshot_spec(..., task_manifest=TASK_MANIFEST)` を追加。auxiliary session と task row を渡された manifest から引く。 |
| `tools/codex_reasoning_ab.py:2551-2630` 直後 | 外部 manifest loader を追加する。 |
| `tools/codex_reasoning_ab.py:2927-3054` | `_prepare_snapshot_case`、`_finish_snapshot_case`、`_derive_snapshot_from_base`、`build_snapshot` に `task_manifest` を通す。`_finish_snapshot_case` からの `verify_snapshot` にも渡す。 |
| `tools/codex_reasoning_ab.py:3093-3102` | `verify_snapshot(..., task_manifest=TASK_MANIFEST)` を追加し、`spec` 未指定時の `_snapshot_spec` に渡す。明示 `spec` の既存挙動は維持。 |
| `tools/codex_reasoning_ab.py:3297-3317` | `render_prompt(..., task_manifest=TASK_MANIFEST)` を追加。task provenance、session ID、rollout SHA を外部 manifest から取る。 |
| `tools/codex_reasoning_ab.py:6926-6973, 7132` | `_supervise_one(..., task_manifest=TASK_MANIFEST)` を追加し、前後の `verify_snapshot` に渡す。 |
| `tools/codex_reasoning_ab.py:7181-7237, 7309-7323` | `supervise_pair(..., task_manifest=TASK_MANIFEST)` を新設し、schedule 検証、oracle probe、各 `_supervise_one` に同じ object を渡す。 |
| `tools/codex_reasoning_ab.py:10091-10104, 10345` | `_replay_manifest` は既に引数を持つ。schedule だけでなく replay 時の `verify_snapshot` にも渡し、外部 task と既定 snapshot spec の混線を閉じる。 |
| `tools/codex_reasoning_ab.py:11093-11255` | `_add_task_manifest_option()` を設け、対象 subparser に `--task-manifest PATH` を追加。`--case` の固定 `choices=("POS","NEG")` は外し、妥当性を resolver に一本化する。 |
| `tools/codex_reasoning_ab.py:11259-11420` | parse 後に manifest を一度だけ load。alias 解決より前に確定し、対象 verb、resolver、内部関数へ同じ object を渡す。 |

### CLI verb ごとの判断

| verb | 追加 | 理由 |
|---|---:|---|
| `build-snapshot` | 足す | task selector と snapshot/provenance を task manifest から引く。 |
| `verify-snapshot` | 足す | selector だけでなく既定 `_snapshot_spec` も同じ manifest に束縛する必要がある。 |
| `render-prompt` | 足す | task provenance、session、prompt pin が task-specific。 |
| `collect-run` | 足す | main 冒頭の alias 解決を外部 manifest で行う。resolver の canonical ID から同 manifest の `legacy_case` を取り、`collect_run(case=...)` へ渡す。 |
| `supervise-pair` | 足す | schedule と snapshot oracle の両方を同じ manifest で検査する。現物の関数引数も追加対象。 |
| `aggregate` | 足す | `_replay_manifest` と `_aggregate_verified` の task、finding、軸を決める。 |
| `verify` | 足す | `aggregate` と同じ certified replay 経路。 |
| `make-packets` | 足す | schedule cardinality と task alias を検査する。 |
| `append-verdicts` | 足す | mapping reveal 前に manifest-wide finding union を検査する。 |
| `freeze-verdicts` | 足す | freeze 前の verdict 再検査に同じ finding union が必要。 |
| `reveal-mapping` | 足す | frozen verdict の最終再検査に必要。 |
| `freeze-stage2-plan-replayer` | 足さない | task manifest/schedule/verdict consumer ではなく独立 contract 生成。 |
| `replay-stage2-plan` | 足さない | stage2 contract のみを authority とする。 |
| `freeze-stage5-author-replayer` | 足さない | stage5 contract 生成であり task catalog を読まない。 |
| `validate-stage5-author-application` | 足さない | stage5 contract/receipt validator。 |
| `validate-stage5-downstream-receipt` | 足さない | 同上。 |
| `score-run` | 足さない | task-neutral な単一 output scorer。 |

`_replay_manifest` は CLI verb ではないため option は持たせず、`verify` / `aggregate` から到達させる。

### Loader 契約

署名は一つに固定する。

```python
def _load_task_manifest(path: Path) -> dict[str, Any]:
```

受理形も一つだけとする。UTF-8 JSON の top-level object がそのまま task-manifest envelope である形だけを受理する。配列、`{"task_manifest": {...}}` の wrapper、JSONL は受理しない。

処理順は次のとおり。

1. `path.read_bytes()`。
2. `json.loads()`。
3. top-level が `dict` であることを確認。
4. 既存 `_validate_task_manifest(value)` に委譲。
5. 読取、decode、parse、top-level 型の失敗は `ValidationError(..., RC_ROUTING)`。envelope の理由と rc は既存 validator のものを保持する。

loader 自身は schema を重複実装しない。

| 拒否 | 同じ境界を通る正例 |
|---|---|
| path 不在、権限不足、読取失敗 | readable な通常ファイルに `_canonical_bytes(TASK_MANIFEST)` を保存 |
| UTF-8/JSON parse 失敗 | `{"schema_version":3,...}` の正しい JSON bytes |
| top-level が配列、文字列、null | top-level が直接 manifest object |
| envelope が `_validate_task_manifest` 不受理 | `_synthetic_task_manifest()` または `TASK_MANIFEST` |

未指定時は `TASK_MANIFEST` object を直接使い、loader を呼ばない。

### alias と module 定数

`main()` は現在 [tools/codex_reasoning_ab.py:11262-11272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:11262) で既定 manifest による解決を先行させている。変更後は以下の順にする。

1. `task_manifest = TASK_MANIFEST` または外部 loader の結果。
2. `resolve_benchmark_task_id(..., manifest=task_manifest)`。
3. `_manifest_task(..., manifest=task_manifest)` から canonical ID と `legacy_case` を得る。
4. その同一 manifest を snapshot/render/supervisor/replay/aggregate/verdict 経路へ渡す。

例えば外部 manifest で alias `POS` が canonical `alpha` を指す場合、既定 `POS` は候補集合へ混ぜない。外部 manifest 内で二つの task が同じ alias を持つ場合だけ、既存の ambiguous 拒否を発火させる。外部 held-out manifest は v3 schedule を使う。v2 で `LEGACY_EXPECTED_SCHEDULE` を返す [同:2869-2875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:2869) は T-181 legacy 互換として維持する。

指定された module 定数の consumer は次で尽きる。

| 定数 | consumer 数 | 現物 |
|---|---:|---|
| `_LEGACY_KNOWN_FINDINGS` | 1 | [同:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:260) で既定 `TASK_MANIFEST` を import 時に組み立てるだけ。外部 runtime consumer ではない。 |
| `EXPECTED_SCHEDULE` | 0 | [同:330-335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:330) の定義後に参照なし。live 経路は `expected_schedule_from_manifest`。 |
| `KNOWN_FINDINGS` | 0 | [同:336-340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:336) の定義後に参照なし。live 経路は `known_finding_ids_for_manifest`。 |

したがって、この3定数による誤った既定値 consumer は残っていない。ただし別の import 時 alias である `SESSION_IDS` は [同:501,829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:501)、`ROLLOUT_SHA256` は `:502,545` に実行時 consumer が残る。上記 `_find_rollout`、`_verify_rollout_sha`、`derive_independent_golden`、`render_prompt` の変更で、外部経路からこれらを除去する。

## (c) の変更閉包

| file:line | 変更 |
|---|---|
| `tools/codex_reasoning_ab.py:27-29` | `Decimal`、`InvalidOperation`、`ROUND_HALF_EVEN`、必要なら `localcontext` を import。float は使わない。 |
| `tools/codex_reasoning_ab.py:8709` 付近 | `_load_frozen_price_snapshot_for_cost() -> dict[str, Any]` を追加。既存 `_validate_frozen_price_snapshot_record` を変更せず prerequisite として呼び、その後に凍結 bytes を読み、validator の返す fresh tree を cost 層へ渡す。 |
| `tools/codex_reasoning_ab.py:9287` 直後 | cost の新関数と mapping operation interpreter を追加。version 束縛関数群とは別ブロックに置く。 |
| `tools/codex_reasoning_ab.py:9373` の前後 | attempt cost を軸別に集める `_aggregate_normalized_costs` を追加。 |
| `tools/codex_reasoning_ab.py:9482-9512` | `_aggregate_verified` で全 slot の price が凍結 version の場合だけ snapshot を load し、attempt cost を計算する。 |
| `tools/codex_reasoning_ab.py:9752-9790` | `resource_ledger` の各 bound attempt に新 key `normalized_cost` を追加。依頼文では `_replay_manifest` とされているが、現物で resources を作る関数は `_aggregate_verified`。 |
| `tools/codex_reasoning_ab.py:9867-9890` | bound 経路だけ top-level の新 key `normalized_cost_axis_ledger` を追加。既存 key は改名・削除しない。 |

新関数の署名は次で固定する。

```python
def _normalized_cost_for_attempt(
    attempt: Mapping[str, Any],
    *,
    requested_model: str,
    price_version: str,
    price_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
```

### mapping と計算契約

receipt field 対応は hard-code せず、validated snapshot の `sku_mapping[requested_model]["receipt_token_mapping"]` を読む。任意式を実行せず、次の operation だけを closed allowlist として実装する。

- `identity`
- `input_tokens-minus-cached_input_tokens`
- `None` かつ空 field list

これにより field/category の authority は snapshot に残り、operation の意味だけをコードが実装する。

出力例は次の形にする。

```json
{
  "status": "partial",
  "currency": "USD",
  "price_unit": "per-million-tokens",
  "price_version": "...",
  "accounted_amount": "0.00051000",
  "components": {
    "input": {
      "tokens": 75,
      "unit_price": "4",
      "amount": "0.00030000"
    },
    "cached_input": {
      "tokens": 25,
      "unit_price": "0.4",
      "amount": "0.00001000"
    },
    "output": {
      "tokens": 10,
      "unit_price": "20",
      "amount": "0.00020000"
    }
  },
  "unaccounted_token_categories": ["cache_write"],
  "reasoning_output_tokens_accounting": "included-in-output_tokens-not-added-separately",
  "rounding": {
    "decimal_places": 8,
    "mode": "ROUND_HALF_EVEN"
  }
}
```

`cache_write` は component を作らず、tokens も amount も `0` にしない。snapshot の unknown category として `unaccounted_token_categories` に残し、総額を完全な請求額とは表現しない。

`reasoning_output_tokens` は以下の二重 guard を置く。

- exact int で `0 <= reasoning_output_tokens <= output_tokens` を要求。
- mapping の `receipt_fields` に `reasoning_output_tokens` が現れないことを要求し、計算 component に加えない。

### Decimal と丸め

計算式は各 category について、

```text
Decimal(tokens) * Decimal(unit_price) / Decimal(1_000_000)
```

とする。8小数桁、`ROUND_HALF_EVEN` で固定する。現在の最小単価 `0.02 USD / 1M` は1 token 当たり `0.00000002 USD` であり、現在の凍結表の整数 token cost は8桁で正確に表現できる。component の未丸め和を最後に quantize し、JSON へは固定小数点の文字列だけを出す。

### fail-closed 条件

| 拒否条件 | 通る正例 |
|---|---|
| snapshot が validator 不受理、currency/unit/version が不一致 | 現在の凍結 snapshot と `FROZEN_PRICE_VERSION` |
| `price_version` が null、非文字列、snapshot version と不一致 | exact `FROZEN_PRICE_VERSION` |
| `requested_model` が空、非文字列、`sku_mapping` に無い | `gpt-5.6-sol` または `gpt-5.6-luna` |
| 4 token field の欠落、bool、非 int、負値 | `{input:100, cached:25, output:10, reasoning:4}` |
| `cached_input_tokens > input_tokens` | `25 <= 100` |
| `reasoning_output_tokens > output_tokens` | `4 <= 10` |
| mapping の operation/field list が未対応 | 現在の validated `receipt_token_mapping` |
| mapping が reasoning token を component に含める | 現在の mapping は output に `output_tokens` だけを使う |
| unknown category と計測不能 mapping が食い違う | 現在は双方とも `cache_write` |
| price が非 decimal、非 finite、0以下 | 現在の canonical decimal 文字列 |

helper を直接 null price で呼べば `RC_AGGREGATE` で拒否する。一方、統合層では `_validated_slots_price_version` が `None` を返す all-null schedule には helper 自体を呼ばない。これにより既存の all-null 受理集合は変えず、cost だけを生成しない。

軸集計は `_AXIS_FIELDS` と `arm` ごとに、次を持つ新規行を作る。

- `accounted_amount`: decimal string
- `attempt_count`
- `currency`
- `price_unit`
- `price_version`
- `unaccounted_token_categories`
- `coverage_status = "partial"`

retry、post-treatment、pair-invalidated も実際に token が観測されていれば resource 消費へ含める。bound attempt の token が欠ける場合は0を足さず、resource の `normalized_cost.status = "unavailable"` と failure reason を残して report 全体を invalid にする。

schedule descriptor 無し、v2 compatibility、または全 slot `price_version=null` の場合は、resource 行に `normalized_cost` を足さず、top-level の `normalized_cost_axis_ledger` も出さない。packet 経路の uncertified 性と `_certification_scope` は変更しない。

## 追加するテスト

追加先は [orchestrator/tests/test_codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/orchestrator/tests/test_codex_reasoning_ab.py)。

| 現在の挿入位置 | 正例 | 対になる負例 |
|---|---|---|
| `:6005-6023` fixture 直後 | valid object を `_load_task_manifest` が同値で返し、rc を変えない | unreadable、malformed JSON、top-level array、invalid envelope を各 `RC_ROUTING` で拒否 |
| `:8958-9021` | 外部 manifest の `POS -> alpha` alias を main が `alpha` として解決し、同じ manifest を verb へ渡す | 既定 manifest と混ぜる mutation、および外部 manifest 内の alias ambiguity を拒否 |
| `:8958-9021` | option 未指定と、`TASK_MANIFEST` を明示ファイル化した実行で verb が受け取る mapping と結果が等価 | explicit file を無視して既定 object を渡す mutation を検出 |
| `:8958-9021` | 11対象 verb の parser が `--task-manifest` を受理 | stage2/stage5/score の非対象 verb では option を unknown として拒否 |
| `:7921-7980` | external manifest の session ID/SHA が `derive_independent_golden` と `render_prompt` へ届く | `SESSION_IDS` / `ROLLOUT_SHA256` を poison しても外部経路がそれを読まないことを確認 |
| `:8260-8545` | external task manifest が supervisor、replay、verify、aggregate まで一貫して到達 | 途中一箇所を `TASK_MANIFEST` に戻す mutation で alias/task mismatch を発生させる |
| `:6102` 直後 | sol の `{100,25,10,4}` が `0.00051000`、reasoning を0から10へ変えても cost 不変 | reasoning 11、cached 101、各 token の負値・bool・文字列・欠落を個別に拒否 |
| `:6102` 直後 | luna/sol の既知 SKU が mapping-driven に計算される | unknown model、null/wrong price version を拒否 |
| `:6102` 直後 | output subtree 内の amount/unit price がすべて文字列で、float が無い | float amount を返す mutation を再帰型検査で検出 |
| `:6102` 直後 | `cache_write` が unaccounted list に残り、component に存在しない | `cache_write: 0` または総額への0加算を行う mutation を検出 |
| `:6102` 直後 | 8桁 formatter の通常値と half-even tie を確認 | half-up、切捨て、指数表記を検出 |
| `:11331` 前後 | bound schedule の resource 2行と model別 axis ledger に exact cost を出す | attempt token/model/version を壊すと report が invalid になり、0 cost を生成しない |
| `:11266-11329` | all-null v3 と既存 legacy aggregate は cost key を一切持たない | null price で cost helperを呼ぶ、または空/0 ledger を出す mutation を検出 |
| `:11472` 周辺 | retry・pair-invalidated の観測済み resource cost をすべて合算 | final attempt だけに落とす mutationを検出 |

## 壊れうる既存テスト

(a) の署名伝播で更新が必要になりうるもの:

- `test_derive_independent_golden_wires_pins`
- `test_render_prompt_wires_pin`
- `test_build_snapshot_public_path_delegates_in_order`
- `test_shared_base_copy_preserves_metadata_and_relocates_submodules`
- `test_supervisor_falls_back_to_default_model_without_requested_model`
- `test_supervisor_binds_requested_model_to_argv_receipt_and_identity`
- `test_cli_benchmark_task_id_is_parsed_and_resolved`
- `test_cli_case_and_benchmark_task_id_conflict_is_fail_closed`
- `test_replay_passes_schedule_requested_model_to_collect_run`
- `test_replay_forwards_only_successful_snapshot_evidence_to_adjudication`
- `test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run`
- `test_verify_replays_complete_fake_codex_experiment`

主因は monkeypatch の fake が新しい `task_manifest=` keyword を受け取らないこと、および main の resolver fake が manifest 引数を未検査なことである。

(c) の出力追加で監視すべきもの:

- `test_bound_price_reaches_supervisor_replay_verify_and_aggregate_consumers`
- `test_bound_price_aggregate_rejects_attempt_price_mismatch`
- `test_aggregate_verified_uses_oracle_kind_and_keeps_task_model_axes_separate`
- `test_zero_component_total_only_aggregate_counts_by_arm_and_case`
- `test_asymmetric_technical_pair_retry_marks_mate_and_keeps_resources`
- `test_m9_post_treatment_failure_remains_in_denominator`

all-null/legacy テストは cost key が追加されないことを新しい互換条件として明示する。静的検査のみであり、pytest を実行済み、または緑とは報告しない。

## 実装子 A / B の編集面分割

| 担当 | 専有する編集面 |
|---|---|
| A = (a) | `tools/codex_reasoning_ab.py:493-550, 820-893, 2551-2630直後, 2927-3307, 6926-7323, 10091-10345, 11093-11420` |
| B = (c) | `tools/codex_reasoning_ab.py:27-29, 8709付近, 9287-9512, 9752-9790, 9867-9890` |
| A のテスト | loader、alias、CLI dispatch、manifest propagation、rollout pin。主に tests `:6005`、`:7921-7980`、`:8958-9021`。 |
| B のテスト | cost unit、fail matrix、aggregate/legacy。主に tests `:6102-6480`、`:11266-11490`。 |

衝突面は次の2箇所である。

1. `test_bound_price_reaches_supervisor_replay_verify_and_aggregate_consumers` (`:8260-8545`): A は `verify_snapshot` fake の新 keyword 対応、B は cost assertion を加える。Aを先に適用し、Bがその変更を保持して追記する。
2. preregistration の §5.2 / §10 到達度記述: (a) と (c) の双方に触れるため、実装子へ分配せず親が統合後に一度だけ更新する。

`_replay_manifest` はA専有、`_aggregate_verified` はB専有とし、同時編集しない。`_synthetic_task_manifest` は共有 fixture として原則変更せず再利用する。

## 親の provisional 裁定 P1〜P4 への評価

- P1: 支持。`prereg-s5.md:16-55` は到達度表を実測事実として更新する方針を明記し、`prereg-s10.md:81-83` は cost が未実装だと明記している。実装と実測後は、この到達度だけを更新すべきである。estimand、margin、gate、oracle、task 除外規則は変更しない。§13 は登録世代 lock の未完了状態を「cost 実装」で完了扱いにしてはならない。
- P2: 条件付きで支持。`--task-manifest PATH` と既定 `TASK_MANIFEST` は妥当。ただし既存7 verbだけでは不十分で、selector を持つ `build-snapshot`、`verify-snapshot`、`render-prompt`、`collect-run` も同じ外部 manifest に束縛する必要がある。新しい生成器は不要。
- P3: 支持。version 束縛と cost 計算は別関数・別 failure reason にする。per-run resource と axis aggregate の双方に載せる。現物の resources 生成位置は `_aggregate_verified:9752-9790`。
- P4: 支持。通貨は凍結 snapshot の USD、値は decimal string。加えて `cache_write` 未計上を明示し、`accounted_amount` を実請求額や完全額と呼ばないことが必要。

## 総括

実装順は A、B、親統合が安全である。Aは単なる parser option 追加ではなく、alias 解決、snapshot provenance、supervisor/replay oracle まで同一 manifest を通す必要がある。指定された `EXPECTED_SCHEDULE`、`KNOWN_FINDINGS`、`_LEGACY_KNOWN_FINDINGS` 自体に外部 runtime consumer は残っていないが、`SESSION_IDS` / `ROLLOUT_SHA256` の既定値漏れは同時に閉じる。

Bは凍結 price version の束縛を変更せず、snapshot-driven mapping、`Decimal`、8桁 half-even、reasoning subset 検査、`cache_write` の明示的未計上を持つ独立集計層として追加する。legacy/all-null 経路には cost keyを生成せず、uncertified 性も変えない。