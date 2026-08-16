# [T-1174] numactl 契約 gate — 変異検査と敵対検証の記録

2026-08-16、branch `worktree-dev-wave-t1174-numactl-contract-gate`。

裁定 (2026-08-16 /rulings 全件 第 2 回、択 (d) 新案) は
「実装は判定式の変更にあたるため**変異検査と敵対検証を受入条件とする**」と定めていた。
判定式の実装本体は同日 19:47 に別 wave が `f689d716` として land した。本 wave は
その受入条件を供給し、land 済み実装に無かった防壁と検査層を載せた。

## 置いてあるもの

- `verbatim/s3-consult-sol.md` — 段 3 敵対相談 (レンズ A: 正しさ防壁の緩み)
- `verbatim/s3-consult-luna.md` — 段 3 敵対相談 (レンズ B: 恒真・先取り・帰属不成立)
- `verbatim/s6-review-sol.md` — 段 6 敵対レビュー (レンズ A: 裁定と規律からの逸脱)
- `verbatim/s6-review-luna.md` — 段 6 敵対レビュー (レンズ B: 検査の実効性と変異耐性)

変異台帳の実体は `dev-wave-jobs/wave-t1174-numactl-contract-gate/` の
`mutation-spec-final2.json` と `mutation-final2-ledger.json` (repo 外)。

## 変異 matrix — 13/13 KILLED、共通核と delta

最終形 (`repo_head=f3b858ab`) に対する本走で 13/13 KILLED、baseline PASSED、
SURVIVED / MISMATCH ともに 0。runner は dispatch、範囲は `extra_correctness` に触れる 5 file。

**帰属は共通核を差し引いた delta で行う。** `orchestrator/campaign/pipeline.py` は
`campaign_lock` の enforcement source closure に入るため、1 byte でも変えると
`contract-loader-drift` (disk bytes が記録 commit blob と不一致) で **43 node が変異の意味に
無関係に落ちる**。この核は過剰決定する mask であり、単独変異の証拠にはならない。

| 変異 | delta | 唯一/主たる killer |
|---|---:|---|
| m01 wave 前の述語へ戻す | 4 | 空 prefix 正例・空 list 正規化・契約外 prefix 拒否・不正型 |
| m02 契約比較を反転 | 11 | 正例群 + S2 二本立ての各経路 |
| m03 tuple 正規化を外す | 3 | 空 list 正規化・immutable 配線・S2 lock |
| m04 権威を `env_contract` 引数へ | 11 | 正例群 |
| m05 qualification 除外節を反転 | 3 | 契約外 prefix 拒否・空 prefix 拒否・不正型 |
| m06 fullscale verify 呼出→None | 5 | AST + 動的配線 |
| m07 screening bench 呼出→None | 2 | AST + 動的配線 |
| m08 通常 bench 呼出→None | 2 | AST + 動的配線 |
| m09 `_run_one_pass` の forwarding→None | 4 | **動的配線のみ (AST は生存)** |
| m10 bench の False 分岐→None | 1 | **動的配線のみ** |
| m11 bench の True 分岐→None | 1 | **段 6 fix が足した検査のみ** |
| m12 実 trace 起動の argv から prefix 落とし | 1 | **段 6 fix が足した検査のみ** |
| m13 両層 (gate + 認可検査の numactl 比較) | 3 | 契約外 prefix 拒否・空 prefix 拒否・不正型 |

m09 が AST を生存し動的配線だけに殺されることは、**AST は `evaluate` 内の呼出しか固定できず、
helper の内側で prefix を落とす変異には届かない**という設計上の限界の実測である。
m11 / m12 は段 6 の敵対レビューが指摘するまで核に完全に埋もれていた。

`m01` は「wave 前の実コードの形 (numactl 非空判定) を必ず変異集合に含める」要求を満たす。

## 敵対検証が出した所見の要点

段 3 は親 brief の一般化を限定した。親は probe 3 本から「契約不一致側の純増検出力は 0」と
結論したが、これは「同一 snapshot・有効な current authorization・不変な引数」の下でのみ
成立する限定命題であり、無条件では反証される。

段 6 は must-fix を 4 件出し、**いずれも production ではなく検査側の穴**だった。

1. 空 list `[]` の正規化が未固定 — truthy だけ tuple 化する誤実装が全テストを通過した。
2. bench の `measure_point` 呼出は `record_rep_returncodes` で 2 分岐するが、検査は既定の
   False 側しか通っていなかった。**qualification はこの値を必須にするため実運用側が未被覆**。
   2 レーンが独立に指摘した。
3. 動的検査は trace 実行関数自体を差し替えるので、その内側で prefix を落とす変異が通過した。
4. 「正規化は qualification 検査より後」という受理集合の境界を、どのテストも守っていなかった。

## この記録が保証しないこと

動的配線検査が保証するのは、通常分岐と screening 分岐で fake の API 境界が同一の
immutable tuple object を受け取ったところまでである。実 trace 起動については argv 先頭に
prefix が並ぶことを別途固定したが、**bench 側の各 rep が実際に起動する argv、および
OS 上の実メモリ配置は保証していない**。実機 campaign の再投入は [T-1112] の別 wave である。
