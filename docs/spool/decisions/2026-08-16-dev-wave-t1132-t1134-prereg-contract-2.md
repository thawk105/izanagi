---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1132-t1134-prereg-contract
seq: 2
---

## {{D:s8c-prereg-contract-revision}}. 8c 事前登録の証拠契約を、受理集合を広げずに評価器へ到達させる形へ改訂する

**決定 (2026-08-16 ユーザー一括裁定 T-1132 / T-1133 / T-1134 = 推奨どおり全件確定の実装形):**
段 8c 事前登録の証拠契約 `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` と
`docs/phase3-8c-preregistration.md` §6 を、次の 4 点で改訂する。本 D は D96 条項 1 が要求する
新しい設計判断の記録であり、改訂を行う wave の世代記録が引く裁定参照でもある。

**決定 (1): 評価器の到達可能化は `machine_checkable` の反転だけで行い、終端は変えない。**
評価器が実装済みの 6 条件 (C01・C04・C09・C10・C11・C12) だけを `true` にする。
評価器を持たない 6 条件は `false` のまま残す。**6 評価器の終端
`EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` と、空集合の
`SATISFIABLE_CONDITION_IDS` は維持する。** 静的到達性は完了の証明ではない。
本改訂の実利は受理側にはなく、**恒真だった負の対照 6 件が発火するようになること**にある。
現行の `test_noop_and_token_only_fixtures_never_satisfy` は、字面だけの fixture と
それを壊した fixture の双方に同じ `EVIDENCE_UNDEFINED` を期待しており、契約が
「機械検査対象外」と記す限り内容と無関係に必ず通る。反転後は壊した側が条件別の
`UNSATISFIED` 理由を返し、対照が初めて拒否能力を持つ。

**決定 (2): 条件 11 の証拠を、廃止済みの方針成果物から既存の実装機構へ差し替える。**
`output/s8c-preregistration/sample-plan.v1.json` と
`output/s8c-preregistration/generation-cap-lift.v1.json` は作らないことが確定しているため
証拠から外し、承認上限定数と 3 入口の予算 validator、および
`orchestrator/campaign/s8c_generation_projection.py` の閉じた第二層射影
(`_CRITIC_KEYS` / `_DIAGNOSTIC_METRICS` / `apply_critic_feedback` /
`_validate_critic_projection` / `validate_planner_payload`) を証拠とする。
**これらを「独立 4 機構」と数えない** — 上限定数と 3 入口 validator は 1 機構、
射影と production 配線は 1 機構、負の対照は開発テストであって commit 証拠に入らない。
差し替えにより条件 11 は `UNSATISFIED` から `EVIDENCE_UNDEFINED` へ移り、
受理集合は広がらない。

**決定 (3): 世代下限の強制は条件 11 の機構に求めず、起動形の責務のまま残す。**
削除する標本設計成果物は `minimum_generations >= 2` の下限を持っていたが、
既存機構は上限しか持たない。実測では予算 validator が `1` 以上を受理し、起動側の既定値も
`1` である。ただし事前登録文書 §4 と §7 は exact `G=2` を起動形の責務として既に規範化し、
「`G=2` を宣言だけで満たしたと見なさない」と書いている。したがって差し替えは文書と整合する。
残余として「exact `G=2` を要求する正式受入 consumer が存在しない」ことを別タスクへ起票する。

**決定 (4): 条件 3 / 8 の commit 自己参照は、内容 commit と発効 commit を分ける二段束縛で解く。**
内容 commit `P` が 6 cell manifest の bytes を導入し、**manifest は `P` の識別子も
自分自身の digest も持たない**。発効 commit `C` は `P` の直子で、
`prereg_content_commit` と manifest digest を持つ binding record だけを導入し、
`C` 自身の識別子は持たない。祖先代用の禁止は `is-ancestor` ではなく
**「`C` の親集合が exact `{P}`」**で維持する。ff-only land と後続 fold は `C` の親を変えないため
両立する。`prereg_commit` を互換 alias として残さない (D75 の同名識別子二義化)。
本改訂は契約と規範本文の形だけを直し、`orchestrator/campaign/trial_registry.py` ほかの
consumer 配線は行わない。条件 3 / 8 は `machine_checkable: false` のまま残し、
実装したふりをしない。

**D410 との関係:** D410 は「s8c C11 は `machine_checkable: false` のまま `EVIDENCE_UNDEFINED`
= 未充足」と記した。本 D はその記述を、決定 (1)(2) の範囲でのみ更新する。
D410 が同時に述べた「C11 の充足状態を承認上限引き上げの権威根拠に使わない」は不変であり、
本 D も C11 の充足を主張しない。D410 が作らないと定めた 2 成果物も作らない。

**D165 との関係:** D165 は発効を導出値と定め、条件ごとの充足判定器の実装を後続タスクとして
明示的に残した。本 D はその後続タスクのうち、**判定器を到達可能にする部分だけ**を実施し、
充足を返す部分は実施しない。

**理由:**

- 証拠契約が 12 条件すべてを機械検査対象外と記す限り、実装済みの評価器は 1 本も呼ばれず、
  どの条件も充足を返せない。これは発効経路の最も手前の閂である。
- 同じ記述が、条件別の負の対照を同時に恒真化していた。反転しなければ、
  「負例あり」という契約表示は実際の拒否能力を持たないまま残る。
- 終端まで動かすと、静的検査を通るだけの実体のない実装が充足と認定される。
  既存の字面だけ fixture がそれを実証しており、規律 2 が名指しで禁じる形になる。
- 条件 11 の証拠を方針成果物に置いたままでは、それらを作らない裁定と両立せず、
  条件は構造的に永久未充足である。
- 条件 3 / 8 は、manifest の bytes が commit 識別子の入力である以上、
  単一 commit では構成できない。二段に分ける以外に構成可能な形が無い。

**却下した選択肢:**

- **6 評価器の終端を一律 `SATISFIED` にする** — 静的検査を通るだけの実体のない実装を
  充足と認定する。受理集合を広げる方向の緩和であり規律 2 違反。
- **AST の支配関係検査で完了証明を discharge し、条件 11 だけを `SATISFIED` にする** —
  D96 が同方式を「構文形状しか固定できない (`if False`・alias・`getattr`・例外握り潰しを
  見逃す一方、無害な refactor で偽赤になる)」として既に却下している。
  実際に `if False` と catch-and-continue で全条件を通す最小偽装が構成できることを確認した。
- **評価器を持たない条件も `true` にする** — 評価器不在で `ERROR` になるだけで、
  診断を悪化させる。
- **manifest に内容 commit の識別子を埋める** — 二段に分けても自己参照が残る。
- **`prereg_commit` を互換 alias として残す** — 同名識別子が 2 つの意味を持つ。

**研究状態への影響:** 本 D 単独では certified 選択・材料レポート・試行台帳のいずれの値も
変えない。改訂を実施しなければ、8c 本走の事前登録は永久に発効せず、正式系列は開始できない。

## {{D:s8c-freeze-ruling-must-land-first}}. 条件契約の世代記録が引く裁定は、記録を導入する commit より前に台帳へ着地していなければならない

**決定:** 段 8c の条件契約世代記録 (`output/s8c-preregistration/condition-freeze/`) の
`ruling_reference` が指す決定見出しは、**その世代記録を導入する commit の時点で
`docs/decisions.md` に実在していなければならない**。したがって、凍結範囲を変える wave は
次のいずれかの形をとる。

1. 裁定を記録した決定が既に main に着地している場合は、その番号を引いて同一 wave で改訂する。
2. 決定がまだ無い場合は、**決定だけを先に land する wave** と、**世代記録・契約改訂・
   境界テストを同一 commit で land する wave** に分ける。

**D96 との関係:** D96 が「同じ変更単位」を要求しているのは条項 2 (境界テスト) だけであり、
条項 1 (新しい設計判断の記録を起こす) には同単位要求が無い。したがって形 2 は D96 に適合する。

**理由:**

- 世代記録の検証は、記録を導入した commit 時点の台帳 blob に対して決定見出しを探す。
  台帳への追記と採番は land が協調 lock の中で ff-only 取り込みの**後**に行うため、
  wave 側の commit には新しい決定が存在しえない。
- 前例でも、第 2 世代が引いた決定は同世代の導入 commit より 12 時間前に別 land で
  着地していた。当時この順序は暗黙であり、記録されていなかった。
- 受入は作業ツリーから候補 commit を合成して同じ検証を走らせるため、
  順序を誤ると受入が赤になり land できない。手順を知らずに組むと wave 1 本を丸ごと失う。

**却下した選択肢:**

- **世代記録の裁定参照に手続の決定を代用する** — 機械検査は通るが、
  その決定は当該改訂の内容を承認していない。改訂の provenance が承認元へ到達しなくなる。
- **裁定参照の受理形を未 fold の台帳 fragment まで広げる** — canonical でないものを
  裁定 authority に昇格させる。fragment・採番後の番号・導入 commit・land transaction を
  結び付ける新しい検査が要り、単なる受理形の拡大では済まない。
- **land が ff-only 取り込みの前に台帳を fold する順序へ変える** — land 手続と
  再検査単位の変更であり、本件の副産物として決めてよい範囲を超える。

**研究状態への影響:** なし。本 D は手続き規律であり、受理集合・certified 選択・
proof chain を変えない。変わるのは凍結範囲を触る wave の分割方法である。
