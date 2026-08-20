---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1337-launcher-timing-proof
seq: 1
---

## {{D:attempt-timing-registry-proof}}. attempt 分類の時点証明を registry 内の論理順序偽装不能性として機構化する

**決定:**

1. 分類 (classify_attempt) が性能出力を読む前に確定したことの証明を、attempt registry 内での
   イベント順序の偽装不能性として機構化する。freeze→start→pre-observation-seal→classification→
   observation-start→terminal の全行を hash chain (event_index / previous_event_sha256 /
   event_sha256) で結び、registry の genesis が持つ schema_version を以後の全行へ強制する
   (genesis と異なる schema_version の行は reject する)。retry admission は直前 slot の terminal に
   observation_start_event_sha256 が存在しないことを必須条件とし、report_sha256 を持つ
   terminal-failure も同様に observation-start を必須とする。
2. この機構が証明するのは「registry に記録された論理順序が事後偽装不能である」ことであり、
   「trusted launcher 自体が実際に OS レベルで性能出力を先読みしていない」ことの独立検証では
   ない。後者は launcher (呼び出し側コード) の誠実な実装を前提とし続ける。
3. 性能 read API 自体を registry capability で包み、launcher 自体が信頼できない場合の時点保証を
   追加する拡張は、本決定の scope 外とする。

**理由:**

- D510 決定4は「分類は信頼側の起動器が...確定する」と、起動器の信頼性を前提として書いている。
  D550 決定6/7 はこの前提の下で保証範囲を「最初の性能観測より前」へ既に狭めていた。本決定は
  その系譜のまま「登録された分類が事後に偽装できない」という具体的な機構を追加するものであり、
  前提そのものを検証する新しい保証を作るものではない。
- 敵対レビューは、hash chain 単独では「OS レベルで実際に性能出力を先に読んだ上で後から正しい
  順序を偽装できないか」という別の脅威モデルを閉じないと指摘した。この指摘は正しいが、D510の
  前提 (起動器は信頼側) の範囲では、レビューが示した迂回はいずれも起動器自身が不誠実である
  ケースに限られ、正直な起動器を前提とする限り機構は機能する。
- プロトタイプ基準の下では、完全に敵対的な launcher への防御より、事後監査可能性 (改ざん検出)
  を優先する。

**却下した選択肢:**

- 性能 read API を capability で包み、launcher 自体の信頼性も機構的に保証する — 呼び出し側の
  広範な再設計を要し、既存の trusted launcher 前提 (D510) を覆す再裁定に相当するため、
  本 wave の scope を超える。将来 task 候補として起票する。
- per-slot の3イベントだけを hash 連鎖し全行連鎖は見送る — 検討したが、既存の full-ref 履歴検査と
  同じ層への統合であり実装複雑度がむしろ下がること、registry 全体の tamper-evidence という
  副次的価値もあることから、全行連鎖を採用した。
