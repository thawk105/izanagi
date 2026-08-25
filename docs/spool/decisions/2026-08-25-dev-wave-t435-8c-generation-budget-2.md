---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t435-8c-generation-budget
seq: 2
---

## {{D:s8c-generation-budget-reprereg}}. 段 8c 事前登録の世代予算条項は宣言 budget の束縛として改訂し、条件 11 の証拠要求は広げない

**背景:** 段 8c 事前登録文書 (`docs/phase3-8c-preregistration.md`) の §6 条件 11 は、
「これらの機構が強制するのは承認**上限**であって世代の下限ではない — 各 cell を正確に `G=2` で
起動することは §4 と §7 が定める起動形の責務である」と書いている。D443 (2026-08-16) 以降この記述は
古い。証拠契約 `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` の条件 11
`consumer_requirement.proof` と `docs/phase3-s8c-autonomous-trial-runbook.md` にも同じ主張がある。
2026-08-25 の /rulings 全件で、凍結・再事前登録の手続きに従って改訂すること、
変更単位を世代予算条項のみに限ることが確定した。本決定はその裁定を canonical 台帳へ記録し、
改訂の内容を確定するものである。

**決定 (1): 改訂の変更単位は、同型の主張を現在形で述べている 6 locus と、その生成閉包とする。**
`docs/phase3-8c-preregistration.md` の §6 条件 11 本体と §6「衝突 (b)」の「残る欠落」段、
証拠契約の条件 11 `proof`、`docs/phase3-s8c-autonomous-trial-runbook.md` の 3 箇所である。
生成閉包として、証拠契約の意味 hash を literal で pin する
`orchestrator/tests/test_s8c_preregistration_core.py` の
`test_current_evidence_contract_hash_is_frozen` と
`test_evidence_contract_hash_accepts_non_path_controls` の 3 parametrize を同じ変更単位で更新する。
歴史記録 (`docs/phase3.md` の当時の経緯、D438 本文、archive worklog) と
凍結 snapshot (`output/insights/` 配下) は改訂しない。

**決定 (2): 改訂文が主張してよいのは、manifest を伴う registered 起動における
「宣言される generation budget が整数 2 に束縛されること」だけとする。**
D443 決定 (1) が manifest schema で各 trial の `generations` を整数 2 に限り、
決定 (3) が registered 起動で runtime 引数と manifest 宣言値の不一致を campaign identity 導出・
run root 作成より前に拒否し、決定 (2) が受入で 6 report 全件の
`generation_budget_per_workload` と manifest 宣言値の不一致を拒否する。
**次の 2 つの限界を同じ文で明示する。** (a) 束縛されるのは宣言 budget であって実際の完遂世代数では
ない — crash・supervisor-error・early-stop で 2 世代に届かなかった cell は D443 決定 (4) により
partial として記録し拒否しない。(b) manifest を伴わない unregistered exploratory 経路には
この束縛が及ばない。限界を落とした「exact G=2 は機械強制されている」という無限定の文を書かない。

**決定 (3): 条件 11 の `required_evidence`・`consumer_requirement.path`・評価器・負の対照は
変えない。したがって受理集合は変わらず、`DECIDER_VERSION` は bump しない。**
条件 11 の証拠要求は supervisor と第二層射影の 2 種であり、決定 (2) が挙げる 3 機構は
`orchestrator/campaign/trial_registry.py` 側にあって評価器の検査対象ではない。
**改訂した `proof` には、これらの機構が条件 11 の評価器の検査対象ではないことを明記する。**
明記しない `proof` は、束縛されていない事実を充足根拠へ昇格させる。
同じ理由で、これらの機構は現在いかなる変異にも保護されていない。

**決定 (4): 「承認上限と閉じた還流を強制する」のような、還流の保証格を言い換える文言を書かない。**
同文書 §4 は「上の閉包はキー集合の閉包であって情報量の遮断ではない」と自ら記録しており、
言い換えは自己矛盾になる。現行の「世代間で運ぶものを固定 key 集合へ閉じる第二層射影」を維持する。

**決定 (5): 本決定を記録する wave と、条件契約の改訂を land する wave を分ける (D439 形 2)。**
本決定が着地した後の後続 wave が、決定 (1) の 6 locus と生成閉包、および
`output/s8c-preregistration/condition-freeze/condition-freeze.v1.g11.json` を
**同一 commit** で land する。g11 の `ruling_reference` は本決定を引く。

**理由:**

- D439 は、世代記録が引く決定見出しが記録導入 commit の時点で `docs/decisions.md` に
  実在することを要求し、決定が未着地なら決定先行 wave と改訂 wave へ分ける形 2 を定めている。
  3 台帳の採番と追記は land が協調 lock の中で行うため、wave 側の commit に新しい決定は存在しえない。
- 保証の射程を落とすと、事前登録が実装より強い保証を名乗る。事前登録の値は
  「後から都合よく変えていない」ことの保証であり、過大な保証はその値を毀損する。
- `proof` は評価器では非空文字列としてしか読まれない。読者は人間の監査者だけである。
  だからこそ、束縛の所在と射程を文自身が正確に述べる必要がある。

**却下した選択肢:**

- **g11 の `ruling_reference` に D443 を代用して単一 wave で改訂する** — 機械検査は通るが、
  D443 は機構を決めた決定であって本改訂の内容と変更単位を承認した裁定ではない。
  D439 が却下済みの形であり、改訂の provenance が承認元へ到達しなくなる。
- **決定先行 wave で runbook の 3 箇所だけ先に直す** — 同一の主張を半分だけ直した状態を
  後続 wave のレビューへ渡すことになり、変更単位が割れる。
- **条件 11 の `required_evidence` へ D443 の 3 機構を足す** — 拒否理由の意味が変わるため
  `DECIDER_VERSION` bump と評価器改訂を要し、確定した変更単位を超える。
  必要なら独立の裁定として起こす。
