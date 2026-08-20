---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t1442-c06-reachability
seq: 3
---

## 新規

### {{F:dev-wave-stage4-dispatch-row-mutation-clause-missed}}. 段4裁定確定時に dispatch 表の複合行から `docs/dev-wave/mutation.md: DW-M01` 部分だけを読み落とす [手順漏れ]

- 事象: [T-1442] wave で、段4裁定 (通常の 1→2→3→4→5→6 直線フロー) を確定する際、command
  dispatch 表の「段4 |U| `docs/dev-wave/core.md`: `DW-S04`, `DW-G01`〜`DW-G05`;
  `docs/dev-wave/mutation.md`: `DW-M01`」という複合行のうち `core.md` 側だけを読み、
  `mutation.md: DW-M01` を見落とした。段6 fix 完了後、変異 matrix 投入直前になって
  `docs/dev-wave/mutation.md` を一度も読んでいないことに気づき、事後的に DW-M01 の変異
  事前登録を遡及して行った。同型の1例目は [T-1142] n-pilot R33 admission 再設計 wave
  (2026-08-19、非直線フロー「実装しない→ユーザー指示で再開」を経由) で発生している。
- 根本原因: 1 つの dispatch 表 row に複数の参照節 (`;` 区切りで異なる文書 2 つ) が
  併記されている箇所で、先頭の文書だけを読んで後続を読み飛ばす。通常の直線フローでも
  非直線フローでも共通に起きうる (1例目は非直線フロー、2例目は直線フロー)。
- 恒久対応: Claude 個人 memory `dev-wave-stage4-mutation-registration-checklist`
  (段4裁定確定直前に DW-M01 適用有無を自問し、handoff へ「変異事前登録: 済/対象なし(理由)」を
  明示欄として含める運用) が次回セッション以降の再発防止策として機能する。dev-wave command
  本体 (dispatch 表複合行の分割・強調) の是正は、`docs/dev-wave/*.md` 3層の byte 予算が
  既知で満杯 (`dev-wave-docs-compression-breaks-exact-pins` 系の既存制約と一致) のため
  本 wave では見送り、ユーザー裁定へ返す。
- 再発検知: なし (dispatch 表複合行の読了を機械的に検査する仕組みは未整備。Claude memory は
  同一ユーザーの別セッションへは伝播するが、Codex 子や他 AI 作業者には伝播しない)。
