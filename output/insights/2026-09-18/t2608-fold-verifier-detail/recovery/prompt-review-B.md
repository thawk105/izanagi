単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2608-fold-verifier-detail
必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2608-fold-verifier-detail/CLAUDE.md の絶対規律 — 読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2608-fold-verifier-detail/docs/dev-wave/workers.md の DW-S06-A — 読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2608-fold-verifier-detail/s4-ruling.md — 読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2608-fold-verifier-detail/mutation-final.json — 読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2608-recovery/HANDOFF.md — 読めなければ即停止。

T-2608既存成果物の独立引継ぎ監査。対象固定tip 2b1015486096566210386b138333a89b7f94a526。git diff main...2b1015486 の実装2fileと関連producer/consumerを読む。親brief・裁定自体も攻撃対象。
レンズ: 過剰・削除レンズ。scope拡張や恒真テスト、一次資料と実装・変異結果の食い違い、consumer取り残し。
実装は tools/spool_fold.py の DevWavesError message 6行と orchestrator/tests/test_spool_fold.py の20行。tools/dev_waves/schema.py、redaction.py、git_state.pyは変更禁止で静的追跡。規律2を緩めず、既存受理集合を維持するか。生pathや子出力が追加されないか、実際のproducer値を調べる。sanitizer一般保証を過大主張しない。
F649 [恒真ゲート][テスト代表性] の再発として実callee不通過を疑う。[捏造/幻覚][ドリフト][権限逸脱] の観点も必要範囲で確認。
旧受入はrc70で終了、2回目の赤は test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed の10秒timeout。受入緑とは扱わない。親が単独実走中。新受入・land・テストを起動しない。
read-onlyで書込tmpなし。pytest緑は要求せず静的監査のみ。コード/docs/commitを変更しない。scope外のgate・台帳・一般化を提案しない。残余は明記。
予算が尽きそうなら途中結論を以下形式で書いて終える。
## 総括
GO/NO-GO、must-fix件数、未実走を明記。
## 所見
real/refuted、file:line、影響、最小修正。なければなし。
## 検証範囲と限界
sanitized detail経路、受理/拒否、正例・負例、変異証拠の区別。
