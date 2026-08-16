---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1167-c12-allocation-binding
seq: 3
---

## {{D:c12-allocation-binding-shrink}}. 8c 条件 12 の allocation 証拠を実在する予約 binding へ縮小する

**決定:** ユーザー裁定 (2026-08-16 /rulings 全件 第 3 回、択 (c)) に従い、8c 事前登録 §6 条件 12 の
allocation 節が要求する証拠を、実在する予約 binding の照合 — `read_binding` / `check_reservation`
と PBS job ID・boot ID・予約期限までの残時間 — だけへ縮小する。単独性述語の呼び出しと、
launcher が single-process 違反および resume を launch 前に拒否することの証明は要求しない。
縮小で保護されなくなった 3 点は規範本文の「既知の構造衝突」へ逐語で名指しし、証拠範囲から外れた
プロセス単独性の運用要求が Pegasus runbook 側に残ることも本文で分離する。

判定器では allocation gate を独立 helper へ切り出し、environment / execution_guard gate より**前**へ
置く。終端は `EVIDENCE_UNDEFINED` のままとし、`SATISFIED` 経路は作らない。受理集合は変えない。
評価器の拒否理由の意味が変わるため判定器の版を bump する (D458 決定 1)。

**理由:**
- 旧契約が要求していた `single_process_required` は実装に存在せず、launch 前拒否の証明は module
  局所の到達解析では原理的に示せない。**検査すると謳って 1 度も発火しない保証**であり、恒真ゲート
  そのものだった (D441)。
- 旧要求は 1 度も発火していないため (D441 決定 3)、縮小によって**新たに拒否されなくなった実行は
  無い**。発火しない保証を発火する保証へ置き換える変更であり、正しさゲートを緩める変異ではない。
- gate の順序を前へ出すのは、実 repository に対する条件 12 の理由コードを誤診断 (環境契約
  consumer の不在) から実在の欠落 (allocation consumer の不在) へ変えるためである。D441 決定 4 が
  環境 gate の理由を誤診断と認定し、決定 5 が allocation 検査だけが真に欠けていると認定している。
- 縮小は保証を弱める方向なので、何が保護されなくなったかを規範本文に残さなければ、後世代が
  「元から要求していなかった」と誤読する。

**却下した選択肢:**
- 契約を保ったまま launcher へ配線する — 単独性述語が実在せず、新規実装は本裁定の scope 外。
  scope を広げて既成事実にしない。
- 条件 12 を丸ごと削除する — 予約 binding の照合は実在し実際に発火するため、発火する部分まで
  捨てる理由がない。
- 綴りを固定する形状検査を足す — 到達解析は may-reach であり、綴り一致は data-flow・支配関係・
  例外伝播のいずれも証明しない。証明しないものを証明したように見せる検査は足さない。

**記録した限界:** 第 5 世代 record の `ruling_reference` は D441 とした。D441 は択一集合を記録した
決定であって本決定の承認そのものではない。承認の一次資料は record の `revision_reason` の逐語と
worklog である。
