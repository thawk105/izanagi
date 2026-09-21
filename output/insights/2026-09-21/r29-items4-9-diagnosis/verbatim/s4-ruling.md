# 段 4 裁定 — 相談 (codex/s3-consult.md) 20 所見と plan v2

裁定時刻 2026-09-21 14:3x JST。裁定 inbox の再走査: wave 開始 (14:06) 後の新着なし (最新 = 13:34 の full29)。local main は `d4c88bb60` へ進んだが、
実測は起点 `d99c556df` の worktree で行い SHA を記録する (実装差分ゼロなので取り込みは受入の post-claim merge に任せる)。

## 所見の裁定

| # | 相談の判定 | 親裁定 | 処置 |
|---|---|---|---|
| 1 | real must-fix (P2 が狭い) | 採用 | 置換候補を用途名で除外しない。(a) は「構造上の上限」と「証拠で確定した数」を分けて出す (plan v2 A) |
| 2 | real must-fix (16〜20 は未証明) | 採用 | 親観測 10 の「事後の最良 4 本」は候補の列挙で下限にならない。撤回し、構造上の上限 (1 job = 1 invocation、集合走は各 wave に最低 1 本残る) だけで下限を出す |
| 3 | real must-fix (事後の緑 ≠ 単独でも緑) | 採用 | 事後候補を「省ける job 数」と書かない |
| 4 | refuted (標本固定は妥当) | 維持 | 22 / 2 / 20 は「07:38 固定標本・計算ノード焦点 log の範囲」と限定して書く |
| 5 | refuted (plan §1 の層は揃う) | 維持 | — |
| 6 | real should (行数は仮説) | 採用 | 行数は「未検証の概算」、中断・timeout・未実行結果・二重記録防止を未見積りの費用として列挙 |
| 7 | 一部 real should (20 本の検索式欠落) | 採用 | 20 本の表は再提示に使わない (局所策は T-2820 の 2 file で足り、列挙型探索は 130 本の粗い上限だけ書く)。36 / 8 本は「参照候補 / 設計上の優先候補」 |
| 8 | refuted (G の PATH・site・receipt) | 維持 | G は「経路は実在」と書く |
| 9 | 判定不能 (guard 許可) | 採用 (判定不能のまま) | 腕 C を落とすので live 確認はしない。G の即時可用性は主張しない |
| 10 | real must-fix (腕 S の cwd) | 採用 | 腕 C を落とすので 2 本目の worktree は作らない。腕 S は本 worktree を cwd (repo root) にして走らせる |
| 11 | real must-fix (C/S は同条件の比較にならない) | 採用 | 腕 C / S の対比較は行わない。D289 決定 (2) の block / randomization を満たす束ね効果の識別は、複数 invocation の実行器 (= harness) が要るので本 wave では測れないと明記する |
| 12 | real must-fix (inline `bash -c` も新 harness) | 採用 | 腕 C を scope 外にする。provenance の commit 要件とは別の判断と明記。G を運用手段に採るなら launcher は実装面 (Codex author、D2092 の先例) と費用欄に書く |
| 13 | real should (S だけで固定費は測れる、束ね効果は測れない) | 採用 | (c) は「同じ試行で払った固定費 (投入前 + 待ち + collection) と、どの手段でも残る単独 RUN」を分けて報告する。束ね後の待ち・内側 RUN の変化・完了時間短縮は未測定 (D130 決定 (2) の変異走の先例 = 内側所要差 0.15 % は引くが、焦点走への転移は主張しない) |
| 14 | refuted (L は実在、D325 理由欄は陳腐化) | 維持 | L は「dispatch 0 本の既存手段、ただし admission 不足時は dispatch へ退避、login 固有の偽赤あり」と書く。実測しない (P6 維持) |
| 15 | refuted (T-2820 が 2 例を覆う) | 維持 | 「集合に載る」と「同じ赤を必ず検出する」は分けて書く (静的目録 test なので決定的だが、再現走はしない) |
| 16 | real should (T-2820 へ接続、費用対象を限定) | 採用 | 項 9 の再提示 = 「新しい択は不要、既裁定 T-2820 の実装で覆える」。追加時間は T-2820 全体 (2 file) と `test_ccbench_spawn_sites.py` 単体を分けて出す |
| 17 | real must-fix (21 対 22、順序の限定) | 採用 | 測定集合は run-focus.sh 既定 21 file (focus-3 と同一 argv とは主張しない) と、T-2820 の 2 file を足した 23 file。21 を前後 2 回走らせて同日の揺れを見る。差は当該試行の観測値 |
| 18 | refuted (台帳は代用不可) | 維持 | 理由は「有効数字 2 桁の丸め値の和で、file 起動費・xdist 配置を含む wall 差ではない」 |
| 19 | real should (研究前進の母数) | 採用 | 「焦点走あり 8 wave で累積 wall 平均 22.1 分、待ち 74.1 %、待ちの帯別平均 8.9 秒 / 632 秒。研究完了時間の短縮は未測定」に訂正 |
| 20 | refuted (held を走らせない) | 維持 | — |

## plan v2

**A. 項 4 (a) 残件数 (再走なし、既存資料だけ):** 07:38 固定の 12 wave、計算ノード焦点 log の範囲で k = 22、単独確認済み s = 2、未確認 20。
置換 (既存走 1 本を単独走 1 file に変える) の構造上の上限 = wave ごとに min(k − s, J − 1) (J = その wave の計算ノード焦点 job 数、集合走は最低 1 本残す)。
下限 = Σ max(0, (k − s) − (J − 1))。各置換の可否 (tip・file の存在・赤の入力・集合被覆) は証明しない。

**B. 項 4 (b) 最小改修範囲:** plan §1 を「設計仮説」として再掲し、未見積りの費用を列挙。改修なしの既存経路 G / L の可否と費用 (G は launcher が実装面) を並べる。

**C. 項 4 (c) と項 9 の実測 (親、既存 runner だけ、本 worktree、直列 10 job、`--force-dispatch`):**
1. S01 = 集合 21 file (run-focus.sh 既定)
2. S02〜S08 = t2797 の変更 test 7 file の単独走 (各 1 job、changed_files.txt の順)
3. S09 = 集合 23 file (21 + `test_ccbench_spawn_sites.py` + `test_check_subprocess_bytecode_guard.py` = T-2820 適用後の形)
4. S10 = 集合 21 file (再走、同日の揺れ)
各 job の 4 区間 (投入前 = launcher の start 行 → NQSV Created、待ち、RUN、collection = Ended → launcher の end 行) を前回診断と同じ定義で取る。
env は t2797 の run-focus.sh と同じ (`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600`、`IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600`)、`-q -rf`、nproc は既定。held は設定しない。
走行中は worktree を触らない (F849)。insight は job dir で下書きし、走行後に worktree へ置く。
報告の限定: 1 試行、待ちの二峰分布の混合比や将来の短縮は推定しない。赤が出ても所要の観測として扱い、帰属は所要の議論と分ける。

**D. 変異:** 実装面の差分ゼロ (DW-S04) なので免除。受入全走は記録 commit を含む最終 tip に 1 回。

## 採らない案

- 腕 C (generic 1 job) と 2 本目の worktree — 所見 11・12。
- 列挙型探索 (130 本 / 絞り込み 20 本) の走行 — 所見 7・16。
- L の実測、held の走行、置換可能性を確かめる過去 tip の再走 — 所見 14・20・相談「実測を減らせる所」。
