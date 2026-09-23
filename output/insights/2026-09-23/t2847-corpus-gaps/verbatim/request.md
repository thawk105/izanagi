/dev-wave [T-2847] の残り (1) (P1、VLDB 差分分析 P0) — 小履歴コーパスの未被覆 2 案 (F03・F06 = 同じ取引が同じ key を 2 回読む合成入力)
  と、B06 の分類 G1c を独立の期待値として固定する assert を test として実装する (Codex author、D95)。設計 =
  output/insights/2026-09-22/t2847-verifier-detection-design/README.md §3・§3.1 (期待する辺の集合と判定)。新しい test は新規 file (例
  orchestrator/tests/test_verifier_corpus_gaps.py) に test 内の合成 trace で書き、orchestrator/tests/test_verifier.py・fixture
  dir・orchestrator/verifier/ は編集しない (T-2854 の存在履歴 wave と並走するため)。期待と合わない場合は verifier
  を直さず、欠陥として構造化して記録し返す。担当分割: (2) は稼働中の t2847-patch-verify、(3) は別 wave。規律 2 は緩めない。本題の test
  だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh worktree を作る。
