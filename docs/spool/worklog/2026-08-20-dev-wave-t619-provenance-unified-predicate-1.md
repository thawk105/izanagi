---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t619-provenance-unified-predicate
seq: 1
title: '[T-619] D230 の統一述語を既定監査へ導入した — 選択集合+scope/implementation/CAB3層のepoch適用+HEAD pin+shallow/graft/replace/非一意policy add rc=2を実装、333605d6を既知違反台帳へ追加、契約文をnet−168 bytes縮約 (コード+テスト+docs、branch worktree-dev-wave-t619-provenance-unified-predicate、変異matrix = baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=non-attributable-only)'
---

## 本文

- 2026-08-07 /rulings 第5回 (docs/archive/worklog-phase3-0807-299.md entry 299) の5点裁定を実装した。
  設計そのものは同日の先行 wave (`output/insights/2026-08-07_t619-provenance-range-permanent-design/`)
  が既に確定させており、本 wave は「実装しない」と裁定した D230 の恒久形を実装へ進めるだけの
  スコープだった。設計判断は {{D:t619-unified-predicate-implementation}} を参照。
- 着手前に T-614/T-618 (既知違反台帳への追加を実装した先行2 wave) の実装形を確認し、同じ整理
  (`KnownViolationSpec` タプルへ1 entry 追記、記録 commit へ実測値を書く) を踏襲した。
- **brief 前提の再実測 (F1 discipline)**: 設計時 (2026-08-07, `bb824d8b`) の「新規違反は
  `333605d680ec` の1件だけ」という前提を、12日後・数百 commit 後の HEAD (`f5677a66`) で
  出荷済み関数を import する使い捨てスクリプトを使い再実測した。4層 epoch は不変、
  実装面/CAB の gap は設計時と完全に同一の26 commit (実装面2件+CAB24件)、新規 finding は
  設計時と同じ1件のみで、新事実による裁定の巻き戻しは不要だった。
- 段2 codex プランは brief 自身の軽微な誤り (`_policy_commit()` の非一意検査を `-S` pickaxe と
  誤記していたが、実コードは `--diff-filter=A` を使う) を自己修正した。
- 段3 敵対相談2レンズ (計8所見、全件 real・採用) と段6 敵対レビュー2本 (nit 5件、うち2件を fix・
  3件は見送り: 裁定文書内の byte 数記載ミスは本記録で訂正、追加境界テストは不要と判断、
  docs/ai-provenance.md の別1箇所 (`導入 commit より後の...`) の文言統一は今回の裁定 (非遡及4箇所
  →1文統合) の範囲外として backlog に留めた) を実施した。段3 の blocker
  (`_ledger_policy_is_visible` への `authoritative` 配線漏れ) は実装で解消し、再発防止の専用テスト
  (`test_t619_authoritative_ledger_visibility_wiring_is_explicit`) を追加した。
- 受入投入時、他 wave の land (`301d62d13a0b`→`main=7d8b8a87`) と競合し1回目は
  `rc=70 reason=receipt-waiter-sha256-mismatch classification=restart-required` で失敗した。
  残骸 (receipt file・submodule 未初期化) は無く、単純再投入で解消した (コード起因ではない、
  複数 wave が同時に land する繁忙期の一時的競合)。
- 変異事前登録12件は全て実装後にコードで単一理由性を確認してから本登録した (段4 裁定どおり)。
  probe走 (全件 SURVIVED 期待) で実際の kill node を実測し、11/12 は事前予測どおり、1件
  (M10, 台帳 entry 削除) は予測より1件多い node で kill された (台帳 entry 削除が別テストの前提も
  壊すため、論理的に妥当と判断し本登録に反映した)。

## 次の一手差分

### 完了

- [T-619] D230 の統一述語を既定監査へ導入した。実測: `check_ai_provenance.py` の既定監査を
  この repo で実走し 4351 件・known-violations=43・新規違反なし (rc=0) を確認。
  `orchestrator/tests/test_check_ai_provenance.py` 317 passed / 0 failed (計算ノード実走、
  親が独立に確認)。`python3 tools/check_docs.py` 違反なし。変異 matrix は baseline PASSED・
  12/12 KILLED・SURVIVED 0・MISMATCH 0。受入全走 verdict=non-attributable-only
  (無関係な既知flake `test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed`
  1件のみ、非帰属checkerが確認済み)。
  remaining: none
  base: 9d9a666188b4f08e94fc1909f5e1263d4921bc53302b1a4dcab120919daf0b8c
