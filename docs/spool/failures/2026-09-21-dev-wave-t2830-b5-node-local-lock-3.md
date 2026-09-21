---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-t2830-b5-node-local-lock
seq: 3
---

## 再発

### F71

- **再発: 2026-09-21** — [T-2830] wave で、変異 final の期待 node を集める親の login self-run probe (DW-M08) が node 抽出で 2 度つまずいた。
  1 回目は pytest の ANSI 色付けで `FAILED` 行が regex に一致せず、M1 で「rc=1 だが抽出 0」の probe 自身の fail-closed で止まった
  (復元は正常)。`PY_COLORS=0` と ANSI 除去で取り直した 2 回目は、regex `\S+?::\S+?` が**空白を含む parametrize id** (fragment メタ test 30 node)
  を切って取りこぼし、期待集合が不完全のまま final を投入して M7 / M8 が MISMATCH (81 vs 51、76 vs 46) になった。F71 の「記録側と検査側で
  node 形式が揃っていない」型のうち、**親の probe が表示行を空白区切りで読んだ**向きである。harness の完全一致比較が fail-closed で捕まえ、
  M7 / M8 は元々過剰決定として単一理由の証拠から外す登録だったので判定への影響は無い (一次資料 = `output/insights/2026-09-21/t2830-b5-node-local-lock/README.md` §6)。
  是正: self-run は `PY_COLORS=0` で走らせ、node は表示行の空白区切りでなく、自走出力に並ぶ `IZANAGI_FAILURE ... nodeid="..."` 行か
  dispatch 結果の `failed_nodes` から取る (memory `mutation-expected-nodes-via-login-selfrun` の regex 記述を訂正)。
