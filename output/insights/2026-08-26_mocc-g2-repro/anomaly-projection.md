# 本 study の anomaly 5 件の構造化投影

段 6 レビュー [RA-7] / [RB-6] の指摘に応じた投影である。`runs/<ordinal>/verifier.json` は
cycle・edge・key・version を持つが **thid を持たない**。thid は trace 原本にしかなく、
原本は repo 外へ退避してある。ここでは原本から読んだ値と、原本を特定する SHA-256 を repo 内へ写す。

**これは事前登録 §7 の副次解析 (a)(c) の素データである。** 因果の主張はここでは行わない。

## trace 原本の所在

repo 外: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-g2-repro-20260826/evidence/job-staging/0:<request>/run/trace/`

trace の行形式は `C <txid> <thid> <epoch> <tid> <n_read> <n_write>`。

## 5 件の逐語

### ordinal 19 — `950401.nqsv` (host bnode008)

```
C 691105 46 69 4358 5 5
C 691107 39 69 4359 4 6
```

| edge | type | key | u_ver | v_ver |
|---|---|---|---|---|
| 691105 -> 691107 | rw | `0000000000000002` | (69, 4355) | (69, 4359) |
| 691107 -> 691105 | rw | `000000000000000b` | (69, 4355) | (69, 4358) |

- `run/trace/trace_46.log` sha256 `64ddb3941512d605d0ef7b97bc23b9f55ccbd49b6e42e76ee825351209888ae6`
- `run/trace/trace_39.log` sha256 `5a7b9af72bd93706adade37d54e959bbb5528a4e2ba2792c03b9b2dd2af8bec7`

### ordinal 24 — `950408.nqsv` (host bnode036)

```
C 319459 13 32 3988 5 5
C 319460 28 32 3989 3 7
```

| edge | type | key | u_ver | v_ver |
|---|---|---|---|---|
| 319459 -> 319460 | rw | `0000000000000001` | (32, 3987) | (32, 3989) |
| 319460 -> 319459 | rw | `0000000000000049` | (32, 3982) | (32, 3988) |

- `run/trace/trace_13.log` sha256 `4637563fff2c7f8149a72692ed1d84d3d7ae4dac5f2fcb165d6332df2cd7b8fb`
- `run/trace/trace_28.log` sha256 `555ff7507051129e0c971a07c546bba4277a15c8007892956bcd93dd35c59040`

### ordinal 30 — `950424.nqsv` (host bnode061)

```
C 501707 17 49 591 7 2
C 501708 31 49 592 5 5
```

| edge | type | key | u_ver | v_ver |
|---|---|---|---|---|
| 501707 -> 501708 | rw | `0000000000000001` | (49, 587) | (49, 592) |
| 501708 -> 501707 | rw | `0000000000000000` | (49, 590) | (49, 591) |

- `run/trace/trace_17.log` sha256 `ecb3e12947eeca2c0f8936d267da05cd1422ac8709baa5585a5b7b35c8508b03`
- `run/trace/trace_31.log` sha256 `61bcb5a8887fe9fb7296dfd92a7e6e17c998263e4225bc808a11c238509e9db9`

### ordinal 31 — `950437.nqsv` (host bnode064)

```
C 27629 29 4 839 3 6
C 27630 15 4 840 5 5
```

| edge | type | key | u_ver | v_ver |
|---|---|---|---|---|
| 27629 -> 27630 | rw | `0000000000000006` | (4, 825) | (4, 840) |
| 27630 -> 27629 | rw | `0000000000000000` | (4, 838) | (4, 839) |

- `run/trace/trace_29.log` sha256 `9b754d93f72ac370aed315b622ce05fb54af86840192370449fa724bdff7938b`
- `run/trace/trace_15.log` sha256 `bbb832b9bdf082a46e85b3290b7c92357d8ac1bda7a6e64118b7a214200c67be`

### ordinal 32 — `950438.nqsv` (host bnode023)

```
C 181195 13 19 309 5 4
C 181196 21 19 310 4 6
```

| edge | type | key | u_ver | v_ver |
|---|---|---|---|---|
| 181195 -> 181196 | rw | `0000000000000002` | (19, 305) | (19, 310) |
| 181195 -> 181196 | rw | `0000000000000055` | (19, 201) | (19, 310) |
| 181196 -> 181195 | rw | `0000000000000000` | (19, 308) | (19, 309) |

- `run/trace/trace_13.log` sha256 `c2a0721fa7d5571f16b203a05e28645e43b05649dac9b49f04f4183515037ea9`
- `run/trace/trace_21.log` sha256 `2f9f1a7b441c5e427e9220ea6e9d70d14b810b5fb0043618a7cce55c5e02708e`

## 5 件を並べて観測できること (記述のみ)

| ordinal | thid | commit version | tid の差 | txid の差 |
|---|---|---|---|---|
| 19 | 46 / 39 | (69,4358) / (69,4359) | 1 | 2 |
| 24 | 13 / 28 | (32,3988) / (32,3989) | 1 | 1 |
| 30 | 17 / 31 | (49,591) / (49,592) | 1 | 1 |
| 31 | 29 / 15 | (4,839) / (4,840) | 1 | 1 |
| 32 | 13 / 21 | (19,309) / (19,310) | 1 | 1 |

- **5/5 で cycle 長は 2、全辺が rw、`total_cycles` は 1、integrity は clean。**
- **5/5 で 2 つの transaction の thid は異なる。**
- **5/5 で 2 つの commit version は同一 epoch、tid の差は 1 である。**
- 前向き辺の key は `0x1` / `0x2` / `0x6` と小さく、後ろ向き辺の key は
  `0x0` が 3 件、`0xb` と `0x49` が各 1 件である。
  workload は zipf skew 0.9 なので小さい key ほど高頻度に触られる。
- ordinal 32 だけ前向き辺の理由が 2 本 (key `0x2` と `0x55`) ある。

**前 wave (`949964.nqsv`) の 1 件は本 study の N・m・k に入らない。**
その投影は `pilot-anomaly-projection.md` にある。同 wave の観測は thid 40 / 21、
commit version (53,2868) / (53,2869) で、上と同じ形をしている。
**これは既知資料としての参考であって、本 study の副次解析の一部ではない。**
