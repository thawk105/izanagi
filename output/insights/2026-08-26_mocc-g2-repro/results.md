# 結果 — MoCC TRACE=1 の G2 再現率 study ([T-1892])

**G2 は再現した。** 42 本中 5 本が non-serializable で、5 件すべてが G2 だった。

- 事前登録: `output/insights/2026-08-26_mocc-g2-repro/pre-registration.md`
  (凍結 commit `f7f6dd2e70ccb27f531011881e47c45617d3ffaf`、
  sha256 `182abe5cdad001d8ec799bbf33d097674ad7292cd8e5880826ca56654dd6e235`)
- 段 4 裁定: 同 directory の `s4-adjudication.md`
- 機械台帳: 同 directory の `ledger.json` (`orchestrator/campaign/mocc_g2_repro_ledger.py` が生成)
- 証拠: 同 directory の `runs/<ordinal>/`、`submissions/<nonce>/`、`submission-ledger.tsv`
- anomaly の構造化投影: 同 directory の `anomaly-projection.md`
- 生 trace を含む job-staging (12 GB) は repo 外
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-g2-repro-20260826/evidence/` へ退避した

## この結果の射程 — 先に限界を書く

- **`official_certification=false` である。headline・certified な選択・floor・oracle・fitness の
  根拠に使わない。**
- **この study は原因を確定しない。** 「MoCC 実装の性質」「trace hook の記録の取り違え」
  「verifier の版順序仮定の不成立」のどれであるかは、再現率では分けられない。
- **provenance は機械 gate ではなく、次の 2 つに依っている。**
  - **artifact が支える事実:** submitter の clean-tree gate
    (`tools/pegasus/submit_mocc_trace.sh` の投入前検査) が 42 回すべての投入で実際に走っており、
    各 `submissions/<nonce>/submit-receipt.json` が `source_commit` を記録している。
    42 件すべての `source_commit` は凍結 commit と一致する。
  - **artifact が支えない申告:** 「各 batch の前後で HEAD と clean を確認した」という親の運用は、
    台帳 TSV に `head` 列しか無く **clean 列が無い**ため、記録として残っていない。
    これは親の未収録の運用申告であって、証拠ではない。
- **job 側の source 検査は開始時 1 回だけで、判定後の再検査は無い。**
  **これを「TOCTOU を塞いだ」とは書かない。**
- pair receipt の `prohibited_uses` は宣言であって強制ではない。それを必須入力として読む consumer は
  repo 内に存在せず、下流利用を機械的に止めるものは無い ([T-1893] は裁定待ち)。

## 一次結果

| 量 | 値 |
|---|---|
| N (request ID が発行された run) | 42 |
| m (verdict が確定した run) | **42** (除外ゼロ) |
| k (G2 を 1 件以上出した run) | **5** |
| `k/m` (条件付き `p_det`、一次報告値) | **0.11904761904761904** |
| Clopper-Pearson 両側 95% | **[0.039806, 0.256317]** |
| `k/N` (欠測を全部 non-G2 とした下限) | 0.11904761904761904 |
| 識別区間 `[k/N, (k+欠測)/N]` | [0.119047…, 0.119047…] (欠測 0 のため縮退) |
| 実効検出力 `1 - 0.9^42` | **0.988027484817438** |

**除外は 1 本も無かった。** 42 本すべてが verifier の verdict を出したので、
段 3 が指摘した informative missingness の懸念は、この走行に関しては空振りである
(規則自体は事前に凍結してあり、今後の走行でも同じ規則を使う)。

判定文は事前登録の `k >= 1` の側をそのまま使う。

> 固定した MoCC TRACE=1 / trace hook / verifier の組で G2 signal を再現した。
> 条件付き再現率は 5/42、95% CI は [0.0398, 0.2563]、下限側の無条件率は 5/42 である。

前 wave の観測 (3 本中 1 本) はこの区間と矛盾しない。

## 全 42 本の分類

| 分類 | 件数 | ordinal |
|---|---|---|
| certified (serializable) | 37 | 上記 5 本を除く全部 |
| non-serializable (G2) | 5 | 19, 24, 30, 31, 32 |
| indeterminate | 0 | — |
| verifier インフラ失敗 | 0 | — |
| その他の stage 失敗 | 0 | — |

**輻輳 fallback は発火しなかった** (`third_party` / `source_materialization` / `allocation` /
`glog` / `gflags` の失敗が 0 件だったので、7 batch とも 6 本ずつ投入した)。

## 並行度 — 事前登録の記述と実測の差

**事前登録は「並行度 6」を estimand の一部として固定したが、それが固定したのは
投入時の扇出であって実行時の同時実行数ではなかった。** 実測すると次のとおりである
(`runs/<ordinal>/reservation.json` の `scheduler_started_epoch` と
`job-result.json` / `failure.json` の完了時刻から算出)。

| batch | 投入本数 | 実測 peak 同時実行数 | batch の span (秒) | k |
|---|---|---|---|---|
| 1 | 6 | 5 | 214 | 0 |
| 2 | 6 | 3 | 514 | 0 |
| 3 | 6 | **6** | 102 | 0 |
| 4 | 6 | 4 | 198 | 2 |
| 5 | 6 | 5 | 370 | 1 |
| 6 | 6 | **2** | 689 | 2 |
| 7 | 6 | 5 | 348 | 0 |

**全 42 本を通じた peak 同時実行数は 6 である。**
**anomaly は高並行に偏っていない** — peak 2 の batch 6 で 2 件、peak 6 の batch 3 で 0 件である。
**これは記述であって、並行度と anomaly の関係についての推論ではない**
(標本が疎で、そのような推論を支える設計になっていない)。

## 副次解析 (a) — anomaly の構造 (本 study の 5 件)

| ordinal | request | host | txns | cycle | 2 trx の thid | commit version |
|---|---|---|---|---|---|---|
| 19 | `950401.nqsv` | bnode008 | 745,328 | [691105, 691107] | 46 / 39 | (69,4358) / (69,4359) |
| 24 | `950408.nqsv` | bnode036 | 764,160 | [319459, 319460] | 13 / 28 | (32,3988) / (32,3989) |
| 30 | `950424.nqsv` | bnode061 | 782,296 | [501707, 501708] | 17 / 31 | (49,591) / (49,592) |
| 31 | `950437.nqsv` | bnode064 | 753,208 | [27629, 27630] | 29 / 15 | (4,839) / (4,840) |
| 32 | `950438.nqsv` | bnode023 | 564,251 | [181195, 181196] | 13 / 21 | (19,309) / (19,310) |

**5 件すべてが次の形を取る。**

- `total_cycles` は全件 1、`phenomenon` は全件 G2、cycle 長は全件 2。
- cycle の全辺が `rw` (anti-dependency) である。
- **2 つの transaction の thid は全件で異なる。**
- **2 つの commit version は全件で同一 epoch、`tid` の差は 1 である。**
- 前向き辺の key は `0x1` / `0x2` / `0x6`、後ろ向き辺の key は `0x0` が 3 件、`0xb` と `0x49` が各 1 件。
  workload は zipf skew 0.9 なので小さい key ほど高頻度に触られる。
- ordinal 32 だけ前向き辺の理由が 2 本 (key `0x2` と `0x55`) ある。

edge・key・version の逐語は `runs/<ordinal>/verifier.json`、thid と trace 原本の SHA-256 は
`anomaly-projection.md` にある。

**報告される witness は 1 run あたり最大 20 本である** (`orchestrator/verifier/cli.py` の
`--max-report` 既定 20、job は上書きしない)。本 study では全件 `total_cycles` が 1 なので、
打ち切りは起きていない。

**前 wave の `949964.nqsv` の 1 件は本 study の N・m・k にも副次解析にも入らない。**
既知資料として `pilot-anomaly-projection.md` に投影してあり、同じ形 (thid 40 / 21、
commit version (53,2868) / (53,2869)) をしている。**参考であって本 study の結果ではない。**

## 副次解析 (b) — integrity

**5 件すべてで integrity は clean である** (orphan_reads、version_dups、dup_txids、
missing_txids、write_version_mismatch、malformed_keys、framing_violations、
lock_coverage_violations、write_intent_violations、permutation_violations がすべて 0)。

## 副次解析 (c) — cycle 内 transaction の関係

上表のとおり、thid は全件で異なり、commit の `(epoch, tid)` は全件で差 1、
txid は 4 件で差 1、ordinal 19 だけ差 2 である。

## 副次解析 (d) — G2 以外

G0 / G1c だけの run は 0 件、indeterminate は 0 件である。

## 副次解析 (e) — batch 別・host 別

batch 別は上の並行度の表に併記した。host は 25 種に散り、
**anomaly を出した 5 本は 5 つの異なる host に 1 件ずつである** (bnode008 / 023 / 036 / 061 / 064)。
**host 効果は標本が疎で評価できない** — host ごとの曝露数が不均一で
(bnode061 と bnode064 は m=1 で k=1、bnode023 は m=5 で k=1)、
「host に依らない」と読んではならない。言えるのは**同一 host での反復が無かった**ことだけである。

## この結果が原因の 3 分岐に対して意味すること

**確定しない。** 事前登録は因果推論を禁じているので、ここでは**観測の記述と、
今後の観測で分けるために要るもの**だけを書く。

- 観測された構造は上のとおり均質である (5/5 で長さ 2・両辺 rw・別スレッド・同一 epoch・
  tid の差 1・integrity clean)。**この均質性から原因を推論しない。**
- **verifier の版順序仮定 (分岐 3) について。** 仮定は「同一 key 上で `(epoch,tid)` の
  辞書式順序が版の全順序」である (`orchestrator/verifier/model.py`)。
  MoCC の commit TID は read/write set の最大 +1、**同 worker の直前 TID (`mrctid_`) +1**、
  local epoch の最大で決まり (`external/ccbench` の `cc/mocc/transaction.cc:1018-1034`)、
  write set は施錠後に最大版を取る (`:896-908`)。**同一 key の後続 writer は直前版より
  大きい tid を持つ**ので、per-key の全順序という仮定はこの範囲では支持される。
  なお `(epoch,tid)` は**非競合 transaction 間では大域一意ではない**
  (`include/trace.hh` が明記)。verifier は `(key, version)` を producer の鍵にするため、
  この重複自体は問題にならない。
- **分岐 1 (MoCC の性質) と分岐 2 (hook の取り違え) を分けるには、
  read-from・write version・commit 順序を独立に束縛する観測が要る。**
  同じ trace を同じ verifier で再検査しても分けられない。これは CCBench 側の追加計装を伴うので、
  段 4 で別 wave の裁定パッケージへ回した。

**この anomaly を理由に verifier を緩めていない (規律 2)。** 5 本とも job は rc=1 で
fail-closed し、throughput を生成していない。verifier の受理集合は本 wave で 1 文字も変えていない
(`git diff main...HEAD -- orchestrator/verifier/` が空であることを親が実測した)。

## CCBench 側への扱い

これは第三者 submodule の実装に関する所見でありうる。`CLAUDE.md` の作業の進め方 4 に従い、
**上流 PR / push の判断は人間に委ねる。** 本 wave では insight として構造化して残すだけとする。
