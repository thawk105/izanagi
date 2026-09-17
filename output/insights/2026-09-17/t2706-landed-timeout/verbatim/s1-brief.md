# 段 1 brief — [T-2706] `check_branch_landed.py` の per-command 上限を実測で決める

- 基準: local main b4631a92e (worktree `.claude/worktrees/dev-wave-t2706-landed-timeout`、clean、submodule 初期化済み、開始 gate fresh OK @ abc7085ae → ff-only で b4631a92e)
- 起票: worklog archive entry 1552 の [T-2706] (`docs/archive/worklog-phase3-0916-1552.md`)
- 裁定: D2104 項 24 (2026-09-17 第 20 回 /rulings 全件、main 着地済み)。「受理述語は不変 (timeout は証拠にならず、verdict は決定的証拠からだけ出る) と確認したうえで、per-command 上限の値は Git 操作別の完了時間と全体予算内の完走率を実測して有界に決める (AI 手番)」。理由: 起草の「上げる」は根拠不足。
- 実行機: pegasus02 (login node、96 core、load avg 24 前後、git 2.34.1)。repo: main 11,246 commit、packed 176,575 object、19 pack、579 MB。

## 研究前進 (土台)
着地判定器は D720 条件 1 (未着地) の唯一の機械判定で、`check_branch_rescue.py` (rescue gate) と cleanup の削除判断の入力である。本 repo では 30/30 が per-command 5 秒で `assessment-timeout` (entry 1552)、つまり **この repo で 1 件も判定できない**。放置時の成果物影響 (DW-G05): 到達不能 commit 台帳の `assessment_verdict` が永久に `indeterminate` のまま、rescue gate は救出 ref を消せず、branch 掃除は人の目視だけになる。最小差分 = 定数 1 本 (+ 受理述語不変の正例・負例 test)。完了判定: (a) 現物で timeout → `indeterminate` 固定を示す、(b) 30 件の Git 操作別完了時間と、全体予算 (既定 60 秒、CLI 上限 300 秒、rescue 既定 8 秒) 内の完走率の実測表、(c) 実測から有界に決めた新定数、(d) 変異 matrix で「定数が受理集合に触れない」正例・負例が KILLED。

## 親の実測 (段 1 時点、job dir `timing-lifted-2.json.jsonl`)
- 現状再現: OID `0b92c254…` を `--timeout-seconds 300` で走らせても proof 段の `git log` が 5 秒で timeout (git 子 22 本、10.8 秒、rc=2)。closure は 0.58 秒で完了。
- 上限を 300 秒に持ち上げた 1 件目 (proof unit 18、git 子 140 本): 壁時計 175 秒 (cold) / 97 秒 (warm)。**重いのは `git log --full-history --format=%H --max-count=1025 <main> -- <path>` だけ** (18 本、中央値 5.2 秒、最大 10.1 秒、合計 84 秒)。他は ls-tree 53 本 (最大 0.20 秒)、cat-file --batch-check 18 本 (最大 0.43 秒)、cat-file 36 本 (最大 0.14 秒)、rev-list --topo-order 1 本 0.67 秒、rev-parse 6 本 (最大 0.17 秒)、diff / diff-tree / for-each-ref いずれも < 0.4 秒。
- 5 秒上限は `log -- <path>` の**中央値にちょうど掛かる**ので、30/30 timeout は偶然でなく決定的。
- warm の 2 巡目は verdict `refs-moved` (97 秒の間に main が abc7085ae → b4631a92e へ動いた)。長い判定は共有 repo では ref 移動にも負ける (受理述語どおり indeterminate)。
- 30 件全数は計測中 (detached、`timing-lifted-2.done` で完了)。段 4 の裁定はこの表で行う。

## 受理述語の不変 (現物、`tools/check_branch_landed.py`)
- `Git.run` の `subprocess.TimeoutExpired` → `AssessmentError("assessment-timeout", outcome="truncated")`。`timeout = min(command_timeout, remaining)` なので per-command 上限は全体予算より緩くはなれない。
- AssessmentError の捕捉 8 箇所: 決定的層は `_proof_unit` の spool 2 箇所 (`_decision("indeterminate", exc.code)`)、`history_scan` (不完全なら負例 unit を `indeterminate` へ戻す)、最上位 `assess` の except (`_decision("indeterminate", code)`)。観測層 (verbatim / ledger corpus / ledger probe / patch-id / task index) は outcome を記すだけで verdict に触らない。`_target_resolution_candidates` は `branch-not-found` 以外を再送出。
- `landed` は `search.outcome == "matched"` (tip または履歴の exact state) か receipt 一致からだけ、`not-landed` は `not-matched` + any-path 不一致 + 完全な history scan からだけ (D922 項 4)。timeout がどちらかへ落ちる経路は無い。
- 既存 test: `test_batch_failure_never_becomes_negative` (注入 timeout → indeterminate)、`test_global_timeout_is_indeterminate_json` (全体予算 1e-6 秒 → indeterminate)。**subprocess 段の実 TimeoutExpired を通す test は無い。**

## scope (本題だけ)
1. `tools/check_branch_landed.py:38` `COMMAND_TIMEOUT_SECONDS` の値を実測から有界に決めて変える。docstring / コメントに根拠 (実測値・repo 規模・日付) を 1〜2 行。
2. `orchestrator/tests/test_check_branch_landed.py` に正例・負例: (正例) 定数は `0 < COMMAND_TIMEOUT_SECONDS <= DEFAULT_TIMEOUT_SECONDS` で `Git.run` の既定値と同一 (定数変更が実際に効き、全体予算を超えて無意味にならない)。(負例) PATH に sleep する偽 `git` を置き `Git.run(..., command_timeout=小)` で実 `TimeoutExpired` → `AssessmentError` code `assessment-timeout` / outcome `truncated`、その状態で `assess()` の verdict は `indeterminate` (landed / not-landed にならない)。
3. insight README (実測表・完走率・決定理由) + worklog / decisions fragment。

scope 外: `--command-timeout` CLI の追加、retry、timeout 管理基盤、`DEFAULT_TIMEOUT_SECONDS` / rescue の `DEFAULT_ASSESSMENT_TIMEOUT_SECONDS = 8.0` の変更 (実測結果は記録し carry へ)、`git log` の高速化 (`--first-parent` 等の探索方式変更は受理集合に触る)、gate・台帳の追加。

## 親の provisional 裁定 (攻撃対象)
- (P1) 新定数の候補 = 「30 件で観測した単一 Git 操作の最大完了時間 × 余裕 2〜3」を全体予算既定 60 秒以下に丸めた値。1 件目の最大 10.1 秒からは 20〜30 秒。段 4 で 30 件の表から確定する。
- (P2) per-command 上限の役割は「1 本の git が固まったとき全体予算を待たずに indeterminate で返す」だけであり、verdict の質には寄与しない。したがって値を上げても偽 landed / 偽 not-landed は生まれない (受理述語不変の帰結)。
- (P3) 全体予算内の完走率は per-command 上限だけでは決まらない: proof unit 数 × `log -- <path>` (5〜10 秒) が全体予算を超える件は上限を何にしても完走しない。この事実は記録し、既定 60 秒 / rescue 8 秒の見直しは carry (本 wave では変えない)。
- (P4) 変異 matrix: 定数 → 極小 (0.001) は実 repo 経路でしか赤にならず単体 test では検出不能なので登録しない。登録するのは (負例) timeout 捕捉を `landed` / `not-landed` へ変える変異、`outcome="truncated"` を落とす変異、`Git.run` の既定値を定数から切り離す変異、上限 pin の緩和、(等価) コメントだけ。
- (P5) 段 5 は author 1 本 (定数 1 行 + test 2〜3 本)。

## 不変条件
- 規律 2: 受理述語 (D922 項 2・4) 不変。`landed` / `not-landed` の出る条件と経路は 1 byte も触らない。
- `Git.run` の `min(command_timeout, remaining)` 構造不変。CLI 引数集合不変。JSON schema `izanagi-branch-landed-v1` 不変。
- 変更は定数 1 行 + test 追加のみ。

## 受入・実測
- 焦点走 (login): `orchestrator/tests/test_check_branch_landed.py` (+ consumer `test_check_branch_rescue.py` は judge subprocess を起動するので同走)。受入全走 = `tools/dev_wave_wait.py acceptance --lease-optional -- python3 tools/run_tests.py`。
- 定数変更後の実走: 30 件を新定数・既定予算 60 秒で走らせ完走率を記録 (変更前 0/30 との対照)。変異 matrix は container worktree から。
