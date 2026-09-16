---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2731-cpp-normalize-dd
seq: 2
---

## 新規

### {{F:dd-predefined-assumption}}. 裁定文が GCC 文書の古い記述 (`-dD` は predefined を含まない) を前提にし、素の実装なら inert template ≠ stock を受入 suite が検出できなかった [テスト代表性] [手順漏れ]

- 事象: 2026-09-17 [T-2731] の段 1。D2104 項 2 と T-2630 insight §8 は「`-dD` は前処理結果に加えて `#define` / `#undef` を出力し、
  predefined は含まない」を前提に「`_cpp_normalize` に `-dD` を足す (1 箇所)」と裁定していた。親の前提実測 (login pegasus02、
  g++ 11.4.0 と g++-12 12.3.0、checker と同じ argv) で **predefined 419〜437 行と command-line `-D` も出力される**ことが分かった。
  template patch は CMake 供給に `BACKOFF_FIXED` / `BACKOFF_NOINLINE` を足すため、素の `-dD` では `compute()` の出力にだけ
  `#define BACKOFF_FIXED -1` 等が現れ `baseline()` (HEAD 供給) には現れず、未変異の template を当てた木が非 stock になる
  (完了条件 1 「inert = stock」の破壊)。
- 根本原因: (1) 裁定の技術前提を文書の記述から取り、対象 compiler で実測していなかった。(2) 受入 suite は共有 submodule に
  template patch を当てないため (`test_source_digest_stock_roundtrip` は stock checkout、template 依存 node は
  `skip_conditional_unrun`)、この破壊は受入では緑のまま通り、T-2630 §9 の recipe 再走の baseline 赤で初めて見える構造だった。
- 恒久対応: 実装は空入力の環境 prefix を剥がす形にした ({{D:cpp-normalize-dd-env-prefix}})。受入で検出できる回帰 test として
  `orchestrator/tests/test_campaign.py::test_source_digest_unused_universal_supply_preserves_stock` と
  `::test_source_digest_unused_protocol_supply_preserves_digest` (fake repo で template と同型の「working-tree だけの追加供給」を
  作り `"stock"` / `compute == baseline` を要求する fails-closed の負例) を追加した。変異 S2 (prefix 剥がしを外す) がこの 2 node を
  赤にすることを台帳で確認した。発見した防壁は DW-S01 の「brief 前に前提を実測する」規律 (docs/dev-wave/core.md)。
- 再発検知: 上記 2 node の赤。裁定文が compiler / tool の挙動を前提にするときは、段 1 で対象実体の実測を brief に書く。

## supersede 追記

- F1016 **supersede: 2026-09-17** — 恒久対応の「[T-2731] として起票 (裁定待ち)」は D2104 項 2 で (a) と裁定され、[T-2731] が `_cpp_normalize` に `-dD` + 環境 prefix 剥がし ({{D:cpp-normalize-dd-env-prefix}}) を実装した (commit bd21bc501 / 2cc661235)。再発検知の recipe 再走で M3b / M6 の identity node が赤 (別 identity) になり、M0 は同 identity のまま (`output/insights/2026-09-17/t2731-cpp-normalize-dd/README.md` §6)。残る限界 (指令と include の相対位置、push_macro / pop_macro) は同 D の裁定パッケージ。
