---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-next-tasks-command-20260908
seq: 1
title: next-tasks command を ~/.claude/commands から repo へ移して git 管理を始め、途中で見つけた main 系統 blocker (c12e25078 の gitlink 110 本) を前進修正した (docs + checker 登録 + test、branch worktree-dev-wave-next-tasks-command-20260908、変異 matrix = baseline PASSED・KILLED 2・SURVIVED 1 (M3 = interface 登録の検査空白)・MISMATCH 0・期待 node 完全一致 333/333)
---

## 本文

ユーザー指示「next-tasks スキルの所在を確認し、izanagi/.claude/commands/ 配下へ移動して git 管理を始める」。
所在は `/home/SFC/tanab/.claude/commands/next-tasks.md` (27054 bytes、sha256 10c6c0b4…9ee15) で、
bytes 同一で `.claude/commands/next-tasks.md` へ置いた。`tools/check_docs.py` は command directory と
`COMMAND_LIMITS` の完全一致を要求するので、予算 `TextLimit(27_100, 100)` と interface (frontmatter 2 key、
`$ARGUMENTS` 0 件) を登録し、合成 fixture と予算 literal の test を足した ({{D:next-tasks-command-budget}})。
Codex 側の同名 skill `~/.agents/skills/next-tasks/` は scope 外で repo 外のまま。
逐語・変異台帳・受入受領証は `output/insights/2026-09-08_next-tasks-command-relocation/`。

**wave 起動時に main の系統 blocker を見つけた。** main 先頭 c12e25078 ([T-2412] の docs commit) は、主 checkout に
cwd を残した session が `git add -A` した際に untracked の `.codex/worktrees/` 110 本を gitlink として commit したもので、
中身は gitlink だけ (message が言う台帳 json は無い)。新規 worktree の submodule 初期化が全て失敗し、全史 provenance
監査が rc=1 で全 session の land が rc=29 になる状態だった。原因 session ([T-2412] wave) は自分では reset の権限が
無く、前進修正を本 wave へ委ねた。`git rm --cached -r .codex/worktrees` と既知違反登録 (Codex author) を 1 commit
にし、全史監査が rc=0 に戻ることを確かめた ({{D:c12e25078-forward-fix}})。F100 の再発として記録した。
`.gitignore` への `.codex/worktrees/` 追記は peer 2 session から提案されたが、F599 の既裁定に反するので含めず
ユーザー裁定へ返した。主 checkout の index.lock を握っていた hung `git status` は kill せず (他 session で権限拒否された
操作の代行になるため)、約 27 分で自然終了した。

**段 2・3 は省略し、段 6 の敵対レビュー 2 本は維持した** (plan は file:line で確定していたが、checker と provenance の
受理集合が変わるため)。レンズ C の所見 3 件: 共通自己改善契約と checker の終端 pin が 3 command のまま (real、scope 外 →
裁定へ)、移設後も「本ファイル (repo 外)」の文言と `/work/1/SFC/tanab/scripts/` 絶対 path 依存が残る (real、bytes 同一の
不変条件を優先 → 裁定へ)、現物 27,054 bytes の exact assertion が予算余白を実質使えなくする (既存 3 command と同型の
pattern として維持 → 裁定へ)。レンズ D の所見 4 件: **commit A は `tools/dev_wave_land.py` の control-plane 保護
(`_verify_target_collisions` が main..tip の差分 path と `.codex/worktrees` の重なりを RC_CONTROL_PLANE=21 で無条件拒否、
`_removed_gitlinks_absent` が除去 gitlink の実 path 残存を拒否、override なし) で通常 land 経路では着地できない** (real、
bootstrap 問題。ユーザーが主 checkout で `git cherry-pick 48837186c` する手番が要る)、既知違反の ruling がユーザー未批准
(real、cherry-pick が批准を兼ねる)、母集団 pin 4 node (real、fix 子で解消)、c12e25078 を含む他 4 worktree は main 修正後に
取り込みが要る (real、報告)。nit 4 件は除去集合・登録の形状・trailer・`.gitignore` 不変更がいずれも正しいという確認。

**焦点走で既知違反台帳の母集団 pin が赤になった。** `test_check_ai_provenance.py` の 4 node が
`_known_violation_group_stdout(53, 2)` で post-baseline 件数を pin しており、登録で 3 になった。fix 子が 4 箇所を
`(53, 3)` へ追従させ、再走は 938 passed / 3 skipped。

**エージェント工数。** 段 5 実装 1 本 (45 model call)、段 6 レビュー 2 本 (レンズ C / D)、fix 1 本。段 2・3 は省略。
起動失敗 1 回 (review 段に `--reasoning` を付けて rc=2、DW-C01 の既知制約)。

## 次の一手差分

### 新規

- {{T:next-tasks-command-edit-boundary}} **P2・ユーザー裁定待ち**: repo 内 command になった
  `.claude/commands/next-tasks.md` の編集境界を決める。論点は (a) 共通自己改善契約
  (`docs/skill-self-improvement.md`) と checker の終端 pin (3 command) へ next-tasks を加えるか、
  (b) 本文の「本ファイル (repo 外) の短い手順是正はその場で直す」と `/work/1/SFC/tanab/scripts/` 絶対 path 依存を
  どう扱うか (絶対 path は memory `no-machine-coupling-in-shared-docs` と衝突)、(c) 予算を既存 3 command と同じ
  tight (現物 +46 bytes、exact-size test) にしたままでよいか、(d) Codex 側 `~/.agents/skills/next-tasks/` も repo へ
  移すか。裁定まで本文は bytes 同一のまま。
- {{T:codex-worktrees-gitignore-ruling}} **P2・ユーザー裁定待ち**: 主 checkout で `git add -A` すると
  `.codex/worktrees/` が gitlink として commit される再発 (F100) の防壁として `.gitignore` へ
  `.codex/worktrees/` を足すか。F599 と D (除外設定で隠すと変異 harness の共有 checkout 観測 bytes が変わり
  rc=125) に反するため本 wave では採らなかった。採るなら変異 harness の観測面の扱いと同時に裁定する。
