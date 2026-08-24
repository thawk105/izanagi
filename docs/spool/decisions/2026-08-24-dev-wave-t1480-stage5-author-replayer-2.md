---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: dev-wave-t1480-stage5-author-replayer
seq: 2
---

## {{D:stage5-acceptance-unbound}}. stage5 author replayer の task acceptance を unbound に固定する

**決定:** stage5-author-replayer が出す receipt の `task_acceptance_status` は exact に `unbound`
とし、`fix_gate_eligible` と `routing_evidence_eligible` は false に固定する。機械的な
receipt status・CLI の終了コード・patch が当たったという事実のどれからも「その仕事が
受け入れられた」に相当する値を導出しない。contract、integrity、validation receipt、
downstream receipt validator、CLI 出力のすべてで exact field を要求し、generic な
`accepted` / `success` / `passed` を全深さで再帰的に拒否する。

**理由:**
- 意味的な受理を判定する task-specific oracle がまだ存在しない。oracle が無い状態で
  「機械的に valid な receipt」を受理の代理に使うと、正しさゲートを機械的整合性へ
  すり替えることになる。これは最適化圧力が最初に攻撃する面である。
- 受理が定義できない以上、fix への遷移も routing 証拠としての採用も定義できない。
  false 固定は機能の欠落ではなく、oracle 不在という事実の正直な表現である。
- exact field を要求すると、後から oracle が入ったときに「どこを変えれば受理が動くか」が
  1 箇所に限定される。generic な真偽値を受理していると、その面が散らばって特定できない。

**却下した選択肢:**
- `receipt_status=valid` を semantic review acceptance として review/fix loop の停止条件に使う —
  machine-invalid な receipt は常に fail-closed であって fix の入力ではない。停止条件に使うと
  「形式が整えば止まる」になり、意味の検査が消える。
- 適用後の tree hash を出力 hash や受理条件と呼ぶ — 適用後 tree hash は validation receipt の
  観測値であって事前登録した出力の同一性ではない。事前登録する `author_output_hash` は
  固定 author patch bytes の SHA-256 に限る。
- 汎用の correctness boolean を 1 つ置いて将来 oracle が埋める — 埋まるまでの間、consumer が
  それを受理と読む経路が開く。unbound を exact に要求するほうが fail-closed である。
