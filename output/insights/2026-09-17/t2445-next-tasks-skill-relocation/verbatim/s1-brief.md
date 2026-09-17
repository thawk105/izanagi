## 段 1 brief (親)

**研究前進 (土台):** 研究 wave の選定入口 `/next-tasks` は D2051 (2026-09-16) で「事実は claude・判断は codex」へ
書き換えられたが、Codex 側の `$next-tasks` は repo 外 `~/.agents/skills/next-tasks/SKILL.md` (13,255 bytes、
sha256 39d3247e…、2026-09-10 版) を読んでおり、D2051 が却下 (a) とした旧規定「独立に評価し右から左に流さない」を
まだ含む (実測)。権威の指示文が version 管理外にある再現性の欠落 (項 37 の理由) を、既存 3 skill と同じ薄い
adapter で閉じる。完了判定 = (i) `.agents/skills/next-tasks/` 2 file が `.claude/commands/next-tasks.md` へ委譲し
checker の guard に登録される、(ii) `docs/skill-self-improvement.md` が next-tasks を含む、(iii) command から
`/work/1/SFC/tanab/scripts/` の絶対 path と「本ファイル (repo 外)」が消え runbook §7.2 が所在を持つ、
(iv) `python3 tools/check_docs.py` 緑。

**確定済みユーザー裁定:** D1890 (1)(2)(3)、D2051、第 20 回 /rulings 項 37 (fragment
`docs/spool/decisions/2026-09-17-rulings-all-20260917-1.md`、branch `worktree-rulings-all-20260917`、
**段 2 で補正: main `b4631a92e` で D2104 項 37 として fold 済み**。段 9 で再確認)。D744 (`.agents/**` は docs 面、親が直接編集)、
D95 (checker/test は Codex author)。

**引数の前提を覆す新事実 (段 4 で再裁定):**
- 「checker 側 `tools/check_docs.py` は登録済み」は command の予算・interface pin (entry 1352) のこと。D1890 (1) と
  T-2680 (entry 1538) が言う**終端 pin `REQUIRED_SELF_HEADINGS[3]` は `{dev-wave, cleanup-branches, rulings}` のまま**
  (check_docs.py 実測)。契約文書へ `### next-tasks` を足すと孤児 H3 で赤になる。
- 契約文書は 5,999 / 6,000 bytes (`SELF_LIMITS`)。登録には縮約 (D730/D782 手順) か上限の最小増分が要る。
- 項 37「byte 予算は既存 3 skill と同じ扱い」= 既存 3 skill は `_check_codex_skill_guard` で個別 pin
  (T-171/172/191 の先例)。同じ扱いは checker への登録を伴う。
→ 「docs / skill 文書のみ」では裁定 2 件の中身を満たせない。`tools/check_docs.py` と
  `orchestrator/tests/test_check_docs.py` への最小登録を Codex author で行う。候補生成ロジック・追加ガードレール・
  next-tasks 実行は不変で scope 外。

**割れうる前提 (親の provisional 裁定・攻撃対象):**
- (P1) 移設の形 = **薄い adapter** (rulings/SKILL.md と同型、`.claude/commands/next-tasks.md` を共通 dispatcher として
  全文読んで実行)。13 KB の逐語複製は採らない (D2051 前の却下文言を repo へ入れる・二重権威・予算不整合)。
- (P2) 契約文書の予算 = まず縮約で 6,000 に収める。収まらなければ最小増分 (D782、報告のみ)。
- (P3) checker/test 登録は scope 内 (上記の新事実)。guard 定数は sibling 同型 (limits・files・literals・openai.yaml exact)。
- (P4) `~/.agents/skills/next-tasks/` の原本は land 成功後に `~/.agents/skills-retired/next-tasks-2026-09-17/` へ
  移動 (削除しない、sha256 を insight に記録)。land 前に動かすと Codex の入口が消える。
- (P5) 絶対 path の間接化 = command 冒頭で「道具置き場 (以下 `<tools>`、所在は `docs/pegasus-runbook.md` §7.2)」を
  1 度定義し 7 箇所を `<tools>/…` に置換。runbook §7.2 に `/work/1/SFC/tanab/scripts/` を 1 行足す。

**不変条件:** 規律 2・6 不変。command の byte 上限 27,100 / 最長行 100 は動かさない。既存 3 skill の pin は不変。
候補生成手順・選定規則・出力形式の意味を変えない (文言の間接化のみ)。

**成果物:** docs (親): `.agents/skills/next-tasks/{SKILL.md,agents/openai.yaml}`、`docs/skill-self-improvement.md`、
`.claude/commands/next-tasks.md`、`docs/pegasus-runbook.md` §7.2、insight README、spool fragment (worklog / decisions)。
実装面 (Codex author): `tools/check_docs.py` (`REQUIRED_SELF_HEADINGS[3]`、`CODEX_NEXT_TASKS_SKILL_*`、guard 呼出し、
必要なら `SELF_LIMITS`)、`orchestrator/tests/test_check_docs.py` (合成 fixture・pin test・負例)。

**並列分割:** 段 5 は author 1 本 (checker + test)。docs は親。段 6 はレビュー 2 本 (レンズ A = 受理集合の変化と
恒真 pin、レンズ B = adapter が command の義務を落としていないか / 絶対 path の残存)。変異 matrix は checker の
負例 (H3 欠落・skill 予算超・openai.yaml 不一致・SKILL literal 欠落) で登録。

**受入・実測環境:** login node で `check_docs.py`・焦点走 (`orchestrator/tests/test_check_docs.py`) と変異 matrix。
受入全走は `tools/dev_wave_wait.py acceptance --lease-optional` (所在 = worklog、機体固有 = runbook §7.3)。

## 変更面 (実アンカー)

| file | anchor | 変更 |
|---|---|---|
| `.agents/skills/next-tasks/SKILL.md` | 新規 | rulings 同型の薄い adapter |
| `.agents/skills/next-tasks/agents/openai.yaml` | 新規 | 原本 (208 bytes) と同内容 |
| `docs/skill-self-improvement.md` | 冒頭段落 / `## 発火 gate` / `## command 別の終端` | next-tasks 登録、縮約 |
| `.claude/commands/next-tasks.md` | L29,31,45,60,69,204,261 (`/work/1/SFC/tanab/scripts/`)、L256-262 | 間接化・「本ファイル (repo 外)」削除 |
| `docs/pegasus-runbook.md` | `### 7.2` 末尾 | 道具置き場の所在 1 行 |
| `tools/check_docs.py` | L287-290 `SELF_LIMITS`、L709-735 sibling 定数、L833-836 `REQUIRED_SELF_HEADINGS`、L6552-6568 guard 呼出し | 登録 |
| `orchestrator/tests/test_check_docs.py` | L911-930 合成 next-tasks、L1064-1086 self_doc、L9785-9840 pin test | fixture + pin + 負例 |
