---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t810-harness
seq: 3
---

## {{D:t810-launch-authorization-witness}}. 測定装置の effect 入口は休眠封印ではなく起動認可 witness で塞ぐ

**決定:** T-810 測定装置の effect を持つ入口 (scheduler adapter、qdel、benchmark 実行、
marker と manifest の書込み、台帳 append) は、`t810-launch-authorization/v1` witness を
型付きの引数として要求する。witness は schema module の検証関数だけが構成でき、
CLI・設定・環境変数から合成する経路を作らない。**本 wave は witness の発行経路を実装しない** —
実体は protocol §9.1 item 6 の人間による第 1 段承認 ID である。

**理由:**
- 既存の休眠封印 (`run_authorized`) は effect gate に使えない。§6.3 の validator は
  `run_authorized=True` の事前登録を「封印が閉じていない」として拒否するため、
  封印を開けた状態では非流入検査そのものが走らない。封印検査と effect 認可は別の問題である。
- 低水準 adapter を private 名 (`_subprocess_scheduler` 等) にするのは能力境界ではない。
  import して直接呼べる以上、型で要求しない限り認可を迂回できる。
- 発行経路を作らないことで、実装が揃っても本 wave 自身では 1 件も投入できない状態を保てる。

**却下した選択肢:**
- effect adapter 自体を置かない (認可されるまで実装しない) — runner policy が単独の
  mediation 点を持たない限り receipt-only へ退化するため、adapter と同一 wave に置く必要がある。
- 封印を一時的に開けて検査する — 非流入検査が走らなくなり、絶対規律 1 と 6 の防壁を弱める。
- caller が渡す boolean で認可する — 自己申告であり、過去のレビューが恒真化として退けた形と同じ。

**限界 (機械可読に宣言する):** witness に署名も外部の信頼の根も無く、
発行者を偽装できる。この限界は `approval_receipt_trust_root_absent` として
policy・receipt・終端状態へ同じ ID で伝播する。
