# 制約検算の逐語 — [T-244] U-10

親が実走した検算の記録。判定はすべて production の実関数を直接呼び、
自前で制約を再実装した判定は行っていない。

- import root: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u10-draft`
- 呼んだ実関数: `orchestrator/campaign/reflux_origin_ledger.py` の
  `_budget_from_object` (:315) と `_check_budget_codec_feasibility` (:2284)。
  PASS / FAIL は production 例外の有無だけで決めている。
- floor の `formula_id` = `q-lower-bound/base+perRound*R+Emin/v1` (受理される唯一の値)
- literal 定数: `_MAX_BATCH_MEMBER_ROW_COUNT = 2248`、`_MAX_CLASS_CARDINALITY = 15650`、
  `_MAX_LEDGER_BYTES = 67108864`

**この検算が確かめたのは「parse と codec 直列化が受理するか」だけである。**
値の科学的妥当性、32 mask の物理被覆、query と evidence row の対応、8c からの到達可能性は
検証していない。

---

## 1. 推奨 tuple と近傍 (親が実走。逐語)

```
| case              | Imax | Qmax | Kmax | Bmin | cand | floor        | parse | F  | origin bytes | head tx bytes | headroom |
| 推奨 (訂正後)      |    4 |   68 |    1 |    2 |    1 | (1,32,1,0)   | PASS  | 33 |        75206 |         30753 |       35 |
| 旧推奨 (会計誤り)   |    4 |   66 |    1 |    2 |    1 | (1,32,1,0)   | PASS  | 33 |        73388 |         30753 |       33 |
| 再予約余裕なし      |    2 |   34 |    1 |    2 |    1 | (1,32,1,0)   | PASS  | 33 |        38356 |         16281 |        1 |
| Q = F ちょうど      |    2 |   33 |    1 |    2 |    1 | (1,32,1,0)   | PASS  | 33 |        37447 |         16281 |        0 |
| Q < F              |    2 |   32 |    1 |    2 |    1 | (1,32,1,0)   | FAIL  |  — |            — |             — | query floor is outside authority budget |
| Kmax = 0           |    4 |   68 |    0 |    2 |    1 | (1,32,1,0)   | PASS  | 33 |        75140 |         30753 |       35 |
| Kmax = 2           |    4 |   68 |    2 |    2 |    1 | (1,32,1,0)   | PASS  | 33 |        75273 |         30753 |       35 |
| cand=32 / Bmin=32  |    4 |   68 |    1 |   32 |   32 | (1,32,1,0)   | PASS  | 33 |        69262 |         16281 |       35 |
| E_min = 1          |    4 |   68 |    1 |    2 |    1 | (1,32,1,1)   | PASS  | 34 |        75206 |         30753 |       34 |
| R = 2              |    4 |  132 |    1 |    2 |    1 | (1,32,2,0)   | PASS  | 65 |       133382 |         30753 |       67 |
| R = 3              |    4 |  196 |    1 |    2 |    1 | (1,32,3,0)   | PASS  | 97 |       191558 |         30753 |       99 |
```

**「head tx bytes」は共有 head の総量ではない。** `_check_budget_codec_feasibility` の
第 2 戻り値は当該 origin の transaction 寄与分であり、共有 head の総量は
genesis frame と他 origin の寄与を足した値になる (:2377 と :1870)。

`R=2` / `R=3` 行の `Qmax` は、択一 6 と同じ会計 (探索 2 + 探索放棄 2 + P6 32R + P6 放棄 32R) で
再計算した値である。

## 2. `Kmax` の実効上限 (二分探索、親が実走)

```
Kmax max accepted = 15638   first rejected = 15639
拒否の逐語: Kmax exceeds codec feasibility
```

literal 定数 `_MAX_CLASS_CARDINALITY = 15650` との差 12 は、literal が SHA 配列単体の
概算上限であるのに対し、実際には counter・event wrapper・event hash を含む
`OriginSealed` frame 全体を 1 MiB gate に通すためである (:98, :846, :2310)。

## 3. 使い捨て probe による格子検算 (grid 1〜4)

Codex `role=author` が書いた probe を親が実走した。
probe 本体と全出力は repo 外に置き land しない。

- probe: `/work/1/SFC/tanab/dev-wave-jobs/t244-u10-draft/probe/u10_feasibility_probe.py`
- 出力: `/work/1/SFC/tanab/dev-wave-jobs/t244-u10-draft/probe-out.md`

| grid | 内容 | 結果 |
|---|---|---|
| 1 | `R∈{1,2,3}` × `E∈{0,1,32,64}` × `K∈{0,1,2}` × `B∈{2,32}` × `D∈{1,2}` × topology `I∈{1,32,16R,32R}` の 576 組 | **576 PASS / 0 FAIL** (parse と codec の受理のみ) |
| 2 | `Qmax` の 64 MiB 境界 (二分探索、`I` 連動) | 受理 73,717 / 拒否 73,718 (`authority budget exceeds ledger codec feasibility`) |
| 3 | 同一 policy の origin を 1 / 2 / 3 件載せた authority 全体 | いずれも PASS。3 件で authority 5,011 bytes / 共有 head 1,743,006 bytes |
| 4 | 単一 batch に `32R` 行を入れる形の最大 `R` | 受理 `R=70` (2,240 行) / 拒否 `R=71` (`batch minimum exceeds codec feasibility`) |

**grid 1 の 576 組に推奨 tuple (`I=4`) は含まれない。** topology 格子の `I` は
`1 / 32 / 16R / 32R` の 4 通りだけである。推奨 tuple の受理は §1 で別に確認した。

**grid 3 の manifest は budget policy 以外がダミーである。** workload descriptor・各 sha256・
CCBench OID・evidence path はすべて形式を満たすダミー値で、ycsb-a/b/c の実値ではない。
したがって grid 3 が示すのは **schema と容量の smoke test** までであり、
実 manifest を載せた authority の容量を証明したものではない。
