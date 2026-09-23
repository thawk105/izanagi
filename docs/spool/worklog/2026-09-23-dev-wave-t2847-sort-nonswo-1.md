---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: dev-wave-t2847-sort-nonswo
seq: 1
title: [T-2847] 残り (2) のうち sort-nonswo (V07) を gate と同じ供給経路で build し、stock 対照つきで計算ノード実走した — 17 要素の壊し build は hang でなく SIGSEGV で別の層 (process の異常終了)、16 要素は S、対照 2 本は S (insight のみ、branch worktree-dev-wave-t2847-sort-nonswo)
---

## 本文

- 依頼はユーザー直接起動の `/dev-wave [T-2847]` (残り (2) のうち sort-nonswo (V07) の 1 行だけ)。並走 wave `dev-wave-t2847-mutation-run` (entry 1854) は同じ残り (2) の別の行を持ち、sort-nonswo を段 1 で scope 外とした。本 wave は gate の登録表・`patches/` に触れておらず、[T-2847] の項の更新は相手の着地 (main da5dc0258) を取り込んでから書いた (merge b09b04411)。
- 記録 = insight `output/insights/2026-09-23/t2847-sort-nonswo/README.md` (commit fa3f94eff)。repo の実装面の差分はゼロで、起動器 (Codex author、fix 2 巡) は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py` に置き、逐語を insight の `verbatim/launcher-source.md` に残した。変異 matrix は DW-S04 により免除。
- 素材: V07 を 1 job (request 21250.nqsv、bnode017、Elapse 88 s、pin `e9e477ca`) で実走した。build は gate と同じ `-DCCBENCH_SORT_VARIANT=<v>` の経路で、`CMakeCache.txt` と実コンパイル定義で値 1 / 0 を照合した (前回の「driver の build 経路と gate の供給経路が一致しない」を解消)。投入前に固定した事前登録表の規則を起動器が機械的に当てた分類は、R4 (壊し・17 要素) = 別の層で検出 (process の異常終了。hang の主予測に反して 0.013 s で SIGSEGV)、R3 (壊し・16 要素) = 期待どおり S (設計書と D42 の「16 以上で hang」は再現せず、libstdc++ 11 の「16 を超えたら分割」と一致)、stock 対照 R1・R2 = S。verifier の判定は V07 を捕まえていない (盲点の行のまま)。SIGSEGV の原因は未検証。
- 段 1 で親が見つけた新事実: 設計書 §4.3 と D42 の閾値「16 要素以上」は、libstdc++ 11 の source では「16 を超える」(17 以上)。16 と 17 の 2 条件を事前登録して弁別した。
- 記録の直前に local main の pin が `68106660` へ進んだ ([T-2858])。`e9e477ca` との差は `cc/mocc/transaction.cc` だけで silo の source は同じ。走らせ直していない。
- レビュー: 段 3 相談 1 本 (所見 9 件、real 6・部分的 3・refuted 0、全採用。R4 の期待を「未定義動作、主予測 hang」に改め、分類規則を順序付きにした)。段 6 は起動器の review 1 本 (NO-GO、must 1・should 3・nit 1、全採用) → fix1 → 焦点再レビュー (NO-GO、新 must 2) → fix2 → 親が login で実機確認して閉じた (空でない out-dir は rc=2 で既存 file 不変、login 拒否は rc=2 で JSON 記録)。insight の review 1 本 (NO-GO、must 1 = R4 の verifier の I を「verdict が出ない」と誤記、should 2) を採用して直した。一次資料は insight の `verbatim/`。
- 同じ依頼文の dev-wave が 22:02 JST に重複起動され (session bcd1e7)、本 wave の handoff を見て無操作で終了した (peer 通知)。
- 工数: codex 子 7 本 (consult 1・author 1・review 2・fix 2・focus 1、全 rc=0・受理)。計算ノード job は実走 1 本 (Elapse 88 s、約 0.024 node 時間) と受入。

## 次の一手差分

### 更新

- [T-2847] **P1・一部実走済み・容量は済み (VLDB 差分分析 P0: 検証の意味と容量)**: 計算なしの設計を insight `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` に記録した — 判定の範囲 (§2)、小履歴コーパス 27 案 (§3)、CC 変異 34 と無改変 si 1 の検出期待表 (§4)、既存 broken patch 16 本の現行 pin への適用可否と記録 (§5.1)、si の v1 拒否 (§5.3)、容量評価の計画 (§6)、論文用の射程文 (§7、済)。
  2026-09-23 に残り (1) コーパスの test (`output/insights/2026-09-23/t2847-corpus-gaps/README.md`) と残り (3) 容量の実測 (`output/insights/2026-09-23/t2847-verifier-capacity/README.md`) を済ませた。
  2026-09-23 に残り (2) のうち、既存の silo 壊し patch 10 本 (`output/insights/2026-09-23/t2847-patch-verify/README.md`、13 run 中 12 run が期待どおり・1 run が別の層) と、pin C に依存しない新規 silo 変異 14 本 (変異 11・対照 3、`patches/broken-silo-*.patch`・`patches/control-silo-*.patch`) と trigger-misattr を現 pin `e9e477ca` で実走した (`output/insights/2026-09-23/t2847-mutation-run/README.md`)。15 行 = 期待した層で検出 3 (V17 巡回・V19 version dup・V20 orphan)・別の層 1 (V18 に genesis への commit)・盲点として certified 6 (V22・V23・V26・V27・V35・V08、発火診断で変異の commit を確認)・未発生 2 (V21 発火 0・V24 未到達)・対照の誤検出 0。trigger-misattr の driver `main()` は現行の source digest が裸マクロを拒否して走らないので、起動器で misattr build だけを直 CMake にした。
  2026-09-23 に残り (2) のうち sort-nonswo (V07) を、condition gate と同じ供給経路 (`-DCCBENCH_SORT_VARIANT=<v>`) で build し、同じ job の stock 対照つきで pin `e9e477ca` で実走した (`output/insights/2026-09-23/t2847-sort-nonswo/README.md`)。事前登録した 4 run = 17 要素の壊し build は hang でなく SIGSEGV で別の層 (process の異常終了)、16 要素の壊し build は S (設計書の閾値「16 以上」は source どおり「16 超」だった)、stock 対照 2 本は S。verifier の判定は V07 を捕まえない (盲点の行のまま)。
  残り = (2) の残り: mocc の既存 4 本と新規 V25・V34 (X/P の emitter = pin C の計装の上。pin C = `68106660` は [T-2858] で local main へ着地済み)。(4) si の emitter の v2 化 ([T-2854] の実装単位 (12) に相乗り) と、その後の si の V28・V29・V36。完了 = 検出表の実測 (容量の実測表は済み)。
  計算: (2) の残りは、同じタスクで投げる job の合計 (開発の検査を含む) が 2 node 時間以上なら投入前に見積りを示してユーザー確認 (D2212 項 4、D2219 項 1)。実測単価: 変異の計測 1 job (build 4〜5 本 + run) の Elapse 139〜194 秒、焦点走 (25 test file) 193〜200 秒、sort-nonswo の 1 job (build 2 本 + run 4 本) 88 秒 (2026-09-23)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P0。
  base: 27832cf64b5363e5dc6273718cb4f3683d57c489d694fcc17156a40ea9cec2b6
