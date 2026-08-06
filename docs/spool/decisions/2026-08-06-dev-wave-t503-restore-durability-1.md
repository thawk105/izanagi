---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t503-restore-durability
seq: 1
---

## {{D:no-issuerless-capability-freeze}}. 発行者のいない capability を受ける API を v1 として凍結しない

**決定:** 層の公開 API と record schema を実装・凍結してよいのは、その API が受け取る
capability (canonical root、incarnation nonce、quiescence 証明、exclusive lease) の**発行者が
実在する**ときだけとする。発行者が別 wave の scope にある間は、caller が自前構築できる値を
capability の代わりに受ける API を作らない。配線先を持たない基盤層も同じ扱いとし、
設計・逐語・択一を凍結して裁定へ返す。

**理由:**
- 発行者不在の capability を受ける API は、後で発行者を作ったときに必ず作り直しになる。
  凍結した schema と test が先に既成事実として残ると、正しい形へ戻す方が高くつく。
- caller が自前構築できる値は権威を表さない。同じ checkout に対して二つの正しい値が作れる以上、
  それを鍵にした排他は split-brain を防げない。
- 検証を caller の callback へ逃がした API は、no-op の復元でも terminal 状態を書ける。
  これは正しさシグナルを後付けにする failure mode そのものである。
- 配線しない層は `DW-G05` の成果物影響を書けない。書けない項目を実装 blocker にしないという
  gate は、基盤層にも同じ強さで効く。

**却下した選択肢:**
- 基盤だけ先に作って後で配線する — 敵対レビュー 2 本が独立に「安全な部分集合は無い」と結論した。
  抽出だけ先行すると、稼働中の durable 経路を触る risk だけを負って便益がゼロになる。
- 発行者の代わりに caller callback を信頼する — 上記のとおり terminal 状態を自己申告できる。
- schema を「暫定 v1」と称して凍結する — 暫定の表示は consumer には伝わらず、
  version 付き schema は事実上の受理契約として読まれる。
