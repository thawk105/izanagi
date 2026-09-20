## 対応表

出所パスは対象ディレクトリからの相対パス。判定は本文全体での反映状況による。

| 初回所見 | 判定 | 根拠・再計算結果／残る差分 |
|---|---|---|
| 1. model の介入対象 | **closed** | 結論5・§5(a)・§8は「中央値のある未収載333 node全部」に訂正し、事前登録の8 node条件との差も明記。`ledger-model.json:missing_ledger_nodes` と `junit_samples` の照合で **未収載334、中央値あり333、なし1**。各案の `workers[*].units` と `fixed_durations` から最大占有を再計算すると **253.264 → 233.739、差19.525秒**。既知unit costの降順96番目も **9.6 → 11.0** と一致。 |
| 2. plugin／path正規化への確定的帰属 | **partial** | 題名・結論3・§4・§6・§8は複合区間と解釈を区別し、§2b N4も21 sessionへの外挿を撤回。`t2817_probe_plugin.py.txt:pytest_itemcollected, pytest_collection_finish` と集計器の `cell()` は関数別計時ではない。`tools/acceptance_shards.py:records_from_items, pytest_collection_modifyitems` では正規化2回を確認。**残差：§5(b)だけ「plugin modify 45」「plugin の modifyitems の内訳」と記し、複合区間45秒をpluginへ戻している。ここも「modify複合区間」に統一する必要がある。** |
| 3. 占有和と経過時間の混同 | **closed** | 結論1・§3.2は占有和と後続開始時刻を分離し、t起点も明記。`raw/job-out-b/analysis-A.json:shard.O_max_timeline` の先頭26件は **54.165秒**、全28件は **54.165 + 180.595 + 46.232 = 280.992秒**。reportの `shard.O_max=280.990634055` との差は約0.001366秒で、丸め精度内。 |
| 4. 最大差・rank母集団 | **closed** | §2b N3/N4を訂正。`verbatim/shards-recent-v1.json:[session=408dd532, shard=shard-0]` から **123.892635345 − 45.498091384 = 78.394543961秒**。`verbatim/t2724-nodes-v3.json:rows` の8 node全件をsession別に集計すると、18 sessionが **422〜430**、`fd6825ad` が **420〜428**、末尾2 sessionが **374〜382**。本文の19 sessionを束ねた420〜430という範囲と一致。 |
| 5. 発行件数・待ち手 | **closed** | §3.2は発行6 key、待ち手を「1秒超の全件」と明記。`analysis-A.json:keys[*].builds[*].seconds.issue` は正値 **6件、69.102464〜69.883867秒**、非発行1件。`keys[*].flock_waits` の1秒超10件も全て表にあり、gw5〜10の182.0秒、gw46の125.3秒、gw14/45/47の143.6/144.6/145.3秒と一致。 |
| 6. Δ32を処理費用上限とする誤読 | **closed** | 結論3・§4は正味差に限定し、相殺と未分離を明記。`job-out-aggregate.json:cells[*].xdist.workers[*].times` からΔ32を再計算すると **0.888104 / 0.235473秒**。modify中央値差は **−0.976222 / −0.766089秒**、`cells[*].wall` の差は **0.88 / 0.29秒**。記述と一致。 |
| 7. 並走式の変更後への外挿 | **partial** | 結論5は「他方の所要・開始時刻を固定した場合」を追加。model差の理由も結論5・§5(a)で候補に限定。**残差：§5(b)は依然「片方だけを縮めても…もう片方で止まる」と無条件に記載。表にも固定条件を付ける必要がある。** |
| 8. model・参照条件の限定 | **closed** | §8は `ledger-model.json:limitations` に対応して保存順・同値順、先読み未再現、欠損時代用等を明記。結論3・§4・§8は同SHAから同codeへの変更を明示。worker時刻から求めたS3平均は **61.450055957秒**。`verbatim/acceptance-ref-shards.json:[shard=shard-0].pre` との差は **−0.312303185秒**、`analysis-A.json:shard.pre` との差は **−0.495372415秒**で、−0.31/−0.50と一致。 |
| 9. Job B相対パス | **partial** | 結論・§3.2見出し等は修正済み。**残差：§3.2のO_max worker説明末尾に `job-out-b/analysis-A.md` が残る。`raw/job-out-b/analysis-A.md` に直す必要がある。** |
| 数表不一致1：8 → 333 node | **closed** | 結論5・§5(a)。所見1の集合照合で **334 − 1 = 333** を確認。 |
| 数表不一致2：83.1 → 78.4秒 | **closed** | §2b N4。pairingあり・shard-0の21件から最大を再計算して **78.394543961秒 → 78.4秒**。 |
| 数表不一致3：54.5 → 占有和54.2秒 | **closed** | 結論1・§3.2。timeline先頭26件の和 **54.165秒 → 54.2秒**。54.5秒は後続開始時刻として区別された。 |
| 数表不一致4：発行7 → 6 key | **closed** | §3.2。共有7 key中、`seconds.issue > 0` は **6 key**。 |

追加で指定された派生値も検算した。

- **段差平均**：workerの `cf_exit` 最大値とJUnit起点から再計算し、Δ10 **−2.128409743**、Δ21 **45.936486006**、Δ32 **0.561788201秒**。§3.1の−2.13／45.94／0.56と一致。
- **正規化件数**：`verbatim/trailing-whitespace-normalization.json:* .stripped_lines` は **14 file・90行**。初回13 file・60行とレビュー1 file・30行に分かれる。各ファイルへsuffixを戻し、原文・正規化後のbytes数とSHA-256を照合して **全14件一致**。

## 新規所見

無し。残存する帰属表現・並走条件・相対パスは、初回所見2・7・9の未完了分として扱った。

## 総括

対象13件は **closed 10件 / partial 3件 / regressed 0件**。
指定された派生値は原データから再計算し、記載値との一致を確認した。
**must-fix残数は1件**：§5(b)に残る、modify複合区間45秒のplugin単体への帰属。
**NO-GO**。所見2・7・9の残存箇所を修正する必要がある。