---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-t409-evolve-hole-allowlist
seq: 1
title: [T-409] EVOLVE-BLOCK hole の受理文法を設計凍結し、実装は択一 5 件の裁定へ返す — 敵対 2 レンズが独立に同じ配線漏れへ到達 (docs のみ、branch worktree-wave-t409-evolve-hole-allowlist)
---

## 本文

- **[T-409] は本 wave で実装しない。設計を凍結し、ユーザー択一 5 件を返す。**
  設計・逐語・real/refuted 表 = `output/insights/2026-08-04_t409-evolve-hole-allowlist/`
  (裁定の正本は同 dir `s4-adjudication.md`)。**実装差分が無いため、変異 matrix と受入全走は
  対象外**である。受理集合を変えていないので D96 手続 (新 D + 境界テスト) は実装 wave が負う
- **実装しない理由 3 点 (いずれも親が現物で裏取り)。** (1) `.claude/agents/` の変更は
  ユーザーの明示承認が必須 (`docs/decisions.md:1367-1370`、`:1967`) で、本 wave は持たない。
  (2) producer を変えず consumer だけ狭めるのは D127 決定 (1) が名指しで退けた形であり、しかも
  「機械化するだけで契約は狭めない」は**偽**だった — `izanagi_gate_pass = 1;` は D48 の
  「コンパイル時定数のみ」契約・1 行制約・副作用なし・禁止識別子非参照をすべて満たすが、
  新文法は数字を字句段で落とす。文法の中身そのものが裁定事項になる。
  (3) 発火層が未確定の条件付き機能は設計メモに留める (DW-G04)
- **D127 決定 (1) は却下ではなく先送りだった。** 「boolean-expression AST/DSL は本 wave では
  採らない、別 wave へ分離する」であり、[T-409] がその別 wave である。反対理由 2 点
  (producer 契約非互換 / sort 軸で合成が選択に化ける) がそのまま設計制約になった
- **敵対 2 レンズが独立に同じ 2 件へ到達した (合議ではない)。**
  (a) `s1_verify_extime_calibration.py:329-357` が trigger implementation を `write=True` で
  materialize するのに配線案から漏れていた。(b) checked-in freeze と live source を結ぶ回帰
  テストが無い。DW-G03 が求める独立 2 例に相当する
- **親の段 1 実測が 3 回訂正された (訂正はすべて親が現物で裏取りしてから採用)。**
  (1) `makeProcedure` は冒頭で `pro.clear()` するため (`external/ccbench/include/ycsb.hh:57`)、
  `pro_set_.pop_back()` の縮小は同一論理トランザクションの retry 列内に限られる。攻撃の成立は
  不変だが初版の「恒久的」は過大だった。(2) 回収した正例 26 件の内訳は trigger 代入式 9 +
  trigger stock 説明 1 + sort 16 で、新 gate に通すべきは 9 件だけ。(3) **最も重い訂正** —
  初版は「`axis_trigger_gating.py` を編集しても全スイート緑 (5430 passed) だから凍結 pin は
  発火しない」と書いたが、正しくは「**本番の検証経路では発火するが、通常スイートが
  checked-in freeze 対 live source を検査していない**」。
  `s1_direct_comparison.load_verified_freeze` → `s1_measurement_freeze.verify_document` →
  `_verify_known_axes` が live source の sha を照合する。no-touch 制約はより強い理由で維持
- **棄却した所見 (refuted、記録に残す):** D96 との手続衝突 (D96 の「機械検査は新設しない」は
  consumer 閉集合の一般 AST 固定についての判断であり個別 domain recognizer の恒久禁止ではない)、
  D48 が機械執行を auditor 目視へ永久限定した説 (D51 が既に blacklist を machine hard gate に
  している)、blacklist 撤去で受理集合が広がる説、許可文法を role へ書くとリークする説
  (D51 が naked member 提示を許可済み)、`axis_trigger_gating.py` の no-touch は不要説
- **セッション異常:** 段 3 レンズ A の初回投入が上流の安全分類器に拒否された
  (「サイバーセキュリティ上のリスク」)。依頼文が「関所を通る入力を作れ」という攻撃者視点
  だったため。防御目的 (境界テストの negative ベクタ設計) を明示した prompt で再投入して成功。
  凍結してあるのは再投入版の出力である
- **受入 (docs のみ): 全スイート = 2 failed, 5437 passed, 19 skipped。`check_docs.py` / fold dry-run /
  `check_ai_provenance.py` (992 件) はいずれも緑。赤 2 件はどちらも本 wave の差分に帰属しない。**
  (1) `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight` は
  main c642263 以前から赤で、[T-407] 所有の非 UTF-8 blob 由来。clean tree で単独再現を実測して
  切り分けた。レンズ A の警告を採用し、今後の waiver は nodeid だけでなく `non-utf8` + 対象 path で
  固定する。(2) `test_codex_worker_launch.py::test_check_receipt_rejects_impossible_truth_table` は
  **単独再走で 64 passed となり再現しない** ため DW-O18 に従いフレークとして起票する (下記新規)。
  本 wave の差分は docs のみでこの経路へ到達しえない
- **verifier は workload 縮小を構造的に検出しない (段 3 が裏取り)。** trace は commit した実際の
  read/write 集合しか出さず、`orchestrator/verifier/model.py:37` の `Txn` に予定操作数の欄が無く、
  `:132` の integrity にも `FLAGS_ycsb_max_ope` 照合が無い。verifier 側の不変条件追加は別 task 候補。
  なお「当該変異を入れた実 run が実際に certified されるか」は**未実測**である

## 次の一手差分

### 更新

- [T-409] **P1・設計凍結済 → ユーザー裁定待ち (択一 5 件)**:
  受理文法 v1 と must-fix 8 件を
  `output/insights/2026-08-04_t409-evolve-hole-allowlist/` へ凍結した。実装 wave は
  再導出せずここから始める。**択一 1** 権威境界 = 全 materializer で中央再検査 / 合格時に
  封印済み receipt を発行し build 境界が要求 (親推奨 = receipt。D127 決定 (3) の先例、
  cache preimage と WAL へ束縛できる)。**択一 2** 既存 cache・WAL・S8B resume の移行 =
  cold invalidate / 再検査 / overlay (親推奨 = 再検査)。**択一 3 (最重要)** 数値 literal を
  文法へ入れて現行 producer 契約を維持するか、契約を狭めて role 定義変更の明示承認を取るか
  (親推奨 = 後者。ただし承認が無い限り本件は前へ進まない)。**択一 4** scope = trigger のみで
  閉じ backoff へ別 T を起票するか、全軸へ拡張するか (親推奨 = 前者。sort は [T-410] が所有)。
  **択一 5** checked-in freeze 対 live source の回帰テストを本件に含めるか別 T にするか
  (親推奨 = 別 T。本件は実装待ちで止まるため防壁追加まで止めない)
  base: 0e23d9e1c71ad7904c7064fe17edc4126b55fcb92aea9c523ecc747ca5c72666

### 新規

- {{T:codex-worker-launch-flake}} **P3・新規・フレーク起票 (DW-O18)**:
  `test_codex_worker_launch.py::test_check_receipt_rejects_impossible_truth_table` が
  16 並列の全走時にだけ落ちる。`_run_case` の子プロセスが **stdout / stderr 空のまま rc=1** で
  終わる形で、`--termination-grace-s 0.05` / `--poll-interval-s 0.01` という極小の時間窓を
  使うテストである。単独再走は 64 passed で再現しない (2026-08-04、main c642263 + docs 2 commit、
  Pegasus gen_S request 883957 / 883999)。負荷依存の待ち時間不足を疑うが未診断。
  観測 1 回なので族一般化はせず、再現条件の特定から始める
