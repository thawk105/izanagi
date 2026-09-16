# 段 1 brief — [T-2622] 計算ノード job が pytest 完了後に終わらない事象の原因同定

## 研究前進

この事象が起きると dispatcher は `overall-timeout` (rc=16) を返し orphan hold を立て、
**8 session が共有する受入・land の経路がその job の walltime (最大 1 時間) 分止まる**
(F901 の実例では約 45 分)。原因が同定できれば次 wave が最小差分で塞げる。
完了判定 = 機序を real / refuted に分けた結論を実測つきで insight に出すこと。原因同定だけで、
機構追加はしない。

## scope

- **入る:** 機序の同定。既存トレース・NQSV 会計・dispatcher のコード読解・計算ノードでの生死実験。
- **出る:** 防壁・機構・gate・回収処理の追加。`_group_member_count` の `Z` 除外
  ([T-2620] がユーザー裁定待ち)。dispatch の受理集合の変更。subreaper (F973)。

## 確定済みユーザー裁定 (依頼本文より)

1. subreaper は採らない (F973)。
2. 計算ノードへの投入は必ず detached 経路から行う。走行中に殺さない。
3. `output/pegasus-dispatch/orphan-holds/` は現在 0 件。dispatch を塞がないこと。
4. 仮想リスク向けの防壁追加は scope 外。原因同定だけ。
5. 規律 2 を緩めない。実装面の著者は Codex `role=author` (D95)。

## 不変条件

- 既存 job を kill しない。`qdel` を使わない。orphan hold を新たに作らない。
- 実験 job は必ず自然終了する設計にする (hang する job を投げない、F901)。
- probe は `tools/pegasus/` 配下に置かない (置くと F660 で同じ wave から起動できない)。
- 絶対 path で機械防壁を迂回しない (F660 の「迂回してはいけない道」)。

## 親の provisional 裁定 — 攻撃対象

- **(P1-a)** 機序は「job の stdout / stderr を掴んだまま生き残った子孫が NQSV request を
  RUN に留める」である。根拠 = F853 の実例 (request 979716、pytest 14.28 秒完了 /
  job は walltime 3609 秒まで) と、submission dir の `dispatch.sh` 最終行が
  dispatcher python を `exec` する構造 (job の最上位 process が dispatcher 自身)。
- **(P1-b)** 容疑者「`_write_result_replace` 後の上限なし `os.fsync`」は **refuted**。
  根拠 = 159 job の実測で file fsync 最大 315.468 ms / dir fsync 最大 1633.431 ms、
  かつ fsync が返らなければ `result.json` が公開されず「pytest は完了している」症状と両立しない。
- **(P1-c)** request を RUN に留める決め手は子孫の**存在**ではなく **job の stdout/stderr
  descriptor の保持**である。F853 の本文はそう読めるが、実験で 2 つを分けていない。
- **(P1-d)** 前 wave の前提「トレースが次の再発時にどの段で止まったかを与える」は**不完全**。
  `job-run-returned` は正常終了時も hang 時も最後の事象になるので、トレース単体では両者を
  分けられない。分けるには NQSV 会計 (`Ended Request Time`) との差が要る。
- **(P1-e)** そもそも**再発が 0 件**なので、痕跡からの同定経路は現時点で行き止まりである。

## 段 1 で実測した事実 (すべて既存成果物の読み取り)

| # | 事実 | 根拠 |
|---|---|---|
| 1 | トレース導入 (`52e8fe7cf`、2026-09-14 07:44 JST) 以降の計算ノード job は 169 本、うち 159 本がトレースを持つ | 全 worktree の `output/pegasus-dispatch/*/izdw-*.e*` |
| 2 | 159 本すべてが `job-run-returned` まで到達。NQSV の `Ended Request Time` との差は最大 0.0 秒 | 同上 |
| 3 | 保存された全期間 338 本に walltime 近くまで走った job は 0 本 (最大 22.7%) | 同上 |
| 4 | file fsync 中央値 19.777 ms / 最大 315.468 ms、dir fsync 中央値 1.716 ms / 最大 1633.431 ms | 同上 |
| 5 | dispatcher は `qstat` の state が `END` になるまで待ち、`result.json` の出現では止まらない | `tools/pegasus/dispatch_compute.py` の待機ループ |
| 6 | job 側 python (dispatcher) に `threading` / `Executor` / `multiprocessing` / `atexit` は 0 件 | 同 file |
| 7 | F973 の実走で subreaper が孫 6 本を実際に回収した | `output/insights/2026-09-14_acceptance-5min-floor/README.md` |

## 既存被覆 (純増だけ書く)

- F853 = 機序の一次記録 + FIFO wrapper 族への局所修復 (D1684)。**族一般化はしていない。**
- F901 = hang 変異が job を walltime まで居座らせた別事例。原因は子自身の hang で本件と別。
- F973 = subreaper による一般対策の撤去。F846 = login node 側の同型 (thread join 待ち)。
- **純増** = (i) 再発 0 件の実測、(ii) fsync 容疑の数値による否定、(iii)「存在 vs fd 保持」の分離。

## 成果物

`output/insights/2026-09-16_t2622-compute-job-exit-hang/` に段 1 実測表・実験設計と生データ・
機序の結論。worklog / decisions / failures は `docs/spool/` の fragment。

## 実測環境

計算ノード (Pegasus, `gen_S`)。投入経路は `tools/pegasus/dispatch_compute.py --task generic`
(main 側 `admission_registry.json` で `class=local-ok`、D895。F660 は 2026-09-14 に supersede
され、`tools/pegasus/` 配下でない probe なら同じ wave で実測できる。先例 = request `997000.nqsv`)。
投入は detached (`nohup setsid` の launcher / detach 2 枚)。

## 変更面 (実アンカー)

| path | 種別 | 誰が書くか |
|---|---|---|
| (新規) `tools/` 配下の非 `tools/pegasus/` probe 1 本 | 実装面 | Codex `role=author` |
| `tools/pegasus/dispatch_compute.py` | 読むだけ・変更しない | — |
| `output/insights/2026-09-16_t2622-.../` | docs | 親 |
| `docs/spool/` fragment | docs | 親 |

## 並列分割

段 2 = plan 1 本 (read-only)。段 3 = 敵対 2 レンズ (機序帰属の当否 / 実験設計が結論を支えるか)。
段 5 = probe 実装 1 本。段 6 = 敵対レビュー 2 本 + 変異 matrix + 受入全走。
