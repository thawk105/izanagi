**B-1 / should-fix / [R2 図の provenance](</work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/figure/fig6_r2_a2_certification.provenance.json>) の `reproduction` / 再現コマンドをそのまま実行すると入力 hash 検査で止まる。 / [insight §5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/README.md:130) もこの制限を認め、別途 wrapper 経由のコマンドを示している。 / provenance の再現手順を実際の wrapper 呼び出しに合わせるか、同じ場所に実行可能な手順を明示する。**

**B-2 / should-fix / [R2 図の caption](</work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/figure/fig6_r2_a2_certification.provenance.json>) / 末尾が「旧系列との符号差」を示唆するが、この図の R2 と原 attempt の効果はともに正である。図だけを読む人には誤解を招く。 / [insight §5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/README.md:127) に定型文との注記はあるが、図には届かない。親の [P2 裁定](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/verbatim/s4-ruling.md) もこの文の意味を再検討し、少なくとも図と一緒に見える注記を置く。**

**B-3 / nit / [insight §6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/output/insights/2026-09-29/t2853-r2-fig6/README.md:150)・[worklog](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig6/docs/spool/worklog/2026-09-29-worktree-dev-wave-t2853-r2-fig6-1.md:13) / 「受入全走 1 回」と記す一方、実測を記すとした worklog にその値がまだない。 / 2.41 node 時間は測定実績 2.16 と受入見積り 0.25 の和であり、現状の「見込み」という区別は正しい。 / 親の受入実走後、実測値を worklog に追記して総費用を確定する。**

見積りの算術と投入前確認、別 attempt としての扱い、非合成、条件差と性能認証の限界は、指定資料の範囲で適切。追加の gate や台帳を求める所見はない。

**NO-GO**

## 総括

図の caption と provenance は、insight の説明を離れると誤読または再生成失敗を招く。
両者を直せば、依頼の本題に対する不足は見当たらない。