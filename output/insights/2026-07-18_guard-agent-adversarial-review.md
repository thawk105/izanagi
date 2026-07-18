# guard_agent hook 敵対レビュー (opus×2) — 逐語と裁定

- 対象: hooks/guard_agent.py + .claude/settings.json 配線 + test_hooks.py guard_agent 節 + hooks/README.md hook 4 節 (基準: worktree-agent-model-guard, d0c947a からの未コミット差分)
- レンズ: A = bypass (契約すり抜け)、B = 偽陽性 + ドキュメント整合。いずれも opus、独立コンテキスト、decide() を実測攻撃
- 裁定者: 親セッション (fable)。F20 対応として逐語をここに凍結

## レビュー B (偽陽性 + 整合レンズ) — 逐語

I have everything I need. Let me compile the review.

### 敵対レビュー結果: guard_agent.py

対象を全読し、`decide()` を python3 で直叩きして 13 role・組み込み type・plugin 形・fork・model 明示を実測。以下が裁定。

#### Finding 1 — should-fix (A: 対処案内が実行不能, かつ B: docstring と実態の食い違い)
- 箇所: `hooks/guard_agent.py:93` (拒否メッセージ option (1))、同種の主張が docstring `:12`
- 具体: メッセージは option (1)「model を明示して再試行」の中で「**effort も難易度に整合させて明示する**」と指示する。しかし Agent tool のスキーマには `effort` パラメータが存在せず (`description` / `prompt` / `subagent_type` / `model` / `isolation` のみ)、かつ `additionalProperties: false`。したがって ad-hoc な Agent 呼び出しに effort は渡せない。effort をピンできるのは named role の frontmatter (= option (2)) だけ。
- なぜ問題か: 拒否を受けた子/親がメッセージに忠実に従い、再試行の Agent 呼び出しに `effort` キーを足すと、Agent tool 側で InputValidationError になり**再試行が 1 回余計に失敗する**。誰が困るか = 拒否メッセージを額面どおり実行する呼び出し側 (特に自動オーケストレーション)。model だけ足せば最終的には通るので致命ではないが、「正確で実行可能な対処案内」を破っている。
- 提案修正: 「effort も明示する」を option (1) から外し、effort ピンは option (2)(named role frontmatter) 側の利点として記述する (`opus。(2) frontmatter に model+effort ピンのある named role …`)。

#### Finding 2 — nit (A: plugin 形 subagent_type の過剰拒否)
- 箇所: `hooks/guard_agent.py:36` (`_ROLE_NAME_RE`) と `:81`
- 具体 (実測): `subagent_type="plugin:foo"` は colon が `^[A-Za-z0-9._-]+$` に弾かれ frontmatter 探索に入らず拒否 (`allow=False` を確認)。plugin agent が自前で model を持っていても拒否される。
- なぜ問題か: plugin 由来の named agent は fable 暗黙継承ではない可能性があるのに一律拒否。ただし当リポジトリには plugin 設定が無く (`.claude/settings.json` に plugin 参照なし、`~/.claude/agents` も空)、現時点では純理論。かつ model 明示で 1 回の再試行から回復可能 (`model` 判定が subagent_type 判定より前で return するため確認済み)。
- 提案修正: plugin 名を許可する場合は regex に `:` を足し `.claude/agents` 解決を plugin 側にも広げる — もしくは「plugin agent は解決不能ゆえ model 明示を要求する」と既知の限界へ 1 行追記。

#### Finding 3 — nit (A: harness 自動起動される組み込み utility agent)
- 具体 (実測): 組み込み type (`general-purpose` / `Explore` / `Plan` / `claude-code-guide` / `claude` / `statusline-setup`) は model 無しで全て拒否。LLM が起動する type (general-purpose 等) は親が model を足して 1 回で回復可 (実測: `general-purpose+sonnet`, `Explore+haiku` は allow)。ただし `statusline-setup` のように harness の固定フローが model 無しで自動起動する場合、再試行の機会が無く「モデル経済衛生」拒否で機能が壊れ得る。
- なぜ問題か: これは harness が当該 utility agent を PreToolUse(Agent) hook 経由・model 無しで起動するか次第で、確証は無い (だから nit)。
- 提案修正: 既知の限界節に「harness 内部起動の utility agent (statusline-setup 等) は再試行不能で誤拒否し得る」を 1 行明記、または該当組み込み名を allowlist 化。

#### Finding 4 — nit (メッセージが "fable" を決め打ち)
- 箇所: `hooks/guard_agent.py:90`
- 具体: 拒否理由は常に「セッション主モデル (fable) の暗黙継承」と述べるが、hook は payload からセッション実モデルを知り得ない。opus で走る sub-orchestrator が model 無し子を起動すると継承先は opus で、メッセージの "fable" は不正確。プロジェクト規約上トップは fable なので実害は小さい。
- 提案修正: 「セッション主モデル (通常 fable)」等に緩める。

#### Refuted (検討したが問題なし)
- refuted: 13 project role 全件が許可経路を通るか — `decide()` 実測で 13 role すべて `allow=True` (model 無しでも frontmatter ピンで通過)。frontmatter は全件 `model:` + `effort:` を保持 (auditor/critic 系=opus/high、coder/calibrator/verifier=sonnet)。
- refuted: 悉皆 gate が model と effort の両方を検査するか (恒真性) — `test_agent_all_project_roles_pinned` は `_fm_has(model) and _fm_has(effort)` を要求し、`_fm_has` は「frontmatter 内に `key:` があり値が非空」を実検査。恒真でなく、README の「model + effort の両ピン」主張どおり。加えて各 role を `GA.decide` で allow 確認しており許可経路も実走 (repo_root="" → 実 repo 解決)。
- refuted: 煙テストの期待値が decide() と一致するか — `test_hook_scripts_run_as_subprocess` の guard_agent 4 ケース (general-purpose→2, model:sonnet→0, verifier→0, 壊れた json→0) はいずれも decide()/main() の実挙動と一致。verifier.md は model:sonnet を持つため 0 で整合。
- refuted: 組み込み general-purpose/Explore/Plan の拒否は false positive か — hook の意図 (model 無し ad-hoc = fable 暗黙継承を止める) に照らし、これらは model 無しなら実際に親モデルを継承するため拒否は設計どおり。`test_agent_adhoc_without_model_denied` が明示的に固定。model 明示で 1 回再試行から回復可 (実測)。
- refuted: fork / model 明示 (fable 含む) / path traversal — fork は allow、model 明示は値を問わず allow、`../evil` 等セパレータ入り subagent_type は拒否 (regex + realpath)。README・test と一致。
- refuted: fail-open の一貫性 — `main()` が `decide()` 全体を try/except で包み、内部例外は exit 0。docstring/README の「hook 自身の不具合では止めない」と整合。読めない role 定義を `_frontmatter_has_model` が False (=拒否) にするのは「ピンの証明にならない」の意図どおりで、hook バグではなく model 明示で回復可。
- refuted: README hook 4 各主張と実装 — 管轄=Agent のみ / model 明示許可 / project→user 順の frontmatter 解決 / role 名 regex / fork 許可 / 既知の限界 (Workflow 内 agent()・codex exec・user 側ピン) は実装と一致。
- refuted: 配線 (settings.json) — PreToolUse に Agent matcher で guard_agent.py が配線済み、`test_settings_json_wires_all_hooks` が Agent matcher の存在を gate。

最重要は Finding 1 (拒否メッセージが渡せない `effort` の明示を指示 → 額面実行で余分な検証エラーを誘発)。他はいずれも回復可能または当リポジトリで非該当の nit。

## レビュー B の裁定 (親)

- B-F1: **real (should-fix)** — Agent tool スキーマを親が独立確認し effort パラメータ不在を裏取り。拒否メッセージから「effort も明示」を外し、effort は named role ピン側の記述へ移す。採用
- B-F2: **real (nit)** — 修正は README 既知の限界へ 1 行 (plugin 形は解決不能ゆえ model 明示が必要)。regex 拡張は plugin 不在の現状では盛りすぎ (規律5)。採用 (文書側)
- B-F3: **real (nit)** — B-F2 と同根 (定義ファイルを持たない type はピン証明不能)。同じ 1 行に畳んで README へ。allowlist 化は憶測ベースの穴あけになるので不採用
- B-F4: **real (nit)** — 「(通常 fable)」へ緩和。採用

## レビュー A (bypass レンズ) — 逐語

All confirmed. The proposed regex fix matches `model :` / `model:\t` while still rejecting `models:` / `model_x:`.

### 裁定レポート — guard_agent.py bypass レンズ

対象の第一攻撃面である **tool_input のみで暗黙継承をすり抜ける over-allow は成立しませんでした**(critical なし)。model 非文字列・型トリック・fork 変種・traversal・fail-open 到達性はすべて正しく拒否/防御されています。実在の finding は frontmatter パーサの忠実度ギャップ(主に over-deny)と dir 優先順位の 1 件です。すべて `decide()` を import して実証済み。

#### Finding 1 — `model : sonnet`(コロン前空白)で over-deny　【should-fix】
- 攻撃入力: role 定義 frontmatter が `---\nname: x\nmodel : sonnet\n---\n`。`decide("Agent", {"subagent_type":"role"}, repo_root=<その root>)` → **allow=False**。
- 契約違反: `_frontmatter_has_model` の `re.match(r"^model:\s*\S", line)` はコロン直前の空白を許さない。しかし YAML パーサ(実測: PyYAML 5.4.1 → `{'model':'sonnet'}`)は `model : sonnet` を正当な model ピンとして解釈する。**ピンがあるのに拒否**= 正当な named role 呼び出しの over-deny。
- 提案修正 1 行: `if re.match(r"^model\s*:\s*\S", line):`(`models:`/`model_x:` の誤検出なしを実証済み)。

#### Finding 2 — dir 優先順位が OR で over-allow　【should-fix(潜在)】
- 攻撃入力: project 側 `.claude/agents/collide.md` を **unpinned**(`---\nname: collide\n---\n`)、user 側 `~/.claude/agents/collide.md` を **pinned**(`model: opus`)。`decide("Agent", {"subagent_type":"collide"})` → **allow=True**(`expanduser` を temp user dir に差し替えて実証)。
- 契約違反: harness は同名衝突を優先順位(project が user を上書き)で解決するため、実際に spawn されるのは **unpinned な project role = 親 fable 継承**。だが guard は両 dir を OR で走査し user のピンで許可 → **暗黙継承が素通り**(over-allow)。現状 repo は衝突ゼロ・user agents dir 不在のため潜在。なお guard は書かれた契約(「project → user のいずれかにピンがあれば許可」)には忠実で、契約自体が harness 優先順位と乖離している。
- 提案修正 1 行: role を**定義する最初の dir で確定**する — `_agents_dirs` を回すループを「`os.path.exists(md)` なら、その file の判定だけで break」に変える。

#### Finding 3 — UTF-8 BOM で over-deny　【nit】
- 攻撃入力: frontmatter が BOM 始まり `﻿---\n...\nmodel: sonnet\n---`。→ **allow=False**。`'﻿---'.strip()` は BOM を残し `!= "---"` になるため frontmatter 全体を無視。
- 契約違反: BOM 付き pinned role の over-deny。現 repo の role は全て BOM なしなので実発火は低い。
- 提案修正 1 行: `with open(md_path, encoding="utf-8-sig", errors="replace") as f:`(BOM を除去)。

#### Finding 4 — `...` YAML 終端マーカー無視で over-allow　【nit(要作為ファイル)】
- 攻撃入力: `---\nname: x\n...\nmodel: opus in body\n`(YAML doc-end `...` の後の本文行が `model:` で始まる)→ **allow=True**。真の frontmatter は `{name:x}` で **ピン無し**だが、guard は `...` を終端と見なさず本文まで走査してピン誤検出。
- 契約違反: ピン無し role の over-allow。ただし信頼された role ファイルを作為的に書く必要があり attacker(tool_input のみ制御)には非到達。
- 提案修正 1 行: `if line.strip() in ("---", "..."):`(`...` も終端扱い)。

#### Refuted(破れなかった攻撃)
- model 非文字列(`123`/`["sonnet"]`/`{...}`/`True`/`0`)→ 全て deny。harness の model は enum 文字列のみで非文字列は正当な明示選択になり得ず、拒否が正しい。乖離なし。
- model の奇異な文字列(`"garbage-not-an-enum"` / `" sonnet "` / `"\tsonnet\n"`)→ allow。契約「値を問わず許可」通りで、不作為でなく可視・意図的な選択のため仕様準拠。over-allow ではない。
- fork の変種(`"Fork"`/`"FORK"`/`"ﬀork"`(合字)/`"fork​"`(ゼロ幅)/`["fork"]`)→ deny。harness は fork を literal 小文字で扱い、未知 subagent_type は fork を spawn しない(継承は起きない)ため拒否は安全。空白パディング `" fork "` は `strip()` 後に正しく許可。
- traversal / セパレータ(`"../evil"` / `".claude/../.claude/agents/pinned"` / `".."` / `"."` / `"..."`)→ 全て deny。regex が `/` を排除し、ドットのみの名は無害なファイル名に解決。既存テストも網羅。
- JSON 重複キー(`subagent_type` 二重、`model` 二重)→ Python は last-wins。harness は tool_input を構造化・再直列化して渡すためワイヤ上に重複キーは生じず、生パススルーでも last-wins は大半の JSON 実装と一致。悪用可能な乖離を構成できず。
- 非 dict payload の fail-open(`[1,2,3]`/`"hello"`/`null`/`42` → rc=0)→ 仕様の fail-open。harness は常に object を送り、実 Agent spawn を非 object payload に載せられない。`tool_input: null` は `{}` に矯正され deny(rc=2)で安全。
- tool_input で decide() 例外を誘発 → fail-open allow: 構成不可。open() に至る経路は regex `[A-Za-z0-9._-]+` で門番され、到達しても OSError は捕捉。NUL 等は regex で弾かれる。
- leading blank 行(`\n---\n...`)→ deny だが、harness も frontmatter の先頭 `---` を要求する見込みで乖離なし(over-deny と断定できず refuted 扱い)。
- 配線: settings.json の matcher `"Agent"` は現行唯一の spawn ツール名と一致。取りこぼしなし。

#### 総括
主眼の「tool_input だけで暗黙継承(fable)を素通しする」経路に critical over-allow はありません。実 finding は frontmatter パーサ忠実度(Finding 1 が最も実害寄り = 正当な pinned role の over-deny)と dir 優先順位(Finding 2 = 衝突時の潜在 over-allow)で、いずれも 1 行修正可能です。

## レビュー A の裁定 (親) と修正記録

- A-F1: **real (should-fix)** — regex を `^model\s*:\s*\S` に修正。採用
- A-F2: **real (should-fix)** — 「最初に定義を見つけた dir で確定 (exists → 判定して break)」に修正。README の契約記述も harness 優先順位に合わせて更新。採用
- A-F3: **real (nit)** — `utf-8-sig` で BOM 除去。採用
- A-F4: **real (nit)** — `...` も frontmatter 終端扱い。採用

## 総合結果

- real 8 (should-fix 3: B-F1 / A-F1 / A-F2、nit 5)、critical 0、refuted 側の攻撃・観点はいずれも防御確認済み
- 全 real を修正: guard_agent.py (パーサ忠実度 3 点 + dir 優先順位 + 拒否メッセージの effort 案内撤回・(通常 fable) 緩和)、hooks/README.md (first-definition-wins 明記 + 組み込み/plugin 型の既知の限界 1 項)
- 回帰固定: `test_agent_frontmatter_parser_fidelity` (A-F1/F3/F4) と `test_agent_dir_priority_first_definition_wins` (A-F2) を追加。修正後 30 passed / 0 failed / 1 skip (既存 submodule skip)
- 工数: opus reviewer ×2 (bypass 63K / 偽陽性 68K subagent tokens)、裁定・修正は親 (fable)
