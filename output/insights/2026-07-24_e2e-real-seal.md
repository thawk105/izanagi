# 統合 E2E — 実 seal を official floor 経路に通す (2026-07-24)

/ dev-wave 1 回 (引数「なるべく路線復帰を目指して優先度の高いタスクを選んで」)。**D79(7) の
「protocol→seal→commit→floor 完全同型 E2E」の欠落**を、実凍結済み seal bytes を official floor 経路の
test seam に通す統合テストで**部分的に**埋めた。code commit = 6b4fbdf (test-only、production・凍結
成果物 bytes・guard・calibration 無変更)。変異台帳 = `2026-07-24_e2e-real-seal-mutation-ledger.json`。

## 経緯 (タスク選定の 2 段訂正 — 忠実報告)
1. 路線復帰狙いで「統合 E2E」を選定 → DW-G01 生死確認で、統合 E2E + lineage は正本上 floor と不可分・
   Pegasus 単独に見え、「実装しない → gate パッケージ」へ pivot (ユーザー裁定)。
2. gate パッケージ整備中、codex 2 レンズが私の枠組みを**訂正**: (a) official guard は「stale 誤記」でなく
   F6 承認束縛方式の裁定 (2026-07-18) の**後に意図的に置かれた dormant 防壁** (commit 1eb1ed1c が
   bfa0f085 の子孫)、(b) 統合 E2E は worklog:585「protocol 凍結後 unblock 済み・floor 直前 blocking
   前提」= **建てられる定義済み T-011 作業** (生死確認が「Pegasus 単独」を E2E まで過剰拡大読みしていた)。
   → ユーザーへ訂正・再提示 → 「統合 E2E を実装」を選択。

## 実装 (test-only)
実 committed HEAD を tmp clone し、実 `floor_protocol.json` / `selector_predictions.json` /
selector-runs journal を production preflight に読ませ、private `_run_campaign_core` (mode=official) を
直呼び (guard は public `run_campaign` にのみ存在 = test seam として正当、bypass 新設なし)。
- **probe** は実 registered calibration 由来の clean な in-tolerance 観測 (logical 48 標本・observed
  tolerance 100.0)。実 comparator / issuer / consumer / v2 receipt は production を通す (**物理 Pegasus
  attestation ではない**)。
- **reservation / claim / preflight allowlist / clean_scan 二重 / launch cert 発行+再検証 / full
  verifier / journal resolver / floor result / 最終自己検査** の実 gate を通過。spy は純委譲 (original
  捕捉→return original、call-count assert)、stub なし。
- **workload rratio / floor / schedule / build src_token** を seal から**独立に**照合 (production 関数
  非依存の独立射影・独立 golden)。
- **producer tripwire** (seal/provider/drive_journal を「呼ばれたら失敗」)。実行前後で 16 frozen +
  calibration bytes を source/clone 双方で snapshot 比較 (凍結 bytes 無変更の実効)。

## 検証プロセス
codex プラン (max) → 敵対相談 2 (max、reservation/claim gate 欠落を両者独立に検出) → 親裁定 (plan v2) →
実装 (high) → fix1 (probe faithfulness — 実装子が正直に赤報告、親が comparator 精読して in-tolerance
観測へ) → 敵対レビュー 2 (max、**核心 sound = bypass/stub/frozen 破損なしを confirmed**、検出力の
弱点を摘出) → fix2 (独立期待値・honest 分類・probe production 忠実化) → **親 empirical 変異 matrix**。
- 受入全走: <受入結果を反映>。check_docs / check_ai_provenance (324) / repo scan invariant (F34): <反映>。

## 変異 matrix の結論 (empirical が静的分析を訂正)
- **MK-workload = 排他的新検出力**: real seal の workload が誤 holdout へ配線される変異を、既存 196
  テストは全通過し新テストの独立 rratio assertion だけが検出。**本テストの固有価値** (real seal が
  正しい cell へ流れるかの検証)。
- MK-build-src (src_token 定数化) は 45 既存テストも破る過剰決定、MK-digest (allowlist sha 除去) は
  既存 digest テスト 3 件も検出 → いずれも新検出力に数えない (統合カバレッジ)。empirical が codex
  fix2 静的分析の過大主張を訂正した (matrix の価値)。
- gate 呼出し spy (verify/resolver/revalidate/receipt-consumer/self-check) は **diagnostic invocation
  pin** であり mutation kill でない (DW-M03/M08)。teeth は既存 HEAD negative が担保。

## 主張の限定 (D79(7) 部分閉鎖)
producer `seal()` / provider 実走 / commit 作成はしない **consumer replay** = D79 文字どおりの完全同型
E2E ではなく「歴史 anchor→floor replay」。**R3 (初回導入捏造) / R4 (HOME 盲検境界) は残存** (closed
としない)。journal↔prediction row の直接 assertion は「固定 seal の characterization」であり official
gate の enforcement 証明ではない (resolver は claim=decision_method・invocation=順序/重複のみ照合)。

## 残った人間/設計 gate (floor 実測へ、次の一手)
本 wave では触れない。official 解禁には (a) official guard (_assert_official_permitted) 解除の設計判断
(F6 後の意図的 dormant、typo 修正でない)、(b) Pegasus PBS floor wrapper (untracked)、(c) 実行 revision
束縛、(d) §5-(viii) 残存限界の最終受諾 (B-005 未裁定) が残る。これらは gate パッケージ調査で棚卸し済み。
