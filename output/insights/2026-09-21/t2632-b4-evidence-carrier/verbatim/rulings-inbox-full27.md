# /rulings 全件 第 27 回 — ユーザー裁定の控え (2026-09-21 00:5x JST、「推奨通り」、台帳へ未記録の間の一次控え)

提示 = entry 1770・main `285477c00`、索引 14 行 (ユーザー裁定待ち 11 + 人間手番 1 + 収載維持 2)。ユーザーの発話 = 「推奨通り」(直接、2026-09-21 00:5x JST)。
最終索引と相談の採否 = `/work/1/SFC/tanab/dev-wave-jobs/rulings-all-20260921/final-index.md`。記録 wave = `rulings-all-20260921` (branch `worktree-rulings-all-20260921`)。

1. T-2807: (a) 承認 — B-8 事前登録 v1 を案 A の発効束 (identity g_rl `b0f95b21…` / g_rt `a0219ce0…`、pin `e9e477ca`、patch `31316713…`、verifier 9 file、runner v5 `4ff6652a…`) で発効し、
   校正 3 job (walltime 03:30:00) → 規則が決める extime で本走 6 job (≤ 4 h / 対象、verifier hard timeout 1800 s) の投入を認可。発効 commit で story §8 B-8 の仕分け (2) の限定を書く。
2. T-2795: 4 巡目の入力元 = A (round 3 の派生物から射影、再構成物は明記・harness に load させない、記録に原本消失と派生物構成を書く、sha 一致は確認済み data の同一性まで)。
   pair 修復 wave (AI) → pair 再投入 + 4 巡目の予算再提示 (ユーザー) は不変。`submit-tree-pair` は本 session が lock 済み。
3. T-2632: (1) α (base driver の harness 書き side channel)、(2) (i) WAL record の canonical sha256 (`agent_outputs.canonical_bytes`)・(ii) ① 同一 campaign 内の時間順・(iii) PerfConfig 全 field を出所名指し (reps / ycsb_max_ope は不足として残す)、
   (3) 新規 base campaign の起動前、(4) 呼び手の trial 読取りを既存 codec 経由へ (Codex author の別 wave)。
4. T-2344: (1) 次段 = 発行器 6 本 (+ 発行器起点にだけ居る 10 本) 先行。(2) (c) 現状維持を既定、再解析需要 (T-1998 型) が生じた成果物に限り (a) を用意。
5. 未採番 (T-2810 wave の `{{T:g1-candidate-doc-scan-hit}}`): (a) 候補 file `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` だけを削除する commit を、T-2810 wave の land 後に別 commit で。
   scan 除外不変、削除後に load / reverify 再実測。根拠 = 候補 path の役割終了 (批准済み世代 D2180 へ移った)。
6. T-2792 (終端済み): (a) 次の story 版で 2 attempt の観察として書き L-A1S-4 を書き換える (プール・再現判定はしない)。図は作らない。新規 T は起票せず次版 wave の依頼文へ。
7. 未採番 (fig13): (a) README results 表の当該行を追補 (T-2816 と同 wave、AI)。後継図は作らない。
8. 未採番 (DW-O26): (a) inventory 群へ `test_ccbench_spawn_sites.py` / `test_check_subprocess_bytecode_guard.py` の 2 file を足す (D2186 項 5 の集合拡張)。予算は D782 / D961 の手順で AI、上限を上げた場合だけ報告。
9. T-2804 (終端済み): (a) 480 秒維持 + 内側導出 (C-2804)。延長は T-2805 / T-2819 の証拠が揃ってから。
10. 掃除: 候補 2 (現存 6 本) = retire-dry + fail-closed 退避 + insight「証拠の所在」節との照合を通して AI が撤去 (branch は残す) / 候補 3 = 据え置き / `impl-t2766-pairing-optin` = 撤去 / `impl-t2700-early-memo-optout` = 保存。
11. T-1558: 見送り維持 (F1034 は所有権証明では防げない。防壁は T-2814)。
12. T-2791: 送信 (人間手番、継続)。13. T-2605: 据え置き。14. 収載維持 7 件: 変更なし。

## 照合項 (記録 wave が状態語を書かない稼働 wave 所有の ID)

- T-2724 → T-2810 (索引 5 は未採番 T として D に記録、同 session へ SendMessage で通知)。T-2797 (試走中)。

## 反映

- 2026-09-21 01:20 JST に land (main fold commit `2afb39768`、記録 commit `3016f22ee`)。canonical = **D2194** (14 項)、worklog **entry 1771**、新規 **T-2820** (DW-O26 の 2 test 追加、項 8) / **T-2821** (候補 2 の検査付き撤去、項 10)。T-1558 は見送り台帳に追記済み (項 11)。この控えは台帳の写しに降格。
