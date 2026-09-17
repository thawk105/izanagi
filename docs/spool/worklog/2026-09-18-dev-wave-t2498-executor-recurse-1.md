---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2498-executor-recurse
seq: 1
title: [T-2498] guard_bash の重量判定を script-executor の内側実行対象へ層ごとに適用した — 段 6 が深い入れ子の RecursionError → 許可の穴を捕まえ反復化して閉じ、9/9 KILLED (コード + テスト + docs、branch worktree-dev-wave-t2498-executor-recurse、変異 matrix = baseline PASSED・負例・正例 9/9 KILLED 期待 node 完全一致・等価 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「[T-2498] hooks/guard_bash.py の重量 interpreter 検出が cProfile / profile / coverage 等の
  script-executor module を挟んだ pytest 起動を素通しする件を、既存の script-executor parser が抽出した内側の実行対象へ
  同じ重量判定を再帰的に適用する形で直す (D1891)。wrapper module の列挙追加はしない。着手直前の local main から fresh
  worktree。正本 hooks/README.md の契約とテストに従う。実装面は Codex author (D95)、変異事前登録 = 内側 pytest の素通し
  変異が KILLED、直接起動の既存拒否は正例維持。規律 2 を緩めない。本題の再帰適用だけ。防護対象の拡大・追加 gate は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-18/t2498-executor-heavy-recurse/README.md`。設計判断は
  {{D:executor-inner-same-judgment}} と {{D:hooks-second-worktree-launcher}}、失敗の型は F709 の再発 (near miss)。
  実装 commit `1f0594712` / `ddb6b760f` (Codex author、第 2 worktree)、test `f94fde871` / `abee732be`、README `301dab228`。
- **着手前の実測:** 現行 main で `python3 -m pytest` は DENY、`-m cProfile / profile / pdb / trace --module / runpy /
  coverage run` 越しの pytest は全部 ALLOW (2026-09-09 の 172 秒走行の機序)。`_script_executor_targets` が repo 外 module を
  空に落とし、`_python_pytest_args` が最初の `-m` しか見ないため。
- **段 2・3 は省いた** (D1891 が plan + 別系統相談を経て設計を確定済み)。D428 が「防壁の受理集合を変える wave」と明記するので
  段 6 の敵対レビューは 2 本とも回した — この判断は正しかった (下記)。
- **段 6 レビュー A が NO-GO を出し、must-fix 2 件を閉じた。** (1) `-m cProfile` を 1,100 層重ねた 13 KB の command で段 5
  の再帰実装が `RecursionError` になり、`main()` の例外経路 (防護 path を含まない入力は rc 0) が後続 segment の `pytest -q`
  を検査せず**許可**する — `decide()` の戻り値だけを比べる反転検査では捉えられない実入口の deny→allow。親が再現 (1,100 層で
  EXC、300 層は DENY、旧版は両方 DENY)。fix A2 で層剥きを while 化し深さ O(1)、深さ上限は設けない (深い軽量形を過剰拒否
  しない)。F709 と同じ型。(2) script 形 (`-- -m pytest`、`/tmp/safe.py -mpytest`) が合成後の既存 residual で新たに拒否される
  — 直接形は旧版でも拒否 (包み形だけが穴)。契約を「内側 segment は直接形と同じ判定」と固定し、fix B2 で包み形と直接形の
  受理 bit の一致 test (7 組、値は pin しない) を足した。
- **段 6 レビュー B (GO) が M8 の識別入力を見つけた。** 層剥きを sanctioned 早期許可の後へ移す変異は corpus 上 SURVIVED 対照
  だったが、`python3 -m cProfile tools/run_tests.py -m pytest -q` (現物 D / M8 A) で非等価。fix B2 で専用 test を足し KILLED
  期待へ。内側の `-h` / `--co` が非実行と扱われないのは既存 `_pytest_nonexecuting` の境界で直接形も同じ → backlog。
- **D427 の第 2 worktree で launcher の手順差を 1 つ解いた。** 有効化前 commit (2026-08-13) の `dev_wave_codex.py` /
  `codex_worker_launch.py` は現行 argv を受けず、旧 docs 権威は superseded 済み `gpt-5.6-sol` / xhigh を導出する (2026-09-10 の
  V2 化以後、先行 wave の「両 worktree が同じ model」はもう成り立たない)。親が AGENTS.md / CLAUDE.md / docs/dev-wave を現行 main
  へ同期する docs-only commit を作り、現行 `--dry-run` の argv で launcher だけ現行版へ差し替えて起動した (同期後の第 2
  worktree で `gpt-6-astra` / `medium` を導出し配線 findings 0 を実測)。最初 `.codex/worktrees/` に作った第 2 worktree は
  EnterWorktree(path) が `.claude/worktrees/` 限定で拒否したので作り直した。
- **親の実測 (すべて親が実行)。** 単位 B の新 test を段 5 前の guard へ: 3 failed (負例) / 3 passed (正例)。統合後焦点走
  (login) は 762 passed / 41 failed で、41 件は全部 `test_codex_worker_launch` の F57 型 → 同 file を計算ノード単独再走
  211 passed (非帰属)。fix 後焦点走 5 file (計算ノード) **806 passed / 1 skipped / 0 failed**。D428 反転検査は corpus 345 → 383
  command × 4 site (両レビューの追加形と深い生成 case 入り、例外を fail-closed で別枠に数える runner): fix 前は例外 6
  (1,100 層 × 3 × LOGIN/SUSPECT)、**fix 後は deny→allow 0・例外 0**、allow→deny 90 (45 command × LOGIN/SUSPECT、大半が
  重量 module 形、script 形 7 件は直接形も拒否、`-h`/`--co` 2 件は既存境界、深い pytest 1 件)。
- **変異 matrix (scratch worktree、`run_tests.py` test_hooks 1 file、計算ノード dispatch)。** 段 5 tip で probe (10 走)、fix 後
  tip で probe (11 走)、最終 tip 301dab228 で本走 (11 走)。本走は baseline PASSED (28.1 秒)、**M1〜M9 の 9 件すべて KILLED で
  期待 node と観測 node が完全一致 (matching 10/10)**、等価 M0 (docstring) SURVIVED、MISMATCH 0、TIMEOUT 0。M8 (層剥きの
  位置) は `precedes_sanctioned_allow` だけの単一理由。M4 (`*rest` 落とし) は過剰拒否 + 2 重 wrapper 素通しの 2 理由で単独
  証拠に数えない。M6 / M7 は既存 test が守る (新規検出力に数えない)。M9 は queue 待ちで 402 秒。
- scope 外で残る: 内側の `-h` / `--co` の非実行判定 (既存境界)、`main()` の例外経路が防護対象を含まない入力の例外を
  許可へ倒す方針 (本 wave は例外を起こさない実装で閉じた)、`trace -m` 短形 (既存 option 表に無く script 扱いで保守的に拒否)。
- 段 8 (自己改善): 候補 2 件 — (a) D427 第 2 worktree の launcher 手順差は decisions に記録 (hooks/README.md の保守境界節への
  追記は次に guard を触る wave で)、(b) D428 反転検査 runner に例外を別枠で数える経路 (F709 再発の再発検知として記録)。
  docs/dev-wave への追記は予算満杯で行わない。
- 工数: codex 子 8 本 (author 2、review 2、fix 2、focus 1、全段 `gpt-6-astra` / `medium`) + 段 2・3 を省略。親の実測: 焦点走 4
  (login 1・計算ノード 3)、probe 3 本、D428 反転検査 3 走、変異 3 走 (計算ノード 32 run)、provenance 監査は land 前に full 1 本、
  受入は land 前に 1 回。

## 次の一手差分

### 完了

- [T-2498] D1891 の実装を着地した。内側 program への層ごとの適用 (反復・深さ上限なし)、直接形と同じ判定の契約、
  9/9 KILLED。
  remaining: none
  base: d22312a00fd912a3da5a4cecc92b5b393f57fc57b8f89dde88123eeab5eec7f2
