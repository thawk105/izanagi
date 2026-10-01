/dev-wave silo-function-policy 軸の系列 C で certified になった候補 3 本 (iteration 2〜4。同じ job の stock 比
  2.17・1.86・2.64、各 1 観測) を R2 で再測定し、比が再現するかを確かめる ([T-2865] の候補の再測定)。着手直前の local
  main から fresh worktree と新しい submit checkout を作る。入口は docs/phase3-silo-policy-runbook.md §3.1
  (IZANAGI_S4_POLICY_MODE=replay、--replay-proposal、evaluation_purpose=r2、LLM なし、loop
  の予算は使わない)。入力は記録 output/insights/2026-09-29/t2865-silo-policy-series-c/README.md と repo 外
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-series-c/evidence/ の保存 proposal。候補ごとに 2
  回を目標とし、同じノード・同じ round に stock を置いて同時刻の比と abort 率を取る。反復の識別子は R2
  に閉じた最小の対応で扱う。共有 driver の編集が要り、稼働 wave (md_24 の p3_s4_loop_policy.py、pin-f・md_42 の
  test_p3_s4_loop.py) と衝突するなら、各候補の初回 R2 までで区切る。trace 保全 (§3.2) と正しさ gate
  は実走と同じで、anomaly の候補は即失格にする。smoke の後に積算し、2 node 時間以上なら land 調整役に諮る。成果は
  insight と spool fragment。stock
  比の再現は最高水準に対する優位の証明とは別に書く。本題の再測定だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。規律 2 は緩めない。
