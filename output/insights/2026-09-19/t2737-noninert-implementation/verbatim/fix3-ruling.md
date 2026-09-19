# fix3 裁定 (受入 attempt 1 の赤 3 件、2026-09-19 21:39 JST)

## 事実
- 受入全走 (tested main 2ba400087、tip 4c9d9ecc2、3 shard) は 3 failed / 25276 passed / 69 skipped。F945 型なし。
- 赤 3 件はすべて `orchestrator/tests/test_ccbench_spawn_sites.py`:
  1. `test_patch_define_inventory_matches_condition_gate_registry` —
     `frozenset(patch_sources) == frozenset(condition_meaning_gate.DEFINE_SPECS)` の左側に
     `SS2PL_WFG_HH`, `SS2PL_LOCK_HH`, `SS2PL_STUDY_LOCK_HH` が余分。
  2. `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` —
     `proven-unreachable` 38 != 35 (+3)。
  3. `test_define_sink_cross_product_t2520_certify_entry_removal` — `proven-unreachable` 28 != 25 (+3)。
- 3 test とも `_patch_added_define_interfaces()` の候補集合から数える。+3 は同じ 3 macro。
- 3 macro は本 wave が `patches/ss2pl-lock-protocol-study.patch` に足した新規 header 3 本
  (`cc/ss2pl/include/ss2pl_lock.hh`, `ss2pl_study_lock.hh`, `ss2pl_wfg.hh`) の include guard
  (`#ifndef X` / `#define X` / 末尾 `#endif  // X`)。base 7975385b5 と main 2ba400087 の patch には無い
  (どちらも `#pragma once`)。→ 本 wave 起因の赤 (DW-O18「自分起因は直す」)。
- include guard 化は一次資料 §1.1 の patch **c** で、D2148 項4 が採用済み。理由: `#pragma once` は
  `-E -P` 前処理に 7 空白 + 改行の残渣を残し dependency-closure 比較を壊す (login 実測)。
- 目録関数の docstring は「patch 内部の target 定義と CMake marker 値は構造的に除く」と言う。
  include guard の macro は patch 内で `#define` される patch 内部定義であり、外部供給 TU define ではない。
  現行の除外規則 (`target_compile_definitions` の内部 define、`set()` の literal 値、既存 token) は
  include guard 慣用句を扱っていない — 他の patch は新規 header を足していないため前例が無かった。

## 採らない選択肢
- `#pragma once` へ戻す: 裁定 (patch c) を覆し WFG の dependency-closure-drift を再発させる。不可。
- `DEFINE_SPECS` に 3 macro を登録: `SUPPLY_DOMAIN_MACROS` に入り condition gate の供給 macro になる。意味が違う。不可。
- 期待値 25/35 (および 14/39) の更新、xfail、skip、deselect、`--ignore`: テスト弱体化。不可 (規律 2、DW-S06-B)。

## 採る修正 (fix3、Codex author 1 単位)
- 所有: `orchestrator/tests/test_ccbench_spawn_sites.py` だけ。production・patch・`condition_meaning_gate.py` は触らない。
- `_patch_added_define_interfaces()` に include guard 慣用句の構造的除外を足す。慣用句の定義 (この 3 条件を全部満たす場合だけ):
  (a) patch 内で `new file mode` を持つ file の追加行のうち、最初の前処理 directive 行が `#ifndef X`;
  (b) その直後の追加行が値なしの `#define X` (macro 名の後に token が無い);
  (c) その file の最後の非空追加行が `#endif` (行末 comment は許す)。
  満たす X は候補 (`sources`) から除く。変更 file (new file でない) の hunk に足された guard、値付きの
  `#define X 0` (既定値慣用句)、`#endif` で閉じない file は従来どおり候補に残す。
- 受理の含意: 新規 file の include guard は外部供給 interface として数えない。
- 拒否の含意: 既定値慣用句 `#ifndef X` / `#define X 0` / `#endif` と、変更 file 内の bare guard は従来どおり
  外部供給候補として発見され、`DEFINE_SPECS` に無ければ赤のまま。
- 正例・負例: 同 file に unit test を 1 本足し、`tmp_path` に最小 patch file を書いて `patch_dir=` 引数で呼ぶ。
  正例 = 新規 file の guard が `patch_sources` に現れない。負例 2 つ = 既定値慣用句、変更 file 内 bare guard は現れる。
  fixture に現行 hash・揮発値を焼き込まない。既存 test の期待値 (25/35/14/39 等) は変更しない。
- 規模: 変更 80 行以内 (unit test 込み)。新しい仕組み・helper module・gate は足さない。

## 期待される結果
- 修正後、上記 3 test は既存期待値のまま緑に戻る (候補集合が base と同じ 25/35 に戻るため)。
- 親が焦点走 (`test_ccbench_spawn_sites.py` 全体 + `test_ss2pl_lock_study.py`)、変異 2 本
  (除外を「bare `#define X` 全部」へ広げる / 値付き define も除外する) で負例 test が赤になることを裏取りし、受入を再走する。
