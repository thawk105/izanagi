---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2443-acceptance-duration-20260908
seq: 1
title: [T-2443] 受入全走の所要を 09-08 の改修前分布と比べて記録した — 対象 5 module の W は 0.08〜0.23、対照は 0.98 / 0.99 で改修に帰属でき、wall の改善は主張しない (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t2443-acceptance-duration-20260908)
---

## 本文

- 依頼は「受入全走の所要を 09-08 の改修前分布と比べて記録する。canonical 起動 (K=3) の junit を取り、
  対象 module の W と最遅 shard wall を D1714 の読み方で記録する。1 走では wall の改善を主張しない。
  実装差分ゼロで返してよい」。**実装面の変更はゼロで、記録だけを land する。** 一次資料は
  `output/insights/2026-09-08_t2443-acceptance-duration-postfix/` (集計値は同 dir の `measurements.json`)。
- **本 wave の canonical 走 (K=3)。** 受領証は `child-green`、`tested_main` = `tested_tip` = `cc9bba523`、
  21,971 passed / 68 skipped、赤 0・flake 0。W 全体 17,522 秒、3 shard の pytest wall は
  311.38 (bnode095) / 205.90 (bnode094) / **315.40 (bnode012、最遅)** 秒。
- **D1714 の 3 点併記。** (a) 最長 node 上位 10 本はすべて `test_s8b_oracle_driver` (最長 185.86 秒)。
  (b) 対象 5 module を全部消しても最長 node は同じで、短縮は **0 秒**。対象 module 内の最長は
  74.24 / 41.88 / 8.16 / 6.83 / 3.77 秒で床のはるか下にある。(c) 最遅 shard は**仕事量が最大の shard では
  ない** — shard-0 は W が 1,225 秒多いのに wall は 4.0 秒短い。wall の律速は testcase 時間の外側にある。
- **改修前後の比較 (改修前 48 走 / 改修後 22 走、いずれも canonical K=3)。** W 全体 28,729 → 17,256 秒
  (0.60)。対象 5 module は `test_autonomous_trial_completeness` 0.10 / `test_p3_b4_raw_record_producer` 0.23 /
  `test_p3_b4_closed_critic` 0.10 / `test_trial_registry` 0.17 / `test_layer3_report` 0.08。
  binding を通らない対照 2 module は 0.98 / 0.99。**対照が動かないので W の低下は改修に帰属できる。**
  先行 wave が受入形でない 1 走で得た比と一致し、受入形でも同じ大きさで再現した。
- **wall の改善は主張しない。** 最遅 shard wall の中央値は 392.4 → 317.1 秒だが、走ごとに別 wave・別ノード・
  別負荷で同一条件の対照がない。300 秒未満は改修後 22 走中 6 走 (改修前は 48 走中 1 走)。本走は 315.4 秒で未達。
- **床が交代した。** 対象 5 module を除いた残存最長 node の所在は、改修前が
  `test_p3_autonomous_workload_trial` 37 / 48 走だったのに対し、改修後は `test_s8b_oracle_driver` 21 / 22 走。
  対象 5 module に挙がっていなかった `test_p3_autonomous_workload_trial` も W 621 → 178 秒 (0.29) で、
  同じ binding 経路を通っていた。D1714 が「次の床」と名指しした
  `test_t080_stub_free_e2e_single_defects...[ccbench-current...]` が実際に本走の最長 node になった。
- **依頼が引いた改修前 wall の基準値は一次資料から再現できない。** 依頼文と worklog 1351 の
  「最遅 shard wall 中央値 286 秒 / p75 350 秒 (09-08 分)」に対し、09-08 の改修前 80 走の最遅 shard wall は
  **最小値が 296.67 秒**で、286 秒は観測された最小値より小さい。どの部分集合でも中央値になり得ない。
  W の四分位が先行記載と一致する窓 (00:00〜07:15、48 走) では中央値 392.4 秒 / p75 441.1 秒だった。
  最も近い分布は 09-05 の 28 走 (中央値 291.1 / p75 359.9 秒) で、日付の取り違えの可能性がある。
  **W の基準値 28,734 秒のほうは同窓で 28,729 秒として再現できた**ので、集計面は先行 wave と同じである。
  過去の測定事実は取り消さず、改修前 wall の所在を 392.4 秒 (p75 441.1 秒) として置き換えて記録する。
- **D1620 の記述と現物の齟齬を 1 件見つけた (本 wave では直さない)。** D1620 は測定面を
  「canonical 起動の receipt が記録する最遅 shard の wall」と書くが、現行の受領証 schema
  `dev-wave-acceptance-receipt/v5` に shard 別 wall の field は無い (本走の受領証で確認)。実際に読める面は
  shard junit の `testsuite@time` で、これは D1618 の「最遅 shard の pytest wall」と同じものである。
  面そのものは変わらないので測定は成立しているが、「receipt が記録する」という記述だけが現物と合っていない。
  依頼の外なので裁定へ返す。
- 段 2・3・5・6 の子はゼロ。実装面の差分がなく、設計択一も正しさ防壁も受理集合も動かないため軽量版で通した。
  D95 決定 2 により変異 matrix は免除、受入全走は免除せず実走した。
- 工数: Codex 子 0。親 = Claude 1 context。

## 次の一手差分

### 完了

- [T-2443] 改修後の canonical 走 (K=3) を取り、対象 5 module の W と最遅 shard wall を D1714 の読み方で
  記録した。改修前の wall 基準値が一次資料と合わないことも併記した。
  remaining: none
  base: e7890223168af349c997e8140d52f7e1654ee265a1369d86224acc9b7655cbf5

### 新規

- {{T:d1620-receipt-wall-field-wording}} **P3・裁定待ち**: D1620 の「receipt が記録する最遅 shard の wall」
  という記述を現物へ合わせるか決める。受領証 schema `dev-wave-acceptance-receipt/v5` に shard 別 wall の
  field は無く、実際に読めるのは shard junit の `testsuite@time` (= D1618 の面) である。測定面自体は
  変わらないので、選択肢は (a) D1620 の文言を junit 側の面へ訂正する、(b) 受領証へ shard wall を足して
  記述どおりにする、の 2 つ。どちらも受理集合には触れない。
