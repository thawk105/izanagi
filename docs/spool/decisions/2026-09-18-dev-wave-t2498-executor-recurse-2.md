---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2498-executor-recurse
seq: 2
---

## {{D:executor-inner-same-judgment}}. script-executor の内側 segment は直接形と同じ重量判定を層ごとに反復で受け、深さ上限を設けない

**決定:** D1891 の「既存 parser が抽出した内側の実行対象へ同じ重量判定を再帰的に適用する」を、
`hooks/guard_bash.py` では次の 3 点で実装する。

1. **内側 segment は直接形と同じ判定を受ける。** executor (`cProfile` / `profile` / `pdb` / `trace` /
   `runpy` / `coverage run`) が実行する内側 program (module または script) から同じ head の segment を合成し、
   `_heavy_segment_violation` の全 gate (provenance / 出力先 / admission / residual / shell / sanctioned /
   pytest 等) をそのまま当てる。baseline の保守性 (`-m` の anywhere 走査など) も含めて同じにする。
   したがって `python3 -m cProfile /tmp/safe.py -mpytest` は直接形 `python3 /tmp/safe.py -mpytest` と同じく
   拒否される。テストは包み形と直接形の**受理 bit の一致**を pin し、値そのものは pin しない
   (baseline の保守性が将来緩めば両方が一緒に動く)。
2. **層剥きは Python 再帰ではなく反復で行い、深さ上限を設けない。** 各層の引数は前層の正規形 args の
   真の suffix なので有限回で止まり、Python の stack は層数によらず一定。深い軽量 command
   (`-m cProfile` を 1,100 層重ねた `-m json.tool`) は過剰拒否しない。
3. **層剥きは shell command-string 再帰の直後、sanctioned 早期許可の前に置く。** sanctioned な target を
   持つ executor 形 (`python3 -m cProfile tools/run_tests.py -m pytest -q`) が内側の pytest を隠せない。
   専用テストがこの位置を pin する。

**理由:**
- 段 5 の再帰実装は 1,100 層の入力で `RecursionError` になり、`main()` の例外経路 (防護 path を含まない
  入力は rc 0) が後続 segment の `pytest -q` を検査せず許可した — 実入口での deny→allow (D428 違反)。
  F709 と同じ「深さがデータに比例する再帰」の型で、対応も同じ (while 化)。深さ上限で拒否側へ倒す案は、
  深い軽量 command の過剰拒否を残すので採らない。
- script 形の追加拒否は「同じ判定」の帰結であり、直接形は旧版でも拒否されていた。包み形だけが穴だった。
  期待値を固定しないと D428 の反転検査で「重量形のみ」と記録できない。
- 位置は段 4 の provisional 裁定だったが、段 6 レビューが識別入力を見つけたので専用テストで pin した。

**却下した選択肢:**
- 深さ上限 + 上限超過で拒否 — 深い軽量 command を過剰拒否する。上限内の層数は事故で越えうる。
- 内側 segment に residual の anywhere 走査を掛けない緩和 — D1891 の「同じ判定」に反し、受理集合を
  広げる側へ動く (D428)。
- `main()` の例外経路を fail-closed へ変える — 本 wave の scope 外 (防護対象を含まない入力の例外方針は
  別の裁定面)。例外を起こさない実装で穴を閉じる。

## {{D:hooks-second-worktree-launcher}}. 有効化前 commit の第 2 worktree では docs 入口を現行 main へ同期し、現行 launcher で Codex 子を起動する

**決定:** D427 / D1719 の第 2 worktree (guard_write に hooks 施錠が入る 1 つ手前の commit を base) で
Codex 子を起動するときは、次の 2 点を加える。

1. 親が `AGENTS.md` / `CLAUDE.md` / `docs/dev-wave/` を現行 main の版へ同期する docs-only commit を
   第 2 worktree に作る (role=manager)。launcher の docs 権威 (DW-O01 の model 行、DW-S05-A の reasoning) と
   子が読む入口 (単独段 dispatch の例外) を現行と同じにするため。
2. 起動は現行 checkout の `tools/dev_wave_codex.py --dry-run` が生成した argv を使い、launcher だけを現行
   checkout の `tools/codex_worker_launch.py` に差し替える。第 2 worktree の旧 launcher は現行 argv
   (`--*-admission-bound-s`) を受けず、旧 docs 権威 (V1 形式) は superseded 済みの model を導出するため。
   現行 launcher の `snapshot_authority` は `--repo-root` (第 2 worktree) の docs から model を導出し、
   `validate_installation` は同 worktree の hooks 配線を検査する — どちらも同期後の第 2 worktree で通ることを
   起動前に実測する。

**理由:**
- 2026-09-10 に model 権威が `gpt-6-astra` / `medium` へ変わり (V2 形式)、有効化前 commit (2026-08-13) の
  launcher と docs では現行権威を導出できなくなった。先行 wave の実測 (両 worktree が同じ model を導出) は
  この改訂前の事実で、もう成り立たない。
- 実装面 (`tools/`) を親が同期するのは D95 に反する。docs だけの同期で権威と入口を揃えられる。

**却下した選択肢:**
- 旧 launcher をそのまま使う — superseded 済みの model を起動する (ユーザー裁定に反する)。
- 旧 launcher が読める V1 形式の model 行を親が書く — 権威の書式を偽装する。
- 第 2 worktree の `tools/` を現行へ同期する — 実装面を親が動かす。
