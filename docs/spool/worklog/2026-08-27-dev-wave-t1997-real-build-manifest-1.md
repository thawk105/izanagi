---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1997-real-build-manifest
seq: 1
title: [T-1997] 計算ノードで実 build 正例を 1 回取り、模擬 fixture が実物と逆向きに固まっていたことを確定した — 依存受け渡しの既定 regime が build 段で全件拒否されていた (コード + docs、branch worktree-dev-wave-t1997-real-build-manifest、変異 matrix = baseline PASSED・KILLED 6/6・SURVIVED 0・MISMATCH 0)
---

## 本文

- **実 build 正例を 1 回取り、2 経路のうち 1 つが実物で通らないことを確定した。** 計算ノード
  `bnode009` (queue `gen_S`、job `951893.nqsv`、CMake **3.25.0**、g++ 11.4.0) で pin 済み CCBench
  `511c9538e4e8efa54b45cda62e72389ed3b706ec` を base-only regime で configure / build し、
  `ycsb_silo.exe` を得た (両 rc=0)。compiler input manifest の採取は**通った**
  (`depfile_count=3`、入力 588 = 絶対 549 / snapshot 相対 39、
  `manifest_sha256=990abdffb2212d60f70acac19bcc79d5a6695de4d3a48ea44ba9ea5b68cac281`)。
  一方 masstree source root の解決は**通らなかった**。逐語と数値は
  `output/insights/2026-08-27_t1997-real-build-manifest-shapes.md`。
- **原因は「模擬が実物と逆向きに固まっていた」ことである。** CMake は `FetchContent_Declare` の
  時点で `FETCHCONTENT_SOURCE_DIR_MASSTREE` を**空値の cache entry として必ず作る**。
  実装は当該行の**存在**だけを「指定あり」の条件にしていたため、`<FETCHCONTENT_BASE_DIR>/masstree-src`
  を使う分岐は実物では構造的に到達不能だった。既存の正例は実 CMake が作らない「行なし」形を使い、
  既存の負例は実 CMake が必ず作る「空値行」形を**拒否として固定**していた。
  依存受け渡しの既定 `transport_mode` は `base-only` なので、その regime の全 cell が
  build 段で `BuildCacheError` になっていた。F542 の再発として台帳へ記録した。
- **是正が実物で効くことを親が実測した。** 修正後の
  `_masstree_source_root_from_cmake_cache` を実 build tree へ直接走らせ、計算ノードの
  CMake 3.25.0 build とログインノードの CMake 3.22.1 configure の**両方**で
  `<base>/masstree-src` を返すことを確認した。裁定は {{D:empty-cache-entry-is-unset}}。
  正例 fixture を道具の実出力から作る規律は {{D:mock-shape-must-come-from-the-tool}}。
- **敵対レビューの最重要所見を実測で反証した。** 段 3 レンズ A は「空値の受理を無条件にすると
  宣言記述子なしの呼び手にも届き D1134 の同一挙動境界を破る」として条件付き opt-in を推した。
  親が全件検索したところ、`fetchcontent_dependency_receipt` を渡す production 呼び手は
  floor campaign の 1 箇所だけで、その同じ呼び出しが記述子を全 cell へ無条件に渡している。
  「記述子なし + receipt」の呼び手 class は production に存在せず、opt-in の否定側の枝は
  一度も通らない。装飾の機構を足さず無条件修正を採った。
- **既存テストの期待値変更を 1 件だけ親裁定で許可した。** 実 CMake が必ず出す形を拒否として
  固定していた parametrize 1 件を外し、テスト名を非空かつ不正な SOURCE 限定へ改めた。
  `relative` と `nul` の期待は 1 文字も変えていない。`DW-S06-B` が禁じるのは
  「実装が誤りなのにテストを緩めること」であり、ここでは実測により**テストの期待が誤り**と
  判明した型である。段 2 の子は実際にそう報告して止めた。
- **段 3 レンズ B の最重要所見は real だが scope 外と裁定した。** manifest は job-local な
  FetchContent base (`tempfile.mkdtemp`) 配下の絶対 path を 31 件含み、base が消えた後の
  cache hit は `external compiler input is unavailable` で落ちる。ただし
  `-I<base>/masstree-src` は両 transport mode で等しく include path に載るため、
  この性質は本 wave と独立に**今日すでに成立している**。是正は manifest schema と
  cache hit 契約の同時変更になり D1136 の境界に触れるため、裁定パッケージとして起票した。
- **レビュー B の指摘で親自身の資料の不備も判明した。** 子へ渡した実測逐語で `.o.d` の中身を
  `...` で省略していたため、実物に在る `../` を含む非正規化 path が射程から落ちていた。
  実 build tree から取り直して fix 子へ渡し、fixture へ固定した。
- **変異走行は共有木の観測で 1 度止まった (rc=125)。** 観測 root に並行セッションが稼働する
  main checkout が入っていたためである。独立 clone を `--source-repo` に渡して観測 root を
  移し、構造的に断った。段 8 でこれを改善候補に挙げたが、F300 の系列が同じ原因・同じ手段・
  同じ予算上の障害まで既に記録しており、5 件目の同型 `再発` 行は情報を足さないため追記しない
  と裁定した。
- **段 8 は改善候補 2 件を裁定した。** 上の rc=125 は既存正本で被覆済みとして追記なし。
  もう 1 件 (親が「逐語」と称した射影資料を省略記号で切ったこと) は新しい型なので
  {{F:verbatim-projection-elided}} を起票した。`DW-O02` への 1 文追記を試みたが、
  L1.5 層の unique footprint が 9716 bytes となり予算 9566 bytes を 150 bytes 超えたため、
  安全義務を削らず reference への追記を見送り、台帳を正本にした。
  同じ理由で `DW-M05` への rc=125 の 1 文追記も 9737 bytes で入らなかった。
  **予算の上限引き上げには至っていないが、L1.5 が 2 件連続で満杯だったことは報告事項である。**
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、fix 1)。全数 `gpt-5.6-sol` /
  `xhigh` / accepted。実装子と fix 子はいずれも dispatch 基盤の rc=16 で pytest を実走できず、
  緑の一次資料はすべて親の実走である。

## 次の一手差分

### 完了

- [T-1997] 計算ノードで実 build 正例を 1 回取り、`DependInfo.cmake` と `.o.d` の実形で
  採取が通るかを実測した。compiler input manifest の採取は通り、masstree source root の
  解決は通らないことを確定して是正した。通らなかった形状は insight へ構造化済み。
  remaining: none
  base: a3ad865246505c49502f8e79d840a87a9ca90e2c251a9a3cc8b28fc1697e68dd

### 新規

- {{T:manifest-external-input-rebinding}} **P1・ユーザー裁定待ち**: compiler input manifest が
  job-local な FetchContent base 配下の絶対 path を保存するため、base が消えた後の cache hit が
  `external compiler input is unavailable` で落ちる。本 wave の実測で 31 件を確認した。
  両 transport mode で等しく起きる既存の性質であり、是正は manifest schema・completion・
  cache hit 検証・receipt 発行の同時変更になる。設計択一は (1) manifest に FetchContent root の
  分類と root 相対 path を持たせ、cache hit と receipt 発行時に現在の canonical base へ束縛して
  hash を再検証する (親の推奨)、(2) base の絶対 path を descriptor-bound cache identity へ入れて
  base が違えば必ず fresh build にする (run 間 cache reuse を失う)、(3) 旧 external path が
  消えた entry を cache miss へ降格する (競合・隔離・回収規則の新設が要る)。D1136 の
  「snapshot 内外で扱いを分ける」境界に触れるため裁定が要る。
