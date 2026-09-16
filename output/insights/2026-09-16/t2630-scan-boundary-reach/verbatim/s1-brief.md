# 段 1 brief — [T-2630] 非再帰な走査境界から許された variant の到達実測

- 研究前進: 論文の正しさ主張 (variant identity = 実ビルドと一致、絶対規律 2) を支える `source_digest` の走査境界に穴があるかを実測で確定する。到達すれば「実測で確認された正しさ欠陥」として起票して返す (修正は本 wave 外)。完了判定 = 変異 harness の台帳 (baseline PASSED + 各変異の failed_nodes 署名) と、到達例ごとの構造化記録 (どの境界を通り・どの identity を継承し・実 TU がどう違うか) が insight にある。
- scope: 到達実測のみ。gate / 検査 / 台帳 / 一般化の追加なし。修正なし。未到達だけを不存在と結論しない。
- 確定済みユーザー裁定: D2044 項 25 (既存 harness で実測、未到達≠不存在)。command 引数: 計算ノードへ dispatch、子が編集中の worktree で probe しない、local main から fresh worktree、規律 2 を緩めない。

## 前提の実測 (brief 前に済)
1. checker と同じ argv (`-E -P -nostdinc -Werror=undef -std=c++20 -O3 -DNDEBUG …`) で、`#define X Y` / `#undef X` の挟み込みと `#undef Linux` は stock と byte 一致 (sha `dd769427…`、g++ 11.4.0、login pegasus02)。指令は消費され、`-P` が空行も畳む。
2. harness (`tools/mutation_harness.py`) は superproject 固定 HEAD の blob (`git show HEAD:<rel>`) しか変異できない。`git show HEAD:external/ccbench/cc/silo/transaction.cc` は `fatal: … not in 'HEAD'`。→ 変異対象は superproject tracked の carrier = template patch `patches/silo-backoff-fixed.patch` (製品経路 `patchharness.applied()` が submodule へ適用)。runner は `tools/run_tests.py <固定 HEAD で tracked な test>` に限られる。
3. conftest の real-repo guard (`patchharness._guard_real_shared_checkout`) は実共有 submodule の git common-dir 同一性で発火する。同 commit の local clone を `checkout(PIN, base_dir=clone)` の base にすれば登録不要。
4. 実 TU (`cc/silo/transaction.cc`) の `-E` には masstree の `config.h` が要る (T-2650)。T-2213 と同じく永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache/<name>` を `-DFETCHCONTENT_SOURCE_DIR_*` で直指しし、configure + `-E` のみ (build しない → cache は汚れない)。gflags/glog は `/work/SFC/tanab/ss2pl-study-deps/{gflags,glog}-install` (`CMAKE_PREFIX_PATH`)。compile command の導出は既存 `condition_meaning_gate._configure_compile_commands` / `_preprocess_argv` を再利用。
5. CCBench は `-Wall -Wextra -Werror` (`cmake/CompileOptions.cmake:32`)。警告を出す変異 (builtin 再定義) は build で fails-closed。`#undef` → `#define` の再定義は無警告。
6. 既存被覆: D34 の「残る穴」= computed include のみ。T-148 レビュー A-n2 (`#undef` 未モデル) は「記録のみ (alias 源にならない)」。include 先 header への効果・file 間の漏れは source_digest では未記録 → 純増。
7. `assert_trace_diff_matches_head` (規律 1 の diff-of-diffs) も file 単独・include 除去で動く → backoff.hh からの `TRACE` 漏れは transaction.cc 側で不可視 (規律 1 側の候補)。
8. 消費側: `src_token == "stock"` は loop の skip / buildcache の stock 継承に直結 (`test_loop_identity_skip_is_visible_when_stock_id_terminal`)。

## 成果物影響 (DW-G05) と凍結 pin 閉包 (DW-O09)
- 放置時: 到達例の形の variant は `src_token == "stock"` (または兄弟 variant の token) となり、stock の certified 結果・cache binary・verification receipt を**別のプログラムが継承**する = certified 選択の受理集合が破れる (規律 2)。TRACE 漏れなら perf build に trace が混入する (規律 1)。
- 凍結 pin: `patches/silo-backoff-fixed.patch` は `orchestrator/campaign/paper_story_a1_source.v1.json` の `patch_sha256` で pin。本 wave は committed bytes を変えず、harness の一時変異は scratch worktree 内で復元検査付き → `DW-O09` / `O10` 不成立。probe test は sha pin に依存しない (`patchharness.applied()` は sha を見ない)。

## 不変条件
- `source_digest.py` 等の gate を 1 byte も変えない (規律 2)。probe を main へ land しない。実共有 submodule に触れない。凍結 artifact の committed bytes を変えない (harness の一時変異は復元、DW-O19)。計測は計算ノード dispatch。

## 成果物の形
- (a) probe test `orchestrator/tests/test_t2630_scan_boundary_reach.py` — Codex author が書き、**probe branch にだけ commit** (harness の固定 HEAD 束縛のため)。wave branch には入れず land しない。逐語は insight `verbatim/*.md` へ (`.py` を repo に残さない)。
- (b) 変異 spec (`izanagi-dev-wave-mutation-spec/v1`、job dir、repo 外)。
- (c) harness 台帳 (job dir) + insight `output/insights/2026-09-16/t2630-scan-boundary-reach/README.md`: 到達例ごとに (通った境界、継承した identity、実 TU の差分 `.diff.txt`、compile/link の可否)。
- (d) `docs/spool/` fragment (worklog、到達すれば failures 候補 + 修正 T 起票)。

## 変更面 (実アンカー)
- 新規 (probe branch のみ): `orchestrator/tests/test_t2630_scan_boundary_reach.py`
- 一時変異 (harness が復元): `patches/silo-backoff-fixed.patch` の backoff.hh hunk `@@ -11,6 +11,15 @@` (include 直後) と `@@ -91,9 +100,29 @@ public:` (EVOLVE-BLOCK)。transaction.cc 用 hunk の追加は patch 末尾。
- 読み取りのみ: `source_digest.py` (`resolve` `compute` `_include_lines` `_assert_conditional_macros_covered` `_worktree_defines`)、`patchharness.py` (`checkout` `applied`)、`condition_meaning_gate.py` (`_configure_compile_commands` `_preprocess_argv`)、`p3_s4_loop.py:346` (`_condition_gate_offline_configure_args`)、`buildcache.compilers_for_current_site`。

## 変異 (仮説。段 4 で事前登録)
probe の node (仮): N1a = stock genome (BACKOFF_FIXED=-1) の `resolve()` が `"stock"`; N1b = variant genome (synthetic 枝 live) の token が HEAD template 適用木の token と一致; N2a = stock genome の実 TU `-E -P` が HEAD template 適用木と一致; N2b = variant genome 同。baseline (未変異 template) は 4 node 緑。KILLED/SURVIVED は failed_nodes の署名で読む (**KILLED = 到達ではない**)。
- M0 comment-only (対照) → SURVIVED
- M1 synthetic 枝の実コード編集 (正例) → KILLED [N1b, N2b]
- M2 `#include` 行追加 (正例、include-match gate) → KILLED [N1a, N1b, N2a, N2b]
- M3a `#undef SLEEP_READ_PHASE` + `#define SLEEP_READ_PHASE 1` を synthetic 枝内 (coder 面) → 仮説: KILLED [N2b] = 兄弟 variant と identity 衝突
- M3b 同を backoff.hh の include 直後 (top-level) → 仮説: KILLED [N2a, N2b] = stock 継承
- M4 `#define desired expected` / `#include "include/atomic_tool.hh"` / `#undef desired` の挟み込み (transaction.cc hunk) → 仮説: KILLED [N2a, N2b] = stock 継承 (include 行不変で include-match を素通り)
- M6 `#undef TRACE` + `#define TRACE 1` top-level → 仮説: KILLED [N2a, N2b] = stock 継承 + 規律 1 (link 可否は別途)
- 任意: M5 `#undef Linux`; M7 `NO_WAIT_LOCKING_IN_VALIDATION` 0 化

## 環境・分割
- 前提実測 = login pegasus02。harness 本走 = `--runner-mode dispatch` (計算ノード、機体固有は `tools/pegasus/README.md`)。harness の `--repo` = probe branch tip の clean な別 worktree。compiler = `compilers_for_current_site()` (g++ 11.4.0、g++-13 不在)。
- 段 2 plan 1 子 (read-only)。段 3 consult 2 子 (レンズ A = probe の妥当性・模擬差・F29・恒真; レンズ B = 変異設計・到達判定の逃げ道・harness/patch 契約)。段 5 author 1 子 (probe test)。段 6 review 2 子 + fix。実走・記録は親。

## 割れうる前提 (親の provisional 裁定 = 攻撃対象)
- (P1) real-repo guard を local clone で外すのは「登録の回避」ではなく guard の対象外 (guard は実共有 checkout の保護)。同 commit なので模擬ではない。
- (P2) 永続 cache 直指し (configure + `-E`、build なし) で得た TU 前処理は実 build の compile command と同等で、cache を汚さない。
- (P3) 変異の判定は node 署名で読む。KILLED を「到達」と読まない。恒真化 (baseline が空同値で緑) を避けるため、N2 は HEAD template 木の `-E` 出力と byte 比較する。
- (P4) carrier = template patch (hunk 算術あり) を、probe test 内の定数 (単純) より優先する — 製品経路・tree 状態の忠実さのため。
- (P5) probe を wave branch に land しない (probe branch + verbatim `.md`) が、「既存 harness で実測」と「probe を repo に入れない」の両立形。
