# 段 1 brief — [T-1311] arm execution authority

worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority`
branch: `worktree-dev-wave-t1311-arm-authority` (base `2a3b5055`)

## scope

arm (`on` / `off` / `swapped`) が 8c 正式系列の**実行を実際に変える** authority を実装する。

1. `off` の「凍結済み中立入力」の canonical bytes を新規に作る (schema + 生成器 + 検証器)。
2. arm が選ぶ入力から **sealed execution digest** を導出する。
3. 同じ digest を 6 sink すべてで消費させる (下表)。
4. 契約が名指しする entrypoint `bind_trial_arm` を `orchestrator/campaign/trial_registry.py` に実装する。

## 確定済みユーザー裁定

- T-822 問 2 の択 (a) が採択され本タスクが起票された。択 (b) (`report["executed_arm"] = binding.arm`
  の往復照合) は**定義上恒真として明示的に不採用**。同型の実装を採ってはならない。
- 択 (c) (receipt v2 で `c02-arm-binding-unproven` を外す) は arm authority 完成**後**の別件。
  本 wave では receipt v1 のまま `certifying=false` と必須 reason 2 語を保持する。

## 実測 (brief 前に親が測った事実)

- `enforcement_arm` は宣言 token でしかない。`OriginProducerInputs.enforcement_arm`
  (`p3_autonomous_workload_trial.py:338`) は caller が渡す非空 str 検査 (`:851-857`) だけを受け、
  `_complete_origin_runtime` (`:962`) 経由で `reflux_formal_consumer.evaluate_formal_origin`
  (`reflux_formal_consumer.py:893,897,916,1001`) と projection (`:384`) へそのまま出る。
  **どの実入力からも導出されていない。**
- `_descriptor_for` (`:687-695`) は `WORKLOADS[workload]` の flags だけから descriptor を作る。
  8c supervisor 全体に arm 引数が 1 つも存在しない (`grep -n "arm" p3_autonomous_workload_trial.py`
  の hit は上記 4 行のみ)。
- したがって `_campaign_for` (`:637-668`) の `descriptor_sha256` も arm 非依存。
  `spec_slug=f"p3-t178-{workload}"` / `trial=f"{trial_id}-{workload}"` にも arm が入らない。
- `invocation_id=f"{workload}.g{generation}.<role>"` (`:2616,:2667,:2703,:2724`) にも arm が無く、
  proposal bytes は `raw_{invocation_id}.txt` (`:1518`) と `{kind}_{invocation_id}.json` (`:1537`)
  に落ちる。arm を増やすと path が衝突する (事前登録 §6 前提条件 2 が名指しした状態)。
- 証拠契約 C02 (`s8c_preregistration_evidence_contract.v1.json`) は sink を凍結済みで、
  `field_paths = manifest.cells[*].arm / run_start.arm / terminal_report.arm /
  campaign_identity.arm / proposal_path.arm / invocation_id.arm`、
  `consumer_requirement.entrypoints = [bind_trial_arm, accept_trial]`、
  `negative_control_id = nc_c02_proposal_path_arm_collision`、`machine_checkable: false`。
- 判定器の現状 (library 経路で実測、HEAD=2a3b5055): **C02 = `EVIDENCE_UNDEFINED` /
  `arm-binding-declared-only`**。`machine_checkable:false` ゆえ本 wave で SATISFIED にはならない。
- `output/s8c-trial-registry/` は**存在しない** = 正式 trial は 1 本も走っていない。
  `p3-t178` を pin するのは 4 test file だけで、凍結 artifact の pin は無い
  (`grep -rln "p3-t178"`: 実装 1 + test 4、`output/` 0 件、docs は archive worklog 2 件のみ)。
  → campaign identity を arm 依存へ変えても凍結 bytes の巻き添えは無い。

## 不変条件 (破ってはならない)

- **`s8c_preregistration_evidence_contract.v1.json` と `output/s8c-preregistration/condition-freeze/`
  を編集しない。** 変えると contract sha256 が動き g6 凍結世代が要る (本 wave の scope 外)。
- **`assert_trial_registry_acceptance` を `accept_trial` へ改名しない。** T-822 問 3 の所有物で
  (i) Layer-3 の wave が持つ。C02 の consumer 半分は未充足のまま残ると正直に報告する。
- receipt v1 の `MANDATORY_NON_CERTIFYING_REASONS` (`s8c_acceptance_receipt.py:25-28`) と
  `certifying=false` の構造固定を外さない。
- 規律 2/3: 既存テストの期待値を反転・緩和・skip・削除しない。恒真な assert を新設しない
  (宣言値どうしの往復照合は本タスクが禁じた形そのもの)。
- `docs/phase3-8c-preregistration.md` / `docs/phase3-8b-descriptor-design.md` の規範本文を変えない
  (§6 前提条件 2 は既に本実装を要求しており、実装は文言変更を要さない)。

## 成果物影響 (DW-G05)

実装しない場合、8c 正式受入 receipt は**宣言と違う arm で走った run を受理し続ける**。
同一 holdout の `on` / `off` label を manifest 内で入れ替えて hash を再生成するだけで、
trial_id・campaign_id・proposal・invocation・実行 descriptor が不変のまま通る。
6 cell 比較 (descriptor 条件付き挙動の有無) という主張そのものが成立しない。

## 6 sink と実アンカー

|#|sink|現在のアンカー|
|---|---|---|
|1|descriptor|`_descriptor_for` `:687-695` → `_common_payload` `:1589-1600` の `workload_descriptor` / `descriptor_binding`|
|2|campaign identity|`_campaign_for` `:637-668` (`search_config`, `spec_slug`, `trial`) → `ident.campaign_id` (`_prepare_campaign_identity` `:727`)|
|3|proposal bytes/path|`_invoke` `:1518` `raw_{invocation_id}.txt`、`:1537` `{kind}_{invocation_id}.json`|
|4|invocation namespace|`:2616,:2667,:2703,:2724,:1966` の `invocation_id`、`ensure_exploration_namespace` `:3040`|
|5|run-start|`run_start` dict `:3078-3104` と journal append|
|6|terminal report|`_complete_origin_runtime` `:962` `enforcement_arm` → `reflux_formal_consumer.py:893,916,1001,384`|

加えて `trial_registry.py`: `ARMS` `:49`、`assert_campaign_binding` の呼び (`:796-799`)、
`launch_admission_record` `:912`、および新設 `bind_trial_arm`。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** sealed execution digest は「arm が選んだ**実入力 bytes** の canonical hash」とし、
  arm 名 (`on`/`off`/`swapped`) を hash の入力に**含めない**。理由: arm 名を混ぜると、
  中身が同一でも label だけで digest が動き、label 交換攻撃を検出する代わりに label を信じることになる。
  digest が違えば実行入力が違う、が成り立つ形にする。
- **(P2)** `off` の中立入力は「descriptor と同じ schema・同じ field 集合を持ち、全 workload で
  同一の固定 bytes」とする。`null` や欠落ではなく実体を置く。理由: planner/coder の payload schema を
  arm 別に分岐させると、arm が prompt 構造から漏れて blind 性が壊れる。
- **(P3)** `swapped` の対応先 flags は**解決器 (resolver) 越し**に取り、本 wave で新規の対応表を
  凍結しない。実測: `WORKLOADS` は `ycsb-a/b/c` (rr50/95/100) だけで (`:188-192`)、
  `trial_registry.HOLDOUT_BINDINGS` の `H1=rr80` / `H2=rr20` は `WORKLOADS` に無い。
  さらに `HOLDOUT_BINDINGS` が持つのは `ycsb_rratio` だけで、descriptor に要る
  `ycsb_zipf_skew` / `ycsb_rmw` が無い。**したがって `swapped` の実 flags は [T-1310] が
  production profile を入れるまで構成できない。** 本 wave は resolver を実装し、
  対応先 flags が解決できないときは**起動を拒否する** (静かに `on` へ落ちる・空 descriptor で
  走る形を作らない)。H1/H2 は 2 要素なので derangement は一意 (H1↔H2) であり表は要らない。
- **(P4)** 新規凍結 artifact は `output/s8c-preregistration/arm-inputs/` 配下に置き、
  独自の schema_version と検証器を持つ。condition-freeze の世代機構には**入れない**。
- **(P5)** 分割: 単位 A = 中立入力 artifact + digest 導出 + `bind_trial_arm` (trial_registry 側)、
  単位 B = 6 sink の消費配線 (p3_autonomous_workload_trial 側)。B は A に依存するので直列。

## 変異の事前登録方針 (段 4 で確定)

「digest を消費しない sink を 1 つ残す」形を 6 sink 分、必ず殺せる対を作る。
wave 前の実コードの形 (arm が全く入っていない `invocation_id` / `spec_slug` / `enforcement_arm`) を
変異体として必ず含める。
