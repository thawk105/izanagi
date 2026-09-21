---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2795-k2-pair-repair
seq: 1
title: "[T-2795] K2 同 job pair launcher と one-shot claim の整合を直した — 1 process・1 回の認可 / claim 所有期間で候補→stock を評価する driver へ (コード + テスト + insight、branch worktree-dev-wave-t2795-k2-pair-repair)"
---

## 本文

- 依頼 (D2187 の修復方向、D2194 項 2 の控え) を 9 段で処理した。段 2 plan (codex read-only) → 段 3 敵対相談 2 本 (must-fix 2: 85 path closure の live=HEAD 照合により
  bytes 注入の変異は「内容と無関係な赤」を生む / 結合正例が両 arm の certified を固定していない) → 段 4 裁定 (全 10 所見 real・採用、plan v2、変異 H 群 + commit 群を事前登録) →
  段 5 Codex author 2 単位 (A1 = `loop.py` の認可 session、A2 = CLI の pair mode + job body + 結合検査) → 段 6 敵対レビュー 2 本 (ともに NO-GO、新規 must-fix は同一 1 件) →
  fix 3 巡 → 焦点走 3 回 → 変異 → 受入 → 記録。設計判断は {{D:k2-pair-authorization-session}}、F1019 への追記は同 wave の failures fragment。
- **段 6 fix1 の 1 巡目は「既存テストの期待値を変更しない」の解釈で正しく停止した** (変更 0 行)。本 wave の A1 が今回作った未 land の test と、main に land 済みの tracked test を
  prompt で区別していなかったため。区別を明記して再投入 (fix1b) した。
- 親が実測した赤の分類: 焦点走 1 (17 file) で 100 赤 → (a) 静的目録 18 node = `_authorize_with_session` の局所変数経由の呼出し、(b) job contract 72 node = 契約断片の責務が分かれておらず
  1 変異で欠落が 2 つ出る、(c) 結合検査 3 node = 実機 attestation に入る / perf preflight 代用が受領証無し。焦点走 2 で 4 赤、焦点走 3 で **全緑 (2,015 passed / 5 skipped / 154.35 s)**。
- 変異の帰属条件として、等価変異 1 本 (comment 追加) の probe で **114 node が「変異の内容と無関係に」落ちる**ことを実測した (`contract-loader-drift`)。
  この集合を除外して帰属を保った。副作用として、pytest の `--deselect` は param に `/` を含む nodeid に効かず、テスト名ごとの除外が必要だった。
- M6 (pid 照合の単独削除) は survivor だった — 最後の台帳 tuple 照合が同じ process 束縛を冗長に強制するため、単独削除では受理集合が広がらない。等価として登録し直した。
- **実機 (Pegasus) の pair 1 走は本 wave では投入していない。** D2172 項 3 の予算再提示はユーザー手番で、結合検査の緑は stock 対照の成立を意味しない (insight §0 の「主張しない」)。
- 工数: codex 子 = plan 1 + consult 2 + author 2 + review 2 + fix 4 (うち 1 は正しい停止) の 11 本、親の計算ノード走行 = 焦点走 3 + 変異 probe 2 + 変異 final 1 + 受入。

## 次の一手差分

### 更新

- [T-2795] **P1・修復済み (AI) → pair 再投入 (1 job) と 4 巡目 (1 job) の予算再提示はユーザー手番**: D2187 の修復方向 (ii') を実装し land した
  ({{D:k2-pair-authorization-session}})。pair mode は `--run-iteration <proposal> --stock-control` の 1 process で、1 回の認可・claim 所有期間で候補→stock を評価する。
  claim leaf は bytes 不変、`--stock-control` 単独 (B-5) と job body の既定 argv も不変。F1019 には認可 / claim 結合の再発検査を追加したが、
  実 compiler の STOCK 成立・実 build との統合・production の pair 1 走は未実施。4 巡目の入力元は D2194 項 2 (択 A) のまま。
  base: 30b80c167a846593674059c4676634cd7b91e3586d28a66815ee8ccfac831c80
