# [T-142] 出力集合 O への S2 promotion — 実装 preflight の新事実と再裁定 package (2026-07-29)

## 結論

2026-07-29 (54) で承認された択 (a) は、実装 preflight で未見の blocker が判明したため、
本 wave では実装しない。採用を AI が取り消すのではなく、追加情報を添えて再裁定へ返す。
plan・敵対相談・親裁定の逐語は
`output/insights/2026-07-29_t142-output-promotion-verbatim/`。

## 新事実

1. 現 sort/trigger は `reps=2`。現行 Mann–Whitney 実装では完全分離した n=2 対 n=2 も
   `p=0.1939308523` で `no-difference` となり、安全案の唯一の省略枝
   `slower && !near_floor` は到達不能。既存 target 3 候補は全件 S2 済みで、反実仮想 skip は 0/3。
2. 現動作点 (linux-baremetal・100k records・4 threads・extime=1・reps=2) と全座標が一致する
   between-run floor は存在しない。最寄りの既存 floor は 1m・48 threads・extime=3・reps=5。
3. 旧 88% は全 numeric COMMIT 426 件中の raw new-best 比率であり、S2 実走集合ではない。
   再集計は S2 済み numeric COMMIT 78、campaign 内 raw new-best 18、raw skip 上限 60/78 = 76.9%。
   tie/near-floor/unstable を加味した安全案の期待値ではなく、target では 0%。
4. 現 p3 に formal selected/stock/tie producer と同一 config の certified stock がない。
   tie も direct-winner 比較と no-difference 推移閉包の二つが現存し、どちらを O とするか未裁定。

## なぜ実装を止めるか

- floor 不在は安全側に全件 S2 となるため短縮ゼロ。
- floor を追加しても `reps=2` では comparator の skip 分岐が発火しない。
- formal selector がないため、all-S2 と adaptive の selected/stock/tie 一致を機械検査できない。
- この状態で attempt FSM、第三 terminal stage、schema v3、全 consumer 改修を先行すると、
  発火実績のない大型機構になり DW-G01/G04 と規律5に反する。

## 再裁定が必要な択

### (a) T-142 を close する — 親推奨

「現 production 経路では安全な省略枝が到達不能で、O 自体の producer も未実装」を理由に
コード変更なしで閉じる。将来 formal selector と live campaign が揃った時は新タスクとして再起票する。

### (b) 前提 wave を承認する

次を T-142 実装より先に行う。

1. O の tie 規則を direct-winner / 推移閉包から裁定し、authoritative selector と certified stock を実装。
2. live campaign、正式 perf config、到達可能な reps/比較規則を裁定。
3. 同一座標の between-run calibration を取得。
4. 同じ候補列で all-S2 / adaptive paired pilot を行い、自然な skip 1 件以上、正の wall-time 削減、
   selected/tie/proof refs 一致を確認。

推移閉包 tie を維持する、live campaign を指定しない、または pilot で skip が出なければ close する。

## 本 wave の射程

コード・テスト変更なし。したがって mutation matrix と受入全走は対象外。
親の前提テストは変更前 baseline 325 passed / 9 skipped であり、実装受入や効果の証拠には数えない。
