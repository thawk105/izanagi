---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: dev-wave-t2847-mocc-run
seq: 1
title: [T-2847] 残り (2) の mocc 部分を pin C で実走した — 既存壊し patch 4 本と新規 V25・対照 V34 の 34 cell を計算ノードで測り、期待した層で検出 20・盲点として certified 1・未発生 2・発火未確認の S 2・停止 3・対照正常 6 (patch + 条件 gate 登録 + insight、branch worktree-dev-wave-t2847-mocc-run)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `output/insights/2026-09-26/t2847-mocc-run/verbatim/request.md`): mocc の既存壊し patch 4 本と新規 V25・V34 を現 pin C で実走し、検出表を実測で埋める。記録 = 同 insight の README、設計判断 = {{D:t2847-mocc-run}}。
- 起点 = local main `42d148868` (fresh worktree、開始 gate rc=0)。patch と条件 gate の受理集合を変えるので、DW-C00 により段 2・3・6 の独立検証子を省かなかった。
- **計算投入の確認:** 段 4 の見込み 0.95〜1.45 node 時間、walltime 上限でも 1.9 (2 未満) のため投入前の確認は取っていない (D2212 項 4)。実績 (job Elapse、受入を除く): 計測 4 job 1,376 秒・焦点走 144 秒・変異 matrix (probe + final) 1,378 秒の計 2,898 秒 ≈ 0.81 node 時間。
- **変異 matrix:** 事前登録 M0〜M4 (登録簿の削除・key の 1 字違い・site 数の虚偽)。final (独立 clone = `267b8992f`) は KILLED 4・正例 M0 生存・MISMATCH 0。
- **段 3 相談 2 本の must-fix:** 停止時の診断契約、4 thread の多層同時発火の分類の一意化、`_variant_run` では発火行と trace を保存できないこと、spawn_sites の件数固定 2 箇所の漏れ ([T-2849] と同じ行)、完了判定と「発火未確認・停止」の両立。policy が旧 pin に束縛されて起動器が止まるという指摘は、既存の pin 候補経路が同じ policy のまま C を build している先例で refuted とした。
- **段 5:** 実装子が `test_screening_driver.py` に足した追加検査 (既定値 0 の固定と、Genome 経由で裸マクロを供給できないことの固定) は、依頼の scope 外 (仮想リスク向けの検査の追加) として統合しなかった。焦点走 (33 file) は 4,049 passed・8 skipped・失敗 0。
- **段 6:** レビュー A・B とも条件付き GO。実装への must-fix は無く、fix 子は起動していない。段 4 の分類に「対照正常」の名前が無かったので erratum で足した (計測後、変異 cell の分類は不変)。README の inert 文を「未定義の枝を除いた全文が pin C と一致」に狭めた。
- **並走 [T-2849] との合流:** `orchestrator/tests/test_ccbench_spawn_sites.py` の件数行は、t2849-unit-a の変更 (非 CCBench subprocess site 1 件) が件数に増分を持たないので、合流値 = 55 / 59 / 45 / 45 (レビュー B の照合)。
- **near miss:** unit worktree の作成に短縮 SHA を手で伸ばした値を渡し `git worktree add` が rc=255 で失敗した (何も作られず、rev-parse の完全 SHA でやり直した)。
- 工数: Codex 子 = plan 1、consult 2、author 3、review 2 の計 8 本。

## 次の一手差分

### 更新

- [T-2847] **P1・一部実走済み・容量は済み (VLDB 差分分析 P0: 検証の意味と容量)**: 計算なしの設計を insight `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` に記録した — 判定の範囲 (§2)、小履歴コーパス 27 案 (§3)、CC 変異 34 と無改変 si 1 の検出期待表 (§4)、既存 broken patch 16 本の現行 pin への適用可否と記録 (§5.1)、si の v1 拒否 (§5.3)、容量評価の計画 (§6)、論文用の射程文 (§7、済)。
  2026-09-23 に残り (1) コーパスの test (`output/insights/2026-09-23/t2847-corpus-gaps/README.md`) と残り (3) 容量の実測 (`output/insights/2026-09-23/t2847-verifier-capacity/README.md`) を済ませた。
  2026-09-23 に残り (2) のうち、既存の silo 壊し patch 10 本 (`output/insights/2026-09-23/t2847-patch-verify/README.md`、13 run 中 12 run が期待どおり・1 run が別の層) と、pin C に依存しない新規 silo 変異 14 本 (変異 11・対照 3、`patches/broken-silo-*.patch`・`patches/control-silo-*.patch`) と trigger-misattr を現 pin `e9e477ca` で実走した (`output/insights/2026-09-23/t2847-mutation-run/README.md`)。15 行 = 期待した層で検出 3 (V17 巡回・V19 version dup・V20 orphan)・別の層 1 (V18 に genesis への commit)・盲点として certified 6 (V22・V23・V26・V27・V35・V08、発火診断で変異の commit を確認)・未発生 2 (V21 発火 0・V24 未到達)・対照の誤検出 0。trigger-misattr の driver `main()` は現行の source digest が裸マクロを拒否して走らないので、起動器で misattr build だけを直 CMake にした。
  2026-09-23 に残り (2) のうち sort-nonswo (V07) を、condition gate と同じ供給経路 (`-DCCBENCH_SORT_VARIANT=<v>`) で build し、同じ job の stock 対照つきで pin `e9e477ca` で実走した (`output/insights/2026-09-23/t2847-sort-nonswo/README.md`)。事前登録した 4 run = 17 要素の壊し build は hang でなく SIGSEGV で別の層 (process の異常終了)、16 要素の壊し build は S (設計書の閾値「16 以上」は source どおり「16 超」だった)、stock 対照 2 本は S。verifier の判定は V07 を捕まえない (盲点の行のまま)。
  2026-09-26 に残り (2) の mocc 部分を pin C `68106660` で実走した (`output/insights/2026-09-26/t2847-mocc-run/README.md`、{{D:t2847-mocc-run}})。既存 4 本 (V13〜V16) は計装 patch を重ねず C に単独で当て、新規 V25 (`patches/broken-mocc-skip-canonical-restore.patch`) と対照 V34 (`patches/control-mocc-negated-temperature-predicate.patch`) を加えた 34 cell = 期待した層で検出 20 (V13・V14・V15 の全 cell と V16 の hot。4 thread の V13・V15 は巡回と version dup が併発)・盲点として certified 1 (V25 の 1 thread、lock 順違反を含む完走履歴)・未発生 2 (V16 の cold、hot 分岐に届かない)・発火未確認の S 2 (V16 の default、診断なし)・停止 3 (V25 の 4 thread、stock は完走、原因は未確定)・対照正常 6 (V34、評価された site は 297・460 行だけ)。別の層・誤検出は 0。
  残り = (4) si の emitter の v2 化 ([T-2854] の実装単位 (12) に相乗り) と、その後の si の V28・V29・V36。完了 = 検出表の実測 (容量の実測表は済み)。
  計算: 残りは、同じタスクで投げる job の合計 (開発の検査を含む) が 2 node 時間以上なら投入前に見積りを示してユーザー確認 (D2212 項 4、D2219 項 1)。実測単価: 変異の計測 1 job (build 4〜5 本 + run) の Elapse 139〜194 秒、mocc の計測 1 job (build 2〜3 本 + run 8〜24 本) 157〜540 秒 (停止 run は 1 本 120 秒)、焦点走 (25〜33 test file) 144〜200 秒 (2026-09-23・26)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P0。
  base: 6707fd2bef630f5297052742887f47f24fa1bb501599aa68d306744e8e5d6761
