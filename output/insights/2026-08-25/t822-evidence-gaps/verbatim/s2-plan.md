# 判定

- **P1: 再導出できる。** ただし `build_records` / `bench_records` の record 数からではない。`artifact_refs` が封印する `loop_state.json` を再読し、その `iteration` を cell ごとの独立世代数として使う。
- **P2: `trial_registry.py` 側だけで実装できる。** `autonomous_trial_completeness.py` は一切変更しない。

## P1: 再導出経路

返却された辞書だけを見ても世代数そのものは入っていない。しかし、次の封印参照から再読できる。

| 射影 field path | 到達できるもの | 世代数への利用 |
|---|---|---|
| `bindings.artifact_refs[*].campaign_id` | 対象 campaign | `report.cells[*].campaign_id` と対応付ける |
| `bindings.artifact_refs[*].refs[*].path == "loop_state.json"` | campaign 内の独立 checkpoint | `report.cells[*].campaign_root / "loop_state.json"` を特定 |
| `bindings.artifact_refs[*].refs[*].sha256` | checkpoint 全 bytes の封印値 | 再読 bytes の SHA-256 と一致させる |
| 再読した `loop_state.json.iteration` | WAL 非依存の実行 iteration 数 | cell の再導出世代数とする |

`artifact_refs` は campaign tree 全ファイルを列挙し、参照先 bytes を検証して返されるため、`loop_state.json` の path と digest は層 3 鎖に含まれる。[autonomous_trial_completeness.py:3175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/autonomous_trial_completeness.py:3175) [autonomous_trial_completeness.py:3620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/autonomous_trial_completeness.py:3620) [autonomous_trial_completeness.py:3761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/autonomous_trial_completeness.py:3761)

`iteration` が独立値といえる根拠は以下である。

- `LoopState.iteration` はコード上も「WAL 由来でない独立カウンタ」と定義されている。[p3_s4_loop.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/p3_s4_loop.py:156)
- standard driver は実行前に `state.iteration += 1` し、driver 完了後に `loop_state.json` へ保存する。[p3_s4_loop_trigger_gating.py:823](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/p3_s4_loop_trigger_gating.py:823)
- checkpoint の正規形は `iteration/start_wall/reverse_recommendations/whiteboard` で、`save_loop_state` が別ファイルへ保存する。[p3_s4_loop.py:653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/p3_s4_loop.py:653) [p3_s4_loop.py:731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/p3_s4_loop.py:731)
- supervisor は世代ループ中に driver を一度呼び、その結果を受けてから `report.cells[].generations` に追加する。[p3_autonomous_workload_trial.py:3733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/p3_autonomous_workload_trial.py:3733) [p3_autonomous_workload_trial.py:4032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/p3_autonomous_workload_trial.py:4032)

受入で要求する等式は次とする。

```text
sealed loop_state.iteration
== len(report.cells[cell].generations)
== report.generation_budget_per_workload
== manifest.trials[trial_id].generations
```

### 他の三 field からは直接導けない

- `build_records[*].records[*]` は `variant/stage/env_tag/ts/payload` だけで、`workload` と `generation` がない。`build_start` 数は attempt 数にはなるが、duplicate、入口停止、role-invalid 前停止があるため世代数とは一般に同値でない。
- `bench_records` はさらに `build_attempt_id` を落とした Layer 3 view であり、bench に到達しない世代も数えられない。[layer3_report.py:305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/layer3_report.py:305)
- `source_refs` は `wal:<sha256>` / `wb:<sha256>` の multiset で、世代番号や checkpoint counter を含まない。
- `campaign.lock.search_config.generation_budget` も `artifact_refs` 経由で到達可能だが、これは runtime 引数から作る宣言値であり、実行世代数の独立証拠には使わない。

### fixture の所在

- producer 型の checkpoint を実際に保存する fixture は [test_p3_autonomous_workload_trial.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/tests/test_p3_autonomous_workload_trial.py:121)。2 世代で driver iteration が `[1, 2]` になる実例は同ファイル [test_p3_autonomous_workload_trial.py:4600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/tests/test_p3_autonomous_workload_trial.py:4600)。
- cross-binding fixture は [test_autonomous_trial_completeness.py:3262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/tests/test_autonomous_trial_completeness.py:3262)。現在の `loop_state.json` は `whiteboard` だけの簡略 fixture なので、返却 projection の構造確認には使えるが `iteration` の正例には使えない。
- 正式 build 受入 fixture は [test_trial_registry.py:1017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/tests/test_trial_registry.py:1017)。こちらの `loop_state.json` を production shape に直す。

## P2: 編集面

実装は以下の二ファイルだけで完結する。

1. `orchestrator/campaign/trial_registry.py`
2. `orchestrator/tests/test_trial_registry.py`

`verify_s8c_cross_binding` は必要な `artifact_refs` をすでに返しているため、`orchestrator/campaign/autonomous_trial_completeness.py` の返却 schema や処理を変える必要はない。したがって同ファイルは **0 byte 変更**とする。

## file:line 実装プラン

### `orchestrator/campaign/trial_registry.py`

1. 定数群付近 [trial_registry.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/trial_registry.py:107)

   `_SEALED_LOOP_STATE_KEYS = frozenset({"iteration", "start_wall", "reverse_recommendations", "whiteboard"})` を追加する。checkpoint schema drift を黙って受けないため exact key 集合とする。

2. `assert_trial_registry_acceptance` の直前 [trial_registry.py:5402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/trial_registry.py:5402)

   新規 helper `_assert_sealed_loop_generation_binding(...)` を追加する。

   処理は以下の順に固定する。

   - cross-binding receipt が `mode == "build"`、`unbound_fields == []`、`bindings.artifact_refs` が list であることを確認。
   - `campaign_id` で report cell と artifact row を一対一対応させる。
   - 各 row に `path == "loop_state.json"` がちょうど一件あることを要求。
   - 既存 `_read_regular_bytes` で非 symlink regular file と読取中不変性を確認。
   - 再読 bytes の SHA-256 を `refs[*].sha256` と照合。
   - `_decode_json` で strict JSON と duplicate key 拒否を適用し、上記 exact key 集合と `type(iteration) is int`、`iteration >= 0` を要求。
   - `iteration`、cell の generation list 長、report budget、manifest 世代数の四者を照合。

3. cross-binding 呼び出し箇所 [trial_registry.py:5811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/trial_registry.py:5811)

   `verify_s8c_cross_binding` の返却値を一旦 `cross_binding_receipt` として保持し、digest を辞書へ格納する前に新 helper を呼ぶ。

   - `do_build=True` かつ完全な Layer 3 report が存在する cellでは証明を必須化。
   - `do_build=False` は既存の `no-build` 理由へ残す。
   - campaignless または Layer 3 不在は既存の `layer3-chain-absent` 理由へ残す。
   - 完全な Layer 3 鎖があるのに `loop_state.json` が封印されていない場合は hard failure とする。

### gate とエラー文言

既存の `generation-binding` gate を拡張し、新しい reason code は追加しない。

```text
[generation-binding] cross-binding projection does not seal exactly one loop_state.json for campaign '<id>'
[generation-binding] sealed loop_state.json bytes differ from cross-binding artifact_refs for campaign '<id>'
[generation-binding] sealed loop_state.json has invalid generation-counter schema for campaign '<id>'
[generation-binding] sealed loop_state.iteration differs from report/manifest generations for campaign '<id>': sealed=<n>, cell=<n>, report=<n>, manifest=<n>
```

不一致時は receipt を発行しない。したがって不一致 run が既存の必須理由だけを持つ receipt として紛れ込むこともない。

### 受理例

- 正例: sealed `iteration=2`、cell generation 数 `2`、report budget `2`、manifest `2`。従来どおり receipt 発行へ進む。
- 負例 1: sealed `iteration=1`、他の三値は `2`。下振れとして `generation-binding` で拒否。
- 負例 2: sealed `iteration=3`、他の三値は `2`。上振れとして同 gate で拒否。

入口停止、duplicate、driver 前の role-invalid などで checkpoint から世代数を証明できない run も拒否側へ倒れるため、受理集合は狭まるだけである。

## テスト計画

対象は [test_trial_registry.py:1017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/tests/test_trial_registry.py:1017) だけとする。

- `_build_registered_campaign` の `loop_state.json` を production と同じ四 key shape にし、正例では `iteration == trial.generations == 2` を保存する。
- test 専用 helper `_reseal_registered_loop_iteration` を追加する。iteration を変更後、persisted Layer 3 の `artifact_refs[path=="loop_state.json"].sha256` も更新し、単なる hash mismatch ではなく新しい世代 gate まで到達させる。
- 既存正例 `test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads` に、全六 cell の sealed iteration が 2 で receipt 発行まで到達する述語を追加する。
- 新規 `test_t1211_acceptance_rejects_sealed_loop_generation_count_below_declaration` は `sealed=1, cell/report/manifest=2` と exact gate 文言、receipt 不在を pin。
- 新規 `test_t1211_acceptance_rejects_sealed_loop_generation_count_above_declaration` は `sealed=3, cell/report/manifest=2` と exact gate 文言、receipt 不在を pin。

AST による現状確認では `trial_registry.py` と `test_trial_registry.py` の top-level 関数名重複はともにゼロで、上記新規名も存在しない。D864 に従い、実装後にも変更した `test_trial_registry.py` だけを再走査する。

## リスクと不変性

- **六 report 受入経路:** report 数、trial の並び、既存 holdout/arm 条件は変えない。正しい build 六報告は通り、食い違う報告だけが新たに落ちる。
- **receipt bytes:** helper は cross-binding receipt を変更せず読むだけである。正しい既存入力では `receipt_value` の key、値、canonical preimage、SHA-256 は不変。
- **非 certifying 理由:** `no-build`、`layer3-chain-absent`、`c02-arm-binding-unproven`、必須理由を変更しない。新 reason code は追加しない。
- **schema version:** acceptance receipt v3、cross-binding receipt v1、report、journal、Layer 3 の全 schema version を据え置く。
- **fixture:** registered-build fixture の一時生成 bytes は production shape 化により変わるが、追跡済み receipt schema や製品の正例 receipt 生成規則は変わらない。
- repo 内に正式 8c の report、journal、campaign WAL 三点セットはないため、既存正式成果物の再発行や migration は発生しない。

## 総括

- P1: できる。`artifact_refs` で封印された `loop_state.json.iteration` を再読し、cell ごとの独立世代数とする。
- `build_records`、`bench_records`、`source_refs` 単独からは世代番号を導出できない。
- P2: できる。実装は `trial_registry.py` の消費側だけで完結し、競合中の completeness file は触らない。
- 四者不一致または封印欠落は `generation-binding` で hard failure とし、受理集合だけを狭める。
- receipt bytes、reason code、schema version は変更しない。