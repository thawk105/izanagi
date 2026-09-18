---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2691-rescue-checker-timeout-grace
seq: 2
---

## {{D:rescue-checker-exit-grace}}. landed checker の親待機は「子予算 + 終了余裕定数」とし、子予算・JSON 検証述語・全体残時間の cap は変えない

**決定:** `tools/check_branch_rescue.py` の `_landed_assessment` が子 `check_branch_landed.py` を待つ外側 timeout を
`min(子予算 + CHECKER_EXIT_GRACE_SECONDS, overall_remaining)` にする。`CHECKER_EXIT_GRACE_SECONDS = 2.0` は
module 定数 1 つで、CLI に出さない。子へ渡す `--timeout-seconds` (= `--assessment-timeout-seconds`)、受理する JSON の形・
schema・rc↔verdict 対応、`overall_remaining` による最終打切りは 1 bit も変えない。

**理由:**
- 子は自分の期限を `Git` 構築時 (interpreter 起動後) から数え、期限で `indeterminate/assessment-timeout` の JSON を
  書いて rc=2 で終わる。親の期限は `communicate()` 起点で同値だったため、子の JSON は常に親の kill に間に合わず
  (実 repo で 0/2)、掃除の landed 判定は `checker-timeout` (`child-report-unavailable`) に落ちていた。
- 変更は D498 と同型 — 宣言した子予算を親が黙って削っている状態の是正で、JSON 検証述語は不変、時間内に回収できる
  契約準拠の報告 (`assessment-timeout` だけでなく期限後に届く `landed` / `not-landed` も) が増える。
- 2.0 s の根拠は login node 12 走 (load 24〜35、T=1 ×10 / T=8 ×2) の wall − T = 0.087〜0.134 s の max × 約 15
  (DW-O13 の「実測分布の max への倍率」)。共有 FS 高負荷は未測定で、超えれば従来どおり `checker-timeout` に戻るだけ
  (受理集合は緩まない)。
- 総待機の上限は `max_assessments × (子予算 + 2 s)` へ伸びるが `--timeout-seconds` (既定 300) の cap が残る。

**却下した選択肢:**
- 子へ `子予算 − 余裕` を渡す — `--assessment-timeout-seconds` の下限 1 で 0 以下になり CLI 契約と衝突、子予算の意味も変わる。
- 余裕を CLI 引数にする — 実測に基づく定数 1 つで足り、公開設定面を増やす理由がない。
- 起動所要を実測して控除する — 控除量が観測値依存になり閾値が再び可変になる (D498 の却下と同じ)。
- `_audit` の子 (`audit_dangling_commits.py`) へ deadline を渡す — 同値問題ではなく、新しい子の期限契約を設ける別件。
- overall 値を厳密な wall 上限にする (準備・後処理を含める) — 既存の限界で本件の欠陥ではない。実害の観測なし。
