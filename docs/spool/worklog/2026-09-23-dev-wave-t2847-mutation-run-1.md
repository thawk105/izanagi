---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: dev-wave-t2847-mutation-run
seq: 1
title: [T-2847] 残り (2) のうち pin C に依存しない変異を実走した — 新規 silo 変異 14 本 (変異 11・対照 3) を patch にし、trigger-misattr と合わせて 15 行を計算ノードで測り、期待した層で検出 3・別の層 1・盲点として certified 6・未発生 2・対照の誤検出 0 (patch + 条件 gate 登録 + insight、branch worktree-dev-wave-t2847-mutation-run)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `output/insights/2026-09-23/t2847-mutation-run/verbatim/request.md`): trigger-misattr と、新規 18 変異のうち現 pin `e9e477ca` で作れるものを実走し、検出表を実測で書く。記録 = 同 insight の README、設計判断 = {{D:t2847-mutation-run-scope-and-firing}}。
- 起点 = local main `65fd1422f` (fresh worktree、開始 gate rc=0)。wave 中に local main `4f0a74997` を merge `a40f56ce8` で取り込んだ (docs のみで変更面と重ならない)。patch と条件 gate の受理集合を変えるので、DW-C00 により段 2・3・6 の独立検証子を省かなかった。
- **計算投入の確認:** 段 4 の見込み 1.0〜1.3 node 時間 (2 未満) のため投入前の確認は取っていない (D2212 項 4)。実績 (job Elapse) は計測 7 run 1,148 秒・焦点走 2 回 393 秒・変異 probe と final 1,343 秒・受入 890 秒の計 3,774 秒 ≈ 1.05 node 時間 (受入 2 回目の基盤中止分は log に Elapse が無く含まない)。
- **変異 matrix:** 事前登録 M1〜M4 (M4 は登録簿の site 数へ再照準、erratum)。final (独立 clone = `ff9e48b66`) は KILLED 4・正例 M0 生存・MISMATCH 0。
- **受入:** 1 回目は main 取り込みの merge で `test_p3_s4_loop.py` が両親と違う内容に合流し Codex author 不在で provenance 事前検査が赤 (Codex が 3 版照合で修正なしと確定し、親が merge `0721f059f`)。2 回目は計算ノードの待ち行列の timeout による基盤の赤 (test 未実行、非帰属)。3 回目 = tested main `aa96126f2`・tested tip `ddb079e34` で 27,557 passed・74 skipped、child-green。
- **並走 wave の着地:** [T-2858] の pin 前進 (C = `68106660`、変更は `cc/mocc/transaction.cc` だけ) を wave 中に取り込んだ。本 wave の計測は e9e477ca 上の事実として記録し、patch の当て先 (`cc/silo/transaction.cc`) は C でも不変。
- **段 3 相談 2 本:** 発火の証拠が無いと「盲点」と「未発生」を取り違える (発火診断を採用)、同時投入は job ごとの別 checkout が必須、stock は workload ごとの run が要る、V20 の公開値の具体化。全 must-fix を採用。
- **段 6:** レビュー A は NO-GO (V18/V35 が有効 build で compile 不可、V20 の tid 巻き戻り (親の所見を real と判定)、V21 の証人なし verify の例外経路)、レビュー B は条件付き GO (重複した照合表・不要な test 改名)。焦点走 1 回目は登録の追随漏れ 4 件 (screening の既定値表・件数固定)。fix 1 巡 → 焦点再レビュー NO-GO (V20 の公開値の重複) → fix 2 巡 → GO。
- **実走後の実装の誤り 2 件:** (1) V20 の公開 epoch を減らす版は巡回 1 本 (G2・長さ 4) を出し、rw 辺はすべて公開版の番号の逆転から生じていた (狙った機構とは別)。増やす向きに直して別 run で orphan だけの I を得た (初回結果は insight に残す)。(2) trigger-misattr の driver `main()` は現行の source digest が misattr の裸マクロを拒否して止まった (2026-07-10 以降未実行)。防壁は緩めず、起動器で misattr build だけを直 CMake にして checks 11 個すべて真。
- **起動器の要約欄の誤り:** J1〜J4 の版は `cmake --build --target ycsb_silo.exe` を ycsb の実行と分類し、変異区間の要約が空になった。検出表は保存 subprocess 記録から親が集計した。
- 工数: Codex 子 = plan 1、consult 2、author 4、review 2、fix 7 (段 6 の fix1 3 本・fix2 2 本・fix3 1 本・V20 fix を含む)、focus 2 の計 18 本。

- [T-2847] 残り (2) のうち pin C に依存しない部分を実走した (記録 = `output/insights/2026-09-23/t2847-mutation-run/README.md`、設計判断 = {{D:t2847-mutation-run-scope-and-firing}})。

## 次の一手差分

### 更新

- [T-2847] **P1・一部実走済み・容量は済み (VLDB 差分分析 P0: 検証の意味と容量)**: 計算なしの設計を insight `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` に記録した — 判定の範囲 (§2)、小履歴コーパス 27 案 (§3)、CC 変異 34 と無改変 si 1 の検出期待表 (§4)、既存 broken patch 16 本の現行 pin への適用可否と記録 (§5.1)、si の v1 拒否 (§5.3)、容量評価の計画 (§6)、論文用の射程文 (§7、済)。
  2026-09-23 に残り (1) コーパスの test (`output/insights/2026-09-23/t2847-corpus-gaps/README.md`) と残り (3) 容量の実測 (`output/insights/2026-09-23/t2847-verifier-capacity/README.md`) を済ませた。
  2026-09-23 に残り (2) のうち、既存の silo 壊し patch 10 本 (`output/insights/2026-09-23/t2847-patch-verify/README.md`、13 run 中 12 run が期待どおり・1 run が別の層) と、pin C に依存しない新規 silo 変異 14 本 (変異 11・対照 3、`patches/broken-silo-*.patch`・`patches/control-silo-*.patch`) と trigger-misattr を現 pin `e9e477ca` で実走した (`output/insights/2026-09-23/t2847-mutation-run/README.md`)。15 行 = 期待した層で検出 3 (V17 巡回・V19 version dup・V20 orphan)・別の層 1 (V18 に genesis への commit)・盲点として certified 6 (V22・V23・V26・V27・V35・V08、発火診断で変異の commit を確認)・未発生 2 (V21 発火 0・V24 未到達)・対照の誤検出 0。trigger-misattr の driver `main()` は現行の source digest が裸マクロを拒否して走らないので、起動器で misattr build だけを直 CMake にした。
  残り = (2) の残り: mocc の既存 4 本と新規 V25・V34 (X/P の emitter = pin C の計装の上。[T-2858] の pin 前進の後)、sort-nonswo (既存 driver に経路が無い)。(4) si の emitter の v2 化 ([T-2854] の実装単位 (12) に相乗り) と、その後の si の V28・V29・V36。完了 = 検出表の実測 (容量の実測表は済み)。
  計算: (2) の残りは、同じタスクで投げる job の合計 (開発の検査を含む) が 2 node 時間以上なら投入前に見積りを示してユーザー確認 (D2212 項 4、D2219 項 1)。実測単価: 変異の計測 1 job (build 4〜5 本 + run) の Elapse 139〜194 秒、焦点走 (25 test file) 193〜200 秒 (2026-09-23)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P0。
  base: 909004738d7a58bc2ba67df9f1fb2b427398e0a0d51ed04075f14be662b4e24c
