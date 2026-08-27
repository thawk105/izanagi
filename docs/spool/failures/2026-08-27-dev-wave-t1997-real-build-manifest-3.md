---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1997-real-build-manifest
seq: 3
---

## 再発

### F542

- **再発: 2026-08-27** — 同じ述語が 2 度目も実物と食い違った。F542 の恒久対応で張り替えた
  `FETCHCONTENT_SOURCE_DIR_MASSTREE` / `FETCHCONTENT_BASE_DIR` 経路のうち、
  **BASE_DIR 分岐が実物では構造的に到達不能**だった。CMake は `FetchContent_Declare` の時点で
  当該 key を**空値の cache entry として必ず作る**ため、「行が無い」ことを BASE_DIR 分岐の
  条件にしていた実装は、実 `CMakeCache.txt` で必ず SOURCE_DIR 分岐へ入り絶対 path 検査で落ちた。
  F542 が「positive control は実環境と同じ形の CMakeCache を使う」と宣言した当の positive control
  (`test_masstree_source_root_accepts_base_only_shape`) が、実 CMake の出さない「行なし」形を
  使っていた。さらに `test_masstree_source_root_invalid_source_does_not_fallback` の `empty`
  parametrize が、実 CMake が必ず出す形を**拒否として固定**しており、fixture が実物と逆向きに
  固まっていた。計算ノード (CMake 3.25.0、job `951893.nqsv`) とログインノード (3.22.1) の
  実 build 2 例で確定した。F542 の「再発検知」は `DW-O13` の未適用を指摘していたが、
  今回は key の**存在**でなく key の**値**について同じ未適用が起きた。恒久対応は
  {{D:empty-cache-entry-is-unset}} (空値を未設定として読む) と
  {{D:mock-shape-must-come-from-the-tool}} (正例 fixture を道具の実出力から作る) の 2 件、
  および実 CMake 形を固定する正例・負例テスト群である。
