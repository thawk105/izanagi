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

**manifest を伴わない起動は既定で拒否される ([T-470] 配線 wave、U-4)。** §§3.1–3.3 はいずれも
未登録の探索起動であり、`--allow-unregistered-exploratory` を明示しないと run root 作成前に
`[u4-exploratory-opt-in]` で止まる。明示した起動は非認証であり、`launch_admission.certifying`
が false のまま journal と report に記録され、正式選択の入力にはならない。

**この opt-in は holdout 束縛 workload には使えない。** H1/H2 (`rr80` / `rr20`) に触れる起動は、
opt-in を付けても `[u4-holdout-workload]` で無条件に拒否される。正式な holdout 起動には
登録済み manifest、その manifest を導入した内容 commit と発効 commit の二段束縛
(`prereg_content_commit` / `prereg_effective_commit`。正本は事前登録文書 §1) に一致する
発効 capability、未消費の trial ID がすべて要る。**現行実装はこの二段束縛を消費しておらず、
単一の事前登録 commit 識別子しか持たない。** 現 repository の 12 述語は C10 だけが SATISFIED、
C03 が UNSATISFIED、残り 10 件が EVIDENCE_UNDEFINED である。発効は 12 述語すべての充足を要求するので、
**正式 H1/H2 起動が通ることを期待してはならない。**

### 3.1 決定論 fixture、build なし

```bash
python3 -m orchestrator.campaign.p3_autonomous_workload_trial \
  --trial-id fixture-abc-g1 \
  --provider fixture \
  --workloads ycsb-a,ycsb-b,ycsb-c \
  --max-generations 1 \
  --allow-unregistered-exploratory \
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
  --allow-unregistered-exploratory \
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
  --allow-unregistered-exploratory \
  --max-wall-seconds 3600
```

**`--max-generations` の承認上限は現在 `2` である** (D410 が D114 の上限 1 を 2 へ引き上げ、
世代間で運ぶものを閉じた第二層射影として実装した)。**D114 でこれは機械 gate になった** — 承認上限
`MAX_APPROVED_GENERATIONS` を超える値は CLI・`run_trial()`・`_run_workload()` の 3 入口で
`AutonomousTrialError` になる。**強制されるのは上限だけであり、下限ではない。**
起動側の既定値は `1` であるため、正確に `G=2` で走らせるには世代数を明示的に指定する必要がある
(事前登録文書 §4 / §7、D438 決定 (3))。以下の探索例が `--max-generations 1` を使うのは
配線確認のためであり、正式系列の形ではない。正式経路 (`provider_kind ==
"claude-headless"`) の `run_trial()` は、caller 注入 `providers` (D148) と explicit keyword の
`drive` / `preview` ([T-244] U-1、2026-08-04) を artifact 作成前に拒否する。拒否できるのは
**explicit keyword の注入だけ**であり、module 属性の再束縛、private sentinel の持込み
(introspection 経由)、sentinel を束縛した wrapper / `partial`、同一 process 並行実行中の差替え、
driver の直接反復、fixture 経路は引き続き保証対象外である (D114「保証の限界」、D148 決定 (4))。
保存済み artifact から driver の同一性を事後判定することもできない (journal / report の schema に
driver identity の field が無い)。

`--no-build` を外すと実計測である。supervisor は起動前に競合 `ycsb_*.exe` を検査し、
CCBench を pinned commit の使い捨て worktree へ隔離する。pipeline 自身の bench lock / settle /
直前競合検査もそのまま働く。競合 process を自動 kill はしない。
加えて `numactl --interleave=all` が利用できる計測ホストでなければならない。S2 verify は
interleave を必須とするため、`numactl` のない login host で空 command に差し替えて走らせない。

最初の実計測は 1 generation/cell で correctness と measurement wiring を確認する。
**以下の段落は D410 より前の状態を記した歴史記述であり、結論部分は失効している。**
現行の承認上限の正本は D410 である。

- (歴史) 2 generations 以上へ増やせるのは、D121 が列挙した多世代開放の前提条件 10 件を満たし、
  D96 手続を経て、D114 の承認上限定数と境界テストを同じ変更単位で更新してからだとされていた。
  当時**満たされているのは P10 (予算値・origin authority・軸 (iii) のユーザー裁定) の 1 件だけ**で、
  残り 9 件は満たされていないと評価していた。
- (歴史) 前提条件の評価規則は D121 決定 (7) から改訂されている — **P4 は無条件義務として評価し、
  P6 は未実装なら失敗、実装済みで当該運転が generalized cut を主張しない場合だけ免責する。
  P4 と P6 を単一の「非適用」で失敗から外してはならない。**
- **(現行) D410 が承認上限を 2 へ引き上げ、世代間で運ぶものを閉じた第二層射影として実装した。**
  したがって「承認上限 1 を維持する」という上の結論は失効している。ただし引き上げられたのは
  上限だけであり、**正確に `G=2` で走らせる責務は起動形の側にある** (事前登録文書 §4 / §7)。
A/B/C は 100k records / 4 threads / extime 1 / reps 2 の配線規模で、
headline 性能や有意差を主張しない。

## 4. 出力と読み方

既定出力は `output/exploration/autonomous-trials/<trial-id>/` (D123)。
`IZANAGI_EXPLORATION_OUTPUT_ROOT` 設定時は `--run-root` 省略の既定が
`<base>/exploration/autonomous-trials/<trial-id>/` になる ([T-422]。使い捨て worktree 配下への
materialize は拒否される):

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
  「なぜ壊れたか」は次の生成入力に入らない。**D114 でこれは機械 gate になった** (3 入口 +
  campaign freshness)。ただし機械化したのは「generation 予算」と「campaign state の freshness」の
  2 つだけである。承認上限の定数は producer の 3 入口に加え
  `autonomous_trial_completeness.py` の run-envelope / campaign-chain の 2 consumer gate も読む。
  **D410 が承認上限を 2 へ引き上げ、世代間で運ぶものを固定 key 集合の第二層射影として実装した**
  ため、「前提条件が満たされるまで 2 世代で走らせない」という旧規則 (D106 残余 1 / D121) は
  失効している。**引き上げられたのは上限だけであり、下限は機械強制されない** — 正確に `G=2` で
  走らせる責務は起動形の側にある (事前登録文書 §4 / §7、D438 決定 (3))。
  なお D410 が明示した保証の限界は不変である — 運ぶのは人間ループが運んだものの部分集合であり、
  診断 4 値と `reverse_recommended` の 1 bit は明示的に許可された情報であって、ゼロ漏洩は名乗らない。

- auditor の mediated schema は **要素 field まで閉じていない**。consumer は要素が `dict` で
  あることしか検査せず、`{}`・未知キー・非文字列 field を含む要素が通る。
  「schema を object 配列へ明確化した」の射程はここまでである
- `--provider fixture` は `--no-build` 併用時だけ受理する。fixture auditor は入力を監査せず
  無条件 `pass` を返すため、実計測経路に載せない ([T-207] で fail-closed 化)
- **workload 単位の fan-out は「1 process 1 workload の探索 pilot を N 起動する」形だけを許す**
  ([T-809] 2026-08-11 ユーザー裁定)。本体 loop (`for workload in selected:`) を割る実装はしない。
  割ってよいのは次を**すべて**満たすときに限る。(1) `--no-build` かつ
  `--allow-unregistered-exploratory` で、holdout 束縛 workload を含まない。(2) 1 process 1 workload、
  一意な `--trial-id` と、互いに異なる resolved run root。(3) 出力は **repo 外かつ git 配下でない**
  job 専用 base へ置く。推奨経路は `IZANAGI_EXPLORATION_OUTPUT_ROOT` に job 専用 base を設定して
  `--run-root` を省略することで、**git 祖先を機械的に拒否するのはこの経路だけである**
  (`dev-wave-jobs/` は自身の `.git` を持つので base に使えない)。**`--run-root` を明示すると
  この admission は走らない** — 明示経路が repo 外・非 git であることは人手確認である。
  (4) 投入前に N slot と各 slot の trial_id・workload・run root・submission nonce を固定し、
  投入直後に scheduler が返した request ID と receipt を対応する slot へ束縛して group manifest を
  完成させる (**request ID は投入結果なので事前には書けない**)。(5) 集計前に全 N slot の
  terminal state・rc と、report / journal の存在または欠落を照合する。存在する artifact は hash も
  照合する。**欠落を含む group は incomplete のまま保存し、先に終わった成功分だけで集計しない。**
  (6) N 本を「旧 1 trial と同値な 1 成果物」と呼ばない — 性能主張・正式主張・同値性主張へ
  流入させない。**これは人手確認であって機械保証ではない** (汎用の N-job verifier は存在しない)。
  割っても各 process 内の検査はそのまま働くが、**group 単位の保証は無い** — workload coverage は
  singleton report ごとの prefix / 欠落理由の検査へ縮み、wall 予算は 1 個の共有予算から N 個の
  独立予算になり、`CrossRoleSessionTracker` の session 相異検査は process 間を覆わない
  (report 間の valid `child_id` 比較では代替できない。parse 失敗 attempt の session id は
  valid provenance に現れない)。**exploratory 起動には `lifecycle-start-once` 自体が適用されない。**
  job 間の並行投入規範と build 付き fan-out の禁止は `docs/pegasus-runbook.md` §7.5 が正本
- **再投入の定義は経路で違う** (同上の裁定)。**exploratory** は新しい `--trial-id` と
  新しい `--run-root` で行う。既存 checkpoint を持つ同一 trial/config の build 再走は campaign
  freshness gate で拒否されるが、**state 生成前の crash と並行 race は覆わない**ので、
  新 ID・新 run root は機械保証ではなく必須の運用規範である。
  **registered は同一 trial_id では不可**である (`lifecycle-start-once`)。manifest は
  exact 6 trial で、受入は manifest hash との一致を要求するので、clean な再実験には
  **新しい exact-six manifest と新しい 6 ID**、すなわち再凍結とユーザー裁定が要る。
  **ただしそれは「やってよい」ではない** — 8b の裁定は crash 後の再走を認めず実験全体を
  判定不能とする。失敗系列を残したまま成功するまで新系列を作れば repeat-until-success になる。
  どの経路でも旧 request と新 request の対応を残す

次の正式系列は H1 rr80 / H2 rr20 × descriptor on/off/swapped、同一 generation budget、
同一 correctness gate、固定 stop、全 attempt 報告である。A/B/C live はその前の operational
pilot として扱い、成功しても正式主張へ昇格させない。
