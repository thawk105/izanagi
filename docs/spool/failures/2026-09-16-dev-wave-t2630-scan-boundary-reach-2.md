---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2630-scan-boundary-reach
seq: 2
---

## 新規

### {{F:scan-boundary-directive-leak}}. 非再帰な走査境界を `#define` / `#undef` の漏れと include の挟み込みが抜け、別のプログラムが stock の identity を受け取った [恒真ゲート] [テスト代表性]

- 事象: 2026-09-16 [T-2630] の計算ノード実測 (bnode001、変異 harness 10 request) で、`include/backoff.hh` の
  include 直後に `#undef SLEEP_READ_PHASE` + `#define SLEEP_READ_PHASE 1` を置いた variant (M3b) が、実
  `source_digest.resolve()` で `src_token = "stock"`、pre-image と receipt の variant ID (`19d4249ef295`) も pure stock と
  一致したまま、実 configure 由来の compile command で前処理した `cc/silo/transaction.cc` に `sleepTics(1);` が入り、object
  も別物になった。同じ形で `TRACE 1` を漏らす M6 は `assert_trace_diff_matches_head` (規律 1 の diff-of-diffs) も通過し、
  object に `izanagi_trace` symbol が 8 個入った。synthetic 枝内に置く M3a は兄弟 variant と token 衝突、`#include` の前後で
  macro を定義・解除する挟み込み (M4 / M4b) も include 行一致検査を素通りした (M4 は compile 失敗、M4b は x86-64 で生成
  コード不変)。対照 M0 / M1 / M2 は登録どおり。
- 根本原因: identity は `EVOLVE_BLOCK_SOURCES` の 3 file を `#include` 除去のうえ**単独で** `-E -P` した出力しか見ない。
  `#define` / `#undef` は前処理器が消費して出力に現れず、file 自身の本文がそのマクロを使わなければ digest は動かない。
  一方、実 TU は 3 file と header を 1 つの翻訳単位として組むので、指令の効果は後続 header と別 file の本体へ届く。
  include 行の HEAD 一致検査は include 行そのものしか見ず、条件指令検査は `#define` 本体の `##` と `__has_include` しか
  見ない。T-148 (2026-07-28) の A-n2「`#undef` 未モデル」は file 内の条件枝の論点で、file 間の漏れは扱っていなかった。
- 恒久対応: 修正は {{T:scan-boundary-directive-leak-fix}} として起票 (裁定待ち。選択肢は
  `output/insights/2026-09-16/t2630-scan-boundary-reach/README.md` §8、親推奨は `_cpp_normalize` への `-dD`)。現行で
  残る層は `build_admission.py:674-676` (STOCK_BASELINE は `tracked_clean` 必須、`tracked_diff_sha256` は変異ごとに別) と
  `buildcache._assert_no_trace_symbols` (M6 の symbol を binary で捕まえる対象)、coder 面は `diff_quarantine` の
  `HOLE_ESCAPE` (hole 内の生指令を拒否)。**identity 層 (loop の skip key) には無い。**
- 再発検知: 同 insight §9 の recipe で変異 harness を再走する (M3b / M6 が正例、M0 が負例)。修正後は M3b / M6 の
  identity node が赤 (別 identity) になることで確認する。

### {{F:conftest-site-neutralized-compute-probe}}. pytest 内の計算ノード probe が既定 compiler (g++-13) を掴んだ — autouse fixture が site 判定を中和していた [テスト代表性] [手順漏れ]

- 事象: 2026-09-16 [T-2630] の変異 harness 試行 1 で、計算ノード bnode001 の baseline (2243.nqsv) が 4 node 同因
  `FileNotFoundError: site compiler cc=gcc-13 unavailable` で赤になり、harness が中止 (dispatch 1 本と試行 1 本を空費)。
- 根本原因: `orchestrator/tests/conftest.py` の autouse fixture `_declare_default_test_site` が全 test で
  `site_policy.socket.gethostname` を `"test-host"`、`_has_nqsv` を `False` に差し替えるため、pytest の中では
  `buildcache.compilers_for_current_site()` が計算ノード上でも `PEGASUS_COMPUTE` にならず既定の `gcc-13/g++-13` を返す。
  段 3 の整合レンズは real-repo guard は見たが、この autouse は見落とした。
- 恒久対応: memory `compute-pytest-probe-needs-detect-site-fixture` — pytest 経由の計算ノード probe は全 node に fixture
  `_detect_site_under_test` を要求し、`environment.json` に `site_policy.current_site()` を記録して `PEGASUS_COMPUTE` を
  実測で確認する。fix commit は probe branch `e35fb7c4e`。
- 再発検知: probe の環境記録に `site` が無い、または `PEGASUS_COMPUTE` でない run の結果を本走として読まない。
