---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: worktree-rulings-20260820-all
seq: 1
---

## 再発

### F272

- **再発: 2026-08-20** — 未採番のrulings-inbox候補 (DW-S07段記録容量問題、一次資料
  `2026-08-19-t828-dw-s07-acceptance-ordering-note.md`) が同日朝の別 `/rulings` セッションで
  既に裁定・採番済み (T-1430) だったにもかかわらずinbox未削除で残存し、後発の収集が同一内容を
  未解決として再提示しかけた。既存の恒久対応 (`ruling-status-follow-to-latest-entry`) は既存
  T-IDの照合を想定するが、本件は対象が**裁定後に初めて採番される**未採番候補であり、
  T-ID化前のinboxファイルには機械的な事前照合手段が無かった。worklog全体を一次資料ファイル名で
  全文検索し archive 側の「2026-08-20裁定」マーカー付き実体を発見して手動で回避した
  (未機械化のまま)。

### F417

- **再発: 2026-08-20** — 2026-08-19 の supersede (「恒久対応は完了に訂正する」、D551経由) の
  1日後、[T-1362] のwaveが同一の `MAX_BATCH_REQUESTS` 超過に再び当たった (実測50072、main比
  commit 7件追加のみ)。D551本文の実測 (適用直後の local main で余裕は残り16件) を読み直すと、
  supersede 時点で既に再超過は時間の問題だったと判明する。D551が narrow したのは
  `validate_condition_freeze_at` 1経路のcostだけで、`_batch_oids` を通る他経路 (F418が指す
  candidate commit祖先集合 × generation-freeze追跡ファイル) は履歴比例のまま残っている疑いが
  強い。ユーザー裁定 (2026-08-20、詳細は本fragmentの worklog 側) により、上限引き上げは
  再度不採用のまま維持し、D551と同じ原則を `_batch_oids` の残る全呼び出し経路へ適用する恒久
  対応を worklog 新規項目として起票した。
