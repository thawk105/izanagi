# 段 6 レビュー裁定 / fix 契約 (第 1 巡) — [T-1128]

親裁定。2026-08-16 00:20 JST。段 4 裁定 (`s4-ruling.md`) の追補であり、上書きではない。

## 0. 実測 (子の主張ではなく親が測った値)

計算ノードでの焦点走はすべて緑。**ただし受入全走ではない。**

| 走行 | 結果 |
|---|---|
| 4 file 合同 (request 912295.nqsv、00:09 JST 終了) | 504 passed, 2 skipped, 33.97s, rc=0 |
| `test_buildcache_v2.py` 単独 | 117 passed, rc=0 |
| `test_build_site_gate.py` 単独 | 23 passed, rc=0 |
| `test_pegasus_floor_tools.py` 単独 | 71 passed, rc=0 |
| `test_s8b_floor_campaign.py` 単独 | 293 passed, 2 skipped, rc=0 |

login node の bounded local は 2 回とも rc=16
(`bounded scope の memory.max / memory.oom.group を走行中に attest できない`)。
**これはテスト結果ではなく実行基盤の失敗**であり、赤にも緑にも数えない。

## 1. 所見の裁定

| # | 所見 | 判定 | 採否 | severity |
|---|---|---|---|---|
| A-1 | job-local base が変わるだけで正当な cache hit が postflight 拒否される (受理集合の過剰縮小) | **real** | 採用 | must-fix |
| A-2 | postflight 拒否より前に未検証 binary を完成 cache へ publish している | **real** | 採用 | must-fix |
| A-3 | `_fetchcontent_base_dir` の store / projection gate が非 sort cell にも開いている | **real** | 採用 | must-fix |
| B-1 | build 中に archive を差し替えて復元する ABA を前後 snapshot では検出できない | **real** | 一部採用 | should → 予防は scope 外 |
| B-2 | base / source の消失競合で、閉じた detail code と永続化を通らず素の例外が抜ける | **real** | 採用 | must-fix |
| B-3 | M4 を落とすテストが無い (helper 全体を fake へ置換しており実効 gate を通らない) | **real** | 採用 | must-fix |
| B-4 | cache hit 経路と archive receipt の検出力が固定されていない (期待値が production から自己導出、fake は `cached=False` 固定) | **real** | 採用 | must-fix |

親が独立に検算した 2 件: B-3 (`test_s8b_floor_campaign.py:2247` が
`_prepare_floor_oracle_dependency` を丸ごと差し替えている)、
B-4 (`test_s8b_floor_campaign.py:338` が `cached=False` を固定している)。どちらも指摘のとおり。

### B-1 の裁定理由

前後 snapshot の同値検査は、**build 中の差し替え + 復元**を検出できない。これは real である。
しかし予防 (依存 tree を書換不能にする、link 入力の identity を binary へ束縛する) は
download / 書込み権威の変更を伴い、段 4 で scope 外とした
`FETCHCONTENT_FULLY_DISCONNECTED` と同じ審査が要る。よって:

- **採用する**: A-2 の fix (build 直後・publish 前の内容再照合) により観測窓を
  「build 完了から publish までの間」から「build 中のみ」へ狭める。
- **採用しない**: 依存 tree の書込み禁止と link 入力 identity の束縛。**裁定パッケージへ返す。**
- **記録の義務**: 本 wave の記録は「build 中の差し替え + 復元に対する保護」を主張しない。
  主張するのは「oracle が検証した内容と、build 前後で観測した内容が一致した」ことだけである。

## 2. fix 契約 (F1〜F6)

- **F1 (A-1)。** cache hit 経路で **absolute root path の再一致を要求しない**。
  権威は completion に束縛された**内容 receipt** (masstree HEAD + `config.h` sha256 +
  archive sha256) とする。absolute root hash は診断として記録してよい。
  fresh build 経路では従来どおり実効 root == 現在の base を要求する。
  **正例**: base A で fresh build → 内容が同一の base B で hit → 通る。
- **F2 (A-2)。** `build_v2` が completion を publish する**前**に、
  masstree の HEAD・`config.h` sha256・archive sha256 を再取得して入力 receipt と比較する。
  不一致なら publish せずに失敗する。campaign 側の postflight は残す (二重防壁)。
  **負例**: build 中に内容が変わったら完成 entry が publish されず、
  内容を戻しても拒否済み binary が hit されない。
- **F3 (A-3)。** `_fetchcontent_base_dir` の存在を `configuration_id == "sort_best"` と
  **同値**にし、store gate と portable projection の**双方**で強制する。
  **負例**: stock / 非 sort record に同 field を付けたら拒否される。
  **正例**: sort record は通る。
- **F4 (B-2)。** base / source に対する filesystem probe (`resolve()` 後の `stat()`、
  hash 後の `stat()` を含む) をすべて段階別の `_FloorOraclePreflightError` へ変換する。
  prebuild helper の `except Exception` を checkout / configure / target / base で分離し、
  `BuildCacheError` を checkout failure へ誤分類しない。
  **負例**: 消失競合を注入し、private failure JSON の exact detail code と、
  oracle 呼出し 0 回・`build_fn` 呼出し 0 回を検査する。
- **F5 (B-3)。** prebuild 失敗の負例を**実効 gate へ再照準**する。
  `_prepare_floor_oracle_dependency` 全体を fake へ置換せず、checkout は成功させたまま
  本物の helper を通し、`buildcache.prepare_masstree_fetchcontent` だけを
  configure 失敗 / target 失敗の 2 通りで失敗させる。
  握り潰す変異 (M4) が単一理由で赤になること。
- **F6 (B-4)。** 検出力を固定する。
  - archive receipt の期待値を **production の `cache_receipt()` から導出せず**、
    独立 literal の 3-key dict とする。fake も exact key / hash を検証する。
  - fake builder が `cached=True` も返せるようにし、
    **postflight → 永続化 → admission 未実行**の通しを `cached=False` と `cached=True` の
    両方で検査する。
  - M8 (archive sha256 を receipt から外す) が単一理由で赤になること。

## 3. 変更しない事項

- 段 4 裁定 §2.1 の編集面 7 ファイルを増やさない。
- 段 4 裁定 §2.4 の「主張してはならないこと」は不変。B-1 の限定を追加する。
- `FETCHCONTENT_FULLY_DISCONNECTED`、T-1129、SWO PASS receipt の durable 束縛は
  引き続き scope 外。

## 4. 裁定パッケージへの追加

段 4 裁定 §4 に次を足す。

5. **build 中の依存差し替え (ABA) に対する予防。** 前後 snapshot では検出できない。
   予防には依存 tree の書込み禁止か、linker が実際に読んだ archive の identity を
   binary completion receipt へ束縛することが要る。どちらも書込み / download 権威の変更。
   **推奨: 新規起票 (P2)。**
