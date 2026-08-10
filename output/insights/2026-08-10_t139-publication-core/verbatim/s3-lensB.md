静的敵対検証の結論は `NO-GO` です。指定ファイルは全て読了し、bytes は変更していません。pytest・build・simulation は実走していません。

以下の `BL-*` は、成果物の受理集合・値・参照へ影響する独立 blocker です。

## 1. 別 study と §14 閉集合

B4(a) の「新 core を別 study とする」形式自体は成立し得ます。しかし、同一の測定・cluster・`J`・`Y_j` を使うことだけでは study 分離の証拠になりません。[段2プランの7条件]( /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-publication-core/s2-plan.md:331 )

1. **条件1: real / BL-1。** source pilot 前凍結は文書宣言だけです。現在 pilot が B8(a) で止まっていても、pilot の外部 submission 時刻と新 core の fold 時刻を検査する gate はありません。pilot 後に文書を作り、事前登録済みと称せます。  
   影響: 公表 p 値・区間の「事前固定」主張と、試行台帳の freeze 参照が無効になります。

2. **条件2: real / BL-2。**「全適格 main cluster を一意固定」と書くだけで、canonical な集合・`Y_j` の全件性・除外不能な dataset identity がありません。結果を見て有利な `J` 個だけを公表解析へ渡せます。  
   影響: `T_k`、Holm 棄却集合、同時下限、材料レポートの6行が変わり、台帳の入力集合参照も変わります。

3. **条件3: refuted（意味上）。** 新 core が primary、`P_W1∧P_W2`、`q`、first-match、失敗分類を変更しないという契約は、直接の primary 変更経路を閉じています。  
   影響: この条件単独では source の certified 選択値は変わりません。ただし consumer 未配線は BL-9 に残ります。

4. **条件4: real / BL-9。**「公表結果を primary へ逆流させない」は文書規則に留まり、consumer が `holm_reject` 等を certified 選択へ渡さない機械的境界がありません。  
   影響: 実装側が public decision を入力にすると、certified 選択の受理集合が primary から公表結果へ変わります。

5. **条件5: real / BL-3。**結果後の変更版 core を同じ root の次 ordinal で出す経路を明記しています。`0.05/(k(k+1))` なら2本目は約 `0.00833` です。これは置換を禁止するだけで、結果を見て分析手続きを選ぶ post-hoc 選択を禁止しません。しかも現 `p01` は ordinal `{1}` だけを許すため、条件5は現 draft とも衝突します。  
   影響: 別 ordinal の p 値・有意セル集合・材料レポートを後選択でき、試行台帳には複数の分析参照が残ります。

6. **条件6: real / BL-8。** `p01`〜`p03` の閉集合を提案しているだけで、既存実装が検査するのは `a01`〜`a13` です。[既存 exact-key 実装]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/orchestrator/preregistration/addendum_envelope.py:13 )  
   影響: p addendum の余剰・欠落・別値が受理集合を拘束せず、spending・root・ordinal の参照が変えられます。

7. **条件7: refuted（形式上）。**新 core を現 core の erratum/addendum として compose しないという境界は正しいです。  
   影響: この条件単独では現 core の bytes は変わりません。ただし raw/composed digest の問題は BL-7 です。

## 2. `main_admission` と追補 B

- **B4(a)との両立: refuted（文書継承ではない限り）。**現 B と新 p 追補が同じ数値を持つこと自体は「値の継承」であり、B4(a)に反しません。文書を相互に親子化しないことが条件です。
- **現 B を新 core に束縛する経路: real / BL-4。**現 B の `core_ref` は現 core です。これを新 core に差し替えると現 core §14 の従属先不一致となり、現 main admission の B ではありません。[現 core の admission]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:8 )
- **現 B を発効するだけで `alpha_pub_1` が適用されるか: real。**現 B 自身が「公表手続きが未確定で適用先がない」と認めています。[追補Bの記述]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:145 )
- **二重束縛: real。**現 B と新 p 追補がともに `(88d68f91…, individual_publication, ordinal=1)` を主張すると、同じ公表台帳の同一 entry を二つの文書が予約します。これは primary/public の意図した2系列ではなく、public/public の重複です。

影響: 現 B を現 core 用、新 p を新 core 用に分けても、現状は source main の admission と公表 procedure の適用先が同時には閉じず、本走・材料レポート・試行台帳を確定できません。

## 3. 公表台帳の根

- **`88d68f91…`をrootにすること自体: refuted（条件付き）。**新 core の fold commit を root にして spending をリセットしない、という意図は正しいです。F は T-139 例外の family root、new core の文書 identity は別、とする整理は可能です。
- **`ledger_kind`による自己申告リセット: real / BL-5。**`ledger_kind` は draft の literal であり、canonical ledger・固定 enum・key→path binding・原子予約の実体がありません。親系列 IDを変えなくても別 `ledger_kind` を名乗れば新しい `k=1` を作れる経路が残ります。[追補Bの自己申告非権威宣言]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:181 )

影響: `alpha_pub` の累積値と有意判定の閾値がリセットされ、材料レポートの有意セル集合と試行台帳の root/ordinal 参照が不正確になります。

## 4. roadmap の限定例外

- **「裁定を求めること自体が抵触の証拠」: refuted。**これは条文の曖昧さを発見した証拠であって、直ちに違反の証拠ではありません。
- **明示裁定なしで凍結できるか: real / BL-6。**roadmap は `[T-139]` の paired measurement 例外と、他 study への一般化禁止を明記しています。[roadmap限定例外]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/docs/roadmap.md:228 )  
  検証済み `Y_j` の下流解析を同じ T-139 study 内の解析と認める裁定なら roadmap 改訂は不要です。別 study による paired data の再利用と判定するなら、roadmap 改訂または別の根拠が必要で、本 wave の scope 外です。

影響: 裁定がない間、新 core の study identity と roadmap 例外の参照が確定せず、材料レポートを「例外条件下の事前登録解析」として受理できません。

## 5. `p` namespace と exact-key

- **現 A envelope に p を混ぜない判断: refuted（安全側）。**A の exact-key は `a01`〜`a13`専用で、p を混ぜれば余剰として拒否される設計です。[A exact-key検査]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/orchestrator/preregistration/addendum_envelope.py:183 )
- **p envelope がないまま凍結できるか: real / BL-8。**p 専用の定数・approved checker・binding caller はなく、テストも A のみです。[Aのみを検査するテスト]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/orchestrator/tests/test_t139_preregistration_binding.py:487 )  
  generic `require_exact_fields` は caller が集合を渡せますが、T-139の p admission は存在しません。

影響: p addendum の受理集合、p core への従属、spending/root/ordinal の参照が未拘束になります。

## 6. seed と digest

**real / BL-7** です。seed は raw core digest `ac939af4…` を含みますが、既存 erratum を適用した composed digest は `d1782b04…` と別物です。[raw/composed digest の固定テスト]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/orchestrator/tests/test_t139_preregistration_binding.py:502 )

raw core を seed に使うことは自己参照を避けますが、effective core の identity を表しません。将来 §7 の第2 erratum が発行されれば、同じ seed が異なる有効規則に再利用されます。現在の erratum も seed preimage に含まれていません。

影響: stress check の pass/fail、`J` の `design_not_feasible` 判定、main admission、後続の公表表が異なる有効 core で同じ seed を参照できます。

## 7. producer → validator → consumer

プランは役割名を列挙していますが、成果物を出すための実効契約は未接続です。core 自身も機械配線を次 wave に委ねています。[core §15]( /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:366 )

| 層 | 公表表が出るために必要な処理 | 静的確認 |
|---|---|---|
| producer / receipt | source core・A・B、新 core・p、dataset、全 attempt、raw pointer を記録 | T-139 producer なし |
| source validator | raw receipt から cluster、`J`、`Y_j`、`qualification_status` を再計算 | その値の生成元なし |
| publication validator | `T_k`、未調整 p、Holm、Bonferroni 下限、6セル固定表を再計算 | API・gateなし |
| consumer / renderer | source validator を再実行し、6行を省略せず、public decision を certified 選択へ逆流させない | consumer bindingなし |
| publication ledger | canonical root、create-only ordinal、spending、core/p参照を予約・照合 | ledger実体なし |

`qualification_status` は「source validator が確定した値を逐語複写」する規定ですが、複写元が存在しないため発火しません。

**real / BL-9。** これは単なる未実装ではなく、文書だけでは certified 選択・材料レポート・試行台帳の信頼境界を閉じられない scope 外の裁定パッケージ候補です。

影響: `qualification_status` が権威値にならず、公表表は生成不能または自己申告になります。結果として材料レポートと試行台帳を受理できず、certified 選択も public study からは出せません。

## Nit

- R4 probe の最大 `0.0791` や `TRACE=1` stock witness は、文書自身が単一 node・単一 allocation の記述結果であり、全割当てへの一般化を主張していません。この限定を守る限り、今回の blocker ではありません。実測自体は再実走していません。
- `T_k` の数式を A と同じにすることは、new core が式を独立に規範化し、A を権威文書として継承しない限り B4(a) と両立します。

## 総括

**NO-GO — blocker 9件。**

主因は、①時点・dataset・ordinal の三面で post-hoc 解析を完全には閉じていない、②現 B と新 p の二重束縛を解消していない、③`ledger_kind` と p namespace の機械的拘束がない、④effective core digest が seed に反映されない、⑤producer・validator・consumer・ledger・`qualification_status` の全層が未接続、の5群です。