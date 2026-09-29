## 総括

[T-2867] は、**系列台帳から次の実行単位を導出し、その単位を job 起動時に照合する**契約を先に固定すると、U1〜U6 を所有 path ごとに並列実装できる。計測 identity は D2281 の `policy_iteration` を対照用に拡張し、論理 slot と retry attempt ごとに分ける。既定の `default_cfg` と既存 CLI action は変更しない。

以下は指定資料とコードの静的検査に基づく実装 plan。書込み・テスト・計算投入は行っていない。

## 1. 固定する interface

### 1. 系列 identity

`default_cfg` に任意の `contrast=(cohort, arm, series)` を加える。指定時だけ `search_config` に `contrast_cohort: str`、`contrast_arm: "llm-cpp"|"llm-ir"|"random-ir"|"evo-ir"|"reference"`、`contrast_series: int` を追加する。参照は `series=0`。未指定時は現在の辞書と campaign ID の bytes を維持する。追加位置は [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:121) の `default_cfg`、約25行。`form` は arm に従い、reference では方策候補を持たない。

### 2. 計測 campaign identity

系列 cfg に `contrast_slot: str`、`contrast_index: int`、`contrast_attempt: int` を足して計測 cfg を作る。slot は `job1-stock/0`、`job1-seed/1`（5 µs）、`job1-seed/2`（10 µs）、`eval/b`（b=1..10）、`score/s`（s=1..5）、`reference-stock/s` と `reference-fixed10/s`（s=1..5、batch は `contrast_index` の上位座標として別 `contrast_batch: 1..3`）とする。通常の `contrast_index` は前述の b または s。初回 attempt は 0、機械故障 retry は 1、2。同一論理 slot の retry でも claim が新しくなる。既存 pair の `policy_iteration` は対照経路で使わず、[D2281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/docs/decisions.md:73481) の one-shot claim と計測 dir 分離を継承する。約20行。

### 3. 単位 file

launcher が create-only で書く JSON の schema を `silo-policy-contrast-unit/v1` とする。

```json
{
  "schema": "silo-policy-contrast-unit/v1",
  "ledger_root": "/absolute/path",
  "cohort": "test-cohort",
  "arm": "llm-cpp",
  "series": 1,
  "kind": "job1",
  "a": null,
  "b": 0,
  "proposal_path": null,
  "proposal_sha256": null,
  "endpoint_identity": null,
  "slots": [
    {"slot": "job1-stock", "index": 0, "attempt": 0},
    {"slot": "job1-seed", "index": 1, "attempt": 0},
    {"slot": "job1-seed", "index": 2, "attempt": 0}
  ]
}
```

`kind` は `job1|eval|score|reference`。eval は `a,b,proposal_path,proposal_sha256`、score は固定済み `endpoint_identity` と5 slot、reference は `arm=reference, series=0, contrast_batch` と10 slotを持つ。`next_unit(ledger)` が返す同じ schema の JSON と、起動時に全 field を照合する。proposal bytes の SHA-256 も再照合し、不一致なら **slot 開始 event と session の前**に rc=2。`slot-attempt-start` があり結果が無い場合、次単位を自動生成せず停止する。草稿 [§5.6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/docs/silo-policy-generator-contrast-preregistration.md:239) の要求に対応する。

### 4. driver CLI

[p3_s4_loop_policy.py:533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:533) の action 群に、対照専用の `--contrast-cohort`, `--contrast-arm`, `--contrast-series`, `--contrast-ledger-root` と次を加える。

| action | 引数・stdout JSON | rc |
|---|---|---|
| `--contrast-emit-coder-input` | baseline、任意の `--critic-output`。既存の5 key、診断時6 keyをそのまま出す | 0、入力不正2 |
| `--contrast-preview PROPOSAL` | 既存 preview と同じ `{passed,working_diff,diff_digest,subtype,rule_id}` | 通過0、拒否1、入力不正2 |
| `--contrast-record-reject PROPOSAL` | `{outcome:"rejected",reject_subtype,reject_rule_id}`。系列履歴と台帳の A を1消費 | 0、通過候補を渡した誤用2 |
| `--contrast-run-unit UNIT.json` | `{kind,slots:[{slot,index,attempt,campaign_id,outcome,quality,fitness_tps,abort_rate_pct,wal_sha256}],driver_rc}` | 完了0、候補・測定不成立1、契約不一致2 |

最後の action だけ計算 node で実行し、既存の [検査順:178–205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:178)、[評価:388–431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:388)、[stock:366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:366) を呼ぶ。既存 `--run-iteration --stock-control` 等の分岐 [653–697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:653) には入れない。対照の停止は台帳の A/B で決め、既存 `L.check_stop` [450–458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:450) は変更しない。同時検査 key は対照 cfg だけに `verify_performance_concurrent: true` を入れ、既存の [loop.py:902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/loop.py:902) に委ねる。

### 5. proposal

LLM は既存 `{coder,auditor}` を維持する。機械生成 IR は別 schema にする。

```json
{
  "generator": {
    "name": "random-ir",
    "version": "test-version",
    "preimage": "test-version|random|1|1|0",
    "counter": 0
  },
  "ir": {"kind": "PolicyIR"}
}
```

`name` は `random-ir|evo-ir|evo-fallback-ir`。生成器は tagged IR を [parse_policy_ir:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_ir.py:136) と [render_policy:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_ir.py:296) に渡す。`policy_gate` [193–204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:193) の auditor 分岐だけ機械候補では省き、書込後 digest 再照合は両由来で行う。`llm-*` arm は機械 proposal を拒否。初期点は proposal と別の登録 seed 分岐で、[enumerate_recon:381–398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_ir.py:381) の `0000`,`0001` の IR だけを全 arm に許す。

### 6. 系列台帳

`header.json` に schema、cohort、arm、series、form、HEAD、PIN、登録版、A/B/N_eval、配置 batch、計測設定、submit checkout を固定する。event は連番の create-only file とし、種類を `series-start`, `slot-attempt-start`, `slot-result`, `proposal-opportunity`, `proposal-rejected`, `pipeline-submitted`, `evaluation-result`, `machine-retry`, `llm-outage`, `llm-role-result`, `critic-result`, `endpoint-fixed`, `score-session`, `series-end` に限定する。共通 field は `a,b,logical_slot,attempt,campaign_id,campaign_root,proposal_path,proposal_sha256,provenance,identity,source_digest,variant,wal_sha256,outcome,failure_class,quality,fitness_tps,abort_rate_pct,anomalies,timing,note`。未使用 field は null。

A は `proposal-opportunity` で1回、B は `pipeline-submitted` で1回だけ進める。429 は `llm-outage` の回数・時刻・長さを記録し A/B/retry を進めない。機械故障は同じ論理 slot の `machine-retry` と attempt を進め、2回の追加 retry 後は `series-end(reason="machine-retry-exhausted", score=null)`。他の終了理由は `b-complete`, `a-exhausted`, `stock-unestablished`, `quality-missing`, `proposal-role-failure`, `model-mismatch`, `unclassified-missing`。endpoint は identity・source・slotを `endpoint-fixed` で score 前に固定する。

[t2849 の SeriesLedger:49–92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/t2849_comparison_harness.py:49) は `EVENT_KINDS` と `END_REASONS` を B-5 から import しているため**直接再利用不可**。その約45行の連番・create-only 書込の形だけを、本対照の一つの台帳へ移す。B-5 の schema を広げる互換層は作らない。

### 7. critic と履歴

`job1` 完了時、系列 dir の `policy_history.jsonl` に初期点2行を順番に入れる。既存 [ `_append_history`:216–226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:216) と [coder の `self_history`:282–300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:282) の行形を用い、`iteration` は初期点に `-2,-1`、探索点に原提案番号 a を使う。追加する `logical_slot` と `measurement_campaign_id` は履歴原本に置き、coder 射影には足さない。stock は履歴候補行にせず baseline として渡す。

系列 dir の `contrast_critic_digest.json` に、前回 critic 以後の各 slot の `{logical_slot,campaign_id,digest}` を保存する。digest は各計測 campaign の admitted WAL から既存 `L.make_critic_digest` [481–484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:481) で作る。critic prompt はこの digest、slot の方策本文、同 job の stock を逐語で組み立てる。新結果がある原提案機会だけ、critic を最初の役割にする。却下だけが続く場合は再呼出ししない。草稿 [§4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/docs/silo-policy-generator-contrast-preregistration.md:105) の情報境界を維持する。

### 8. round tool と親

新 `tools/silo_policy_contrast_round.py` の subcommand は `critic-input`, `coder-input`, `preview`, `record-reject`, `auditor-input`, `finalize`。役割の入出力を file に保存し、`coder-input` は driver stdout の JSON を無加工で渡す。親 `tools/pegasus/silo_policy_contrast_parent.py` は **1 原提案 a ごとに新しい `claude -p --output-format json`** を起動し、resume しない。指示文は「必要なら critic → coder → preview → 拒否なら record-reject → 通過なら auditor → proposal 確定」の機械的手順、他系列・偵察値を読まない指示、手直し・再抽選をしない指示を含む。auditor spawn prompt には runbook [§1(d):83–92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/docs/phase3-silo-policy-runbook.md:83) の `violations`、`nits`、`proposed_tests`、`uncertainty` の閉じた形を逐語で書く。`classify_exit` [b5_llm_parent.py:41–50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/b5_llm_parent.py:41) だけで429を判定する。許可 tool は round tool を呼ぶ `Bash`、役割用 `Agent`、保存済み入力を読む `Read` に絞り、一般の編集 tool は与えない。

### 9. report

入力は上記 header・event と各 slot の WAL 結合結果、3 batch の reference 台帳、発効束、endpoint 目視所見。`exact_sign_flip_p`、`_holm`、`stock_cv_floor(v2=True)`、`decide_comparison(v2=True)` を [B-5 report:48–174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/b5_generator_contrast_report.py:48) から import する。`pair_differences` [103–115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/b5_generator_contrast_report.py:103) は 1..12 固定なので使わず、対照側で `range(1,n+1)` の小関数を作る。n は発効束から10または12。族 A/B 各2比較の Holm を別々に呼ぶ。生成不成立は「certified・品質正常な**探索点**を持つ系列数」で数え、初期点を除く（草稿 [§7.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/docs/silo-policy-generator-contrast-preregistration.md:312)）。

### 10. 生成器と試験版

新 `silo_policy_contrast_generators.py` に `random_ir(*, version:str, series:int, a:int) -> (ir, provenance)|None`、`evolve_ir(*, version:str, series:int, a:int, eligible_points:Sequence[Point]) -> (ir, provenance)|None` を置く。内部の counter は0..999。`None` は空出力として A だけ消費する。式・定数・変異 site は [IR の型:24–121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_ir.py:24) と [validate_ir:231–285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_ir.py:231) に従い、整数重みは [weights_table:82–94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/b5_generator_contrast.py:82) を呼ぶ。親選択は品質正常の探索 session median 最大、同値は早い slot。**試験・生死確認の `version` は `silo-policy-contrast-test-2026-09-29`** とし、v1 の文字列や、その preimage から引く IR・値を試験出力に使わない。発効後だけ草稿 [§4.4–4.5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/docs/silo-policy-generator-contrast-preregistration.md:144) の登録文字列を指定する。

## 2. 単位ごとの plan (U1〜U6)

| 単位・所有 path | 主な変更箇所と見積り | 依存 |
|---|---|---|
| U1 driver: `orchestrator/campaign/p3_s4_loop_policy.py`、`orchestrator/tests/test_p3_s4_loop_policy.py` | cfg [121–143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:121)、proposal [88–119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:88)、gate [178–205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:178)、履歴 [216–300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:216)、CLI [533–697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:533) に約260–340行、テスト約220–300行。fixed10 は [silo_policy_recon.py:70–85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_recon.py:70) の define 確認を trace/bench 両 build に適用する。 | 本節の interface を固定後。U4 の `next_unit` API に依存 |
| U2 job body: `tools/pegasus/p3_s4_loop_pegasus.sh`、既存の job body test、`tools/pegasus/README.md` | mode 解析 [227–259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/p3_s4_loop_pegasus.sh:227) と実行 [789–803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/p3_s4_loop_pegasus.sh:789) に `contrast` を約35–55行、テスト約70–100行、手順約35行。env は `IZANAGI_S4_POLICY_UNIT_PATH` のみ追加し、既存 mode と排他。 | U1 CLI |
| U3 生成器: 新 `orchestrator/campaign/silo_policy_contrast_generators.py` と同名 test | IR tree の型付き grow、preimage、random、進化、provenance を約330–430行、固定入力 test 約180–230行。 | interface 5・10 |
| U4 制御・起動器: 新 `orchestrator/campaign/silo_policy_contrast.py`、`tools/pegasus/silo_policy_contrast_launch.py`、各 test、`tools/pegasus/admission_registry.json` | 台帳・A/B・next_unit・session 分類・endpoint 約430–560行、launcher 約180–240行、test 約300–400行。[B-5 分類:265–308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/b5_generator_contrast.py:265) は bench payload/WAL timing 部分のみ再利用。registry に login-direct/local-ok を登録。 | U1 schema、U3 proposal |
| U5 round・親: 新 `tools/silo_policy_contrast_round.py`、`tools/pegasus/silo_policy_contrast_parent.py`、指示文 file と test | round 約180–240行、親約130–180行、test 約180–240行。[系列 C の auditor prompt](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-series-c/make-auditor-prompt.py)、[critic prompt](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-series-c/make-critic-prompt.py) を下敷きにする。親の tool 登録も U5 所有。 | U1・U4 |
| U6 report: 新 `orchestrator/campaign/silo_policy_contrast_report.py` と test、`docs/README.md` の地図 | 台帳射影・n=10/12・4比較・記述統計を約260–340行、test 約180–240行、地図約5行。 | U4 schema |

合流順は **interface 固定 → U1/U3/U4 の骨格 → U2/U5/U6 → 結合試験 → 生死確認**。所有 path が重ならないよう、U1 は U4 の台帳実装を編集せず、U4 は driver を編集しない。

## 3. 影響テストと inventory

- **U1:** [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/tests/test_p3_s4_loop_policy.py:602) の既存 pair/claim 試験を退行確認し、対照 cfg、初期点、機械 proposal、fixed10、session 分類を追加する。[test_campaign.py:4937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/tests/test_campaign.py:4937) の certified-writer caller inventory は U1 が `run_campaign` の呼出箇所を増やした場合に [5520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/tests/test_campaign.py:5520) と [5603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/tests/test_campaign.py:5603) を更新する。既存呼出しの再利用だけなら数は変えない。[test_p3_exploration_namespace.py:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/tests/test_p3_exploration_namespace.py:455) の driver 登録・site 契約も確認する。
- **U2:** job body の mode 排他、unit path 不在、開始前不一致、旧 `stock|pair|replay` の argv を試験する。[test_p3_b4_wiring_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/tests/test_p3_b4_wiring_probe.py) は mode 配線を grep して該当性を確認する。`tools/pegasus/README.md` の [登録表:22–35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/README.md:22) と [方策手順:476–495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/README.md:476) を更新する。
- **U3:** IR の depth/node/type と再抽選1000回、進化の field 追加・同値親を固定入力で検査する。既存 `test_silo_policy_ir.py` も退行確認する。
- **U4/U5:** 新しい Pegasus login 実行体は [admission_registry.json:34–44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/admission_registry.json:34) と README 登録表を各所有者が追加する。`test_pegasus_policy_registry.py` 等の閉集合 test を確認する。U4 の ledger は B-5 の `EVENT_KINDS` を変更しない。
- **U6:** [test_official_perf_closure.py:45–105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/tests/test_official_perf_closure.py:45) の perf file inventory と [916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/tests/test_official_perf_closure.py:916) の検査は、新 module が perf 実行 API を呼ぶ場合だけ更新する。report は記録読取りに留める。`docs/README.md` の地図を追加する。

## 4. 生死確認の手順と walltime 案

計算投入前に、brief の見積り **生死確認約1.5 node 時間＋検査最大約1.9 node 時間**を提示し、D2212 項4に従ってユーザー確認を得る。以下は確認後の login 操作列の雛形であり、ここでは実行しない。

```bash
# submit checkout は job dir 下、AI worktree 容器の外に1本
make-submit-tree.sh <landed-HEAD> <submit-tree>
python3 tools/pegasus/silo_policy_contrast_launch.py init \
  --checkout <submit-tree> --cohort silo-policy-contrast-test-2026-09-29 \
  --series 1 --arms llm-cpp,llm-ir,random-ir
python3 tools/pegasus/silo_policy_contrast_launch.py submit-next \
  --checkout <submit-tree> --cohort silo-policy-contrast-test-2026-09-29 \
  --arm llm-cpp --series 1                 # job1
# llm-ir、random-ir の job1 も同じ順で投入し、各 WAL と台帳の終端を確認
python3 tools/pegasus/silo_policy_contrast_parent.py run-one \
  --checkout <submit-tree> --arm llm-cpp --series 1
python3 tools/pegasus/silo_policy_contrast_launch.py submit-next \
  --checkout <submit-tree> --arm llm-cpp --series 1  # 評価1
# llm-ir も run-one→submit-next、random-ir は生成→submit-next
python3 tools/pegasus/silo_policy_contrast_launch.py inspect \
  --checkout <submit-tree> --series 1
```

`submit-next` は unit file を書き、[系列 C の submit](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-series-c/submit-policy.sh) と同じ env・archive・`qsub` 形で1 jobを投げる。3系列それぞれ job1 と評価1について、job rcだけでなく **各 slot の計測 dir の WAL 終端、campaign ID、台帳の `slot-result`** を照合する。

暫定 walltime は全 arm 共通で job1 **60分**、評価 **30分**、score **90分**、reference **90分**。草稿 [§11.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/docs/silo-policy-generator-contrast-preregistration.md:388) の例であり、発効束では今回の最大 Job Elapse に倍率を掛けて確定する。score と reference の単価は job1・評価の session 単価からの**換算**と明記する。進化は固定入力試験のみ。

## 5. 変異の候補

| 単位 | 壊す1行 → 赤になる test の機構 |
|---|---|
| U1 | `contrast_attempt` を cfg から落とす → retry の campaign ID 差を検査する test。`auditor is None` の書込拒否を全候補へ戻す → random IR 実行 test。LLM arm で機械 proposal を許す → arm 拒否 test。fixed10 の trace0 define 確認を外す → 両 build define test。 |
| U2 | `contrast` mode の unit path 必須行を外す → env 排他 test。driver argv の `--contrast-run-unit` を `--run-iteration` に替える → argv 配線 test。旧 pair の `--stock-control` を落とす → 既存 mode 退行 test。 |
| U3 | zero の確率分母を8から7へ変える → 固定分布 test。`c += 1` を外す → 不正 IR 再抽選 test。親の同値 tie を遅い slot に変える → 親選択 test。field 追加時の自己参照を落とす → 変異 arity test。 |
| U4 | `pipeline-submitted` で B を増やさない → A/B 計上 test。attempt を据え置く → one-shot claim retry test。未終端 `slot-attempt-start` を無視する → 途中死停止 test。endpoint 同値を遅い slot にする → 固定 test。 |
| U5 | `api_error_status` を見ず文言で429判定する → `classify_exit` test。前回 critic 以後の新結果判定を常時 true にする → 却下連続 test。coder 入力に独自 key を足す → driver 出力の bytes 一致 test。 |
| U6 | `range(1,n+1)` を `range(1,13)` にする → n=10 test。生成不成立の数に初期点を含める → 探索点ゼロ test。族 A/B を一つの Holm にする → 族別補正 test。 |

## 6. brief への異議・草稿との食い違い

| 項 | 判定と理由 |
|---|---|
| P1 | **同意。** D2281 の claim 単位を各 slot/attempt へ拡張する。score・reference の各 session も別計測 campaign とする。 |
| P2 | **同意。** 系列座標を対照指定時だけ cfg に足し、既定 bytes を守る。 |
| P3 | **同意。** unit file と台帳からの導出結果を session 前に全 field で照合する。 |
| P4 | **同意。** 機械 proposal は provenance を持つ別形とし、登録 seed だけ全 arm の例外にする。 |
| P5 | **同意。** slot ごとの WAL digest と本文・同 job stock を critic へ渡す。初期点の履歴行は原提案1より前に置く。 |
| P6 | **同意。** 元の fixed10 patch と2 defineを使い、trace/bench 両 build で確認する。ただし既存 `run_campaign` への source/build option の通し方は U1 実装時に最小の既存入口を確定する必要がある。 |
| P7 | **同意。** 統計核のみ importし、`pair_differences` の固定12件と B-5 台帳射影は本対照側で扱う。 |
| P8 | **同意。** 3系列の job1＋評価1で生死を確かめ、進化・score・reference の計算実測を主張しない。 |

草稿からの規則変更は提案しない。`policy_history.jsonl` の初期点用 iteration `-2,-1`、cfg key、unit JSON、event 名は草稿が未指定の実装表現であり、発効前に固定する interface としてここで提案した。