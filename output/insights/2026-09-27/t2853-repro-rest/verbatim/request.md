/dev-wave [T-2853] 再現パッケージの残りを進める: (i) 新しく論文根拠になった job dir のうち [T-2850] 試走 v2 (所在は
  output/insights/2026-09-27/t2850-trial-v2-analysis/README.md から引く)、[T-2849] MOCC 疎通、[T-2865] 段階 F の job dir
  にだけある論文根拠データを、既存の手順 (output/insights/2026-09-23/t2853-repro-package-archive/README.md) で repo 外
  /work/1/SFC/tanab/izanagi-repro-archive/ へ写し、sha256 を照合する (trace を保全済みの t2849-mocc-conn・t2865-stage-f は重複させない)。(ii)
  R2 (保存候補の LLM なし再評価) の投入単位を決め、図ごとの node 時間を Elapse 単価で見積もる
  (output/insights/2026-09-23/t2853-figure-rerun-plan/README.md)。投入は 2 node 時間以上ならユーザー確認後で、この wave
  は見積りまでで返してよい。公開範囲の最終確定は投稿前なので扱わない。凍結 chain は足さない (D320)。着手直前の local main から fresh
  worktree。本題だけ、仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
