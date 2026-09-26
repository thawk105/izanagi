# 段 4 裁定 (2026-09-23 21:05 JST)

入力: brief.md、prereg-draft.md、codex/s3-consult.md (相談 1 本、rc=0、check_codex_output rc=0)。裁定 inbox の wave 開始後の更新は 0 件 (find -newer startup-gate.log)。

| 所見 | 判定 | 採否 | 反映 |
|---|---|---|---|
| 1 P1 供給経路は置換で一致。実 argv と実コンパイル定義を記録せよ | real | 採用 | prereg 共通条件「build の記録」 |
| 2 別 patch の木でも gate は落ちない。通過を V07 挙動の保証と書くな | 部分的 (落ちないは静的推定、実走で確認) | 採用 | prereg 共通条件「gate」の但し書き |
| 3 同じ適用木の v=0 は妥当な stock 対照。0/1 が binary に入った記録を | real | 採用 | CXX_DEFINES 照合 (不一致なら走らせない) |
| 4 17 の timeout は確定予測にできない (UB・-ffinite-loops) | real | 採用 | R4 期待を「UB、主予測 hang」に改め、他の観測の分類を固定 |
| 5 write_count は commit した取引の大きさ。timeout 時に未到達と断定するな | real | 採用 | 到達の証拠の定義、timeout run の C 行統計は参考値 |
| 6 timeout run を verifier にかけない方針は正しい | real | 採用 | 変更なし |
| 7 分類表が一意でない (stock 失敗・verifier 失敗・帰属不明の異常終了が未定義) | real | 採用 | 段 A〜D の順序付き規則 |
| 8 R3/R1 は目的はあるが V07 分類の必須条件ではない | 部分的 | 採用 (4 run 維持、R3 は追加検証と明記) | prereg の役割欄 |
| 9 最小記録の欠落・見積りは期待値と上限を区別せよ | 部分的 | 採用 | build の記録、計算節 |

scope: 変更なし (V07 の 1 行、repo 実装面の差分ゼロ、gate・台帳・一般化の追加なし)。
分類は起動器が prereg.md の段 A〜D を機械的に計算して result JSON に書く (観測後の選択を無くすため)。親は insight でその値を写し、変えない。
変異 matrix: repo 内の実装面差分ゼロのため免除 (DW-S04)。受入全走は行う。
