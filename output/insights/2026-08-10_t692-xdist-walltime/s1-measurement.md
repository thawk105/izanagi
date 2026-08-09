# 段 1 実測所見 — dev-wave-t692-r3-xdist-walltime

一次資料: `junit-baseline.xml` / `analysis-baseline` (= `analyze-out.md` 内の全量出力) /
`measure1.log` / `measure2.log` / `junit-serial3.xml`。

## M1. baseline 全走 (計測 1)

- job `898058.nqsv` / bnode055 / base `4be7a362` / 48 worker / `--dist loadgroup`
- 7685 passed / 20 skipped / **wall 1407.97 秒** (PBS Elapse 1419 秒、上限 2400 秒)
- 直列総和 **16534.55 秒** → 実効並列度 **11.74 worker 相当 = 48 の 24.5%**

## M2. group ごとの直列和

| group | 直列和 (秒) | node 数 |
|---|---|---|
| `real-repo` | **1388.80** | 43 |
| `real_repo` (表記ゆれ、[T-438]) | 69.45 | 1 |
| `s8c-preregistration-candidate` | 58.35 | 3 |
| `dev-waves-runtime` | 16.17 | 22 |
| (group 未指定) | 15001.78 | 7636 |

- critical path 下界 = max(最大 group 直列和, 直列総和/48) = **1388.80 秒**。
  実測 wall 1407.97 秒との差 19 秒がスケジューリング余剰である。
  **wall は `real-repo` group の直列和でほぼ完全に説明できる。**
- **worker は余っている。** 並列度を上げても下界は動かない (下界は最大 group が決める)。
  2026-07-30 の `-n 48` vs `-n 32` がほぼ同値だった実測とも整合する。

## M3. `real-repo` group の内訳 (43 node / 1388.80 秒)

| 順 | 秒 | node |
|---|---|---|
| 1 | 680.23 | `test_s8b_binding_driftguards::test_run_block_broken_binding_manifest_refuses_and_writes_nothing` |
| 2 | 653.50 | `test_s8b_oracle_driver::test_cli_subprocess_returns_rc_2_on_gate_refused` |
| 3 | 18.85 | `test_s8b_oracle_driver::test_real_freeze_gate_lists_floor_and_budget_null` |
| 4 | 18.19 | `test_s8b_repo_scan_invariant::test_real_repository_scan_matches_known_hits_and_has_positive_control` |
| 5〜43 | 合計 18.03 | (残り 39 node、いずれも 6 秒未満) |

**上位 2 本で group の 96.0%。** 残り 41 node の合計は 55.07 秒しかない。

## M4. 670 秒帯の正体 (計測 2 = 切り分け実験)

group 未指定側にも 631〜680 秒の testcase が約 16 本並ぶ (すべて `test_s8b_oracle_driver`)。
これが本質的な仕事量か並行競合かを、**同じ 3 本を `-n 0` (直列・単一プロセス) で**走らせて切り分けた。

- 結果: **3 本合計 433.56 秒**
  - `test_oracle_pipeline_contract_keyword_is_mandatory_positive_control` = **427.58 秒**
  - `test_success_wal_order_budget_and_evaluate_contract` = **3.27 秒**
  - `test_run_block_broken_binding_manifest_refuses_and_writes_nothing` = **2.08 秒**
- 全走での同 3 本は 671.55 / 671.37 / 680.23 秒。

**【2026-08-09 訂正 — 段 3 レンズ A/B の指摘により】**
**この実験はログインノードで走った。** `junit-serial3.xml` の `hostname="pegasus02"`、
`measure2.log:2` に「ログインノードで … bounded local」と記録がある。`run_tests.py` が
計算ノードへ dispatch するのは受入形 (全 suite) のときだけで、node 指定の部分走は
ログインノード上の bounded local 実行になる。baseline (bnode055) とは**機体が違う**。

したがって次は**撤回する**:
- 「427.58 秒」を bnode055 の観測として扱うこと。
- 「428 → 670 秒の膨張は 48 worker 競合である」という分解。機体差・page cache・
  git object cache の差を分離していない。

**この実験がなお示すこと (機体に依らない構造的事実):**
単一プロセス内では、最初の 1 本だけが実 repo の T-080 receipt 解決を払い、
以後の同種テストは memo / session cache により 2〜3 秒になる
(427.58 → 3.27 → 2.08 秒)。670 秒帯が「仕事量 × 本数」でないことはこれで否定できる。
ただし全走の 670 秒帯が**共有解決の待ちである**ことまでは、この実験では確定していない
(開始時刻・lock owner が記録されていないため)。

## M5. critical path の分解 (M3 + M4 から)

`real-repo` group 1388.80 秒 ≒ 680.23 (共有解決の完了待ち)
+ 653.50 (**subprocess による再解決**) + 55.07 (残り 41 node)。

2 本目 `test_cli_subprocess_returns_rc_2_on_gate_refused` は CLI を**別プロセスで起動する**ため、
`mock.patch` によるプロセス内 memo が効かない。直列単独走で 2 秒だった 1 本目と違い、
この 653 秒は「待ち」ではなく**実際に解決をもう一度払っている**可能性が高い
(未検証。段 2/段 3 で機序を確定させること)。

## M6. R3 の値段 (数値化)

- R3 原案 (実 repo 読取テストを `real-repo` へ寄せる) は、**寄せた分がそのまま
  critical path に加算される**。[T-438] の ruleops 1 本を canonical group へ移す場合は
  **wall +69.45 秒** (現行 1408 秒に対し +4.9%)。
- 逆に上位 2 本を group から安全に外せる / 待ちを消せるなら、下界は
  1388.80 → **708.57 秒** (残り 41 node + 653.50) あるいはさらに下がる。
- **フレーク除去と wall 短縮は同じ 1 本の直列鎖を取り合う。** 両方を満たす設計を段 2 で作る。

## M7. 主張しないこと

- 653.50 秒が「解決の二重払い」だと**まだ確定していない** (M5 の未検証点)。
- 428 秒は bnode055 上の 1 回の観測であり、ノード間差 (既知で最大 1.8 倍) を含まない。
- 本 wave は個別テストの中身を速くしない (`dev-wave-suite-floor-recheck` の所有)。
  ここで測った 428 秒は、その wave が短縮しようとしている量そのものである。
