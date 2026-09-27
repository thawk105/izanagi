# 依頼の逐語 (2026-09-27、ユーザー直接起動の `/dev-wave` 引数)

[T-2865] (= [T-2848] の具体化、D2214 の軸 silo-function-policy) の段階 F として、実 LLM の 1 iteration E2E まで進める。正本:
  D2214・D2240・D2250・D2256、runbook docs/phase3-silo-policy-runbook.md (§0 の実走前ゲート〜§3)、記録
  output/insights/2026-09-26/t2865-silo-policy-stage-e/README.md と output/insights/2026-09-26/t2865-known-best-recheck/、worklog entry 1877 の
  carry。やること: (1) driver orchestrator/campaign/p3_s4_loop_policy.py 用の計算ノード投入経路を作る (現状の
  tools/pegasus/p3_s4_loop_pegasus.sh は p3_s4_loop 固定。driver 選択か兄弟 job body に、契約 test と投入許可台帳の登録を付ける。hooks
  と権限に触れる部分は Codex author (D95)、hooks/README.md の契約とテストに従う)。(2) 同じ動作点の stock baseline を同じ job
  で測る形を決める。(3) job Elapse の実測単価で見積もり、検査込みで 2 node 時間以上ならユーザー確認の後に投入する (D2212 項 4)。(4) runbook
  どおり 1 iteration を回す。coder と planner の入力には段階 D の projection.json の二値と射程文だけを渡し、偵察・小比較・再測の点
  ID・因子・比・順位は流さない。(5) 新しい job body で [T-2853] (1'') の保全口の opt-in を有効にし、(4) R2 の入口も同じ wave
  で置く。p3_s4_loop.py の flock 範囲は並走の [T-2104] の担当なので触らない。anomaly は即 reject、trace は compile 時に除去 (規律 1・2
  を緩めない)。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh worktree を作る。
