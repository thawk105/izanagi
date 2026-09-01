---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2127-empty-commit-loop
seq: 2
---

## {{D:certified-view-universal-vs-existential}}. certified view の全称保証と存在保証を別の名前へ分ける

**決定:** `CertifiedCampaignView` は「存在する全 commit の証拠が妥当」という全称保証だけを表し、
commit の存在は保証しない。存在保証は `require_certified_commit_evidence` だけが与える。
commit 走査は共通入口 1 本へ寄せ、検査を通した件数を view の必須 field として持たせる。
非ゼロ要求を配線するのは、commit 由来の主張を作る consumer に限る。

**理由:** 全称命題は commit 0 件でも真であり、空走そのものは欠陥ではない。欠陥は、
その全称保証を存在保証として読む consumer 契約の曖昧さにある。admission 層で
commit 0 件を一律拒否すると、全試行 abort の campaign の棄却を報告する正当な経路を壊し、
failure campaign が拒否されることに依存する負例側の制御を恒真化する。

**却下した選択肢:**
- admission で commit 1 件以上を必須にする — 棄却報告の経路を壊し、負例制御を恒真化する。
- 各 consumer が件数を再導出する — 取り残しを再発できる (D1246 が既に却下した形)。
- 件数 field を検証の証拠として扱う — 件数は records から導出でき、検査通過を証明しない。

## {{D:nonzero-wiring-needs-counterfactual}}. 存在保証の配線は反実仮想を満たす箇所にだけ足す

**決定:** 存在保証の要求を consumer へ足すのは、「その要求を置かなくても別の層が同じ入力で
先に赤を出す」ことが成り立たない箇所に限る。先に赤を出す箇所へは足さない。

**理由:** 先行する述語から含意される要求は、置いても発火せず、その要求だけが殺す変異を作れない。
足りる既存策があるのに防壁を増やすと、変異事前登録の単一理由性が崩れ、
「謳うだけで発火しない検査」が増える。

**却下した選択肢:**
- 名前が似た consumer へ一律に配線する — 恒真な検査を増やし、変異の証拠能力を下げる。
- 呼び手ごとに配線する — 名前検索に現れない間接 consumer を取りこぼす。共有入口へ置く。
