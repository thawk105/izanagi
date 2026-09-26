単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s4-ruling.md — 段 4 裁定 (plan v2・事前登録)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/verbatim/T-2273-origin.md — 依頼の逐語 (「本題だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/codex/s5-author-out.md — 実装子の報告。
- レビュー対象 (commit `2ebf25e24`、作業木 /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe): `tools/t2273_replica_runner.py`、`tools/t2273_replica_plugin.py`、`tools/t2273_replica_analyze.py`。第 4 回の実走版との差分は `git diff 7f38ac7fd 2ebf25e24 -- tools/`。

## レンズ B — 過剰・削除と、走らせて初めて分かる壊れ方

1. s4-ruling にない機能・分岐・検査が足されていないか。削っても事前登録の判定量と有効性が出せる部分 (過剰) を挙げよ。逆に、事前登録の判定量・有効性の項目で**実装されていないもの**を挙げよ。
2. 計算ノードで 1 回走らせて初めて落ちる型 (1 job ≈ 1,000 秒、1 回落ちると取り直しの費用がかかる): import の失敗、path の前提 (tempdir・`/scr`・job dir)、clean env (generic dispatch は `HOME LANG LANGUAGE LC_ALL LC_CTYPE LOGNAME PATH TZ USER` だけを渡す)、例外が握りつぶされて無効な走が有効に見える経路、逆に record-error が 1 件出ただけで全対が無効になる経路。smoke (`--smoke both`) がそれらを本走前に捕まえるか。
3. 第 4 回の実走版から変えた部分のうち、既存の観測 (span・資源標本・guard) を意図せず壊した箇所。
4. analyzer の出力が、親が結論 (「(a) を実装する / この基準では確認できず (b) へ」) を書くのに十分か。足りない欄・誤解を招く欄。

read-only で書込可能 tmp が無いので静的検査でよい。実走は親が計算ノードで行う。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ。

## 出力形式

- `## 所見` — ID (RB1, ...)、重大度 (must-fix / should / nit)、根拠 file:line、放置時に診断の結論がどう変わるか / 走が何秒無駄になるかを 1 行、推奨修正 (削除を含む)。
- `## 総括` (3〜6 行、GO / 修正後 GO / NO-GO)
