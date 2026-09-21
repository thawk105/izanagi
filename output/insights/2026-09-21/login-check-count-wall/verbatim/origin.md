# 依頼文 (逐語、2026-09-21、`/dev-wave` 引数)

dev-wave 1 本が login で回す検査 (tools/check_docs.py、三軸語走査の権威 CLI、check_ai_provenance.py 全史監査、fold
  dry-run、find-fold-owned.py) の実行回数と wall を直近 landed wave 12 本の job dir (log の mtime、HANDOFF.md の時刻) から再構成し、wave
  あたりの合計と「契約で必須の回数」「習慣で増えた回数」を分ける (診断のみ、実装 0 行、着手直前の local main から fresh worktree)。全史監査は
  T-2803 後の warm 22 秒 / cold 58 秒を前提に、実 wave 内で cold になった回数と原因 (checker sha 変更・.gitattributes・partition)
  を数える。結果は効果見積り付きの裁定パッケージ (回数を減らせる契約上の余地、順序の入替え) として insight に置き、検査の受理集合・判定・5
  分上限 (D690) は変えない。規律 2 を緩めない。診断だけ。gate・検査・台帳・一般化の追加は scope 外。
