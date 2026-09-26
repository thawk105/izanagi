# 段 6 裁定 — レビュー 2 本と本走結果 ([T-2847] si-v2、2026-09-26 20:0x JST)

入力: codex/s6-review-a.md (GO)、codex/s6-review-b.md (静的 must-fix なし、結果待ちで NO-GO)、runs/j1-a・j2-a の結果。

| ID | 裁定 | 採否 | 反映 |
|---|---|---|---|
| RA-01 V28 の reached と changed は構造上つねに等しい | real (should) | 採用 | insight の読み方に明記 (V28 は status が適格でない版で snapshot 条件を満たすものに出会った時点で必ずその版を選ぶので、reached = changed)。実装は変えない |
| RA-02 status と cstamp を別々に読むので境界で厳密な反実仮想にならない | real (nit) | 採用 | insight で診断値を「版選択時の観測値」と書く |
| RB-01 未完走 run の trace 行数が記録されない | real だが影響なし | 不採用 | 本走 J1・J2 の全 run が rc 0 で完走し、停止・異常終了は 0 件。成果物の値は変わらない (DW-G05)。起動器は直さない |
| RB-02 `test_screening_driver.py` の既定値 0 の assert 追加 10 行は直上の集合照合と重複 | real (nit) | 採用 | 依頼の scope 外 (仮想リスク向けの検査の追加)。先例 mocc でも同種の追加を統合しなかった。fix 子 F1 が hunk を外す (既存 test の期待値は変えない) |

本走の分類 (事前登録 R4 どおり、事後の変更なし):

| 行 | cell | 観測 | 分類 |
|---|---|---|---|
| V36 | K t4 | N、巡回 2,236、integrity 0 | 無改変 si の巡回検出 |
| V36 対照 | K t1 | I、巡回 0 | 期待どおり |
| V29 | S1 t4 | I、巡回 0、integrity 0、R 行 0、reached 17,825・changed 17,732・committed 17,732 | 盲点 |
| V29 の対照 | V2 S1 t4 | I、巡回 0、integrity 0 | 対照正常 |
| V28 | S2 t4 | I、orphan 45、巡回 0、他 integrity 0、reached = changed = committed = 2,931 | 期待した層で検出 |
| V28 の対照 | V2 S2 t4 | I、巡回 0、integrity 0 | 対照正常 |
