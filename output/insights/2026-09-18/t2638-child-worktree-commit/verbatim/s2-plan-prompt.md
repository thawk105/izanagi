単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s1-brief.md` — 親の段 1 brief (scope、裁定、不変条件、(P1)〜(P6))。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_wave_codex.py` — 起動器 (thin dispatcher、354 行)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_wave_wait.py` の 1585〜2000 行 (`_producer_parser`、`_parse_cli`、`_derive_producer_state`、`_producer_state_outcome`、`_publish_producer_receipt`、`wait_for_producer`) と 330〜400 行 (`_GIT_ENV_OVERRIDES`)。全文 4593 行は読まない。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/dev_waves/git_state.py` の 1〜230 行 (`GIT_COMMANDS`、`_git_env`、`_run`、`_text`)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/tools/codex_worker_launch.py` の 2632〜2660 行 (receipt の field 名) と 4834〜4930 行 (`run` の argv)。全文 4995 行は読まない。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/orchestrator/tests/test_dev_wave_codex.py` — 既存テストの書き方 (658 行)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/orchestrator/tests/test_dev_wave_wait.py` のうち `producer` を扱う test 関数 (grep `def test_.*producer` で当たる範囲だけ)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/docs/dev-wave/workers.md` の `## DW-S05-A` 節 (18〜25 行)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2638-child-worktree-commit/docs/ai-provenance.md` の「必須形式」節。読めなければ即停止。

## 依頼

[T-2638] (D2044 項 16、ユーザー裁定) の実装 plan を file:line 粒度で起草せよ。brief の scope 1〜6 を
そのまま実装単位にし、変更する関数・追加する関数・追加するテスト (正例 / 負例、実体名指し) を、
`path:line` と「現状 → 変更後」で書け。

守る前提 (再裁定しない): 起動器 (`tools/dev_wave_codex.py`) と待ち手 (`tools/dev_wave_wait.py producer`)
の終端で、`--sandbox workspace-write` の子の作業木残差を現在 branch へ commit する。破棄はしない。
新しい保存 framework・台帳・schema・一般化は作らない。read-only 子では絶対に発火しない。

plan に必ず含める項目:

1. 共有 helper の置き場 (既存 `tools/dev_waves/git_state.py` へ追加 vs 小さな新 module) の択一と理由。
   `git_state._run` は `GIT_COMMANDS` allowlist 経由なので、`add -A` / `commit -F` / `symbolic-ref` /
   `rev-parse --show-toplevel` / `diff --cached --quiet` を通すのに何を足すか。`_git_env` が
   `GIT_CONFIG_GLOBAL=/dev/null` を設定するため commit identity が repo-local config に依存する点の扱い。
2. 発火判定と skip 条件の実装位置 (detached HEAD、`main`/`master`、`MERGE_HEAD`/rebase/cherry-pick
   進行中、作業木 root ≠ `--repo-root`、index.lock)。skip と failed の区別、stdout 固定書式 1 行、
   rc の扱い (brief (P1))。
3. commit message の組み立て (件名・本文・`AI-Agent` trailer)。receipt の `recorded_model` /
   `recorded_effort` → `requested_*` → `unknown` の fallback。trailer 値の文字集合
   `[a-z0-9][a-z0-9._-]*` への正規化。message file は artifact_dir 配下の tmp に書き `commit -F`。
4. 待ち手側 `--commit-worktree <abs>` の追加位置と、flag 無しで既存挙動 (receipt の bytes を含む) が
   1 byte も変わらないことの担保方法。producer 死亡確定 (done file 非空 or pid 消失) の後にだけ呼ぶ。
5. テスト計画: 実 git repo (tmp_path) で helper を通す正例 (残差あり → commit 1 つ、trailer 1 行、
   staged 空 → `clean` で commit なし)、負例 (read-only では呼ばれない、detached で skip、mid-merge で
   skip、`main` で skip、launcher rc≠0 でも commit される、rc 隠蔽なし)。monkeypatch は既存の
   `subprocess.run` seam を除き避ける (DW-O14)。
6. DW-S05-A の改訂案 (親が編集): `git diff --cached <base> --output=<f> -- <所有パス>` と終端 commit の
   1 文。L1.5 予算が 9,696 / 9,696 (空き 0) なので、同節または同層の他節で意味を保って縮約できる
   候補文を bytes 数付きで挙げよ。`codex は reasoning=medium、sandbox=workspace-write とする。` の
   行は pin されているので触らない。
7. 変異 matrix 候補 (段 4 で親が事前登録): 反転すべき述語を最低 6 件、各々「どのテストが殺すか」を添える。
8. brief の (P1)〜(P6) への異論があれば、根拠 (file:line) 付きで書け。同意なら「同意」と 1 語で。

制約: read-only sandbox なので pytest は走らせない。静的検査でよい。書き込みは一切しない。
実装はしない (plan のみ)。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
出力は最終メッセージ本文に全文を書け。

## 出力形式

見出しはすべて `##` (H2) で揃える。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 変更面 (file:line 表)
## helper 設計
## 発火判定と rc
## commit message
## 待ち手
## テスト計画
## DW-S05-A 改訂案と予算相殺
## 変異候補
## brief への異論
## 総括
