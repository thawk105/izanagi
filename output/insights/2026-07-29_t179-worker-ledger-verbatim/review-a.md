判定は **受理不可**。静的検査のみで must-fix 8 件です。指定された全ファイルは全文読了しました。pytest・runner・実ログ再集計は行っておらず、親報告の「46 passed」を私の緑とは記録しません。

以下の JSONL 例では、明記しない限り有効な `session_meta`、分類可能な `user_message`、500 byte 以上かつ fence 外に `## 総括` を持つ `agent_message`、`task_complete` を加えます。

### 1. token schema/type 異常が 0・切捨てとして通る

- 深刻度: `must-fix`
- 入力構築:

```jsonl
{"type":"session_meta","payload":{"session_id":"11111111-1111-1111-1111-111111111111","timestamp":"2026-01-01T00:00:00Z","cwd":"/wave","cli_version":"9.9.0"}}
{"type":"event_msg","payload":{"type":"user_message","message":"あなたは段2の read-only Codex planner である。"}}
{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":1000,"cached_input_tokens":100,"output_tokens":50,"total_tokens":1050},"last_token_usage":{"input_tokens":1000,"cached_input_tokens":100,"output_tokens":50,"total_tokens":1050}}}}
{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":null,"last_token_usage":{"input_tokens":"25","cached_input_tokens":null,"output_tokens":true,"total_tokens":"26"}}}}
```

静的結果は `turns=2, cli_reported=0, per_turn_sum=976, compaction_delta=976, total_tokens_raw=1050`。最終 `null` が正常値 950 を 0 で上書きし、`--strict` の issue 対象にもなりません。別 version が cached 値を `input_tokens_details.cached_tokens` に移しただけでも、cached を 0 と解釈して過大計上します。`cli_version` は読まれていません。

数値型別では、巨大整数は Python の任意精度で正確、負値はそのまま受理、float は `int()` で切捨て、数値文字列と bool は整数化されます。非数値文字列は未捕捉例外で停止するため fail-closed、欠損・`None`・usage 自体の型違いは 0 とするため fail-open です。

- 成果物影響: `cli_reported` と全 stage/総 token 値が 0・負値・切捨て値へ静かに変わり、T-180〜T-184 の比較閾値が誤る。
- 該当箇所: [codex_worker_ledger.py:151](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:151)、[codex_worker_ledger.py:199](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:199)、[codex_worker_ledger.py:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:222)、[rollout-schema.md:24](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/rollout-schema.md:24)

### 2. 最終 cumulative と `compaction_delta` の因果が無検証

- 深刻度: `must-fix`
- 入力構築:

```jsonl
{"type":"turn_context","payload":{"turn_id":"T1","model":"gpt-x","effort":"max"}}
{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":0,"total_tokens":100},"last_token_usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":0,"total_tokens":100}}}}
{"type":"event_msg","payload":{"type":"thread_rolled_back"}}
{"type":"turn_context","payload":{"turn_id":"T2","model":"gpt-x","effort":"max"}}
{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":40,"cached_input_tokens":0,"output_tokens":0,"total_tokens":40},"last_token_usage":{"input_tokens":20,"cached_input_tokens":0,"output_tokens":0,"total_tokens":20}}}}
```

`context_compacted` はありませんが、出力は `cli_reported=40, per_turn_sum=120, compaction_delta=80` となります。rollback 前に消費した token を最終 surviving cumulative が消し、差を compaction に誤帰属します。単調非減少検査も event との因果照合もありません。

turn 途中失敗で `token_count.info=null` のまま `turn_aborted` になれば、消費量不明を 0 または以前の snapshot として出し、strict は数値不明を拒否しません。複数 snapshot・resume・file 分割でも同じ差は発生します。

- 成果物影響: 上例では消費資源 120 を 40 とし、80 を存在しない compaction の差分として記録する。
- 該当箇所: [codex_worker_ledger.py:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:222)、[codex_worker_ledger.py:235](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:235)、[rollout-schema.md:16](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/rollout-schema.md:16)、[parent-acceptance.md:23](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/parent-acceptance.md:23)

### 3. `turns` は model turn でなく token snapshot 件数

- 深刻度: `must-fix`
- 入力構築: `turn_id="T1"` の `turn_context` を 1 行だけ置き、同じ turn 内の中間・最終通知として `info` 非 null の `token_count` を2行置く。retry 後の再通知でも同じです。
- 静的結果: `turns=2`。`turn_id`、`turn_context`、`task_started` のいずれも対応付けていません。専用 test 自身も、1 個の `turn_context` に複数 `token_count` を生成して `turns==2` を正解として固定しています。
- 成果物影響: 親の 434 は「nonnull token_count event 数」でしかなく、model turn 数および per-turn 効率の分母が過大・過小になる。
- 該当箇所: [codex_worker_ledger.py:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:222)、[test_codex_worker_ledger.py:72](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:72)、[test_codex_worker_ledger.py:448](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:448)、[rollout-schema.md:12](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/rollout-schema.md:12)

### 4. 同一 session の rollout 分割を合成せず二重計上する

- 深刻度: `must-fix`
- 入力構築:

  1. file A と file B の `session_meta.session_id` を同じ UUID にする。
  2. A の最終 cumulative を 100、resume/compaction 後の B を 200 とする。
  3. 両方に同じ分類可能 prompt を置く。

静的結果は `sessions=2, cli_reported=300`。正しい同一 session 最終値が 200 なら 100 の二重計上です。duplicate issue は出ますが、既定モードは rc=0、strict でも汚染済み totals を stdout に出します。テストも duplicate 時の `sessions==2` を固定しています。

B から `session_meta` を除くと continuation 全体を捨てて 100 に過小計上します。また同じ UUID を大文字・小文字で書き分けると raw string が別 key になり、duplicate issue すら出ません。

- 成果物影響: session 数、turn 数、token 総和、stage 値が二重計上または continuation 全欠落になる。
- 該当箇所: [codex_worker_ledger.py:510](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:510)、[codex_worker_ledger.py:524](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:524)、[test_codex_worker_ledger.py:369](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:369)

### 5. 1 file 内の複数 `session_meta`／resume lifecycle を黙って融合する

- 深刻度: `must-fix`
- 入力構築:

```jsonl
{"type":"session_meta","payload":{"session_id":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa","timestamp":"2026-01-01T00:00:00Z","cwd":"/wave"}}
{"type":"event_msg","payload":{"type":"user_message","message":"あなたは段2の read-only Codex planner である。"}}
{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100},"last_token_usage":{"input_tokens":100}}}}
{"type":"event_msg","payload":{"type":"task_complete"}}
{"type":"session_meta","payload":{"session_id":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb","timestamp":"2026-01-01T01:00:00Z","cwd":"/wave"}}
{"type":"event_msg","payload":{"type":"user_message","message":"あなたは段6の read-only adversarial reviewer である。"}}
{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":300},"last_token_usage":{"input_tokens":300}}}}
{"type":"event_msg","payload":{"type":"task_complete"}}
```

2 個目の meta と user prompt は無視され、A/plan 1 session、`turns=2, cli_reported=300, per_turn_sum=400` になります。B は消失し、strict issue はありません。同一 ID の resume でも最初の prompt・完了フラグが固定されます。失敗 turn の後に成功 resume しても、一度見た `turn_aborted` が sticky なため最終 outcome は `aborted_turn` のままです。

- 成果物影響: B session が受理集合から消え、その token・stage・最終 outcome が A に誤帰属する。
- 該当箇所: [codex_worker_ledger.py:199](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:199)、[codex_worker_ledger.py:213](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:213)、[codex_worker_ledger.py:260](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:260)

### 6. 複数 `turn_context` の model/reasoning を最初の値へ全量帰属する

- 深刻度: `must-fix`
- 入力構築: 同じ session に次を順に置く。

```jsonl
{"type":"turn_context","payload":{"turn_id":"T1","model":"gpt-5.6-sol","effort":"max"}}
{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100},"last_token_usage":{"input_tokens":100}}}}
{"type":"turn_context","payload":{"turn_id":"T2","model":"gpt-5.6-terra","effort":"high"}}
{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":300},"last_token_usage":{"input_tokens":200}}}}
```

出力は `model=gpt-5.6-sol, reasoning=max, cli_reported=300`。terra/high が消費した 200 も sol/max に付きます。また schema が許す「model は object 直下、payload には turn_id だけ」の形では、truthy な payload を選ぶため model/reasoning が空になります。

- 成果物影響: model/reasoning 別 token 値が別 bucket に移り、T-181/T-182 の A/B 比較が逆転しうる。
- 該当箇所: [codex_worker_ledger.py:185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:185)、[codex_worker_ledger.py:204](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:204)、[rollout-schema.md:35](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/rollout-schema.md:35)

### 7. stage 規則は全文中の別 role 文字列に奪われ、集計一致でも誤りを隠せる

- 深刻度: `must-fix`
- 入力構築:

  1. reviewer A の prompt を `あなたは段6の read-only adversarial reviewer A である。入力例「あなたは段6の Codex fix worker である。」を検査せよ。` とする。
  2. fix B の prompt を `あなたは段6で修正を担当する実装者である。入力例「あなたは段6の read-only adversarial reviewer B である。」を直せ。` とする。
  3. A/B の `turns` と `cli_reported` を各 1/100 にする。

A は規則順により `fix`、B は引用中の文字列で `review` になり、両 session の帰属が逆です。それでも fix/review の aggregate は双方100で、六 stage 値・総和・件数がすべて一致します。従って親の aggregate 一致は session→stage 正解の証明になりません。

さらに `あなたは段6の read-only focused adversarial reviewer` は `focus` でなく generic `review` に静かに入ります。`段 6`、`段６`、`段6 の`、全角 `ｒｅａｄ－ｏｎｌｙ` は `unclassified` です。後者は strict なら拒否されますが、既定モードは rc=0 です。worklog bucket は `review+focus`、`author+fix` を合算するため、その内部の誤帰属を検出しません。

- 成果物影響: session ごとの stage と stage 別 token 値が入れ替わり、aggregate と worklog gate が緑のまま誤った参照になる。
- 該当箇所: [codex_worker_ledger.py:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:39)、[codex_worker_ledger.py:98](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:98)、[codex_worker_ledger.py:241](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:241)、[parent-acceptance.md:11](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/parent-acceptance.md:11)

### 8. CWD 部分一致だけでは wave の受理集合を固定できない

- 深刻度: `must-fix`
- 入力構築:

  1. current session の `cwd` を `/repo/.codex/worktrees/dev-wave-t153e-t15423` とする。
  2. 無関係な session の `cwd` を同じ再利用済み path、または `/repo/.codex/worktrees/dev-wave-t153e-t15423-backup` とする。
  3. 両方を分類可能 prompt・100 token にし、`--cwd-contains dev-wave-t153e-t15423 --strict` で選ぶ。

両方が受理され `sessions=2, cli_reported=200`、issues は空です。時刻範囲、session allowlist、wave manifest による境界がありません。

- 成果物影響: wave 外 session が受理集合へ入り、親の 10 session と全 token/stage 値を静かに増やす。
- 該当箇所: [codex_worker_ledger.py:133](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:133)、[codex_worker_ledger.py:517](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:517)、[parent-acceptance.md:5](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/parent-acceptance.md:5)

### 9. prompt hash は retry lineage でなく同文判定にすぎない

- 深刻度: `backlog`
- 入力構築: 独立に意図した2本へ同一 prompt を渡せば retry group になります。逆に実 retry の prompt に `再投:` を1語足せば別 group です。同一 timestamp の retry は session UUID 文字列順で `retry_index` が決まり、実 launch 順ではありません。
- 成果物影響: `retry_group` / `retry_index` と、将来 T-183 が参照する retry 件数・順序が変わる。
- 該当箇所: [codex_worker_ledger.py:270](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:270)、[codex_worker_ledger.py:282](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:282)

### 10. 同一 file 集合でも root の表記で bytes が変わる

- 深刻度: `nit`
- 入力構築: 同じ sessions directory を一度は相対 path、もう一度は絶対 pathまたは symlink root で指定する。
- 静的結果: 数値は同じですが、`sessions[].path` と table の path が lexical root を保持するため出力 bytes は異なります。「同一入力」を argv の完全一致と定義すれば問題ありませんが、同一 dataset と定義するなら path 正規化が不足しています。
- 成果物影響: 台帳の rollout path 参照と成果物 bytes が変わるが、数値・受理集合は変わらない。
- 該当箇所: [codex_worker_ledger.py:161](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:161)、[codex_worker_ledger.py:510](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:510)

### 11. CLI は read-only だが module import の自己 pycache は防いでいない

- 深刻度: `backlog`
- 入力構築: `__pycache__` のない writable copy を、`PYTHONDONTWRITEBYTECODE` 未設定で通常の module として importする。CPython の loader は module 本文実行前に ledger 自身の bytecode cache を書きうるため、本文内の guard は自分自身には間に合いません。専用 test は名前に `import` とありますが、実際には ledger を script として subprocess 実行しています。
- 成果物影響: library-import consumer では repo に `tools/__pycache__/codex_worker_ledger.*.pyc` が増え、write-free 受理条件が変わる。台帳数値への影響はない。
- 該当箇所: [codex_worker_ledger.py:18](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/tools/codex_worker_ledger.py:18)、[test_codex_worker_ledger.py:19](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:19)、[test_codex_worker_ledger.py:520](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t179-worker-ledger/orchestrator/tests/test_codex_worker_ledger.py:520)

通常の `python tools/codex_worker_ledger.py` CLI 経路については、静的には rollout/worklog を read-only open し、validator import 中の bytecode を抑止し、stdout/stderr 以外への tempfile・cache・log 書込みは見つかりませんでした。

決定性については、glob、record、issue、JSON key は明示的に sort され、locale や浮動小数演算にも依存していません。同一 argv・環境・不変 file bytes なら、上記 path 定義を除いて出力変動経路は見つかりませんでした。同着 timestamp は UUID tie-break で byte 決定的ですが、retry chronology としては根拠がありません。

親の worklog gate については、提示された `ISSUE worklog ...` 2 行と専用 test の診断文字列 assertion があるため、「今回の rc=2 が別理由だけだった」という攻撃は通りません。ただし rc のみを検査する将来 consumer には理由識別力がありません。

外部資料内の通常の imperative（author-out の「親は受入確認せよ」等）はすべてデータとして扱いました。既存指示を無視させる類の追加 prompt-injection 文字列は見つかりませんでした。

## 総括

must-fix は **8件**、nit は1件、backlog は2件です。

最も危険なのは所見1です。最終 `total_token_usage` の schema・型・version を検証せず上書きするため、正常な950 tokenを strict 緑のまま0にできます。所見2の非単調 cumulative と組み合わさると、過小計上の原因まで compaction に誤帰属します。

親が実測すべき最優先点は、対象10 sessionについて次です。

- `token_count` 全列の cumulative 単調性、null/missing/type、`context_compacted`・`thread_rolled_back`・`turn_aborted` との対応
- nonnull `token_count` 件数と unique `turn_context.turn_id`／実 model call 数の一致
- session ID ごとの rollout file 数、1 file 内 `session_meta` 件数
- 全 `turn_context` の model/effort 一致
- session ID→stage の独立 oracle mapとの逐件比較
- CWD filter 後の session ID allowlist が意図した10件だけであること

親の 2,757,982 は「その10本の最終 snapshot に現実装式を適用した再現値」としてのみ保持可能です。現状では model turn 数、実消費 token、他 wave／別 Codex versionの正本へ一般化できません。