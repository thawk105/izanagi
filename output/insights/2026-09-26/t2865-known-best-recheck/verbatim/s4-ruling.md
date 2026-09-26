# 段 4 裁定 — [T-2865] 付随: 既知最良超え IR 3 点の別 job 再測 (2026-09-26 20:1x JST)

入力: 段 3 相談 A (`codex/s3-consult-A.md`、gpt-6-sol / medium、read-only、adopt_with_conditions、check_codex_output rc=0)。
裁定 inbox 再走査 (20:14 JST): 第 36 回 (D2249) の時間帯の裁定 = 時間帯の区切り・時間を空ける規則を入れない、同時刻の対照は残す。本計画は同 job の参照 (同時刻の対照) を使い、時間帯の規則を持たないので整合。

## 所見の裁定

| # | 所見 | 判定 | 処置 |
|---|---|---|---|
| 1 | P2 の分類に優先順位が無い (must-fix) | real・採用 | 判定規則に順序を固定: 束縛 → 点の verify/trace0 → 他の適格性 → 比。相方 IR は条件に含めない |
| 2 | P3 の投げ直し条件と採用時点が曖昧 (must-fix) | real・採用 | 起動前失敗か対象点の行が 0 の job だけ 1 回。部分 JSON に対象点の行があれば採用。採用試行は結果 JSON を開く前に完了順で固定 |
| 3 | 集計の正例一致だけでは束縛照合を保証しない (should) | real・採用 | 集計スクリプトの受入: (a) 旧 8 job で既存 compare-aggregate.json の 16 点と完全一致、(b) 負例 2 本 (source evidence 欠落、fixed10 の trace0 define 不成立) を旧 JSON の写しから作り、対象点が判定不能 / 束縛不成立になることを親が確認。repo へは入れない (仮想リスク向けの検査を repo に足さない) |
| 4 | 見積りが P3 と不一致 (should) | real・採用 | 最悪 6 計測 job 4,674 秒 (1.30) + 受入 2 回 (最新実測 3 shard 合計 約 1,070 秒/回、0.59) = 約 1.89 node 時間 < 2。通常 約 0.95。焦点走は実装面 0 で不要。確認線未満で投入 |
| 5 | 「別 job」の効力の限定 (should) | real・採用 | insight に「対象点の job 内位置は元と同じ (同じ `_cases` 巡回)。job・ノード・時刻が別の再測であって、位置・job 内交絡から独立した再現ではない」と書く |
| 6 | pin 差の説明の範囲 (nit) | real・採用 | 「確認した CCBench の差分は cc/mocc/transaction.cc の 64 行追加のみ。pin 差を記録し、同一 binary の証明とは扱わない」 |

## プラン v2

1. 判定規則 (下の最終形) を新 insight `output/insights/2026-09-26/t2865-known-best-recheck/README.md` §1 に書き、**計測投入の前に wave branch へ commit** する。
2. 計測木 3 本 (`.claude/worktrees/t2865-recheck-recon-{0,1,6}`、detached `265cce13c`、ccbench 68106660、作成済み rc=0 clean) から `dispatch_compute.py --task generic --walltime 00:30:00 --queue-wait-timeout 3600 -- python3 -m orchestrator.campaign.silo_policy_recon run --phase compare --job <i> --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache --out <木>/output/env/pegasus/calibration/silo_function_policy_recon/compare-recheck/compare-<i>.json` を同時 3 本。
3. 段 5 (並行): Codex author 1 本が repo 外集計スクリプト (`recheck_aggregate.py`) を子 worktree に書く。親が job dir へ退避し、受入 (所見 3) を確かめてから新 job に当てる。
4. 結果を wave 木へ移し (`compare-recheck/`)、集計 JSON を同 dir に置く。README §2 以降に結果・判定・限定。
5. 段 6: read-only review 1 本 (README の数値・判定を生 JSON と照合、過剰・言い過ぎレンズを兼ねる)。
6. 段 7 記録 (insight・worklog fragment・decision fragment)、受入全走、段 9 land。

変異 matrix: repo の実装面の差分ゼロ (集計スクリプトは repo 外) なので免除 (DW-S04)。受入全走は行う。

## 判定規則 (最終形、insight §1 へこのまま書く)

相談 A の推奨文を採用し、親が次を足した: 対象点と job の対応 (1111 = job 0、1110 = job 1、1001 = job 6)、束縛照合に IR 本文 sha256 が元 compare JSON の値と一致すること、補助指標 (fixed10 比、5 rep 最小 > 同 job fixed10 の 5 rep 最大、元の比との差) は判定に使わない記述だけとすること。
