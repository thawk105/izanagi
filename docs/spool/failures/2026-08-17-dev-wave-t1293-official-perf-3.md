---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1293-official-perf
seq: 3
---

## 新規

### {{F:codex-child-oom-on-wide-reads}}. 所有 file の合計行数が大きい実装子が SIGKILL され成果物ゼロで終わる [セッション死・救出] [コンテキスト浪費]

- 事象: dev-wave 段 5 の実装子 2 体が `codex_exit_code = -9` で終了した。1 体目は
  production 差分 245 行を worktree に残したままテスト 0 行で、2 体目は差分ゼロで終わった。
  どちらも receipt の `output_bytes = 0`、`stop_reason = max_attempts` で、
  `attempt-0001.stderr.log` には `Reading additional input from stdin...` の 1 行しか無い。
  **`.log` も成果物も空なので、receipt を読まないと原因が分からない。**
- 根本原因: 両者とも `actuals.input_tokens` が約 350 万 token に達した時点で殺されている
  (1 体目 3526974 / 353 秒、2 体目 3542031 / 424 秒、model call はそれぞれ 37 / 36)。
  所有 file の合計が 25000 行級 (production 6813 行 + その test 9501 行 等) で、
  子が構造把握のために網羅読みしたため、計算機のメモリ上限に当たった。
  **`DW-S05-A` は実装単位を「編集ファイル所有が素集合」で決めるが、単位の大きさ
  (所有 file の行数合計) に触れていない。** 素集合条件は満たしていた。
- 恒久対応: 段 5 の実装子 prompt へ読み取り予算を明記する
  — (a) ファイル全体を読まない、(b) `grep -n` で位置を特定してから `sed -n` で範囲読みする、
  (c) **読んだ合計が 2000 行を超えたら読解を打ち切って実装へ移る**、
  (d) 完全な理解より生きて成果物を出すことを優先し、未確認箇所は報告へ「未確認」と書く。
  本 wave では所有を 11 単位へ分割し、この 4 点を prompt へ入れて全単位が完走した。
  単位の大きさを `DW-S05-A` の分割条件へ加えるかは予算の都合で保留し、裁定へ返す。
- 再発検知: `dev-wave-jobs/**/receipt.json` の `codex_exit_code == -9` と
  `actuals.input_tokens` の同時観測。親は子が成果物ゼロで終わったとき、`.log` の空を
  「起動失敗」と誤読せず receipt の `codex_exit_code` を必ず読む。
- 併発した誤読: 1 体目の失敗直後、親は `.log` が 0 byte だったため起動失敗を疑った。
  実際は起動して 7 分走った末の OOM であり、**receipt を読むまで区別できなかった**。
