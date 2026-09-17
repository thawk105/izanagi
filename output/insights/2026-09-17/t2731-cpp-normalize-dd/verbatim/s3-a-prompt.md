単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s1-brief.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s1-brief.md`
  — 親 brief (scope、不変条件、前提実測 F-1〜F-4、(P1)(P2))。**brief 自身も検査対象**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s2-plan-prompt.md`
  — 段 2 の依頼 (親が plan 子に何を要求したか)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s2-plan-out.md`
  — 段 2 plan 子の起草 (検査対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/verbatim-rulings.md`
  — 既裁定 (第 20 回 rulings 項 2)、F1016、D34、insight §8、親の前提実測 script と出力の逐語
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/campaign/source_digest.py`
  — 変更対象 (`_cpp_normalize` :1646-1676、`_normalize_contexts` :1686、`_dump_macros` / `_environment_macros` :1702-1745、`_merge_defines` :902、`_worktree_defines` / `_head_defines` :2071-2097、`compute` / `baseline` :2116 / :2212、`_trace_pair_diff` / `assert_trace_diff_matches_head` :2150-2210)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_campaign.py`
  — source_digest 系 test (:11040-11335、:11470 `_FAKE_BACKOFF_HH`、:11541 `_fake_ccbench_repo`、:11790-11910、:12561-12600)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/output/insights/2026-09-16/t2630-scan-boundary-reach/README.md`
  — F1016 の実測記録
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2630-scan-boundary-reach/mutation-spec.json`
  — T-2630 の 8 変異 spec (修正前の期待署名)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/patches/silo-backoff-fixed.patch`
  — template patch

上記以外に repo 内を読んでよい。`external/ccbench/` 配下 (pin 511c953 の `include/backoff.hh`、`cc/silo/transaction.cc`、
`cc/mocc/transaction.cc`、`cmake/Options.cmake`、`cc/silo/CMakeLists.txt`)、`tools/check_trace0_preprocess_identity.py`、
`orchestrator/campaign/buildcache.py`、`orchestrator/campaign/diff_quarantine.py`、`docs/decisions.md` (D23 / D34 / D1490)、
`docs/failures.md` (F1016) は一次資料である。

## レンズ A — 正しさ境界

plan を守らず検査する。**親 brief 自身も検査対象**である。正しさ境界 (規律 2 の一次防壁である identity が、修正後に
「別のプログラムを同一視する」経路を残していないか、逆に「同じプログラムを別視する」過剰拒否を新たに作っていないか) を攻める。

1. **prefix 剥がしの健全性。** 親案 (同 argv の空入力出力を prefix として `removeprefix`) が偽陰性 (剥がしすぎ) / 偽陽性
   (剥がし残し) になる入力を探す。例: source 先頭が prefix の末尾と同文の `#define` (command-line と同名同値の再定義)、
   `#undef` した builtin を再 `#define` する source、`-Werror=undef` との相互作用、`__COUNTER__` 等の非決定 builtin、
   `#pragma push_macro` / `pop_macro`、`#pragma GCC system_header`、`-imacros` 相当の経路。壊れる経路が本当にあるかを
   現物 (g++ の挙動、`_INCLUDE_RE` の除去、`BUILD_FLAGS`) で確かめ、無いなら「無し」と書く。
2. **親の実測値の一般化。** 親は stdin 断片 7 形で「prefix から始まる・決定的」を測った (verbatim の probe script)。
   これを EVOLVE_BLOCK_SOURCES 全文 + template + 2 文脈 (`_context_overlays`) + `_worktree_defines` の実 defines に
   一般化してよいか。login の g++ 11.4 / 12 と計算ノードの compiler (`compilers_for_current_site`) で `-dD` の出力形
   (順序・空白正規化) が食い違うと何が起きるか (compute と baseline は同 cxx なので stock 判定は保たれるか)。
3. **不変条件。** (i) inert template = stock、(ii) `compute == baseline ⇔ 同一 pre-image`、(iii) `assert_trace_diff_matches_head`
   の述語不変 (M6 形で D_variant == D_stock のまま通過し、最終層 `buildcache._assert_no_trace_symbols` が残る)、
   (iv) `HOLE_ESCAPE` 不変。plan と brief がこれらを本当に保つか、`_trace_pair_diff` の `TRACE=1/0` の command-line 行、
   `_head_defines` と `_worktree_defines` の供給差、CONTEXT_MACROS の overlay 行 (`#define GLOBAL_VALUE_DEFINE 1`) で
   検査する。
4. **規律 7 の再検証発火条件。** 「M3b / M6 が別 identity・M0 は同 identity」を結果を見る前に登録する形が、plan の test /
   spec v2 で恒真化していないか (例: 期待 node が修正前 HEAD でも同じ集合になる = 検出力ゼロ)。「golden は動かない」(親 F-4)
   が正しいなら、規律 7 の「identity 版の変更」は何を意味するか — 記録済み測定 (stock / template variant の token) は
   同一値のまま有効で、無効化も再認証も要らないという親の読みに反例があるか。
5. **過剰拒否。** 受理集合を狭める向きの変更なので、承認外の過剰拒否 (正当な template / coder 面の編集が別 identity に
   なって cache miss を増やすだけでなく、`resolve` が RuntimeError で止まる) の正例を探す。`startswith` 不成立の
   RuntimeError が実 file で起きる条件を挙げる。
6. **主張の限定。** 修正後の insight に書いてよい文と書いてはいけない文を対で列挙する (「F1016 は塞がった」と言える範囲、
   有限 matrix の限界、mocc / `#pragma` / computed 系の不存在は言えない等)。

## 禁止

- gate・検査・台帳・一般化の新設を提案しない。裁定 (a) を (b)(c)(d) に差し替える提案をしない。規律 2 を緩める方向を書かない。
- commit・push・file の書き込みをしない。テストの実走を成功条件にしない — **pytest 緑を要求しない。静的検査でよい。**
  親が実走する。実走していないものを緑と書かない。

## 出力形式

Markdown。次の H2 節をこの順で必ず置く。所見は 1 件ずつ `A-1`, `A-2`, … と番号を付け、各件に
**根拠 (file:line)**・**real と主張する理由**・**是正案 (scope 内 / scope 外)** を書く。

## 所見 (real 候補)
## 親の実測値の一般化
## 不変条件と規律 7
## 主張の限定 (書いてよい / 書いてはいけない)
## 親 brief への反論
## 総括

予算が尽きそうなら、途中までの結論をこの出力形式どおりに書いて終える。**無出力が最悪である。**
