## 結論

実装可能。ただし `whiteboard=[]` と `ReservationCell.reserved_bench_s` の出所は既存 schema だけでは決まらない。次の二案を推す。

- `whiteboard` は「任意の空配列も許す」のではなく、**初期状態では exact `list` の `[]` だけを受理し、従来 fixture の非空 sentinel は拒否**する。
- §5 の予算 JSON に six-cell の `reserved_bench_s` を明記させる。上限から分配値を推測しない。

禁止対象の `s8c_preregistration.py`、evidence evaluator、contract JSON、generation projection は編集不要である。

## 実装差分

[p3_autonomous_workload_trial.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:41)

- `from . import s8c_schedule` を追加する。C05 の到達性解析は import binding を実 module path まで解決するため、関数を動的取得せず `s8c_schedule.load_schedule` のように module attribute で呼ぶ。
- `s8c_budget` import に `BudgetError` を加え、§5 数値から `BudgetLimits` / `ReservationCell` を作る際の失敗を `AutonomousTrialError` へ理由別に包む。

[p3_autonomous_workload_trial.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:139)

次の局所定数を置く。

- schedule: `output/s8c-preregistration/schedule.v1.json`
- ledger directory: `output/s8c-preregistration/`
- budget field 名: `累積ベンチ実時間の総上限と arm ごと・holdout ごとの上限`
- seed field 名: `master_seed`
- budget JSON の exact key 集合:
  `total_bench_s / per_arm_bench_s / per_holdout_bench_s / reserved_bench_s`

ledger は全 six-cell run で共有し、別 manifest と衝突しないよう、`root / output/s8c-preregistration / ("budget-ledger." + manifest.sha256 + ".v1.json")` を推す。

[p3_autonomous_workload_trial.py:1856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:1856)

無条件 raise を次の構造へ置換する。

```python
def _load_s8c_schedule_authority(
    *,
    root: Path,
    manifest: trial_registry.TrialManifest,
    prereg_content_commit: str,
) -> Mapping[str, Any]:
    live_bytes = s8c_schedule.load_schedule(root / SCHEDULE_RELATIVE_PATH)
    committed_bytes = s8c_preregistration.read_blob_at(
        root, prereg_content_commit, SCHEDULE_RELATIVE_PATH.as_posix()
    )
    require(live_bytes == committed_bytes)

    master_seed, budget = _load_s8c_section5_values(
        root=root, commit=prereg_content_commit
    )
    authority = _build_s8c_schedule_authority(
        root=root, commit=prereg_content_commit
    )

    verified = s8c_schedule.verify_schedule(
        committed_bytes, master_seed=master_seed, authority=authority
    )
    consumed = tuple(
        s8c_schedule.consume_schedule(
            committed_bytes,
            master_seed=master_seed,
            authority=authority,
            schedule_index=index,
        )
        for index in range(6)
    )

    # consumed の (holdout, arm) を manifest.trials に一対一対応させる
    # cell_id は manifest の trial_id、予約値は §5 の six-cell matrix
    ...
    return {
        "ledger_path": ...,
        "schedule_sha256": hashlib.sha256(committed_bytes).hexdigest(),
        "cells": tuple(reservation_cells),
        "limits": BudgetLimits(...),
    }
```

重要点は次のとおり。

- `root` は捨てず、schedule の worktree path、commit blob 読取、role file、arm-input resolver、ledger path の全基準にする。
- commit は `manifest.prereg_commit` ではなく、[TrialBinding.prereg_content_commit:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/trial_registry.py:318) を使う。manifest、§5 値、schedule を同じ内容 commit `P` に置け、自己参照も生じない。
- `load_schedule` で読んだ checkout bytes と `read_blob_at(P, schedule path)` を一致させ、検証対象には committed bytes を渡す。
- `verify_schedule` の戻り値を直接 budget cell にしない。全 ordinal を `consume_schedule` に通した結果だけから `ReservationCell` を構築する。
- `cell_id` は文字列を新規合成せず `manifest.trials` の `trial_id` を使う。これは [_finish_trial:3531-3541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:3531) が settlement に同じ binding trial ID を渡すためである。
- `schedule_sha256` は artifact bytes から計算し、定数・fixture・§5 から取らない。

[p3_autonomous_workload_trial.py:1864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:1864)

`_prepare_s8c_budget_inputs` の既存検査は維持し、呼出しだけを次へ変える。

```python
schedule = _load_s8c_schedule_authority(
    root=ROOT,
    manifest=manifest,
    prereg_content_commit=admission.binding.prereg_content_commit,
)
```

loader と caller の責任分担は以下とする。

|loader が検査・構築するもの|既存 `_prepare_s8c_budget_inputs` に残すもの|
|---|---|
|committed/worktree schedule bytes 一致|`registered-effective` と binding の存在|
|§5 seed・budget の status/value|manifest の load と binding hash 一致|
|18-key production authority|ratified freeze document と 2 SHA|
|byte-exact regenerate、全 ordinal consume|返却 mapping の exact 4 key と型|
|schedule pair と manifest trial の一対一対応|schedule holdout と ratified holdout の一致|

これにより [p3_autonomous_workload_trial.py:1870-1935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:1870) の既存 defensive boundary と重複・矛盾しない。

## 18 key authority の組み方

authority はすべて plain JSON へ射影してから [validate_authority:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_schedule.py:210) に渡す。`MappingProxyType`、tuple、`Path` はそれぞれ dict、list、repo-relative POSIX path にする。

|key|production の出所と射影|
|---|---|
|`arms`|`s8c_arm_inputs.ARMS`、`trial_registry.ARMS`、`s8c_schedule.ARMS` の exact 一致を確認して list 化|
|`designated_source_context`|[DESIGNATED_SOURCE_CONTEXT:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:357) の全文|
|`descriptor_bindings`|[resolve_arm_input:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_arm_inputs.py:434) を H1/H2 × on/off/swapped に実行し、各 `descriptor` を nested mapping 化|
|`gating_spec`|[GATING_SPEC:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:322) の全文|
|`holdout_bindings`|[trial_registry.HOLDOUT_BINDINGS:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/trial_registry.py:81)|
|`holdouts`|`trial_registry.HOLDOUTS` と `s8c_schedule.HOLDOUTS` の一致後に list 化|
|`role_contracts`|[ROLE_CONTRACTS:271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:271) の全文|
|`role_files`|[ROLE_FILES:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:261) ごとに `{path, role_name, sha256}`。SHA は provider が実際に使う [role_file_sha256:644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:644) と同じ bytes から計算|
|`role_payload_allowlist`|[ROLE_PAYLOAD_KEY_SPEC:333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:333)|
|`workloads`|[FORMAL_WORKLOADS:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:242)。探索用 `WORKLOADS` は使わない|
|`attempt_policy`|[s8c_generation_projection.ATTEMPT_POLICY:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_generation_projection.py:28)|
|`baseline`|各 resolved descriptor について [_role_metric_payloads:1741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:1741) の第1要素を生成し、six-cell 全一致を確認した値|
|`descriptor_binding`|six-cell の `{selected_holdout, input_schema_version, content_digest_sha256, arm_binding_digest_sha256}` 完全表。単一 cell の record ではなく、全 cell が共有する extensional binding 規則|
|`gating_snapshot`|`snapshot_gating_spec(GATING_SPEC)` の `{text, sha256}`|
|`initial_role_metrics`|[_INITIAL_ROLE_METRICS:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:145)|
|`leakproof_context`|`{"text": LEAKPROOF_CONTEXT}`|
|`stop_policy`|[s8c_generation_projection.STOP_POLICY:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_generation_projection.py:32)|
|`whiteboard`|exact `[]`。[_whiteboard:1707-1709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:1707) と既存の fresh-state check [3810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:3810) が定める正式初期値|

`campaign_id` と `freeze_id` は authority に合成しない。manifest/ratified binding の既存検査に残す。

## P1-a / P1-b / P1-c の結論

**P1-a**

`{"text": LEAKPROOF_CONTEXT}` を採用する。文字列をそのまま唯一の field value として包む単射なので、文脈内容を追加・欠落させない。

**P1-b の択一**

|案|受理集合|保証の実効性|判断|
|---|---|---|---|
|空・非空の両方を許す top-level 例外|現 schema の真の上位集合になる|loader が常に `[]` を入れるだけなら恒真化しやすい|却下|
|非空 sentinel を入れる|schema は広がらない|production にない値を保証するため偽の proxy|却下|
|`whiteboard` を authority から外す|変更を digest しない方向へ拡大|共有初期状態の保証が消える|却下|
|18 key 全体を外部 caller に要求する|広がらない|厳密にはできるが production 正本が無く、D1448 の実解決にならない|予備案のみ|
|**exact empty list だけを許し、非空を拒否**|旧集合の単純な上位集合ではない。fixture 非空値を失効させる|fresh-state check と組み合わさり、正式初期状態そのものを拘束する|**推奨**|

[s8c_schedule.py:106-114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_schedule.py:106) と [validate_authority:235-249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_schedule.py:235) で、`key == "whiteboard"` のときだけ `type(value) is list and value == []` を要求し、`_validate_non_degenerate_value` を適用しない。他 key の非退化規則は一切緩めない。

**P1-c**

単一 cell の `descriptor_record` を選ばず、`resolve_arm_input` が six-cell について返す binding metadata の完全表を `descriptor_binding` とする。これは cell ごとの異なる値を隠さず、同じ完全な規則表を全 schedule cell の initial-state digest が共有する形である。

## §5 の機械 parse

[s8c_preregistration.py:771-832](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_preregistration.py:771) の `_parse_section5` を受理判定の唯一の入口にする。

`p3_autonomous_workload_trial.py:1856` 前へ `_load_s8c_section5_values` を置き、以下を行う。

1. `read_blob_at(root, prereg_content_commit, SOURCE_PATH)` で committed Markdown bytes を得る。
2. 既存 `_normalize_newlines`、`_fence_map`、`_section_bounds` で §5 slice を作る。
3. `_parse_section5(section_lines, section_fenced)` を呼ぶ。
4. `Section5Finding` を field 名で引き、[FieldStatus:138-142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_preregistration.py:138) を identity 比較する。
5. `FILLED` の2値だけを、既存 `split_markdown_table_row` と [_parse_filled_section5_value:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_preregistration.py:867) で decode する。独自 JSON/code-span parser は書かない。

budget JSON は exact 4 key とする。

- `total_bench_s`
- `per_arm_bench_s`: exact `on/off/swapped`
- `per_holdout_bench_s`: exact `H1/H2`
- `reserved_bench_s`: exact `H1/H2 × on/off/swapped` の nested matrix

最初の3つは `BudgetLimits` へ渡す。最後は consumed schedule cell と manifest trial を結び `ReservationCell.reserved_bench_s` に渡す。未記入の上限から均等配分などを導出しない。

安定した失敗理由は次に分ける。

- `8c preregistration source is unavailable: <PreregistrationError.reason>`
- `8c preregistration section 5 is invalid: <reason>`
- `8c schedule budget field is absent`
- `8c schedule budget field is unfilled: <finding.reason_code>`
- `8c schedule budget field is invalid: <finding.reason_code>`
- `8c schedule master_seed field is absent`
- `8c schedule master_seed field is unfilled: <finding.reason_code>`
- `8c schedule master_seed field is invalid: <finding.reason_code>`
- `8c schedule master_seed value must be a string`
- `8c schedule budget value is not an object`
- `8c schedule budget keys are not exact`
- `8c schedule reserved cell coverage is incomplete`
- `8c schedule budget values are invalid: <BudgetError>`

既定値、環境変数 fallback、別 freeze の seed は設けない。

## schedule 読取・改竄検知の失敗理由

loader 内ではさらに以下を区別する。

- `8c schedule artifact could not be loaded from repository root`
- `8c schedule artifact is unavailable at preregistration content commit: <reason>`
- `8c schedule worktree bytes differ from preregistration content commit`
- `8c schedule production authority could not be constructed: <reason>`
- `8c schedule verification failed: <ScheduleError>`
- `8c schedule consumption failed: <ScheduleError>`
- `8c schedule cells do not match the trial manifest`

`verify_schedule` は [byte 再生成比較:498-529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_schedule.py:498)、`consume_schedule` は [532-555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_schedule.py:532) をそのまま使う。例外を握りつぶす受理経路は作らない。

## C05 到達性の確定

[_evaluate_c05:2083-2192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/s8c_preregistration_evidence.py:2083) は次を辿る。

- `run_trial` から `_ReachabilityExplorer.walk` を開始する。
- import binding と top-level function call を module 横断で解決する。
- `graph.calls` に次の exact target が全部必要:
  - `(orchestrator/campaign/s8c_schedule.py, load_schedule)`
  - 同 `verify_schedule`
  - 同 `consume_schedule`
- schedule module 内でも `verify_schedule -> verify_exact_schedule_bytes / verify_shared... / validate_authority`、`consume_schedule -> verify_schedule`、`verify_exact... -> regenerate` を `_live_called_names` で要求する。
- 全部通っても終端は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` であり、SATISFIED にはならない。

`run_trial` 側は既存の [budget enable gate:4576-4578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:4576) と [_prepare call:4709-4715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:4709) を維持する。経路は次になる。

`run_trial -> _prepare_s8c_budget_inputs -> _load_s8c_schedule_authority -> load_schedule / verify_schedule / consume_schedule`

メモリ上で実 evaluator と全 production AST を使って確認した結果は以下だった。

- 現行: `UNSATISFIED / schedule-consumer-unreachable`、schedule target は空集合。
- 上記の module import と3呼出しを加えた形: `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`、3 target 全部が `graph.calls` に入った。

evaluator/contract の変更は不要である。

## test 計画

[test_s8c_schedule.py:12-70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/tests/test_s8c_schedule.py:12)

- fixture の `whiteboard` を `[]` に変更。
- `whiteboard=[]` の受理と、非空 list・tuple・mapping の拒否を固定する。
- [各 authority field の digest test:199-211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/tests/test_s8c_schedule.py:199) は `whiteboard` 以外の17 keyを従来どおり mutation→digest 差にする。`whiteboard` は mutation→拒否を別 test にする。期待を弱めず、初期値を単一点へ強める。
- empty `arms`、empty nested authority、非 canonical bytes、seed mismatch の既存負例は変更しない。

[test_p3_autonomous_workload_trial.py:9024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/tests/test_p3_autonomous_workload_trial.py:9024)

ここへ production loader の test fixture と以下を追加する。

- `test_load_s8c_schedule_authority_resolves_committed_schedule_and_manifest_cells`
  - tmp Git repo に synthetic filled §5、role files、off authority、six-cell manifest、real `S.regenerate` bytes を commit。
  - real loader を呼び、返却 key が exact 4、SHA が artifact bytes、cell IDs が manifest trial IDs、予約値が §5 と一致することを検査。
  - 無条件 raise、SHA 推測、synthetic cell ID、budget 値の発明を殺す。
- `test_load_s8c_schedule_authority_uses_supplied_root`
  - module の repository に decoy を置かず、tmp root のみで成功させる。
  - `del root` 回帰と ambient root 読取を殺す。
- `test_load_s8c_schedule_authority_rejects_worktree_commit_byte_drift`
  - commit 後に current schedule を1 byte変更。
  - committed blob を読まず worktree だけを信用する実装を殺す。
- `test_load_s8c_schedule_authority_rejects_seed_or_authority_drift`
  - §5 seed、role-file SHA、descriptor binding の各一箇所を独立 mutation。
  - artifact decodeだけで通す経路、`verify_schedule` 不在を殺す。
- `test_load_s8c_schedule_authority_fails_closed_for_section5_status`
  - budget/master_seed それぞれに `UNFILLED` と `INVALID`。
  - default 値や field 相互流用を殺し、理由文字列も exact 比較。
- `test_load_s8c_schedule_authority_rejects_budget_shape`
  - missing/extra key、arm/holdout/cell coverage 欠落、bool・負値・非有限値。
  - permissive `.get()` と均等配分 fallback を殺す。
- `test_prepare_s8c_budget_inputs_with_real_schedule_loader`
  - `_prepare_s8c_budget_inputs` と loader/schedule module を stub せず通す。
  - loader 単体だけ正しく caller 統合が壊れる回帰を殺す。

既存 [_s8c_budget_test_setup:9024-9055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/tests/test_p3_autonomous_workload_trial.py:9024) は caller の shape/ratified-holdout 単体 test として残し、mock lambda を新しい keyword 引数に対応させる。

[test_s8c_preregistration_predicates.py:44-102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/tests/test_s8c_preregistration_predicates.py:44)

- `_c05_authority()["whiteboard"]` を exact `[]` に更新する。

[test_s8c_preregistration_predicates.py:4036-4078](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/tests/test_s8c_preregistration_predicates.py:4036)

- helper は `TOKEN_ONLY_C05_*` でなく、実 `p3_autonomous_workload_trial.py` と実 `s8c_schedule.py` bytes を cache に入れる。
- 正例は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` を期待する。SATISFIED は期待しない。
- 実 p3 から `load_schedule` 呼出しだけ除去した mutation、`consume_schedule` 呼出しだけ除去した mutation を作り、双方 `UNSATISFIED / schedule-consumer-unreachable` を要求する。
- 実 schedule module の `consume_schedule -> verify_schedule` 呼出しだけ除去し、同じ UNSATISFIED を要求する。
- 各 mutation は exact anchor の出現数を1と検査してから置換する。

これにより、正例も変異例も「supervisor と consumer の両層を stub」しない。既存 [TOKEN_ONLY fixture:798-867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/orchestrator/tests/test_s8c_preregistration_predicates.py:798) は evaluator 単体・named negative control 用として残すが、production 配線の証拠には数えない。

## runbook

[phase3-s8c-autonomous-trial-runbook.md:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2159-c05-schedule-authority/docs/phase3-s8c-autonomous-trial-runbook.md:71)

「12 述語の SATISFIED が 0 件」を次へ置換する。

> 現 repository は C10 のみ SATISFIED、C03 は UNSATISFIED、残り 10 件は EVIDENCE_UNDEFINED であり、12 条件全充足を要求する正式 H1/H2 起動が通ることを期待してはならない。

他の runbook 記述は本 wave で一般修正しない。

## 編集しない面

次は変更しない。

- `orchestrator/campaign/s8c_preregistration.py`
- `orchestrator/campaign/s8c_preregistration_evidence.py`
- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`
- `orchestrator/campaign/s8c_generation_projection.py`
- `orchestrator/campaign/s8c_budget.py`
- `output/s8c-preregistration/schedule.v1.json`
- `docs/phase3-8c-preregistration.md` §5

既存 parser の private helper 利用で値を回収できるため、禁止された preregistration module に public API を足すことは不可避ではない。

## 総括

**推す案:** whiteboard exact-empty-only、six-cell reservation を§5 budget JSONに明記、descriptor binding は実 resolver の完全表とする。
受理集合の単調拡大や sentinel 発明を避け、artifact bytes・production authority・manifest ID を一本の検証経路に束縛できる。
C05 は予定どおり completion-proof undefined に留まり、評価器や契約を緩めない。

**実装単位の分割**

- 単位A: `p3_autonomous_workload_trial.py`、`s8c_schedule.py`、`test_p3_autonomous_workload_trial.py`、`test_s8c_schedule.py`、`test_s8c_preregistration_predicates.py`
- 単位B: `docs/phase3-s8c-autonomous-trial-runbook.md`
- 禁止面4 file と `s8c_budget.py` は所有対象外

**親が段4で裁定すべき択一**

- whiteboard を exact-empty-only にするか、caller authority のまま延期するか。
- §5 budget JSON に six-cell `reserved_bench_s` を加えるか、上限から分配規則を導出するか。
- `descriptor_binding` を six-cell の extensional 完全表にするか、symbolic resolver 規則を新設するか。
- ledger path を manifest SHA 派生名にするか、単一固定 path にするか。

**確かめられなかった箇所**

- §5 数値、master_seed、schedule artifact、active ratified freeze が不在なので production 受理分岐は実走できない。
- 書込み可能な tmp がなく pytest は実走していない。したがって緑とは報告しない。
- `reserved_bench_s` の既存正本は見つからず、上記 §5 schema 案は段4裁定が必要。静的 C05 到達性だけは実 evaluator と production AST で確認済み。