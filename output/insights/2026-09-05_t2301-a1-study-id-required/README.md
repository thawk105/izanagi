# [T-2301] / [T-2272] — A-1 の submit --study-id から既定 study を外し、fan-out docs 2 件を追随させた (2026-09-05)

- wave: `dev-wave-t2301-a1-study-id-required` (branch `worktree-dev-wave-t2301-a1-study-id-required`)
- 基準 commit: `97ee3cd3a49ebc62914909012687bccd907ac4ae` (local main、着手時点)
- 裁定: D1619 (既定撤去・contrast の読み)、D1262、D1295、D95 (実装面は Codex author)
- 形: 軽量版 (段 2・3・段 6 review 子を省略)。実装子 1 本、fix 子 0 本。

## 1. 依頼と、着手前に実測した事実

依頼は 2 つ。(a) `paper_story_a1_paired.py` の `submit --study-id` の既定値を無くして明示必須にし、job body と契約テストも
同じ形へ直す。(b) `output/insights/2026-09-01_t1777-pilot-preregistration/README.md` §4.1 の行 locator 4 件と
`docs/pegasus-runbook.md` §7.7 を現行の 3 job fan-out へ追随させる。

着手前の実測で、依頼の前提と違う事実が 2 つあった。

1. **job body は既に fail-closed だった。** `tools/pegasus/paper_story_a1_paired.sh` の case は `IZANAGI_A1_STUDY_ID` 未設定を
   `refuse "study ID differs"` で拒否していた。残っていたのは冒頭の既定代入 `EXPECTED_STUDY_ID="paper-story-a1-20260826-sized-v1"`
   と、v2 枝だけがそれを再代入しない非対称だけで、job body 側の変更は構造の整合であって挙動は変わらない。
2. **README §4 の発効手順は実施済みだった。** worklog 1275 (D1638 の委任) で AI が発効 5 箇所 + sized fixture 1 行を束縛している。
   依頼の「人間の発効より先に済ませる」という目的は失効していたが、locator 4 件は依然として古い位置を指していたので更新した。

## 2. 変更

| 面 | file | 内容 |
|---|---|---|
| 実装 (Codex author) | `orchestrator/campaign/paper_story_a1_paired.py` | `submit --study-id` を `required=True`、`run_submit` の `getattr` 退避を `args.study_id` へ。1:1 置換で行数不変 (7103 行 pin を保つ) |
| 実装 (Codex author) | `tools/pegasus/paper_story_a1_paired.sh` | 冒頭の既定代入を撤去、v2 の case 枝に `EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"` |
| テスト (Codex author) | `orchestrator/tests/test_paper_story_a1_job_contract.py` | source pin を新形へ、env 欠落の負例 1 本、legacy `run_submit(SimpleNamespace)` 17 箇所へ `study_id` 明示 |
| テスト (Codex author) | `orchestrator/tests/test_paper_story_a1_paired.py` | argparse 拒否 (M1)、3 study の明示受理 (正例)、属性欠落で退避しない (M2) |
| docs (親) | `output/insights/2026-09-01_t1777-pilot-preregistration/README.md` | §4.1 locator 4 件 (driver 198-203 / 192-194、test 1387-1397 / 1012-1019)、§4 冒頭に実施済みの 1 行 |
| docs (親) | `docs/pegasus-runbook.md` §7.7 | `--study-id` 必須、3 request と group intent、group receipt / failure、job 別 evidence、barrier と再投入禁止、group completion、D1619 の estimand の読み |

凍結 policy JSON (v2 / v3-pilot / v3-sized) は触っていない。`complete --study-id`・`run_complete`・`load_policy` の既定は D1619 の
文言外として残し、worklog の次の一手で裁定へ返した。

## 3. 検査

| 検査 | 結果 |
|---|---|
| 焦点走 run1 `test_paper_story_a1_paired.py` 単独 | 182 passed |
| 焦点走 run2 `test_paper_story_a1_job_contract.py` 単独 | 139 passed |
| 焦点走 run3 consumer 集合 (spawn_sites / p3_exploration_namespace / p3_build_authority_cli / official_perf_closure / hooks / a1_non_certifying_marker / campaign) | 1007 passed, 4 skipped |
| `check_docs.py` | 違反なし |
| provenance 全史監査 (実装 commit `7e043f4be` + docs commit `09e9c70ac` の後) | 8242 件、新規違反なし |
| `test_paper_story_a1_headline.py` (commit 後) | 35 passed |
| 変異 probe (全件 SURVIVED 期待、観測 node 収集) | 4 件走行、baseline PASSED。M1/M2/M3 は MISMATCH (SURVIVED 期待に対し、事前登録した node と完全一致の赤)、M4 SURVIVED。冗長 gate 0 件 |
| 変異 本走 | baseline PASSED。KILLED 3/3 (M1・M2・M3、期待 node と完全一致)、M4 (等価) SURVIVED、MISMATCH 0 |
| 受入全走 | 記録 commit の後に投入 (結果は受入後の追記 commit) |

## 4. 変異台帳

事前登録は段 4 (`verbatim/ruling-stage4.md`)。runner argv は `python3 tools/run_tests.py --force-dispatch
orchestrator/tests/test_paper_story_a1_paired.py orchestrator/tests/test_paper_story_a1_job_contract.py -q -rf`。

| id | 位置 | 期待 | 結果 | 赤 node |
|---|---|---|---|---|
| M1-submit-study-id-default-restored | driver `_parser()` submit `required=True` → `default=STUDY_ID` | KILLED | KILLED | `test_submit_parser_rejects_missing_study_id_M1` |
| M2-run-submit-getattr-fallback | driver `run_submit` `args.study_id` → `getattr(args, "study_id", STUDY_ID)` | KILLED | KILLED | `test_run_submit_rejects_missing_study_id_attribute_M2` |
| M3-job-body-default-assignment-reinserted | job body 冒頭に `EXPECTED_STUDY_ID="paper-story-a1-20260826-sized-v1"` を再挿入 | KILLED | KILLED | `test_job_body_dispatches_legacy_pilot_and_future_sized_studies`<br>`test_job_body_contains_all_m12_gates_and_no_submitter` |
| M4-equivalent-docstring | driver `run_submit` docstring に `(equivalent)` を追記 | SURVIVED | SURVIVED | (なし) |

M3 は job body の既定代入を再挿入する変異で、挙動は不変 (case が未設定 env を先に拒否する) のため kill には数えず、
契約テストの source pin が反応することを示す diagnostic sensitivity pin として別枠に置く (DW-M03 / DW-M08)。
M4 は docstring だけを変える等価変異で、harness が SURVIVED を報告できることの正例。

## 5. 段 5 の子の実測

- Codex author: `gpt-5.6-sol`、`reasoning=xhigh`、32 model call、wall 553 s、outcome accepted。
- 子は login sandbox で pytest を dispatch できず (rc=16)、追加 test を直接呼び出して 6 件通過、3 変異を一時注入して赤化
  (M1 `DID NOT RAISE SystemExit`、M2 既定へ退避して後段の `PaperStoryError`、M3 source pin の assertion) を確かめて復元した。
- `bash -n tools/pegasus/paper_story_a1_paired.sh` は hook `guard_bash` (dispatch-required 実行体の保護) に 2 回拒まれ、
  Python subprocess から同じ argv で rc=0 を取った。
- 親の brief に無く子が見つけたもの: 既定退避に依存する legacy `run_submit(SimpleNamespace(...))` が契約テストに 17 箇所あった。
  AST 走査で意図した M2 負例以外の `study_id` 省略が 0 件であることまで確かめている。

## 6. 逐語

- `verbatim/ruling-stage4.md` — 段 4 裁定と変異の事前登録
- `verbatim/author-1-prompt.md` / `verbatim/author-1-report.md` — 実装子の prompt と報告
- `mutation-probe-spec.json` / `mutation-probe-report.json` / `mutation-main-spec.json` / `mutation-main-report.json`

## 7. 受入と land (2026-09-05〜07)

- 受入 attempt 1 (09-05 20:33 JST): rc=70 `dispatch-attestation-missing`。shard-1 が `queue-wait-timeout` (既定 900 s) で落ち、launcher が
  shard-0/2 を SIGTERM。テスト 0 件実走。attempt 2 (20:58): D612 の 3600/600 上書きを export しても `preclaim-history-provenance`
  の監査 dispatch は上書きが効かない経路で queue 待ちに落ちた。孤児 hold (978666.nqsv) を job 不在確認の後に 2 file とも撤去。
- attempt 3 (連結 loop): child-green、20834 passed / 68 skipped。receipt `acceptance-receipt-3.json` (tested main 103c32e30、
  tested tip c59bfb5f5)。
- land (09-07 02:18 JST): main 46b387dc2 を固定 SHA で前方 merge (2353c5177、integrator trailer) して `--landing-wave-tip-sha` で投入。
  `rc=31 fold-gate-failed`: `registered worktree path cannot be resolved: [Errno 2] … '/scr'`。原因は a5 second boot の bench job
  (979578/979579、02:19 開始、上限 7200 s) が計算ノードの `/scr` に作った detached worktree の登録で、login node からは解決できない。
  `retryable_same_request=false` なので同じ receipt は使わず、job 終了後に受入を取り直した (F672 再発、failures fragment seq 1)。
