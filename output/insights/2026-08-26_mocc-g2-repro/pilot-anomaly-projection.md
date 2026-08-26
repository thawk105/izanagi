# 前 wave の G2 anomaly の構造化投影 (`0:949964.nqsv`)

段 3 luna [L-13] の指摘に応じた投影である。前 wave の結果文は cycle・version・integrity までしか
repo 内へ残しておらず、**どの thread の transaction だったかが repo 内資料から独立に確認できなかった。**
一次 trace は repo 外の退避先にある。ここでは、その原本から読んだ値と、原本を特定する
SHA-256 を repo 内へ写す。

**これは前 wave の 1 件の観測であり、本 study の N・m・k のいずれにも入らない。**

## 一次資料の所在と SHA-256

repo 外: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-trace-pair/evidence/paired-97906410/0:949964.nqsv/`

| ファイル | SHA-256 |
|---|---|
| `verifier.json` | `9631d12a48f4eebb47facae918640ea2194db4051601132b6cbfbfef418f5939` |
| `failure.json` | `ed16186b35d89ebd3d77b48288e9da34712a6b6c9968d015900c85e82c9ce04f` |
| `run/trace/trace_40.log` | `951fd0a899207ef6b8e6ca16f4e7a4ba6fd46de5633cadc7a435d36dd200209e` |
| `run/trace/trace_21.log` | `d002b437935a949a4820cf2066e19ef10ec25db6446a62b615a17136bcd84d3d` |

`failure.json` は `{"stage":"verifier","rc":1,"schema_version":"mocc-trace-pilot-failure/v1"}`。
**この run に `mocc-trace-pilot-receipt.json` は存在しない** (verifier 判定の直後に exit するため)。

## cycle に関与した 2 transaction (trace 原本の逐語から)

trace の行形式は `C <txid> <thid> <epoch> <tid> <n_read> <n_write>`、
`R <txid> <key> <ver_epoch> <ver_tid>`、`W <txid> <key> <op> <ver_epoch> <ver_tid>`。

### txid 515615 — `trace_40.log`

```
C 515615 40 53 2868 5 5
R 515615 00000000000009cc 53 1819
R 515615 00000000000010b5 53 2248
R 515615 0000000000000004 53 2866
R 515615 0000000000001d37 53 2791
R 515615 000000000000037e 53 2382
W 515615 0000000000002094 U 53 2868
W 515615 00000000000001d3 U 53 2868
W 515615 0000000000000000 U 53 2868
W 515615 0000000000000014 U 53 2868
W 515615 0000000000000048 U 53 2868
E 515615
```

### txid 515616 — `trace_21.log`

```
C 515616 21 53 2869 4 6
R 515616 000000000000003a 53 2850
R 515616 0000000000000d56 53 2140
R 515616 0000000000000005 53 2866
R 515616 0000000000000000 53 2867
W 515616 000000000000207f U 53 2869
W 515616 00000000000002a7 U 53 2869
W 515616 0000000000000106 U 53 2869
W 515616 0000000000000001 U 53 2869
W 515616 0000000000000004 U 53 2869
W 515616 0000000000000073 U 53 2869
E 515616
```

## 観測できる事実 (解釈ではない)

- **2 transaction は別 thread である。** thid 40 と thid 21。
  したがって「同一 thread の連続 transaction を取り違えた」という説は成立しない。
- txid は隣接 (515615 / 515616)、commit version も隣接 (`(53,2868)` / `(53,2869)`)、
  epoch は同一 (53)。
- cycle の 2 辺:
  - `515615 -> 515616` (rw, key `0000000000000004`): 515615 が `(53,2866)` を読み、
    515616 が直後版 `(53,2869)` を書いた。
  - `515616 -> 515615` (rw, key `0000000000000000`): 515616 が `(53,2867)` を読み、
    515615 が直後版 `(53,2868)` を書いた。
- integrity は clean (orphan_reads 0、version_dups 0、dup_txids 0、missing_txids 0、
  write_version_mismatch 0、malformed_keys 0、framing_violations 0、
  lock_coverage_violations 0、write_intent_violations 0、permutation_violations 0)。
- 関与した key はいずれも小さい整数 key (`0x0`, `0x4`, `0x5`) である。
  workload は zipf skew 0.9 なので、これらは最も高頻度に触られる側に属する。

## まだ確定していないこと (規律 3 に従い、構造化して残すだけ)

原因が (1) MoCC 実装の性質、(2) trace hook の記録の取り違え、(3) verifier の版順序仮定の不成立の
どれかは確定していない。それぞれについて、現時点で言えることだけを書く。

- **(3) について。** verifier は `Version = (epoch, tid)` の辞書式順序を「同一 key 上の版の
  全順序」として使う (`orchestrator/verifier/model.py:17-23`)。MoCC の commit TID は
  read/write set の最大 +1、同 worker の直前 TID +1、local epoch の最大で決まり
  (`external/ccbench` の `cc/mocc/transaction.cc:1018-1034`)、write set は施錠後に
  最大版を取る (`:896-908`)。**したがって同一 key の後続 writer は直前版より大きい
  `(epoch,tid)` を選ぶ**ので、この仮定は同一 key 上では支持される。
  ただし `tid` は 31 bit で overflow guard が無い (本観測の tid は約 2,869 で十分遠い)。
  **この分岐は弱まるが、消えてはいない。**
- **(1) について — 未確認の仮説。** Silo 系の validation は「write set を施錠してから
  read set を検証し、読んだ record が他者に write-lock されていたら abort する」ことで
  この形の cycle を防ぐ (`cc/mocc/transaction.cc:888-940`)。**2 本とも commit したという
  ことは、少なくとも一方でこの検査が発火しなかったことになる。** MoCC は hot record に
  悲観的 read lock を使い、canonical 順序での施錠のために lock を取り直す経路を持つ。
  この経路と上の検査の相互作用が疑わしいが、**本 wave では確認していない。**
  確認するには CCBench 側の追加計装が要る (段 4 で裁定パッケージへ回した)。
- **(2) について。** trace hook は commit 版を実 store の前に emit する。
  integrity 検査が clean であることはこの分岐の可能性を下げるが、消しはしない。
  integrity は framing と参照整合を見るのであって、「記録された版番号が実際に読まれた版と
  一致するか」を独立に確かめるものではない。

**本 study はこの 3 分岐を分けない。** 分けるのは再現率ではなく、
read-from・write version・commit 順序を独立に束縛する観測である。
