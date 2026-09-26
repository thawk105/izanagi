# [T-2850] 性能 trace の同時検査と静定待ちの上限 — 実装・smoke・本番順序の load 実測・変異 (2026-09-26)

案 (b) (試走の費用を削る案、親の委任による codex 相談の決定 `dev-wave-jobs/dev-wave-t2850-trial-run/consult-option/decision.md`) の実装 wave の記録。
設計判断は decisions の fragment (本 wave の D)、試走の規則への反映は追補 2 (`docs/search-repetition-trial-preregistration-addendum-2.md`)。
job dir (repo 外) = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/`。

## 1. 実装 (branch `worktree-t2850-trace-concurrent-verify`)

| commit | 内容 |
|---|---|
| `60325db77` | author: 取得と検査の分離、fork 子の検査と受領証、親の受理と rep 順投影、opt-in の配線 (p3_s4_loop → search_config → loop → evaluate、harness の write-heavy)、初回 settle の上限 |
| `f0f68a26b` | fix 1: fork 起動箇所を `test_ccbench_spawn_sites.py` の非 CCBench 箇所へ登録、test fixture、変異 M4〜M6 の test |
| `18a3197d8` | fix 2: 子を process group の先頭にし group ごと停止 (verifier の pool worker = 孫の残存)、回収済み PID を再 kill しない |
| `45cbfa8a8` | fix 3: group の消滅確認を leader 回収前に /proc で行い、失敗は rep の reject にして保全・削除まで進む |
| `ffab56d15` | fix 4: /proc 走査で終了途中の無関係 process の ESRCH を消滅として読み飛ばす |
| `f180c9de8` | fix 5: 同時検査 mode の初回静定待ちの上限 60 → 120 秒 (§3) |
| `d21b870c9` | fix 6 (test だけ): 既定 campaign identity の test を `--verify-performance` あり × 3 workload でも確かめる (§5 の M8) |
| `d935fa8e1` | fix 7 (test だけ): 新設 test file に自走 harness (`__main__`) を足す。記録 commit の後の受入全走 1 回目 (main `7c1b53a4b` を post-claim merge) が `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` の 1 件だけ赤 (27,677 passed) だった自分起因の赤。fix 7 の子の報告が 495 byte で出力検証の下限 500 byte に届かず不受理になり、fix 7b で差分を確認させて受理した |

- production の差分は +358 / -42 行 (計 400 行、段 4 の上限ちょうど。`git diff --numstat 6d198ca8a d21b870c9 -- orchestrator/campaign/`)。`orchestrator/calibrator/runner.py` は変えていない (B-5 発効束の下書き
  `output/insights/2026-09-22/t2797-effect-bundle/bundle/b5-effective-bundle.draft.json` が現 bytes の sha256 を持つため、呼び出し側で上限を渡した)。
- 既定 (flag なし) の経路は呼出し形も campaign identity も変わらない (fix 6 の test が `--verify-performance` あり・なしで確かめる)。
- 検査 process の故障は `verify-local-unavailable`。比較 harness の機械故障の集合 (`b5_generator_contrast.MACHINE_FAILURE_ABORT_REASONS`) は
  B-5 と共有なので触らず、この reason は候補の `aborted` として数えられる (追補 2 §2 の既知の限界)。

## 2. 焦点走・レビュー

- 焦点走 (`tools/run_tests.py`、計算ノード、12 file: 新規・変更 test、fan-out 受理、起動箇所登録簿、inventory 系 4 群、t2849 の job 契約など):

| 走 | 木 | 結果 | 赤の帰属 |
|---|---|---|---|
| v1 | 未 commit (author) | 179 failed / 16 errors | 全件 `contract-loader-drift` (未 commit の閉包 file)。実装と無関係 |
| v2 | `60325db77` | 6 failed / 1420 passed | 新 test の fixture (build 認可・numactl の型) と起動箇所の未登録 → fix 1 |
| v3 | `f0f68a26b` | 1429 passed / 5 skipped | — |
| v4 | `18a3197d8` | 1432 passed | — |
| v5 | `45cbfa8a8` | 1 failed / 1433 passed | `test_acquisition_failure_stops_later_trace_and_projection` (verify_done 2 件)。fix 3 の /proc 走査が ESRCH で rep を reject したと推定 (log に理由は出ない) → fix 4 |
| v6 | `ffab56d15` | 1436 passed | — |
| v7 | `f180c9de8` | 1436 passed | — |
| v8 | `d21b870c9` | 1439 passed / 5 skipped | — |

- 段 6 レビュー A (正しさ・失敗時) NO-GO → fix 2、焦点再レビュー 1 NO-GO → fix 3、焦点再レビュー 2 NO-GO の残り 1 件は親が refuted と裁定
  (失敗 rep より後と `finally` の経路の group 消滅確認の失敗を捨てる: それらの rep は投影されず、group 全体へ SIGKILL 後の process は利用者コードを
  実行できず、trace の unlink は開いている読み手に影響しないので、判定・記録の値が変わらない)。レビュー B (過剰・配線) は GO。
- refuted とした所見: 相談 A2 (trace 内容 digest)、レビュー A4 (同時経路で不認証の `EvalResult.verify_result` が None。比較 harness の経路は
  `result_evidence_context` を渡さず、構造化診断は WAL の abort detail に残る。remote fan-out も同じ)。

## 3. 静定待ちの上限 — smoke と本番順序の実測

### 3.1 上限 60 秒の smoke (job `29777.nqsv`、bnode092、Elapse 205 s、commit `ffab56d15`)

- cohort `t2850-smoke-v3`、random・a_limit 1・b_limit 1・n_eval 1・系列 9。系列開始 stock は legacy 1 本 + 性能 5 本 (同時) すべて serializable・
  certified、bench 1,383,411 tps (CV 1.69 %)。**`settled=false`** (bench の周辺 wall 76.9 s = bench 16.8 + 待ち 60 の上限) → 品質欠測 →
  `series-end reason=stock-unestablished`、driver_rc 1。load の値は WAL に残らない (bench の記録は settled の真偽だけ)。

### 3.2 本番順序の load 減衰 (測定 script v3 `--order production`、generic dispatch、固定 checkout `7ea9aa09d`)

測定 script (repo 外、Codex author) は build の後、1 秒間隔の load 標本を取りながら trace 5 本を立て続けに取得し、直後に 5 本を同時に検査して
(pipeline と同じ verifier・argv)、検査の終了から 240 秒の減衰を記録する。前回 (vprobe v2) は「直列検査 → 90 秒の減衰 → 同時検査」の順だった。

| 構成 | 開始時 load / CPU | 取得 5 本 | 同時検査 | 取得中の最大 load | 検査終了時 load | 4.0 以下まで | 60 s 時点 | 90 s | 120 s | 判定 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| wh stock | 1.04 / 48 | 20.5 s | 42.3 s | 17.08 | 12.75 | **67 s** | 4.68 | 2.83 | 1.72 | 5/5 certified |
| wh B0-L-W0 (候補の代理) | 0.15 / 48 | 24.5 s | 95.0 s | 27.91 | 14.28 | **77 s** | 5.24 | 3.18 | 1.92 | 5/5 certified |

- 生データ: job dir `vprobe3/runs/vp3-wh-stock/probe.json`、`vp3-wh-b0lw0/probe.json` (要約は `vprobe3/summarize.py`)。
- 60 秒の根拠にした前回の実測 (3〜39 秒) は、同時検査の前に 90 秒の減衰があり取得の負荷が乗っていない regime の値だった (failures の本 wave の F)。
  上限は最大 77 秒の約 1.5 倍の 120 秒にした (fix 5)。
- 開始時の node は空き (load 0.15〜1.04) で、他 job の同居による外乱ではない。本番の job では block 1 の直列経路でも静定の時間切れが
  12 中 5 件あり (原因未確定)、それとは別の現象である。

### 3.3 上限 120 秒の再 smoke (job `29854.nqsv`、bnode095、Elapse 1,145 s、commit `f180c9de8`)

cohort `t2850-smoke-v4`、条件は 3.1 と同じ。driver_rc 0、系列 `b-complete`、score 3,950,518 tps。

| slot | 値 | 1 session (subprocess wall) | 静定待ち (周辺 − bench) | 結果 |
|---|---:|---:|---:|---|
| 系列開始 stock | — | 166.1 s | 53.2 s | certified・settled・normal、1,362,410 tps |
| 初期点 1 | 5 µs | 259.9 s | 69.3 s | certified・settled・normal、3,968,740 tps |
| 初期点 2 | 10 µs | 259.7 s | 69.3 s | certified・settled・normal、3,986,197 tps |
| 探索 1 | 707 µs | 179.3 s | 72.2 s | certified・settled・normal、1,141,350 tps |
| endpoint の測り直し | 10 µs | 245.0 s | 55.3 s | certified・settled・normal、3,950,518 tps |

- endpoint の記録の `reason: nonzero-rc` は旧実装の block 1 (block job の score-session) にも certified と並んで出ており、既存の挙動 (本 wave の回帰ではない)。
- 旧実装の block 1 では stock 245〜273 s、候補 (1〜28 µs) 474〜520 s、1000 µs 215〜220 s だった (`t2850-trial-pause-cost-options/README.md` §2)。

## 4. 試走の費用の見積り直し

`estimate/estimate_v2.py` (repo 外): 旧 block 1 の job ごとに Elapse から slot の wall の和を引いた残り (約 30 s) を保ち、slot の wall だけを 3.3 の実測に置き換えた。
stock → 166.1 s、旧 wall 400 s 超の候補 → 259.9 s、それ以外 → 179.3 s。

| 単位 | 旧 (block 1 実測) | 新 (試算) | 比 |
|---|---:|---:|---:|
| bo の系列 (18 session) | 8,079 s | 4,374 s | 0.541 |
| evolution の系列 | 9,023 s | 4,615 s | 0.512 |
| block job (10 session) | 3,710 s | 2,161 s | 0.583 |

図 1 枚 (非 LLM) 3.6〜3.8 node 時間、LLM 5.8〜23.3 (親の待ち 2.2〜19.5 は insight 前稿 §4 の幅のまま)、試走全体 22.2〜40.5 node 時間 (旧 40.8〜58.2)、
block job の按分込みの図 1 枚 4.4〜8.1。LLM 系列の待ちは node を確保したままで、今回の変更では減らない。

## 5. 変異 (`tools/mutation_worktree.py`、独立 clone、dispatch)

段 4 の事前登録 M1〜M9 からの変更 (erratum): M3 (最小失敗 rep より後の成功を投影) は、投影の loop が最初の abort で return するので等価になり登録から外した
(その barrier は M1・M4 の test が確かめる)。M5 は「取得の途中で子を起動」を単一置換で作れないので「取得失敗の後も取得を続ける」に再照準した。
drift 層の基準として M0 (pipeline.py のコメント)・M0p (p3_s4_loop.py のコメント)・M0h (harness のコメント、閉包外) を足した。

- **probe 2** (commit `ffab56d15`、spec sha256 `e1dc6a6f…`): baseline PASSED。M0 = M0p = 139 node (contract-loader-drift、F1037 の型)、M0h は SURVIVED。
  drift 集合を引いた値の層の差分:

| 変異 | 置換 | drift 集合の外で落ちた test |
|---|---|---|
| M1 | 子の不認証の結果から abort を捨てる | `test_real_anomaly_stops_projection_and_matches_serial`・`test_failed_rep_reaps_every_later_child`・`test_failed_rep_kills_later_groups_with_live_pool_workers`・`test_group_timeout_rejects_reaps_and_preserves_traces` |
| M2 | 投影を逆順にする | `test_reverse_completion_projects_distinct_payloads_in_rep_order` ほか 4 |
| M4 | 失敗後に後続の子を止めない | `test_failed_rep_kills_later_groups_with_live_pool_workers` |
| M5 | 取得失敗の後も取得を続ける | `test_acquisition_failure_stops_later_trace_and_projection` |
| M6 | verifier の `expected_commits` を None | `test_expected_commits_reaches_real_verifier_in_fork` と commit witness の既存 test 13 |
| M7 | 測り直し round の settle も 60 秒にする | `test_concurrent_verify_extends_only_initial_settle` |
| M8 | `--verify-performance` だけでも同時検査の key を入れる | **0** (狙いの test が drift 集合の中) |
| M9 | harness が read-heavy にも flag を付ける | `test_write_heavy_concurrent_verify_slot_and_header` (1 node だけ = 閉包外) |

- **M8 の commit 注入 (F1037 の恒久対応):** 独立 clone に M8 を commit して狙いの 2 test だけを dispatch。`f180c9de8` では **2 passed (値の層で生存)** —
  既定 identity の test が `--verify-performance` なしの呼び方だけだった。fix 6 の後 (`d21b870c9`) は 3 failed / 2 passed で、落ちたのは
  `test_concurrent_verify_absent_from_default_search_identity[True-write-heavy / True-read-heavy / True-balanced]` (assertion は「search_config に key がある」)。
  記録: job dir `m8c.log`、`m8c2.log` (clone の HEAD `be1706cf…`・`16c4ab03…`)。
- **final** (commit `f180c9de8`、spec `mutation-spec-final.json` sha256 `024dd402…`、期待 node は probe 2 の観測集合): baseline PASSED、
  **11 / 11 が期待と完全一致** (KILLED 10、SURVIVED 1 = M0h)。node 数 M0 139・M0p 139・M1 143・M2 144・M4 140・M5 140・M6 153・M7 140・M8 139・M9 1。
  閉包 file の変異の KILLED は drift 層と値の層の和で、単一理由の証拠は probe 2 の差分表 (上) と M8 の commit 注入。final は fix 6 (test だけ) の前の
  commit で走らせた。fix 6 は production を変えず (`git diff --stat f180c9de8 d21b870c9` は test file 1 本)、M8 の値の層は commit 注入で確かめた。
  記録: job dir `mutation-final-results.json`、`mutation-probe2-results.json`。
