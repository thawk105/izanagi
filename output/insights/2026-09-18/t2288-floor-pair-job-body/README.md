# [T-2288] (a) B-4 床値 (floor-pair) の窓 job と finalize job を計算ノードで起動する Pegasus job body と submitter を着地させた — 実投入は次の測定 wave (F660)

`authority: none`
`default_effect: no-state-change`

2026-09-18。wave `dev-wave-t2288-floor-pair-job-body`、branch `worktree-dev-wave-t2288-floor-pair-job-body`。起点 local main
`24ede1d11cb33af8d2278cd6d48d29863225465b` (10:43 JST)、段 5 前に `4e3d1df971224b41b04d7899ba8b6615202f2093` へ ff-only (11:14 JST、
編集面に差分なし)。可変状態の正本は worklog 末尾と現行 phase doc であり、本書ではない。

## 依頼と答え

依頼は「[T-2288] (a) B-4 床値 (floor-pair) の run_window / finalize を計算ノードで起動する Pegasus job body を着地させる wave — 凍結済み
3 spec (commit 0b4fbd7a6 の output/env/pegasus/floor-pair/t2288-f1/、窓 w1 2026-09-19〜09-27 / w2 09-29〜10-07 UTC、各 62 標本) を
orchestrator/campaign/floor_pair_driver.py の run_window / --finalize CLI で走らせる job body と submit script を、既存の
tools/pegasus/floor_campaign.sh + submit_floor.sh の型で足し、admission_registry.json (必要なら spawn sites / materializer 登録簿) の閉包を通す。
run_window は site_policy.current_site(require_evidence=True) の証拠を要求する。申し送りは output/insights/2026-09-18/t2288-a5-freeze/README.md
「後続の測定 wave への申し送り」1〜7 (3 段を同じ実行 HEAD で、place は checkout ごと (D2069)、窓の末端に投入しない、create-only)。F660 により
実測 (w1 は 09-19T00Z 以降の session 開始) は含めず、job body の起動確認までとする。Codex author (D95) + 変異事前登録。稼働 t2772 が
orchestrator/tests/test_ccbench_spawn_sites.py / orchestrator/campaign/materializer_admission.py を編集中なので、起動時に編集面を照合し、重なるなら
t2772 の land 後に着手する (重ならない file だけで閉じられる場合に限り先行可)。着手直前の local main から fresh worktree を作る。規律 2 を
緩めない。本題の job body だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」だった。

**答え: 着地させた。** 新規 `tools/pegasus/floor_pair_campaign.sh` (job body、mode = window | finalize) と `tools/pegasus/submit_floor_pair.sh`
(login 側 submitter)、登録簿 2 entry、`test_hooks.py` の golden 3 箇所、新規契約 test `orchestrator/tests/test_floor_pair_job_contract.py`
(22 test)、runbook §7.0 投影表 2 行 + §7.8 投入手順。設計判断は decisions fragment
`docs/spool/decisions/2026-09-18-dev-wave-t2288-floor-pair-job-body-1.md` (fold 後に D 番号が付く)。編集面は t2772 と重ならない
(spawn sites の `.sh` 走査は cmake --build sink だけで、本 job body は build しない)。**実 qsub・計算ノードでの job body 実行・8 変数の伝播・
実効 walltime・signal 配送は実測していない** (F660: 新規 `tools/pegasus/` 実行体は main 着地前に live hook が拒否する)。

## 成果物の形 (要点。契約の正本は決定 fragment と runbook §7.8)

| 項目 | 値 |
|---|---|
| 分割 | 1 job = 1 spec × (1 窓 \| finalize)。6 window job + 3 finalize job |
| job body の段 | bootstrap (`FP_*` 8 変数) → PATH 固定と `PYTHON*`/`LD_*`/`GIT_*` unset → interpreter (≥ 3.10) → 必須 command 9 本 (`git nm pgrep sha256sum hostname date realpath mkdir env`) → checkout (realpath 一致、HEAD == 投入時 HEAD) → spec sha / binary 全件 sha → site (第一 label lowercase の `^bnode[0-9]+$` 完全一致) → 窓の時刻 gate → scratch `/scr/${PBS_JOBID//:/_}` → 時刻再検査 → driver (`-I -B -c` + sys.path 挿入 + `main()`、background child + `wait`) → `job-result.json` (`open(...,"x")`) |
| submitter の前段 | 引数閉集合 `--workload {rr95,rr50,rr5}` + (`--window {w1,w2}` \| `--finalize`) + `--dry-run`、D2138 項 7 の 3 組 pin、detached・tracked clean・実 file と HEAD blob の sha・binary・窓の時刻 gate・対象窓 JSONL 不在・他窓 header `loaded_head` == HEAD・finalize は summary 不在 + 両窓 header 一致 + 末尾 terminal |
| walltime | window `24:00:00` / finalize `00:30:00` (submitter 1 箇所、`qsub -l` と `FP_ELAPSTIM_REQ`) |
| 証拠 | `/work/1/SFC/tanab/izanagi-job-evidence/floor-pair/<nonce>/` (submitter / scheduler / job body で file を分離) |
| 登録簿 | job body `dispatch-required` / `static job-body classification`、submitter `local-ok` / `static login-side submitter classification` |

## 段 3・段 6 が親 brief / plan / 実装を訂正した点 (すべて採用)

- **3 段同一 HEAD は投入時に機械保証されない** (レンズ A1): w1=H1・w2=H2 の投入は driver の finalize まで通る。submitter が他窓 header の
  `loaded_head` を現 HEAD と照合する前段を採った (申し送り 2 の実装であり仮想リスクではない)。
- **finalize は `incomplete` terminal の窓からも `not_generated_*` summary を create-only で作る** (A2): 失敗 summary も 1 回限り。runbook に明記し、
  submitter の finalize 前段 (両窓の末尾 record が terminal) が早すぎる投入を止める。
- **walltime 10 h の根拠は不成立** (A3): 「全 rep timeout の 44.4 h は 5% 判定で不採用になる」は経過時間の上限を与えない。窓の喪失は回復不能で
  要求超過の費用は queue 待ちだけなので、window job を 24 h (gen_S 上限、`b10_backoff_shape_campaign.sh` の先例) にした。成功保証ではない。
- **`test_hooks.py` の golden 3 集合に 2 entry が要る** (B1)、**scratch 名は `0:` 付き job ID を `_` に正規化** (B2)、**driver は session 内で
  `nm -C` を起動するので必須 command に `nm`** (B3)、**python3 shim は本 driver 経路に不要** (B4: 孫 process は binary・pgrep・nm・git)。
- **契約 test は関数抽出だけでなく分岐・配列・dry-run・child rc・main の呼出し列を実行観測する** (B5、段 6 F6)。
- **計算ノードの job は SIGTERM を SIG_IGN で継承する (F1012)**: 焦点走 1 で `test_child_rc_collection` の TERM 経路が赤 (`reason=completed`)。
  test 側の子で `SIG_DFL` + unblock を明示して緑。job body 側の TERM trap も同じ理由で計算ノードでは発火しない可能性があり、runbook §7.8 に
  「trap の存在を終了記録の保証と読まない」と書いた。
- **signal 観測時に driver rc=0 を signal rc で上書きする分岐は裁定外** (A2/B3): 削除し、signal は `reason=signal_observed` に残す。
- **環境消去は `PYTHON*`/`LD_*`/`GIT_*` の prefix 全件** (B1 レビュー): 名指し 5 個から prefix 全件 unset へ。
- runbook の「9 job すべて同じ HEAD」は申し送り 2 (各 spec の 3 段) より強い → 各 spec の 3 段に (A3 レビュー)。「実配送を確認してから最初の投入」は
  循環 → 次の測定 wave の初回実行で確認し記録する (A8)。

不採用 (記録のみ): finalize では `nm`/`pgrep` は不要 (loader は sha だけ) だが集合を mode で分けない / job body の spec 名 3 本の再列挙は
submitter と同じ閉集合の二重管理だが費用が小さい / `driver_stdout_sha256`・`qsub.rc` は裁定 §4.2 と `submit_floor.sh` の型 / hostname の lowercase
化と `--help` alias は裁定の逐語より広いが `site_policy._first_label` と整合 (裁定側を補正)。

## 起動確認 (login) — 到達した gate の記録

| 手段 | 結果 |
|---|---|
| Bash tool から `bash -n tools/pegasus/submit_floor_pair.sh` / `floor_pair_campaign.sh` | live hook (`hooks/guard_bash.py`、main の登録簿) が「未登録 Pegasus 実行体」で**拒否** (F660 の型)。到達 gate なし (script 未起動)。迂回しない |
| submitter `--dry-run` / job body の PBS env 模擬 | 同じ理由で試みず (同 hook が同じ path を拒否する)。負対照の観測は無し |
| 契約 test (`tools/run_tests.py`、計算ノード) | `test_scripts_parse` (`bash -n` 2 本 rc=0)、実関数の抽出実行 (窓 gate 全 6 窓 × 5 境界、hostname 正例 3 / 負例 3、gate 到達順 (site → bounds → time → scratch → time → driver、途中拒否で後続未到達)、main の呼出し列 (J: bootstrap → … → admit_and_run、HEAD 不一致で admit_and_run 未到達; S: parse_args → … → submit_or_dry_run、check_outputs 拒否で未到達)、driver argv 配列 (window / finalize)、dry-run 分岐 (stub qsub の呼出し痕跡)、child rc 回収 (rc 7、TERM 後 rc 0 と `signal_observed`)、`clean_environment`、scratch 名、A1/A2 の合成 header・terminal 正負例、pin の三者一致 (D2138 の表・submitter の case・実 file sha)、登録簿 2 entry) |
| Codex author / fix 子 | `bash -n` submitter rc=0 (author)。job body の `bash -n` は Codex 側 hook も拒否 |

模擬 / 実の差: 実関数を実 spec の field・実登録簿・実 binary bytes で走らせたのは契約 test (計算ノード)。実 qsub、PBS の env 配送、実 hostname、
実 driver 起動、実 signal 配送はすべて未観測。計算ノードでの正例は次 wave。

## 実走の記録

| 走 | 結果 |
|---|---|
| 焦点走 1 (統合 commit 20aca3006、request 5523.nqsv、13 秒) | `test_floor_pair_job_contract` + `test_hooks` + `test_plain_runner_coverage`: 503 passed / 1 failed (TERM 経路、上記) / 1 skipped |
| 焦点走 2 (fix commit cbcb4bf95、request 5553.nqsv、82 秒) | 同 3 file + `test_ccbench_spawn_sites`: **579 passed / 3 skipped / rc=0** |
| login 自走 harness | 統合 commit 18/18 (1.6 秒)、fix 後 22/22 (1.5 秒) |
| `python3 tools/check_docs.py` | 統合 commit 後 rc=0 (登録簿と投影表の集合一致) |
| `check_ai_provenance.py --message-file` | 統合 commit・fix commit とも 1 件・違反なし |
| `--validate-only` 3 本 (login、HEAD 24ede1d11、place 後) | rc=0・stderr 0 byte (前提実測、`validate-<wl>.json` は job dir) |

## 変異 matrix (段 4 事前登録 M0〜M10、fix commit cbcb4bf95 に対して)

harness = `tools/mutation_harness.py --runner-mode dispatch --detached` (container worktree `mut-dev-wave-t2288-floor-pair-job-body`、
HEAD cbcb4bf95)、runner argv = `python3 tools/run_tests.py orchestrator/tests/test_floor_pair_job_contract.py orchestrator/tests/test_hooks.py
orchestrator/tests/test_plain_runner_coverage.py -q -rf --force-dispatch`、dispatch 上書き queue_wait 1800 / grace 600、spec `timeout_seconds` 2700。
probe 走 (全件 SURVIVED 期待、`mutation-probe.json`、spec sha `bd61e8d9…5a70`) で観測 node の完全集合を採り、本走 (`mutation-ledger.json`、
spec `mutation-spec-final.json` sha `46e9d17c…81bf`) を期待集合の完全一致で判定した。M6 は pytest 層では殺せない (runbook 投影表の検査は
`tools/check_docs.py`) ので DW-O19 の一時変異で直接測った。

| ID | 変異 (file / old → new) | 殺す node | 結果 |
|---|---|---|---|
| M0 | job body の comment 1 行に語を足す (等価) | — | **SURVIVED** (等価の正例、注入実在は台帳の diff) |
| M1 | 登録簿の job body entry `dispatch-required` → `local-ok` | `test_floor_pair_job_contract::test_registry_entries`、`test_hooks::test_bash_pegasus_registry_schema_and_fixed_classes`、`::test_bash_pegasus_registry_login_and_suspect_bits_are_pinned`、`::test_bash_sanctioned_pegasus_paths_are_derived_from_registry` | **KILLED** (4/4) |
| M2 | submitter の rr95 pin sha 先頭 `9` → `8` | `::test_frozen_spec_pins` | **KILLED** |
| M3 | job `window_gate` の `<=` → `<` | `::test_window_gate_boundaries` | **KILLED** |
| M4 | job hostname 判定 command → `:` | `::test_hostname_gate` | **KILLED** |
| M5 | job driver argv `--execute-window "$FP_WINDOW_ID"` → `--validate-only` | `::test_driver_argv`、`::test_no_build_or_output_replacement` | **KILLED** (2/2) |
| M6 | runbook §7.0 の job body 投影行を削除 | `python3 tools/check_docs.py` 直接 | **KILLED** (rc=1、違反 1 件だけ: `registry_only=[floor_pair_campaign.sh …]`、`mutation-m6-check_docs.log`。復元後 diff 0) |
| M7 | job の `require_compute_hostname` 呼出しを `if false` へ | `::test_gate_order_and_calls` | **KILLED** |
| M8 | submitter の `if (( DRY_RUN ))` を反転 | `::test_dry_run_has_no_execution` | **KILLED** |
| M9 | job scratch 名の `${PBS_JOBID//:/_}` → `${PBS_JOBID}` | `::test_scratch_name_normalizes_colon` | **KILLED** |
| M10 | submitter の `loaded_head` 比較を `if False` へ | `::test_submitter_head_consistency_preflight`、`::test_finalize_preflight_requires_terminal` | **KILLED** (2/2) |

summary: baseline PASSED (508 passed / 1 skipped、32 秒)、KILLED 9 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0、matching 10/10。M1〜M10 の kill は
shell・登録簿・docs の契約に対するもので、driver の検査強度の証明ではない (段 3 A6 / 段 6 A9・B8: 前段の拒否は driver の変異を mask しうる)。

## 主張しないこと

- **実 qsub・PBS の env 配送・実効 walltime・signal 配送・計算ノードでの job body / submitter の実行**は観測していない。契約 test が
  実関数を実 spec の field と実登録簿で走らせたことと、`bash -n` が通ったことだけを観測した。
- **window job の 24 h が足りることを主張しない。** 本走 (62 標本 × 2 side × 2 測定 × 5 rep) の所要分布は測っていない。走行が walltime を
  超えれば窓は失われ、再走は無い。
- job body の TERM trap が計算ノードで発火することを主張しない (F1012 の継承)。
- 3 段同一 HEAD・create-only・窓の時刻の保護は「早期拒否」であって機械的な不変性の保証ではない。同時投入 (別 nonce) は排除しない。
- 前段 (spec sha・HEAD・binary・site) の複製が driver の検査を代替することも、driver の検査強度を高めたことも主張しない。
- 床値の生成・採用・§5 の記入・本書の発効はいずれも主張しない。

## 次の測定 wave への申し送り

1. **初回実行で実配送を確認して記録する**: 到達した段 (`job-result.json` の `gate`/`reason`)、8 変数の値、`scheduler.std{out,err}`、
   `driver.stdout` の result JSON、rc。job body の TERM trap の発火有無。
2. **投入元 checkout**: detached、tracked clean、`place` 済、各 spec の 3 job を同じ `H` から。`H` は本 wave の着地を含む main 以降。
3. **w1 は 2026-09-19T00:00Z 以降に投入** (`now + 24h <= 2026-09-27T00:00Z` まで)。w2 は 09-29T00:00Z 以降。finalize は両窓の terminal の後。
4. `--dry-run` は gate を全部通して qsub だけ省く。窓前は `window/before_window` で止まる (これが本 wave で観測できなかった負対照)。
5. 3 spec の並走可否・queue 待ち・`/scr` 容量は資材が保証しない。

## 生証拠

| path | 中身 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief (親)。(P1)〜(P10) と前提実測 |
| `verbatim/s2-plan.md` | 段 2 plan (codex、read-only)。訂正 6 点 |
| `verbatim/s3-consult-A.md` / `s3-consult-B.md` | 段 3 敵対相談 (A = 凍結成果物の保護、B = 実行面・登録簿・test)。must-fix 3 + 4 |
| `verbatim/s4-ruling.md` | 段 4 裁定 (親)。plan v2、変異事前登録 |
| `verbatim/s5-author.md` | 段 5 author の報告 (終端 commit c913aca99、テスト未実走) |
| `verbatim/s6-review-A.md` / `s6-review-B.md` | 段 6 敵対レビュー (A = 過剰・削除、B = 逐語照合・実効性)。両者 NO-GO |
| `verbatim/s6-ruling.md` | 段 6 裁定 (親)。F1〜F6 と不採用の理由 |
| `verbatim/s6-fix1.md` | 段 6 fix の報告 (終端 commit 9c9607e81、自走 22/22) |
| `verbatim/focus-1.log` / `focus-2.log` | 焦点走 1 (5523.nqsv、赤 1) / 2 (5553.nqsv、579 passed) |
| `mutation-spec-probe.json` / `mutation-probe.json` | probe の spec と台帳 (観測 node の採取) |
| `mutation-spec-final.json` / `mutation-ledger.json` | 本走の spec と台帳 |
| `mutation-m6-check_docs.log` | M6 の直接測定 |

prompt 全文・launcher・validate 出力・author / fix の patch は job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-job-body/`) に
残した。
