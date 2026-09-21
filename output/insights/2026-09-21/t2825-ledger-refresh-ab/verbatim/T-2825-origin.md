# [T-2825] 依頼の逐語 (/dev-wave の command 引数、2026-09-21 受信)

[T-2825] (entry 1777、D2107、D1936 項 35、一次資料 output/insights/2026-09-21/t2817-acceptance-bottleneck-3/README.md §5 (a))
  tools/update_acceptance_duration_ledger.py --refresh で orchestrator/tests/acceptance_duration_ledger.json を最新の緑走 1 走の JUnit
  から再生成し (T-2724 追加 node を含む未収載 334 unit の再登録、凍結 8 suite は据え置き)、同一 tip の実受入で隣接対 (A = 旧 ledger / B = 新
  ledger、3 対以上、D357、T-2766 の事前登録の形) の shard-0 W / O_max / O_max − L / 最大占有 worker の item 列を測ってから land する。参考値
  (model 差 19.5 秒、観測 O_max − L 中央値 62.7 秒) は効果ではないので別々に持ち、実効果に上下限を置かない。active_v2 系 key の base 構築が t=0
  の 5 本と同時に走ると L 自身が伸びる可能性を対の判定に含める。着手直前の local main から fresh worktree。受入の投入は門番 (leaders ≤ 1 ∧
  load ≤ 60) に従う。本題だけ。gate・台帳・一般化の追加は scope 外。

## worklog entry 1777 の次の一手 (逐語、docs/worklog.md)

- [T-2825] **P1・新規**: D2107 の refresh mode で `acceptance_duration_ledger.json` を最新の緑走 1 走の JUnit から再生成し (T-2724 追加 node を含む未収載 334 unit の再登録)、同一 tip の実受入で隣接対 (A = 旧 ledger / B = 新 ledger、3 対以上、D357、T-2766 の事前登録の形) の shard-0 W / O_max / `O_max − L` / 最大占有 worker の item 列を測ってから land する (D1936 項 35)。参考値は別々に持つ: T-2817 README §5 (a) の model 差 19.5 秒 (固定所要 model、中央値のある未収載 333 node 全部を更新、実 wall の予測ではない) と、観測の `O_max − L` (保存済み 21 session の中央値 62.7 秒、Job B 65.0 秒 = 最大占有 worker と L の差であって再登録の効果ではない)。実効果は未測定で上下限も置かない。active_v2 系 key の base 構築が t=0 の 5 本と同時に走ると copy 配置が 100 秒級になり L 自身が伸びる可能性 (未測定) を対の判定に含める。
