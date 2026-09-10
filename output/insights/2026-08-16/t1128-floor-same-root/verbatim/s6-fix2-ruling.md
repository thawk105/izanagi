# 段 6 fix 契約 (第 2 巡) — [T-1128]

親裁定。2026-08-16 00:50 JST。第 1 巡 (`s6-fix-ruling.md`) の訂正と残件。

## 0. 実測 (親が計算ノードで測った値。fix 第 1 巡の適用後)

| 走行 | 結果 |
|---|---|
| `test_buildcache_v2.py` 単独 | **1 failed**, 118 passed |
| `test_build_site_gate.py` 単独 | 23 passed, rc=0 |
| `test_pegasus_floor_tools.py` 単独 | 71 passed, rc=0 |
| `test_s8b_floor_campaign.py` 単独 | **75 failed** |
| meta 4 file (`test_env_contract` / `test_sort_swo_oracle` / `test_s8b_oracle_manifest` / `test_s8b_oracle_report`) | **4 failed** |

fix 第 1 巡の前は `test_s8b_floor_campaign.py` が 293 passed / 2 skipped / 0 failed だった。
**79 件の赤はすべて fix 第 1 巡が入れた回帰である。**

## 1. 原因は 1 本 — 親の裁定文の誤り

79 件の赤のうち **78 件**が同一行から出ている。

```
orchestrator.campaign.s8b_floor_campaign.FloorCampaignError:
binary store runtime record._fetchcontent_base_dir は sort_best と同値でなければならない: cell=rr20::sort_best
orchestrator/campaign/s8b_floor_campaign.py:3454
```

**第 1 巡 fix 契約 F3 の「同値」という指定が誤りである。** 実装子は書かれたとおりに実装した。

正しい契約は**片方向の含意**である。

- **正**: `_fetchcontent_base_dir` が record にあるなら、その record は `configuration_id == "sort_best"` である。
- **誤 (第 1 巡が書いてしまったもの)**: `sort_best` なら `_fetchcontent_base_dir` が必ずある。

後者が誤りである理由: base 注入は production の sort 経路が
`sort_best` cell を持つときにだけ起きる。pilot、注入 build seam、base 未使用の run では
`sort_best` record が base を持たないのが正常であり、それらを拒否すると
**受理集合が空になる** (レビュー A-1 で潰したのと同じ型の過剰縮小を、別の場所で作り直していた)。

## 2. fix 契約 (G1〜G2)

- **G1 (F3 の訂正)。** `_fetchcontent_base_dir` の gate を**片方向**にする。
  - 拒否する: 非 `sort_best` record に `_fetchcontent_base_dir` がある。
  - **拒否しない**: `sort_best` record に `_fetchcontent_base_dir` が無い。
  - store gate と portable projection の**双方**で同じ片方向規則にする。
  - **正例 1**: base を持つ `sort_best` record は通る。
  - **正例 2**: base を持たない `sort_best` record も通る (これが今回の赤の正体)。
  - **負例**: `stock_common` 等の非 sort record に base を付けたら拒否される。
  - 第 1 巡で追加した負例テスト
    `test_fetchcontent_runtime_field_is_rejected_for_non_sort_record[store]` / `[project]` は
    片方向規則でも成立するはずである。成立しない形になっていたら直せ。
- **G2 (`test_buildcache_v2.py` の 1 件)。**
  `test_v2_dependency_drift_before_publish_leaves_no_completed_cache_entry` が
  `claims[0].unlink()` で落ちている。**v2 build claim は directory である**
  (`buildcache.py:1452` の `_mkdir_open_at`)。テストの後始末が entry 種別と合っていない。
  併せて次を判定し、報告で明示せよ。
  - drift 検出で失敗したとき claim を残す挙動は意図的か。
    同じ `build_v2` の他の失敗経路が claim を解放しているなら、**drift 経路も同じにせよ**
    (fail-closed のまま、手動回収を不要にする)。他経路も残すなら現状維持とし、
    テストの後始末だけを entry 種別に合わせよ。
  - **drift 検査そのものを緩めてはならない。** `completion` を publish しないこと、
    内容不一致で必ず失敗することは維持する。

## 3. 変更しない事項

- 第 1 巡 fix 契約の F1・F2・F4・F5・F6 は**そのまま維持**する。触るな。
- 段 4 裁定 §2.1 の編集面 7 ファイルを増やさない。
- 段 4 裁定 §2.4 と第 1 巡 §1 の B-1 限定は不変。
