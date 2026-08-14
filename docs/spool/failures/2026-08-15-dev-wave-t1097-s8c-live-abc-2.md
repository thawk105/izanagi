---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-15
wave: dev-wave-t1097-s8c-live-abc
seq: 2
---

## 再発

### F84

- **再発: 2026-08-15** ([T-1097] wave、near miss)。段 1 の前提実測 probe が
  production の `buildcache._v2_commands` を呼んで configure argv を導出したが、
  production caller が渡す `dependency_prefix` を空のまま渡した。結果、計算ノードでの
  configure は 0.655 秒で `find_package(gflags)` に落ち、**測定対象だった FetchContent へ
  1 度も到達しなかった**。誘発要因は「argv を production から取れば同じ経路だ」という認識で、
  F84 本体の「transport を変えるだけ」と同型 — **使い捨て経路が production caller の設定を
  写し漏らすと、内側が同じ経路でなくなる**。
  誤結論 (「[T-1094] の FetchContent 不通を確認」) の直前で止められたのは、probe が
  `_deps` の中身を成果物として記録しており **0 件だったから**である。prefix を production の
  seam 経由で渡して再測すると rc=0 / 8.357 秒で依存 3 本が pin 通りに生成された。
- **恒久対応 (本再発分):** 前提実測 probe が「X は通るか」を測るときは、
  **X へ到達した witness を成果物に含める** (本 wave の `deps_present` がその実例)。
  rc だけを見て非 0 を X へ帰属しない。近縁 = F41 (偽赤の非帰属)、F99 (sanctioned 呼出し形の逐語写し)。

### F97

- **再発: 2026-08-15** ([T-1097] wave、独立 2 例目 — 別 producer / 別 consumer)。
  D122 決定 (2)(ii) の transport 受理条件が、計算ノードで実在する `PBS_JOBID` を必ず拒否する。
  `claude_transport.PBS_JOBID_PATTERN` は `[A-Za-z0-9][A-Za-z0-9._-]*` で colon を含まないが、
  NQSV が渡す実値は `0:911106.nqsv` (job index + request id) である。pattern は
  `qsub_binding._JOB_ID_TEXT` と byte 一致で pin されているが、そちらは **qsub が印字する
  request ID** の文法であって環境変数の文法ではない。**repo 自身がこの差を知っている** —
  `test_claude_transport.py` は `COLLECTOR._JOB_ID.pattern == rf"(?:0:)?{PBS_JOBID_PATTERN}"` を
  pin しつつ、同じテストで `"job:id"` を invalid と主張している。F97 と同型で、
  **参照/実在値が自分自身の受理述語を通らない**ため、計算ノードでの 8c live 実行が全面的に塞がる。
  D122 段 1 の前提実測 (request `877155`) は proxy key と `claude -p` の rc を測ったが、
  `is_valid_pbs_jobid` を実機の `PBS_JOBID` へ通す end-to-end を測っていない。
  緩和も迂回もせず裁定へ返した (材料 = `output/insights/2026-08-15_t1097-s8c-live-abc/` §5 問 1)。
  **F97 の「再発検知」が提案する自己整合 positive control は、独立 2 例目が出たことで
  F97 単体でなく fail-closed admission 述語の族へ一般化できる状態になった** (`DW-G03` の閾値充足)。
  族一般化そのものは受理集合と検査義務に触れるため {{T:admission-predicate-live-value-control}} で裁定へ返す。
