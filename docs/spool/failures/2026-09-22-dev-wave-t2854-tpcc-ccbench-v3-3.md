---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-22
wave: dev-wave-t2854-tpcc-ccbench-v3
seq: 3
---

## 新規

### {{F:ccbench-archive-export-ignore}}. 計算ノード probe が CCBench の source を `git archive` で取り出し、`.gitattributes` の `export-ignore` で `cc/oze` が黙って落ちて configure が失敗した [手順漏れ]

- 事象: TPC-C 段 1 の CCBench 側 wave の計算ノード確認 1 本目 (request 18068.nqsv、Elapse 17 秒) で、C0 の CCBench configure が `add_subdirectory given source "cc/oze" which is not an existing directory` で rc=1 になった。依存の hydrate と gflags / glog の build までは成功しており、計算 job 1 本と fix 1 巡を失った。
- 根本原因: probe は pin と候補の source を bundle の bare 保管庫から `git archive` で取り出していた。CCBench の `.gitattributes` は `oze* export-ignore` (と `.gitignore` / `.gitattributes` の export-ignore) を持つので、archive は commit の tree を忠実に再現しない。取り出し後に tree との一致を照合していなかったため、欠落は build 段まで黙って進んだ。
- 恒久対応: 同 wave の probe (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/probe/run_probe.py` の `sources()`) は、scratch 保管庫の `info/attributes` に `* -export-ignore` / `* -export-subst` を置き、取り出した regular file の集合と各 blob id を `git ls-tree -r` と完全一致で照合し、不一致なら C0 で fail-closed に止める (2 本目で pin・候補とも 404 / 404 一致)。以後の wave 向けの作法は memory `ccbench-git-archive-drops-export-ignore-paths` (CCBench の source を取り出すときは tree 照合付きにするか worktree checkout を使う)。記録 = `output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md` §6。
- 再発検知: 取り出した file 集合と blob の tree 照合が fail-closed で止める。照合を持たない取り出し経路では、CMake の configure が同じ message で落ちる。

## 再発

### F63

- **再発: 2026-09-22** — 段 5 の Codex author (workspace-write、計算ノード probe の実装子) が、`run_probe.py` の後半を shell の heredoc で追記しようとして guard_bash に「防護パスと不透明構文の同居」で拒否され、迂回せず停止した (約 12 分、model call 13 の 1 巡)。書く内容に防護ツリーの path 字面が含まれていた。継続子へ「file は編集 tool (apply_patch) で書き、heredoc・`cat >`・`tee`・`python -c` で書かない」と明記して回収した。親向けの同趣旨 (DW-O03) は reference にあるが、実装子の prompt 定型には無い。本 wave の続く fix 子 3 本は同じ 1 文を入れて拒否 0 件。
