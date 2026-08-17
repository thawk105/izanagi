---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t782-approval-sha-binding
seq: 1
---

## {{D:approval-pin-is-an-admission-gate}}. 承認済み spec の pin は admission gate として不変扱いにし、縮小候補は generator の bytes 照合に限る

**決定:** `s8b_oracle_spec.APPROVED_SPEC_SHA256` と disk bytes の一致検査は、
D320 の「対象外 (不変): 正しさゲート (verifier / admission / 変異検査)」に当たる admission gate として
扱い、`freeze_verification_hold` の held 集合へ入れない。撤去・緩和も行わない。
bytes 級 provenance 機構の既定見送りを理由にこの検査を縮小してよいのは、
同じ spec 内でも `generator_versions` の live bytes 照合だけである。

**理由:**
- 現在 pin が `None` なので official manifest を生成できる spec の集合は空である。
  pin を held にして照合を省略すると、この集合は「canonical path に置かれた schema を満たす
  任意の spec」へ広がる。schema 検証と批准凍結との cell 突合は残るが、
  `n`・`master_seed`・`block_sizes`・`campaign_ids` と run contract の
  `reps` / `extime` / `clocks` / `bench_max_rounds` は schema の範囲で自由であり、
  これらは実験そのものを決める研究設計値である。
  **すなわち held 化は未承認の研究設計を official 経路へ入れる受理集合拡大であり、
  規律 2 が名指しする経路を自分で開く。**
- 「内容再導出が残るので門は弱まらない」は誤りである。内容再導出は残るが、
  再導出の元が未承認のファイルになる。D356 も「欠けているのは内容束縛ではなく
  承認者の同一性である」として内容束縛そのものは健全と明記しており、
  承認者の同一性が恒久的に不在であることは内容束縛の無価値を意味しない。
- `generator_versions` の live bytes 照合だけは向きが違う。D302 が
  「defense-in-depth であり、新規の受理集合縮小としては主張しない」と本文で先に宣言しており、
  緩めても受理集合は広がらない。一方で維持費は実測で高く、pin 対象の production 5 source は
  2026-08-01 以降 22 commit で変更され、4 本は直近 4 日以内にも変わっている。
  durable spec を発行すれば数日で失効する。
- 既に held の凍結同一性検査 21 件 (D328) との扱いの不揃いは正しい不揃いである。
  held の対象は実装・測定の同一性検査であって admission gate ではない。
- 承認者の同一性を機械確認する外部 trust root は設けないと既に裁定されている。
  これは blocker ではなく宣言済みの保証限界であり、pin を外す理由にならない。

**却下した選択肢:**
- **承認 pin を held 集合へ加える** — 上記の受理集合拡大。親が当初推奨し、
  段 3 敵対検証が反証して撤回した。
- **durable な reviewed spec を発行して承認 SHA を記入する** — 判定を変えないまま
  schema 据え置き前提を崩し、再発行費用と失効管理だけが増える。
  手前に未凍結の集約規則・spec 層の単一 block 未検査・env 契約世代の失効・
  批准凍結なしでは導出不能な binding identity が残り、本走にも到達しない。
- **fail-closed を緩めて経路を通す** — 規律 2 違反であり、既存のユーザー裁定が
  「fail-closed のまま待つ。これは正しい状態であり緩めない」と定めている。
- **`generator_versions` の照合を今 held にする** — 向きは正しいが、この照合が噛むのは
  durable spec が存在するときだけで、今日は存在しない。
  発効しない裁定に手番を使わず、durable 発行の可否と同時に決める。
