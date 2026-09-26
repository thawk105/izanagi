# 依頼の逐語 (/dev-wave の引数、2026-09-26)

[T-2853] の残りのうち次の 2 つを行う。(1') 標準評価経路の trace 保全口 (env IZANAGI_TRACE_ARCHIVE_ROOT、D2233) の inventory に、R1
  入力一式の残り (verifier の argv・repo commit・pin・patch・verifier module の sha256) を D2160・B-8 の runner と同じ組で足す。(5')
  output/insights/2026-09-23/t2853-figure-rerun-plan/README.md に従い、生成器のある 17 図を描き直して一致を確かめる (node 時間 0)。作図は
  tools/plotting/FIGURE_CONVENTIONS.md に従い、計測機の外で行う。fig1 の生成器作成と fig15 の repo 外入力の写しは含めない。正本は worklog の
  [T-2853] carry と output/insights/2026-09-23/t2853-repro-package-archive/README.md。着手直前の local main から fresh worktree を作る。実装は
  Codex author (D95)。規律 2 は緩めない。本題だけで、凍結 chain や仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外 (provenance
  は粗い粒度で足りる、D320)。
