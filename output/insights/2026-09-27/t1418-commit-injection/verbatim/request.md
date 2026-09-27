/dev-wave [T-1418] tools/mutation_harness.py (--runner-mode dispatch の file-swap 方式) が campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
  の閉包 (loop.py・pipeline.py・wal.py・ident.py・execution_guard.py・env_contract*.py・verifier/* など) のメンバーを変異検査できない
  (docs/failures.md の F424)。ratified_enforcement_source fixture の disk==HEAD blob 検査と構造的に衝突するためで、これまでの wave は手動の
  commit-reset で回避してきた。harness 側か fixture 側のどちらに、閉包を横断する安全な変異経路を持たせるかを段 1 で決めて実装する。閉包の drift
  検査を弱めない (等価変異・drift 層の区別は既存の変異台帳の作法に従う)。規律 2 を緩めない。本題の実装だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh worktree を作る。
