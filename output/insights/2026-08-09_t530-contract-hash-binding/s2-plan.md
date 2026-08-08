採る設計は P1〜P3 です。標準 `campaign.lock` の top-level 5 key は維持し、認証済み実行契約の hash を `search_config.environment_contract_sha256` に入れます。WAL 側は COMMIT payload の `contract_sha256` として記録し、両者を独立に読み出して照合します。

以下の行番号は現行ファイル基準です。read-only の静的調査のみで、テストは実走していません。

## 1. P1 — campaign identity の束縛点

正準形は次に固定します。

```json
{
  "spec_content": "...",
  "ccbench_commit": "...",
  "search_tag": "...",
  "search_config": {
    "...": "...",
    "build_admission": { "...": "..." },
    "environment_contract_sha256": "<64 lowercase hex>"
  },
  "trial": null
}
```

規則は以下です。

- identity field 名: `environment_contract_sha256`
- 値: [`ExecutionEnvironmentContract.contract_sha256`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/env_contract.py:156>) の scalar 文字列
- `env_tag` は別 field として入れない。ただし `contract_sha256` の原像には [`env_tag`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/env_contract.py:103>) が含まれるため、env は間接的に identity へ入る。
- date、receipt 発行時刻、PID、activation serial/state hash は入れない。
- [`GenerationEntry.generation`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/env_contract.py:169>) は入れない。これは明示的に T-627 へ残す。
- full contract object も格納しない。正本の canonicalization は `env_contract.py:151-166` のままとする。

既存 [`bind_admission_policy`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:31>) と同型の `bind_environment_contract(cfg, contract)` をその直後へ追加します。

共通点:

- exact `ExecutionEnvironmentContract` 型を要求
- 正本オブジェクトから canonical 値を導出
- 同じ値なら冪等
- 既存の異なる値を上書きせず拒否
- `dataclasses.replace` で immutable config を返す

差分:

- `build_admission` は policy preimage object、環境契約は 64 hex scalar
- caller 注入値ではなく、必ず [`require_certified_writer_authorization`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/execution_guard.py:107>) の戻り値から束縛する
- generation や authorization receipt の一時的属性は束縛しない

### D13 との衝突処理

これは [`D13`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/docs/decisions.md:180>) と互換だとは扱えません。contract hash は `env_tag`、clock、numactl、attestation、isolation、calibration reference を覆うため、「env を identity に含めない」を実質的に破ります。

したがって設計上は、確定済み T-530 裁定を D13 の狭い supersession と明記します。

- supersede する範囲: certified execution contract fingerprint
- 維持する D13: raw `env_tag` field、date/created-at、実測値を直接 identity に入れないこと
- [`D125`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/docs/decisions.md:6098>) の「OTHER の ID は変えない」も、この範囲では supersede される
- calibration の保存場所を env scope に置く D13 の二軸レイアウト自体は変更しない

`guided.py:127-137` の synthetic replay COMMIT は認証済み `pipeline.evaluate` の出力ではありません。ここへ現在の host contract を偽装して入れてはいけません。新 field の「必須」は certified campaign boundary に限定し、guided の raw historical lane は別扱いのままにします。

## 2. `campaign.lock` schema

標準 lock の top-level schema は変更しません。

[`verify_admission_preimage`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:47>) の exact set は引き続き以下の5個です。

```text
spec_content
ccbench_commit
search_tag
search_config
trial
```

変更するのは `search_config` 内の必須 entry だけです。これにより、親実測で top-level 追加時に落ちた27件を避けつつ、既存 canonical sorting [`ident.py:136-144`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:136>) にそのまま乗せられます。

既存32本は書き換えません。既存 lock に新 entry がないため、現在の contract を束縛した config とは canonical bytes が一致せず、新 ID から到達不能になります。

例外は S8b の private one-shot lock です。[`s8b_oracle_driver.py:979-1012`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8b_oracle_driver.py:979>) は標準 exact-5 lock ではなく独自3-key claim を書いています。directory-only 照合を成立させるには、ここだけ次の exact-4 にします。

```json
{
  "manifest_sha256": "...",
  "block_id": "...",
  "campaign_id": "...",
  "contract_sha256": "..."
}
```

これは標準32 campaign の schema には影響しません。既存 S8b lock は one-shot resume 拒否のままで、bytes は変更しません。

## 3. file:line 単位の実装計画

| 箇所 | 変更 |
|---|---|
| [`model.py:25`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/model.py:25>) | `ENVIRONMENT_CONTRACT_SEARCH_KEY = "environment_contract_sha256"` と `COMMIT_CONTRACT_SHA256_KEY = "contract_sha256"` を共有定数化。`wal -> ident` の循環を避ける。 |
| [`model.py:62-75`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/model.py:62>) | D13 の狭い supersession を docstring に反映。`search_config` は既に object 値を持つため型を `Dict[str, Any]` 相当に修正。 |
| [`ident.py:2-10`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:2>) | 「env を含めない」という無条件記述を、raw env/date は除外するが certified contract fingerprint は含める記述へ更新。 |
| [`ident.py:31-44`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:31>) | 直後に `bind_environment_contract` を追加。異なる事前束縛値は拒否。 |
| [`ident.py:47-72`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:47>) | exact top-level 5 は維持。新たに `verify_environment_contract_preimage` を分離し、検索 key の存在・exact lowercase SHA-256・現在の guard-returned contract との一致を検査。 |
| [`ident.py:125-144`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:125>) | certified config では新 key を必須化。既存 key sort により canonical bytesへ包含。 |
| [`ident.py:167-182`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:167>) | lock と現在 config の比較前に、新 binding の形と contract 一致を検証。 |
| [`ident.py:185-257`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:185>) | certified `ensure_*` に actual contract を渡し、lock 作成・repair より前に config の hash と照合。 |
| [`loop.py:61-89`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/loop.py:61>) | `_authorize_measurement` を `(registered_contract, optional_receipt)` 返却に変更。 |
| [`loop.py:123-135`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/loop.py:123>) | 順序を admission bind → authorization → environment bind → `campaign_id` に固定。認証前に ID/layout を作らない。 |
| [`loop.py:147-149`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/loop.py:147>) | `ensure_resumable_wal` に同じ registered contract を渡す。 |
| [`pipeline.py:595-601`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/pipeline.py:595>) | guard の戻り値を `authorized_contract` として保持。引数の raw object から hash を取らない。 |
| [`wal.py:939-1057`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:939>) | `_validate_attempt_topology` に `campaign_lock` を渡し、COMMIT topology を状態へ射影する前に contract binding を検証。 |
| [`wal.py:1219-1351`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1219>) | recovery は既存 WAL の検証を append より前に実施。無束縛/mismatch COMMIT があれば repair record も書かない。 |
| [`wal.py:1356-1403`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1356>) | replay の state 構築前、および orphan repair 後の再読時に再検証。 |
| [`wal.py:1406-1427`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1406>) | `records_by_stage` にも検証を置き、`replay` を通らない選択 reader の迂回を閉じる。 |
| [`artifact_admission.py:637-659`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/artifact_admission.py:637>) | `_validate_attempt_topology` へ既読 lock を渡す。artifact admission も同じ照合を使用。 |
| [`s8b_oracle_driver.py:990-994`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8b_oracle_driver.py:990>) | private claim lock に plan の `contract_sha256` を追加。 |
| [`s8b_oracle_driver.py:1405`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8b_oracle_driver.py:1405>) | 新規 COMMIT を読む箇所でも private lock hash と照合する。 |

[`terminal_variants`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1430>) と [`EvalState`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/model.py:131>) は変更しません。検証失敗時は state 自体を返さないためです。

## 4. Scope 2 — COMMIT payload の4書込み口

payload field は `contract_sha256`、値は guard が返した registered contract の hash です。

| 現行位置 | 経路 | 変更 |
|---|---|---|
| [`pipeline.py:1026-1032`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/pipeline.py:1026>) | no-bench → `wal.log` | inline payload に追加 |
| [`pipeline.py:1034-1042`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/pipeline.py:1034>) | no-bench → `qualification_policy.event_sink.emit` | inline payload に追加 |
| [`pipeline.py:1073-1084`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/pipeline.py:1073>) | bench → `wal.log` | shared `commit_payload` に追加 |
| [`pipeline.py:1073-1087`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/pipeline.py:1073>) | bench → `event_sink.emit` | 同じ shared payload で伝播 |

qualification sink は [`artifacts.py:745-780`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/qualification/artifacts.py:745>) で payload を canonical JSON に包むため、sink 側での別フィールド生成は不要です。

COMMIT 以外の BUILD/VERIFY/BENCH/ABORT payload には追加しません。

## 5. Scope 3 — 非恒真な照合

[`wal.py:939`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:939>) の直前に、概念上次の関数を置きます。

```python
validate_commit_contract_bindings(
    records,
    *,
    campaign_lock,
    require_binding: bool,
)
```

標準 lock では期待値を `campaign_lock.search_config.environment_contract_sha256` から、各実値を `record.payload.contract_sha256` から別々に読みます。欠落、型不正、大文字、64 hex でない値、不一致をすべて `AttemptTopologyError` で拒否します。

この比較は恒真ではありません。例えば lock が `H_A` の directory に対して以下で発火します。

- 別 campaign の `H_B` 付き COMMIT 行だけを複写
- COMMIT payload を手編集して `H_B` に変更
- 旧 writer が書いた `contract_sha256` 欠落 COMMIT
- WAL 全体を別 directory へ移植し、lock は元のまま
- 同じ variant/attempt/receipt を保ったまま contract field だけ変更

これらは admission receipt と attempt topology が完全に正しくても、新比較だけで拒否できます。期待値を current writer object から再生成したり、payload 自身から期待値を作ったりしません。

`read_records` は引き続き framing/parser です。選択判断をする reader は `replay`、`records_by_stage`、artifact admission、S8b の post-write reader のいずれかを通すよう caller inventory test で固定します。

## 6. P2 — resume 受理集合

通常の `run_campaign` の経路は次になります。

1. [`loop.py:131`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/loop.py:131>) で authorization を検証
2. returned contract hash を config へ束縛
3. [`loop.py:135`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/loop.py:135>) で新 campaign ID を計算
4. 新 directory の identity lock を確立
5. [`wal.replay`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1356>) が lock hash と全 COMMIT hash を照合
6. 照合済み COMMIT だけが `EvalState.committed=True` になり terminal skip へ入る

既存の無束縛 COMMIT は次の扱いです。

- 通常起動: ID が変わるため既存32 directory へ到達せず、新 campaign として再評価
- 旧 directory を低水準 API で明示: identity mismatch、または WAL contract-binding error で拒否
- 同じ旧 directory 内で「無束縛なので非terminalとして再評価」はしない。汚染台帳への追記を避けるため、directory 全体を fail-closed にする
- WAL bytes や既存 lock は変更しない

受理集合は、post-policy resume について次の部分集合になります。

```text
旧: valid admission topology
新: valid admission topology
    AND lock has H
    AND every COMMIT has exact H
```

したがって拡大はありません。

一方、明示的に grandfather されている lockless pre-policy/parser-only fixture は `admission_policy=None` の legacy laneとして維持します。これを一律拒否すると、T-530 が承認していない受理縮小になります。正当な新 resume `lock=H_A, COMMIT=H_A` と、この legacy lane の双方を正例で固定します。

## 7. P3 — campaign ID 再計算 consumer の全列挙

以下は production の直接 `ident.campaign_id` callerです。`ident.py` 自身とテスト内呼出しは除いています。

| consumer | 現行行 |
|---|---|
| campaign loop | [`loop.py:135`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/loop.py:135>) |
| screening | [`screening_driver.py:109`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/screening_driver.py:109>) |
| S1 direct comparison | [`s1_direct_comparison.py:244`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_direct_comparison.py:244>), [`:652`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_direct_comparison.py:652>) |
| P3 autonomous workload | [`p3_autonomous_workload_trial.py:631`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:631>) |
| P3 S4 red | [`p3_s4_red.py:170`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_s4_red.py:170>) |
| P3 kickoff | [`p3_kickoff.py:116`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_kickoff.py:116>) |
| P3 S4 loop | [`p3_s4_loop.py:870`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_s4_loop.py:870>), `872`, `997`, `1105`, `1135` |
| P3 S4 sort loop | [`p3_s4_loop_sort.py:231`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_s4_loop_sort.py:231>), `233`, `321`, `446`, `485` |
| P3 trigger gating | [`p3_s4_loop_trigger_gating.py:488`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:488>), `635`, `637`, `713` |
| backoff repro/sweep | [`backoff_repro.py:113`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/backoff_repro.py:113>), [`backoff_sweep.py:107`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/backoff_sweep.py:107>) |
| S6 sort sweep | [`s6_sort_sweep.py:240`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s6_sort_sweep.py:240>), `463` |
| S8a trigger sweep | [`s8a_trigger_sweep.py:341`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8a_trigger_sweep.py:341>), `568` |
| completeness check | [`autonomous_trial_completeness.py:1139`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/autonomous_trial_completeness.py:1139>) |

各 caller は layout 計算より前に、実行時なら guard-returned contract、manifest/planning 時なら明示された `contract_sha256` を config helper へ渡します。「current registry」を layout helper 内で暗黙 lookupすると、計画時と実走時で generation head が変わり得るため禁止します。

間接 consumer も次の影響を受けます。

- [`s1_report.py:339`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_report.py:339>): `layout_for` の新 IDへ追随
- [`artifact_admission.py:487-518`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/artifact_admission.py:487>): lock canonical bytesから directory suffixを再計算するため、新 lockなら自動的に新 ID
- [`s8b_oracle_manifest.py:659-675`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8b_oracle_manifest.py:659>): campaign ID が campaign-config preimage hashへ波及
- [`s8b_oracle_manifest.py:739-768`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8b_oracle_manifest.py:739>): future manifest IDも変化
- [`s8b_oracle_driver.py:1158-1171`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s8b_oracle_driver.py:1158>): manifest内の新 IDをlayoutに使用
- `trial_registry.py` と `p3_autonomous_workload_trial` の producer/manifest照合: old ID の registry entry は新 producer と一致しなくなる
- [`replay.py:89-112`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/replay.py:89>): ID再計算を避ける prefix discovery は維持。旧・新 directory が共存して曖昧なら既存どおり拒否し、old fallbackを追加しない

既存 directory は rename、copy、lock migrationをしません。新 consumer は新 rootを指すため、未完了だった旧 campaign も新規測定になります。既存 S8b manifestや凍結 artifact内の旧 IDも書き換えません。

## 8. テスト計画

主な nodeid 候補は以下です。

| nodeid | 落とす誤実装 |
|---|---|
| `test_campaign.py::test_environment_contract_binding_is_scalar_hash_only` | full contract、raw env_tag、generation、receipt属性をidentityへ混入 |
| `test_campaign.py::test_bind_environment_contract_rejects_conflicting_prebound_hash` | caller指定hashをguard結果で黙って上書き |
| `test_campaign.py::test_campaign_lock_contract_binding_stays_under_search_config` | top-level 6 key化、exact-5検査の破壊 |
| `test_campaign.py::test_run_campaign_binds_guard_contract_before_campaign_id` | authorization後ではなくdefault/current envでID計算 |
| `test_campaign.py::test_pipeline_no_bench_wal_commit_binds_authorized_contract` | no-bench WAL口の漏れ |
| `test_t126_qualification_driver.py::test_no_bench_qualification_commit_binds_authorized_contract` | no-bench event sink口の漏れ |
| `test_campaign.py::test_pipeline_bench_commit_binds_authorized_contract_on_both_sinks` | shared bench payloadまたは片方のsinkの漏れ |
| `test_campaign.py::test_contract_hash_is_commit_only` | scope外のBUILD/VERIFY/BENCH/ABORTへの拡張 |
| `test_campaign.py::test_commit_contract_validator_rejects_independent_hash_mismatch` | lockとWALを実際には比較しない恒真実装 |
| `test_campaign.py::test_replay_rejects_bound_lock_with_unbound_legacy_writer_commit` | field欠落をterminal扱い |
| `test_campaign.py::test_records_by_stage_rejects_commit_contract_mismatch` | `replay` だけ守り別readerから迂回 |
| `test_campaign.py::test_replay_accepts_matching_contract_bound_commit_and_skips_evaluation` | 正当なresumeまで拒否する承認外の受理縮小 |
| `test_campaign.py::test_lockless_prepolicy_replay_remains_legacy_accepted` | pre-policy legacy laneまで一律拒否 |
| `test_s8b_oracle_driver.py::test_private_campaign_lock_and_commit_bind_same_contract_hash` | private lockがdirectory-only照合不能 |
| `test_campaign.py::test_evaluate_commit_writes_are_syntactically_verify_gated` | 既存AST gateを拡張し、WAL 2口だけでなくevent sinkを含む4口を数える |

既存 literal pin 4件は緩和せず、T343値を履歴値として残して `_T530_*` を追加します。

- `test_campaign.py::test_campaign_id_binds_admission_policy`
- `test_campaign.py::test_screening_search_config_omits_none_and_binds_current_admission_policy`
- `test_campaign.py::test_screening_none_keeps_representative_legacy_campaign_ids_unchanged`
- `test_p3_autonomous_workload_trial.py::test_no_build_campaign_identity_binds_shared_policy_context`

`_PRE_T343_* → _T343_* → _T530_*` の三世代を literal で pin し、期待値を動的生成しません。

[`test_campaign.py:1-6`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:1>) は pytest 不在時も素の Python runnerで走るため、同ファイルの新テストは必須 fixture・parametrizeを使わず、既存 `_tmpdir` と `try/except` 形式に合わせます。

## 9. 変異事前登録候補

以下の `old` は実装後にこの綴りへ固定する前提です。同じ文字列が複数あるものは位置指定で変異します。

| 位置 | old → replacement | 期待赤 nodeid |
|---|---|---|
| `ident.bind_environment_contract` | `if existing is not None and existing != expected:` → `if False:` | `test_bind_environment_contract_rejects_conflicting_prebound_hash` |
| `loop.py` のID計算直前 | `cfg = ident.bind_environment_contract(cfg, authorized_contract)` → `cfg = cfg` | `test_run_campaign_binds_guard_contract_before_campaign_id` |
| no-bench WAL payload | `"contract_sha256": authorized_contract.contract_sha256,` → `"contract_sha256": "0" * 64,` | `test_pipeline_no_bench_wal_commit_binds_authorized_contract` |
| no-bench qualification payload | `"contract_sha256": authorized_contract.contract_sha256,` → `"contract_sha256": "0" * 64,` | `test_no_bench_qualification_commit_binds_authorized_contract` |
| WAL validator | `actual = record.payload.get(COMMIT_CONTRACT_SHA256_KEY)` → `actual = record.payload.get(COMMIT_CONTRACT_SHA256_KEY, expected)` | `test_replay_rejects_bound_lock_with_unbound_legacy_writer_commit` |
| WAL validator | `if actual != expected:` → `if actual != record.payload.get(COMMIT_CONTRACT_SHA256_KEY):` | `test_commit_contract_validator_rejects_independent_hash_mismatch` |
| WAL validator | `if actual != expected:` → `if actual == expected:` | `test_replay_accepts_matching_contract_bound_commit_and_skips_evaluation` |
| `records_by_stage` | `validate_commit_contract_bindings(records, campaign_lock=campaign_lock)` → `None` | `test_records_by_stage_rejects_commit_contract_mismatch` |

変異用 mismatch fixture は、lock=`H_A`、COMMIT=`H_B` とし、両方とも正しい64 lowercase hex、admission receipt、attempt ID、BUILD_DONE順序を正当にします。したがって比較を無効化した場合、前後の admission・format・topology 層には拒否理由が残りません。

matching正例は lock/COMMITとも `H_A`、missing正例は contract field以外を完全に正当化します。pipeline系変異は replayせず、発行されたrecord/eventを直接検査するため、下流validatorが同じ入力を先に拒否して赤理由を隠しません。

## 10. 危険箇所

- D13およびD125との衝突は文言修正だけで隠さず、T-530による狭い supersession として記録する必要がある。
- 4件のliteral pinは削除・動的化せず、T343履歴値を保存したままT530値を追加する。
- `ident.py` は既に `wal.py` をimportするため、`wal.py -> ident.py` を追加すると循環する。共有wire keyは`model.py`へ置く。
- `ExecutionEnvironmentContract` のgenerationを取り込むとT-627を先取りするため禁止。
- 23件の `FROZEN_MANIFEST` と既存lock/WAL bytesは更新・再生成・再承認しない。future artifactのみ新ID/hashになる。
- source-record hashが変更対象driverを覆っている可能性があるため、実装段では frozen artifact testを「期待hash更新なし」で確認する。
- `guided.py` のsynthetic COMMITへ現在の環境契約を偽装しない。certified readerとの境界を明文化する。
- `test_campaign.py` のdual runner契約を壊すpytest fixture依存を持ち込まない。
- 本回答ではテストを実走しておらず、親brief記載のbaseline以外を緑とは評価していない。

## 総括

- P1は標準lockの`search_config.environment_contract_sha256` scalar束縛を採る。
- hashはenv_tagを間接的に含むため、T-530をD13/D125の狭いsupersessionとして扱う。
- generation・date・receipt属性は含めず、T-627/T-658を先取りしない。
- 標準lockのtop-level exact 5は維持し、既存32 directoryは移行せず到達不能とする。
- COMMIT 4書込み口へ`contract_sha256`を追加し、lockとWALを独立に照合する。
- 無束縛・不一致COMMITはstate構築前に拒否し、正当な一致resumeは維持する。
- 残る主なriskはsynthetic guided lane、S8b private lock、frozen source-hash波及である。