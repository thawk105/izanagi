# [T-2630] 非再帰な走査境界から許された variant が、別のプログラムのまま stock の identity を受け取ることを実測した

`authority: none` / `default_effect: no-state-change` — これは**実測記録**である。可変状態の正本
(worklog 末尾・現行 phase doc) ではなく、gate の受理集合も 1 byte も変えていない。

- 実測日: 2026-09-16 (JST 23:37〜23:46、UTC 14:37〜14:46)
- 実測機: 計算ノード `bnode001` (NQSV request `2246`〜`2255.nqsv`、10 本、いずれも `accounting` 済み)
- 基準 commit: izanagi `a5f953a66` (wave / probe branch の共通 base)、CCBench pin `511c9538e4e8efa54b45cda62e72389ed3b706ec`
- 依頼: 「非再帰な走査境界から許された variant が、別挙動と stock identity 継承へ到達する例を既存の変異 harness で実測する
  (D2044 項 25)。未到達だけを不存在とは結論しない。到達すれば構造化して記録し、修正は起票して返す (本 wave では実装しない)。」

---

## 1. 結論を先に

**到達した。** 事前登録した 8 変異のうち 5 変異 (M3a / M3b / M4 / M4b / M6) で、`source_digest.resolve()` の
実関数が variant を受理し、**identity (src_token、pre-image、receipt の variant ID) は基準の木と byte 単位で同一**のまま、
実 configure が導いた compile command で `cc/silo/transaction.cc` を前処理した bytes は**別のプログラム**になった。
対照 3 変異 (M0 / M1 / M2) は事前登録どおりの向きに動き、変異 harness の台帳は 8 件すべてが期待署名と一致した
(`MISMATCH 0`)。

| 到達例 | 通った境界 | 継承した identity | 実 TU の対応差 | compile | 後段で止める層 |
|---|---|---|---|---|---|
| **M3b** `#undef SLEEP_READ_PHASE` + `#define SLEEP_READ_PHASE 1` を `include/backoff.hh` の include 直後 (top-level) に置く | backoff.hh の digest は指令を消費して stock と一致。transaction.cc の digest は include を剥がすので漏れを見ない | stock genome で `src_token = "stock"`、receipt の `verification_variant = 19d4249ef295` (pure stock と同じ ID) | `transaction.cc:278` の `#if SLEEP_READ_PHASE` が真になり `sleepTics(1);` が入る。object も `rdtscp` ループ込みで差 | 成功 (無警告) | identity 層には無い。admission は `tracked_diff_sha256` で区別できる (§6) |
| **M3a** 同じ 2 行を EVOLVE-BLOCK の synthetic 枝 (`#if BACKOFF_FIXED >= 0` の内側) に置く | 同上。stock genome では枝が dead で無影響 | variant genome で token `d8a4a10d…` = 未変異 template の variant と同一、`verification_variant = 02138ae2bdd3` も同一 | 同上 (`sleepTics(1);`) | 成功 | 同上。**coder の hole 編集としては `diff_quarantine` の `HOLE_ESCAPE` が拒否する** (§6)。到達は template 経由に限る |
| **M6** `#undef TRACE` + `#define TRACE 1` を backoff.hh の top-level に置く | 同上。加えて `assert_trace_diff_matches_head` (規律 1 の diff-of-diffs) も file 単独なので通過 (実関数で確認) | stock と同一 (`19d4249ef295`) | TU に trace 実装が展開 (差分 2,441 行)。object に `izanagi_trace` symbol が **8 個** (基準は 0) | 成功 | **`buildcache._assert_no_trace_symbols` (nm) が binary で捕まえる対象** (今回は object の nm で symbol の存在まで確認。buildcache 経路の実走はしていない) |
| **M4b** `cc/silo/transaction.cc` で `#define __atomic_compare_exchange_n(...)` → `#include "include/atomic_tool.hh"` → `#undef` の挟み込み (memory order を relaxed 化) | include 行は不変なので `assert_includes_match_head` を通過。指令は消費される | stock と同一 (`19d4249ef295`) | TU では libstdc++ `<atomic>` と `atomic_tool.hh` の CAS の memory order が `0, 0` に変わる | 成功 (無警告) | **x86-64 では生成コードが変わらない** — object の差は `__LINE__` 由来の定数 1 箇所のみ。source 水準の意味差であり、この機体での実行差ではない |
| **M4** 同じ挟み込みで `#define desired expected` | 同上 | 同上 | masstree `compiler.hh` の `val_cmpxchg(…, type expected, type desired)` が `expected, expected` になる | **失敗** (`redefinition of … expected`) | build が fails-closed。実行可能な到達例ではない |

**この表から言ってよいこと**: 走査境界の外 (include 先の header、別 file の本体) を書き換える variant を、identity 層は
stock または兄弟 variant と区別できない。**言ってはいけないこと**: 「製品経路が許可した coder variant である」
「stock の certified 結果・cache binary・receipt を継承した」「実 workload の結果が変化した」「非再帰境界に穴は
これだけである」(§6・§8)。

---

## 2. 機構 — なぜ digest に映らないか

`orchestrator/campaign/source_digest.py` (基準 commit の現物) の identity は次の形である。

1. `EVOLVE_BLOCK_SOURCES` の 3 file (`include/backoff.hh`、`cc/silo/transaction.cc`、`cc/mocc/transaction.cc`) を
   **1 file ずつ独立に**、`#include` 行を正規表現で除去してから `g++ -E -P -nostdinc -Werror=undef -std=c++20 -O3 -DNDEBUG -D…`
   で前処理し、その出力を連結して sha256 する (`_cpp_normalize` / `canonical_source_preimage_bytes`)。
2. gate は 3 つ: tracked 改変が `ALLOWLIST` 内か、`#include` 行の列が HEAD と一致するか (`assert_includes_match_head`)、
   条件指令が参照するマクロが既知集合に閉じ `__has_include` を使わないか (`_assert_conditional_macros_covered`)。

`#define` と `#undef` は前処理器が**消費する**指令であり、`-E -P` の出力には現れない (`-P` は空行も畳む)。
親の前提実測 (login `pegasus02`、g++ 11.4.0、checker と同じ argv): `#define desired expected` / `#undef desired` を
先頭に持つ断片も、`#undef Linux` を持つ断片も、素の断片と**同じ sha256** `dd769427…` になった。
したがって、file 自身の本文がそのマクロを使わない限り、

- 別 file の header に漏れる `#define` (M3a / M3b / M6)、
- `#include` の前後を `#define` / `#undef` で挟んで include 先だけを書き換える形 (M4 / M4b)

は、どの file の digest にも映らない。gate 3 種はいずれも拒否しない: allowlist 内、include 行は不変、
`_assert_conditional_macros_covered` は `#define` 本体の `##` と `__has_include` しか見ない (`#undef` は `_dump_macros` に
反映されるが、条件指令の未知名検査にしか使われない)。

---

## 3. 測り方

すべて既存の部品で、新しい機構は無い。

| 部品 | 現物 |
|---|---|
| 変異 harness | `tools/mutation_harness.py` (`--runner-mode dispatch`、ログインノードに居て変異ごとに計算ノードへ投げる)。台帳 `verbatim/mutation-out-2.json` (schema `izanagi-dev-wave-mutation/v4`、`repo_head = e35fb7c4e`)、事前登録 `verbatim/mutation-spec.json` (sha256 `3766d53ef981bd9020f0169eeac75b6cc49e14ac7982ee0ba0c248216777d41f`) |
| 変異の carrier | `patches/silo-backoff-fixed.patch` (製品の template patch、pin `paper_story_a1_source.v1.json`)。harness は submodule 内 file を直接変異できない (`git show HEAD:external/ccbench/…` は gitlink で `fatal`) ので、superproject tracked の template を変異し、probe が製品の `patchharness.applied()` で pin の木へ当てる |
| runner (probe test) | `orchestrator/tests/test_t2630_scan_boundary_reach.py` (410 行、sha256 `55504495456d808e54ee9845e688c753948032827830ad4a653a7ae27af5c771`、Codex `role=author`)。**probe branch `worktree-dev-wave-t2630-scan-boundary-reach-probe` (tip `e35fb7c4e`、base `a5f953a66`) にだけ commit し、wave branch と main へは入れない** (harness が runner の test を固定 HEAD で tracked に要求するため)。逐語は `verbatim/probe-test.md` |
| 4 node | `test_stock_identity` (stock genome の `resolve()` が両側で `"stock"`)、`test_variant_identity` (variant genome の token が基準と同一)、`test_stock_owner_tu` / `test_variant_owner_tu` (実 TU 前処理 bytes が基準と一致)。**基準 = superproject 固定 HEAD の template bytes を当てた木**、**現在 = harness が変異した template を当てた木**。同じ使い捨て worktree で基準→観測→復元、現在→観測→復元 |
| 木 | `external/ccbench` の `git clone --no-hardlinks --no-checkout` を計算ノードの `/tmp` に作り、`patchharness.checkout(PIN, base_dir=clone)` で pin の detached worktree を取る。実共有 submodule には書かない。conftest の real-repo guard は common-dir の path/inode 同一性で発火するので独立 clone は対象外 (現物で確認) |
| genome | `Genome("silo", {"BACKOFF_FIXED": -1})` (stock) / `{"BACKOFF_FIXED": 1}` (variant、synthetic 枝が live) |
| identity | 実 `source_digest.resolve` / `canonical_source_preimage_bytes` / `resolve_evidence` / `assert_trace_diff_matches_head` (stub なし) |
| 実 TU 前処理 | `condition_meaning_gate._configure_compile_commands` → `_select_owner_entry` (`cc/silo/transaction.cc`、target `ycsb_silo.exe`) → `_entry_argv` → `_preprocess_argv` (`-c` を外し `-E -P -MD -MF` を足す。include path・-D・`-O3 -Wall -Wextra -Werror` は実 compile command のまま)。configure 引数は `p3_s4_loop._condition_gate_offline_configure_args` 由来 + `CMAKE_PREFIX_PATH` (gflags/glog) + `CMAKE_BUILD_TYPE=Release` + `ENABLE_SANITIZER=OFF` + 実 C compiler + `CCBENCH_TRACE=0` + genome の `cmake_defines()` |
| 依存 | masstree / mimalloc / googletest = 永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache/<name>` を `FETCHCONTENT_SOURCE_DIR_*` で直指し (configure と前処理・compile だけ、build しない)。3 dir の前後 inventory (相対 path + sha256) は全 run で差分ゼロ |
| compiler | `compilers_for_current_site()` → `g++` → `/usr/bin/x86_64-linux-gnu-g++-11` 11.4.0 (sha256 先頭 `2360901d864c`、login と同一実体)。cmake `/usr/bin/cmake` |
| 追加観測 (node の合否に入れない) | 同じ compile command で `-c` した object の生成可否と `objdump -drC` の差、`assert_trace_diff_matches_head` の成否、cache inventory の前後差 |

所要: collection 22 秒、baseline 53 秒、各変異 42〜53 秒、10 request 合計 8 分 34 秒 (queue 待ちはいずれも数秒)。

---

## 4. 結果表

台帳の status は「runner test の失敗 node 集合が事前登録と一致したか」だけを言う。**KILLED = 到達ではない。**
失敗 node の署名と、各 run の `observations.json` に残る赤理由を突き合わせて読む (段 6 レビュー A6-1)。

| 変異 | 登録 | 台帳 | 失敗 node | token (stock / variant) | pre-image | TU bytes | object | compile | TRACE gate | 赤理由 (現物) |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline (未変異 template) | PASSED | PASSED | — | `stock` / `d8a4a10d…` | 一致 | 一致 (4,949,328 / 4,950,039 bytes) | 一致 | 成功 | 通過 | — |
| M0 cmake comment 1 行 | SURVIVED [] | SURVIVED | — | 一致 | 一致 | 一致 | 一致 | 成功 | 通過 | (対照: 何も変わらない) |
| M1 synthetic 枝に `now_backoff += 1.0;` | KILLED [N1b, N2b] | KILLED | variant identity, variant TU | `stock` / **`efadd99f…`** | variant 差 | variant 差 | variant 差 | 成功 | 通過 | digest 差 (正例: identity が動く) |
| M2 backoff.hh に `#include <cstdint>` | KILLED [4 node] | KILLED | 4 node | **resolve が RuntimeError** | — | 一致 | 一致 | 成功 | 通過 | `assert_includes_match_head` 拒否 (正例: include-match gate)。TU は `<cstdint>` が既 include のため不変 |
| **M3a** hole 内 `SLEEP_READ_PHASE=1` | KILLED [N2b] | KILLED | variant TU | 一致 / 一致 | 一致 | variant 差 (`+ sleepTics(1);`) | variant 差 (`rdtscp` 込み) | 成功 | 通過 | **到達 (兄弟 variant と衝突)** |
| **M3b** top-level `SLEEP_READ_PHASE=1` | KILLED [N2a, N2b] | KILLED | stock TU, variant TU | 一致 / 一致 | 一致 | 両 genome 差 (`+ sleepTics(1);`) | 両 genome 差 | 成功 | 通過 | **到達 (stock 継承)** |
| **M4** `desired`/`expected` 挟み込み | KILLED [N2a, N2b] | KILLED | stock TU, variant TU | 一致 / 一致 | 一致 | 両 genome 差 | **生成不能** | **失敗** (再定義) | 通過 | 到達だが compile 不能 |
| **M4b** CAS relaxed 挟み込み | KILLED [N2a, N2b] | KILLED | stock TU, variant TU | 一致 / 一致 | 一致 | 両 genome 差 (`<atomic>` 内 `int(__m1), int(__m2)` → `0, 0`) | `__LINE__` 定数 1 箇所のみ | 成功 (無警告) | 通過 | 到達 (source 水準)。x86-64 の生成コードは同じ |
| **M6** top-level `TRACE=1` | KILLED [N2a, N2b] | KILLED | stock TU, variant TU | 一致 / 一致 | 一致 | 両 genome 差 (2,441 行、trace 展開) | 差 (`izanagi_trace` symbol 8 個) | 成功 | **通過** | **到達 (stock 継承 + 規律 1 の一次防壁通過)** |

pre-image の列は `canonical_source_preimage_bytes` の bytes 比較 (identity が「何を見て同一と言ったか」)。
receipt の `verification_variant` も到達 5 変異で基準と一致した (stock genome `19d4249ef295`、variant genome `02138ae2bdd3`)。
一方 `resolve_evidence` の `tracked_diff_sha256` は基準 `29aef2bc…` に対し各変異で別の値、`tracked_clean = False` である (§6)。

---

## 5. 到達例の構造 (欠陥の記述)

**欠陥**: `source_digest` の identity は「3 file を include 除去のうえ単独で前処理した出力」しか見ないので、
(a) file 内の `#define` / `#undef` が同じ TU の後続 header・別 file の本体へ漏れる効果、(b) `#include` の前後で
マクロを定義・解除して include 先の展開だけを変える効果、が identity に乗らない。include 行の一致検査は (b) を
止めない (include 行そのものは不変)。条件指令の既知集合検査は `#define` の本体しか見ない。
実 TU は 3 file と header を 1 つの翻訳単位として組み立てるので、両者は食い違う。

**到達の条件**: マクロ名が、その file 自身の本文 (指令の後) に現れないこと。現れれば digest が動いて別 identity になる
(M1 と同じ向き)。今回の 5 例はいずれもこの条件を満たす。

**継承の実体** (段 3 レンズ A の A-5、親が現物で確認):

| 継承候補 | 現物 | 今回の実測 |
|---|---|---|
| loop の skip key | `pipeline.py:137-143` `variant_id(genome, src_token)` は stock token のとき src を省く。`loop.py:695-706` は `variant_id` が `done` にあれば評価を skip する | token と `verification_variant` が同一 = **同じ key になる**ことを実測。実 loop で skip されたことは未実測 |
| build cache の binary | `build_admission.py:674-676` は STOCK_BASELINE に `src_token == stock ∧ tracked_clean ∧ pin 一致` を要求し、admission hash が cache key に入る (段 3 A-1) | `tracked_clean = False`、`tracked_diff_sha256` が変異ごとに別 → **admission は区別できる**。cache hit の実測はしていない |
| verification receipt | `verifier/core.py:226-234` は source・admission・variant・snapshot を束縛する | receipt 発行は未実測 |

つまり今回示したのは「**identity 層 (src_token / pre-image / variant ID) が別のプログラムを同一視する**」ことであり、
その下流で何が実際に継承されるかは、skip key の一致までである。

**規律 1 側 (M6)**: `assert_trace_diff_matches_head` も file 単独なので、backoff.hh からの `TRACE` 漏れを transaction.cc 側で
見ない (実関数で「通過」を記録)。ただし object には `izanagi_trace` symbol が 8 個入るので、`buildcache` の nm 検査
(`_assert_no_trace_symbols`) が binary で捕まえる対象になる。一次防壁は抜け、最終層は残る。

**coder 面との関係 (M3a、段 3 A-2)**: hole 内の生指令は `diff_quarantine.py:492-497` の `HOLE_ESCAPE` が拒否し、
template patch の編集契約 (`:62-67`) も禁止する。**今回の到達は「変異した template を信頼して当てた後、identity 層が
受理した」ものであり、coder 由来の variant が製品経路を通ったことの実測ではない。**

---

## 6. 限界 (書けないこと)

1. **製品経路の全層は通していない。** probe は `resolve` / `resolve_evidence` / `assert_trace_diff_matches_head` と実 configure・
   前処理・単一 TU の compile を呼ぶ。`loop` の skip、`pipeline.evaluate`、`build_admission`、`buildcache` の cache key・nm 検査、
   verifier の receipt 発行は呼んでいない (段 3 A-4 の表)。
2. **木は local clone の pin worktree** であり、実共有 submodule ではない。同じ commit の同じ bytes だが、共有 checkout の
   dirty 状態や repository 固有設定は再現していない。
3. **依存は永続 cache の既存 `config.h`** を読む (masstree の生成は build 時 custom command で、今回は走らせていない)。
   fresh な dependency build との同等性は主張しない。cache の前後 inventory は全 run で差分ゼロだが、途中の変更・復元まで
   排除する検査ではない。
4. **object の差は単一 TU の `-c` と objdump** であり、link・最終 binary・workload 実行は見ていない。M4b の「source 水準の
   意味差」は x86-64 の生成コードには現れなかった。
5. **同一 build dir を再 configure** して基準/現在を測った (CMakeCache を消していない)。compile command は両側で一致した。
6. **有限 matrix である。** 8 変異・1 compiler・1 依存構成・silo の 1 TU での観測であり、走査境界の他の形
   (mocc、`#pragma`、`__has_include` 以外の computed 系など) の不存在は言えない。

---

## 7. 既存記録との差分 (純増)

- D34 の「残る穴」は computed include (`#if __has_include`) のみで、T-148 (2026-07-28) がそれを fails-closed 化した。
- T-148 レビューの A-n2「`#undef` 未モデル」は「記録のみ (alias 源にならない)」と裁定されている
  (`output/insights/2026-07-28/t148-review-verbatim/findings-and-rulings.md:33`)。当時の論点は file 内の条件枝で、
  **include 先 header・別 file への漏れ**は扱っていない。
- D1490 は `condition_meaning_gate` (別機構) で「断片の単体前処理は手前の `#undef` で偽る」を認め、所有 TU 全体の前処理へ
  移した。source_digest には同じ形の判断が無い。
- 初出は T-1643 wave の裁定候補 R-2 (`output/insights/2026-09-14/t1643-has-include-real-pair/README.md` §9) で、
  「未証明」とされていた。**本 wave の純増は、実 `resolve` の受理・identity の byte 一致・実 TU の対応差・compile 可否・
  後段の層を、変異 harness の台帳付きで確定したこと**である。

---

## 8. 裁定パッケージ (修正は本 wave では実装しない)

到達は実測で確認された正しさ欠陥 (規律 2 の一次防壁の穴、M6 は規律 1 も) なので、修正を起票して返す。
選択肢 (親の推奨は (a)):

- **(a) 指令を pre-image に乗せる。** `_cpp_normalize` に `-dD` を足す (`-dD` は前処理結果に加えて `#define` / `#undef` を
  出力し、predefined は含まない)。`#define` / `#undef` が 1 行でも増減すれば digest が動き、別 identity として自分の
  build・verify を受ける。変更は 1 箇所。**代償**: 既存の golden digest (`test_source_digest_preimage_join_has_pre_refactor_golden_digests`
  等の silo 8 golden id) が動く = identity 版の変更であり、規律 7 の「再検証の発火条件」を結果を見る前に決める必要がある。
  本 wave の M3b / M6 が正例、M0 が負例になる。
- **(b) 指令行の一致検査を足す。** `assert_includes_match_head` と同型で `#define` / `#undef` 行の列を HEAD と比較する。
  template patch 自体が `#define` を足していない (skeleton は `#if/#else/#endif`) ので template は通る。**代償**: 将来の
  template や coder 面が正当に `#define` を使えなくなる (現行の hole 契約は既に禁止しているので実害は小さい)。
- **(c) TU 単位の digest。** 実 include path で TU 全体を前処理して digest する。**代償**: 依存供給と configure が identity の
  前提になり、環境依存が強くなる。D34 が「skeleton 抽出が要る」と却下した方向に近い。
- **(d) 限界として明記し、template の信頼境界に委ねる。** coder 面は `HOLE_ESCAPE` が塞ぎ、template は人間が書く。
  **代償**: 規律 2 の一次防壁が「template を信頼する」前提を持つことを認める。

**還元判断: ユーザー確認待ち** (CCBench 本体のバグ報告ではない。izanagi の identity 層の欠陥)。

---

## 9. 一次資料の所在

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2630-scan-boundary-reach/` に全量を保全した (repo には要点だけ)。

| 場所 | 中身 |
|---|---|
| `evidence/bnode001-20260916T14HHMM-<pid>/` (10 dir) | run ごとの証拠。`observations.json` (段階別の ok/例外)、`{reference,current}/{stock,variant}/` に `token.txt`・`preimage.bin`・`source-evidence.json`・`owner.ii` (前処理 bytes、4.9 MB)・`owner.o`・`objdump.stdout`・`compile.stderr`・`configure-input.json`・`owner-command.json`、`*-tu.diff.txt` / `*-object.diff.txt`、`cache-{before,after}.json`、`environment.json`、`compiler-*.json` |
| `mutation-out-2.json` / `mutation-attempt-2.json` | harness の台帳と attempt 記録 (試行 2 = 本走)。試行 1 (`mutation-out-1.json`) は baseline が F6-1 で赤になり中止 |
| `harness-2.log`、`output/pegasus-dispatch/<hash>/izdw-*.o2246`〜`o2255` (probe worktree 側) | harness 本体の log と計算ノードの job stdout |
| `s1-brief.md` / `verbatim-rulings.md` / `s2-plan-out.md` / `s3-a-out.md` / `s3-b-out.md` / `s4-ruling.md` / `s5-author-out.md` / `s6-fix1-out.md` / `s6-a-out.md` / `s6-b-out.md` | 段 1〜6 の逐語 |

run と変異の対応 (UTC 時刻が dir 名): `143830` baseline、`143925` M0、`144015` M1、`144111` M2、`144158` M3a、
`144256` M3b、`144352` M4、`144444` M4b、`144540` M6 (`143141` は試行 1 の失敗 baseline)。

本 dir の `verbatim/` に複製したもの: 段 1〜6 の逐語 (`s1-brief.md` … `s6-b.md`)、`probe-test.md` (probe 本文の逐語、
`.py` は repo に残さない)、`mutation-spec.json`、`mutation-out-2.json`、`mutation-attempt-2.json`、
差分 `m1-variant-tu.diff.txt` / `m3b-stock-tu.diff.txt` / `m3a-variant-tu.diff.txt` / `m4-stock-tu.diff.txt` (先頭 60 行) / `m4-compile.stderr.txt` /
`m4b-stock-tu.diff.txt` (先頭 60 行) / `m4b-stock-object.diff.txt` / `m6-nm-izanagi-trace.txt`、
各 run の `observations.json` (`obs-<変異>.json`)、`environment-m3b.json`、`compiler-cxx.json`。
`.diff` / `.patch` 拡張子は provenance checker が実装面と分類するため `.diff.txt` にしてある。

**`verbatim/` の段 1〜6 逐語は可逆最小正規化を施していない** (原文と byte 一致)。原文の sha256 は `verbatim/SHA256SUMS.txt`。

計算ノード実走の再現 (probe branch の clean な worktree から):

```
env IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600 IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600 \
    IZANAGI_DISPATCH_WALLTIME_OVERRIDE=01:00:00 \
python3 tools/mutation_harness.py --repo <probe worktree> --spec <job dir>/mutation-spec.json \
  --expected-spec-sha256 3766d53ef981bd9020f0169eeac75b6cc49e14ac7982ee0ba0c248216777d41f \
  --out <job dir>/mutation-out-N.json --attempt-out <job dir>/mutation-attempt-N.json --wrapper-attempt N \
  --runner-mode dispatch --detached \
  -- python3 tools/run_tests.py -rf orchestrator/tests/test_t2630_scan_boundary_reach.py -n 0 --force-dispatch
```

---

## 10. 親が踏んだこと

- **F6-1: conftest の autouse fixture が site 判定を中和する。** `orchestrator/tests/conftest.py:239-254`
  `_declare_default_test_site` は全 test で hostname を `test-host`、NQSV 無しにするため、計算ノード上でも
  `compilers_for_current_site()` が既定 `gcc-13/g++-13` を返し、試行 1 の baseline (2243.nqsv) は 4 node が同因で赤になった
  (dispatch 1 本を空費)。test が fixture `_detect_site_under_test` (`:149`) を要求すれば実 detector が動く。fix commit
  `e35fb7c4e`。
- 隔離 session の guard は `git -C <別 worktree>` を拒否するので、probe worktree への commit は `EnterWorktree(path)` で
  切り替えて行った。
