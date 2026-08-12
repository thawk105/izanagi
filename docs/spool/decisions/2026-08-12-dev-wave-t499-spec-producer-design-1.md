---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t499-spec-producer-design
seq: 1
---

## {{D:oracle-spec-durable-is-lifecycle-not-schema}}. 8b oracle の durable 発行判断は schema version の択一ではなく lifecycle state machine の問題である

**決定:** `output/s8b-oracle-spec/` と `output/s8b-oracle-manifest-candidates/` へ durable artifact を
発行する判断を、「D302 の schema version 据え置きを解除するか再発行するか」という択一として扱わない。
`orchestrator/tests/test_s8b_oracle_manifest_contract.py` の zero-file assertion は
schema version で分岐しないため、どちらを選んでも同じ検査が落ちる。
**schema version は、schema object に実際の field / 意味の差分が生じたときだけ、
変更した側だけを上げる。** 現時点では reviewed spec 側も official manifest 側も v1 据え置きとする。

真の問いは「未承認状態の zero-file 条件を保ったまま、承認済み状態だけを受理する lifecycle
state machine をどう設計し、それを runtime のどこへ接続するか」である。
この置換は受理集合を真に広げる (0 件 ⊊ 承認された 1 件) ため、実装者の裁量ではなく
ユーザーの明示裁定として記録されなければならない。**本 wave は裁定材料の提示に留め、実装しない。**

**理由:**
- 現行 test は JSON を parse せず、2 directory 配下の `is_file()` が真な entry の件数だけを見る。
  schema literal を変えても受理集合は 1 bit も動かない。
- durable artifact が 0 件である以上、v1 bytes を読んでいる consumer は存在しない。
  守るべき互換性が無い状態で version を上げると、spec SHA・manifest SHA・manifest ID・
  driver の claim identity・golden・consumer 定数が一斉に変わるだけで、
  certified 選択も受理集合も変わらない。
- D302 が直接論じているのは official manifest schema であり、
  却下選択肢の「durable 発行後にこの決定を変えるなら再発行が要る」は
  **D302 の意味を変える場合**の条件である。最初の v1 artifact を発行すること自体は再発行理由でない。
- 段 2 プラン子は選択肢 A を「受理集合を広げるから規律 2 と両立しない」として却下したが、
  同じプランが「B でも zero-file assertion は落ちる」と認めている。
  受理集合の包含で形式化すると `E ⊊ A` かつ `E ⊊ B` であり、
  差が schema literal だけなら規律 2 の観点で A と B の強さは同じである。
  この否認は段 3 の敵対 2 本と親の独立実測が独立に一致した。

**却下した選択肢:**
- **reviewed spec と official manifest の協調 v2 再発行** — 上記のとおり受理集合を変えず、
  参照値だけを一斉に変える。実利が無い。
- **contract test を「非空でもよい」へ緩める** — 未検証 durable artifact を受け入れる方向へ
  受理集合を広げる。規律 2 違反。
- **contract test を削除・skip する** — 同上。

## {{D:oracle-approval-not-machine-enforced}}. oracle spec の人間承認は現状 機械強制されていないと明記する

**決定:** 現行の `APPROVED_SPEC_SHA256` 方式も、receipt を追加する方式も、
**同じ実装担当 (AI を含む) が bytes・hash・receipt・pin をすべて作成でき、
値の一致検査はすべて通る。** したがって、これらの機構について
**「人間承認を機械確認した」と書いてはならない。** 書けるのは
「人間が staged diff を review した」までである。
機械強制するには AI が書けない外部 trust root (allowlist key による detached signature、
または allowlist 済み署名 commit) が要る。その導入是非はユーザー裁定事項とし、本 wave では実装しない。

**理由:**
- `_load_approved_spec_bytes` は pin と disk bytes の一致だけを見る。git provenance を見ない。
  `_assert_user_commit` は freeze v2 の record 専用で、oracle spec 経路からは呼ばれない。
- `_assert_user_commit` を spec 経路へ足しても人間性は証明できない。
  逐語 `AI-Agent: none` は commit message の文字列であり、誰でも書ける。
  履歴 topology の defense-in-depth としては有用だが、単独で承認の証明にはならない。
- T-810 事前登録は先例にならない。その artifact 自身が
  `limitations.approval_receipt_trust_root_absent = True` と `protocol.run_authorized = False` を
  宣言し、`request_t810_launch` には正例が構造的に存在しない (常に例外送出)。
  すなわち「trust root が無いことを明記した休眠 seal」であって、動いている承認機構ではない。
- D302 は「hash は識別子にすぎず、承認は内容の再導出を伴う」としている。
  内容束縛の層 (`verify_manifest` の再導出比較) は健全であり、恒真ではない。
  欠けているのは内容束縛ではなく**承認者の同一性**である。

**却下した選択肢:**
- **receipt を足せば人間承認を表現できるとする** — receipt も同じ担当が作れる。
  信頼根を持たない receipt は authority ではない。
- **staged diff の人間 review を機械強制と同一視する** — 手続きであって runtime 表現ではない。
