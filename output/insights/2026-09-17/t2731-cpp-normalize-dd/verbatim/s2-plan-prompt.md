単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s1-brief.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s1-brief.md`
  — 親 brief (scope、不変条件、前提実測 F-1〜F-4、(P1)(P2))
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/verbatim-rulings.md`
  — 既裁定 (第 20 回 rulings 項 2)、F1016、D34、insight §8、親の前提実測 script と出力の逐語
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/campaign/source_digest.py`
  — 変更対象。`_cpp_normalize` (:1646-1676)、`_normalize_contexts` (:1686)、`_dump_macros` / `_environment_macros` (:1702-1745、cache `_BUILTIN_MACRO_CACHE` :404)、`_merge_defines` (:902)、`_worktree_defines` / `_head_defines` (:2071-2097)、`compute` / `baseline` (:2116, :2212)、`_trace_pair_diff` / `assert_trace_diff_matches_head` (:2150-2210)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_campaign.py`
  — source_digest 系 test (:11040-11335 golden / roundtrip / semantic、:11790-11910 `_fake_ccbench_repo` を使う fake repo 形、:12169-12200、:12561-12600 trace diff-of-diffs)。`_FAKE_BACKOFF_HH` (:11470) と `_fake_ccbench_repo` (:11541) の定義も読む
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_ccbench_spawn_sites.py`
  — spawn site 登録簿 (`("campaign/source_digest.py", "<module>._cpp_normalize"): 1` :289)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/tools/check_trace0_preprocess_identity.py`
  — `_cpp_normalize` の repo 外 consumer (:583-596)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/docs/dev-wave/mutation.md`
  — 変異走行の契約 (DW-M01〜M08)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/output/insights/2026-09-16/t2630-scan-boundary-reach/README.md`
  — F1016 の実測記録 (§1 表、§2 機構、§4 結果表、§5、§8、§9 再現 recipe)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2630-scan-boundary-reach/mutation-spec.json`
  — T-2630 の 8 変異 spec (carrier = `patches/silo-backoff-fixed.patch`、期待 node は修正前の署名)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/patches/silo-backoff-fixed.patch`
  — template patch (CMake 供給 `BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}` を足す)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/tools/mutation_harness.py`
  — 変異 harness (spec 契約 `_load_spec` / `_require_exact_keys`)

上記以外に repo 内を読んでよい。特に
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/external/ccbench/` 配下
(`include/backoff.hh`、`cc/silo/transaction.cc`、`cc/mocc/transaction.cc`、`cmake/Options.cmake`、`cc/silo/CMakeLists.txt`) と
`orchestrator/tests/test_skip_classification.py`、`orchestrator/campaign/buildcache.py` (`_assert_no_trace_symbols`)、
`orchestrator/campaign/diff_quarantine.py` (`HOLE_ESCAPE`)、`docs/decisions.md` の D23 / D34 / T-148 関連は一次資料である。

## この段の仕事

**`_cpp_normalize` に `-dD` を足して `#define` / `#undef` 指令を identity の pre-image に乗せる修正 (裁定 (a)) と、
その回帰 test・変異登録を、file:line 粒度で起草する。** 実装はしない (read-only)。

起草に必ず含めること。

1. **`_cpp_normalize` の変更設計。** 親の前提実測 F-1〜F-3 (`-dD` は predefined と command-line `-D` も出力する。
   template 適用木では compute だけに `#define BACKOFF_FIXED -1` が出て inert=stock が壊れる) を、
   `_worktree_defines` / `_head_defines` / `_merge_defines` の現物で確かめたうえで、環境 prefix の剥がし方 (P1) を決める。
   親案 = 同じ argv で空入力を 1 回走らせた出力を prefix として `removeprefix` (per (cxx, defines) の module cache、
   `startswith` 不成立は RuntimeError で fails-closed)。spawn site を `_cpp_normalize` 内の 1 箇所に保つ方法
   (再帰呼出し + 内部 flag、または helper へ移して登録簿を更新) を比較し、どちらを採るか理由付きで決める。
   代案 (`-P` を外して linemarker で切る、環境マクロ名で行 filter) の欠点を現物で書く。
   docstring の更新内容 (D34 案 A の説明との整合、prefix を剥がす理由、`-dD` が predefined を含む事実) を書く。
2. **不変条件の保持の確認。** (i) pin 511c953 の EVOLVE_BLOCK_SOURCES 3 file と template patch に `#define` / `#undef` 行が
   0 であること (親 F-4) を現物で確認し、修正後も stock・inert template・既存 variant の pre-image が byte 一致 =
   `_GOLDEN_VID` / `test_source_digest_stock_roundtrip` / `test_source_digest_fixed_variant_distinct` が動かないことを
   論証する。(ii) `_trace_pair_diff` (TRACE=1 と TRACE=0 の差分) が、command-line の `#define TRACE …` 行で偽差分を
   出さないこと (prefix を剥がすので出ない、剥がさなければ両側同じ差分)。(iii) `check_trace0_preprocess_identity.py`
   の old/new 比較が同じ defines で同じ prefix を剥がすため影響がないこと、mocc trace pair (policy の base/new OID)
   の差分に指令行が無いこと (親が確認済み: `#include "../../include/trace.hh"` 1 行のみ)。
   (iv) `test_source_digest_failsclosed_on_missing_define` の経路 (prefix 取得は空入力で成功し、本体で `#error`)。
3. **回帰 test の設計 (`orchestrator/tests/test_campaign.py`、`_fake_ccbench_repo` 形)。** 各 node が何を主張するかと、
   修正前の HEAD でどの node が赤になるか (= 新 test の検出力) を書く。少なくとも:
   - M3b 形: `include/backoff.hh` の include 直後 (top-level) に `#undef X` + `#define X 1` (X はその file 本文に現れない名前) →
     `resolve != STOCK` かつ `compute != baseline`。
   - M6 形: 同じ形で `TRACE` → 別 identity。加えて `assert_trace_diff_matches_head` が通過するか (通過するなら「最終層は
     buildcache `_assert_no_trace_symbols`」と併記)。
   - M0 形: comment-only → `STOCK` のまま (負例)。
   - inert 供給形: working-tree の Options.cmake / protocol CMake にだけ供給マクロ (source が参照しない) を足す →
     `STOCK` のまま (prefix 剥がしの負例。剥がさない実装だと赤)。`resolve` の allowlist が cmake path を許すかを現物で確認し、
     許さないなら `compute` / `baseline` 直呼びの形にする。
   - 指令が skipped 枝内 (stock genome で dead) にあるとき stock identity は不変で variant identity だけ動く (M3a 形)。
   test 名・docstring・assert 文言まで書く。`test_skip_classification.py` の静的 call 数登録簿に触れるかを確認する。
4. **変異登録 (段 4 で親が確定する素材)。** (a) source-level: `-dD` を外す / prefix 剥がしを外す / `startswith` 検査を
   恒真化する / comment-only の対照 — それぞれ新 test のどの node が赤になるか (期待 node は完全集合、`DW-M08`)。
   (b) T-2630 §9 recipe の再走: 8 変異の期待署名を修正後の予測に更新した spec v2 の各 `expected_nodes` /
   `expected_status` を、carrier の変異内容から導く (M3b / M6 / M4 / M4b は 4 node、M3a は N1b+N2b、M1 / M2 / M0 不変
   という親の予測を検証し、違えば理由を書く)。probe branch の作り方 (wave tip + probe test 2 commit の cherry-pick、
   `a519a7560` と `e35fb7c4e`) と、harness の `--repo` に渡す木が clean な別木であること。
5. **親 brief への反論。** (P1)(P2)、F-1〜F-4、不変条件、scope (gate・台帳・一般化の追加は scope 外) を現物で検査し、
   食い違いを書く。無ければ「無し」。特に「golden は動かない」の主張が正しいか、`-dD` が `#pragma push_macro` /
   `-imacros` / `#define` の再定義 (同名同値) でどう振る舞うかで壊れる経路が無いか。

## 禁止

- 裁定外の gate・検査・台帳・一般化を提案しない。(b)(c)(d) 案を再提案しない。規律 2 を緩める方向 (拒否を warning に
  格下げする等) を書かない。
- commit・push・file の書き込みをしない (read-only sandbox)。テストの実走を成功条件にしない — **pytest 緑を要求しない。
  静的検査でよい。** 親が実走するので、実走していないものを緑と書かない。
- 実共有 submodule (`external/ccbench` の主 checkout) に書く設計にしない。

## 出力形式

Markdown。次の H2 節をこの順で必ず置く。

## `_cpp_normalize` の変更 (file:line と擬似 diff)
## 不変条件の保持
## 回帰 test の設計 (node 名・主張・修正前の赤)
## 変異登録の素材 (source-level と recipe v2 の期待署名)
## 親 brief への反論
## 総括

予算が尽きそうなら、途中までの結論をこの出力形式どおりに書いて終える。**無出力が最悪である。**
