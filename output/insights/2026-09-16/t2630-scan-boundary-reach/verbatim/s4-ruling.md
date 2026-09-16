# 段 4 裁定 — [T-2630] 走査境界の到達実測

基準: 親 brief (s1-brief.md)、段 2 plan (s2-plan-out.md)、段 3 所見 A-1〜A-7 (s3-a-out.md)、B-1〜B-3 (s3-b-out.md)。
裁定 inbox 再走査 (local main `045d6dbe2`): T-2630 の新裁定なし (worklog は持ち越し、decisions は D2044 項 25 のみ)。

## 所見の裁定

| 所見 | 判定 | 採否 | 根拠 (親が現物で確認) |
|---|---|---|---|
| A-1 cache 継承は admission 層で分離される | real | 採用 (主張を限定) | `build_admission.py:674-676` は STOCK_BASELINE に `src_token==stock ∧ tracked_clean ∧ pin==CURRENT` の 3 条件。dirty 木は stock 扱いされない |
| A-2 hole 内の生指令は coder 検疫が拒否 | real | 採用 (「coder 面から到達」を撤回) | `diff_quarantine.py:492-497` `_DIRECTIVE_RE` → `HOLE_ESCAPE`。template patch :62-67 の編集契約も macro 定義を禁止 |
| A-3 M6 は後段の symbol 検査が捕捉しうる | real | 採用 (層ごとに別記録) | `buildcache.py:3495-3499` cache hit でも `_assert_trace_diff` + `_assert_no_trace_symbols`、`:3782-3786` `izanagi_trace` 拒否 |
| A-4 製品経路と probe の差の表 | real | 採用 (insight に表を残す) | — |
| A-5 継承候補の強さは skip key > cache > receipt | real | 採用 | `loop.py:695-706` `variant_id(g, src_tok)` が `done` にあれば skip。`pipeline.py:137-143` stock token は src を省く = stock genome と同一 ID |
| A-6 N2 の差は原因 (sleepTics(1) 等) まで確認 | real | 採用 (probe は raw diff を保存、insight で対応差を名指し) | — |
| A-7 stdin 実測は動機に留める、`#undef` は `_dump_macros` に反映される | real | 採用 | `source_digest.py:1702-1726` |
| B-1 resume/TIMEOUT/MISMATCH の意味論 | real | 採用 (再走は別 run、旧台帳保存) | `mutation_harness.py:974-1008, 2782-2788` |
| B-2 計算ノードでの証拠出力先は env で渡せない | real | 採用 (probe 内で共有 FS の固定 root + run ごとの一意 dir) | `dispatch_compute.py:118-132` allowlist |
| B-3 probe branch を wave の祖先にしない | real | 採用 (両 branch を `a5f953a66` から分岐) | — |
| plan: M4 は再宣言で compile 不能 | real | 採用 (対照として残し、M4b を追加) | `atomic_tool.hh:10` `uint64_t expected, desired;` |
| plan: login の `compilers_for_current_site()` は g++-13 | real | 採用 (本走は compute) | `buildcache.py:1861-1865` |

## plan v2 (段 2 からの差分)

1. **主張の限定。** 到達の定義 = 「実 `resolve()` が受理し、(stock genome で) token `stock` / (variant genome で) HEAD template 木と同じ token を返し、かつ実 TU の前処理 bytes が HEAD template 木と意味的に異なる (対応差を名指しできる)」。**書かない**: 「製品経路が許可した coder variant」「stock の certified 結果 / cache binary / receipt を継承した」「実 workload の結果が変化した」「perf binary の symbol 検査まで通過した」「非再帰境界に穴は存在しない」。消費側への影響は A-5 の表で「skip key の衝突 (実測: ID 一致)」「cache (admission で分離、file:line)」「receipt (verifier が admission を束縛、file:line)」を分けて書く。
2. **変異 8 件** (mutation-spec.json、sha256 は投入時に固定): M0 comment-only (SURVIVED, [])、M1 synthetic 枝の実コード編集 (KILLED [N1b,N2b])、M2 `#include <cstdint>` 追加 (KILLED [N1a,N1b,N2a,N2b])、M3a hole 内 `#undef/#define SLEEP_READ_PHASE 1` (KILLED [N2b])、M3b top-level 同 (KILLED [N2a,N2b])、M4 transaction.cc の `desired`/`expected` 挟み込み (KILLED [N2a,N2b]、compile 不能の対照)、**M4b** (新規) transaction.cc の `__atomic_compare_exchange_n` 関数形 macro 挟み込みで epoch CAS の memory order を relaxed 化 (KILLED [N2a,N2b]、compile 可否は `-c` 観測で記録)、M6 top-level `#undef/#define TRACE 1` (KILLED [N2a,N2b])。M5/M7 は初回 matrix から外す。
3. **probe test** `orchestrator/tests/test_t2630_scan_boundary_reach.py` — probe worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2630-scan-boundary-reach-probe` (branch `worktree-dev-wave-t2630-scan-boundary-reach-probe`、base `a5f953a66`) にだけ commit。wave branch には入れない。node 4 本 (`test_stock_identity` / `test_variant_identity` / `test_stock_owner_tu` / `test_variant_owner_tu`)。reference = superproject 固定 HEAD の `git show HEAD:patches/silo-backoff-fixed.patch` bytes、current = working tree の同 file。同一 clone worktree (`patchharness.checkout(PIN, base_dir=<local clone>)`) で reference→観測→復元、current→観測→復元。genome = `Genome("silo", {"BACKOFF_FIXED": -1})` / `{"BACKOFF_FIXED": 1}`。compiler = `compilers_for_current_site()` を実 path に解決 (compute 前提)。識別子は実 `source_digest.resolve` + `canonical_source_preimage_bytes` + `resolve_evidence` (tracked_diff_sha256 等を証拠に記録)。TU 前処理は `condition_meaning_gate` の `capture_define_inputs` / `make_define_request` / `_configure_compile_commands` / `_select_owner_entry` / `_entry_argv` / `_preprocess_argv` を実関数で使い、stdout を bytes で保存。configure 引数は `p3_s4_loop._condition_gate_offline_configure_args` 由来 + `CMAKE_PREFIX_PATH` (gflags/glog) + `CMAKE_BUILD_TYPE=Release` + `ENABLE_SANITIZER=OFF` + 実 C compiler + `CCBENCH_TRACE=0`。`FETCHCONTENT_BASE_DIR` は scratch、`FETCHCONTENT_SOURCE_DIR_*` は永続 cache 直指し (build しない)。追加観測 (node の合否に入れない): `assert_trace_diff_matches_head` の成否、`-c` による object 生成の成否と objdump 差 (should)、cache の前後 inventory (file 名 + sha) の差。証拠は共有 FS の固定 root `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2630-scan-boundary-reach/evidence/<hostname>-<UTC時刻>-<pid>/` に run ごとに保存し、harness stdout に path と sha を出す。観測の失敗は fixture ERROR にせず各 node の call 内で例外化 (FAILED 署名)。環境不足で skip して baseline 緑にしない。
4. **harness 投入形** (親が実行): `env IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600 IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600 IZANAGI_DISPATCH_WALLTIME_OVERRIDE=01:00:00 python3 <PROBE_WT>/tools/mutation_harness.py --repo <PROBE_WT> --spec <JOB>/mutation-spec.json --expected-spec-sha256 <sha> --out <JOB>/mutation-out.json --attempt-out <JOB>/mutation-attempt-1.json --wrapper-attempt 1 --runner-mode dispatch --detached -- python3 tools/run_tests.py -rf orchestrator/tests/test_t2630_scan_boundary_reach.py -n 0 --force-dispatch`。detach は `.sh` 2 枚 (launcher/detach)。実走前に `--plan-only`。
5. **生死実験** (本走前): (a) 計算ノードの configure + `-E` は T-2213 の実績 (bnode006、1832.nqsv) で代替、(b) 変異版 patch の `git apply --check` は実装子が local clone の pin に対して行い報告、(c) baseline 4 node 緑を harness の baseline run で確認 (別走しない)、(d) M0 緑・M1 [N1b,N2b]・M2 全赤の対照は本走の台帳で読む。
6. **記録**: insight `output/insights/2026-09-16/t2630-scan-boundary-reach/README.md` + `verbatim/` (probe 本文は `.md` へ逐語、証拠 diff は `.diff.txt`)。到達例ごとに (通った境界、継承した identity (token と variant ID)、対応差、compile/link の可否、後段で止める層の有無 file:line)。spool fragment: worklog、failures 候補 (到達時)、修正 T の起票文。
7. **scope 外 (実装しない)**: gate の修正 (再帰走査、指令の pre-image 化、hole 外の指令検査など)。到達時は「実測で確認された正しさ欠陥」として起票して返す。

## 変異事前登録 (DW-M01)

各変異の赤理由は 1 つ: M1 = digest 差 (`compute`)、M2 = `assert_includes_match_head` 拒否、M3a/M3b/M4/M4b/M6 = 実 TU 前処理 bytes 差 (identity は同一)。前後・内側に同じ入力を拒否する別層は resolve 内には無い (A-2 の coder 検疫は `resolve` の外、template 適用経路では発火しない)。
spec の sha256 は投入時に `sha256sum` で固定し、insight に書く。
