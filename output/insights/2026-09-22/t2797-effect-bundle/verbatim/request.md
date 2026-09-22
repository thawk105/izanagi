# 依頼逐語 (2026-09-22 08:5x JST、/dev-wave の引数)

[T-2797] (P2、D2200 項 1 の段階認可) B-5 生成器対照の発効束を完成させ、倍率 k と総 wall の倍率を添えて 1
  行で再提示するところまで進める。残りは 3 つ。(a) docs/b5-generator-contrast-preregistration.md §12 の全項目 (exact model ID
  の機械記録手段、prompt template と生成済み prompt の hash、知識射影、入力 schema、random 重み表・preimage、系列別 sweep 全順序、108 系列の
  schedule (同時 LLM 系列 ≤ p)、correctness / Tier0 / bench の exact 引数、事前登録 raw bytes の hash、環境・toolchain の版) の採取。(b)
  calibrator での rep 1 高値の確認。(c) 投入済み duplicate-skip の B 計上 (output/insights/2026-09-21/t2797-tier0/README.md §8 の N1)
  の確認。Tier0 (D2215)・node-local lock (T-2830)・親運用 (D2216)・walltime (D2217) は済んでいるので作り直さない。発効
  commit・校正・本走は承認後で対象外。規律 2 を緩めない。本題だけ、gate・検査・台帳の追加は scope 外。着手直前の local main から fresh
  worktree。
