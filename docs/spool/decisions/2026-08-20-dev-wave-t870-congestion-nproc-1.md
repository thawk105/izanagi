---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t870-congestion-nproc
seq: 1
---

## {{D:t870-congestion-nproc-scope}}. 受入全走への並列度低減 (T-870 item (e)) は現 evidence では実装しない

**決定:** T-870 系列の未着手項目 (e) 「queue 混雑時は待つのでなく並列度を下げる」
(`IZANAGI_TEST_NPROC`) を、受入全走 (`orchestrator/tests` フルスイート、`python3
tools/run_tests.py` 受入形 bare 呼出し) へ適用することは、現時点の evidence では実装しない。
`tools/run_tests.py` の local/dispatch 判定 (`orchestrator/campaign/login_headroom.py` の
`grant_budget`) は `IZANAGI_TEST_NPROC` を直接の入力として使わず、`recall_peak("tests-full")` に
基づく過去 peak の 1.25 倍見積りだけで判定する。現行 peak 記録 (4 GiB 上限相当) がある限り、
既定の呼出し経路では nproc の値や現在の空き容量に関わらず DISPATCH 判定が続く。この経路には
staleness/expiry/decay による自然回復が無い。

改善候補として、operator が明示的に一回限り peak 履歴を無視して local admission を再試行できる
opt-in 機構が段3 敵対相談2レンズから独立に提案されたが、`login_headroom.py` の並行アクセス・
ロック契約に触れる新規設計であり、本 wave の brief・段2・段3 が検証した対象 (nproc の直接効果) とは
別の設計対象である。専用の brief → plan → consult を経ていないため、本 wave では実装しない。

**理由:**
- nproc=4 での受入全走フルスイートの実 peak が 4 GiB 以内に収まり CAP_OOM を避けられるという
  直接証拠が無い (段2 codex プラン、段3 レンズ両方が確認)。
- `grant_budget()` の見積り計算 (peak×1.25 対 既定上限4GiB) は、現行 peak 記録がある限り nproc に
  関わらず恒常的に DISPATCH を選ぶ。これは段3 レンズ sol が file:line で確認したコードの恒常挙動で
  あり、nproc を下げるだけでは admission 判定に到達すらしない。
- D612 (`docs/decisions.md:24540`) が既に、既定 timeout 値の自動引き上げと `_is_acceptance_run`
  ベースの自動分岐を却下している。本決定はこの射程を再訪しない — 却下対象は timeout 値と受入形
  分岐であり、peak 履歴無視の明示 opt-in はいずれにも該当しないため、将来実装する場合も自動選択・
  `is_acceptance` 分岐を追加してはならない。
- 規律5 (段階導入・盛らない) に従い、当初の brief が対象としなかった新しい設計対象
  (safety-critical な並行アクセス ledger への機構追加) を同一 wave で実装へ進めない。

**却下した選択肢:**
- 現行 peak 記録・見積り計算式そのものを変更する (peak の重みを下げる、上限を上げる等) —
  当初 brief の対象 (nproc の直接効果) から逸脱し、`login_headroom.py` の既存 safety 契約への
  影響範囲が本 wave の段2/段3 では検証されていない。
- 「一定確率で local を再試行する」ような自動的な回復機構 — 明示 opt-in ではなく、D612 が拒否した
  自動選択と同種の設計になるため、次 wave でも採用しない前提とする。
