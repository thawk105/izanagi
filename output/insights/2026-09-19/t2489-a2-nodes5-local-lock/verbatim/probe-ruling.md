# 実測後の局所lock採否と段6裁定

- 2026-09-19、request9137.nqsv、bnode082/bnode083の2node・1予約で実bench_lockを測定。
- rank0/1ともstatus=complete、failure記録なし。rank0結果の4caseは以下。会計/最終job終了確認は親が別途行う。

| 保持→挑戦 | 同node | 別node | 解放後 |
|---|---|---|---|
| candidate→candidate | busy | acquired | acquired |
| default→default | busy | busy | acquired |
| candidate→default | acquired | 未対象 | acquired |
| default→candidate | acquired | 未対象 | acquired |

- **候補不採用。** A2/A6 head間のnode-local独立は成立したが、既存default consumerとの同node協調排他を両方向で失う。規律2/測定排他の維持に従い、この局所exportを恒久採用しない。
- 追加gate、global lock変更、他launcher/worker改修、二重lock、総timeout追加へ広げない。scheduler.nodes=5とpolicy pin/fixture閉包は採用済みのまま進める。
- 過去attemptの待ち時間の全帰属・速度改善・論文採用値をこの結果から主張しない。実job body継承はmock harnessで4case緑、computeは実source assignment由来pathの実flockであり証拠は別。
- review Aは新must0、review Bのmust（候補exportを出荷しない）はrealで上記撤回により閉じる。B should（片側doneで採用しない）はreal。両rank終了と会計を確認する。新しい実装修正の指摘はなし。
- final化は同じCodex単位へ依頼する。対象はjob bodyと同testの候補専用harness/testが同一依存であり、素集合に割る利点がない。
- 既存candidate patch、probe2file、固定commit c5bfe9e8249634236ac267e4114044433a64490c、観測JSONを保全する。候補専用testの除去は緑化目的でなく、未出荷機能の試作撤去。既存testの弱化/除去は禁止。
