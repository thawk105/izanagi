# 段 1 brief — [T-1799] oracle 判定後の材料再生成を禁止する (D984)

## scope

oracle が判定した後の build が、判定済み材料 (masstree の `config.h` と
`libkohler_masstree_json.a`) を source tree 内で作り直せる経路を**構造的に禁止**する。
手段は D984 が定めた 2 つ — private snapshot からの build、または判定後の source tree の
書込み不能化 — のいずれか。対象経路は
`orchestrator/campaign/s8b_floor_campaign.py` の `_post_oracle_dependency_binding()` から
`orchestrator/campaign/buildcache.py` の `build_v2(post_oracle_dependency_binding=...)` へ渡る
sort_best floor の post-oracle build と、そこで走る
`external/ccbench/cmake/ThirdParty.cmake` の `masstree_build` custom command である。
**本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外** (ユーザー指示)。

## 確定済みユーザー裁定 (親は不採用にしない)

- **D984**: oracle 判定後に build 処理が source tree 内で材料を作り直す経路を禁止する。
  手段は private snapshot からの build か、判定後の source tree の書込み不能化とする。
  却下済み: 現状維持。
- **D953**: 判定後の**再取得**禁止は明示 capability (`post_oracle_dependency_binding` 引数の存在)
  で表し、材料検査は oracle 自身の検証器を再利用する。**これは既着地であり本 wave の純増ではない。**
- **D95**: 実装面は Codex `role=author` が書く。親は実装面を直接編集しない。

## 既存機構 (純増でないもの — 再実装しない)

- `buildcache.py` の `_FETCHCONTENT_FULLY_DISCONNECTED_DEFINE` を post-oracle build の
  configure argv へ 1 個だけ付け、`_assert_fetchcontent_fully_disconnected_effective()` で
  CMakeCache の実効値が exact `ON` であることを確かめる。→ **再取得**は塞がっている。
- `_assert_post_oracle_dependency_material()` が build 前後に、`<base>/masstree-src` を
  oracle canonical root と二根照合し、`SHA256SUMS` manifest・`config.h`・archive の
  sha256 を oracle receipt と突き合わせる。→ 再生成が**別 bytes**を生めば検出される。
- D152 決定 (4) の実測: 上流 `.gitignore` が `*.a` と `config.h` を無視し、
  **CCBench の FetchContent はそれらを再生成せずリンクする** (既存なら custom command は再走しない)。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1)** 現行は「再生成の**検出**」であって「再生成の**禁止**」ではない。build 前 assert が
  archive の実在と一致を要求するため、outputs が揃った状態では CMake は custom command を
  再走させない。したがって残る再生成の窓は (a) 判定と build の間、または build 中に outputs が
  消える/古くなる場合、(b) assert が見ている根と実際に build が使う根が食い違う場合、
  (c) 同じ FETCHCONTENT_BASE_DIR を共有する **post-oracle 束縛を持たない** 別 build や
  `prepare_masstree_fetchcontent()` が同じ source tree へ書く場合、に限られる。
- **(P2)** `_assert_post_oracle_dependency_material()` は source root を
  `os.path.join(base, "masstree-src")` で**固定導出**する。一方 build 側は
  `FETCHCONTENT_SOURCE_DIR_MASSTREE` の override を受け付け、実効根は
  `_masstree_source_root_from_cmake_cache()` が CMakeCache と DependInfo から読む。
  この 2 つが食い違いうるなら、検査した木と build する木が別物になる (A-2 の教訓そのもの)。
- **(P3)** 手段の択一は「private snapshot からの build」より「判定後の source tree の
  書込み不能化」が安い。D1663 が段 4 loop で `cp -a` 複製を既に採っており、複製は
  複製の分だけ材料の同一性主張を増やす。ただし共有 base を複数 build が使う場合、
  書込み不能化は他の正当な build を巻き込みうる。
- **(P4)** `external/ccbench` は submodule (pin `511c9538e4e8efa54b45cda62e72389ed3b706ec`)。
  ThirdParty.cmake の改変は submodule pin 更新を伴い D16/D18/D20 の面に入る。
  **既定では触らず、izanagi 側 (orchestrator) で閉じる。**

## 不変条件

- 規律 2: 正しさゲートを緩める変更を採らない。既存の post-oracle 照合を弱めない・削らない。
- 規律 1: trace 有無で分岐する経路を足さない。
- 規律 7: 記録済み測定を現行コードとの差だけで無効にしない。
- `orchestrator/campaign/buildcache.py` は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` に
  **在る** = HEAD blob 束縛。未 commit のまま子にテストを走らせると `contract-loader-drift` で
  全赤になる。**編集後・段 6 前に必ず commit する。**
- 同じ理由で、**変異は buildcache.py を狙わない** (drift mask が owner ごと吸収し、
  固有 node 空になる)。狙い先は `s8b_floor_campaign.py` (束縛外) か新規 module。
- 受理集合を広げない。post-oracle 束縛が無い既存 build の挙動を変えない。

## 成果物影響 (DW-G05)

放置すると、A-2 / A-6 の certification が「oracle が判定した材料 = 実際に build へ入った材料」を
主張できない。(P1) の窓が開いたまま certified 選択が出れば、材料レポートの proof chain が
指す `dependency_manifest_sha256` / `config_sha256` / `archive_sha256` は、判定時点の値であって
build 入力の値であるとは言えなくなる。禁止を構造で表せば、この主張が成立する。

## 成果物の形

- `orchestrator/campaign/` 側の最小実装 1 箇所 + 焦点テスト。docs は段 7 の fragment のみ。
- 新しい CLI・新しい台帳・新しい成果物 schema は作らない。

## 分割方針

- 段 2: read-only codex 1 本が file:line 粒度で (P1)(P2) を実測し plan を起草。
- 段 3: 敵対 2 レンズ (sol / luna) — 片方は「窓は実在しない/既存で足りる」を立証しに行き、
  もう片方は「提案手段が他の正当な build を壊す・受理集合を変える」を突く。
- 段 5: 実装子 1 本 (単一の変更面のため分割しない)。
