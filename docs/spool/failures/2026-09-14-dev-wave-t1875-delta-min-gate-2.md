---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t1875-delta-min-gate
seq: 2
---

## 新規

### {{F:ruling-identifier-not-checked-against-freeze}}. 裁定本文が名指す識別子の割り当てを、凍結の権威と逐語照合しないまま確定した [ドリフト] [手順漏れ]

- 事象: D1640 (2026-09-05) が `delta_min` の基準を「H1 = rr20、H2 = rr80」と書いたが、
  凍結の権威 `s8b_holdout_freeze.HOLDOUTS` は rr80 が H1・rr20 が H2 である。
  この対応は `31426fb9a` (2026-08-29) から不変で、**D1640 起草時点で既に逆**だった。
  逐語適用すると各 holdout の実質効果境界が他方の throughput 水準から作られ、片側は
  境界が過小になって環境ばらつき程度の差を「成立」へ通しうる (規律 2 の面)。
  2026-09-14 の T-1875 前提実測で発見。ゲートが閉じており測定は起きていないため実害は無い。
- 根本原因: 裁定を起草するとき、本文が名指す識別子 (H1 / H2) の割り当てを、凍結を生成する
  producer の現物ではなく周辺の記述から取った。同じ裁定を 4 日後に再確認した D1649 でも
  割り当ては照合されなかった。`delta_min` の値そのものは検証 consumer が型・符号・有限性を
  機械検査するが、**どの holdout にどの値を割り当てたかは consumer の検査範囲の外**にある。
- 恒久対応: memory `ruling-identifiers-must-match-frozen-authority` — 裁定・事前登録が
  凍結済みの識別子 (holdout label、cell id、candidate id) を名指すときは、起草時に凍結
  producer の現物へ逐語照合する。
- 再発検知: 凍結の識別子を名指す裁定を引いて実装・測定へ入る wave の段 1 で、
  引用元の割り当てを producer の現物と突き合わせる (目視。lint 化は未実装 —
  裁定本文は自由記述で、識別子と値の対応を機械抽出する経路が無い)。
