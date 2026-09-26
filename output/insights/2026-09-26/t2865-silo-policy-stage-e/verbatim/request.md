# 依頼の逐語 (ユーザー直接起動の /dev-wave、2026-09-26 18:4x JST)

[T-2865] silo-function-policy 軸 (D2214) を段階 E (兄弟 driver・tool なし coder role の C++ 版と IR 版・runbook・firewall
  の機械化。docs/axis-onboarding.md §3-E、§4 第 3 列の型なので planner は外す) へ進める。裁定 = D2243 項 1 (控え
  /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-26-rulings-full35-verdicts.md)。入力は段階 C
  output/insights/2026-09-22/t2857-silo-policy-stage-c/README.md・段階 D output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md
  (後段へ渡すのは D の projection.json の二値と射程文だけ)・設計 output/insights/2026-09-21/silo-function-synthesis-space/README.md。D2240
  の小比較 (output/insights/2026-09-23/t2865-silo-policy-known-best-compare/) の点 ID・因子・比・順位は coder の入力へ流さない (手順書
  §3-D)。.claude/agents/ の具体差分は wave 内でユーザーの明示承認を取ってから入れる。実装は Codex author (D95)、正しさゲートは不変 (anomaly 即
  reject・trace は compile 時除去・毎回検証して構造化フィードバック、規律 1〜3 を緩めない)。計算投入は図 1 枚あたりの node
  時間を示し、検査込みのタスク合計が 2 node 時間以上なら投入前にユーザー確認 (D2212 項 4)。段階 F (実 LLM の iteration) は別
  session。着手直前の local main から fresh worktree を作る。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
