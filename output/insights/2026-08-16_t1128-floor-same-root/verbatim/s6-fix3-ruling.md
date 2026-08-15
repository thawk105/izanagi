# 段 6 fix 契約 (第 3 巡・最終) — [T-1128]

親裁定。2026-08-16 01:00 JST。`DW-O16` により fix は 3 巡が上限であり、これが最終巡である。

## 0. 実測 (親が計算ノードで測った値。fix 第 2 巡の適用後)

| 走行 | 結果 |
|---|---|
| `test_buildcache_v2.py` 単独 | 119 passed, rc=0 |
| `test_build_site_gate.py` 単独 | 23 passed, rc=0 |
| `test_pegasus_floor_tools.py` 単独 | 71 passed, rc=0 |
| meta 4 file | **503 passed, rc=0** |
| `test_s8b_floor_campaign.py` 単独 | **4 failed** |
| 合同 4 file | **4 failed** (同じ 4 node) |

第 1 巡直後の 79 赤 → 4 赤。meta 群が完全に緑になったため、
第 1 巡で meta に出ていた 4 赤も自分の回帰だったと確定した。

## 1. 残る 4 赤の原因 (親が特定)

### H1. テストが `buildcache` を束縛していない (2 node)

- 赤: `test_production_floor_dependency_preflight_failure_persists_private_attempt[configure]` / `[target]`
- 症状: 期待 `floor-dependency-fetchcontent-configure-failed` /
  `...-target-failed` に対し、実際は `floor-dependency-fetchcontent-base-failed`。
- 原因: `orchestrator/tests/test_s8b_floor_campaign.py:2316` と `:2320` が
  `buildcache.MasstreeFetchContentError` / `buildcache.BuildCacheError` を参照するが、
  **この test module には `buildcache` という名前が一度も束縛されていない**
  (module 冒頭の import 群にも、当該 test 関数内にも無い。親が確認)。
  よって fixture の raise は `NameError` になり、production の総括 `except Exception`
  (`s8b_floor_campaign.py:1821-1828`) に落ちて `base-failed` へ分類されている。
- **重要**: 同じ理由で `[base]` パラメータは**偽の緑**である。`NameError` が
  たまたま期待値 `base-failed` と一致していただけで、
  `buildcache.BuildCacheError` を出す経路は一度も通っていない。
  production 側の段階分類 (`s8b_floor_campaign.py:1810-1820`) は静的には正しく見える。
- 型: `[テスト代表性]`。fixture が意図した層に届いていない。

### H2. `Path.stat` 差し替えの注入点が production の変換範囲外 (2 node)

- 赤: `test_floor_dependency_disappearance_race_persists_closed_detail_before_oracle[base-stat]` / `[source-stat]`
- 症状: 素の `FileNotFoundError("fixture disappearance race")` が
  `sort_swo_oracle.SortSwoOracleUnavailable` へ変換されずに抜ける。
- 原因候補: (a) production の閉じた変換が、fixture が実際に発火させる `Path.stat` 呼出し
  (`is_dir()` / `is_file()` / `resolve()` 経由を含む) を覆っていない。
  (b) fixture の「target への 2 回目の `stat`」が意図しない site に落ちている。
  `orchestrator/tests/test_s8b_floor_campaign.py:2445-2454` は `Path.stat` を
  **大域的に**差し替えるため、`is_dir()` など内部で `stat` を呼ぶ経路すべてに当たる。
- 型: `[テスト代表性]` または `[防壁の射程誤認]`。どちらかを実コードで判定すること。

## 2. fix 契約 (H1〜H2)

- **H1。** test module に `buildcache` を正しく束縛する
  (`s8b_floor_campaign.buildcache` を使うか、module 冒頭で
  `from orchestrator.campaign import buildcache` を足す。**同一 module object を使うこと**。
  二重 import で別 module object を作ると exact 型検査が弾かれる)。
  修正後、`[configure]` / `[target]` / `[base]` の 3 パラメータが
  **それぞれ別の detail code** を実際に通ることを固定せよ。
  `[base]` が `NameError` ではなく `buildcache.BuildCacheError` 経由で
  `base-failed` になることを確認できる形にすること。
- **H2。** 原因 (a) と (b) のどちらかを**実コードを読んで判定し、報告に明記**したうえで直す。
  - (a) なら production 側に閉じた変換を足す。**gate を緩めるな。**
  - (b) なら fixture の注入点を**意図した単一の site へ絞る**
    (大域 `Path.stat` 差し替えをやめ、production の該当呼出しだけに当たる形にする)。
    `DW-M03` の「fixture は単一理由であること」に従う。
  - どちらの場合も、**oracle 呼出し 0 回・`build_fn` 呼出し 0 回**と、
    private failure JSON の exact detail code の検査は残すこと。

## 3. 変更しない事項

- 第 1 巡 fix の F1・F2・F5・F6、第 2 巡 fix の G1・G2 には触るな。
- 段 4 裁定 §2.1 の編集面 7 ファイルを増やすな。
- **既存 (本 wave より前から tracked の) テストの期待値を変更するな。**
- production を fail-open にして辻褄を合わせるな。

## 4. 本巡で閉じなければ

`DW-O16` により fix を 4 巡目へ重ねない。親が変異で裏取りし、残る所見を
real / refuted に裁定して閉じ、根拠を worklog へ書く。
