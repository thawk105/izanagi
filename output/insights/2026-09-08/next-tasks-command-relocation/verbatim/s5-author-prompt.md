単独段 dispatch: stage=author; sandbox=workspace-write; parent=/home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/brief-stage1.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/1d926f28/tmp/wave/brief-stage1.md (親 brief。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/check_docs.py (編集対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/orchestrator/tests/test_check_docs.py (編集対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/known_violations/25614f868c1a1b562a68072233fdf55b0be93cd1--missing-codex-author--4b6f588aa57a287a6170a707898c37e67b7b77c458fb090fbd3685a08dd46646.json (登録 file の先例。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/check_ai_provenance.py の 196〜232 行と 660〜700 行 (file 名の正規表現と canonical JSON 規則。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/.claude/commands/next-tasks.md (親が配置済みの現物。読めなければ即停止)

## 役割と境界
あなたは Codex role=author の実装子である。作業 root は
/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908 だけ。
禁止: commit、git add / rm / reset / stash / merge、docs (.md) の編集、`.codex/` 配下と `.claude/` 配下の編集、
所有外 file の編集、`tools/run_tests.py` と `python -m pytest` の起動、ネットワーク。
所有 file は次の 3 つだけ: `tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`、
`tools/known_violations/` 配下に新規作成する 1 file。
作業 tree には親が置いた staged 削除 (`.codex/worktrees/*` gitlink 110 本) と untracked の
`.claude/commands/next-tasks.md` がある。どちらも触らない。

## 作業 1 — known-violation 登録 file (1 finding 1 file)
`tools/known_violations/c12e25078ad155486c19eae633fde14e59753272--missing-codex-author--<digest>.json` を作る。
`<digest>` は file 内容 bytes の sha256 hex (先例 file で `sha256sum` と file 名が一致することを確かめてから同じ規則で付ける)。
内容は `_KNOWN_VIOLATION_DATA_FIELDS` の順 (sha, kind, value, ruling, note) で、
`json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n"` と bytes 一致する canonical UTF-8 JSON にする。
値は次を逐語で使う (改行なし、1 行の文字列):
- sha: c12e25078ad155486c19eae633fde14e59753272
- kind: missing-codex-author
- value: (空文字列)
- ruling: 系統 blocker (全 land の全史 provenance 監査 rc=1・全新規 worktree の submodule 初期化失敗) を解除するため、next-tasks command 移設 wave の親 (claude) が 2026-09-08 に登録した。原因 session ([T-2412] wave) は前進修正を本 wave へ委ねた。ユーザー承認は事後報告 (本 wave の worklog fragment)。
- note: commit c12e25078 は [T-2412] wave の親 (claude, role=manager) が主 checkout で `git add -A` を実行した際、untracked だった `.codex/worktrees/` 配下の Codex 子 worktree 110 本を gitlink (mode 160000) として誤って追加したもの。message が言う mutation-ledger-n-final.json は含まれず、変更は gitlink 110 本だけ (`git diff-tree -r --name-status c12e25078`)。`.codex/` 配下の非 .md path なので checker は実装面と判定し、Codex role=author が無いため missing-codex-author を検出した (2026-09-08 job 982930.nqsv、8802 件中 1 新規違反)。gitlink は本登録と同じ commit で `git rm --cached -r .codex/worktrees` により index から除去した。
検証: 作業 root で次の 1 行を実行し、例外なく終わり、新 file 名が列挙に含まれることを確かめる。
`python3 -c "import sys; sys.path.insert(0,'tools'); import check_ai_provenance as c; from pathlib import Path; print(sorted(c._read_known_violation_worktree(Path('tools/known_violations')).keys()))"`
例外が出たら file 名または canonical 形式の誤りなので直す。全史監査 (`python3 tools/check_ai_provenance.py`) は計算ノードへ投入されるので子は走らせない。親が走らせる。

## 作業 2 — tools/check_docs.py の登録
- `COMMAND_LIMITS` に `".claude/commands/next-tasks.md": TextLimit(27_100, 100),` を末尾へ足す。
  現物は 27054 bytes・最長行 91 chars (自分でも `wc -c` と行長で確かめる)。
- `COMMAND_INTERFACES` に次を足す:
  `".claude/commands/next-tasks.md": {"frontmatter_keys": {"description", "argument-hint"}, "arguments_count": 0},`
  (現物は `$ARGUMENTS` を使わず `$1` を使う。`docs/skill-self-improvement.md` への言及は現物にある)。
- 他のロジックは変えない。受理集合の変更はこの 2 登録だけ。

## 作業 3 — orchestrator/tests/test_check_docs.py
- `_build_min_repo` が書く合成 command に `.claude/commands/next-tasks.md` を足す (rulings の合成と同型:
  frontmatter は description / argument-hint、本文に `docs/skill-self-improvement.md` を含め、`$ARGUMENTS` は含めない)。
  これを欠くと `COMMAND_LIMITS` の 4 件目により「予算登録済み command が不在」で既存 test が大量赤になる。
- `test_dev_wave_command_budget_literal_is_exact` と同型の
  `test_next_tasks_command_budget_literal_is_exact` を足す: `COMMAND_LIMITS[rel] == TextLimit(27_100, 100)`、
  実 repo の現物が 27_054 bytes、`_pad_to_bytes(root, rel, 27_101)` で「予算 27100 bytes」の違反が出ること。
- 変異 M1 (COMMAND_LIMITS の next-tasks 行を除く) と M2 (予算値を 27_101 へ) がこの test だけで赤になることを、
  一時的に自分で変異して実測し、必ず元に戻す (戻したことを `git diff --stat` で示す)。
- test file の自走 harness (`__main__`) の対象列挙に新 test が乗ることを確かめる。

## 実走と報告
- `python3 tools/check_docs.py` を作業 root から相対 path で実行し rc を報告する (rc=0 が必要)。
- `PYTHONPATH=. python3 orchestrator/tests/test_check_docs.py` で自走し、passed / failed の件数と失敗 nodeid を報告する。
  既存赤があれば自分の変更に帰属するかを切り分けて書く。
- 完了報告は「実装済み・実走済み」「実装済み・未実走」を分けて書く。所有外の caller・共有 fixture・consumer test の
  波及可能性を静的に列挙する。scope 前の受理・拒否挙動 (次: next-tasks.md が在ると「予算未登録」で赤、無いと緑) を明記する。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 総括
最後に `## 総括` 節を必ず置き、変更 file 一覧、追加 test の nodeid、実走結果、変異 M1/M2 の実測、未実走・未確認の点を書く。
