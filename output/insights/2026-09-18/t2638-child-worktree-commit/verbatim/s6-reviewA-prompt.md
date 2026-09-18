単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-integrated-v1.diff` — レビュー対象の実装差分 (Codex author が子 worktree で書き、親が所有 path 限定 patch として wave worktree へ展開したもの。**commit 前**の作業木差分。親は `git apply` だけを行い、内容は変えていない)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-docs.diff` — 親が編集・commit 済みの docs 差分 (`docs/dev-wave/workers.md` DW-S05-A/B/C、commit 1978fe640)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s4-adjudication.md` — 段 4 裁定 (実装の正本。plan v2 §2、テスト §2.5、変異登録 §3)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s5-author-1.md` — 実装子の最終報告 (未実走の申告を含む)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s5-focus-run.log` — 親が計算ノードで実走した焦点走 (3 test file) の log。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_waves/git_state.py` の 1〜330 行 (差分適用後の実体)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_wave_codex.py` (差分適用後の実体、354 行前後)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_wave_wait.py` の 1585〜2020 行と 4470〜4500 行。全文は読まない。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/docs/ai-provenance.md` の「必須形式」節。読めなければ即停止。

## 目的

これは自分たちのコード ([T-2638]、D2044 項 16 の実装) の設計・正しさレビューである。実装子 (Codex author/fix、
`sandbox=workspace-write`) の作業木の残差を、起動器 (`tools/dev_wave_codex.py`) と待ち手 (`tools/dev_wave_wait.py producer
--commit-worktree`) の終端で現在 branch へ commit する機構を足した。破棄はしない。read-only 子・dry-run・flag 無しの待ち手は
1 byte も挙動を変えないことが契約である。

## 依頼 (レンズ A: 正しさ境界と契約の実効性)

裁定 §2 に対する実装の一致を点検し、次を指摘せよ。所見は `real` / `refuted` / `unverified`、`must-fix` / `nit` を付け、
根拠 (file:line、差分の hunk)、再現条件、「放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか」を 1 行で添える。

1. **不発火の保証**: read-only 子、workspace-write の非 author/fix、dry-run、`--commit-worktree` 無しの待ち手で、Git 書込み・stdout 変化・rc 変化・receipt bytes 変化が本当に起きないか。`dev_wave_codex.main` の rc 合成 (launcher rc≠0 保持、rc=0 ∧ refused/failed → 3) の抜け。
2. **refused / deferred / failed の分類と rc**: 裁定表 (主 checkout・detached・main/master・root 不一致 = refused、操作進行中 = deferred、Git 失敗 = failed) と実装の対応。`_run` の allowlist 経由か、`GIT_COMMANDS` の追加が 5 操作だけか、hardening (`GIT_HARDENING_CONFIG`、`_git_env`) が維持されているか。
3. **provenance**: trailer が `docs/ai-provenance.md` の必須形式と `check_ai_provenance.py` の `AGENT_VALUE` (model/reasoning の `none` 拒否) を満たすか。`recorded_*` → `requested_*` → `unknown` の順序、正規化、本文への改行・`;` 混入防止。message file が repo 外に作られ削除されるか。
4. **待ち手**: DEAD 確定後にだけ 1 回呼ぶか。既存成功 outcome で refused/failed のとき receipt を公開せず fail-closed になるか。check-only 経路が不変か。`main` の配線。
5. **DW-S05-A の `<base>` 化**: `git add -A` → `git diff --cached <base> -- <所有パス>` が helper の commit 前後で同じ patch を出すことをテストが実体で固定しているか。
6. **テストの実効性**: 各テストが実体 (実 git repo、実 dispatcher、実 producer process) を名指ししているか。代役で通る緑 (F649) や揮発 payload の焼き込みが無いか。焦点走 log の結果と照合し、未実走の主張を緑と読んでいないか。
7. **裁定 §3 の変異 M0〜M14** について、各変異を殺すと登録されたテストが本当に殺すか (静的に)。殺せないものは再照準案を書け。

制約: read-only sandbox。pytest は走らせない。静的検査でよい。実装しない。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
出力は最終メッセージ本文に全文を書け。

## 出力形式

見出しはすべて `##` (H2)。最後の節は必ず `## 総括` (`#` を 2 個)。`### 総括` と書いてはならない。

## 所見一覧 (番号、real/refuted/unverified、must-fix/nit、根拠、再現条件、成果物影響)
## 変異 M0〜M14 の静的検証
## 推奨する fix
## 総括
