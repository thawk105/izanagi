---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1999-define-gate-family
seq: 1
title: [T-1999] 測定条件の関門を族として設計し driver 全体へ義務化した (コード + docs、branch worktree-dev-wave-t1999-define-gate-family、変異 matrix = baseline PASSED・KILLED 5・SURVIVED 0・MISMATCH 0・期待 node 完全一致 5/5)
---

## 本文

- D1198 の未実装部分。T-2018 が call-scoped の 2 節と負例を land 済みで、残っていたのは
  patch 供給の define を build へ渡す driver 全体への義務化だった。
- **逐語の読み方が本 wave の分岐点だった。** D1198 が driver 全体へ義務づけているのは
  **効いたことの正例検査**であり、macro ごとの意味 witness を全部実装することではない。
  この読み分けで scope が確定した。段 3 のレンズ B が独立に同じ判断へ達している。
- **正例の形を binary hash 相異から前処理後 bytes の差へ変えた。** hash 案は `BACKOFF_FIXED`
  でしか成立しないと plan 自身が認めていた。前処理差なら未供給・綴り違い・写像欠落・
  条件指令へ未到達のすべてで bytes が同一になり、cache option 経由と compiler flag 経由の
  両方で成立する。無効値 (`-1` や `requested == default`) は向きを反転し、TU 到達を確かめた
  うえで stock との一致を要求する。
- **経路 2 (`-DCMAKE_CXX_FLAGS=-D<NAME>=1`) には fails-closed の保護が 1 つも無いことを実測した。**
  経路 1 の `patches/silo-backoff-fixed.patch:42` は `#error` を持つが、
  `patches/broken-*.patch` は `error` を 0 件しか持たず `#if IZANAGI_BREAK_*` を使う。
  未定義 macro は 0 と評価されるので、綴り違い・未供給・patch 未適用のいずれでも
  壊れているはずの枝が黙って選ばれない。正しさの対照を作る driver 群には
  条件が効いたことを確かめる層が現状ひとつも無かった。
- **段 6 の敵対レビュー 2 本がどちらも NO-GO を出した** (レンズ A = blocker 9、レンズ B = blocker 6)。
  core API (2 節の型・record ID・digest・status・reason の分離) は両者が健全と認め、
  欠陥は配線・昇格境界・閉包検査・record の発行束縛に集中していた。重複を除く 10 件を修正した。
  詳細は {{F:gate-implemented-but-not-firing}}。
- **強化した閉包検査が、誰も閉包に入れていなかった build sink を 3 つ掘り当てた。**
  `screening_driver.py`、`silo_ladder_rung1._build_variant`、`s8b_floor_campaign` の campaign sink。
  plan v2 の 51 sink 独立検出でも、レビュー 2 本でも、親の手検索でも出なかった。
  独立列挙 × 直積という設計の効果である。前 2 者は配線し、3 者目は t2027 所有のため繰延べた。
- **親の裁定を 2 度撤回した。** 1 度目は「単一の絞り口で fail-closed に拒否する」で、
  全閉包が必ず通る絞り口は不在と plan が反証した。2 度目は P-strict ({{D:promotion-requires-effectuation-not-meaning}})。
- **段 5・6 の fix は計 14 巡。** 空転の原因は技術的難易度ではなく、子が毎回「実装済み・未実走」で
  報告し一度も自分の修正を確かめていなかったこと。子は計算ノードへ pytest を投げられないが
  素の python は実行できるので、repo 外の診断スクリプトで直接呼ばせる形に変えたところ
  1 巡で真因に到達した。詳細は {{F:child-reports-unverified-fix}}。
- **親が自分の測定を 3 度訂正した。** patch 供給 define を 11 個と数えた件 (正しくは経路 1 が 9、
  経路 2 が 13)、`CMAKE_CXX_FLAGS` が最適化 flag を壊すという推測 (ccbench 本体は base へ代入せず
  反証)、S1 の赤を選択依存と結論した件 (バッチでも赤で、真因は裁定の反映漏れ)。
- 段 6 レビュー B が親の記述を 2 点訂正した。凍結編集は 7 file 中 5 file でなく **4 file**
  (`axis_trigger_gating.py` は本 wave 非編集で既にずれている)。hold 対象 test は保存済み artifact
  でなく live `build_document()` と人工 tamper を検査するため、hold 解放時の全走の緑は静的には未確認。
- `output/` 配下の pin は多数あるが**いずれも過去の測定に対する historical binding** であり、
  live approval pin ではない。未更新のままが正しい。repin すれば過去測定の実行体参照を改変する。
- 変異は 5 件登録し全件 KILLED、期待 node 完全一致。5 件目は初版が検査関数の改名という誤った
  設計だったため、`_PythonGateFlow.coverage_for_sink` の sink 単位支配計算を file 単位の流用へ
  弱める形へ再照準した (DW-M01/M02 の実効 gate 再照準)。
- 実装 commit `0218acc61` / `ee635c953`、main 取り込み merge `649290c06`。
  main は 130 commit 前進していたが**編集面の重なりはゼロ**で自動 merge が通った。push はしていない。

## 次の一手差分

### 完了

- [T-1999] patch 供給の define を build へ渡す driver 全体へ、効いたことの正例検査を義務化した。
  供給・実効化の節と実行側の意味の節を、独立した必須節と負例として持たせた。
  remaining: none
  base: f2e462befffdee1e09d84ae2abda5648512bdb00980f7883d3a0b127a1a162c6

### 新規

- {{T:meaning-witness-backlog}} **P2・新規**: 意味 witness を持つ macro は `BACKOFF_FIXED` の 1 件だけで、
  残り 21 macro は昇格時に `unestablished` として成果物へ持ち越される。この一覧が縮むことが後続の仕事。
  macro ごとに実行側の意味を観測する witness を実装する。
- {{T:deferred-gate-members}} **P2・新規**: 稼働 wave 所有と事前登録束縛のため本 wave で配線しなかった
  4 member を配線する。`b10_backoff_shape_sweep.py` (t1905)、`paper_story_a1_paired.py` (t1819)、
  `s8b_floor_campaign.py` の `build_fn` seam と campaign sink (t2027)、
  `s8b_oracle_n_pilot.py` (事前登録 `protocol-r33.json` の `driver_sha256` 束縛)。
  最後の 1 件は事前登録の後継発行か凍結解除のユーザー裁定が要る。
