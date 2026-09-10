# 段 6 裁定 (3 巡目・最終) — F-6 / F-8 と変異 anchor の確定 (2026-08-04)

焦点再レビュー 2 巡目 = closed 8 / partial 2 / regressed 0、RG2 なし。`DW-O16` の 3 巡上限に
達したため fix はこれ以上重ねず、残 2 件を親が裁定して閉じる。いずれも製品の受理集合の欠陥
ではなく、**変異証拠の表現力**の問題である。

## F-6 (M-A2) の裁定

登録 operator「global flock → per-origin flock への置換」は、現実装の `_locked(store)` が
origin を引数に持たないため**単一点変異として表現不能**。`DW-M01` の「確認できなければ登録せず
実効 gate へ再照準する」に従い、**M-A2 を「global flock の除去」operator へ再照準して確定する**
(1 巡目 fix の anchor L:1376–1406 相当を正とする)。旧登録は erratum として記録する
(`DW-M02`)。kill の意味は「flock 除去で 2 subprocess が同時進行し、LOCK_NB probe の
blocked 状態 assert と global head chain の衝突検出が赤になる」= fail-closed 挙動の期待方向の
変化であり `DW-M03` を満たす。per-origin 退化そのものの単一変異証拠は**取得不能と正直に記録**し、
「global 直列化は flock 除去変異 + cross-origin vector で担保」と限定して名乗る。

## F-8 (M-A5) の裁定

operation B (別 operation) は op-identity gate (L:2620–2621)・base gate (L:2622–2623)・
exact-continuation (L:2650–2655)・replay gate (L:2112–2125) の**多層防御**下にあり、
二層除去でも受理されない。`DW-M03` に従いこれらを**冗長 gate (防御深度) として記録**し、
単独変異の証拠から外す。**M-A5 の最終登録は「二層 (replay gate + exact-continuation) 同時除去で
altered continuation (同一 operation の改変 payload) が受理される」**とし、kill target は
受理集合 assert (T:757 相当) に限定する。operation B 排他は「変異で証明済み」と**名乗らない**。

## 変異 anchor 表の最終補正 (fix2-report 表への差分)

- M-A2: 上記のとおり flock 除去 operator へ (L:1376–1406 / T:601–716)
- M-A5: 二層 + altered continuation へ (L:2112–2125 + L:2650–2655 / T:742–758 の受理 assert)
- M-N1/N2: source anchor は L:430–442 (cell 4 要素の完全範囲 + return)
- M-N3: L:1081–1100, 1160–1169 (linked-worktree common-root producer), 1376–1406
- M-N6: source anchor に L:1858–1890 (prepared commitment 本体) を含める
- 他は fix2-report / focus2 監査の「○」のとおり

この表を `DW-M07` の anchor 再検証の入力とし、統合 commit 後に本走する。
