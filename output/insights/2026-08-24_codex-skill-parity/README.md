# Codex skill (rulings / dev-wave / cleanup-branches) と Claude command の内容一致

2026-08-24、branch `worktree-dev-wave-codex-skill-parity`。
base `2584907090fa3e524c4ffbf7bc4463b41cab125b`、実装 `9039c4a6` + `d96a67fd`。

本書は wave の逐語記録である。可変状態の正本は worklog 末尾と現行 phase doc であり、ここへ再掲しない。

## 1. 何を検査したか

Codex 側 `.agents/skills/{rulings,dev-wave,cleanup-branches}` が、Claude 側
`.claude/commands/*.md` と内容として一致しているか。

Codex 側 3 skill は Claude command を**複製せず**「共通 dispatcher として全文読んでそのまま実行する」
委譲型である (D280 / D564 / D102 決定(1)、`docs/skill-self-improvement.md` §routing 5 が
「同じ内容を複数の行き先へ全文複製しない」を課す)。したがって手順本体は参照で構造的に一致し、
ずれは次の 4 面にしか出ない。

1. 参照先の実在と一意性
2. overlay が述べる**事実**の正本整合
3. Claude 固有機構の Codex 翻訳の網羅
4. 規範 delta と競合時の優先順位 (段 3 レンズ B が親の 3 面定義を反証して追加した面)

## 2. 見つかった非一致と処置

| # | 面 | 内容 | 処置 |
|---|---|---|---|
| 1 | 2 | `AGENTS.md`:28-30, :48 が「Codex には hook が未配線」を前提にしていた | D294 (2026-08-11) で `.codex/hooks.json` の `apply_patch` / `Bash` へ配線済み。現行 `hooks/README.md` と checker を根拠に書き直した |
| 2 | 2 | cleanup-branches skill の「PreToolUse hook が未配線であるため」は平叙の断定で偽 | 「実効発火を仮定できない」型の正本委譲へ |
| 3 | 3 | Claude の dev-wave は `disable-model-invocation: true`、Codex 側に対応なし | `policy.allow_implicit_invocation: false` を追加し description も明示起動限定へ |
| 4 | 3 | cleanup-branches は逆に Codex 側だけが暗黙起動を禁止 | ユーザー裁定で禁止を解除し Claude へ揃えた |
| 5 | 1 | `/rulings` / `/dev-wave` の読み替え規則の指し先が command 本体に不在 | rulings は起動語宣言へ。dev-wave は `DW-CTX` に実在するため指し先を dispatcher closure へ是正し `/clear`・`claude -p`・`/loop` も保持 |
| 6 | 3 | 条件 03/04 が命じる Claude の `Write` ツールに Codex 側の対応なし | `apply_patch` tool の直接呼出し・`*** Add File:`・`git commit -F` を明記 |
| 7 | 4 | cleanup-branches の意図的な安全縮退 7 面が「裁定済みの一致例外」として無記録 | 全数表を decisions へ記録 |

## 3. 恒真だった保証の実測

`.agents/skills/dev-wave/SKILL.md` の frontmatter `description` を書き換えても
`python3 tools/check_docs.py` は **rc=0 のままだった** (親が実測)。
`_check_codex_skill_guard` の `expected_description` が dev-wave 呼出しへ渡されていなかったためである。
`CODEX_DEV_WAVE_DESCRIPTION` を新設して配線し、変異 D で単一理由の kill を確認した。

同様に、本 wave で新設した 2 契約 (自然文依頼の停止規律、防護パスを含む prompt / commit message の
Codex 側作成経路) は、当初どちらも削除しても検査が緑のまま通った。逐語 literal を
`CODEX_DEV_WAVE_SKILL_LITERALS` へ登録し、positive control を 2 件足して閉じた。

## 4. 変異台帳

固定 HEAD と spec sha256 は `mutation-main.json` / `mutation-main-out.json` (job dir) に対応する。
harness は `tools/mutation_harness.py`、`--runner-mode local`。

### 4.1 初回 spec (実ファイル変異) — 全件 SURVIVED、erratum

| ID | 変異位置 | 結果 |
|---|---|---|
| M1 | `.agents/skills/dev-wave/agents/openai.yaml` から policy block を削除 | SURVIVED |
| M2 | dev-wave SKILL の description を旧文へ | SURVIVED |
| M3 | `tools/check_docs.py` から `expected_description=` 配線を削除 | KILLED (2 node) |
| M4 | cleanup SKILL の hook 文を旧文へ | SURVIVED |
| M5 | cleanup の openai.yaml へ policy block を復活 | SURVIVED |

**原因**: 実ファイルと checker 定数の一致を見る唯一の自動テスト
`orchestrator/tests/test_check_docs.py::test_real_repo_clean` が `GROWTH_TEST_HOLDS` で
既定 skip される (`correctness_gate: true`、`release_condition: explicit-user-command-only`、
`ruling: 2026-08-12 rulings 第 3 束`)。DW-M01/M02 に従い実効 gate へ再照準した。
**この事実は本 wave が作ったものではなく既存条件である。** 帰結として、
本 wave が入れた一致は `python3 tools/check_docs.py` を明示的に走らせたときだけ機械的に守られる。

### 4.2 再照準後 (checker の判定述語を変異) — 本走

固定 HEAD `9039c4a62005665f12da3e54f4d55289a910a81e`、
spec sha256 `7a34ddafc24ddf6c39f29500327aea25b57ca29ca9fceef5f295e3180fa22f5c`。
baseline **PASSED**、**KILLED 4 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0**。

| ID | 変異位置 | status | 失敗 node 数 | 単一理由性 |
|---|---|---|---:|---|
| A | openai.yaml の完全一致判定を反転 | KILLED | 25 | 過剰決定 (冗長 gate、DW-M03) |
| B | description の exact pin 判定を反転 | KILLED | 24 | 過剰決定 (冗長 gate) |
| C | whole-file SHA-256 判定を反転 | KILLED | 25 | 過剰決定 (冗長 gate) |
| D | dev-wave への `expected_description` 配線を削除 | KILLED | 2 | **単一理由** |

A/B/C が過剰決定なのは、これらの判定述語を 3 skill の多数の契約が共有しており、
反転させると正しいファイルまで違反として出るためである。単一理由へ差し替える改造は
checker の構造を変えることになるので行わず、冗長 gate と明記した。

### 4.3 runner-mode の逸脱

`DW-M07` は本走を `--runner-mode dispatch` 既定とするが、その理由は
「runner の実行経路を変異させると local では runner が自壊し収集段が rc=16 になる」ことである。
本 wave の変異は `tools/check_docs.py` と `.agents/**` だけで runner (`tools/run_tests.py`) を
触らない。加えて実行時のキューは待ち 35・実行 54 で混雑しており、`run_tests.py` 自身が
実行場所を自動判定する。よって `local` を選んだ。

## 5. Codex 子の実行面の実測

| 観測 | 内容 |
|---|---|
| `.agents/` への書込み | sandbox 化された Codex 子は 2 経路とも拒否された。Bash 経由の `apply_patch <<'PATCH'` は guard_bash が「防護ツリーのパスと不透明構文の同居」で拒否。native `apply_patch` tool は `patch rejected: writing outside of the project; rejected by user approval settings` で拒否。同じ sandbox・同じ worktree で `tools/` と `orchestrator/` へは書けている |
| guard の発火 | 上記 1 件目は、**Codex 子で guard_bash が実際に発火した実測**である。「Codex には hook が未配線」という旧記述が偽であることの、文書ではなく実行による裏付けになった |
| `evidence_status=invalid` | workspace-write の子 3 本すべてで発生し不採用。read-only の子 4 本では 0 件。成果物はツリーに残るため親が監査して採用した |
| dispatch の不安定 | wave 中に `qstat -Q preflight rc=1` が続き、子の pytest は 3 本とも未実走。テストの実測はすべて親が行った |
| F43 (`## 総括`) | 段 2 の初回子が `### 総括` (H3) で不採用。内容 21137 bytes は妥当だった。`tools/check_codex_output.py` の `_DEFAULT_HEADING = r"^## 総括"` は H2 のみ受理する |

## 6. 残した未検証

段 2 plan が「射影資料では真偽を判定できない」とした Codex dev-wave skill の 4 命題は、
本 wave では触っていない。**「一致」と数えていない。**

- `.codex/worktrees/` 配下への worktree 作成・再利用契約
- 隔離された `codex exec` subprocess の実効性 (普通の collaboration child で代替できないこと)
- `role=author` が provenance 上の帰属に限られ native role の有効化を意味しないこと
- `tools/dev_waves` の real supervisor が Codex Skill の実行面でないこと

## 7. 親の裁定が覆された点

段 3 と段 6 のレンズが親 brief / 裁定を次の点で覆した。いずれも real として採用した。

- 「一致は安全側へ倒して取る」— 根拠不成立。暗黙起動の禁止は作業を止めず**安全手順書の到達性**だけを
  止める。`docs/failures.md` の 2026-08-01 再発 (「恒久対応の内容は正しく、経路が欠けていた」) が実例。
- 「D294 があるから未配線記述は偽」— D294 は「trust bypass は argv に入れない」と書くが、
  現行 `tools/check_codex_hooks.py` は `TRUST_BYPASS_FLAG` を必須にしている。
  D294 単独は現行契約を表さない。根拠は現行 `hooks/README.md` と checker に置き直した。
- 「`/dev-wave` の読み替えは指し先がないので削れる」— command 本体には無いが
  `docs/dev-wave/core.md` の `DW-CTX` に実在する。削らず指し先を是正した。
- 「rulings/dev-wave の hook 文は全面否定で偽」— 強すぎる。両者は「発火したと主張しない」と
  述べるだけで真である。明白な偽は `AGENTS.md` と cleanup-branches skill の断定だけだった。
- 「`.agents/**/*.yaml` は判定器が実装面としないから親が書いてよい」— 判定器の盲点は許可ではない。
  D95 の停止条項に従いユーザー裁定へ返した (結果は docs 面と確定)。
