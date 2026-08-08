---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-08
wave: dev-wave-t181-stage6-high
seq: 1
---

## {{D:stage6-reasoning-high}}. 段 6 review 子の reasoning を `high` に確定する — D207 の段 6 限定例外

**決定:** `docs/dev-wave/workers.md` の `DW-S06-A` (敵対レビュー 2 本) と `DW-S06-C`
(焦点再レビュー) の reasoning を `high` と明記し、`tools/check_docs.py` が節ごとに exact pin する。
`DW-O16` には effort 値を置けない (焦点再レビューの effort は `DW-S06-C` だけを正本とする)。
段 2・段 3 の `reasoning=max` と段 5 の `reasoning=high` は変更しない。

**採用根拠は 2026-08-08 のユーザー裁定のみである。** 本決定は 2026-08-01 のユーザー裁定
(`DW-S06-A` / `DW-S06-C` は `max`、引き下げは A/B の 10 run 再走で根拠ができてから、
当該測定は段 6 focused review のものであり他段へ外挿しない) と、工程別 policy 採用を
再走待ちとした裁定を**明示 supersede する**。D207 の一般原則
(effort の引き下げ可否は paired・blind・非劣性の評価だけが決める) に対する
**段 6 限定・人間裁定による例外**であり、一般 precedent にしない。

**証拠の状態 (記録から落としてはならない):**
- 参照する A/B は `aggregate` / `verify` ともに `experiment_complete=false` / `decision=null`、
  失敗理由は全 10 run の `snapshot oracle replay mismatch` で**未認証**である。
- 当該 insight の事前登録により、許される主張は「その 6 run で劣化を観測しなかった」だけであり、
  **非劣性・同等性・採用の証明ではない**。
- 測定対象は焦点再レビューの prompt 由来 benchmark だけで、**敵対レビュー 2 本は測っていない**。
  段 6 全体への適用はユーザーによる外挿の裁定である。

**射程:** 本決定が拘束するのは **docs の記述と、その書き換わりを止める機械 pin だけ**である。
段 6 の子は `DW-O01` の雛形どおり親が起動 command を組み立てるため、
**実起動値が `high` である機械保証は含まない**。それには launcher 結線が別途要る。
pin 対象は `DW-S02` / `DW-S03` / `DW-S06-A` / `DW-S06-C` と `DW-O16` の effort 不在のみで、
**`DW-S05-A` と `DW-S06-B` は対象外**である。「段 6 の全 child を機械 pin した」と書いてはならない。

**理由:**
- 段 6 の effort は契約に無く歴史運用が割れていた。値を確定して機械 pin することは、
  値が `max` でも `high` でも独立に必要な是正である。ユーザーが値を選ぶ。
- 未認証の証拠で検出力側を動かす判断は規律 2 の射程に入る。だからこそ AI は採否を決めず、
  証拠の欠落と既存裁定との衝突を開示したうえで人間へ返した。開示後の裁定を採用根拠とし、
  証拠が採用を支持したようには記録しない。
- 文字列の存在を数えるだけの pin は恒真になる。本 wave では 3 巡続けて迂回が見つかった
  ({{F:substring-pin-tautology}})。規範文と完全一致する可視な独立行がちょうど 1 行あることを
  要求する形だけが、契約の消失を実際に止める。

**却下した選択肢:**
- `DW-S06-A` だけを pin する — `DW-S06-C` に `max` と書いても通る穴が残る。両節を pin する。
- 条件節「実装 wave は」を落として無条件形にする — docs-only wave へ敵対レビュー 2 本を
  強制する受理集合の拡大になり、軽量版の「docs-only は子ゼロでよい」と衝突する。
- 「全体へ 1 本でよい」を byte 捻出のために削る — この「1 本」は 1 巡あたりの reviewer 本数の
  許可であり、削れば子とトークンが増える。byte は導入文の縮約で捻出する。予算値は上げない。
- 実装せずユーザーへ返し続ける — 値の確定自体は既に裁定済みで、実装待ちのまま滞留していた。
