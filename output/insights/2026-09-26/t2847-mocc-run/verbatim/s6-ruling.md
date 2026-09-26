# 段 6 裁定 — [T-2847] mocc-run (2026-09-26)

入力: codex/s6-review-a.md (条件付き GO、F1〜F5)、codex/s6-review-b.md (条件付き GO、B1〜B4)、焦点走 f1 (HEAD 267b8992f、33 file、4,049 passed・8 skipped・失敗 0、Elapse 144 秒)、計測 m1-J1〜J4。

| ID | 裁定 | 反映 |
|---|---|---|
| A-F1 | real (分類の名前の欠落) | **erratum (段 4 R4):** 状態 9「対照正常」= stock と V34 の非空 S・X/P・他 integrity 0 を足す。V34 は changed = 0 が定義なので「未発生」に数えず、到達は site 別 counter で書く。計測の後に足した名前であり、変異 cell の分類は変えない |
| A-F2 | real | 停止 3 cell は「同 job の stock は約 1 秒で完走、変異 build は 120 秒で停止、診断欠落。相互待ち・自己待ちの原因は未確定」と書く。gate の 4 条件は満たし、変更由来の二重取得・二重解放の経路はレビューで見つからなかった |
| A-F3 | real | V34 の対照が示すのは評価された site 297・460 の等価性と verifier の正常判定だけ。W (rratio 0・rmw true) は site 567 (delete 経路) と 971 (read set の要素がある validation) を通らない |
| A-F4・A-F5 | 確認 | 変更なし |
| B1 | 実装の must-fix としては refuted | 既定値は screening_driver.py にあり焦点走で緑。Genome 経由で供給できないことは既存の汎用 build 経路照合 (`screening-build-route-mismatch`) に依り、専用 test は足さない (前回の silo 14 本と同じ)。insight に書く |
| B2 | real (docs) | README の inert 文を「未定義の枝を除いた全文が pin C とバイト一致」に狭めた |
| B3 | real nit (docs) | README 冒頭表の「broken-mocc 3 本」を直した |
| B4 | refuted | repo 外の使い捨て起動器の定数照合は計測の前提を守る確認で、repo に検査面を足していない。残す |
| T-2849 合流 | 事実 | t2849-unit-a は test_ccbench_spawn_sites.py に非 CCBench subprocess site 1 件を足すだけで件数行に増分なし。合流値 = 55 / 59 / 45 / 45 |

コードの fix は無し (fix 子を起動しない)。焦点再レビューは fix が無いので不要。変異 matrix (段 4 R7) へ進む。
