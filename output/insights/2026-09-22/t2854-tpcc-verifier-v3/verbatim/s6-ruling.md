# [T-2854] 単位 4 — 段 6 裁定 (親、2026-09-22 20:4x JST、対象 = 統合 commit 788657426)

入力: codex/s6-review-A.md (正しさ境界、GO、must-fix 0)、codex/s6-review-B.md (過剰・削除、GO、must-fix 0)、review/focus-1.log
(3,532 passed / 3 skipped / 0 failed)。統合 snapshot の退避 = review/integrated.diff (eef04f5a7..788657426)。

| 所見 | 判定 | 採否 |
|---|---|---|
| A1〜A10 (偽の認定・counter/capability・identity・fallback・v2 不変・schema 混在・厳格検査・構造化・試験の実体・既存試験 0 行変更) | refuted (攻撃不成立) | — |
| A11 (M1〜M15 の KILLED・単一理由は未実証、M1 は予定の assertion より先の辺集合比較で落ちる見込み) | real (検証残件) | 変異 probe と本走で確かめる。M1 の赤理由は「表が落ちて辺集合が変わる」で狙いどおり (検出点の行は問わない) |
| A12 / B10 (焦点走は受入全走・変異 KILLED の証拠ではない) | real (証拠の限界) | 受入全走と変異を別に行う。記録でも区別する |
| **B1** (fallback 試験の parse PID 確認が helper 末尾の `parse_trace_dir(..., workers=1)` の上書きを見ており、workers=2 の障害注入後の fallback を証明していない) | real | **採用 (fix2)**。段 4 R8(c)「v3 の parse / edge pool 障害から逐次への fallback 1 例」の未充足。成果物影響: 放置すると v3 の fallback で metadata を落とす退行を試験が検出する根拠がない |
| **B2** (legacy は workers を使わないのに workers=1/2 で反復。混在・優先順位試験も同様) | real | **採用 (fix2)**。R8 (a) の直積削減の未充足。成果物影響: 試験時間と保守量だけ (判定は不変) |
| **B3** (table 拒否 fixture の R/W が 0R/0W 宣言へ行を足しており単一違反でない) | real | **採用 (fix2)**。宣言件数を合わせ、拒否理由を table の字句・値域 1 つにする |
| **B4** (「packed」経路が実際に packed 表現になったことを肯定 assertion していない) | real | **採用 (fix2)**。通常の v3 fixture で `DSG.versions` が packed 型であることを確かめる |
| B5〜B9 (R1 の最小性、schema 機構、v2 の局所化、R8(c) の他項目、後続への足場) | refuted | — |

fix2 の制約: 試験 (test_verifier.py) だけを直す。production・既存試験の行は変えない。R9 の上限 (tests 800 行) 内。変異の新規登録はしない
(試験の実効を強める修正で、新しい production 機構ではない。M1〜M15 の位置は production 不変なので動かない)。
fix2 の後は焦点走と焦点再レビュー 1 本 (DW-S06-C、DW-O16) を行い、変異 probe → 変異本走 → 受入へ進む。
