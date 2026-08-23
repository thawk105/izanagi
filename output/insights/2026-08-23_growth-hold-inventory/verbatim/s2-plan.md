# 段 2 plan — growth hold inventory

## 結論

暫定裁定は **再導入 11 件 / 削除 0 件 / hold 継続 5 件** とする。

ただし `test_verify_replays_complete_fake_codex_experiment` の hold 継続は、D451 上の防壁を既定の静的 node が十分に代替するかという段 4 の裁定を要する。代替しないなら、現編集面では D451 と全走 300 秒上限を同時に満たせない。

親の provisional 前提には次の修正が必要である。

- P1: 現環境では fixture 費は既定 4 node により支払われるが、14 node の body 費までゼロになるわけではない。特に 171.83 秒の replay body は hold で節約されている。
- P1: `_SNAPSHOT_CORPUS_REASON` は「node が fixture を読む」という構造の記述としては正しい。「hold により fixture 費が消える」という意味に一般化するのが誤り。
- P3: `pinned_label="POS"` は全 rollout 内容走査を除去するが、`sessions_root.rglob(...)` 自体は残る。D463 の構造判定では、厳密には引き続き output artifact corpus 比例である。
- P4: 各 body の一時 snapshot は固定大だが、node の呼出し閉包には module fixture の再帰的 session 探索が入る。body だけを見て node 全体を非比例とするのは D463 に反する。

## F(t) の共通定義

以下では次の略記を使う。

- `Sdir(t)`: `/home/SFC/tanab/.codex/sessions` の再帰探索で訪れる directory entry 集合。pinned 探索でも `Path.rglob` が残る。`tools/codex_reasoning_ab.py:444-484`。
- `Sall(t)`: unpinned `_find_rollout` が列挙し、session meta を読む全 `rollout-*.jsonl`。`tools/codex_reasoning_ab.py:483-492`。
- `Hfixed`: `BASE_COMMIT`、`INTEGRATED_COMMIT`、`ARTIFACT_COMMIT` とその固定祖先閉包、固定 `TRACKED_PATHS`、pin 済み rollout bytes。定数は `tools/codex_reasoning_ab.py:59-110`、snapshot 構築は同 `2550-2647`。
- `Tnode`: node が作る有限個の tmp snapshot、schedule、fake run artifact。入力数は test body により固定。

`benchmark_snapshots` は `Sdir(t) ∪ Hfixed ∪ Tfixture` を読む。fixture 定義は `orchestrator/tests/test_codex_reasoning_ab.py:506-555`。そのため fixture consumer 14 件は、body が固定大でも node 全体としては D463 の「比例」に入る。第 3 区分に該当する node はない。

## 16 node 裁定表

秒数はすべて親が 2026-08-23 に得た一回の opt-in 実走の call 値であり、恒久性能値ではない。

| node | 現 reason | F(t) | D463 | 秒 | 他の既定防壁、D451 | 裁定 | 根拠 |
|---|---|---|---|---:|---|---|---|
| `test_m3_focus_artifact_directions` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed ∪ Tnode` | 比例 | 18.32 | 無。同じ forbidden-focus mutation は当該 node `test_codex_reasoning_ab.py:2040-2056` のみ | **再導入** | M3 の POS/NEG focus 方向を失うため D451 が D335 に優先 |
| `test_verify_replays_complete_fake_codex_experiment` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed ∪` 固定 10 run の replay artifact | 比例 | 171.83 | 限定的に有。M5 の文字列防壁は `test_m5_generated_session_rows_require_set_equality`、同 `9138-9141`。完全 replay と tamper 実行 `6205-6237` の代替ではない | **hold 継続、段4裁定付き** | 単独再導入でも現基準線との和が 307.28 秒。削除は D335 と統合検出力のため不可 |
| `test_m3_ignored_extra_and_missing` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed ∪` 固定 4 snapshot copy | 比例 | 14.95 | 無。extra/missing 両方向は同 `2017-2037` のみ | **再導入** | synthetic symlink test の付随 extra reason `3763-3766` は missing 防壁を持たず代替にならない |
| `test_m3_snapshot_mode_change` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed ∪` 固定 2 snapshot copy | 比例 | 6.95 | 無。root tracked mode mutation は同 `1995-2004` のみ | **再導入** | submodule executable-bit tests は別防壁 |
| `test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed` | 比例 | 7.16 | 有。cache 除去防壁は `test_object_info_derived_caches_are_removed_for_root_and_submodule`、同 `1818-1849`。既定 fixture も clean snapshot を verify する | **hold 継続** | manifest の逐語 assertion は固有だが、commit-graph cache 除去という正しさ防壁は既定で残る |
| `test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed ∪` 固定 stale commit | 比例 | 7.49 | 無。`test_fsck_nonzero_reason...`、同 `1937-1952` は formatter 単体で end-to-end rejection ではない | **再導入** | stale graph の生成、manifest、`verify_snapshot` rejection の三層が固有 |
| `test_agent_sandbox_binds_exclude_attempt_receipt_directory` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed ∪` 固定 2 fake launch | 比例 | 29.39 | 無。既定 supervisor node は自己申告 `attempt_receipts_bound=False` を見るだけ、同 `6150-6177`。実 argv の bind set は held node `6181-6202` のみ | **再導入** | sandbox receipt と実 argv の独立照合を残す |
| `test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed ∪` 固定 2 generation | 比例 | 7.77 | 無。同 `7393-7492` の pair completion/retry 防壁のみ | **再導入** | prelaunch 例外後の ledger と次 generation 許可を同時に守る唯一の node |
| `test_m3_symbolic_head_is_required` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed ∪` 固定 1 snapshot copy | 比例 | 3.82 | 無。builder の positive assertion `1749-1751` は detached HEAD rejection を検査しない | **再導入** | verifier の fail-closed 防壁がゼロになる |
| `test_m1_snapshot_head_pin_is_independent` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed` | 比例 | 3.32 | 有。synthetic snapshot で実際の `HEAD mismatch` を検査する `test_verify_snapshot_submodule_preflight_skips_worktree_git_and_aggregates`、同 `4060-4095` | **hold 継続** | production fixture 固有の検出力は残るが、HEAD pin 防壁自体は既定で動く |
| `test_forbidden_commits_are_unreachable_in_both_cases` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed` | 比例 | 0.01 | 有。fixture 構築中の `verify_snapshot` は forbidden object を検査し、既定 `test_git_answer_object_reinjection_is_rejected`、同 `4859-4871` が rejection を動的検査 | **hold 継続** | 明示的な両 case assertion は固有だが forbidden-object 防壁はゼロにならない |
| `test_attempt_four_is_rejected_before_launch` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed ∪` 固定 schedule | 比例 | `<0.005` | 無。attempt 4 の prelaunch rejection は同 `7373-7390` のみ | **再導入** | 費用は無視でき、D451 の最後の防壁 |
| `test_pos_neg_submodule_initialization_state_mismatch_is_rejected` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed ∪` 固定 10 slot | 比例 | `<0.005` | 無。既定 legacy schedule node `4778-4787` は happy path のみ | **再導入** | cross-case mismatch rejection がゼロになる |
| `test_parent_numstat_controls_remain_pinned` | `_SNAPSHOT_CORPUS_REASON` | `Sdir(t) ∪ Hfixed` | 比例 | 6.91 | 有。fixture の `verify_snapshot` が全 numstat を照合し、POS literal は `test_task_manifest_binds_frozen_provenance_to_literal_values`、同 `1412-1433` にもある | **hold 継続** | 個別 POS/NEG oracle assertion は固有だが、pin 防壁は既定で残る |
| `test_m2_production_golden_requires_both_routes` | `_ROLLOUT_REASON` | `Sdir(t) ∪` 固定 3 rollout bytes `∪` 固定 2 commit の 2 path bytes | 比例 | 0.55 | 無。`test_derive_independent_golden_wires_pins`、同 `6037-6065` は `_find_rollout` monkeypatch 配線だけ | **再導入** | 実 route A/B 比較と pin bytes を同時に見る唯一の node |
| `test_prompt_replacement_count_zero_expected_and_excess` | `_ROLLOUT_REASON` | 現在 `Sall(t)`、pin 後 `Sdir(t) ∪` 固定 POS rollout bytes | 比例 | 250.68 | replacement-count 防壁は無。unpinned resolver 自体は synthetic 既定 node `4935-4951` 等が守る | **pin 後再導入** | production と同じ pin 経路へ寄せ、replacement 0/9/10 防壁を復帰。ただし D463 上の比例性は完全には消えない |

## hold 継続行の再評価条件

### dataclass field 追加案と両立性

正規化された field 案は次のとおり。

```python
measured_at: str | None = None
reevaluation_trigger: Literal[
    "default-barrier-missing",
    "suite-plus-node-at-most-budget",
] | None = None
reevaluation_budget_seconds: float | None = None
reevaluation_barrier_nodes: tuple[str, ...] = ()
```

しかし本 wave での採用は不可と判定する。

投影内で確認できる consumer は以下である。

- `_hold` の `GrowthTestHold(...)` 構築: `growth_test_holds.py:42-56`。必須 field 追加なら全 row が壊れる。default 付きなら Python 呼出しは維持できる。
- `_validate_hold_rows`: 同 `518-560`。新 field の組合せ検査が必要。
- `growth_test_hold_inventory`: 同 `697-710`。`asdict` により default 値を含めて全 row の JSON shape が変わる。
- inventory CLI: 同 `714-716`。上記 shape をそのまま外部出力する。
- hold enforcement: 同 `631-689`。mapping key しか使わないので field 追加の直接影響はない。
- test module の consumer: `test_codex_reasoning_ab.py:9157-9158`。enforcement 呼出しだけなので直接影響はない。
- `tools/codex_reasoning_ab.py` には registry/dataclass consumer はない。

一方、`conftest.py`、contract test、`tools/hold_inventory.py` は射影外かつ別 wave 編集面である。そこを変更せず、`schema: izanagi-growth-test-holds/v1` のまま `asdict` field を増やす安全性は証明できない。したがって dataclass は変えず、reason suffix を使う。

### reason 内 token

形式を次で固定する。

```text
[reeval:v1 {"measured_at":"2026-08-23", ...}]
```

5 行の具体条件は以下。

| hold node | token の主要 payload |
|---|---|
| `test_verify_replays_complete_fake_codex_experiment` | `{"measured_at":"2026-08-23","observed_call_seconds":171.83,"trigger":"suite-plus-node-at-most-budget","budget_seconds":300.0}` |
| `test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure` | `{"measured_at":"2026-08-23","observed_call_seconds":7.16,"trigger":"default-barrier-missing","barrier_nodes":["test_codex_reasoning_ab.py::test_object_info_derived_caches_are_removed_for_root_and_submodule"]}` |
| `test_m1_snapshot_head_pin_is_independent` | `{"measured_at":"2026-08-23","observed_call_seconds":3.32,"trigger":"default-barrier-missing","barrier_nodes":["test_codex_reasoning_ab.py::test_verify_snapshot_submodule_preflight_skips_worktree_git_and_aggregates"]}` |
| `test_forbidden_commits_are_unreachable_in_both_cases` | `{"measured_at":"2026-08-23","observed_call_seconds":0.01,"trigger":"default-barrier-missing","barrier_nodes":["test_codex_reasoning_ab.py::test_snapshot_submodule_object_store_is_recursive","test_codex_reasoning_ab.py::test_git_answer_object_reinjection_is_rejected"]}` |
| `test_parent_numstat_controls_remain_pinned` | `{"measured_at":"2026-08-23","observed_call_seconds":6.91,"trigger":"default-barrier-missing","barrier_nodes":["test_codex_reasoning_ab.py::test_task_manifest_binds_frozen_provenance_to_literal_values","test_codex_reasoning_ab.py::test_snapshot_submodule_object_store_is_recursive"]}` |

これらは自動解除条件ではない。`release_condition` は引き続き `explicit-user-command-only` であり、token は再裁定を起動する条件だけを表す。

`_validate_hold_rows` の `reason` 検査直後、現 `growth_test_holds.py:542-543` に次を追加する。

1. `" [reeval:v1 "` があれば suffix は一つだけ、末尾 `]` を必須とする。
2. suffix 本文を `json.loads` し、JSON object 以外を拒否する。
3. `measured_at` を ISO `YYYY-MM-DD`、`observed_call_seconds` を finite かつ非負として検査する。
4. `trigger` を上記 2 値へ閉じる。
5. `default-barrier-missing` なら非空 `barrier_nodes` を必須とし、各値を `_HOLD_KEY_RE` で検査する。
6. `suite-plus-node-at-most-budget` なら finite、正の `budget_seconds` を必須とする。
7. token が無い既存の本 wave 外 row はそのまま許す。

この validator 編集は親 brief の当初編集面より広い。段 4 で明示的に許可する必要がある。

## `_find_rollout` の比例源除去案

変更点は `orchestrator/tests/test_codex_reasoning_ab.py:6105-6107` のみ。

```python
source_rollout = TOOL._find_rollout(
    _HISTORICAL_SESSIONS,
    TOOL.SESSION_IDS["POS"],
    pinned_label="POS",
)
```

意味上の評価は次のとおり。

- 2026-08-23 の親 probe では pinned/unpinned とも同一 path を返した。現 corpus に限れば source bytes は同じ。
- pinned 経路は session identity と rollout SHA を確認してから返すため、source identity は強くなる。`tools/codex_reasoning_ab.py:450-481`。
- 一方、valid な named candidate があれば全 corpus duplicate 検査 `483-492` より前に return する。将来、別 filename に同じ session identity が複製された場合の検出力は unpinned より弱い。
- unpinned resolver の zero/duplicate semantics は既定 synthetic node `test_codex_reasoning_ab.py:4935-4951` などに残る。
- 失われるのは「実 5.13 GiB corpus に対する unpinned integration」の既定実行である。これは他にないが、それ自体が D335 の output-corpus 比例経路である。
- production の `render_prompt` は既に `pinned_label=legacy_case` を使う。`tools/codex_reasoning_ab.py:2900-2921`。したがって replacement-count test を production source-selection semantics に合わせる変更でもある。

ただし pinned でも再帰 `rglob` は残る。比例構造を完全に除く必要があるなら、既存の固定 `_REAL_ROLLOUT` `test_codex_reasoning_ab.py:87-91` を直接使い、`TOOL._verify_rollout_sha(source_rollout, "POS")` を呼ぶ方が D463 に忠実である。これは pinned 案とは別の段 4 択一とする。

## 全走予算

再導入 11 node のうち、prompt node を除く親実測 call 合計は次のとおり。

```text
18.32 + 14.95 + 6.95 + 7.49 + 29.39 + 7.77
+ 3.82 + <0.005 + <0.005 + 0.55
= 89.24 秒以上 89.25 秒未満
```

現基準線 135.45 秒との単純和は 224.69 秒以上 224.70 秒未満。fixture setup は基準線ですでに支払われているため再加算しない。

したがって post-edit prompt node の 3 parameter 合計が **75.30 秒以下**なら、単純加算上は 300 秒内に入る。pinned lookup 0.036 秒は lookup 一回だけの測定であり、post-edit node 全体の秒数ではない。親の再実走なしに予算適合を確定してはならない。

既定集合は **11 node / 15 pytest items** 増える。内訳は focus 3 items、prompt 3 items、その他 9 items。現 `347 passed / 20 skipped` を将来結果として流用してはならない。

`test_verify_replays_complete_fake_codex_experiment` は 171.83 秒なので、現基準線との和だけで 307.28 秒となる。最終的に再導入するには、他の再導入後の既定集合を基準として replay node を約 75 秒以下まで最適化するだけでも足りず、実際にはその時点の全走余白以下まで落とす必要がある。

## 実測の一般化監査

- `20 items PASS / 544.05 秒`、各 per-node 秒、135.45 秒基準線は一回の本 worktree 実測としてのみ記録する。
- cold 329.754 秒、warm 約 18.5 秒は page cache 状態を含む観測値であり、恒久的倍率ではない。
- `derive_independent_golden` 0.139 秒と pinned lookup 0.036 秒も、現 filesystem/cache/corpus shape の一点観測。固定時間とは書かない。
- `rglob("rollout-*.jsonl")` 0.040 秒でも、入力集合の構造は成長比例のままである。
- 「fixture は既定で必ず構築」は `_HISTORICAL_SESSIONS.is_dir()` が真で、既定 consumer が collection される環境に限定する。偽なら fixture は `test_codex_reasoning_ab.py:508-509` で skip される。
- 現環境で fixture を起動する既定 4 node は `2059`、`4778`、`4859`、`6150`。この4本が残る限り、14 hold は fixture の corpus 探索費を減らさない。ただし各 body 費は減らす。

## 段 5 実装子への編集面

編集する path と箇所:

1. `orchestrator/tests/growth_test_holds.py`
   - 現 `:59-65`: 共有 reason 2 定数を、hold 継続 5 行の事実に合う個別 reason/token へ置換する。
   - 現 `:115-131`: 再導入 11 行を削除し、5 行を残して reason を更新する。
   - 現 `:542-543` 直後: 段 4 が許可した場合だけ reeval token validator を追加する。
   - `RELEASE_EXPLICIT_USER_COMMAND_ONLY`、環境変数名、token、他 file の hold 行は変更しない。

2. `orchestrator/tests/test_codex_reasoning_ab.py`
   - 現 `:6105-6107`: `_find_rollout` 呼出しへ `pinned_label="POS"` を追加する。
   - 段 4 が直接固定 path 案を選んだ場合だけ、同じ箇所で `_REAL_ROLLOUT` と SHA 検証へ置換する。
   - 他の test body、fixture、tool production code は変更しない。

編集してはならない path:

- `orchestrator/tests/conftest.py`
- `orchestrator/tests/test_growth_test_holds_contract.py`
- `tools/hold_inventory.py`
- `tools/codex_reasoning_ab.py`
- 上記 2 編集対象以外の全 path

この段では書込みも pytest 実走もしていない。PASS として報告できるのは親から与えられた 2026-08-23 の過去実測だけであり、計画後の状態は未検証である。

## 総括

暫定裁定は **再導入 11 件 / 削除 0 件 / hold 継続 5 件**。再導入で既定集合は 11 node / 15 items 増える。非prompt追加費は親実測で 89.25 秒未満、post-edit prompt node に残る予算は約 75.30 秒である。

段 4 で決めるべき択一は次の 3 点。

1. `test_m5_generated_session_rows_require_set_equality` の静的防壁を D451 の代替と認め replay integration を hold するか。認めないなら別 wave で replay の分割または最適化が必要。
2. prompt は production と同じ pinned 探索にするか、D463 を厳密に満たす固定 `_REAL_ROLLOUT` 直接参照にするか。
3. `_validate_hold_rows` の token validator 追加を本 wave の編集面拡張として許可するか。許可しない場合、token は JSON として機械可読だが registry import 時には検証されない。