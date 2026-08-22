---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t839-verifier-v2-trace
seq: 1
title: '[T-839] verifier parser の v2 trace 配線は既に着地済みと確認し、stale carry を解消した (docs のみ、branch worktree-dev-wave-t839-verifier-v2-trace)'
---

## 本文

依頼は「verifier の parser に v2 trace 対応 (parse/model/core/report の4層、件数照合と E 終端)
を配線する」だったが、着手前必須確認 (依頼指定) で実装済みと判明したため、コード変更はしていない。

**一次資料での確認結果。** `orchestrator/verifier/parse.py` は既に C レコードを 7-field 必須にし
(txid/thid/epoch/tid/read_count/write_count)、5-field (v1) を専用 `ParseError` で拒否している。
件数照合 (`_record_count_mismatch`/`_record_missing_end` → `TxnFramingViolation`) と E 終端
(必須化・重複検出・txid 不一致拒否) も実装済み。`model.py` の `Integrity.framing_violations`、
`core.py` の構造化 note 配線 (絶対規律3準拠)、`report.py` の JSON/text 出力まで4層とも配線済み。
実装コミットは `fb5e74a1` (`[T-816] 手順4`、2026-08-12 着地、現 main の祖先)。worklog の
`- [T-839] (N)` 持ち越しは、この着地に追随しないまま 10 日間 (entry 445 以降) 機械的に carry
され続けていた stale stub だった。

**codex 敵対検証 (`tools/dev_wave_codex.py --stage consult`, reasoning=max) で反証を試みた。**
verdict は REFUTED — ただし対象は T-839 自体でなく、隣接する T-838
(SI/凍結 v1 raw trace が v2 専用 parser で検証不能になる懸念、2026-08-15 に
`docs/phase3.md` の見送り台帳で「[T-816]の裁定へ吸収、処理済み、再訪条件=なし」として正式終端済み)
の周辺だった。`orchestrator/campaign/silo_ladder_rung1.py:2770-2882` の `validate_raw_bundle`
(現行の生きた CLI subcommand `collect`/`verify-result` から到達可能) は `verify_trace_dir` を
raw trace へ直接呼ぶが、`fb5e74a1` はこの関数を変更していない (`git show fb5e74a1 --
orchestrator/campaign/silo_ladder_rung1.py` で確認 — 変更は PIN 前進と
`framing_violations` 検査追加のみ)。この bundle
(`output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/
correctness/traces/`) は今も git tracked・v1 形式のまま (直接 Read で確認、`C 0 0 1 1`)。
commit message の「trace 再検証を退役した」は**現行テスト側**では真
(`test_silo_ladder_rung1_evidence.py` の `test_silo_ladder_rung1_commit_witness_matches_
committed_raw_data` が witness-only 検査に置換され `verify_trace_dir` を呼ばないことを
実物確認、focus run で緑を実測) だが、**production 関数自体は退役されておらず** CLI からは
today も到達可能なまま — commit message の記述と実装に齟齬がある。ただし `ParseError` は
未捕捉クラッシュであり「検証をすり抜けて偽陽性 certified を出す」経路ではないため絶対規律2の
核心的懸念には抵触しない。T-839 のスコープ外・T-838 のスコープ内であり、T-838 は
「再訪条件なし」で正式済みのため、本 wave では見送り台帳への 1 行追記 (見送り追記) で
透明性だけ確保し、再訪・修正は行わない。

**実測**: focus run (`orchestrator/tests/test_verifier.py` + `test_silo_ladder_rung1_evidence.py`)
= 74 passed, 1 skipped, 0 failed。受入全走 = `verdict: child-green`
(`red_nodeids: []`, `flake_nodeids: []`, `tested_tip: 2c63829e`)。

**エージェント工数**: codex 子 1 本 (consult、`reasoning=max`、`sandbox=read-only`)。初回2回は
launch 事故 (stdin 未クローズによる異常終了、手動 detach が harness に早期回収される問題) で
不採用、3回目 (harness-native `run_in_background`) で完走した。実装子・fix子は起動していない
(実装差分ゼロ)。

## 次の一手差分

### 完了

- [T-839] parser・model・core・report の v2 trace 配線 (件数照合・E終端) は既に
  `fb5e74a1` ([T-816] 手順4、2026-08-12) で着地済みと一次資料で確認した。追加のコード変更なし。
  remaining: none
  base: 18f016ddc9846e5ec57d9e0e5b4b9f990d7e1c006cef6d433f5cc2aed740ccfe

### 見送り追記

- [T-838] 2026-08-22 再検査 (dev-wave-t839-verifier-v2-trace): `validate_raw_bundle` (`orchestrator/campaign/silo_ladder_rung1.py:2770-2882`、CLI `collect`/`verify-result` から到達可能) の `verify_trace_dir` 呼び出しは `fb5e74a1` で変更されておらず、tracked v1 raw bundle (`0_873920.nqsv`) に対し実行すれば未捕捉 `ParseError` で停止する。現行テストは witness-only 検査に置換済みで到達しないため受入は緑 (crash であり false-green ではないため絶対規律2には抵触しない)。再訪要否はユーザー判断に委ねる。
