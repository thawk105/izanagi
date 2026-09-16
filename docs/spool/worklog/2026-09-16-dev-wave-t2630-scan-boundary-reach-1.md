---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2630-scan-boundary-reach
seq: 1
title: [T-2630] 非再帰な走査境界から許された variant が別プログラムのまま stock の identity を受け取ることを、既存の変異 harness で計算ノード実測した — 5 変異で到達、修正は起票 (docs + 計測成果物、branch worktree-dev-wave-t2630-scan-boundary-reach、変異 matrix = baseline PASSED・8/8 期待署名一致・MISMATCH 0、probe は probe branch のみで land せず)
---

## 本文

- 依頼と裁定: D2044 項 25 (2026-09-16 ユーザー裁定)「非再帰な走査境界から許された variant が別挙動と stock identity 継承へ
  到達する例を既存の変異 harness で実測する。未到達だけを不存在とは結論しない」。修正は本 wave で実装せず起票して返す。
- 結果: **到達した。** 事前登録 8 変異のうち 5 変異 (M3a / M3b / M4 / M4b / M6) で、実 `source_digest.resolve()` が受理し
  src_token・pre-image・receipt の variant ID が基準の木と byte 一致のまま、実 configure 由来の compile command で前処理した
  `cc/silo/transaction.cc` の TU bytes が別のプログラムになった。M3b (`include/backoff.hh` top-level の
  `#undef/#define SLEEP_READ_PHASE 1`) と M6 (同 `TRACE 1`) は stock genome で `src_token = "stock"`、
  `verification_variant = 19d4249ef295` (pure stock と同じ ID)。M3a は synthetic 枝内の同指令で兄弟 variant と token 衝突
  (`d8a4a10d…`)。対応差は `transaction.cc:278` の `sleepTics(1);` (object にも `rdtscp` ループ)。M6 は
  `assert_trace_diff_matches_head` (規律 1 の diff-of-diffs) も実関数で通過し、object に `izanagi_trace` symbol が 8 個入る
  (後段の nm 検査が捕まえる対象)。M4 (transaction.cc の `#define desired expected` 挟み込み) は TU 差あり・compile 失敗
  (masstree `compiler.hh` の再定義)。M4b (`__atomic_compare_exchange_n` の関数形 macro 挟み込み) は無警告で compile するが
  x86-64 では object 差が `__LINE__` 定数 1 箇所のみ = source 水準の意味差に留まる。対照 M0 (SURVIVED)、M1 (digest 差で
  identity が動く)、M2 (`assert_includes_match_head` 拒否) は登録どおり。
- 機構: `#define` / `#undef` は `-E -P` の出力に現れない (親の前提実測: 断片 3 種が同一 sha `dd769427…`)。3 file を
  include 除去のうえ単独で digest するので、別 file の header・本体へ漏れる効果と include の前後の挟み込みは identity に
  乗らない。include 行一致検査も条件指令検査も止めない。
- 主張の限定 (段 3 レンズ A の A-1/A-2/A-5 を親が現物で裏取り): 継承として実測したのは identity 層 (token・pre-image・
  variant ID = loop の skip key) までである。cache binary は `build_admission.py:674-676` (STOCK_BASELINE は
  `tracked_clean` 必須) が区別でき、`tracked_diff_sha256` は変異ごとに別値だった。receipt 発行・実 loop の skip・実
  workload は未実測。**coder 面からの到達ではない** — hole 内の生指令は `diff_quarantine` の `HOLE_ESCAPE` が拒否する。
  今回の到達は「変異した template を信頼して当てた後、identity 層が受理した」ものに限る。
- 測り方: harness は submodule 内 file を変異できない (`git show HEAD:external/…` が gitlink で fatal) ので、製品の
  template patch `patches/silo-backoff-fixed.patch` を carrier にし、probe test (Codex author、410 行) が
  `patchharness.checkout(PIN, base_dir=<local clone>)` + `applied()` で pin の木へ当て、4 node (stock/variant の identity、
  stock/variant の owner TU 前処理一致) を判定。実 TU 前処理は `condition_meaning_gate` の実 configure→compile command 導出
  (T-2213 の形、永続 cache 直指し、build なし)。probe は **probe branch `worktree-dev-wave-t2630-scan-boundary-reach-probe`
  (tip `e35fb7c4e`、base `a5f953a66` = wave と同じ) にだけ commit** し、wave / main には入れない (逐語は insight の
  `verbatim/probe-test.md`)。計算ノード bnode001、g++ 11.4.0 (`/usr/bin/x86_64-linux-gnu-g++-11`)、10 request
  (2246〜2255.nqsv) 8 分 34 秒、queue 待ち数秒。
- 段 6 レビュー 2 本: probe への must-fix ゼロ。A6-1 (台帳の KILLED 署名を observations の赤理由と照合) を採用して
  全 8 変異の赤理由を現物で確認した。A6-2 (位置差と意味差の区別) により M4b を「source 水準」に限定。
- 親が踏んだこと (F6-1): conftest の autouse `_declare_default_test_site` が全 test の site 判定を中和し、計算ノードでも
  `compilers_for_current_site()` が既定 gcc-13 を返して試行 1 の baseline が同因 4 赤 (dispatch 1 本空費)。fixture
  `_detect_site_under_test` を全 node に要求する fix (Codex) で解消。{{F:conftest-site-neutralized-compute-probe}}。
- 起票: 欠陥は {{F:scan-boundary-directive-leak}}。修正は {{T:scan-boundary-directive-leak-fix}} (裁定パッケージは insight §8:
  (a) `-dD` で指令を pre-image に乗せる [親推奨、golden digest が動くので規律 7 の再検証条件を先に決める]、(b) 指令行の
  HEAD 一致検査、(c) TU 単位 digest、(d) template の信頼境界として限界明記)。
- 工数: Codex 子 7 本 (plan 1、consult 2、author 1、fix 1、review 2、全段 gpt-6-astra / medium)、計算ノード 12 request
  (試行 1 の 2 本を含む)、wall 約 1 時間 20 分 (22:25〜23:50 JST)。
- 一次資料: `output/insights/2026-09-16/t2630-scan-boundary-reach/README.md` (+ `verbatim/`)、job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2630-scan-boundary-reach/` (evidence 10 run 全量)。

## 次の一手差分

### 完了

- [T-2630] 非再帰な走査境界から許された variant の到達例を既存の変異 harness で実測した。5 変異で到達 (identity 同一・
  実 TU 差)。修正は {{T:scan-boundary-directive-leak-fix}} として起票。
  remaining: none
  base: 4977b32a2cb229ef4d54ec3633dd8bd9a4f8b1a0be26c1ad825c3a76cc80ef19

### 新規

- {{T:scan-boundary-directive-leak-fix}} **P1・裁定待ち (実測で確認された正しさ欠陥、{{F:scan-boundary-directive-leak}})**:
  `source_digest` の identity に `#define` / `#undef` の効果を乗せる、または指令を拒否する修正の択一。選択肢 =
  (a) `_cpp_normalize` に `-dD` を足して指令を pre-image に乗せる [親推奨、1 箇所の変更。golden digest
  (`test_source_digest_preimage_join_has_pre_refactor_golden_digests` 等) が動く = identity 版の変更なので規律 7 の
  再検証発火条件を**結果を見る前に**定める]、(b) `assert_includes_match_head` と同型の `#define` / `#undef` 行の HEAD 一致検査、
  (c) 実 include path で TU 全体を digest、(d) 限界として明記し template の信頼境界に委ねる。正例 = 本 wave の M3b / M6、
  負例 = M0 (insight `output/insights/2026-09-16/t2630-scan-boundary-reach/README.md` §8、再現 recipe は §9)。
  M6 は規律 1 側でもあり、最終層 (`_assert_no_trace_symbols`) が残ることを併記して裁定する。
