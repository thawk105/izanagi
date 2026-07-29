# Phase 3 段 8c Runbook — workload-conditioned bounded autonomous trial

**位置づけ:** `orchestrator/campaign/p3_autonomous_workload_trial.py` は、既存の
`silo-backoff-trigger-gating` 安全 harness を Python supervisor から駆動する段 8c の
bounded MVP である。planner / coder / auditor / critic を fresh な headless Claude context
で直接呼び、workload descriptor を proposal 前に渡し、固定世代数または wall budget まで
無人継続し、全試行 journal と terminal report を生成する。

これは汎用 daemon でも正式な descriptor-conditioned synthesis 実験でもない。YCSB A/B/C
は配線 pilot であり、正式主張には
`docs/phase3-8b-descriptor-design.md` の H1/H2 × on/off/swapped を別途実装・凍結・実走する。

## 1. 何が自動化されたか

1 generation は次の順で Python が運ぶ。

1. search config から `8b-v1` workload descriptor を決定論射影し、schema と禁止キーを検査
2. descriptor + 当該 campaign の観測済み値 + abstract whiteboard を planner へ射影
3. planner の `axis/direction/magnitude` **だけ**を coder へ渡し、具体 gate 述語を合成
4. working diff を preview し、DiffQuarantine と禁止識別子 gate を先行判定
5. diff と designated context だけを auditor へ渡す
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

```bash
python3 -m orchestrator.campaign.p3_autonomous_workload_trial \
  --trial-id live-abc-g2 \
  --provider claude-headless \
  --workloads ycsb-a,ycsb-b,ycsb-c \
  --max-generations 2 \
  --max-wall-seconds 3600
```

`--no-build` を外すと実計測である。supervisor は起動前に競合 `ycsb_*.exe` を検査し、
CCBench を pinned commit の使い捨て worktree へ隔離する。pipeline 自身の bench lock / settle /
直前競合検査もそのまま働く。競合 process を自動 kill はしない。

最初の実計測は 1 generation/cell で correctness と measurement wiring を確認し、その後に
2 generations へ増やす。A/B/C は 100k records / 4 threads / extime 1 / reps 2 の配線規模で、
headline 性能や有意差を主張しない。

## 4. 出力と読み方

既定出力は `output/autonomous-trials/<trial-id>/`:

- `attempts.jsonl`: append-only supervisor journal。role attempt は attempt=1 / retry=false
- `provider/<role>/payload_*.json`, `envelope_*.json`: headless 呼び出し証拠
- `raw/raw_*.txt`: role の raw response
- `proposals/*.json`: harness へ渡した proposal と descriptor binding
- `campaigns/*`: `--no-build` 専用の隔離 campaign layout
- `report.json`: 全 cell、全 generation、stop reason、descriptor、role provenance、harness 結果

実 build 時の WAL / campaign report は通常どおり `output/campaigns/<campaign-id>/` が正本。
supervisor report はその campaign id/root を指す。`report.json` は run-finish まで含む
`attempts.jsonl` の SHA-256 を持つ。

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
- `max-wall-seconds` は supervisor 全体の上限だが、正式設計が要求する bench 実時間 budget の
  独立 accounting は未実装

次の正式系列は H1 rr80 / H2 rr20 × descriptor on/off/swapped、同一 generation budget、
同一 correctness gate、固定 stop、全 attempt 報告である。A/B/C live はその前の operational
pilot として扱い、成功しても正式主張へ昇格させない。
