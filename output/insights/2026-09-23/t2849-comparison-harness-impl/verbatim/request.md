[T-2849] 5 手法比較基盤の実装と [T-2853] 残り (1) の trace 保全口を 1 wave で行う (Codex author = D95)。T-2849: 設計 D2220・insight
  output/insights/2026-09-22/t2849-comparison-harness-design/README.md §11 の単位 1〜7 (S1 = silo の backoff 値空間。B-5 の module
  は編集せず兄弟 module に置く。新しい gate・検査・台帳は足さない)。単位 8 (MOCC、[T-2858] の pin 前進後) と第 2 プロトコルの疎通は scope
  外。T-2853 (1): 標準評価経路 orchestrator/campaign/pipeline.py (約 2160〜2178 行、一時 dir を検証後に rmtree している箇所)
  に、論文根拠の実験では作業保管を全量 zstd で残す保全口を入れる (insight output/insights/2026-09-22/t2853-repro-package-estimate/README.md
  §7・§11)。T-2853 の (2)(3) は同時に投げる別 wave が持つ (分担済みなので譲り合わない)。稼働中の t2857 (silo 関数方策の file
  群・docs/axis-onboarding.md) と t2854 (CCBench・verifier) の編集面へ広げない。正しさゲートと trace の compile 時除去は変えない (規律
  1・2)。開発の検査を含む job 合計が 2 node 時間以上なら、job Elapse の実測単価で見積りを示し、投入前にユーザー確認を取る (D2212 項 4、第 31
  回項 1)。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh worktree を作る。
