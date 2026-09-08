# 受入全走の所要 — 改修後の canonical 走 (K=3) と 09-08 改修前分布の比較 [T-2443]

- authority: none (可変状態の正本は worklog と decisions。本書は一次資料の置き場)
- default_effect: no-state-change
- wave: `dev-wave-t2443-acceptance-duration-20260908` / branch `worktree-dev-wave-t2443-acceptance-duration-20260908`
- base main: `cc9bba523ac7804aadb7891d686bf4c925789a3f` (実装差分ゼロ。本 wave は計測と記録だけ)
- 実測日: 2026-09-08 (Pegasus login pegasus02 から投入、計算ノード bnode012 / bnode094 / bnode095)
- 一次資料: `/work/1/SFC/tanab/.izanagi-acceptance-shards/<group>/junit.xml` (受入走の合算 junit)。
  本走の group は `a06ed38d35e769589ebb63a401e74b6e`。集計値は本 dir の `measurements.json`
- 読み方の正本: D1714 (最長単体を犯人にせず 3 点を併記する)、D1618 (面は最遅 shard の pytest wall)、
  D1620 (5 分目標の測定面)、D1795 (改修の内容)

依頼は「受入全走の所要を 09-08 の改修前分布と比べて記録する。canonical 起動 (K=3) の junit を取り、
対象 module の W と最遅 shard wall を D1714 の読み方で記録する。1 走では wall の改善を主張しない」。

---

## 0. 測る面の定義

| 記号 | 定義 | 出所 |
|---|---|---|
| W | 1 走の全 testcase の junit `time` 属性の総和 (3 shard 合算)。直列総仕事量 | 合算 junit |
| shard wall | shard ごとの `testsuite@time` (= その shard の pytest wall)。queue 待ちを含まない | 同上 |
| 最遅 shard wall | 1 走の 3 shard のうち最大の shard wall | 同上 |

**改修の境界。** contract-loader binding の blob 取得を 2 process へ改めた `6e885df4f` は、
local main が `ab51c7a2f` へ進んだ **2026-09-08 14:33:20 JST** に main へ入った。受入は claim 直後に
local main を wave branch へ merge するため、**これ以降に投入された受入走はすべて改修後**である。
改修前の窓は 09-08 00:00〜07:15 (48 走) を使う — 先行 wave (worklog 1351) の記載 W 中央値 28,734 秒
(p25 24,691 / p75 35,645、47 走) を、同じ集計で 28,729 秒 (24,716 / 34,983、48 走) と再現できる窓である。

---

## 1. 本 wave の canonical 走 (K=3)

受領証 `dev-wave-acceptance-receipt/v5` は `verdict=child-green`、`tested_main` = `tested_tip` =
`cc9bba523`、`red_nodeids` / `flake_nodeids` はいずれも空。子の集計行は **21,971 passed / 68 skipped**、
赤 0。K=3 は受入 log の `IZANAGI_ACCEPTANCE_SHARD_ARTIFACTS_V1 {"shard_count":3}` が示す。

### (c) 3 shard それぞれの wall と最遅 shard の identity

| shard | pytest wall | 実行ノード | 開始 | その shard の W | node 数 |
|---|---:|---|---|---:|---:|
| shard-0 | 311.38 秒 | bnode095 | 19:45:57 | 7,094 秒 | 7,347 |
| shard-1 | 205.90 秒 | bnode094 | 19:45:55 | 4,558 秒 | 7,346 |
| **shard-2 (最遅)** | **315.40 秒** | bnode012 | 19:45:56 | 5,869 秒 | 7,346 |

W 全体 = **17,521.8 秒** (22,039 node)。

**最遅 shard は最大の仕事量を持つ shard ではない。** shard-0 は W が最遅 shard より 1,225 秒多いのに
wall は 4.0 秒短い。すなわち wall の差は testcase 時間の外側 (collection・report 外費用・ノード差) にある。

### (a) 最長 node の分布

上位 10 node は**すべて** `test_s8b_oracle_driver` で、すべて shard-0 にある。

| 秒 | node |
|---:|---|
| 185.86 | `test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]` |
| 181.99 | `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5` |
| 175.22 | `test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known_axes...]` |
| 174.32 | `test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modified...]` |
| 173.13 | `test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknown...]` |

D1714 が「次の床」として名指しした
`test_t080_stub_free_e2e_single_defects...[ccbench-current...]` が、実際に本走の最長 node になった。

### (b) 対象 5 module を全部消したときの残存最長 node

**変化しない。** 対象 5 module を全部除いても最長 node は同じ 185.86 秒の node で、短縮は **0 秒**である。
対象 module 内の最長 node は次のとおりで、いずれも 185.86 秒の床のはるか下にある。

| module | その module 内の最長 node |
|---|---:|
| `test_p3_b4_raw_record_producer` | 74.24 秒 |
| `test_trial_registry` | 41.88 秒 |
| `test_autonomous_trial_completeness` | 8.16 秒 |
| `test_p3_b4_closed_critic` | 6.83 秒 |
| `test_layer3_report` | 3.77 秒 |

---

## 2. 改修前分布との比較

改修前 = 09-08 00:00〜07:15 の 48 走、改修後 = 14:33:20 以降に投入された 22 走 (本走を含む)。
どちらも canonical 起動 (K=3、shard 合算) である。

| 対象 | 改修前 中央値 (最小) | 改修後 中央値 (最小) | 比 | 本走 (n=1) |
|---|---:|---:|---:|---:|
| **W 全体** | 28,729 (22,076) | 17,256 (14,579) | **0.60** | 17,522 |
| `test_autonomous_trial_completeness` | 1,890 (1,232) | 184 | 0.10 | 225 |
| `test_p3_b4_raw_record_producer` | 1,399 (682) | 318 | 0.23 | 281 |
| `test_p3_b4_closed_critic` | 1,296 (825) | 133 | 0.10 | 148 |
| `test_trial_registry` | 2,078 (1,434) | 361 | 0.17 | 389 |
| `test_layer3_report` | 854 (594) | 70 | 0.08 | 126 |
| `test_campaign` | 706 | 185 | 0.26 | 178 |
| `test_p3_s4_loop` | 772 | 122 | 0.16 | 137 |
| `test_critic` | 835 | 86 | 0.10 | 154 |
| 対照 `test_s8b_oracle_driver` | 2,472 | 2,428 | **0.98** | 2,165 |
| 対照 `test_s8b_floor_campaign` | 2,037 | 2,009 | **0.99** | 1,813 |
| **最遅 shard wall** | 392.4 (297.1) | 317.1 (270.3) | 0.81 | 315.4 |

**読み方。** binding を通らない対照 2 module が 0.98 / 0.99 に留まる一方、対象 module は 0.08〜0.23 まで
落ちている。したがって W の低下はノード負荷の差ではなく改修に帰属できる。この比は先行 wave が
受入形でない 1 走で得た比 (0.03〜0.40、全体 0.60) と一致し、**受入形 (K=3) でも同じ大きさで再現した**。

**wall については改善を主張しない。** 本走は 1 走であり、改修後 22 走も走ごとに別 wave・別ノード・
別負荷である。上表の 0.81 は同一条件の対照を持たない。言えるのは分布の所在だけである。

---

## 3. 床の交代

対象 5 module を除いたときの「残存最長 node」がどの module に居るかを走ごとに数える。

| | 改修前 48 走 | 改修後 22 走 |
|---|---|---|
| 残存最長の module | `test_p3_autonomous_workload_trial` 37、`test_s8b_oracle_driver` 9、`test_p3_b4_material_report` 2 | `test_s8b_oracle_driver` 21、`test_p3_b4_material_report` 1 |
| 残存最長 node の秒 (中央値) | 302.1 | 210.7 |
| 最長 node が対象 5 module 内だった走 | 3 / 48 | 0 / 22 |

`test_p3_autonomous_workload_trial` は依頼の対象 5 module に入っていないが、W が 621 → 178 秒 (0.29) へ
落ちており、同じ binding 経路を通っていたことがわかる。これが床から退いた結果、**現在の床は
`test_s8b_oracle_driver` 単独**になった (改修後 22 走中 21 走)。D1714 の「180〜290 秒の帯に複数の node が
並んでおり単独の犯人はいない」という状況は、改修後は「1 module が帯を占める」形へ変わっている。

---

## 4. 5 分 (300 秒) 目標に対する現在地

D1620 の面で見た最遅 shard wall は、改修後 22 走で中央値 317.1 秒・p25 292.5 秒・最小 270.3 秒。
**300 秒を下回ったのは 22 走中 6 走**である。改修前 48 走では 1 走 (48 走中) だけだった。
本走は 315.4 秒で未達である。

W が 0.60 になっても wall が 0.81 にしかならないのは、§1 (c) の分解が示すとおり wall の律速が
testcase 時間の外側にあるためで、D1618 / D1714 が繰り返し記録してきた構造と整合する。

---

## 5. 依頼の基準値との食い違い (一次資料が優先)

依頼文と worklog 1351 は改修前の所在を「**最遅 shard wall 中央値 286 秒 / p75 350 秒 (09-08 分)**」と
書いている。**この値は一次資料から再現できない。**

- 09-08 の改修前 (00:00〜14:33:20) は 80 走あり、**最遅 shard wall の最小値が 296.67 秒**である。
  286 秒は観測された最小値より小さく、どの部分集合を取っても中央値になり得ない。
- W の四分位が一致する窓 (00:00〜07:15、48 走) では中央値 392.4 秒 / p75 441.1 秒。
- 最も近い分布は **09-05 の 28 走 (中央値 291.1 秒 / p75 359.9 秒)** で、日付の取り違えの可能性がある。
- W の基準値 28,734 秒のほうは再現できた (同窓で 28,729 秒)。食い違うのは wall の 2 値だけである。

したがって本書は、改修前の wall の所在を **392.4 秒 (p75 441.1 秒)** として記録する。
これは worklog 1351 の記述を否定するのではなく、同じ一次資料から再計算した値で置き換えるものである
(過去の測定事実は取り消さない — 規律 7)。

### 付随して見つかった記述の齟齬 (本 wave では直さない)

D1620 は測定面を「canonical 起動の **receipt が記録する** 最遅 shard の wall」と書くが、
現行の受領証 schema `dev-wave-acceptance-receipt/v5` に shard 別 wall の field は存在しない
(本走の受領証で確認)。実際に読める面は shard junit の `testsuite@time` であり、これは D1618 の
「最遅 shard の pytest wall」と同じものである。**面そのものは変わらないので測定は成立している**が、
「receipt が記録する」という記述だけが現物と合っていない。記述の是正は受理集合に触れる判断ではないが、
本 wave の依頼 (実測と記録) の外なのでユーザー裁定へ回す。

---

## 6. 再現手順

1. 受入全走を canonical 起動で投入する
   (`tools/dev_wave_wait.py acceptance --wave <slug> --receipt-file <repo 外> --log-file <repo 外> -- python3 tools/run_tests.py`)。
2. 受入 log の `IZANAGI_ACCEPTANCE_SHARD_ARTIFACTS_V1` が指す `session_root` の `junit.xml` を読む。
3. 全 `testcase@time` を合算して W、`classname` の末尾要素で module 別 W、`testsuite@time` で
   shard wall と最遅 shard を取る。
4. 改修前後の切り分けは、`6e885df4f` が main に入った時刻 (2026-09-08 14:33:20 JST、main `ab51c7a2f`) を
   境に、受入 group の `dispatch-intents/shard-0.intent.json` の投入時刻で行う。

集計に使った使い捨てスクリプトは repo 外 (job dir) に置いた。集計結果は `measurements.json` にある。
