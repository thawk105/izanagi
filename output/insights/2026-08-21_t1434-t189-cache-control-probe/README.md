# [T-1434] T-189 provider cache 制御可能性の実測

- 対象: `docs/phase3-t189-model-routing-preregistration.md` §9 (cache 条件の分離、段4裁定 B5 反映)、
  総括 未解決点(3) 「provider cache 制御可能性の実測」
- 実測日: 2026-08-21 (JST)
- 実測環境: `codex-cli 0.148.0`、`claude 2.1.238 (Claude Code)`。実行主体はこのアカウントの
  サブスクリプションログイン (`env | grep -i ANTHROPIC` 空を確認済み、`ANTHROPIC_API_KEY` 等は未設定)。
- 生ログ: `output/insights/2026-08-21_t1434-t189-cache-control-probe/raw/`
  (11 回の実 CLI 呼び出しの生 stdout/stderr、`measurements-manifest.json` に呼出し対応表)
- スコープ: 実測と記録のみ。実装変更なし (規律5、command scope)。

## 結論 (headline)

**Codex CLI・Claude CLI のいずれも、provider 側 prompt cache の reset・namespace・明示的
cold/warm 切替を行う CLI 引数・環境変数を持たない。** `codex exec --help` / `codex exec resume --help`
/ `codex exec fork --help` / `claude --help` の全オプションを走査したが、cache 専用の制御フラグは
存在しない (Claude 側の `--exclude-dynamic-system-prompt-sections` は cache に言及するが目的が
異なる。後述)。

**局所的な isolation (CODEX_HOME を新規作成する、`--no-session-persistence` を付ける等) は
provider 側 cache に一切影響しない**ことを実測で確認した。cache の温度は、(a) Codex では
「同一 thread を続けているか (`resume`) 」だけで決まり、(b) Claude では「同一内容を過去に
一度でも送ったことがあるか (アカウント全体で content-addressed)」だけで決まる。どちらも
実験者が明示的に選べる制御点ではない。

**§9 の blocker (段3所見 B5) は実測により確定した。** T-189 §9 が定める「provider の cache
reset/namespace capability を実走前に実測または契約として固定できない限り、cache condition を
制御因子として扱わない」の判定は **不成立側で確定** — resource 指標 (token/wall-clock) は
cache-stratified な報告を作らず `not-applicable` とする既定 (§9 段6所見 B5 反映) を維持する。
これは D640 が pre-register した contingency を、未検証の前提から実測済みの結論へ格上げするもの
であり、新しい設計判断を追加するものではない。

## 実測 1: Codex CLI

`codex exec --json -s read-only --skip-git-repo-check -C <workdir> "<prompt>"`。
各呼出しごとに独立した `CODEX_HOME` を新規作成し、`tools/codex_reasoning_ab.py:3419-3424`
(`_run_slot_attempt` 内、`agent_workspace / "codex-home"` を新規作成して
`auth.json`/`config.toml` を `_copy_identity_file` でコピーする箇所) と同じ isolation 方式を
再現した。読み取る `usage` は `turn.completed` event の直下 (下記「傍論」参照)。

| call | codex_home | thread | 送信内容 | input_tokens | cached_input_tokens | 比率 | cache_write_input_tokens |
|---|---|---|---|---|---|---|---|
| 1 | 新規 A (初使用) | 新規 | 短い固定文 (初送) | 12969 | 9984 | 77.0% | 0 |
| 2 | A (再利用) | 新規 | 同上・同一内容 | 13177 | 9984 | 75.8% | 0 |
| 3 | 新規 B (未使用) | 新規 | call1/2 と**同一内容** | 13177 | 9984 | 75.8% | 0 |
| 4 | 新規 C (未使用) | 新規 | UUID 付き唯一内容 | 12998 | 9984 | 76.8% | 0 |
| 5 | 新規 D (未使用) | 新規 | 大ブロック (~500行、初送・唯一) | 26018 | 9984 | 38.4% | 0 |
| 6 | 新規 E (未使用) | 新規 | call5 と**同一**大ブロック | 26018 | 9984 | 38.4% | 0 |
| 7 (turn1) | 新規 F (未使用) | 新規 | 別の大ブロック (初送・唯一) | 26018 | 9984 | 38.4% | 0 |
| 8 (turn2) | F (同一、`resume`) | **同一 thread の続き** | 短い追撃発話 | 26079 | 25344 | 97.2% | 0 |

読み方:

- **call1〜4 (固定 9984 の恒常性)**: 短い固定プロンプトでも UUID 付き唯一プロンプトでも、
  新規に作った CODEX_HOME (auth.json を独立コピー) からの初回呼出しで `cached_input_tokens`
  が常に 9984 で一致する。これは codex CLI が毎回送る system prompt / tool 定義という**固定 prefix**
  がすでに warm であることを意味する。このアカウントは dev-wave で codex を継続的に使っており、
  この固定 prefix は実質的に**常時 warm** — 実験者が「このプレフィックスを cold にする」操作は
  存在しない (account 全体の codex 利用を provider の cache TTL 以上停止する以外に手段がなく、
  現実的な制御ではない)。
- **call3 が決定打**: call1/2 が使った home A とは独立の、初めて使う home B から**同一内容**を
  送っても `cached_input_tokens` は 9984 のまま変化しない。ローカル CODEX_HOME の新規性は
  provider 側 cache に一切影響しないことを直接示す。
- **call5/6 (task 内容は cross-thread で warm 化しない)**: 500 行のユニークブロックを初めて送っても
  (call5)、別の新規 home から同一ブロックを再送しても (call6)、`cached_input_tokens` は固定 prefix
  分の 9984 のまま増えない。**task 固有内容は、独立した `codex exec` 呼出し (= 新規 thread) を
  またいでは一切 cache されない** (`cache_write_input_tokens` も全呼出しで 0)。
- **call7→8 (同一 thread 内だけ warm 化する)**: `codex exec resume <thread_id>` で同一 thread を
  継続すると、直前 turn の内容 (call7 の大ブロック) はほぼ全量 (25344/26079 = 97.2%) が cache から
  読まれる。**Codex 側で warm/cold を作る唯一のレバーは「同一 thread を続けるか、新規 thread を
  切るか」であり、これは cache 専用の制御ではなく `exec` と `exec resume` のどちらを叩くかという
  実行方式そのものである。**

この機序は T-182 が観測した arm 間 cache 比率の偏り (sol `2,390,528`、luna `895,488`、
mini `984,320`、docs/phase3-t189-model-routing-preregistration.md:400-401) を素直に説明する —
arm ごとに thread 内の turn 数 (task の手数) が異なれば、within-thread cache 成長の蓄積量が
異なるのは自動的な副作用であり、意図的な cache condition ではない。

**`codex exec resume` は `codex exec` と argv 契約が異なる** (`-s`/`-C` を受け付けない、
`codex exec resume --help` で確認)。当初 `call8` は旧 argv のまま投げて rc=2 で失敗した
(`raw/call8_turn2_resume_same_thread_stderr.log`)。修正後の argv は
`codex exec resume <thread_id> --json --skip-git-repo-check <prompt>`。

## 実測 2: Claude CLI

`claude -p "ping" --agent probe --agents '{"probe":{"description":...,"prompt":<filler>,"tools":[]}}'
--output-format json --input-format text --setting-sources "" --disable-slash-commands
--strict-mcp-config --mcp-config <empty> --no-session-persistence`。
これは `orchestrator/campaign/claude_projected_provider.py:214-235` (`self.argv`) が実際に
production で使う argv パターンを踏襲したもの (tools=[]・fresh context・no-session-persistence)。
env は `orchestrator/campaign/s8b_prediction_runner.py:52` の `CLAUDE_ENV_ALLOWLIST`
(`PATH`/`HOME`/`LANG`/`LC_ALL`/`TERM`) に合わせた。

| call | filler 内容 | 呼出し | input_tokens | cache_read_input_tokens | cache_creation_input_tokens | cache tier |
|---|---|---|---|---|---|---|
| 9 | fixed-A (初送) | 独立 process | 2 | 0 | 13480 | `ephemeral_1h` |
| 10 | fixed-A (call9 と**同一内容**) | 独立 process・新規 session_id | 2 | **13480** | 0 | - |
| 11 | fixed-B (別内容) | 独立 process | 2 | 0 | 14280 | `ephemeral_1h` |

読み方:

- **call9→10 が決定打**: 完全に独立したプロセス (新しい `session_id`、`--no-session-persistence`、
  新しい neutral cwd) から同一内容を送ると、`cache_read_input_tokens` が送信内容の全量と一致する
  (13480/13480)。**プロセスの独立性・session_id の非再利用は provider 側 cache に一切影響しない。**
  一度送った内容は、送り主のプロセスが完全に別物になっても、TTL 内では確実に warm で返る。
- **call11 (対照)**: 内容を変えれば cache miss (`cache_creation_input_tokens=14280`、
  `cache_read_input_tokens=0`) に戻る — cache は content-addressed であり、プロセスや session
  ではなく**内容そのもの**に紐づく。
- 既定の cache tier は `ephemeral_1h` (1 時間) であり、Anthropic API の既定である 5 分
  ephemeral ではない。Claude Code CLI 側の選択で、CLI フラグで変更する手段は見つからなかった。
- `--exclude-dynamic-system-prompt-sections` という cache に言及する CLI フラグが存在するが
  (`claude --help`)、目的は「cwd/env/git status のような per-machine 動的セクションを system
  prompt から切り離し、**複数ユーザー間での** cache 再利用率を上げる」ことであり、単一実験内の
  cold/warm 切替とは無関係。T-189 の cold/warm 軸には使えない。

## §9 への適用

1. **cache condition を制御因子として扱わない、という段6所見 B5 の判定を維持・確定する。**
   §9 が要求する「実走前の実測」が完了し、結果は不成立 (制御不可能) — 新たな設計判断は生じない。
2. resource (token/wall-clock) 指標は、cache-stratified な報告を作らず引き続き `not-applicable`
   とする。quality 系列 (coverage・fix 巡回数・false finding rate) は cache 未確認でも
   §12 のとおり exploratory 報告を続けてよい (§9 の既定どおり)。
3. `routing_evidence_status` (D640) は本 finding だけでは変わらない。残り5論点
   (power simulation・独立 custodian・stage2/5 downstream replayer・task catalog+独立分類者・
   price snapshot) は引き続き未着手であり `inconclusive` のまま。

## 傍論 (この wave の scope 外、follow-up 候補として記録するのみ)

**`tools/codex_reasoning_ab.py` の token 検証コードが期待するイベント名と、実測した codex-cli
0.148.0 の `--json` 出力の実イベント名が一致しない可能性がある。** 本 wave の実測 (`raw/step1_stdout.jsonl`
等) では `codex exec --json` は `thread.started` → `turn.started` → `item.completed` →
`turn.completed` (usage はここに直接埋め込み) という 4 種のみを返した。一方
`tools/codex_reasoning_ab.py:4431` (`_event_payloads(rows, "token_count")`) と
`tools/codex_reasoning_ab.py:4487` (`_event_payloads(rows, "task_started")`) は
`token_count`/`task_started` という別名のイベントを期待するコードを持つ (`thread.started` 自体は
`tools/codex_reasoning_ab.py:3947` で検査されており認識はしている)。

**この観測は実際の apparatus 実行パス (live codex 呼出しを伴う統合テストや本番 dispatch) に対して
検証しておらず、fixture/mock 経由のテストが大半を占めるなら実害は無い可能性が高い。** T-1434 Wave D
(worklog 807) は本日land済みで受入 green だったため、直ちに壊れているとは考えにくいが、
未検証のまま放置すると将来 codex-cli のバージョンが上がった際に沈黙した検出漏れになりうる。
**次の一手として、T-181/T-189 装置の所有者が live codex 呼出しパスをこの版で 1 回確認することを
推奨する** (本 wave では未実施・未確定)。

## §9 引用行番号の陳腐化について

§9 (`docs/phase3-t189-model-routing-preregistration.md:412-415`) が引用する
`tools/codex_reasoning_ab.py` の行番号 (`:2625-2646`、`:2649-2740`、`:2764-2817`、`:4427-4449`)
は、T-1434 Wave D (本日) で同ファイルが約 3000 行増えた後の現在の行番号とは一致しない
(`CODEX_HOME` の出現箇所は現在 2983/3172/3458/3999/4000/7306 行)。**本 insight の中身
(cache 制御不可能という結論) は独立した生の実測に基づくため、この陳腐化に影響されない。**
docs 側の該当行番号は本 wave の commit で本 insight への参照に置き換える。
