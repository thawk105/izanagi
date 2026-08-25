---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1687-carry-obligation-caller
seq: 2
---

## {{D:stage6-adapter-vs-operational-caller}}. 繰越義務は production adapter へ結線し、operational caller とは別々に数える

**決定:** 段 0 から繰り越した fixture 義務の解消述語
`require_stage0_fixture_obligations_discharged()` を、production 側の前提関門 adapter
`orchestrator/campaign/calibration_freeze_stage6_candidate_gate.py` の
`require_stage6_candidate_submission_ready()` から呼ぶ。ただし記録では次を分けて数え、
片方だけを書かない。

- **production adapter** = 義務述語を呼ぶ production module の件数。本決定時点で 1 件。
- **operational caller** = adapter を呼ぶ production module の件数。本決定時点で 0 件。

`docs/env-contract-activation-prerequisites.md` の繰越義務表は、この 2 数を並べたうえで
`unmet` を維持する。adapter が存在することは繰越義務の解消を意味しない。

段 6 の operational caller は義務述語を直接呼ばず、adapter を呼ぶ。直接呼ぶと adapter の
policy 未解決終端を迂回する。設計正本 §10 表 row 6 / §10.2 / §12.3 と contract module の逐語 pin は
この向きで一致させ、いずれかを旧文へ戻す変異が検査で赤になるようにする。

2 数はいずれも AST による機械検査で固定する。母集合は tracked + 非 ignored untracked の
全 Python から `orchestrator/tests/` を除いたもので、母集合が非空であること、
複数の root から選ばれていることを先に検査する。単純代入 alias と literal `getattr` を伝播し、
識別子は NFKC 正規化して照合する。判定は純関数へ切り出し、合成 source を渡す負の対照で
検出力を示す。

D810 の本文は改稿しない。同決定が「現時点でこの述語を呼ぶ production caller は存在せず、
設計正本にそう明記する」と記した箇所だけを本決定が supersede する。D810 の他の条項
(段 0 完了述語が義務述語を呼ばないこと、未解消集合を gate の blocking 状態から独立に算出すること)
は変更しない。

**理由:**

- 呼ばれない義務は機械的な保証にならない。文書上の宣言のままでは、後続段が実装された時点で
  義務を飛び越えて X を発効でき、繰越義務が誰の完了条件でもなくなる。
- 一方で、adapter を作っただけで「結線済み・充足済み」と記録すると、D580 が指摘した
  「production caller がゼロのまま writer API だけを足すのは、問題を API 呼び出しの
  一段手前へ移すだけである」型に当たる。段 3 と段 6 の独立した 4 レンズがこの所見へ収束した。
- 上流の呼び手は本決定の時点では作れない。段 6 の候補提出経路は
  `CFAB-STAGE6-POLICY-PREDICATE` (owner = user, status = `unresolved`) に依存し、
  X の発効自体が D437 の lockstep と人間 seal の手番である。作れない上流を作ったことにするか、
  義務を宣言のまま残すかの二択にしない。
- 2 数を分けて数え、そのうえで件数自体を機械検査にすれば、将来 operational caller を足す変更が
  台帳の該当行を同じ変更単位で直すことを強制できる。義務の所有者が消える経路をここで塞ぐ。

**却下した選択肢:**

- adapter を作って「caller 結線済み・充足済み」と記録する — 到達可能な段 6 経路が義務述語を
  通る証拠は無く、readiness の過大表示になる。
- 義務を宣言のまま据え置く — 後続段が義務を飛び越える経路が残る。
- 本 wave で段 6 submitter まで実装する — ユーザー裁定待ちの policy と人間手番の発効を
  親が飛び越えることになる。
- D810 本文を書き換えて「実装済み」にする — 裁定時点の事実を消す。決定台帳は履歴として保存し、
  supersede する範囲を新しい決定が逐語で指定する。
