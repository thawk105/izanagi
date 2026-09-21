# 受入全走を 2 回以上投入した wave の原因分類 — 直近 landed 20 wave の job dir 一次資料から (dev-wave、2026-09-21)

台帳 ID 未起票 (ユーザー依頼文がそう明記)。軽量版 + 診断 wave の型 (段 3 相談 1 本、段 6 独立 read-only レビュー 1 本、docs-only、Codex author なし = D95 の docs-only 例外、実装 0 行)。
branch `worktree-dev-wave-acceptance-resubmit-causes`、起点 local main `5efd69367` (開始 gate rc 0 = `startup-gate.log` 2026-09-21 07:36 JST)、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes`
(brief `s1-brief.md`、草稿 `s1-prevention-draft.md`、段 4 裁定 `s4-ruling.md`、codex の prompt / 報告 `codex/`、抽出物 `timeline-<entry>.txt` / `inventory.txt`、解析 script `*.py` — script と抽出物は実装面 (D95) / 機械出力なので repo へ入れず `verbatim/scripts.sha256` で束縛)。

## 1. 依頼 (逐語は `verbatim/origin.md`)

直近 landed wave 20 本の job dir の `acceptance-receipt-*.json` と `acceptance-*.log` から、受入全走を 2 回以上投入した wave の原因を 6 分類 (A 自分起因の赤 / B 非帰属の既知間欠赤 (flaky hold 未登録) / C F1013 同型 / D post-claim merge の terminal-merge / E 記録 commit 後の tip 変更 (rc=23 型) / F lease の失効) し、各分類の件数と追加 wall (受入 1 走 + lease 待ち) を出し、防げた分類ごとに既存手順 (受入前の main 取り込み位置、DW-O18 の hold 登録、三軸語走査の出力を insight に写さない) の何が守られなかったかを書く。受入の受理集合・門番・hold の意味論は変えない。診断だけ。gate・台帳・一般化の追加は scope 外。結果は裁定パッケージ。

## 2. 段 1 — 20 wave の同定と資料

- 母集合: worklog の entry 番号 (fold が land 順に付ける) で直近から遡り、dev-wave の entry を 20 本。entry 1758〜1779 のうち `/rulings` の 1751 / 1771 は対象定義で除外。**1760 [T-2501] は job dir (`~/.claude/jobs/f5ab0160/tmp`) が消失しており欠測**。欠測を埋めるため 1 本前の 1758 [T-2153] を補足標本として加えた。したがって本資料の「20 本」は**直近群から一次資料を回収できた 20 本**であり、厳密な直近 20 本 (1760 を含む) ではない。対応表は `verbatim/waves.txt`。
- 一次資料 (job dir、`/work/1/SFC/tanab/dev-wave-jobs/<wave>/`): 門番 loop の log (`acceptance-<label>.chain.log`、または `gate-loop-<label>.log`)、待ち手の attempt log (`acceptance-<label>-<n>.log` の `IZANAGI_ACCEPTANCE_ATTEMPT_V1` 行と `error: stage=… rc=…` 行)、pytest の child log (`acceptance-child-<label>-<n>.log` の `FAILED` 行と集計行)、受領証 (`acceptance-receipt-<label>-<n>.json` の `verdict` / `tested_main` / `tested_tip` / `red_nodeids` / `flake_nodeids`)、`acceptance-<label>-<n>.started.txt` / `.finished.txt`、land 記録 (`land*.json` の `status` / `reason` / `tested_tip_sha` / `landing_tip_sha`、`land*.log` / `*.stderr` の rc と `lease_*` 行) は再投入の原因が land 側にある試行だけ引いた。
- 帰属 (自分起因 / 非帰属) の判定は当該 wave の記録 (worklog entry、job dir の handoff / 判定 memo / insight) を採り、本 wave は再判定しない (規律 7)。
- 抽出は script (`extract.py` → `timeline-<entry>.txt`、`classify.py` → `verbatim/classification.md`) で行い、時刻は file の内容 (started / finished の ISO 時刻、log の時刻欄) と mtime から採った (推定なし)。

## 3. 用語と会計の定義 (段 3 所見 1・4・5 で確定)

- **試行** = 門番 loop の 1 attempt。待ち手 (`tools/dev_wave_wait.py acceptance`) の起動に至ったか (列「待ち手」)、pytest の child が走ったか (列「test」) を分けて示す。親の chain script (`run-acceptance-gated.sh`、T-2792 由来) は待ち手起動の前に固定 SHA で main を merge するので、その merge で止まった試行には attempt log が無い。
- **門番待ち** = その試行の門番 loop の最初の観測行 → 待ち手の `started.txt` (親 script の起動前 merge 数秒を含む)。門番は `leaders ≤ 1 ∧ 1 分 load ≤ 60` (job dir の script)。
- **外側 wall** = `started.txt` → `finished.txt`。待ち手の外側 wall であり test の実所要ではない。待ち手起動なしの試行は chain の attempt 行 → 停止行。
- **追加 wall** (wave ごと) = (最終緑の finished − 最初の試行の門番開始) − (最終緑 1 試行の門番待ち + 外側 wall)。再試行分 (門番待ち + 外側 wall の和) と、試行間の残差 (親の判定・fix・記録 commit・land 試行などが入るが、本資料では内訳を裏付けない) に分ける。
- **lease 待ち** = 0。受入 lease の待ち行列は D662 で廃止され、待ち手は lease を単発・非ブロッキングで扱う (`DW-O27`)。依頼の「受入 1 走 + lease 待ち」には「外側 wall + 門番待ち (lease 待ちは 0、門番待ちは別掲)」で答える。
- T-2817 の `ref` 走は wave の測定対象 (受入の参照走、`handoff-final.md` §1.3) で land に使っていないので、再投入の会計から除外し一覧には残す。T-2817 の `final2` は門番 loop を 1 観測で中止 (走なし) なので同じく除外。

## 4. 結果

### 4.1 試行ごとの分類表 (`verbatim/classification.md`、時刻は JST)

| entry | wave | 試行 | 門番待ち (分) | 外側 wall (分) | 待ち手 | test | 結果 | 分類 | 備考 |
|---|---|---|---|---|---|---|---|---|---|
| 1779 | t2797-b5-contrast | final | 2.3 | 7.6 | 有 | 有 | red-own | A 自分起因の赤 | `test_ccbench_spawn_sites` 2 件 (process 起動点の exact 目録) → fix4 `517fd5451` |
| 1779 | t2797-b5-contrast | final2 | 2.4 | 12.1 | 有 | 有 | green | E rc=23 型 | 緑 tip `088bbdec7` の後に記録 commit `cf1c90e1f` → land rc=23 → final3 |
| 1779 | t2797-b5-contrast | final3 | 2.3 | 22.9 | 有 | 有 | green | (最終緑) | landed 05:26 |
| 1777 | t2817-acceptance-bottleneck-3 | ref | 2.9 | 11.6 | 有 | 有 | green | (診断の参照走) | 会計から除外、一覧には残す |
| 1777 | t2817-acceptance-bottleneck-3 | final | 2.6 | 9.7 | 有 | 有 | red-nonattr | B 非帰属の赤 | `test_t2620_orphan_mixed_is_rejected` 1 件 (`/proc` 走査の競走、entry 1724 で同型観測)、単独再走 1 passed |
| 1777 | t2817-acceptance-bottleneck-3 | final2 | (中止) | — | 無 | 無 | aborted | (投入前中止) | gate 行 1 本のみ、会計から除外 |
| 1777 | t2817-acceptance-bottleneck-3 | final3 | 4.2 | 12.1 | 有 | 有 | red-nonattr | B 非帰属の赤 | `test_t810_coordinator` 2 件 (worktree 登録消失、entry 1756 [T-2766] で記録の型; 03:19 に T-2814 が land)、単独再走 45 passed |
| 1777 | t2817-acceptance-bottleneck-3 | final4 | 2.5 | 22.8 | 有 | 有 | green | (最終緑) | land 初回 rc=23 は監査列の順序 (`--reverse` 抜け) で argv 修正のみ、受入再投入なし |
| 1776 | t2810-g1-launch-validation | final | 5.9 | 4.8 | 有 | 無 | infra | G 分類外: 受入基盤 | collection 段の receipt memo lock timeout → 兄弟 shard 中断 → orphan hold。test 0 件、非帰属 (job dir `acceptance-red-final-1.md`) |
| 1776 | t2810-g1-launch-validation | final2 | 2.6 | 11.8 | 有 | 有 | green | (最終緑) | |
| 1775 | t2814-cleanup-command | final-1 | 12.4 | 0.8 | 有 | 無 | postcheck | D4 待ち手の postcheck | `gate-acceptance-loop.sh` が attempt 2 を自動投入 |
| 1775 | t2814-cleanup-command | final-2 | 2.0 | 24.5 | 有 | 有 | green | (最終緑) | |
| 1770 | t2344-closure-stage | final | 2.9 | 12.3 | 有 | 有 | red-own | A 自分起因の赤 | `test_formal_loader_rejects_real_exploration` 1 件 (受理集合の変化) → fix 2 |
| 1770 | t2344-closure-stage | final2 | 1.8 | 12.3 | 有 | 有 | green | (最終緑) | |
| 1769 | t2803-provenance-receipt | final | 2.5 | 11.4 | 有 | 有 | green | H 分類外: 緑後の受入道具の前進 | tested main `1cc303534` → land 時 main `6305f2d05`、land script rc=92 (F524) |
| 1769 | t2803-provenance-receipt | final2 | 2.4 | 0.1 | 無 | 無 | merge-preflight | D3 親 script の起動前 merge の preflight 赤 | 取り込む main が実装面を含み merge message に `role=author` が無い。親が Codex 署名付き merge を作って再投入 |
| 1769 | t2803-provenance-receipt | final3 | 2.3 | 21.8 | 有 | 有 | green | (最終緑) | |
| 1768 | t2804-provenance-timeout-contract | final-1 | 2.6 | 1.2 | 有 | 無 | postcheck | D4 待ち手の postcheck | `gate-acceptance-loop.sh` が attempt 2 を自動投入 |
| 1768 | t2804-provenance-timeout-contract | final-2 | 2.5 | 9.9 | 有 | 有 | green | (最終緑) | |
| 1767 | t2243-collection-diag | final att1 | 2.9 | 1.3 | 有 | 無 | postcheck | D4 待ち手の postcheck | `run-acceptance-gated.sh` が attempt 2 を自動投入 |
| 1767 | t2243-collection-diag | final att2 | 2.5 | 9.8 | 有 | 有 | green | (最終緑) | |
| 1761 | paper-story-20260920b | final | 80.6 | 2.0 | 有 | 無 | terminal-merge | D1 待ち手の post-claim merge の terminal-merge | `reason=terminal-merge` (実競合)、親が固定 SHA で main を merge して再投入 |
| 1761 | paper-story-20260920b | final2 | 18.5 | 12.2 | 有 | 有 | green | (最終緑) | |
| 1759 | cleanup-backup-loss-record | final | 8.8 | 19.6 | 有 | 有 | red-nonattr | B 非帰属の赤 | `test_real_repo_upgrade_writer_drains_overlapping_reader_stream[legacy]` 1 件 (`'blocked'=='upgraded'`、同居負荷の競走)、非帰属判定は handoff のみ、焦点走 2/2 緑 |
| 1759 | cleanup-backup-loss-record | final2 | 38.9 | 0.1 | 無 | 無 | merge-conflict | D2 親 script の起動前 merge の実競合 | `output/insights/2026-09-19/k2-loop-round3/README.md` ([T-2795] の追記節と衝突)、親が両方保持で merge |
| 1759 | cleanup-backup-loss-record | final3 | 6.8 | 12.1 | 有 | 有 | green | (最終緑) | |
| 1758 | t2153-witness-requested-us | final att1 | 4.2 | 2.5 | 有 | 無 | postcheck | D4 待ち手の postcheck | behind=53 の起動前 merge の後、`run-acceptance-gated.sh` が attempt 2 を自動投入 |
| 1758 | t2153-witness-requested-us | final att2 | 2.3 | 9.3 | 有 | 有 | green | (最終緑) | |

受入 1 試行で済んだ wave (9 本、job dir の attempt log と試行番号付き receipt が各 1 本): 1778 branch-residue-cleanup、1774 wall-decomp、1773 paper-story-20260921、1772 paper-abstract-conclusion-ja、1766 t2807-b8-prerun、1765 t2813-o26-inventory、1764 k2-loop-originals-lost-downstream、1763 fig13-b10-waiting-grid、1762 paper-related-work-ja。attempt log が 1 本であることは「保存済み記録では 1 試行」を示し、抽出器が拾わない起動前停止の不存在までは証明しない。

### 4.2 wave ごとの追加 wall (分)

| entry | wave | 試行数 | うち待ち手起動 | うち test 実行 | 総受入 wall | 最終緑 1 試行 | 追加 wall | うち再試行分 | (門番待ち) | (外側 wall) | うち試行間の残差 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1779 | t2797-b5-contrast | 3 | 3 | 3 | 61.5 | 25.2 | 36.3 | 24.3 | 4.7 | 19.6 | 11.9 |
| 1777 | t2817-acceptance-bottleneck-3 | 3 | 3 | 3 | 61.6 | 25.4 | 36.3 | 28.6 | 6.8 | 21.7 | 7.7 |
| 1776 | t2810-g1-launch-validation | 2 | 2 | 1 | 34.6 | 14.4 | 20.2 | 10.7 | 5.9 | 4.8 | 9.5 |
| 1775 | t2814-cleanup-command | 2 | 2 | 1 | 40.7 | 26.5 | 14.2 | 13.2 | 12.4 | 0.8 | 1.0 |
| 1770 | t2344-closure-stage | 2 | 2 | 2 | 42.1 | 14.1 | 28.0 | 15.2 | 2.9 | 12.3 | 12.8 |
| 1769 | t2803-provenance-receipt | 3 | 2 | 2 | 52.8 | 24.1 | 28.7 | 16.4 | 4.9 | 11.4 | 12.3 |
| 1768 | t2804-provenance-timeout-contract | 2 | 2 | 1 | 17.2 | 12.4 | 4.8 | 3.8 | 2.6 | 1.2 | 1.0 |
| 1767 | t2243-collection-diag | 2 | 2 | 1 | 16.5 | 12.3 | 4.2 | 4.2 | 2.9 | 1.3 | 0.0 |
| 1761 | paper-story-20260920b | 2 | 2 | 1 | 118.9 | 30.6 | 88.2 | 82.6 | 80.6 | 2.0 | 5.6 |
| 1759 | cleanup-backup-loss-record | 3 | 2 | 2 | 93.5 | 18.8 | 74.7 | 67.4 | 47.7 | 19.7 | 7.3 |
| 1758 | t2153-witness-requested-us | 2 | 2 | 1 | 18.3 | 11.6 | 6.7 | 6.7 | 4.2 | 2.5 | 0.0 |
| 合計 (11 wave) | | | | | | | **342.3** | **273.1** | **175.7** | **97.4** | **69.2** |

20 wave のうち**試行 2 回以上 = 11 wave** (待ち手起動 2 回以上 = 11、**test 実行 2 回以上 = 5**: 1779 / 1777 / 1770 / 1769 / 1759)。追加 wall 342.3 分のうち門番待ち 175.7 分が最大の項で、うち 119.6 分 (7,174 秒) は 1761 と 1759 の 2 試行 (80.6 / 38.9 分) に集中する。門番待ちは分類 (原因) の帰結ではなく、再試行のたびに払う待ちで、その長さは同時刻の他 wave の受入 (leaders) と login の load で決まる (本資料はその内訳を裏付けない)。

### 4.3 分類ごとの件数と再試行分の wall (分)

| 分類 | 件数 | うち待ち手起動 | うち test 実行 | 門番待ち | 外側 wall | 計 |
|---|---|---|---|---|---|---|
| A 自分起因の赤 (fix → 最終 tip で再投入) | 2 | 2 | 2 | 5.1 | 19.9 | 25.0 |
| B 非帰属の赤 (hold 未登録) | 3 | 3 | 3 | 15.6 | 41.3 | 57.0 |
| C F1013 同型 (三軸語走査の出力 file が holdout hit) | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| D1 待ち手の post-claim merge の terminal-merge (実競合) | 1 | 1 | 0 | 80.6 | 2.0 | 82.6 |
| D2 親 chain script の起動前 merge の実競合 | 1 | 0 | 0 | 38.9 | 0.1 | 39.0 |
| D3 親 chain script の起動前 merge の message preflight 赤 | 1 | 0 | 0 | 2.4 | 0.1 | 2.5 |
| D4 待ち手の postcheck (child 起動前の main 包含再検査で停止) | 4 | 4 | 0 | 22.1 | 5.7 | 27.9 |
| E rc=23 型 (記録 commit 後の tip 変更) | 1 | 1 | 1 | 2.4 | 12.1 | 14.5 |
| F lease の失効 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| G 分類外: 受入基盤 (collection 段の receipt memo lock timeout → orphan hold) | 1 | 1 | 0 | 5.9 | 4.8 | 10.7 |
| H 分類外: 緑後に main が受入道具を変えて前進 (land script rc=92、F524) | 1 | 1 | 1 | 2.5 | 11.4 | 13.9 |
| 合計 | 15 | 13 | 7 | 175.7 | 97.4 | 273.1 |

依頼の D「post-claim merge の terminal-merge」を待ち手の `reason=terminal-merge` に限れば 1 件 (D1)。main 取り込みの競走の族として D1〜D4 を合わせると 7 件・152.0 分 (うち門番待ち 144.1 分 = 8,647 秒)。test を実際に走らせた再試行は 7 件 (A 2 + B 3 + E 1 + H 1) で外側 wall 84.7 分。

## 5. 各分類の説明と、守られなかった既存手順

依頼が名指しした 3 つの既存手順への回答を先に置く。

| 既存手順 | 結論 |
|---|---|
| 受入前の main 取り込み位置 (`DW-O20`: 取り込みは `tools/dev_wave_wait.py acceptance` の post-claim merge。待ち手・launcher・runner の bytes を変える前進は先に取り込む、F524) | **逸脱は見つからない**。D1 (1761) の停止位置は正本どおり待ち手の post-claim merge。D2 / D3 (1759、T-2803) は親の chain script が待ち手起動前に固定 SHA で merge する運用 (job dir の script、正本の命令ではない) で止まった。その事前取り込みが F524 の条件 (受入道具の bytes を変える前進) に当たっていたかは各件で個別確認が要り、本資料は確認していない |
| DW-O18 の hold 登録 (再赤 / 決定的赤でも hold 登録簿へ登録しない、F1000) | **hold 未登録は契約どおり** (B の 3 件とも)。ただし (i) 1759 は DW-O18 の「判定し根拠を worklog へ残す」を満たしていない (判定は job dir の handoff のみ、worklog entry 1759 本文に無い) — 記録上の逸脱で、再投入の原因ではない。(ii) T-2817 の 2 件は同一 tip の単独再走で非再現を確認し (entry 1777)、その後の受入再投入は判定の追記 commit を挟んだ別 tip で行われた。1759 は焦点走 (計算ノード) 2/2 緑で非再現とし (handoff)、その焦点走の tip が赤の tip と一致するかは資料から未確認。その後の受入再投入は main 取り込み (競合解消 merge) を挟んだ別 tip。DW-O18 の「同一 tip で各 1 回だけ」への適合は本資料では評価しない |
| 三軸語走査の出力を insight に写さない (F1013) | **該当事象なし** (対象標本で同型の再投入 0 件)。全 wave が遵守したことの証明ではなく、F1013 の再発 [T-2792] (entry 1755) は対象外の標本 |

分類ごと:

- **A 自分起因の赤 (2 件、防げた可能性あり):** (T-2797) 焦点走の file 集合 (変更 test + consumer + `DW-O26` の inventory 4 群 + メタ test の 21 file) は指定どおり実施したが、赤を出した `test_ccbench_spawn_sites.py` (process 起動点の exact 目録) は 4 群に無く、consumer 探索でも引けなかった (insight `t2797-b5-contrast/README.md` §4 fix4)。[T-2737] (define 目録) と同型で独立 2 例。(T-2344) 赤 test は変更 symbol を参照せず外部 root の記録済み campaign を読むため参照関係で引けなかった。当該 wave が F474 の再発として記録し、外部 root を読む test file の追加はこの事象の後の対応。どちらも「後から足された手順の不履行」とは判定しない。
- **B 非帰属の赤 (3 件):** T-2817 の 2 件は既知型の根拠がある (`/proc` 走査の競走は entry 1724、worktree 登録の消失は entry 1756 [T-2766])。1759 の 1 件は非帰属判定 (docs 差分から到達不能、焦点走 2/2 緑) が handoff にあるが、既知性の先行根拠は提示されていない。T-2817 の 2 件は同一 tip の単独再走で、1759 は焦点走 2/2 緑で非再現を確認し (1759 の焦点走の tip 一致は資料から未確認)、その後の受入再投入はいずれも記録 commit / main 取り込みを挟んだ別 tip で行った (§5 冒頭の表 (ii))。hold 未登録は契約どおり。既存手順による防止可能性は本資料では確定できない (非帰属判定は防止不能の証明ではない)。
- **C F1013 同型 (0 件)。**
- **D1 待ち手の post-claim merge の terminal-merge (1 件、1761):** 門番待ち 80.6 分の間に main が進み、post-claim merge が実競合で停止 (`classification=merge reason=terminal-merge`)。親が固定 SHA で main を取り込み直して再投入した (F902 にも同型の停止と固定 SHA での解消例がある)。停止位置は正本 (`DW-O20`) と一致する。
- **D2 親 chain script の起動前 merge の実競合 (1 件、1759):** 競合 file は `output/insights/2026-09-19/k2-loop-round3/README.md` で、同時期に landed した [T-2795] (entry 1754) の追記節と衝突。競合を観測した事実だけを書く (段 1 の所有確認を履行したかは資料から未確認)。
- **D3 親 chain script の起動前 merge の message preflight 赤 (1 件、T-2803):** 取り込む main が実装面 (`tools/check_ai_provenance.py` と test) を含み、自動 merge message に `role=author` が無いので `check_ai_provenance.py --message-file` が赤 (直接の根拠は chain log の preflight 診断。F902 の merge-composition-audit は類例)。直前の land script rc=92 が「incoming changes runner/waiter/reds checker/land」と受入道具の変更を名指ししており、親は Codex 署名付き merge を先に作って再投入した。走なし、計 2.5 分 (門番 2.4 + 外側 0.1)。
- **D4 待ち手の postcheck (4 件):** `tools/dev_wave_wait.py` は post-claim merge の commit 後・child 起動前に main 包含を再検査し (`_behind_count`)、behind ≠ 0 なら `terminal-postcheck` で停止する。前進の瞬間 (merge 中か履歴監査中か) は資料から特定できない。4 件とも child は走らず、門番 loop (`run-acceptance-gated.sh` または `gate-acceptance-loop.sh`) が attempt 2 を自動投入した。観測値は 2 つに分けて書く: 失敗側の外側 wall 0.8〜2.5 分 (4 件計 5.7 分、§4 の分類別会計に入る)、attempt 2 の再門番 2.0〜2.5 分 (122 / 152 / 151 / 140 秒。§4 では最終緑 1 試行の門番待ちに入り、分類別会計には加算しない)。**entry 1774 (dev-wave-wall-decomp) の「terminal-postcheck (走行中に main が動いた) … 各 8〜23 分の再走」は、再走側 (必要な走) を費用と読んでいる。**
- **E rc=23 型 (1 件、T-2797、守られなかった手順を名指しできる):** 緑 (tested tip `088bbdec7`) の後に「insight §7 へ受入結果を追記」する記録 commit `cf1c90e1f` を積んで land → `tools/dev_wave_land.py` の `_forward_main_merge_topology` が「tested tip → landing tip の間は main 前方 merge だけ」の検査で rc=23 (`forward main merge first-parent commit must have exactly two parents`)。守られなかった既存手順は `docs/dev-wave/operations.md` `DW-O12` の「land 対象 tip への最終受入投入は DW-S07 と段 8 の commit 完了後に行う——取り違えると記録 commit が tested tip から漏れ land が rc=23 になる」と、直近 wave が採っている「受入全走は記録 commit を含む最終 tip に land 前に 1 回投入し、受領証は job dir と land の記録が持つ (件数は本文へ書かない)」(entry 1770 / 1774 / 1775)。§4 の基準での費用は final2 の 14.5 分 (門番 2.4 + 外側 12.1)。final3 の 25.2 分 (門番 2.3 + 外側 22.9) は原因判明後の最終緑の観測 wall で、分類別会計には加算しない。
- **F lease の失効 (0 件):** 11 wave の attempt log・chain log・land 記録に lease 失効を理由とする停止行は無い (1770 の land stderr に `lease_renew state=stale` はあるが land は成功)。`lease_renew state=…` の値だけでは TTL 内・解放・未取得を弁別できないので、「失効を理由にした再投入は観測されない」にとどめる。
- **G 分類外: 受入基盤 (1 件、T-2810):** shard-1 が collection 終了時の `conftest._wait_early_memo_job` → receipt memo lock 取得で `memo publication timeout` (errno 110) → INTERNALERROR、兄弟 shard 2 本が signal 15 で中断され orphan hold (request 14171 / 14172)。test 0 件、非帰属 (entry 1776)。orphan 終端待ち → hold 退避 → 同一内容で再投入。既存手順による防止可能性は本資料では確定できない。
- **H 分類外: 緑後に main が受入道具を変えて前進 (1 件、T-2803):** 緑 (23:28) の 3 分後の land 時点で main が [T-2804] (land の契約変更) を取り込んでおり、land script が rc=92 で止めた。F524 (待ち手・launcher・runner の bytes を変える前進は先に取り込む) どおり再投入が要る。本資料では防止可能性を確定できない。

## 6. entry 1774 (dev-wave-wall-decomp) の記述への訂正

- 同 insight §3 / §8 の「terminal-postcheck rc=70 (走行中に main が動いた)」は「child 起動前の main 包含再検査で停止」に、「各 8〜23 分の再走」は「失敗側の外側 wall は t2804 1.2 分 / t2153 2.5 分、attempt 2 の再門番は 2.5 / 2.3 分で、8〜23 分は再走側 (必要な走)」に読み替える。件数 (t2804・t2153 の各 1 回) は一致。intro (2 回) は本資料の対象外。
- 同 insight の「story は terminal-merge 1 回、backup は赤 1 回と merge conflict 1 回」は本資料の D1 / B / D2 と一致する。

## 7. 段 3 相談と段 4 裁定 (`verbatim/s3-consult.md`、`verbatim/s4-ruling.md`)

段 3 (codex gpt-6-astra / medium / read-only、07:51〜07:57 JST) は所見 9 件 (must-fix 5)。段 4 で 9 件すべて real・採用: (1) 1759 final2 / T-2803 final2 は待ち手起動前の停止 → D を D1〜D4 に分割、(2) postcheck の「merge 中」「親が手で再投入」を訂正 (gate-loop log で自動投入を実測)、(3) 帰属判定と既知性を分離、(4) `gate-loop-*.log` の門番待ちを補い 333.3 → 342.3 分、(5) 「走 wall」→「外側 wall」、lease は「失効を理由にした再投入は観測されない」に限定、(6) 1759 の worklog 記録漏れは再投入の原因と別記、(7) A の包括断定を狭める、(8) 固定費・防止不能の一般化を削り依頼の 3 手順に明示回答、(9) 母集合 (T-2501 欠測、1758 補足) と「11 / 5」の意味を明示。

## 8. 裁定パッケージ候補 (実装しない。依頼: gate・台帳・一般化の追加は scope 外)

裁定事項として返す。変更箇所・実装方法・費用は本資料からは導けないので書かない。

| # | 裁定事項 | 資料から示せる規模 | 本資料が言えること |
|---|---|---|---|
| 1 | E (記録 commit 後の tip 変更): 既存手順 `DW-O12` の順序命令と「受領証は job dir と land の記録が持つ」運用の再確認で足りるとするか | 20 wave で 1 件、§4 基準で 14.5 分 | 守られなかった手順を名指しできる唯一の分類。新規の正本追加を要するかは資料から言えない |
| 2 | A (自分起因の赤): 既存の焦点走の探索 (`DW-O26` の inventory 4 群 + consumer 探索) から漏れる exact 目録 test の扱いを別途検討するか | 20 wave で 1 件 (T-2797)。同型の先例 [T-2737] (define 目録) と合わせ独立 2 例 | 一般化の追加は本依頼の scope 外。本資料は事象の同型性までを示す |
| 3 | B (非帰属の赤): 3 件が名指しした test の競走 (`/proc` 走査、worktree 登録の列挙、upgrade writer) を別途調査するか | 3 件・57.0 分 (20 wave 中)。hold 登録は F1000 で撤回済みで選択肢に無い | 調査の要否だけ。方法・費用は資料から導けない |
| 4 | D1 / D2 (長い門番待ちの後の競合、80.6 / 38.9 分): 門番待ち自体を扱うか | 2 件・121.6 分 (うち門番待ち 119.6) | 門番待ちは [T-2610] (門番の飢餓) の領分。本資料は競合が門番待ちの後に起きた事実までを示す |
| 5 | D4 (postcheck 4 件・27.9 分、うち初回門番 22.1・失敗側外側 5.7): entry 1774 §8 項 4 の裁定候補の費用見積りを本資料の観測値で読み替えるか | 4 件 | postcheck は tested_main 束縛の検査そのもの。減らす手は本資料に無い |

## 9. 検査・受入 (記録 commit 直前の tree での実測。本節を書き足す前の tree で測り、本節の追加は散文のみ)

- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、2026-09-21 08:18 JST、job dir `three-axis-scan-2.log`): file-level conjunction の候補集合 32,091 file。hit は既知の official 成果物 4 file × 2 holdout (rr80 / rr20) のみで rc=1 はその既知 hit による。本 wave の file (`output/insights/2026-09-21/acceptance-resubmit-causes/` 配下) への hit 0。走査器の候補集合は `search` サブコマンドのもので、t080 e2e の `_assert_search_pass` とは同一でない (F1013) — 後者は受入全走が検出者。
- `python3 tools/check_docs.py` (同時刻、job dir `check_docs-2.log`): 違反なし、rc 0。
- `git diff --check` の末尾空白抵触を避けるため、verbatim の codex 報告 2 file (`s3-consult.md`、`s6-review.md`) の行末空白だけを除去した (可視文字不変、原文 sha256・bytes・除去行は `verbatim/NORMALIZATION.md`、原文は job dir に残る)。
- 記録 commit 後の再走 (F34) は受入全走が兼ねる (`test_check_docs.py` と s8b holdout の t080 系が同じ検査を含む)。
- 受入全走: この記録 commit 時点では未実施。記録 commit を含む最終 tip へ land 前に 1 回投入する (門番付き chain、結果は job dir の受領証と land の記録が持つ。件数は本文へ書かない)。

## 9b. 段 6 レビューの所見と処置 (DW-O16 の対応表、`verbatim/s6-review.md`)

段 6 (codex gpt-6-astra / medium / read-only、08:09〜08:14 JST) は NO-GO、must-fix 6 / should 1 / nit 1。表の主要集計 (342.3 / 273.1 / 175.7 / 97.4 / 69.2、分類別の件数と分、11 / 5、started / finished 50 個) は一次資料から再現された。

| # | 所見 | 処置 | 状態 |
|---|---|---|---|
| 1 | 門番待ちの丸め (119.5 → 119.6、144.0 → 144.1) と D4 の再門番の範囲 (2.0〜2.5 分) | §4.2 / §4.3 / §5 D4 / §6 を秒の加算で訂正 | closed |
| 2 | E の 25.2 分と D4 の再門番が §4 の会計基準 (最終緑側を控除) と混在 | E は §4 基準の 14.5 分に統一し 25.2 分は最終緑の観測 wall と明記。D4 は失敗側外側 wall と再門番を別の観測値として記載。D3 は計 2.5 分 | closed |
| 3 | B の「同一 tip で受入を再投入」は一次記録と逆 (単独再走が同一 tip、受入再投入は追記 commit 後の tip) | §5 冒頭の表 (ii) と B 段落を訂正、DW-O18 の同一 tip 条件への適合は評価しないと明記 | closed |
| 4 | 「守られている」「防げない」の断定が資料より強い | main 取り込み位置は「逸脱は見つからない、D2/D3 の F524 条件は個別確認が要る」、B / G は「防止可能性は本資料では確定できない」に統一。§8 の「変更は受理集合に触れる」を削除 | closed |
| 5 | §8 の候補 2・3 が変更箇所・実装方法・未測定費用を指定 | §8 を裁定事項の表に改め、方法・費用を削除 | closed |
| 6 | §9 が値なし前方参照 | 記録 commit 直前の tree で実測した値を記載 | closed |
| 7 (should) | 順序命令の節は DW-O12 (DW-O17 ではない)。F902 の射程は台帳の実装面 merge | §5 E を DW-O12 に、D1 / D3 の F902 を類例に改めた | closed |
| 8 (nit) | 「green receipt が各 1 本」→「試行番号付き receipt が各 1 本」 | §4.1 を訂正 | closed |

焦点再レビュー 1 本 (`verbatim/s6-focus.md`、08:19〜08:23 JST) は NO-GO: 所見 1・2・4〜8 は closed (派生値は一次資料の時刻から再計算して一致: 7,174 / 8,647 秒、D4 の再門番 122 / 152 / 151 / 140 秒と失敗側外側 46 / 71 / 79 / 147 秒 = 計 343 秒、E 870 秒 = 14.5 分、D3 149 秒 = 2.5 分)、所見 3 は partial (1759 の単独再走まで「同一 tip」とする証拠が無い — handoff は焦点走 2/2 緑としか書かない) → §5 冒頭の表 (ii) と B 段落を T-2817 の 2 件に限定して親が閉じた (根拠: `dev-wave-cleanup-backup-loss-record/HANDOFF.md` 24 行は tip を書かない)。新規 1 (should、本節の工程記録の更新) は本文で反映。3 巡目は投げていない (残件は文の限定だけで派生値に触れない)。

## 10. 言わないこと

- 20 本は 2026-09-20 19:45 〜 09-21 05:21 JST の連続帯の標本で、別日の分布・混雑を代表しない。門番待ちの長さは同時刻の他 wave と login の load に依存し、本資料はその内訳を裏付けない。
- 「追加 wall」の残差 (69.2 分) は親の判定・fix・記録 commit・land 試行を含むが、本資料は内訳を裏付けない。
- 外側 wall は test の実所要ではない (待ち手の外側)。
- 防止可能性は「守られなかった手順を名指しできる」(E) と「名指しできない」(B / G / H / D4) を分けて書いたが、名指しできない分類が防げないことの証明ではない。
- 1 試行で済んだ 9 wave について、抽出器が拾わない起動前停止 (attempt log の無い停止) の不存在は証明していない。
