/dev-wave [T-2865] の付随: D2240 の小比較で同 job の静的 10 µs (既知最良) を 6〜7% 上回った IR 3 点を、1 点 1 job で別 job 再測する (D2243 項
  1「論文でこの 3 点を既知最良超えとして書く前に行う」、控え
  /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-26-rulings-full35-verdicts.md)。機構は既存の偵察 driver
  orchestrator/campaign/silo_policy_recon.py の phase compare (1 job = IR 点 + abort0・stock・B0-L-W0・fixed10、dispatch_compute.py --task
  generic)。判定規則 (何をもって「再現した」とするか) は結果を見る前に insight へ書く (規律 3)。記録は
  output/insights/2026-09-23/t2865-silo-policy-known-best-compare/README.md の後継として新しい insight に置く。点 ID・比は段階 E / F の
  coder・planner の入力へ流さない (手順書 §3-D)。検査込みのタスク合計を job Elapse の実測単価で見積もり、2 node 時間以上ならユーザー確認 (D2212
  項 4)。規律 2 を緩めない。着手直前の local main から fresh worktree を作る。本題だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外。
