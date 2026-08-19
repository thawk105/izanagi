---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t470-accepted-consumer
seq: 2
---

## {{D:layer3-accepted-writer-api-scope}}. certified consumer「実結線」要求は、production caller が無い file scope では writer API 追加に限定する

**決定:** `layer3_report.build_accepted_report()` (520b76cc、"fail-closed future entrypoint")
を実際に呼び出す consumer を求められたが、対象 file scope が `layer3_report.py` とその
テストに限定されている場合、`render()` と対称な `render_accepted()` writer API の追加までを
scope とし、production caller (呼び手) の配線は行わない。これを「production consumer 実結線が
完了した」とは主張せず、production caller 配線・canonical 出力 path・completeness 対応は
別タスクへ明示的に分離する。

**理由:**
- 520b76cc wave の段4裁定 (`output/insights/2026-08-05_t470-t327-wiring/s4-ruling.md` §3) が
  同じ理由 (C02 arm injective binding・T-468 approval authority 未解決、DW-G04 の発火条件を
  書けない) で「certified selector の実結線」を後続タスクへ送っており、この前提は本 wave
  時点でも変わっていない (受入 receipt の `certifying` は構造的に false 固定のまま)。
- 段3・段6 の独立レビュー (計3レンズ) が同じ核心所見に収束した: production caller が
  repo 内にゼロのまま writer API だけを追加しても、「consumer が存在しない」問題を
  API 呼び出しの一段手前へ移すだけである。この事実を隠さず記録する方が、
  「実結線完了」という過大主張より安全である。
- production caller の配線には、caller の呼出し位置・canonical 出力 path・所有権・
  `autonomous_trial_completeness.py` の certified variant 対応という、対象 file の外側の
  設計判断が伴う。これは command 引数のスコープ (対象 2 file) を逸脱する。

**却下した選択肢:**
- production caller まで本 wave で配線する — 所有ファイル外の変更を要し scope 逸脱。
  加えて C02/T-468 未解決のため、配線しても実 E2E 正例は作れない (B-13 裁定と同型)。
- certified/non-certified 出力を分離する canonical path 規約を本 wave で新設する
  (段6レンズA所見1) — 実 caller が無い状態での規約制定は空虚な doc-only 制約になる
  (規律5「盛らない」)。docstring 契約 + race テストの軽量対応に留める。
