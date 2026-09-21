# 焦点走 27 本の帰属表 (親の provisional 分類、段 3 相談の攻撃対象)

区分の記号: C1 = 統合 tip の焦点走 (段 5 後、DW-S05-C「子の実走は親の全走を代替せず」+ DW-O26 集合)、
C2 = 最終 fix tip の受入前走 (DW-O26「受入前に」)、C3 = 受入赤の fix 後の単独再走 (DW-O18)、
C4 = wave 中に land した契約改訂 (DW-O26 inventory 4 群、T-2813 22:49 land) の追随、
C5 = docs-only wave の exact pin consumer 走 (DW-O26 文言外、(P5))、
E1 = 中間 fix 巡の再走 (最終 tip でない)、E2 = 別 job にした単独走 (D325 は相乗り・追加 dispatch 0 本)、
E3 = 親の手順起因の赤 (走行中 commit F558 型 / untracked fragment) で無駄になった走、E4 = held 診断走 (ユーザー明示 env)。
tip / 対象 / 結果は各 wave の insight README §焦点走 と job dir の log から。wall は `focus_runs_table.md`。

| # | wave | log | tip 段階 (insight 記載) | 対象 file 数 | 結果 | 区分 | wall s (queue s) | 備考 |
|---|---|---|---|---:|---|---|---:|---|
| 1 | t2804 | focus-1 | 実装後 (統合) | 15 | 緑 3893 | C1 | 483 (379) | |
| 2 | t2804 | focus-2 | fix1 後 | 15 | 緑 3893 | C2 | 109 (7) | |
| 3 | t2803 | focus-1 | 実装後 (統合、commit 前) | 6 | 緑 2738 | C1 | 777 (689) | 集合に test_check_ai_provenance.py を含む |
| 4 | t2803 | focus-2 | 同 tip、単独走 | 1 | 緑 575 | E2 | 48 (13) | file は #3 の集合内 = 同一 tip の重複 |
| 5 | t2803 | focus-3 | fix1 後 | 6 | 赤 2 | E1 (赤 = fix2 の入力) | 94 (8) | 既存 pin との衝突 |
| 6 | t2803 | focus-5 | fix2 後 | 6 | 赤 1 | E1 (赤 = fix3 の入力) | 94 (7) | 既存 pin との衝突 |
| 7 | t2803 | focus-6 | fix3 後 (commit 前) | 6 | 緑 2718 | C2 | 237 (151) | |
| 8 | t2803 | focus-7 | fix commit 中の単独走 | 1 | 赤 23 (非帰属) | E3 | 58 (23) | 走行中に commit、F558 再発 |
| 9 | t2803 | focus-8 | fix commit 後、単独走 | 1 | 緑 555 | E2 | 47 (8) | #7 と同内容の木 (HEAD だけ違う)、(P1) |
| 10 | t2344 | focus-f1 | 統合 65e94a3a7 | 23 | 赤 3 | C1 | 58 (8) | 期待値追随漏れ |
| 11 | t2344 | focus-f2 | fix1 5bfb5fec0 | 23 | 緑 3115 | C2 | 462 (413) | |
| 12 | t2344 | focus-f3 | merge 後 tip + inventory 4 群 | 9 | 緑 1721 | C4 | 723 (669) | T-2813 の改訂追随、(P2) |
| 13 | t2344 | focus-f4 | 受入赤 → fix2 後、単独走 | 1 | 緑 69 | C3 | 32 (7) | |
| 14 | walldecomp | focus-1 | docs commit 993d2fc5f | 1 | 緑 580 | C5 | 57 (8) | test_check_docs.py (exact pin consumer) |
| 15 | walldecomp | focus-2 | fix1 6d600f0a6 | 1 | 緑 580 | C5 | 1058 (1007) | PRR 16 分 49 秒 (実測済み) |
| 16 | t2814 | focus-1 | 統合 C 6dae18be1 + untracked fragment | 19 | 赤 1 (手順起因) | E3 | 100 (7) | wiring_probe inventory が untracked を検出 |
| 17 | t2814 | focus-2 | 記録 commit 6e0cafe08 (clean) | 19 | 緑 3870 | C2 | 477 (384) | 本来 #16 が C2 |
| 18 | t2810 | focus-impl-1 | 統合 dc5b0f39b | 10 | 赤 1 (本差分) | C1 | 841 (577) | 集合が DW-O26 の consumer 7 を欠く |
| 19 | t2810 | focus-fix2-1 | fix2 083a45ee9 | 17 | 緑 1876 | C2 | 268 (7) | 10 + consumer 7 |
| 20 | t2810 | focus-held-1 | fix2 同 tip、held 6 node | 3 | 緑 9 | E4 | 817 (715) | `IZANAGI_RUN_GROWTH_HELD_TESTS` 明示 env、同 job 化不可 (env が走全体に効く) |
| 21 | residue | focus-f1 | 統合 82b36fb64 (unit A) | 10 (+契約 module 1 混入) | 赤 10 実 + 33 setup error + 1 dirty | C1 | 518 (375) | 実赤 10 が再走を要求、34 は手順起因 |
| 22 | residue | focus-f2 | fix c6638054b | 10 | 緑 1011 | C2 (unit A) | 1161 (1020) | |
| 23 | residue | focus-f3 | 統合 f0a214661 (unit B、+3 file) | 13 | 赤 2 (追随漏れ) | C1 (unit B) | 155 (8) | |
| 24 | residue | focus-f4 | fix 1972bd33f | 13 | 緑 2438 | C2 (unit B) | 1165 (1020) | |
| 25 | t2797 | focus-1 | 統合 commit 3 | 21 | 緑 2475 | C1 | 473 (337) | |
| 26 | t2797 | focus-2 | fix commit 4 | 21 | 緑 2521 | E1 (緑、後続 commit 5 あり) | 145 (7) | 事後的な重複、(P3) |
| 27 | t2797 | focus-3 | commit 5 + main 取込後 e4f4c900c | 21 | 緑 2526 | C2 | 145 (7) | merge 後だが commit 5 の受入前走を兼ねる、(P2)。commit 5 は login 実走で先に確認 |
| — | t2817 | rerun-single | 受入赤の単独再走 (login bounded local) | 1 | 緑 1 | 母数外 | 13 | 計算ノード job でない |
| — | t2817 | rerun-single2 | 同上 | 1 | 緑 45 | 母数外 | 30 | 同上 |

## 集計 (compute 27 本)

| 区分 | 本数 | wall 合計 s | 備考 |
|---|---:|---:|---|
| C1 統合 tip | 7 | 3305 | t2804 / t2803 / t2344 / t2810 / residue ×2 / t2797 |
| C2 最終 fix tip | 8 | 4024 | t2804 / t2803 / t2344 / t2814 / t2810 / residue ×2 / t2797 (下記注) |
| C3 受入赤 fix 後の単独再走 | 1 | 32 | t2344 f4 |
| C4 契約改訂の追随 | 1 | 723 | t2344 f3 |
| C5 docs pin consumer | 2 | 1115 | walldecomp |
| E1 中間 fix 再走 | 3 | 333 | 赤 2 (必要な signal) + 緑 1 |
| E2 別 job の単独走 | 2 | 95 | t2803 focus-2 / focus-8 |
| E3 手順起因の赤で無駄になった走 | 2 | 158 | t2803 focus-7、t2814 focus-1 (再走側で数えると 47 + 477 = 524) |
| E4 held 診断走 | 1 | 817 | t2810 |

注: C2 は #2 #7 #11 #17 #19 #22 #24 #27 の 8 本 (wall 109+237+462+477+268+1161+1165+145 = 4024 s)。C1 は #1 #3 #10 #18 #21 #23 #25 の 7 本 (483+777+58+841+518+155+473 = 3305 s)。
契約内 C = 7 + 8 + 1 + 1 + 2 = 19 本 (wall 3305+4024+32+723+1115 = 9199 s = 86.8 %)、契約外 E = 3 + 2 + 2 + 1 = 8 本 (wall 333+95+158+817 = 1403 s = 13.2 %)。
(P5) で C5 を契約外に読むなら C = 17 / E = 10 (E に 1115 s 加算)。
