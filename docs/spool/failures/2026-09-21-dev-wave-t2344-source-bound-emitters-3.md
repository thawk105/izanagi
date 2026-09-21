---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-t2344-source-bound-emitters
seq: 3
---

## 再発

### F106

- **再発: 2026-09-21** — [T-2344] 発行器収載 wave。**変異 probe の走行中に、親が段 7 の insight 下書きを
  worktree の `output/insights/` へ作って untracked file を増やした。** `tools/mutation_harness.py` は
  runner 実行前の preflight で検出し `rc=2` で停止した (baseline PASSED と M0 SURVIVED までは取れていた)。
  防壁が機能したので実害は probe 1 回の再投入だけである。2026-08-05 / 08-06 の再発と同型で、
  **待ち時間に別の段を進める誘因は注意書きでは消えない**という既載の知見をさらに 1 例増やす。
  今回新しい情報は、親が `DW-M05` の「final の待ちは job dir で確定済み本文と検査の準備に充てる」を
  読んだうえで、**probe の待ちには同じ文が明示的に掛かっていないと読んだ**点である。
  恒久対応は F106 のままとし、本 wave では `DW-M05` の同文を probe / final の両方に掛かる形へ 1 語で明確化した。
  以後の下書きは job dir に置き、走行完了後に `install_docs.py` で repo へ配置した。
