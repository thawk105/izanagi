---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: t2273-acceptance-bottleneck-diag
seq: 1
title: [T-2273] [T-2560] 受入 shard-0 の律速を第 4 回として取り直した — 律速は共有 base 構築のうち Lustre からの可視 output 複製 (共有 7 本 + 非共有 1 本の builder が開始直後に同時に複製、待ち支配) で、複製元を計算ノード局所に置いた対照は同一 node の 1 対で W_0 を 123.9 秒 (27.3 %) 縮めた。次の一手は複製元の局所化 (実装差分ゼロ、insight + docs、branch worktree-t2273-acceptance-bottleneck-diag)
---

## 本文

- 一次資料: `output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md`。標本の時点は開始 gate 2026-09-23T07:42:52+09:00、計測 tip `3886a1fd3` (記録時の main `46933e4da` とは `orchestrator/`・`tools/` の差分なし)。
- 段 3 相談 (read-only 1 本、修正後 GO、所見 7 件) を全件採用した。親の仮説「同時構築本数による copy の IO 競合」は T-2786 §4 を反例に撤回し、無負荷 node の k 曲線 (Job C) を廃止し、対象を最大占有 worker とその依存 builder にした。
- 計算ノード job 4 本 (R1 18929 / R2 19029 / R2' 19108 / R2'' 19131、合計 Elapse 2,598 秒 ≈ 0.72 node 時間、受入を除く)。R2 の対照走は計算ノード /tmp のユーザー quota 超過で無効 (infra、probe の置き場)。R2' は**親が走行中に wave 木へ insight の下書きを書いた**ため smoke 後の clean 検査で止まった (検査は正しく働いた。下書きは job dir へ退避した)。
- probe (runner / plugin / analyze) は Codex author が 4 巡 (author・author-r2・fix1・fix2) で書き、repo 外で実行した。repo には逐語 `.md` だけを置いた。変異 matrix は実装面の差分ゼロで免除。記録前の実 repo テストの実走として、wave tip の受入 shard-0 相当 (4,269 件 = 4,216 passed・53 skipped) を R1・R2 の A2・R2'' の A2 / X で計 4 回完走した (rc 0)。
- 段 6 の独立 read-only レビュー 1 本 (修正後 GO、must-fix 1 = copytree の区間の混同、should 4 = 超過率・走と key の取り違え・非共有 builder の記載漏れ・可視集合件数と実複製件数の区別、nit 2) を全件反映した。受入全走は本記録 commit を含む tip で段 9 の前に行う。
- 今回の 4 走は pre が 128.8〜130.2 秒で、T-2825 の実受入 (62.6〜64.4 秒) の約 2 倍だった。原因は分解していない (insight 結論 8)。

## 次の一手差分

### 更新

- [T-2273] **P1・律速を再同定 (第 4 回)、次の一手 = t080 共有 base の可視 output 複製元の局所化**: 現行 main の shard-0 replica で、最大占有 worker (gw2) と L の worker (gw40) の最大成分はどちらも共有 base の builder を待つ flock (R1 206.5 秒、R2 の A2 230.7 秒、R2'' の A2 230.9 秒)。builder 1 本 = 複製成分 113.4〜138.0 (Lustre の `output/` の可視集合 29,885 path を列挙し所定の除外後に複製、self CPU/壁 0.11 で待ち支配) + 発行 subprocess 79.2〜80.1 (CPU 支配) + git 13.3〜13.5 で、現行台帳では共有 7 key の builder と検査用の非共有 builder 1 本が全部同時に始まる。複製元だけを node-local の git repo に差し替えた対照 (同一 node・同一 job の 1 対、R2''、差し替えは 8 本全部に効く) は W_0 454.6 → 330.7 (−123.9 秒、27.3 %)、O_max −123.6、L −121.4、builder の複製成分 138.0 → 11.1、発行は不変 (staging 43.9 秒は別欄)。実装 wave は局所の写しを作る時期・担い手・未 commit の可視 file の扱いを設計し、D2068 の却下 3 案 (whitelist / alternates / 独立 index) に触れない形で、隣接対の実受入で効果を測ってから land する。複製を除いた次の律速は発行 subprocess (X の依存 builder で 79.4 秒、内訳未測定)。A の同系 node 189.98〜208.09 秒は builder が開始直後の同時構築と重ならなかったことと整合するまでで、原因は未同定。5 分上限超過を受容しない。一次資料 `output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md`。
  base: be729628068efc94e2c331085818674e136082e4cb43e643668d841a07396917
- [T-2560] **P1・追認済み、第 4 回の実測を記録**: D1936 項 35 のとおり実測で律速を選んだ (第 4 回 = 共有 base 構築の可視 output 複製、insight `output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md`)。効果は同一 node の 1 対の対照で先に測った (W_0 −27.3 %)。実装は [T-2273] の次の一手として別 wave で行い、隣接対の実受入で効果を確かめてから land する。
  base: e0b602cfdaff3103c70c4d6c66d2e7e7a4ec46db01f63c5de9a438736d02888f
