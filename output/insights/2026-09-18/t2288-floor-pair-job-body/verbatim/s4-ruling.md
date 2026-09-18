# 段 4 裁定 — [T-2288] (a) floor-pair Pegasus job body 着地 wave (2026-09-18 11:15 JST)

裁定 inbox の再走査: wave 開始 (10:43 JST) 後の更新なし (最新 09:24 の T-2724、本件と無関係)。

## 1. 段 2 plan v1 の訂正 6 点 — すべて real・採用
driver 起動は `"$PY" -I -B -c` + sys.path 挿入 + `main()` 呼出し / window ID は `<wl>-w1` を `windows[].window_id` exact 一致で引く / walltime は submitter の mode 分岐 1 箇所 (`qsub -l` と env に同値) / evidence leaf 内の file 所有を submitter・scheduler・job で分離 / hostname は第一 label の完全一致 `^bnode[0-9]+$` (PBS env は証拠にしない) / login 起動確認は「実際に到達した gate」を記録 (hook 拒否で終わりうる)。

## 2. 段 3 レンズ A (凍結成果物の保護) — 所見 9
| # | 判定 | 採否 | 対応 |
|---|---|---|---|
| A1 3 段同一 HEAD は投入時に機械保証されない (w1=H1、w2=H2 が finalize まで通る) | real・must-fix | 採用 (scope 内 = 申し送り 2 の実装) | submitter の前段: `--window` では**同 spec の他窓の JSONL が checkout に存在すれば**その header (1 行目 JSON) の `loaded_head` == 現 HEAD を要求。`--finalize` では両窓 JSONL の存在・header `loaded_head` == HEAD・末尾 record が `"event": "terminal"` を要求。driver の検査は複製しない (validator を呼ばず、header 1 行と末尾 1 行だけ読む) |
| A2 finalize は `incomplete` terminal でも summary を作る (失敗記録の契約) | real (説明の訂正) | 採用 (docs) | runbook §7.8 に「失敗 summary も 1 回限り。両窓の terminal が出て結果を受け入れてから finalize を投げる。再走は無い」を書く。A1 の finalize 前段 (terminal 存在) が早すぎる投入を止める |
| A3 10 h の根拠 (44.4 h regime は不採用になる) は不成立 | real・must-fix | 採用 | **(P2) 改訂: window job `elapstim_req=24:00:00`** (gen_S 上限 86400 s、`b10_backoff_shape_campaign.sh` の先例)、finalize `00:30:00`。理由 = 窓の喪失は回復不能で、要求超過の費用は queue 待ちだけ (非対称)。24 h も成功保証ではない。実測分布は後続 wave の裁定パッケージ候補 |
| A4 不等号は正しいが walltime・時計の前提が未検証 | should | 採用 | job body は scratch 作成後・driver 直前にも実時計で同じ関数を再検査。前提 (走行中の時計安定、scheduler の終了猶予) は runbook §7.8 に「未検証」と明記 |
| A5 別 nonce の二重投入は nonce dir では排除されない | should | 採用 | submitter: 対象窓の JSONL (`windows[].artifact_relpath`) が既に存在すれば拒否 (早期拒否。同時投入の排除ではない)。runbook §7.8: spec × 窓は 1 回だけ投入、不明な qsub 結果を自動再投入しない |
| A6 前段は driver 検査と意味的に重複 — 変異の帰属を分けて説明 | should | 採用 (記録) | M1〜M10 は shell・登録簿・docs の契約に対する kill。driver の検査強度は主張しない (insight・worklog に明記) |
| A7 signal・create-only は成果物の完結性を保証しない | 情報 | 記録 | 救出経路は scope 外 (裁定パッケージ候補) |
| A8 `--assume-now` 不採用は支持 | 情報 | 採用 (不採用のまま) | 正例は契約 test の now 注入だけ |
| A9 brief「止めているのは job body だけ」は限定すべき | should | 採用 (記録) | worklog: 実走には admission・binary 可用性・時間予算・同一 H・証拠確認が別に要る |

## 3. 段 3 レンズ B (実行面・登録簿・test) — 所見 10
| # | 判定 | 採否 | 対応 |
|---|---|---|---|
| B1 `test_hooks.py` の golden 2 集合 (`_PEGASUS_EXPECTED_CLASSES` 3163、`_PEGASUS_EXPECTED_ENTRIES` 3239) と local-ok evidence 表 (4085〜) に 2 entry が要る | real・must-fix | 採用 (scope に既存 test の golden 更新を追加) | author が 3 箇所へ逐語で追加 (現物で確認済み: 3 golden とも path → 4 field / class / evidence の literal) |
| B2 scratch `/scr/${PBS_JOBID}` は `0:` 付き ID で壊れる | real・must-fix | 採用 | `TMPDIR=/scr/${PBS_JOBID//:/_}` (A-5 の型)。**shim は置かない** (B4) |
| B3 必須 command に `nm` が無い (driver は `buildcache._assert_no_trace_symbols` → `nm -C`) | real・must-fix | 採用 | 必須 command = `git nm pgrep sha256sum hostname date realpath mkdir env` (現物 `floor_pair_driver.py:2117`、`buildcache.py:3775` で確認) |
| B4 python3 shim は本 driver 経路に不要 (孫は binary と pgrep・nm・git) | 情報 | 採用 | shim 無し。`$PY` 明示 + `-I -B -c` bootstrap |
| B5 契約 test は関数抽出だけでなく分岐・配列構築・dry-run 分岐・signal/wait を**実行観測**する | real・must-fix | 採用 | author 指示: `_shell_function` 抽出 + `bash -c` で、(a) gate 呼出しの到達 (stub した gate 関数が呼ばれた痕跡 file)、(b) driver argv 配列の構築 (mode 別に配列を印字して比較)、(c) dry-run 分岐 (stub `qsub` 関数が呼ばれないこと・非 dry-run で呼ばれること)、(d) child の rc 回収 (無害な `sh -c 'exit 7'` を driver の代わりに置く snippet) を実行検査 |
| B6 login 起動確認は hook が先に拒否しうる、`git worktree add` は `.sh` 経由 | real・must-fix | 採用 | 完了条件 = 実際に到達した gate の記録。親は Bash tool から試み、hook 拒否なら rc と reason を記録 (迂回しない) |
| B7 qsub は `cd -P` 後、job 側も realpath 同士 | should | 採用 | submitter は `cd -P -- "$REPO_ROOT"` して相対 `tools/pegasus/floor_pair_campaign.sh` を qsub |
| B8 signal は floor の即 exit ではなく driver 回収型 | should | 採用 | driver を background child で起動し `wait` で rc 回収、TERM/HUP/INT は記録して再 `wait`。shell から driver へ kill しない |
| B9 前提 3 点は正しい (NEEDED 4 本、bench lock なし、build sink なし)。RUNPATH は残る | 情報 | 記録 | compute での依存解決は未実測と書く |
| B10 並走・queue 待ちの保証はしない、evidence root は `dev-wave-jobs` の外 | should | 採用 | evidence base `/work/1/SFC/tanab/izanagi-job-evidence/floor-pair` (dev-wave-jobs の兄弟) |

## 4. plan v2 (確定)
### 4.1 file と所有 (author 1 本、worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2288-fp-author`、branch `impl-dev-wave-t2288-floor-pair-job-body`)
- 新規 `tools/pegasus/floor_pair_campaign.sh` (job body、mode = window | finalize)。名前は `floor_campaign.sh` の型に揃える (plan の `floor_pair_window.sh` から改名。finalize も担うため)。
- 新規 `tools/pegasus/submit_floor_pair.sh` (submitter)。
- `tools/pegasus/admission_registry.json` に 2 entry (plan §4 の逐語、path ソート順)。
- `orchestrator/tests/test_hooks.py` の golden 3 箇所に 2 entry (B1)。
- 新規 `orchestrator/tests/test_floor_pair_job_contract.py` (`__main__` 自走 harness、allowlist 不変)。
- 親: `docs/pegasus-runbook.md` §7.0 投影表 2 行 + §7.8 投入手順 (docs のみ)。`tools/pegasus/README.md`・`orchestrator/tests/README.md`・driver・spec・issuer は 0 byte。
### 4.2 job body の段 (順序固定)
bootstrap (PBS_JOBID / PBS_O_WORKDIR / `FP_NONCE` 32hex / `FP_EXPECTED_HEAD` 40hex / `FP_SPEC_RELPATH` / `FP_SPEC_SHA256` 64hex / `FP_MODE` ∈ {window, finalize} / `FP_WINDOW_ID` (finalize は `none`) / `FP_EVIDENCE_DIR` 絶対 / `FP_ELAPSTIM_REQ` HH:MM:SS) → environment (PATH `/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin` 固定、PYTHON*/LD_*/GIT_* unset、PBS_* は保持) → interpreter (`python3.10 python3.11 python3.12 python3` の順で realpath・実行可・≥3.10) → commands (B3 の 9 本) → checkout (realpath(PBS_O_WORKDIR) == `git rev-parse --show-toplevel` の realpath、`HEAD^{commit}` == FP_EXPECTED_HEAD) → input preflight (spec 実 bytes sha == FP_SPEC_SHA256、`artifacts[]` の binary 全件 実在・実行可・sha 一致) → site (hostname 第一 label 完全一致 `^bnode[0-9]+$`) → time (window mode: `now >= not_before && now + elapstim_s <= not_after`) → scratch (`/scr/${PBS_JOBID//:/_}` を `mkdir -m 0700` 1 回、TMPDIR) → time 再検査 (driver 直前) → driver (background child + `wait`、stdout/stderr を evidence dir へ create-only) → result (`job-result.json` を `open(...,"x")`)。
exit code: 入力不正 2、前段拒否 4、receipt 失敗 5、driver rc は保存して伝播。stderr は固定 token の 1 行 JSON `{"gate":"<段>","reason":"<token>"}`。
### 4.3 submitter
引数 `--workload {rr95,rr50,rr5}` + (`--window {w1,w2}` | `--finalize`) + `--dry-run` + `-h`。pin 表は case 文 (D2138 項 7 の 3 組)。検査順: canonical root → detached (`symbolic-ref -q HEAD` rc=1 のみ受理) → tracked clean (`--untracked-files=no`) → spec 実 file sha == pin && `git show HEAD:<relpath> | sha256sum` == pin → binary 実在・実行可・sha → mode 別: window は時刻 gate (`now >= not_before && now + elapstim_s <= not_after`) + 対象窓 JSONL 不在 (A5) + 他窓 JSONL があれば header `loaded_head` == HEAD (A1); finalize は summary 不在 + 両窓 JSONL 存在 + 各 header `loaded_head` == HEAD + 各末尾 record `"event": "terminal"` (A1/A2) → evidence leaf `mkdir -m 0700` 1 回 (base は `mkdir -p`) → `pre-submit.json` create-only → (dry-run はここで終了、`submit-receipt.json` に `status="dry_run"`) → `cd -P` → `qsub -l elapstim_req=<mode 別> -N fp-<wl>-<w1|w2|fin> -v <8 変数> -o/-e <evidence>/scheduler.std{out,err} tools/pegasus/floor_pair_campaign.sh` → receipt。
walltime: window `24:00:00`、finalize `00:30:00` (submitter 1 箇所、`FP_ELAPSTIM_REQ` として job へ)。
### 4.4 契約 test (実行観測を含む)
plan §5 の 13 関数 + B5 の実行観測 (gate 到達・argv 構築・dry-run 分岐・child rc 回収) + `test_scratch_name_normalizes_colon` (`PBS_JOBID=0:123.nqsv`) + `test_submitter_head_consistency_preflight` (A1: 他窓 header の `loaded_head` 不一致で拒否、一致で通過、不在で通過) + `test_registry_goldens_in_test_hooks` は不要 (test_hooks 自身が検査)。実 qsub・実 driver・hostname 偽装は無し。**job body 全体を実 spec で実行する test は禁止** (compute での受入で `--execute-window` が凍結 dir に書く)。
### 4.5 変異事前登録 (exact diff は author 後に段 6 で固定、対象は一意)
| ID | file / 対象 | old → new | 殺す node | 期待 |
|---|---|---|---|---|
| M0 | job body の説明 comment | `# Window admission` 系の comment 1 行に語を足す | — | SURVIVED (等価) |
| M1 | registry の job body entry | `"class": "dispatch-required"` → `"local-ok"` | `test_floor_pair_job_contract::test_registry_entries` + `test_hooks` の golden node (probe で観測) | KILLED |
| M2 | submitter の rr95 pin | `990e…` → `890e…` | `::test_frozen_spec_pins` | KILLED |
| M3 | job `window_gate` | `now + duration <= not_after` → `<` | `::test_window_gate_boundaries` | KILLED |
| M4 | job hostname gate | 判定 command 全体 → `:` | `::test_hostname_gate` | KILLED |
| M5 | job driver argv | `--execute-window "$FP_WINDOW_ID"` → `--validate-only` | `::test_driver_argv` | KILLED |
| M6 | runbook §7.0 job body 行 | 行削除 | pytest 層 SURVIVED、`python3 tools/check_docs.py` 直接 (DW-O19) | KILLED (checker) |
| M7 | job の site gate 呼出し | `require_compute_hostname ...` → `if false; then ...; fi` | `::test_gate_order_and_calls` (実行観測) | KILLED |
| M8 | submitter の dry-run 分岐 | 条件反転 | `::test_dry_run_has_no_execution` | KILLED |
| M9 | job scratch 名 | `${PBS_JOBID//:/_}` → `${PBS_JOBID}` | `::test_scratch_name_normalizes_colon` | KILLED |
| M10 | submitter の A1 前段 | `loaded_head` 比較を恒真化 (`[[ ... ]] \|\| true` 相当) | `::test_submitter_head_consistency_preflight` | KILLED |
runner argv: `python3 tools/run_tests.py orchestrator/tests/test_floor_pair_job_contract.py orchestrator/tests/test_hooks.py orchestrator/tests/test_plain_runner_coverage.py` (M1 の観測 node は probe 走で採る)。baseline 緑必須。
### 4.6 起動確認 (login) — 完了条件は「到達した gate の記録」
1. `bash -n` 2 本 (author も実走、親も試みる)。
2. submitter `--dry-run --workload rr95 --window w1`: 親が Bash tool から試みる。hook が拒否したら rc と拒否文を記録 (F660 の型、迂回しない)。到達すれば期待 = 窓前で rc=4 `window/before_window`、evidence leaf 未作成。
3. job body の負対照 (PBS env 模擬、`FP_EXPECTED_HEAD` = 実 HEAD、実 spec、実 binary): 同上。到達すれば期待 = `site/compute_node_required` rc=4、scratch・driver・成果物なし。
4. 契約 test (実 spec の field・実登録簿・now 注入) は親が `tools/run_tests.py` で実走 (これは hook の外で確実に走る)。
模擬/実の差は plan §7 の表 + 「hook 拒否で script 未到達」の行を足して insight に載せる。

## 5. scope 外・裁定パッケージ候補 (実装しない)
- 本走の時間予算の実測根拠 (同条件の rep wall の裾・probe・fsync の時間)。24 h は運用上限で成功保証でない。
- 着地後の実行経路確認 (実 qsub、8 変数の伝播、実効 walltime・signal 配送、compute での import・receipt)。= 次の測定 wave の段 1。
- 凍結成果物を失った場合の扱い (terminal 欠落・部分 summary・別 HEAD の窓): 削除・延長・再走せず、別 commit の新凍結 (D2138 却下肢のとおり)。
- 測定後の採用・集約 (D1974・申し送り 6・7)。
