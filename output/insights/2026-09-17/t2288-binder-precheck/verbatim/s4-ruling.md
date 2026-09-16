# 段 4 裁定 — [T-2288] binder precheck

2026-09-17 06:50 JST。親。段 2・3 は軽量版 (DW-C00: 設計択一なし・正しさ防壁に触れない・受理集合不変) で省略、
子ゼロ。裁定 inbox の再走査: local main は `abc7085ae` → `ad12ba35b` (rulings 第 20 回、39 項) へ進み、
wave branch を ff-only で揃えた。39 項に T-2288 / A-5 / 凍結 spec / binder への言及は無い (grep 0 件)。

## 裁定

- (P1)〜(P6) は provisional のまま採用。反証する所見は無い (子ゼロ)。
- 実装面差分 0 → 変異 matrix 免除 (DW-S04)。受入全走は免除しない。
- 実 repo を読む test: 本 wave は test を足さず production も変えないため対象なし。代わりに実走 (place ×1、
  validate-only ×3、負対照 ×3) を段 7 の記録前に行い結果を worklog fragment へ書く。
- plan v2 = brief の scope 1〜6 をそのまま。
- 中止条件 (依頼文): 準備が本番一式の再構築 (build・較正の再取得) になった時点で中止し理由だけ返す。段 1 の
  棚卸しでは record・binary・較正 3 件が揃っており該当しない。
- 捨て branch 名: `precheck-t2288-placeholder-specs`、起点 `ad12ba35b` (= 揃えた後の local main)。
  spec の `source_commit` = `ad12ba35b`。
- 規律 2: binder が落ちた場合、spec や driver を「通るように」変えない。落ちた検査名・エラー文・再現手順を
  insight に返す。凍結 wave に渡す注意点として記録する。
