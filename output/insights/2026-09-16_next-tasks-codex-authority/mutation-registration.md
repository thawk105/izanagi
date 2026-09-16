# 変異事前登録 (実装前に凍結)

登録時刻: 2026-09-16、wave `dev-wave-next-tasks-codex-authority`。
**この登録は実装 (`orchestrator/tests/test_check_docs.py` の pin 更新) より前に書いた。**

## なぜ変異が要るようになったか

段 4 時点では実装面の差分がゼロ (`.claude/commands/next-tasks.md` は Markdown = D95 決定 2 の
実装面ではない) だったので、`DW-S04` により変異 matrix を免除していた。受入 attempt 1 が
`test_next_tasks_command_budget_literal_is_exact` で赤を返し、同 test が実 bytes を
`27_054` の literal で pin していることが判明した。pin の更新は `orchestrator/tests/` 配下の
Python なので実装面であり、免除条件が崩れた。

## 段 1 の閉包が漏れた理由 (実測)

段 1 で `git grep -n "next-tasks" -- . | grep -v "^docs/worklog.md" | head -40` を使った。
**`head -40` が 40 行で切り、`orchestrator/tests/` の hit がその外にあった。**
取り直した `git grep -n "next-tasks\|next_tasks" -- '*.py' | cat` は 8 hit を返し、
生きた pin は次の 3 つだけである。

- `tools/check_docs.py:287` — `TextLimit(27_100, 100)` (上限。変えない)
- `tools/check_docs.py:779` — `COMMAND_INTERFACES` (frontmatter・`$ARGUMENTS` 数。変えない)
- `orchestrator/tests/test_check_docs.py:2541` — **実 bytes の派生値 pin `27_054`** ← これだけ更新する

`orchestrator/tests/test_check_docs.py:911-930` は合成 fixture で実ファイルを見ない。
`docs/archive/worklog-phase3-0908-1352.md`、`output/insights/2026-09-08/...`、
`docs/decisions.md:54358` の `27054` は**測定時点の事実の記録**であり、絶対規律 7 により
現行コードとの差を理由に書き換えない。

## 登録する変異

### M1 — 実 bytes の pin が生きていることを示す

- **位置:** `.claude/commands/next-tasks.md` の本文へ可視 1 文字を追加する
  (26,903 → 26,906 bytes。日本語 1 文字 = 3 bytes)。
- **期待:** `orchestrator/tests/test_check_docs.py::test_next_tasks_command_budget_literal_is_exact`
  が **KILLED (赤)**。期待 node はこの 1 件で完全集合とする。
- **単一理由性 (`DW-M01`):** 実 bytes を pin する層はこの test だけである (上の閉包で実測)。
  前後・内側の他層は発火しない — 26,906 bytes は上限 27,100 に届かないので `check_docs.py` の
  予算検査は鳴らず、追加は既存行への 1 文字なので 100 文字上限にも触れず、`$ARGUMENTS` 数も
  frontmatter も変わらない。したがって赤理由は 1 つに絞れる。

### M2 — pin が上限そのものではなく現物を見ていることを示す

- **位置:** `tools/check_docs.py:287` の `TextLimit(27_100, 100)` を `TextLimit(27_101, 100)` にする。
- **期待:** 同じ test が **KILLED (赤)**。期待 node は M1 と同じ 1 件で完全集合。
- **単一理由性:** 同 test は上限 literal も独立に assert しており (2540 行)、上限の改竄はここで
  止まる。予算検査自体は 27,101 でも通るので、赤理由はこの pin だけである。

## 走らせ方

`DW-M05` に従い `tools/mutation_harness.py` を使う。`DW-M07` に従い本走は
`--runner-mode dispatch` + runner argv の `--force-dispatch`。baseline 緑を先に確認する。
親は変異中に編集せず、worktree へ書きうる子を起動しない。
