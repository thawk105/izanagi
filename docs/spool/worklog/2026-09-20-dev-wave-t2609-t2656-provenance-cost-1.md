---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2609-t2656-provenance-cost
seq: 1
title: [T-2656] 全史 provenance 監査の per-commit git subprocess 29,095 本を一括取得へ置き換え、cold 全史の CPU 総量 −70 % (判定不変、固定全史の旧新一致)、[T-2609] の CPU 判定は保留 (コード + テスト、branch worktree-dev-wave-t2609-t2656-provenance-cost、変異 matrix = baseline PASSED・KILLED 9/9・等価 1 SURVIVED・MISMATCH 0)
---

## 本文

- 起点は台帳 entry 1487 (T-2609)・1518 (T-2656)・D2148 項 8。同一 file なので 1 wave。一次資料は
  `output/insights/2026-09-20/t2609-t2656-provenance-cost/README.md` (実測表・裁定・再現資料)、設計判断は {{D:provenance-batch-path-acquisition}} と
  {{D:dispatch-cpu-input-deferred}}。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2609-t2656-provenance-cost/HANDOFF.md`。
- 段 1 実測 (改善前): 残存 dispatch 受領証 86 件の基盤失敗 3 件 (3.5 %、3 件とも監査本体は緑で前後処理の失敗)、queue 待ち中央値 5.2 秒・最大 537.6 秒。
  計算ノード全史 11,769 commit: wall 41.7 秒 / CPU 288 秒、subprocess 累積 1,128 秒の 66 % が実装 path 取得で、起点 T-2656 の順位 (trailer → 隔離 fs → path → 祖先) と逆。
  login cold 全史 88.1 秒 / CPU 368 秒 / 725 MB、受領証ありは 14.9 秒。**受領証は attributes fingerprint が index の directory 集合に依存し、直近 60 main commit の 50 % が
  新 directory を導入するため land ではほぼ毎回 cold** (D2045 の再訪候補として {{T:receipt-attributes-fingerprint-directory-set}} を起票)。
- 段 2 plan 1 本、段 3 相談 2 本 (等価性 / fail-closed・受理集合・P2 検査)。must-fix 4: (c) の porcelain `diff` → plumbing `diff-tree` で
  `diff.ignoreSubmodules` の判定差 (→ 未設定 gate で条件付き採用)、D2148 項 8 の逐語切り出しミス (別 D の項 8、修正済み)、固定全史比較の実行仕様、変異の 5 分予算。
  P2 (CPU 判定を足さない) は「不要と確定」でなく「保留」に改めた。
- 段 5 author 1 本 (Codex、26 test 追加、sandbox で pytest 起動不能)。焦点走 (計算ノード): 3,427 passed / 1 failed (新規 test の前提 `diff.orderFile` の誤り) →
  fix1 (テスト 1 行) → 549 passed / 0 failed。実装 commit `55068f84e`。段 6 レビュー 2 本とも GO (must-fix / should なし、nit 7 件は記録のみ)。
  fix1 が 1 行のテスト前提削除で実装不変のため焦点再レビューは省略した。
- 固定全史比較 (旧 = `b7f970dfa` blob、新 = 実装 commit、独立 clone の同 path 位置で交互、cold): login 公開 4 走と計算ノード内部/公開 4 走の
  rc・stdout・静的 stderr・`HistoryAudit`・selected 列・監査回数 11,770 が**すべて一致**。`_commit_paths` 呼び出し 11,309 → 4,247、`_ai_agent_values` 13,995 → 11,770。
- 性能 (cold 全史): login 交互 2 ラウンド 旧 133.2 / 143.0 秒 (CPU 318 / 305) → 新 77.7 / 125.9 秒 (CPU 96.6 / 95.3)、計算ノード 2 ラウンド 旧 35.8 / 34.8 → 新 23.7 / 23.8 秒
  (CPU 228 / 226 → 68 / 68)、ピーク 733 → 625 MB。CPU 総量は場所・負荷によらず −70 %、wall は −12〜42 % (負荷依存)。commit 後・merge 後の正規 full 監査は
  69 秒 / 84 秒 (いずれも cold、新規違反なし)。混雑時 (load 100 超) の上限は未観測で「480 秒に確実」とは言わない。
- 変異 matrix (独立 clone、計算ノード dispatch、`test_check_ai_provenance.py` 単独走): probe 全件で観測 node を集め、final は **baseline PASSED、M-1〜M-9 = 9/9 KILLED (期待 node 完全一致)、MISMATCH 0**。
  等価変異 1 件 (positive) を SURVIVED 期待で混ぜ、harness の SURVIVED 検出の正例にした。
- 棄却・限界: 候補別 ablation は取っていない。一括 path list で parser 側 RSS +88 MB。checker 改版のたびに受領証が全失効する (初回 cold)。
  land の `timeout=480` と dispatcher の queue 待ち 900 秒の両立は scope 外 ({{T:land-timeout-vs-dispatch-queue-wait}})。混雑時観測は {{T:congested-login-audit-observation}}。
- 工数: codex 7 本 (plan 1、consult 2、author 1、review 2、fix 1)、計算ノード job = probe 3 (内訳・bindings・固定全史比較) + 焦点走 2 + 変異 22 (probe 11 + final 11)、
  login 走 = 正規 3 + cold baseline 1 + 交互 A/B 4。

## 次の一手差分

### 完了

- [T-2656] 実装 path 取得と重複 trailer parse の一括化を実装し、固定全史の旧新一致と cold 全史の CPU −70 % を記録した。残る隔離 parser の
  tempdir 共有と `%(trailers)` は見送り (理由は D 参照)。
  remaining: none
  base: 12e8b409910eb3ffbaeac343de4de31f0e547802afcf5f4facd0d6a1d03bc278

- [T-2609] dispatch 経路の失敗率 (3/86) とキュー待ちの内訳を実測し、CPU 時間を判定入力に足す案は保留 (再訪条件付き) と裁定した。
  dispatch 判定・timeout は変えていない。
  remaining: none
  base: 13ad193ec3c89445015b62fcc8aa8f6f04428aa46d6cff5bc227650e74b7a9fb

### 新規

- {{T:receipt-attributes-fingerprint-directory-set}} **P2・新規**: 受領証 (D2045) の attributes fingerprint が index の全 path の
  祖先 directory 集合に依存し、新 insight dir を足す commit を跨ぐと全 partition で失効する (直近 60 main commit の 50 %)。実在する
  `.gitattributes` だけを束縛するなど、tip の directory 集合に依存しない形を設計して cold 率を下げる。判定は不変であること。
- {{T:land-timeout-vs-dispatch-queue-wait}} **P2・新規**: land の `_run_provenance_checker` は `timeout=480` を持ち、dispatcher の既定 queue 待ち
  上限は 900 秒。全史監査が dispatch へ倒れると監査本体が正常でも queue 待ちだけで land が先に打ち切る。D2148 項 8 (外側 timeout は全区間) の
  実装と併せて両立の契約を決める。timeout の延長は裁定なしに行わない。
- {{T:congested-login-audit-observation}} **P3・新規**: 改善後の checker で混雑時 (load 100 超) の login 全史監査の wall / CPU / load を集め、
  480 秒超が 1 件でも出たら {{D:dispatch-cpu-input-deferred}} の再訪条件を発火させる。
