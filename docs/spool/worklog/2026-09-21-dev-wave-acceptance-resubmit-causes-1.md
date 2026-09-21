---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-acceptance-resubmit-causes
seq: 1
title: 受入全走を 2 回以上投入した wave の原因を直近 landed 20 wave の job dir 一次資料から分類した — 試行 2 回以上は 11 wave (test 実行 2 回以上は 5)、追加 wall 342.3 分 = 門番待ち 175.7 + 待ち手の外側 wall 97.4 + 試行間の残差 69.2、守られなかった既存手順を名指しできるのは rc=23 型 1 件 (DW-O12 の順序命令) だけ、post-claim merge 系は D1〜D4 の 7 件で門番待ち 144.1 分が支配 (診断のみ・実装 0 行、branch worktree-dev-wave-acceptance-resubmit-causes)
---

## 本文

- ユーザー依頼 (2026-09-21、dev-wave 引数の逐語は insight `verbatim/origin.md`) の範囲で 1 wave。一次資料は `output/insights/2026-09-21/acceptance-resubmit-causes/README.md` (分類表・会計の定義・分類ごとの説明と手順の名指し・entry 1774 への訂正・裁定事項・検査)。decisions / failures fragment は無し (設計判断・新しい失敗型なし)。専用 handoff は job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/HANDOFF.md`)。
- 起点 local main `5efd69367` (fresh worktree、HEAD == main、開始 gate rc 0、07:36 JST)。段構成: 軽量版 + 診断 wave の型 (段 1 → 段 3 相談 1 本 → 段 4 → 段 5 親起草 (docs のみ) → 段 6 read-only review 1 本 + 焦点再レビュー 1 本 → 7 → 8 → 9)。段 2 は省いた (file:line の実装 plan が無い)。変異 matrix は実装面差分ゼロで免除 (DW-S04)。
- 母集合: entry 1758〜1779 の dev-wave 20 本 (rulings 1751 / 1771 を除外)。**1760 [T-2501] は job dir (`~/.claude/jobs/f5ab0160/tmp`) 消失で欠測**、1758 を補足標本にした。「直近群から一次資料を回収できた 20 本」であり厳密な直近 20 本ではない。
- 結果 (§4): 試行 2 回以上 11 wave (待ち手起動 2 回以上 11、test 実行 2 回以上 5)。再試行 15 件の分類 = A 自分起因の赤 2 (25.0 分) / B 非帰属の赤 (hold 未登録) 3 (57.0) / C F1013 同型 0 / D1 待ち手の post-claim merge の terminal-merge 1 (82.6、うち門番 80.6) / D2 親 chain script の起動前 merge の実競合 1 (39.0、うち門番 38.9) / D3 同 message preflight 赤 1 (2.5) / D4 待ち手の postcheck (child 起動前の main 包含再検査) 4 (27.9) / E rc=23 型 1 (14.5) / F lease 失効 0 / 分類外 G 受入基盤 (receipt memo lock timeout → orphan hold) 1 (10.7) / 分類外 H 緑後に main が受入道具を変えて前進 (rc=92、F524) 1 (13.9)。追加 wall 342.3 分 = 再試行分 273.1 (門番待ち 175.7 + 外側 wall 97.4) + 試行間の残差 69.2。lease 待ちは 0 (D662 で待ち行列廃止)。
- 依頼の 3 手順 (§5): 受入前の main 取り込み位置は逸脱を見つけず (D2 / D3 の起動前 merge が F524 条件に当たっていたかは個別確認が要る)、DW-O18 の hold 未登録は契約どおり (1759 は判定根拠の worklog 記録が無い = 記録上の逸脱)、三軸語走査の出力の写しは該当事象なし。名指しできたのは E だけ: T-2797 が緑の後に受入結果を insight へ追記する記録 commit を積み land rc=23 → 再投入 (DW-O12「最終受入投入は DW-S07 と段 8 の commit 完了後」)。
- 段 3 相談 (codex gpt-6-astra / medium / read-only) の所見 9 件は全件 real・採用 (最重要 3: 1759 final2 / T-2803 final2 は待ち手起動前の親 script の merge で止まっており post-claim merge ではない → D を D1〜D4 に分割、`gate-loop-*.log` の門番待ちを落としていた → 追加 wall 333.3 → 342.3 分、postcheck の「親が手で再投入」は誤りで gate loop が自動投入)。段 6 review は NO-GO (must-fix 6 / should 1 / nit 1、主要表と集計は一次資料から再現) → 親の訂正 → 焦点再レビュー NO-GO (closed 7 / partial 1: 1759 の単独再走を「同一 tip」とする証拠なし) → 文を一次資料の範囲に限定して親が閉じた。3 巡目なし。
- entry 1774 (dev-wave-wall-decomp) への訂正 (§6): postcheck は「走行中に main が動いた」ではなく child 起動前の包含再検査で、失敗側の費用は外側 wall 1.2 / 2.5 分 + 再門番 2.5 / 2.3 分 (t2804 / t2153)。8〜23 分は再走側 (必要な走)。
- 裁定事項 (§8、実装しない): (1) E は DW-O12 の再確認で足りるか、(2) 焦点走の探索から漏れる exact 目録 test の扱い (T-2737 / T-2797 の独立 2 例) を別途検討するか、(3) B の 3 test の競走を別途調査するか、(4) 長い門番待ち後の競合は [T-2610] の領分か、(5) 1774 §8 項 4 の費用見積りを本資料の観測値で読み替えるか。
- 検査 (§9): 三軸語走査は既知 official 4 file × 2 holdout のみで本 wave の file に hit 0 (候補 32,091 file)、check_docs 違反なし (記録 commit 直前の tree、08:18 JST)。受入全走は記録 commit を含む最終 tip に land 前に 1 回投入し、受領証は job dir と land の記録が持つ (件数は本文へ書かない)。
- 工数: codex 3 本 (consult 1、review 1、focus 1、gpt-6-astra / medium、read-only)。親の login 実走: 走査 2 回 + check_docs 2 回。計算ノード job 0。解析 script 6 本と抽出物は job dir に置き `verbatim/scripts.sha256` で束縛 (実装面を repo に入れない)。
- 落とし穴: 門番 log は `acceptance-*.chain.log` の他に `gate-loop-*.log` (別版の gate loop) があり、glob `acceptance*` だけでは門番待ちを落とす。chain script (T-2792 由来) は待ち手起動の前に固定 SHA merge をするので、そこで止まった試行には attempt log が無い。

## 次の一手差分
