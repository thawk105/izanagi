---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1156-post-oracle-refetch-ban
seq: 1
title: [T-1156] oracle 判定後の材料再取得を禁止し、判定と同一規則で build 前に検査した (コード + テスト、branch worktree-dev-wave-t1156-post-oracle-refetch-ban、変異 matrix = baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー依頼は `/dev-wave [T-1156] oracle 実行後の材料の再取得を禁止する` (背景 job)。
  裁定は 2026-08-25 の /rulings 全件で確定 (暫定)、正本は archive worklog 956 の本文。
  起票は entry 569 で、D425 が「依存 tree を書込み不能にして再 fetch を禁止する案は
  download / 書込み権威の変更であり別審査」として送った、その別審査が本 wave である。
  base main は `53c61414`。
- **禁止手段の生死を段 1 の前に実測し、そこで設計が決まった。** repo 外の使い捨て driver で
  測ったところ、`FETCHCONTENT_FULLY_DISCONNECTED=ON` は再取得を確かに止めるが、
  **source が不在でも configure は rc=0 で成功し source を再作成しない**。すなわち
  flag 単独では「材料が無いこと」を咎めず、恒真な保証になる。禁止は izanagi 側の材料検査と
  対にして初めて fail-closed になる。
- **段 6 の敵対レビューが第 2 の恒真経路を出し、親が再現した。** argv に flag を置いても
  ambient な `CMAKE_TOOLCHAIN_FILE` が同じ変数を FORCE で `OFF` へ倒すと、実効値は `OFF` になり
  **再 populate が実際に起きた**。`CMakeCache.txt` は実効値を正直に記録するため照合で検出できる。
  {{F:argv-token-is-not-effective-value}}、{{D:disconnected-effective-value}}。
- **初版実装は、gate はあるが成功経路が空という形になっていた。** build 側に独自の inventory
  規則を書き `.git` を除外したため、`.git` を含む oracle 側の exact 一致と交わりが空になった。
  build 側を oracle 自身の検証関数へ寄せて解消した。{{F:dual-rule-empty-intersection}}、
  {{D:post-oracle-refetch-ban}}。
- **親の provisional 裁定を 3 点撤回した。** (a) cache identity を変えないという判断は誤り —
  cache hit は保存済み argv を読まず現在の生成器から再構成するため、禁止前の binary に
  禁止付きの configure 記録が付く。(b) prebuild の oracle 後再入 gate は現行 call graph に
  late edge が無く恒真になるため実装しない。(c) 再生成経路を scope 外とする結論は維持するが、
  理由を「別型だから」から「D425 が別審査とした書込み権威の変更だから」へ訂正した。
- **発火条件を builder の同一性で条件付ける初版は fail-open だった。** 条件が偽になると拒否では
  なく禁止が黙って消える。段 6 レビューが capability の落ちる経路を 13 通りに分類し、5 通りで
  禁止が消えると判定した。fix で「dependency binding を持つ sort_best は capability を伴うか、
  さもなくば build を 1 度も呼ばずに拒否する」へ変えた。
- **実装は本 wave では dormant である (閉じていない残件)。** production に `SHA256SUMS` を
  配置・生成する経路が存在せず、oracle の依存検証は現状 PASS しない。**これは本 wave が
  作った欠陥ではなく変更前から存在する**。fail-closed 化により、この状態では build が
  安全側に止まる (誤った数値が通るのではない)。{{T:floor-oracle-manifest-generator}} で返す。
- **本 wave の主張は「再取得の禁止」までであり「材料変更の全面禁止」ではない。**
  `masstree_build` の custom command が source tree 内で `config.h` と archive を再生成する
  経路は残る。{{T:post-oracle-regen-ban}}。
- 段 3 敵対 2 レンズで所見 17 件、段 6 敵対 2 レンズで所見 13 件。fix は 1 巡。
  焦点走は fix 後に `test_buildcache_v2.py` 172 passed、`test_s8b_floor_campaign.py`
  457 passed / 2 skipped、consumer 7 file で 872 passed / 9 skipped。
- **変異は probe 巡で観測 node を集めてから本走した。** baseline PASSED (629 passed / 2 skipped)、
  6/6 KILLED、SURVIVED 0、MISMATCH 0。M05 (flag を無条件付与) は 55 node を赤にする過剰決定で
  あり、原因を 1 つに絞れない証拠として扱う。逐語と変異台帳は
  `output/insights/2026-08-26_t1156-post-oracle-refetch-ban/`。
- 子の工数は plan 1・consult 2・author 1・review 2・fix 1 の計 7 本。全 codex 子は
  sandbox の構造的制約で pytest を実走できず、テストはすべて親が計算ノードで走らせた。
- **背景コマンドの偽完了を 3 回踏んだ。** 待ち手ツールに固有ではなく自前ループでも起きた。
  3 点照合で 3 回とも検出し実害ゼロ。F24 へ再発として追記した。

## 次の一手差分

### 完了

- [T-1156] oracle 判定後の依存材料の再取得を禁止し、照合を oracle 自身の検証器へ統一した。
  実効値は `CMakeCache.txt` から読み、発火条件は fail-closed にした。
  remaining: none
  base: 5a337136c6a6b43311968fdab0becb7800993b6001504c9f7243310a45716ce3

### 新規

- {{T:floor-oracle-manifest-generator}} **P1・新規**: 床値の SWO oracle が production で
  PASS できない状態を解く。oracle は依存 root に `SHA256SUMS` を要求し、宣言集合と実在集合の
  exact 一致と manifest 本体 hash の pin 一致を求めるが、production 側でこの manifest を
  生成・配置する経路が存在しない (`git grep SHA256SUMS -- tools docs` が 0 件、実在するのは
  test fixture のみ)。**本 wave の変更前から存在する欠陥であり、`sort_best` cell は
  build へ到達しない。** 本 wave の fail-closed 化により安全側に停止するが、床値の
  certified 経路は開かない。oracle と build が同じ検証器を使う形は本 wave で揃えたので、
  残るのは manifest の生成と配置の設計である。
- {{T:post-oracle-regen-ban}} **P2・新規・ユーザー裁定待ち**: oracle 判定後の材料**再生成**を
  禁止する。`ThirdParty.cmake` の `add_custom_command` が `masstree_build` から起動され、
  source tree 内で `bootstrap.sh` / `configure` / `make` / `ar` を再実行して、oracle が判定した
  `config.h` と archive を作り直しうる。本 wave の禁止は fetch 経路だけを閉じた。
  閉じるには依存 tree の書込み禁止か private snapshot build が要り、D425 が別審査とした
  書込み権威の変更に当たる。
- {{T:floor-thirdparty-content-binding}} **P2・新規**: mimalloc と googletest の内容を build
  境界へ束縛する。staged mode は oracle 前に 3 依存を clean 検査するが、build 前後に再観測
  するのは masstree だけである。ycsb target は mimalloc へ直接 link するため、oracle 後に
  mimalloc を書き換えても masstree 側の検査は通る。本 wave が作った穴ではない。
- {{T:cache-hit-historical-configure-argv}} **P3・新規**: cache hit が返す `configure_argv` を
  historical execution の記録にするか、recipe であると明示するかを決める。現状は保存済み argv を
  読まず現在の生成器から再構成するため、cross-base hit では記録された base と binary を実際に
  作った base が食い違う。既存テストが cross-base hit を明示的に許しているため、変更は既存
  受理集合を狭める。
- {{T:floor-shared-base-process-exclusion}} **P3・新規**: 明示共有 base を使う複数 job の間で、
  oracle 判定後に別 process が prebuild を再入する経路を塞ぐ。D424 は job 一意 `mkdtemp` base で
  排他が構造的に成立する設計を採っており、明示共有 base は別モードである。process 間 lock は
  書込み権威の変更を伴う。
- {{T:floor-resume-preban-manifest-policy}} **P3・新規・ユーザー裁定待ち**: resume 経路が
  禁止前の durable manifest を受理し続けてよいかを決める。resume は `build_v2` を呼ばず
  binary/store hash の照合だけで既存 binary を使う。閉じると既存 floor manifest が一括で
  失効する migration になるため、受理集合を大きく縮める判断はユーザーに属する。
  現状 resume は `eligible_for_refreeze: false` であり certified 選択集合は直接広がらない。
