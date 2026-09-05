# [T-2103] 段 6 裁定追補 2 — 201 は設計の下限である。縮小でなく分割で解く

追補 1 (`s6-ruling-addendum.md`) の §D1「最小 block 数」を**撤回**する。他の条項は不変である。

## A. 親の実測 (3 shard、2026-09-03 15:15-15:18 JST)

3 候補の shard を並列実行した。3 本とも rc=1 で、`comparison.json` は合成されなかった。
**harness は正しく fail-closed した。** 成果物 (`/work/1/SFC/tanab/t2103-scratch/shards/*.json`)
を親が読んだ結果は次のとおり。

- 非後退走は 3 候補とも `passed: true` (`producer_node_count: 29`)。所要は 28.7 - 29.6 秒。
  **候補が有効な状態でも既存 29 node は緑である。**
- 一方、**39 組すべてで baseline が
  `{"existing_gate_rejected": true, "guard_rejected": false, "reason": "evaluator:analysis_invalid"}`**
  であった。変異を当てていない baseline すら有効な分析に到達していない。
- 結果として全 case が `observed: "BASELINE_REJECTED"` となり、
  `incremental_kill` は 39 組すべて `false`。**測定値が 1 つも得られていない。**

## B. 原因 — 201 は縮められない下限である

`orchestrator/campaign/p3_b4_analysis_ledgers.py:1158` が次を投げる。

```
design_not_feasible: fewer than 201 eligible registry rows
```

事前登録された B-4 設計は 201 attempt を要求する。201 未満の publication は
`assert_analysis_manifest_complete` で構造的に無効になり、evaluator は必ず
`analysis_invalid` を返す。**1 block では、どの候補でも、いかなる変異でも、
有効な分析に到達しない。** 追補 1 の §D1 はこの下限を見落としていた。親の誤りである。

これは絶対規律 4 が言う「小さすぎると測定が歪む」側の罠そのものである。

## C. 併せて是正する非対称性

fix 第 2 巡は frozen の prototype 経路でだけ「使い捨て process 内で evaluator の期待 block 数を
1 に設定」していた。baseline にはこの緩和が無い。**baseline と prototype は guard の有無以外
すべて同一条件でなければ、測った差が guard に帰属しない。** この緩和は全廃する。

## D. 確定する設計変更

### D5. 全 case・両 phase を 201 block で測る

事前登録された設計スケール (201) を使う。1 block 経路と evaluator 期待 block 数の緩和を
コードから削除する。baseline と prototype は guard の有無だけが異なる。

### D6. 実行時間は分割で解く

`measure-candidate` に `--phase {baseline,prototype}` を足し、
**候補 x phase の 6 shard** に割る。1 shard あたり 13 phase である。
`combine` は 6 shard を受け取り、39 組の完全性を従来どおり検査する。

分割しても 3600 秒に収まらないなら、さらに変異族 (C0 / C1 / R / D / POS) で割れるようにする。
**1 ノード直列で全部を流す形へ戻さない。**

### D7. fixture が有効な分析に到達したことを実測で示す

POS-1 の **baseline** が `accepted` (`existing_gate_rejected: false` かつ
`guard_rejected: false`) であることを要求する。そうでなければ fail-closed で止め、
観測した reason を報告する。これが「fixture が経路を発火させた」ことの唯一の証拠である。
到達しないまま KILLED / SURVIVED を数えない。

### D8. phase ごとの所要を記録する

shard JSON に phase ごとの wall 時間を記録する。次の分割を勘でなく実測で決めるためである。

## E. 変わらないもの

段 4 裁定 §2.1 - §2.12、追補 1 の §D2 (実 regime の正例)・§D3 (測定と gate の分離)・
§D4 (分割実行)、変異事前登録 W01-W09、期待 matrix、採否規則。**結果を見てから変えない。**
規律 2 を緩めない。
