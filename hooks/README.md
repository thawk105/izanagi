# hooks — 機械的防壁 (Python)

絶対規律1・2 を書き込み時点で機械執行する最小限の hook (guard_write / guard_bash)。auditor の
事後監査に加えた第二防壁。ECC のように大量の hook は持たない。正しさ防壁はこの2本だけ
(規律5「盛らない」)。加えて、正しさ規律とは**別系統**の衛生 hook を 2 本持つ:
コンテキスト衛生 (guard_read = D35 の機械執行、hook 3 節。2026-07-15 ユーザー承認、
失敗台帳 F18) と、モデル経済衛生 (guard_agent = subagent model 明示の機械執行、hook 4 節。
2026-07-18 ユーザー承認)。

**実装ステータス: 実装済・配線済 (Phase 3 タスク3、方針 A)。** `.claude/settings.json` の PreToolUse に
4 hook を配線 (matcher = `Write|Edit|MultiEdit|NotebookEdit` / `Bash` / `Read` / `Agent`)。方針 A (D30) で hook の責務を
「明白な直接書き込みを止める最小の第二防壁」に絞り、identity の正直さ (偽 cache hit / `#ifdef`) と
観測者効果の分離 (TRACE 混入) は**一次防壁 (source_digest)** に委譲した。

**Codex へ配線済 ([T-790]、codex-cli 0.146.0 で実測)。** かつては「Codex には配線できない」としていたが、
これは現行 Codex では成り立たない。`.codex/hooks.json` の PreToolUse に `^apply_patch$` と `^Bash$` を
配線し、判定核は Claude と同じ `guard_write` / `guard_bash` を使う。payload は Claude 同型で、
shell は `tool_name: "Bash"` に正規化されるため `guard_bash` は無改造で効く。`apply_patch` だけは
`tool_input.command` に patch 全文を渡し `file_path` を持たないため、`guard_write` に専用の
directive 抽出を置き、相対 path は payload の `cwd` から絶対化する (Codex は repo の subdirectory を
cwd にできる)。`delete` と `move` の元は symlink entry を消すので lexical 判定も併せて行う。

**Codex は hook が exit 2 のときだけ止まる。** hook command 自体の失敗 (script 不在、`python3` や
`bash` の不在、例外) は `PreToolUse Failed` と表示されるだけで**素通しになる**。そのため
`.codex/hooks.json` は guard を直接呼ばず、`0` と `2` 以外をすべて `2` へ写す `hooks/codex_guard.sh` を
経由し、bootstrap 自体も解決できなければ `exit 2` とする。

**配線しただけでは守られない。** 信頼登録の無い hook は無警告で無視される。発火しているかは
`python3 tools/check_codex_hooks.py` で実測する — 設定の存在や JSON 妥当性では
緑にせず、allowed control と protected control を両方測り、`apply_patch` と `Bash` の双方が発火しなければ
非 0 とする。認証・枠・timeout・tool 未試行も非 0 で、`skip` で緑にしない。
計算ノードは直接の外部通信ができず Codex CLI の到達性も未実測のため、この gate は**ログインノードの
手動 gate** とし、受入全走へは自動登録しない。信頼の扱いは次節を正本とする。

## Codex hook trust と自動化時の bypass 契約

**trust は hooks.json の絶対パス単位で永続化される。** 承認結果は `~/.codex/config.toml` の
`[hooks.state]` に `<hooks.json の絶対パス>:pre_tool_use:<index>:<index>` を key として記録される。
したがって **main checkout の承認は worktree・使い捨て clone・temp path へ継承されない。**
信頼の無いパスの hook を Codex は**黙って外す** (エラーも警告も出ない)。
`--ephemeral` は hook の無効化を意味しない — 信頼済みパスなら ephemeral でも発火する。

この機序により、承認済みの main checkout だけが守られ、**dev-wave の codex 子 (worktree で走る) と
checker の probe (使い捨て clone で走る) は hook 無しで走っていた**。checker は構造的に rc=0 に
なれなかった。

**対処は両経路への明示 bypass である。** `tools/check_codex_hooks.py` の probe argv と
`tools/codex_worker_launch.py` の worker argv は、いずれも `--dangerously-bypass-hook-trust` を
option 領域に exact 1 件持つ。**sandbox bypass (`--dangerously-bypass-approvals-and-sandbox`) は
両経路で禁止のまま**で、argv 検査は prompt 内の substring も拒否する。
片方だけに入れてはならない — checker だけなら本番の worker が未防護のまま gate が緑になり、
launcher だけなら受入が閉じない (D294 の却下理由がそのまま実現する)。

**bypass の前に何を検証しているか。** launcher は **retry ごとに `Popen` の直前**で次を検証し、
いずれかが赤なら `LaunchError` で**起動を拒否する。flag 無し起動への fallback は無い**。

- `git -C <cwd> rev-parse --show-toplevel` が `--repo-root` と一致すること
  (Codex は `.codex/hooks.json` を cwd の project root 基準で解決するため、ここが食い違うと
  検証した file と実行される file が別物になる)。`git` 不在・非 0・timeout は fail-closed。
- `.codex/hooks.json` が regular non-symlink で、PreToolUse の配線が exact 一致すること。
- `hooks/codex_guard.sh` / `hooks/guard_write.py` / `hooks/guard_bash.py` が regular non-symlink で
  実在すること。

checker は使い捨て clone を作った**後**に同じ検証を再実行し、argv 検証も live 実行の前に通す。

**checker rc=0 が保証する範囲 (過大に読まない)。** 保証は
**「bypass 下で、その clone の配線について、一致する拒否証拠が stderr にあり、保護対象の
side effect が無い」** までである。hook に拒否された tool 呼び出しは JSON event を一切生成せず、
拒否文は stderr にのみ出るため、証拠は stderr から取る (拒否文 + handler 名 + probe ごとの nonce +
相対 path が揃い、拒否 marker の出現が exact 1)。**protected を exact 1 回試したことの証明ではない。**
rc=0 を「Codex の persisted trust が正常」とは記録しない — 意味が違う。

**launcher 側に live attestation は無い。** launcher が言えるのは「起動直前に配線が exact で、
top-level が一致した」までで、実際に hook が発火したことは測っていない。

**検証していないもの (残余リスク)。**

- `codex_guard.sh` / `guard_*.py` の **bytes / hash は検証していない**。regular file としての実在
  までである。workspace-write の子が guard 本体を書き換えた場合、以後の起動前検証は検出しない。
- 検証から `Popen` までは原子的でない (TOCTOU の窓が残る)。
- user / global config、Codex の設定探索、CLI flag の semantics は検証範囲外。
- `tools/codex_reasoning_ab.py` の直接起動経路 (`-s read-only` 固定) と、
  `tools/run_codex_role.py` → `orchestrator/codex_roles/launcher.py` の経路 (現状 runtime blocked) は
  **本節の防壁の外**である。「repo の Codex 起動を防護した」とは書けない。
- `~/.codex/config.toml` へ worktree パスの信頼を機械追記する運用は**採らない**
  (ユーザーの個人 config を機械が書き換えるため)。

**受入の記録は 3 項目に分ける。** (1) 静的配線検証の結果、(2) bypass 下の live hook 発火の実測
(`check_codex_hooks.py` の rc)、(3) 実 worker が同じ hook source を使う配線であることの根拠。
checker は pytest 全走に内包せず、**全走と直列**に走らせる (全走の隣で live codex を起動すると
既知の偽赤が出る)。

**閉じた面と開いたままの面を混同しない。** 本配線が閉じたのは Codex の `apply_patch` 経由の直接書き込みと、
Claude と同じ既知限界つきの Bash 経由である。**MCP / apps / plugins / `SubagentStart` の子の書込み面、
script file 経由・変数展開・`python3 -c`・persistent shell、および `output/s8b-freeze` への Bash 直接書き込みは
依然として開いている。** 「Codex の proof chain 防護が Claude と同等になった」とは言えない。

ただし hook adapter が完成しても、それだけでは dormant な Codex profile の再開条件を満たさない。
local file write の拒否は、親から継承される MCP / apps・connectors / skills / plugins の外部 read・write
面を閉じないためである。明示 profile selector、全 tool surface の exact allowlist、spawn と許可・拒否
tool event を使う E2E、policy 再分類が揃うまでは active 化せず **BLOCKED** とする。自然言語 final の
「hook が発火した」「権限を拒否した」という自己申告は証拠に数えない。

**3 巡の敵対検証で硬化 (2026-07-02 / 07-03 / 07-04)。** 各巡で Opus 赤チームが real finding を摘出し修正:
- 1・2 巡目 (旧 payload テキスト検査): critical GW2R-1 (コメント行連結でコメント除去器を騙し `#define TRACE`
  を素通し) 等 real 13。「テキスト検査で C++ 翻訳フェーズ・shell を完全再現するのは原理的に無理」を実証し、
  **方針 A = payload 検査を hook から削除し一次防壁へ委譲** (D30/D33)。
- 3 巡目 (方針 A 版 + 一次防壁): real 9 / known-limitation 6 / refuted 0。**critical = source_digest の
  builtin definedness (`#ifdef __x86_64__`) 偽 cache hit** — 方針 A の委譲先自身の穴 — を D34 (-undef 廃止) で
  封鎖。hook 側は絶対パス rm・改行セグメント・heredoc `<<`・symlink root fail-open・NotebookEdit decoy の
  bypass 5 件と、nm/du/tar backup の過剰拒否 3 件を修正。known-limitation 6 (docstring 明示の限界) は据え置き。

## hook 1: guard_write.py (PreToolUse: Write/Edit/MultiEdit/NotebookEdit)

成果物の proof chain を守り、coder の編集面を designated ソースに限定する (規律1・2)。**方針 A では
designated ソース内の内容は検査しない** — 何を書いても identity が正直に変わり (偽 cache hit しない)、
TRACE 混入は build 出口の一次防壁が捕える。

- **成果物への直接書き込み拒否 (規律2):** `output/campaigns/*/runs/` (WAL)・`campaign.lock`・
  `build-variants/` への Edit/Write を拒否。COMMIT/fitness を書く唯一の経路は `pipeline.evaluate()`。
  比較基盤は realpath で解決 (output/ が別ボリュームへの symlink でも fail-open しない, 3 巡目 fix)。
  campaign tree は official / exploration の閉じた 2 要素集合 (`output/campaigns` と
  `output/exploration/campaigns`) であり、同じ条件を両方へ適用する (D123)。
  `output/exploration/namespace.json` (exact path) も改変・削除・移動を拒否する — この marker が
  消えると official report が exploration root を official として受理しうるため。read は許可する。
- **編集面の限定 (規律1・2, D23/D24):** `external/ccbench/` 内は EVOLVE-BLOCK ソース
  (`source_digest.EVOLVE_BLOCK_SOURCES`。現有の対象ファイルは同定数が正本 — 軸の追加で増えるため
  ここに値を再掲しない) だけ書き込み可。`Options.cmake` 等は
  人間 template 専有 — template 改訂は `patches/` + `git apply` (Bash) 経由。NotebookEdit は notebook_path を
  優先判定 (良性 file_path decoy で管轄を外せない, 3 巡目 fix)。
- **s8b-freeze namespace の直接書き込み拒否 (F6a, C1-11):** `output/s8b-freeze/` 配下 (approval record・
  active pointer・revocation/cancellation tombstone・v2 世代 file) への Edit/Write を拒否。これは
  **誤操作抑止であって認証防壁ではない** — 発効の真正性は `s8b_ratified_freeze` の Git 内容による規約
  attestation (`AI-Agent: none` 逐語 + 導入 commit topology) が担い、hook は層に数えない (AI が `none`
  commit を作れる以上、人間性の機械証明にはならない)。誤って freeze を worktree 直書きする事故だけを止める。
- **payload 検査は方針 A で削除 (D33):** `#ifdef`/生指令/TRACE 混入/偽 cache hit の担保は、テキスト検査の
  完全性 (原理的に破れる) ではなく一次防壁 = source_digest の preprocess 後ハッシュ + #include 行 HEAD 固定 +
  build 出口の diff-of-diffs (観測者効果) + TOCTOU 再照合が担う。意味的逸脱 (骨格破壊・領域外編集) の判定は
  auditor / 人間レビュー領域。

## hook 2: guard_bash.py (PreToolUse: Bash)

guard_write が見ない Bash 経由の成果物書き込み (`echo >> wal.jsonl` 等) を塞ぐ (規律2)。

**設計 = allowlist 反転。** 書き込み経路は事実上無限で列挙しきれない (敵対レビューで多数の迂回が実証)。
読み取り専用コマンドの集合は小さく安定なので反転: **防護対象に触れるセグメントは、その head が既知の
読み取り専用でなければ拒否 (未知コマンド = fails-closed)。** shlex (punctuation_chars) でクォートを解決して
トークン単位で判定する。祖先ツリー (campaign dir / ccbench root) を丸ごと削除・移動・展開する操作
(`rm -rf`/`mv`/`git clean` 等) も、対象パスが防護ツリーと重なれば拒否。3 巡目 fix:
- 絶対パス・`~` は repo_root で相対化してから照合 (`rm -rf /abs/.../output/campaigns/c` を塞ぐ)。
- 改行はセグメント境界にする (先頭行 read-only head が後続行 writer を隠蔽するのを防ぐ)。
- here-doc `<<` は不透明構文として fails-closed (bare interpreter への流し込みを塞ぐ)。
- 純読み取り (nm/objdump/readelf/ldd/size/du/zcat 系) を allowlist に追加 (規律1 の nm 手検証を止めない)。
- tar/rsync は read (backup) / write (展開・mirror INTO) を判別 (backup を巻き込まない)。

**Pegasus の重い処理層 (正しさ防壁ではない)。** 同 hook は Pegasus ログインノードでの重量コマンドも
拒否する。admission は **`tools/pegasus/admission_registry.json` が正本**で、
`hooks/guard_bash.py` は共有 validator (`tools/pegasus_admission_registry.py`) を通した投影である
([T-522])。**registry が exact 登録した path は配置場所を問わず対象になるが、未登録 = 拒否の閉包は
`tools/pegasus/` 配下だけに残り、`tools/pegasus/` 外に登録できるのは deny 側 class だけである**
([T-639])。正本が読めない・schema に反するときは空 registry へ縮退し、`tools/pegasus/` 配下と
hook が静的に持つ非 `tools/pegasus/` 登録 path をすべて拒否する (fail-closed)。
一覧はここへ写さない (二重管理はドリフト源になる)。
射程と限界 — 一次強制は各 entry point 自身の fail-closed だが、**site gate を持たない実行体では
この hook が現行唯一の機械面である** ([T-639] で登録した `tools/claude_session_ledger.py` が該当)。
hook が新規に閉じるのは非 sanctioned な綴りだけで、Codex 子・script file 越し・`python3 -c`・
cwd 相対・変数展開・未解析 launcher・ユーザー端末・cron・subprocess の内側は原理的に見えない —
は `docs/pegasus-runbook.md` §7 と D103 / D105 を正本とする。

**raw `systemd-run` の拒否 ([T-300])。** LOGIN / SUSPECT では head が `systemd-run` の呼び出しを
拒否する。上限付き scope は `tools/run_tests.py` などが**内部で**作るものであり、hook は
subprocess の内側を見ないので raw 実行を許可する必要がない。**`_WRAPPERS` へは追加していない** —
wrapper 化すると head の解釈が変わり、これまで拒否されていた綴りが許可側へ移る回帰が生じる
(段 3 レンズが具体例を示した)。`command -v` / `-V` は所在の問い合わせなので終端 reader として通す。

## hook 3: guard_read.py (PreToolUse: Read) — コンテキスト衛生 (正しさ防壁ではない)

大きい記録ファイルの offset/limit 無し Read を止め、D35 (grep index → 部分読み) を prompt 規律から
機械執行に格上げする (2026-07-15 ユーザー承認、失敗台帳 F18)。事故 1 回の全読 (decisions.md
235KB ≈ 70K token) がセッションの利用枠を直撃するため。guard_write / guard_bash (正しさ規律の
第二防壁) とは目的も失敗方向も異なる。

- **管轄:** repo 内 `docs/` / `output/` 配下、**80KB 超**のテキストのみ。規約上の全読があり得る
  文書 (roadmap 52KB の Phase 初回全読、phase3.md 54KB、glossary 43KB) は通し、事故の主犯級
  (decisions.md / worklog アーカイブ / 監査 JSON / WAL・trace) だけ捕まえる。バイナリ族
  (.png 等、offset の概念がない) は管轄外
- **offset / limit / pages のいずれかが明示されていれば通す** — 止めるのは無指定の事故全読だけ。
  意図的な全文読みは offset 明示の分割で 1 回の再試行から可能 (サブエージェントの要約読みも同様)
- **fail-open:** hook 自身の不具合では読み取りを止めない (guard_write の fails-closed と逆 —
  読み取り事故の被害はトークンであって正しさではないため、可用性を優先)
- 既知の限界: Bash 経由の読み込み (`cat docs/decisions.md` 等) は見ない (主経路 = Read ツール
  のみ。Bash 側は CLAUDE.md 作業の進め方 5 の行動規律)。閾値以下の中型ファイルも見ない
  (D35 の grep 規律の領分)。repo 外・docs/output 外は管轄外

## hook 4: guard_agent.py (PreToolUse: Agent) — モデル経済衛生 (正しさ防壁ではない)

model 未指定の ad-hoc Agent 呼び出し (= セッション主モデル fable の暗黙継承) を、PreToolUse が
配送される surface では止める
(2026-07-18 ユーザー承認)。fable のレート制限は他モデルよりタイトで、無指定という**不作為**で
fable 子が量産されると、fable でしか担えない親セッションの裁定・統合が制限に当たる。「子の
model/effort は難易度に整合させて明示する」は prompt 規律 (memory) だったが、不作為で起きる
違反は見落としやすいため機械執行に格上げした。guard_read と同じく正しさ防壁ではない。

- **管轄:** Agent tool のみ。止めるのは「model 明示も frontmatter ピンも無い暗黙継承」だけ
- **model 明示 (非空文字列) は値を問わず許可** — fable 明示も通す。可視・意図的な選択の適否
  (fable は親の裁定と真に最難の 1〜2 エージェント限定) は規律領分で、hook は不作為のデフォルト
  だけを塞ぐ
- **named role は frontmatter の model ピンで許可:** `.claude/agents/<type>.md` (project 側 →
  user 側 `~/.claude/agents` の順で、**最初に定義を見つけた側で確定** — harness の同名解決と
  同じ優先順位。project 側が unpinned で定義する role を user 側の同名ピンで通さない) の
  frontmatter に `model:` があれば呼び出し側の明示は不要 (ピンが harness に機械適用される)。
  role 名は `[A-Za-z0-9._-]+` に限定し、path traversal で agents dir 外のファイルをピン証明に
  使わせない。全 project role が model + effort の両ピンを持つことはテストの悉皆 gate
  (`test_agent_all_project_roles_pinned`) が強制する — role を足すならピンも足す
- **fork は許可:** fork は構造的に親モデル固定 (model override 無効) で明示のしようがない。
  `subagent_type: fork` と書くこと自体が可視・意図的な選択
- **fail-open:** guard_read と同方向 — hook 自身の不具合では起動を止めない (被害はトークンで
  あって正しさではないため可用性を優先)
- 既知の限界: **Workflow の script 内 `agent()` は見えない** (Agent tool call ではなく Workflow
  内部の spawn。script 文字列の lint は brittle で偽陽性の害が大きい — `opts.model` の明示は
  memory 規律の領分)。補助として `tools/check_workflow_models.py` (standalone lint、hook 配線は
  しない — hook による起動拒否をせず、終了コードを gate に使うかは呼出側の判断) を起動前の
  自己検査・過去 script の事後監査に使える。**codex exec (Bash 経由) も管轄外** (model/reasoning は CLI フラグ。
  難易度別割当は同規律の領分)。user 側 `~/.claude/agents` のピンも許可条件に数えるため、
  project 外の role 定義が持つピンの適否までは判定しない (人間レビュー領分)。**定義ファイルを
  持たない組み込み・plugin 型** (general-purpose / Explore / `plugin:name` / statusline-setup 等)
  はピン解決ができず常に model 明示が必要 — LLM 発の呼び出しは 1 回の再試行で回復するが、
  harness 内部の自動起動フローが model 無しで呼ぶ場合は誤拒否し得る (敵対レビュー 2026-07-18、
  fail-open は hook 例外時のみでこのケースには効かない)

### hook 4 の live 発火に関する既知の限界

**観測済み事実:** 2026-07-18、Claude Code daemon 2.1.211 のバックグラウンドジョブ型セッション
(cwd = main checkout、project settings 配線) で、model 未指定の `subagent_type=general-purpose` が
拒否されず spawn した。同一セッションでは guard_bash が発火しており、hooks 全体の停止ではない。
同じ payload を手動で stdin に流すと guard_agent は正しく exit 2 になった。一方、Claude Code
2.1.212 の headless surface と使い捨てプロジェクトによる対照実験では、(a) matcher 無しの logger、
(b) repo と同形の matcher `Agent`、(c) repo と同一 command 形の guard_agent + 併設 logger の
いずれでも PreToolUse が `tool_name: "Agent"` として配送された。(c) の model 欠落呼び出しでは
logger が model 無しを記録し、guard_agent の exit 2 が spawn を阻止し、拒否メッセージも親モデルへ
逐語で返った。公式 docs でも matcher と payload の tool_name は `Agent` が正しく、hooks 設定は
live-reload である。したがって worklog 2026-07-18 (8) の snapshot 前提は現行 docs と一致しない。

**未分離の候補:** 不発側は daemon 2.1.211 + バックグラウンドジョブ型 surface、対照側は 2.1.212 +
headless surface であり、version drift と surface 固有の配送欠落を分離できていない。worktree 由来説は
不発プローブが worktree 進入前だったため refuted。user/local settings 上書き説は、user settings に
hooks が無く、同一セッションで guard_bash が発火したため弱い。

**再検証条件:** 次の新規バックグラウンドジョブ型セッションで daemon version を確認し、model 無しの
Agent 呼び出しを再試験する。拒否されれば version drift、素通りなら同 surface の配送欠落と判定する。
後者の場合の機械的防衛候補は、`permissions.deny` による Agent 全面拒否 (orchestration 全停止)、
`CLAUDE_CODE_SUBAGENT_MODEL` による子モデル強制 (named role の frontmatter ピンも上書き)、または
バックグラウンドジョブ型を使わない foreground 運用である。いずれも副作用を伴うため、適用は
ユーザー判断とする。

**再検証の結果 (2026-07-20、ユーザー裁定 B-008 により実施 — 判定 = version drift):** 新規
バックグラウンドジョブ型セッション (daemon **2.1.214**) で model 無しの `Agent` 呼び出しを 1 回
probe したところ、**guard_agent が PreToolUse で拒否し spawn は起きなかった** (拒否メッセージも
逐語で親へ返った)。すなわち 2.1.211 の不発は **version drift** であり、同 surface 固有の配送欠落
ではない。上記「機械的防衛候補」は素通り時にのみ価値が生じる条件付き候補だったため、**適用不要**
として閉じる (見送り台帳 B-009 も同時に不要化)。ただしこれは 2.1.214 の 1 点観測であり、daemon の
更新で再び drift しうる — 次に daemon major/minor が上がった新規バックグラウンドセッションで
同じ probe を再試験する。

## 既知の限界 (正直に)

これは**テキスト検査の第二防壁であり sandbox ではない**。次は原理的に見えず、一次防壁
(`source_digest` の identity 核 + `pipeline.evaluate` の fails-closed + WAL proof chain) と事後監査 (規律6) に委ねる:
- **変数展開でパスを組み立てる** (`W=wal.jsonl; echo >> $W` / `$HOME/.../output/campaigns`)。シェルの実行時
  展開は hook から追えない。`~` は expanduser で解決するが `$VAR` は不能。
- **スクリプトファイル越しの書き込み** (`bash script.sh` の中身 / `python3 x.py` 内での open+write)。
  スクリプトファイルは監査可能な作業物として Bash 実行自体は許可。
- **部分 glob** (`rm -rf out*` / `output/campaign?`): メタ文字前のリテラル prefix でしか判定できない。
- **末端の tar/rsync backup** (`tar czf b.tgz .../build-variants`): archive 出力先の上書きリスクを厳密に
  判別できないため末端 (build-variants/WAL) を touch する形は拒否したまま (cp -r/nm で代替)。ツリー (campaign
  dir) の backup は通す。
- `git commit -m "$(...)"` の heredoc: メッセージに防護トークンが入ると不透明構文判定で拒否。単一行 `-m` か
  `git commit -F <file>` で回避。
- `chmod -R 000 <campaign dir>` の権限剥奪 DoS: 末端への chmod は末端層で拒否するが祖先 dir への再帰 chmod は
  通す。ただし WAL 追記は `pipeline.evaluate` が PermissionError で fails-closed に倒れ、owner の chmod で回復可能。
- **computed include** (`#if __has_include("x.hh")`): #include 行に現れず、-nostdinc で header 未発見なら
  digest 環境で dead 化 = identity に乗らない (実ビルドで header があれば別バイナリ)。auditor + 規律6 監査領域
  (git status に `?? x.hh` + `M backoff.hh` として露出)。builtin definedness (`#ifdef __x86_64__`) の方は
  D34 で digest に反映して封鎖済み。
- **s8b-freeze は認証防壁ではない**: `output/s8b-freeze/` の Write 拒否は誤操作抑止のみ。Bash 経由の書き込み
  (`echo > output/s8b-freeze/...`) は guard_bash の防護ツリー外で通る (現状 guard_bash は campaign/ccbench
  のみ防護)。approval/active/revocation の真正性は hook でなく `s8b_ratified_freeze` の Git attestation が担う。
  Codex 側も `.codex/hooks.json` は配線済みだが (「Codex へ配線済」節)、`output/s8b-freeze` への Bash
  直接書き込みが防護ツリー外である点は Claude と同じで、ここは開いたままである。AI 偽装を脅威モデル内で
  塞ぐには allowlist 鍵署名への再裁定が要る (C1-11 の should-fix、F6 代替案 b)。
- **ハーネス自身は防護対象外**: 防護ツリーは `output/campaigns`・`output/exploration/campaigns`・
  `external/ccbench` (と marker 1 file) のみで、一次防壁の
  コード・hook 自身・`.claude/settings.json` への書き込みはどの hook も守らない。緩和は規律6 の監査 + 人間の
  コミットレビュー (機械防壁を自己参照で増やすと規律5 と衝突)。

## テスト

`orchestrator/tests/test_hooks.py` が 4 hook の判定核 (`decide()`) を直叩きし、3 巡の敵対レビューで確定した
全 finding を回帰固定する (`test_bash_finding_bypasses_all_denied` / `test_bash_round2_bypasses_denied` /
`test_bash_false_positive_fixes_allowed` / `test_symlinked_output_tree_still_protects` /
`test_notebookedit_decoy_file_path_denied` 等)。settings.json の配線 (全 matcher) と、subprocess として
stdin JSON → exit code で動く煙テスト、guard_agent の悉皆 gate (全 project role の model/effort ピン) も含む。一次防壁 (source_digest) の網羅は `test_campaign.py`
(`test_source_digest_builtin_ifdef_not_aliased_to_stock` = D34 案A の critical 回帰 等)。
