# 親 brief の訂正 (2026-08-27 06:45 JST、親が自分で発見した)

brief の実測表は ledger の key を `@<group>` suffix ごと別 key として数えていたため、
suffix 付きで記録されている node の所要を落としていた。suffix を正規化して再計算した値は次のとおり。

| access (parent, ccbench) | node 数 | ledger 合計 | ledger に無い node |
|---|---|---|---|
| (read, read)  | 52 | 214.24 s | `test_codex_reasoning_ab.py::test_m3_focus_artifact_directions` |
| (read, None)  | 28 |  40.92 s | `test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged` |
| (None, read)  |  6 |   3.57 s | — |
| (read, write) |  3 |   0.00 s | — |
| (None, write) |  1 |   **0.19 s** (brief は 0.00 と書いた) | — |
| **合計**      | **90** | **258.92 s** (brief は 258.73 と書いた) | 2 件 |

**0.00 秒の意味も確定した。** `(read, write)` の 3 本はいずれも
`test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache*` /
`test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2` で、
ledger に 0.0 として載っている。**「速い」ではなく「計測走で走っていない」可能性が高い。**
どの機構で走らなかったのか (growth hold ではない — 親は GROWTH_TEST_HOLDS に無いことを確認した)
は未確定であり、段 2 / 段 3 で確かめる対象である。

結論の向きは変わらない。**排他鎖の所要のほぼ全量が、共有 (SH) ロックしか取らない node である。**

## 追記 (06:50 JST) — 0.00 秒の正体と、regime 依存

`(read, write)` の 3 本は `@pytest.mark.skipif` で
「初期化済み ccbench + 固定 toolchain (`cmake` / `gcc-13` / `g++-13` / `nm`)」を要求する
slow real-build canary である (`orchestrator/tests/test_s8b_floor_campaign.py:9007-9012` と
`test_s8b_oracle_driver.py` の同型 guard)。

**親がこの login node で実測した:** `cmake` と `nm` は在るが `gcc-13` / `g++-13` は不在。
したがって**この regime では 3 本とも skip される。** ledger の 0.0 はこれで説明がつく。

**この事実は 2 つの regime を分ける。**
- login node (受入をローカルで走らせる regime): 排他 (EX) を取る node は実質 1 本・0.19 秒。
- 固定 toolchain のある計算ノード regime: 3 本が実際に走り、`ccbench` へ EX を取り、
  実 build cache へ書く。**所要も未知である。**

**したがって「排他 writer は無視できる」は login node regime 限定の言明であり、
計算ノード regime へ転移させてはならない。** 細分化の設計は
「EX writer が実際に走る regime でも排他の意味が保たれる」ことを満たさなければならない。
床の主張も regime を明記して書く。
