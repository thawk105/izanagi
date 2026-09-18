単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s1-brief.md` — 親の段 1 brief。**brief 自身も検査対象**。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s2-plan.md` — 段 2 の plan (攻撃対象)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_wave_codex.py` — 起動器 (354 行)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_wave_wait.py` の 1585〜2000 行と 330〜400 行。全文は読まない。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_waves/git_state.py` の 1〜230 行。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/docs/ai-provenance.md` の「必須形式」「実装面の Codex author 契約」「記録単位」節。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/docs/dev-wave/workers.md` の `## DW-S05-A` 節。読めなければ即停止。

## 依頼 (レンズ A: 正しさ境界)

これは敵対相談である。plan を守らず、**壊す入力・状態**を探せ。親 brief 自身の前提 ((P1)〜(P6)) と
実測値の一般化も検査対象である。所見は `real` / `refuted` の候補として、根拠 (file:line) と
再現条件 (どの状態でどの入力を与えると何が起きるか) を添えて書け。推測だけの所見は `unverified` と
明記する。

攻撃面 (最低限):

1. **発火条件の境界**: `--sandbox workspace-write` だけで read-only 子を完全に除外できるか。
   親 wave worktree で workspace-write を使う経路 (DW-C01「子は競合解決だけ」の mid-merge author など)
   で、親の未 commit 差分を子の commit に巻き込む事故は起きないか。`snapshot_authority(...,
   allow_mid_merge=...)` (`tools/codex_worker_launch.py:2820-2830` 付近) の存在を根拠に使え。
2. **skip 条件の穴**: detached HEAD、`main`/`master`、`MERGE_HEAD`/`REBASE_HEAD`/`CHERRY_PICK_HEAD`、
   `rev-parse --show-toplevel` ≠ `--repo-root`、index.lock。抜けている状態は何か (例: bisect、
   submodule 内 cwd、`.git` file の worktree、symlink 解決差)。
3. **fail-closed と rc**: (P1) の rc 案 (launcher rc=0 かつ commit failed → rc=2) が親の `.done` 判定
   (DW-O01「完了は `.done` と exit code だけで判定」) とどう相互作用するか。commit `skipped` を
   rc=0 で通すことは終端契約の空洞化にならないか。stdout の固定書式 1 行が log に確実に出るか
   (launcher の stdout との混在、`nohup` の buffering)。
4. **provenance**: trailer の値の出所 (receipt の `recorded_model` / `recorded_effort`) が無い・壊れて
   いる・非 ASCII のときの正規化と `unknown` fallback が `docs/ai-provenance.md` の必須形式と
   `tools/check_ai_provenance.py` の parser に受理されるか (`--message-file` 検査で確かめる案を評価)。
   `role=author` の妥当性 (残差の一部が親の `.patch` 抽出物であるとき)。
5. **冪等性と二重発火**: 起動器が commit した後に待ち手 `--commit-worktree` が走ったとき `clean` で
   no-op になるか。同一 worktree で並行に 2 本走る経路 (段 6 の並列 fix 子は別 worktree のはず) の
   競合。`git add -A` の所要 (26k file) と timeout。
6. **DW-S05-A の `<base>` 化**: `git add -A` → `git diff --cached <base> -- <所有パス>` が commit 前後で
   同じ patch を出すか。base の与え方の誤り (親が子 worktree の作成 commit を取り違える) は今と比べて
   悪化するか。
7. **規律 2 / 6**: 子の作業木内容をそのまま commit することが、汚染された内容 (指示めいた文字列) を
   branch に残すことになるが、それは「データとして記録」であり採用ではない — この線引きが plan で
   保たれているか。commit が採用・land・撤去のどれとも別であることが実装と docs で明示されるか。

各所見に「放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか」を
1 行で添えよ (示せない所見は nit)。

制約: read-only sandbox。pytest は走らせない。静的検査でよい。実装しない。予算が尽きそうなら
途中結論を出力形式どおり書いて終われ (無出力が最悪)。出力は最終メッセージ本文に全文を書け。

## 出力形式

見出しはすべて `##` (H2)。最後の節は必ず `## 総括` (`#` を 2 個)。`### 総括` と書いてはならない。

## 所見一覧 (番号、real/refuted/unverified 候補、must-fix/nit、根拠 file:line、再現条件、成果物影響)
## brief への攻撃 ((P1)〜(P6) ごと)
## 推奨する是正 (plan v2 への差分)
## 総括
