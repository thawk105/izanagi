# [T-2731] 段 1 brief — `_cpp_normalize` に `-dD` を足し `#define` / `#undef` を identity の pre-image に乗せる

- 研究前進: 規律 2 の一次防壁 (source_digest の identity) が実測到達済みの穴 (F1016: file 間へ漏れる指令が digest に映らず、別プログラムが stock の identity・skip key を継承) を塞ぐ。完了判定 = M3b / M6 形の variant が別 identity になり (正例)、M0 (comment-only) と inert template が stock のまま (負例)、既存 tests 緑。論文主張の土台 (variant の identity が正直であること) の修復であり、新しい図表は無い。
- 起点: 第 20 回 rulings 項 2 (fragment `docs/spool/decisions/2026-09-17-rulings-all-20260917-1.md`、main ad12ba35b、D 番号は fold で採番、`{{D:rulings-full20-verdicts}}`)。決定 = (a) `-dD`。規律 7 の再検証発火条件を結果を見る前に段 4 で登録。他案 (b)(c)(d) は却下済み。
- scope: `orchestrator/campaign/source_digest.py::_cpp_normalize` の 1 箇所 + 新規回帰 test (fake repo 形、既存 `_fake_ccbench_repo` 流用) + consumer の整合 (docstring / `tools/check_trace0_preprocess_identity.py` は呼ぶだけで変更不要の見込み)。gate・台帳・一般化の追加は scope 外。規律 2 を緩めない。
- 確定済みユーザー裁定: (a) 採用。golden 更新だけで済ませない。記録済み測定は無効化しない (規律 7)。Codex author (D95) + 変異事前登録。
- 前提実測 (login pegasus02、g++ 11.4.0 / g++-12、`-E -P -dD -nostdinc -Werror=undef -std=c++20 -O3 -DNDEBUG -D…`):
  - (F-1) `-dD` は predefined 419〜437 行と command-line `-D` (`#define FOO 0`) も出力する。insight §8 と裁定文の「predefined は含まない」は反証 (GCC 文書の古い記述)。
  - (F-2) 空入力の出力 = 環境 prefix。実入力の出力は 7 形 (先頭 `#undef linux`、command-line と同文の `#define`、comment 先頭、空行先頭、M3b 形、comment-only) すべてで prefix から始まり、3 走で決定的。skipped 枝の `#define` は出ない。
  - (F-3) template patch は CMake 供給に `BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}` を足す。`compute()` は working-tree 供給、`baseline()` は HEAD 供給で defines を絞るので、素の `-dD` では compute だけに `#define BACKOFF_FIXED -1` が出て inert template ≠ stock (完了条件 1 の破壊、`test_source_digest_stock_roundtrip` も赤)。
  - (F-4) pin 511c953 の EVOLVE_BLOCK_SOURCES 3 file と template patch に `#define` / `#undef` 行は 0。prefix を剥がせば既存の stock・template variant の pre-image は byte 一致 = **golden は動かない**。動くのは指令を持つ variant だけ。
- (P1) 剥がし方 = 同じ argv で空入力を 1 回走らせた出力を prefix として `removeprefix` する (per (cxx, defines) cache、`startswith` 不成立は RuntimeError で fails-closed)。spawn site は `_cpp_normalize` の 1 箇所に保つ (`test_ccbench_spawn_sites` の登録簿 `_cpp_normalize: 1`)。代案 = `-P` を外して linemarker で切る (正規化の意味が変わる) / 環境マクロ名で行 filter (source の `#undef linux` 等を落とす) — 親は不採用。攻撃対象。
- (P2) 再検証の vehicle = (i) fake repo の unit test (login): M3b 形・M6 形 → `resolve != STOCK` かつ `compute != baseline`、M0 → STOCK、供給だけ増える inert 形 → STOCK; (ii) T-2630 §9 recipe を probe branch (wave tip + probe test 2 commit の cherry-pick) で計算ノード再走、8 変異の期待署名を更新した spec v2 を段 4 で事前登録 (M3b / M6 / M4 / M4b: 4 node、M3a: N1b+N2b、M1 / M2 / M0 不変)。queue は現在空。
- 不変条件: `inert template = stock`、`compute == baseline ⇔ 同一 pre-image`、`_assert_no_trace_symbols` (buildcache nm) と `HOLE_ESCAPE` は不変、`assert_trace_diff_matches_head` の述語不変 (M6 形で D_variant == D_stock のまま通過し、最終層 nm が残ることを併記)。enforcement source (campaign_lock / qualification contract / T-671) の blob 束縛 file なので **段 5 後すぐ commit してから焦点走**。
- 成果物: コード 1 箇所 + test、insight README (`output/insights/2026-09-17/t2731-cpp-normalize-dd/`)、spool fragment (worklog / failures F1016 の恒久対応追記)、変異台帳。
- 変更面 (実アンカー): `orchestrator/campaign/source_digest.py:1646-1676` (`_cpp_normalize`)、`:1717-1737` (`_dump_macros` / `_BUILTIN_MACRO_CACHE` の cache 形を踏襲)、`orchestrator/tests/test_campaign.py:11790-11907` (fake repo test の形、`_fake_ccbench_repo`)。
- 並列分割: 実装子 1 (source_digest + test)。docs は親。
- 受入・実測環境: unit test = login (g++-12 / g++)、recipe 再走 = 計算ノード (runbook `docs/pegasus-runbook.md`、dispatch 形は §9 そのまま)。
