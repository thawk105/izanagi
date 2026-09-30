# 段 1 brief — dev-wave・rulings・next-tasks の Codex 子を gpt-6-astra・reasoning=ultra へ (2026-09-30)

- 研究前進 (土台): dev-wave の全 Codex 子 (plan/consult/author/review/fix/focus)、rulings の相談、next-tasks の相談が astra・ultra で走るようにする。完了判定 = land 後の main で `tools/dev_wave_codex.py --dry-run` が review/focus/author/fix で astra・ultra を導出し、check_docs と焦点テストが緑、起動器経由の実走 1 回の受領証が `recorded_model=gpt-6-astra`・`recorded_effort=ultra`・`outcome=accepted`、委任先 (sub-agent) の model call も受領証の集計に入っている。
- 確定済みユーザー裁定 (2026-09-30): 「dev-wave, rulings, next-tasks で codex を gpt-6-astra・reasoning=ultra で使う」。D2229 を model・effort の両方で supersede。型は D2229 決定 1〜5 (slug と effort 値だけ替え、書式・導出経路・過去記録の扱いは同じ)。依頼逐語 = /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/request-md_1.txt
- 開始 gate: `check_wave_startup.py --mode fresh --external-handoff` rc=0 (startup-gate.log)。基準 = main 2094e8862731a16fb881bb382e77c00a931dfaf4。

## 親の実測 (DW-G01 / DW-O13。証跡 = liveness/ 以下)

- L1 `codex exec -m gpt-6-astra -c model_reasoning_effort=ultra --sandbox read-only` (ChatGPT ログイン、ANTHROPIC/OPENAI 系 env 0 件): rc=0、出力 PONG、header `model: gpt-6-astra` / `reasoning effort: ultra`、6.4 秒、14,191 token。
- L2 ultra は developer message に「Proactive multi-agent delegation is active」と spawn_agent 等 (最大 4 並列、子も spawn 可) を注入する。medium は「delegation no longer applies、明示依頼が無ければ spawn しない」を注入する (sol・medium の本番 rollout で確認)。
- L3 委任先は別 rollout file (名前は子の id)。子の `session_meta.session_id` は**親の id**、`id` が子の id、`source.subagent.thread_spawn.parent_thread_id` = 親、`thread_source=subagent`。exec 経由の実測で子の turn_context は model=gpt-6-astra・effort=ultra・sandbox=read-only・cwd=親と同一 (fork_turns none)。
- L4 `--json` の stdout は root の `thread.started` 1 件だけで、子の id は出ない。`collab_tool_call` item (wait 等) は出る。
- L5 起動器 (`tools/codex_worker_launch.py`) は stdout の `thread.started` からだけ session id を集め (1361〜1376 行)、`rollout-*-{id}.jsonl` を探す (1445〜1466 行)。`collab_tool_call` は `STDOUT_CONSUMED_EVENT_TYPES` 外で無視 (1356〜1360 行)。したがって**委任があっても受理される**が、子の model call・token は `max_model_calls` (100) と予算の集計に入らず、子の model/effort/cwd も照合されない (検査は落ちないが素通り)。仮に子 rollout を見つけても、1497 行の `meta_id != rollout.session_id` で session_meta_invalid になる形。
- L6 委任を設定で止める試み 3 種 (`--disable multi_agent`、`-c agents.max_threads=1` (枠表示 4→2 で読まれてはいる)、`-c agents.max_depth=0`) はいずれも spawn を止めなかった (出力 SPAWNED)。
- L7 sandbox: read-only 実行で root・子とも `touch` が `Read-only file system` で拒否 (子の rollout の sandbox_policy も read-only)。ユーザーの TUI セッションの子は親のその時点の sandbox を継承 (親より広くならない)。
- L8 guard: exec (code mode) 経由のシェル実行でも本番 rollout に `Command blocked by PreToolUse hook: [guard_bash]` がある (root)。**子への guard の直接 probe は、trust bypass flag を手打ちする形が auto mode 分類器に拒否されたため未実施**。本 wave の ultra 実走で子が保護面を触れば受動観測するが、発火の保証はない。
- L9 `tools/dev_waves/effort_levels.py` は `daemon._supervisor_digest()` の閉包内。digest は supervisor 管理下の wave の前後比較 (daemon.py 1114/1211 行) に使われる。現在 daemon は稼働 0 件 (pgrep)。

## scope (実アンカー)

| file | 箇所 | 変更 | 担当 |
|---|---|---|---|
| docs/dev-wave/operations.md | DW-O01 の `<model>` 行 (14 行) | `gpt-6-sol` → `gpt-6-astra` (V2 書式保持) | 親 (docs、段 2 前に先行) |
| docs/dev-wave/workers.md | DW-S02 5 行 / DW-S03 10 行 / DW-S05-A 24 行 / DW-S06-A 46 行 / DW-S06-C 60 行 | `reasoning=medium` → `ultra` | 親 (docs、段 5 統合後) |
| tools/check_docs.py | DW-O01 literal (372 行)、`_check_dev_wave_reasoning_effort_pins` の期待値・literal 定数 | astra / ultra へ | Codex author |
| orchestrator/tests/test_check_docs.py | 9138・9424 行 (model)、8241〜9030 行付近 (effort pin) | 同上 | Codex author |
| orchestrator/tests/test_dev_wave_launch_authority.py | 261・377 行 | astra へ (effort 期待があれば ultra) | Codex author |
| tools/dev_waves/effort_levels.py | `CODEX_REASONING_EFFORTS` と docstring | `ultra` を追加、「ultra は luna 系が非対応」を実態として追記。`CLAUDE_EFFORTS` 不変 | Codex author |
| tools/codex_worker_launch.py (+ test) | L5 の委任先会計 | (P1) 参照 | Codex author |
| /work/1/SFC/tanab/scripts/next_tasks_consult.sh (repo 外) | codex 分岐 76 行、24 行 | `-m gpt-6-astra` 明示、`CONSULT_EFFORT` 既定 high→ultra。原本を job dir へ退避 | Codex author (単位 A) → 親が設置 (P3) |

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 委任は許し、起動器が子を会計する: 子 rollout を `session_meta.session_id ∈ 既知 root id` かつ `parent_thread_id` 連鎖で発見し、root と同じく turn_context の model/effort == requested、cwd == requested を課し、model call と token を同じ上限・予算へ合算し、受領証に委任 session 数を記録する。子の証跡不正は fail-closed。対案 (P1') prompt で委任を禁じ、子を 1 件でも検出したら attempt を拒否。対案 (P1'') 権威段だけ max に留める。
- (P2) rulings の相談の effort は DW-S03 の値に従う (rulings.md 58 行は DW-O01/O02 だけを指し値を書いていない)。command は編集しない。
- (P3) repo 外 script も所在不問の Shell 資材なので実装面 (docs/ai-provenance.md「実装面の Codex author 契約」)。Codex author が worktree 内の一時 path (commit しない) に改訂版全文を書き、親が原本を job dir へ退避してから byte 一致で設置する (DW-C01「子の成果物は repo 内に書かせ、親が repo 外へ退避」)。
- (P4) この wave の段 2・3・5 は astra・medium (現行 pin、ultra は effort_levels 着地前は起動器が拒否)、段 6 review 2 本 + focus が astra・ultra の最初の起動器実走 (受領証検査 + P1 の dogfood)。

## 不変条件

- V2 行は launch_authority の `_MODEL_LINE_V2_RE` に一致し、DW-O01 の可視本文に `gpt-` slug はこの 1 件だけ。
- 正しさゲート・verifier に触れない。受理集合の変化は effort 語彙へ `ultra` 1 語の追加と、委任先会計による**締め付け** (拒否が増える方向) だけ。
- 過去記録の sol/medium/astra 表記、`.codex/role-adapters`、`~/.codex/config.toml`、`codex_reasoning_ab.py`・`t189_*`、Claude 側 effort、test_s8b の例示値は触らない。
- 計算ノードは使わない。

## 分割・段構成

- 全 9 段 (受理集合が変わるので DW-C00 の独立敵対検証子必須)。段 5 は所有素集合 2 単位: A = check_docs/test_check_docs/test_dev_wave_launch_authority/effort_levels (値の追随)、B = codex_worker_launch.py と test (委任先会計)。
