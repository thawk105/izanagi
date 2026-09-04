# [T-2103] 段 6 裁定追補 3 — floor 不在という定数を「拒否」と数えない

追補 2 の §D5-D8 は有効である。本追補は観測境界だけを是正する。

本巡は `DW-O16` の 3 巡上限には数えない。上限は「所見が閉じない場合」の制限であり、
本件は**親が実機で特定した blocker** (同節の「親の実機 blocker は別枠」) である。
fix 第 1-3 巡はいずれも指示どおり所見を閉じており、閉じ損ねによる巡ではない。

## A. 親が特定した blocker (実測)

6 shard (候補 x phase、201 block) を並列実行した。6 本とも rc=1 で合成は行われなかった。
**harness の fail-closed は正しく働いた。** shard log の内容は次のとおり。

```
POS-1 baseline did not reach accepted: candidate=issuer reason='evaluator:analysis_invalid'
phase route mismatch: candidate=issuer phase=baseline mutation=C0-P reason='evaluator:analysis_invalid'
... (以下 C0/C1/D 系すべて同一理由)
```

原因は block 数ではない。**production 経路は設計上、有効な分析に到達しない。**

- `orchestrator/campaign/p3_b4_material_report.py:225` は `evaluate_b4_artifacts` へ
  `floor=None` を渡す。
- `orchestrator/campaign/p3_b4_analysis_contract.py:323-325` は
  `as_b4_exact_fraction(floor)` が `None` のとき `FLOOR_DOMAIN_ERROR` を立てる。
- これは事故ではなく既知の設計である。同 module の docstring (`p3_b4_material_report.py:6`)
  が「`floor=None` を凍結 evaluator へ渡し、結果の protocol violation を報告する」と書き、
  同 file は `"floor_availability": "absent"`、
  `"expected_analysis_reason": "floor_domain_error"`、
  `"authoritative_floor_artifact"` を報告 field に持つ。権威ある floor 成果物が未発行だからである。

一方、**受理へ到達する経路は実在する。** `orchestrator/tests/test_p3_b4_raw_record_producer.py:1600`
付近の 201-block 正例は `evaluate_b4_artifacts(floor=0, ...)` を渡し、
`assert result.analysis_invalid is None` が通っている。差は floor だけである。

## B. 判定 — floor 不在は「rogue producer の拒否」ではない

`floor_domain_error` は次の性質を持つ。

- 全 78 phase で発火する。変異にも候補にも phase にも依存しない**定数**である。
- POS-1 (正当な publication) でも発火する。
- rogue producer の有無と無関係である。

**すべての入力で同じ値を返す観測は、拒否能力の情報を 1 bit も持たない。**
これを `existing_gate_rejected` と数えると、全 case が `BASELINE_REJECTED` になり、
測定が構造的に不可能になる。実際そうなった。

## C. 確定する是正

### D9. 測定は floor を供給する

測定の evaluator 呼び出しは、既存の 201-block 正例と同じく **`floor=0`** を渡す。
これにより accept / reject の区別が観測可能になる。他の経路要素は実 production のまま変えない。

**非保証として必ず書く:** 本測定は production 経路が現時点で渡していない floor を供給している。
production は権威ある floor 成果物が未発行のため `floor=None` を渡し、
`floor_domain_error` を返す。したがって本測定の frozen 候補の値は
「floor が供給された場合の拒否能力」であり、現行 production の挙動ではない。

### D10. floor 不在を rogue 拒否と分類しない

万一 `floor_domain_error` が観測された場合、それを `existing_gate_rejected` として
候補の分母へ入れない。`ENVIRONMENT_CONSTANT` など専用の分類で記録し、
その case を KILLED にも SURVIVED にも数えず、理由を報告する。

### D11. D7 の正例条件は維持する

POS-1 の baseline が `accepted` に到達することを引き続き要求する。
D9 を入れれば到達するはずである。到達しなければ観測した reason を報告して止まる。
**到達しないまま数字を出さない。**

## D. この blocker 自体が本 wave の成果である

「凍結 closure 外の producer をどの層が認証するか」を実 production 経路で測ろうとした結果、
**その production 経路が現時点でいかなる入力に対しても有効な分析を返さない**ことが実測で判明した。
これは D1530 が言う「production caller が存在せず、未接続の interface」と同型の事実である。
insight と decision fragment に必ず記録する。

## E. 変わらないもの

段 4 裁定 §2.1-§2.12、追補 1 の §D2-D4、追補 2 の §D5-D8、変異事前登録 W01-W09、
期待 matrix、採否規則。**結果を見てから変えない。** 規律 2 を緩めない。
