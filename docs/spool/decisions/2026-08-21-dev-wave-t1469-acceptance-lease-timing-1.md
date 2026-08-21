---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t1469-acceptance-lease-timing
seq: 1
---

## {{D:lease-preclaim-staleness-evidence}}. D631 が残した実測gapを埋めた — 陳腐化率は十分低いことを示さず、却下は維持

**決定:** D631 の「閉じない残余」(`docs/decisions.md:25286-25288`) が要求した「claim 前に
merge・受入テストを済ませていたら実際にどれくらいの頻度で無駄になっていたか」の定量実測を、
新規lease claim・新規production変更なしの事後解析で実施した (`output/insights/2026-08-21_t1469-acceptance-lease-timing/README.md`)。
既存artifactから機械的に再現できる最小の母集団 (n=7) では、6/7 (85.7%) が claim 前 merge を
無駄にしていたと推定され、待ち時間の中央値は約42分だった。この結果は D631 が再訪の条件とした
「陳腐化率は十分低い」を支持しない。したがって D631 の却下 (`docs/decisions.md:25255-25289`)・
D270 の現行設計 (`docs/decisions.md:12433-12456`) をいずれも維持し、supersede は検討しない。

**理由:**
- n=7 は統計的な決定力を持たないが (`output/insights/2026-08-21_t1469-acceptance-lease-timing/README.md`
  5節-1)、母集団の6/7が閾値 (待ち区間内の他wave land 1件以上) を超えており、「十分低い」と
  解釈できる方向の証拠は無い。
- 除外した4件の複数試行waveは一般に手間取ったwaveである可能性が高く、除外はstale率・
  待ち時間の両方を過小評価する方向に働く (同insight 5節-2)。この方向のバイアスを補正しても
  結論は変わらない。
- D631 自身が「decision を残さず記録のみに留める」選択肢を明示的に却下し、理由を
  「同型の設計が将来再訪されたとき、同じ調査を繰り返さないよう却下理由を正本へ残す方が
  安価」としている (`docs/decisions.md:25283-25285`)。今回のgap充足も同じ理由で記録する。

**却下した選択肢:**
- **この結果を worklog にだけ書き、decision を新設しない** — worklog は
  ローテーション・archive移動の対象であり、D631と同じ理由 (将来の再調査コスト) で
  decisions.md へ残す方が安価。
- **母集団を広げるため新規instrumentationを実装する** — 本wave は docs-only・
  production変更禁止のscopeであり、除外4件の再試行attempt識別を可能にする改修は
  別waveの範囲。

**閉じない残余:** 除外した4件 (複数試行wave) の attempt 単位での claim試行開始時刻を
一意に復元する instrumentation は未実装のまま。これが実現すれば n を最大11まで拡張できる。
