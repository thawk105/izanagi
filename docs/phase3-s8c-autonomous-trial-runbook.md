# Phase 3 段 8c Runbook — workload-conditioned bounded autonomous trial

**位置づけ:** `orchestrator/campaign/p3_autonomous_workload_trial.py` は、既存の
`silo-backoff-trigger-gating` 安全 harness を Python supervisor から駆動する段 8c の
bounded MVP である。planner / coder / auditor / critic を fresh な headless Claude context
で直接呼び、workload descriptor を proposal 前に渡し、固定世代数または wall budget まで
無人継続し、全試行 journal と terminal report を生成する。

これは汎用 daemon でも正式な descriptor-conditioned synthesis 実験でもない。YCSB A/B/C
は配線 pilot であり、正式主張には
`docs/phase3-8b-descriptor-design.md` の H1/H2 × on/off/swapped を別途実装・事前登録・実走する。
事前登録は git commit した文書で行い、凍結機構は使わない (D116)。

## 1. 何が自動化されたか

1 generation は次の順で Python が運ぶ。

1. search config から `8b-v1` workload descriptor を決定論射影し、schema と禁止キーを検査
2. descriptor + 当該 campaign の観測済み値 + abstract whiteboard を planner へ射影
3. planner の `axis/direction/magnitude` **だけ**を coder へ渡し、具体 gate 述語を合成
4. working diff を preview し、DiffQuarantine と禁止識別子 gate を先行判定する。
   これは supervisor 側の **pre-audit の再実行**であり、既存 driver の preview を呼び出しては
   いない。受理集合を広げないが「再実装がない」という意味ではない (段 6 の判定基準は常に
   authoritative path 側)
5. diff と designated context を auditor へ渡す。実際の payload には workload / descriptor /
   generation / policy を含む common 部も入る (auditor は diff だけを見るのではない)
6. 既存 trigger-gating driver へ proposal を渡し、build 有効時は
   diff quarantine → syntax gate → auditor digest 照合 → build → legacy+S2 verify → bench
7. harness digest と結果を critic へ渡し、次 generation の reverse signal を得る
8. 固定世代数、既存 safe-loop stop、または wall budget で停止し report を書く

性能目標による早期停止はない。成功時だけ止める適応停止を入れると Best-of-N / 選択的報告に
なるため、pilot の既定は固定世代数であり全 attempt を残す。

## 2. Provider と隔離

`--provider claude-headless` は project role の本文を read-once し、role ごとの mediated
projection contract を追加した effective prompt を使う。各呼び出しは:

- `claude -p` の 1 turn、session persistence なし、fresh neutral cwd
- runtime `tools=[]`、空 MCP、slash command 無効、settings source 無効
- env allowlist = `PATH/HOME/LANG/LC_ALL/TERM`
- session id 再利用拒否、主 model = Opus 一意、正の input/output token を要求
- server tool use = 0、permission denial = 空を要求
- source role SHA、effective prompt SHA、payload SHA、envelope SHA、CLI binary SHA を記録

auditor / critic の source role は read/Bash tool を宣言しているが、この supervisor では全入力を
inline 射影するため runtime 能力を `tools=[]` へ縮退する。元 tool 権限を headless process へ
持ち込まない。

Codex role adapter はこの実走経路に使わない。`.codex/agents/README.md` と
`tools/check_codex_agents.py` が runtime blocked と分類している間、通常の Codex 子を role
隔離の代替にもしない。

## 3. 起動

全コマンドは repository root から実行する。`TRIAL_ID` は `[a-z0-9._-]` の一意な名前にする。
既存 run root は受理しない。MVP は supervisor crash 後の in-place resume をまだ持たないため、
再実行は新しい trial id で行い、旧 journal を上書きしない。

### 3.1 決定論 fixture、build なし

```bash
python3 -m orchestrator.campaign.p3_autonomous_workload_trial \
  --trial-id fixture-abc-g1 \
  --provider fixture \
  --workloads ycsb-a,ycsb-b,ycsb-c \
  --max-generations 1 \
  --no-build
```

これは descriptor→4 roles→diff/auditor gate→report の配線検査で、LLM 実証でも性能実験でもない。

### 3.2 実 Claude、build なし

```bash
python3 -m orchestrator.campaign.p3_autonomous_workload_trial \
  --trial-id claude-abc-g1 \
  --provider claude-headless \
  --workloads ycsb-a,ycsb-b,ycsb-c \
  --max-generations 1 \
  --no-build
```

12 role attempts (3 workload × 4 roles) が最大各1回で走る。応答 schema 違反は再試行せず
`role-invalid` として当該 cell を停止し、他 cell は続行する。partial report の CLI exit は 2。

### 3.3 build / verify / bench を含む探索

**現在の Pegasus 運用では 3.3 をそのまま実行できない。** login node での build / bench は
`docs/pegasus-runbook.md` が禁じており、campaign の計算ノード dispatch 経路は未実装である
([T-276] / [T-277] の裁定済み項目待ち)。本節は経路が開いたときの手順であり、
**現時点で login node で強行してはならない**。

```bash
python3 -m orchestrator.campaign.p3_autonomous_workload_trial \
  --trial-id live-abc-g1 \
  --provider claude-headless \
  --workloads ycsb-a,ycsb-b,ycsb-c \
  --max-generations 1 \
  --max-wall-seconds 3600
```

**`--max-generations` は 2 以上にできない** ([T-207] / D106 残余 1 / D114)。世代を跨ぐと
前 iteration の critic 出力が次世代の生成へ効くが、その還流は `reverse_recommended` の
boolean だけで「なぜ壊れたか」を含まない (規律 3 に対する狭まり)。**D121 が設計 draft を起草したが
設計は未確定・機構は未実装**なので、引き続き 1 generation/cell に限る。**D114 でこれは機械 gate になった** — 承認上限
`MAX_APPROVED_GENERATIONS = 1` を超える値は CLI・`run_trial()`・`_run_workload()` の 3 入口で
`AutonomousTrialError` になる。既定値も `1` である。ただし `drive` / `providers` / `preview` の
注入経路と driver の直接反復は保証対象外である (D114「保証の限界」)。

`--no-build` を外すと実計測である。supervisor は起動前に競合 `ycsb_*.exe` を検査し、
CCBench を pinned commit の使い捨て worktree へ隔離する。pipeline 自身の bench lock / settle /
直前競合検査もそのまま働く。競合 process を自動 kill はしない。
加えて `numactl --interleave=all` が利用できる計測ホストでなければならない。S2 verify は
interleave を必須とするため、`numactl` のない login host で空 command に差し替えて走らせない。

最初の実計測は 1 generation/cell で correctness と measurement wiring を確認する。
2 generations 以上へ増やせるのは、D121 が列挙した多世代開放の前提条件 10 件を満たし、D96 手続を
経て、D114 の承認上限定数と境界テストを同じ変更単位で更新してからである (それまでは機械的に
拒否される)。**前提条件は現時点で 1 件も満たされていない。**
前提条件の評価規則は D121 決定 (7) から改訂されている — **P4 は無条件義務として評価し、P6 は
未実装なら失敗、実装済みで当該運転が generalized cut を主張しない場合だけ免責する。P4 と P6 を
単一の「非適用」で失敗から外してはならない。** P6 の意味的充足契約と cap-lift receipt が
未裁定・未実装である間は「実装済み」を認定する基準が無いため、**状態を未実装へ再分類するのでは
なく承認そのものを保留し**、承認上限 1 を維持する。
A/B/C は 100k records / 4 threads / extime 1 / reps 2 の配線規模で、
headline 性能や有意差を主張しない。

## 4. 出力と読み方

既定出力は `output/exploration/autonomous-trials/<trial-id>/` (D123):

- `attempts.jsonl`: append-only supervisor journal。role attempt は attempt=1 / retry=false。
  **完全な provenance (source role SHA / effective prompt SHA / session / model / token) が入るのは
  `status=valid` の attempt だけ**で、`status=invalid` は payload / envelope の path と SHA だけを持つ
- `provider/<role>/payload_*.json`, `envelope_*.json`: headless 呼び出し証拠
- `raw/raw_*.txt`: role の raw response
- `proposals/*.json`: harness へ渡した proposal と descriptor binding
- `namespace.json`: exploration namespace marker (exact bytes)。official report に この trial root を
  `--output-root` として渡す経路を fail-closed で塞ぐ。hooks が改変・削除を拒否する
- `campaigns/*`: `--no-build` 専用の隔離 campaign layout (journal-local。正式 campaign ではない)
- `report.json`: 全 cell、全 generation、stop reason、descriptor、role provenance、harness 結果

実 build 時の WAL / campaign report は `output/exploration/campaigns/<campaign-id>/` が正本 (D123)。
supervisor report はその campaign id/root を指す。`report.json` は run-finish まで含む
`attempts.jsonl` の SHA-256 を持つ。

**完全性検査 (T-295):** `report.json` は
`orchestrator/campaign/autonomous_trial_completeness.py` の検査を通らなければ書かれない。
journal の role attempt と report 本体の一次配置が完全一致しない、異常終了した cell の
generation が消える、未知の event 種別が入る、空 cell だけで `status=complete` を名乗る、
`run-start` と report の trial 同一性が食い違う、のいずれも fails-closed である。
事後の独立再検査と campaign 層 (persisted 層3 レポート ↔ fresh rebuild の深い一致) は
同 module の CLI で行う。

```bash
python3 -m orchestrator.campaign.autonomous_trial_completeness \
  <run-root>/attempts.jsonl <run-root>/report.json \
  [--campaign-output-root output]
```

この検査が塞ぐ範囲と**塞がない範囲** (どの trial を台帳へ入れるかの選択、
proposal / raw / envelope / build 成果物の bytes、層3 の任意実行) は
`docs/phase3-8c-preregistration.md` §7 が正本である。

`dry-pass` は「合成候補が diff quarantine / syntax / auditor gate を通り、build 手前まで配線された」
だけを意味する。correctness、性能、workload specialization の証拠ではない。

## 5. 現在の科学的限界と次の実験

- YCSB A = rr50、B = rr95 は既知点。C = rr100 は read-only の exploratory negative-control
  候補だが、write conflict が無ければ trigger-gating 軸自体の signal がほぼ無い
- pilot は descriptor-on だけで、off/swapped arm をまだ持たない
- planner/coder が descriptor を受け、異なる rationale を返すだけでは因果主張にならない。
  proposal/performance の arm 差と全件報告が必要
- supervisor crash 後の in-place resume、axis-proposer による新軸 onboarding、Codex runtime
  provider、複数軸 population は MVP 範囲外
- **`--run-root` を変えても campaign 状態は同一である (build 経路)。** fresh 検査の対象は外側
  `run_root` だけで、build 側の campaign root は cfg の内容 hash から決まる。同じ workload/config なら
  別の `--run-root` でも同一 campaign root になる。**ただし `--no-build` は
  `run_root/campaigns/<id>` を使うため、別 `--run-root` なら別 state になる。**
  **D114 以降、その旧 `loop_state.json` は planner 前に読まれるのでなく
  拒否される** — 既存 checkpoint を持つ layout の invocation は最初の provider 呼び出し前に
  `AutonomousTrialError` になる。crash 後の再開は `--run-root` の変更でなく**新しい trial id** で行う
  (trial は campaign ID の preimage に入るため、新 ID なら新 campaign になる)。壊れた checkpoint も
  fresh とは扱わず同じ例外になる。ただし freshness 検査と state 生成の**並行 race は保証対象外**であり、
  同じ trial/config の 2 supervisor が同時に検査を通過しうる。1 cell が stale だと
  supervisor-error となり、同 invocation の後続 workload も走らない
- `max-wall-seconds` は **hard wall でも safety 上限でもない**。時刻検査は workload と generation の
  **先頭だけ**で行うため、期限を超えても、その generation の coder・auditor・drive/build・critic は
  新たに開始される (1 回の role 呼び出しだけで最大 1200 秒)。正確には「次の境界で開始を止める
  閾値」であり、指定値を大きく超過して走りうる。正式設計が要求する bench 実時間 budget の
  独立 accounting も未実装
- **report の次の field は literal であり、その field 自体は実証ではない** — `fresh_context`、
  `observed_tool_events`、`fixed_generations`、`performance_early_stop`、`scientific_claim`。
  supervisor が書いた値をそのまま読み返しているだけで、実 process の能力・停止条件を
  測定した結果ではない (ただし `scientific_claim` は gate ではなく意図的な scope label であり、
  `fresh_context` / `observed_tool_events` の周辺には `num_turns`・session-id・permission denial・
  server-tool counter の部分検査が実在する)。これらの field を保証の証拠に使わない
- **規律 3 の還流が human-supervised loop より狭い。** 次世代の planner/coder が受けるのは
  抽象 whiteboard (direction/magnitude/result/delta_pct) と、**前世代の結果から更新した
  `current_metrics` (絶対 throughput を含む。planner は `current_perf`、coder は `baseline`、D118)** で、
  critic の attribution/recommend/avoid/uncertainty は `reverse_recommended` の boolean へ畳まれ、
  それは次世代 payload でなく driver の停止カウンタへ行く。
  「なぜ壊れたか」は次の生成入力に入らない。**前提条件が満たされるまで
  `--max-generations >= 2` で走らせない** (D106 残余 1 / D121)。正式系列 (H1/H2) は同一 generation
  budget を要求するのでこの条件で自動的に禁止側へ入る。**D114 でこれは機械 gate になった** (3 入口 +
  campaign freshness)。ただし機械化したのは「generation 予算」と「campaign state の freshness」の
  2 つだけである。承認上限の定数は producer の 3 入口に加え
  `autonomous_trial_completeness.py` の run-envelope / campaign-chain の 2 consumer gate も読む。
  存在しないのは前提条件 10 件と cap-lift receipt の評価器である。
  **D121 は設計 draft と前提条件 10 件を起草した。択一 7 件は 2026-08-03 に全件裁定されたが、
  cap-lift 可能な設計は完成していない** — 択一 1 の予算値、P6 の意味的充足と receipt、
  off アームの予算・受理集合の整合、承認上限の機械束縛、D138 が列挙する crash 回復・replicate 数・
  0 bit 証明が未確定または未実装であり、前提条件は 1 件も満たされていない
  (`output/insights/2026-08-01_t244-reflux-design/`)。
  1 generation/cell を許可する根拠も「fresh campaign の単一 invocation なら還流が起きない」であって、
  無条件ではない。

- auditor の mediated schema は **要素 field まで閉じていない**。consumer は要素が `dict` で
  あることしか検査せず、`{}`・未知キー・非文字列 field を含む要素が通る。
  「schema を object 配列へ明確化した」の射程はここまでである
- `--provider fixture` は `--no-build` 併用時だけ受理する。fixture auditor は入力を監査せず
  無条件 `pass` を返すため、実計測経路に載せない ([T-207] で fail-closed 化)

次の正式系列は H1 rr80 / H2 rr20 × descriptor on/off/swapped、同一 generation budget、
同一 correctness gate、固定 stop、全 attempt 報告である。A/B/C live はその前の operational
pilot として扱い、成功しても正式主張へ昇格させない。
