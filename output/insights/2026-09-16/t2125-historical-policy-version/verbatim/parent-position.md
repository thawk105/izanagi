# [T-2125] 親の追加実測と、段 4 へ持ち込む立場

`measured-facts.md` の続き。**ここも検査対象である。**

## M10. 「読めるようにする」が certified への昇格になる実経路がある

`orchestrator/campaign/layer3_report.py:279` と同 `:959`、および
`orchestrator/campaign/autonomous_trial_completeness.py:4798` は、いずれも

```
    admission_decision.get("admission_status") != "admitted"
```

を見て `certifying_input=true` を拒否している (D259 決定 8)。
`CampaignAdmissionDecision.as_receipt()` (`artifact_admission.py:314-323`) が
`admission_status` をそのまま receipt へ載せるので、**この値は下流の認証判定へ届く。**

一方 `CampaignAdmissionDecision.admitted` は
`artifact_admission.py:311-312` で `self.admission_status != "legacy-unclassified"` と定義されている。
つまり **「歴史閲覧としては通るが、認証の入力にはならない」中間状態が既に存在する** —
v1 の `historical-pre-admission-schema` / `historical-not-reclassified` がまさにそれである
(`artifact_admission.py:1344-1348`)。

**したがって規律 2 の観点では、policy の版が古い v2 campaign を
`classification="admitted-new-schema"` / `admission_status="admitted"` のまま返してはならない。**
返すと、certifying input の条件を満たしてしまう。

## 親が段 4 へ持ち込む立場 (P1 の改訂案・攻撃対象)

上の M10 と、[T-2125] が要求する「`current-closure-unavailable` とは別の識別子」は、
**同じ 1 つの機構で満たせる**と親は考えている。

- `purpose is HISTORICAL_RAW` かつ「記録 policy ≠ 現行 policy」のときだけ、
  **専用の `classification` と専用の `admission_status`** を返す
  (v1 の `historical-pre-admission-schema` / `historical-not-reclassified` と同型の中間状態)。
- その `admission_status` は `"admitted"` ではないので、layer3 と
  autonomous_trial_completeness の certifying gate を**構造的に**通らない。
  恒真ラベルではなく、既存の consumer がその値を実際に見て拒否する。
- `admission_status != "legacy-unclassified"` なので `admitted` property は真になり、
  歴史 view としては読める。
- `HistoricalCampaignView.current_verifier_conformance` は既に exact `"unknown"` を返す (D1365)。

**この立場を両側から攻めよ。**

- 反対側 1: M7 の先例 (`s8b_binary_admission.validate_portable_binary_record` の
  `expected_policy=None` = 歴史再検証では照合そのものを外す、artifact 内 policy を期待値へ流用しない)
  と、この立場は整合するか。記録 policy を `_validate_attempt_topology` へ渡すことは
  「artifact 内 policy を期待値へ流用する」に当たらないか。
- 反対側 2: 新しい `classification` / `admission_status` の literal を足すと、
  `EXPECTED_CAMPAIGN_CLASSIFICATIONS` のような exact 期待値表や、値域を固定している
  schema・test が赤くなる。その閉包を全部挙げられるか。
- 反対側 3: 専用 status を足しても、`as_receipt()` を読まずに `decision.admitted` だけを見る
  consumer が居れば昇格経路は残る。**`admitted` property の呼び手を全部列挙して確かめよ。**
