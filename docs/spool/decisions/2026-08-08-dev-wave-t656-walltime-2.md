---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-08
wave: dev-wave-t656-walltime
seq: 2
---

## {{D:dispatch-default-walltime-40min}}. dispatch の既定 walltime を 40 分へ上げ、下限を余裕比でテストに pin する

**決定:** `tools/pegasus/dispatch_compute.py` の `DEFAULT_WALLTIME` を `00:30:00` から
`00:40:00` へ上げる。`tools/run_tests.py` へ walltime を渡す経路は作らず、受入全走の分割もしない。
あわせて、既定値が受入全走の実測最大所要 (1809 秒) の 1.25 倍以上であることをテストで pin し、
既存の qsub 伝播検査の期待値を literal から `DEFAULT_WALLTIME` 導出へ移す。

本決定は D105 の「`provenance` task の walltime は既定 `00:30:00` を据え置く」の**数値部分だけを
上書きする**。据え置きの理由 (`elapstim_req` は確保上限であって消費ポイントの決定項ではなく、
短縮しても支配項の queue 待ちは縮まない) は不変であり、本決定はその理由と矛盾しない —
短縮ではなく確保上限の引き上げだからである。

**理由:**
- 受入全走の実測所要は 1146〜1809 秒で、30 分枠の 8 割を超えていた。実際に 1 度は進捗 99% 地点で
  per-req elapse 超過により SIGKILL された。試験が増える限りこの縁は再発し、受入結果が
  得られないと wave の land が止まる。
- gen_S の Per-Req Elapse Time Limit は Max 86400S (`qstat -Qf gen_S` で実測) であり、
  40 分は上限に対して十分小さい。`elapstim_req` は確保上限なので、早く終われば消費もそこで止まる。
- 既存の伝播検査は qsub argv の literal 一致だけを見ており、定数と期待値を同時に下げれば
  素通りした。既定値そのものの下限を測る検査が無かったため、同じ縁が黙って戻りうる。
  余裕比を名前付き定数で pin することで、下げる変更が赤になる。

**却下した選択肢:**
- `run_tests.py` へ walltime を plumbing して受入形だけ枠を伸ばす — 受入形の判定は
  「余計な flag を足さない」ことに依存しており、flag を増やすと事前検査が黙って発火しなくなる縁を
  作る。受入全走以外の dispatch も同じ縁を持つため、受入形だけ直すのは対象が狭すぎる。
- 受入全走の分割 — 走行単位が増えると queue 待ちがその回数だけ掛かり、総所要はむしろ延びる。
  分割境界の維持コストも恒常的に乗る。
- lease による直列化だけで足りるとみなす — lease は並行 wave 同士の重なりを減らすもので、
  単一走行の所要そのものを縮めない。SIGKILL の原因は重なりではなく走行時間である。
