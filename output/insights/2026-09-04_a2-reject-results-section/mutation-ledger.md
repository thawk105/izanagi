# 変異台帳 — `tools/plotting/plot_a2_certification.py` (wave dev-wave-a2-reject-results-section)

対象 commit: `7bd03172e4d6381439ee75101f9f9be5502dc714` (統合 commit A)。harness = `tools/mutation_harness.py`、
runner = `tools/run_tests.py --force-dispatch orchestrator/tests/test_plot_a2_certification.py -q -rf`
(計算ノード dispatch、D612 の queue-wait 3600 / grace 600 上書き)。spec = job dir `mutation-probe-spec.json` (sha256 `c038145e…4bb84`) と
`mutation-final-spec.json` (sha256 `76974d6a…b0cec`)。事前登録は `s4-ruling.md` §5 (M1〜M13) と `s6-ruling.md` (M4b を M4b/M4c/M4d に分割、M1 の期待理由を訂正)。
生の結果 JSON は job dir `mutation-probe-out-2.json` / `mutation-final-out.json` (repo 外)。

## 手順

1. probe (attempt 2): 16 件すべて `expected_status=SURVIVED`、`expected_nodes=[]` で走らせ、観測した失敗 node の完全集合を集めた。
   baseline PASSED (23 passed、5.59 s、request 977186)。16 件すべて MISMATCH (= 検出)。
   probe 1 回目 (attempt 1) は起動直後・投入前に SIGTERM で止めた (既定 queue-wait 900 s では混雑で空振りするため)。tree clean を確認して再投入した。
2. final (attempt 1): 観測 node をそのまま `expected_nodes` に固定し `expected_status=KILLED` で本走した。
   **結果: baseline PASSED (26.9 s)、16/16 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0、期待 node 完全一致 16/16。**

## 結果

| # | 位置 (関数) | 変異 (一置換) | 期待 node 数 | 本走 | 単一理由性 |
|---|---|---|---:|---|---|
| M1 | `_bench_done_rows` | stage 述語を外す | 18 | KILLED | 理由は 1 つ (述語除去) だが 18 test が同時に赤 = 過剰決定。直接検査 `test_m1_…` を含む。単独変異の証拠としては冗長 gate と明記 |
| M2 | `_summarize_samples` | `n != 5` の拒否を外す | 1 | KILLED | 単一 (`test_m2_…`) |
| M3 | `_load_external_inputs` | 外部 6 file の SHA-256 照合を外す | 1 | KILLED | 単一 (`test_m3_…`) |
| M4a | `_validate_raw_cell` | WAL samples == raw samples を外す | 1 | KILLED | 単一 (`test_m4a_…`) |
| M4b | `_validate_raw_cell` | top-level build_attempt_id 照合を外す | 1 | KILLED | 単一 (`test_m4b_…`) |
| M4c | `_validate_raw_cell` | variant 照合を外す | 1 | KILLED | 単一 (`test_m4c_…`) |
| M4d | `_validate_raw_cell` | nested `performance.build_attempt_id` 照合を外す | 1 | KILLED | 単一 (`test_m4d_…`) |
| M5 | `_crosscheck_certification` | median 照合を外す | 1 | KILLED | 単一 (`test_m5_…`) |
| M6 | `_crosscheck_certification` | effects 照合を外す | 1 | KILLED | 単一 (`test_m6_…`) |
| M7 | `build_provenance` | `outer_status` を `"reject"` 定数に | 1 | KILLED (機械集計) | **diagnostic sensitivity pin** (canonical 入力では等価。kill 件数に数えない) |
| M8 | `_artist_series` | 基準線の値を adopted median から取る | 2 | KILLED | 理由 1 つ (基準線の値)。`test_m8_…` と landed closure が同じ投影の不一致で赤 |
| M9 | `_caption` | correctness/performance 区別文を落とす | 2 | KILLED | 理由 1 つ (caption の必須句)。`test_m9_…` と landed closure |
| M10 | `_publish_outputs` | 保存前 layout check を外す | 1 | KILLED | 単一 (`test_m10_…`) |
| M11 | `_load_tracked_authority` | certification canonical hash 照合を外す | 1 | KILLED | 単一 (`test_m11_…`、subprocess CLI) |
| M12 | `_load_tracked_authority` | raw-manifest canonical hash 照合を外す | 1 | KILLED | 単一 (`test_m12_…`、subprocess CLI) |
| M13 | `_validate_raw_cell` | `build_evidence.source_commit == current_pin` を外す | 1 | KILLED | 単一 (`test_m13_…`) |

集計: KILLED 16/16 (kill として数えるのは 15、M7 は diagnostic pin)。単一理由で単独証拠になるのは 14 件 (M2〜M6、M4a〜M4d、M10〜M13、M8/M9 は 2 node だが同一投影)。
M1 は過剰決定 (DW-M03)。

## 本走後の変更と再走不要の判定

本走の後、受入全走が `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` を赤にした
(新 test file に自走 harness が無い)。fix 子 2 本目が test file 末尾に `__main__` ブロック 4 行を足した (統合 commit C `6a9c4d080`)。
被変異 file `tools/plotting/plot_a2_certification.py` は commit A と C で byte 同一 (`git diff 7bd03172e 6a9c4d080 -- tools/plotting/plot_a2_certification.py` が空)、
test 関数本体も変わらないため、各変異が赤にする node 集合は変わらない。anchor 16 件は commit C で再検証し全件一意 (DW-M07)。変異の再走は行わない。

## erratum

- M1 の事前登録 (段 4) は「非 bench payload の偽値の読取りを検出」としていたが、レビュー A の指摘どおり実際に最初に当たるのは
  `len(selected) != 2` の選択件数 gate と後続の loader 失敗であり、段 6 で「返り値の stage 集合で検出」へ訂正した上で直接検査を足した。
  probe では 18 node が赤になり、単独証拠としては過剰決定 (DW-M03)。
- M7 は kill に数えない (DW-M08 の diagnostic sensitivity pin)。
- probe attempt 1 は投入前に停止 (rc=143)。investigate 用に job dir の `mutation-probe-attempt-1.json` を残した。
