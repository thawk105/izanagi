---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2356-s4-prebuild-seam
seq: 1
---

## {{D:mutation-runner-narrowed-for-contract-loader-bound-files}}. contract-loader 束縛 file を変異させる wave は、変異 runner を所有 test へ絞る

**決定:** `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` に載る file
(`env_contract.py`、`env_contract_activation.py`、`execution_guard.py`、`loop.py`、`pipeline.py`、
`wal.py`、`ident.py`、`artifact_admission.py`、verifier の 2 本ほか) を変異させる wave は、
変異 harness の runner argv を**その wave が所有する test へ絞る**。repo 全体や当該 file の
consumer test 全部を走らせる形にしない。絞った範囲を insight の変異節へ明記する。

**理由:**
- これらの file を disk 上で書き換えると `ident.verify_against_lock` が
  `contract-loader-drift: disk bytes が記録 commit blob と不一致` を投げ、campaign lock を検証する
  test が一斉に赤になる。変異が意図した gate ではなく drift 検査で殺されるため、赤理由が 1 つに
  絞れない (`DW-M01`)。診断文字列だけの赤を kill に数えないという `DW-M03` にも抵触する。
- 同じ mask を、未 commit 状態の焦点走で実測した。本 wave では
  `orchestrator/tests/test_p3_s4_loop.py` が commit 前に 48 赤、commit 後に 402 緑で、
  48 件はすべて drift 由来だった。実装の回帰ではない。
- 絞った選択 (`-k "prebuild or fetchcontent"`) では、5 箇所の変異がいずれも所有 test だけを
  落とし、drift 由来の node は 1 件も観測されなかった。期待 node が意図した gate を名指しする。

**却下した選択肢:**
- consumer test を全部含める — `DW-O26` の焦点走の考え方に沿うが、変異では drift が全体を覆うため
  証拠にならない。焦点走 (回帰検出) と変異走 (gate の歯の立証) は目的が違う。
- 変異中だけ contract loader 束縛を無効化する — 正しさ防壁を実験のために緩める形であり、規律 2 に反する。
- 束縛外の file へ再照準する — 本 wave の配線は束縛対象 2 file の中にあり、照準を外すと
  配線そのものの歯を立証できない。
