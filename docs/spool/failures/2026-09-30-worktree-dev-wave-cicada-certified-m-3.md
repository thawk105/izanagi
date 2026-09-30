---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: worktree-dev-wave-cicada-certified-m
seq: 3
---

## 新規

### {{F:endif-after-line-shifts-trace0}}. `#if TRACE … #else #line N #endif` の `#endif` 行も行番号を進めることを見落とし、TRACE=0 の `__LINE__` が 1 行ずれた [手順漏れ]

- 事象: [T-2874] の M 計装 (`patches/instr-cicada-trace-m.patch`) の TRACE=0 同一性で、4 target × 2 genome と E-max の 10 組すべてが不一致になった。親が両側の `transaction.cc.o` を `objdump -d` で比べた差は 1 命令だけで、`TxExecutor::gc_records()` の `ERR` の `__LINE__` が pin の 853 に対し 854 として展開されていた。Codex の patch 作成・静的レビュー 2 本・焦点再レビュー 2 巡・`git apply` の確認はいずれもこれを捕まえず、計算ノードの同一性 build で初めて見えた。
- 根本原因: `#else` の直後に `#line N` を置くと、N は次の物理行 (= `#endif` 行) の番号になり、`#endif` の次の source 行は N+1 になる。M の `#line` は「次の source 行が N」と数えて書かれていた。
- 恒久対応: 同 wave で、M 適用前後の source を TRACE=0 側だけ残して `#line` を適用した実効行番号で全行照合する検査を Codex の fix 子が scratch で走らせ、42 本の `#line` を stock と E-max の両 stack で不一致 0 にした。repo 外起動器の TRACE=0 同一性 (命令列・relocation 付き逆アセンブル・前処理・`nm`・`strings`) が計算ノードで fail-closed に拒否する (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py` の IDENT)。記録 = `output/insights/2026-09-30/cicada-certified-m/README.md` §8 の 9。
- 再発検知: TRACE=0 同一性の比較 (定数として展開される `__LINE__` の差が命令列に出る)。`ERR` など `__LINE__` を使う macro が `#line` の後ろに無い file では命令列に出ないので、実効行番号の全行照合を併用する。

## 再発

### F1046

- **再発: 2026-09-30** — [T-2874] の repo 外起動器 (Codex author) が pin の CCBench を `git archive` で展開し、`oze* export-ignore` で `cc/oze` が抜けて計算ノードの configure が rc 1 になった (SMOKE 1 回目、request 38725.nqsv、Elapse 17 秒)。起動器が cmake の stderr を捨てていたので原因の特定に fix 1 巡を要した。雛形 (md_23 の起動器) と同じ pinned full checkout に戻した。

### F440

- **再発: 2026-09-30** — [T-2874] の dev-wave で、照合 (検査) を新設する wave なので条件 dispatch 13 (`DW-O13`、最遅 段 2 前) が着手時から成立していたのに、段 2 の前に読まず段 2〜4 を進めた。段 5 の前の条件再評価で気づき、契約どおり段 2〜4 を無効化して段 2 から取り直した (plan 1・相談 2・裁定 1 が無駄)。
