---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: t2847-verifier-capacity
seq: 1
title: [T-2847] 残り (3) verifier の容量を実測した — legacy・Silo の性能構成の錨・B-8 の verify 経路には同じ構成の実測があり、巡回の多い trace (壊し patch norw × 性能構成 3 workload) と参照 genome (R1・R2) の 3 s trace を計算ノードで測って資源の超過は観測されなかった (insight + 実測 JSON、branch worktree-t2847-verifier-capacity)
---

## 本文

- 依頼: ユーザーの `/dev-wave` 引数 ([T-2847] の残り (3)、担当分割で (1) コーパスの test と (2) 壊し patch の変異実走は別 wave)。軽量版で段 2・3 を省いた (設計の択一なし、正しさ防壁・受理集合を変えない)。成果は insight `output/insights/2026-09-23/t2847-verifier-capacity/README.md`。
- 要る長さの棚卸し (段 1、計算なし): 合成ループの毎回検証 1 s・4 thread・200 レコード、S2 / 性能構成の verify (P3・D2214 段 D・P4 の錨と比較対象) 3 s・48 thread・100 万レコード、B-8 10 s。設計 §6.1 が書いた範囲 (read-heavy は 6 s まで) の外に、B-8 本走の read-heavy 10 s × 8 (約 1,980 万取引・辺 3.47 億・verify 約 496 s) が現行 verifier で完走済みだった。範囲は秒数でなく取引数・辺数で読む。既存の最大は観測した最大であって容量の境界ではない。
- 計算: Pegasus gen_S 4 job、dispatch Elapse 237 S + 328 S + 472 S + 684 S = 1,721 S (0.48 node 時間)。投入前の見積りは初回 (A・B の walltime の和 + 受入 1 回) 1.92、追加時 (A・B の実消費 + C・D の walltime の和 + 受入) 1.57 node 時間で、どちらも確認線 (D2212 項 4・D2219 項 1) の下なので確認待ちにしなかった。job C (19157.nqsv) は PRR で 18 分割当てを待ってから走った (Elapse には入らない)。
- 起動器 (repo 外、job dir) は Codex `role=author` が書き (gpt-6-astra / medium)、fix 2 回 (親の監査で scratch が lustre 上になる所見 → ローカル `/scr` へ、段 6 所見で参照 genome の指定を追加)。s2 driver の下位関数をそのまま呼び、差し替えは PIN・CLK (1800 → 2100)・verifier timeout (600 → 1800)・compiler・出力の受動保存だけ。
- 段 6: 独立 read-only レビュー (Codex) 1 回目は NO-GO (must-fix 3: 全経路の包含の断定、SCC 非律速と [T-2351] 非発火の断定、棚卸しの漏れ = P4 の 17 cell は 48 thread・参照 genome・TPC-C 段 2)。全件 real と裁定し、断定を弱め、記録の無かった参照 genome を 2 job で実測して insight §7 に対応表を置いた。焦点再レビュー (2 回目) も NO-GO (前回 9 件は closed 6・partial 3、新 must-fix 2 = P4 留保を「構成未定」と書いた・node 115 GiB 非超過を B-8 まで広げた) で、全件 real として文書を直した (insight §7 の 2 表目)。3 巡目は GO (must-fix 0、残った should 2・nit 1 は文言を直して閉じた)。
- 開始 gate (`check_wave_startup.py --mode fresh --external-handoff`) は worktree 作成直後に rc=0。記録の前に local main `76d0a0c92` ((2) の wave の land を含む) へ fast-forward し、[T-2847] の base を取り直した。

## 次の一手差分

### 更新

- [T-2847] **P1・一部実走済み・容量は済み (VLDB 差分分析 P0: 検証の意味と容量)**: 計算なしの設計を insight `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` に記録した — 判定の範囲 (§2)、小履歴コーパス 27 案 (§3、本書の走査で同じ意味の test が無いのは F03・F06 の 2 案)、CC 変異 34 と無改変 si 1 の検出期待表 (§4、族 26・変更機構 22)、既存 broken patch 16 本の現行 pin への適用可否と記録 (§5.1)、si の v1 拒否 (§5.3)、容量評価の計画と [T-2351] との関係 (§6)、論文用の射程文 (§7、済)。
  2026-09-23 に残り (2) のうち既存の silo 壊し patch 10 本 (norw・highkey・lockskip・early-unlock・permutation-erase・permutation-swap・write-intent 4 本) を現 pin `e9e477ca` で計算ノード実走した (insight `output/insights/2026-09-23/t2847-patch-verify/README.md`)。13 run 中 12 run が期待どおり (期待した層で検出 7・対象に届かない条件で期待どおり S 1・盲点として certified 4)、1 run (lockskip の 4 thread) は期待外の version dup も出て「別の層で検出」、未発生・誤検出 0。write-intent 4 本は現 pin では `I` 行 0 件のまま certified。
  2026-09-23 に残り (3) 容量の実測を済ませた (insight `output/insights/2026-09-23/t2847-verifier-capacity/README.md`)。legacy 1 s・Silo の性能構成の錨 3 s・B-8 10 s の verify 経路には同じ構成の実測があり、巡回 472〜3,052 本の trace (norw × 3 s の wh / bal / rh) は同じ node の stock と辺あたりの verify 総所要が −0.3〜+6.8 %、参照 genome (R1・R2) の 3 s 4 本は fixed-5 の 3 s とほぼ同じ規模で完走した。[T-2351] を要する資源の超過は取得した記録では観測されず (B-8 は node 全体を測っていない)、巡回の多い trace での SCC 段の律速は未判定。未測 = P4 の留保 23 cell (条件は固定済み、測定の発効前)・mocc の性能規模 (動作点が未定)・TPC-C 段 1・段 2 の本番規模 ([T-2854] の最初の 1 走で測る)。再判定の条件は同 insight §5。
  残り = (1) コーパスの未被覆 2 案 (F03・F06) と B06 の分類 `G1c` の assert を test として実装する (Codex author。fixture dir として置くなら `test_capacity_all_fixture_results_match_frozen_baseline` の凍結一覧の更新が同じ変更に要る)。(2) 変異の実走の残り: mocc 4 本 (計装 patch の上)、trigger-misattr (trigger-gating 骨格の上)、sort-nonswo (既存 driver に経路が無く、build 経路と workload の対応が要る。2026-09-23 insight §1 の 2)、新規 18 変異 (D16 第 3 類の out-of-tree patch)。既存 silo driver を計算ノードで走らせるには 2026-09-23 insight の起動器 (依存物・compiler・出力先の供給) が要る。(4) si の emitter の v2 化 ([T-2854] の実装単位 (12) に相乗り)。完了 = 検出表の実測 (容量の実測表は済み)。
  計算: (1)・(2) はいずれも、同じタスクで投げる job の合計 (開発の検査を含む) が 2 node 時間以上なら投入前に見積りを示してユーザー確認 (D2212 項 4、D2219 項 1)。既存 silo 壊し patch の実走の実測単価は 1 driver の job あたり Elapse 134〜209 秒、容量の実測は 1 job あたり Elapse 237〜684 秒 (2026-09-23)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P0。
  base: 783815d36d9e5d0bd211fed8b2dd09ac0bfdf446f5f77441092c44653e6456a9
