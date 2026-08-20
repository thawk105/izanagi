---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1142-n-pilot-scaleup
seq: 1
---

## {{D:n-pilot-r33-scope-defer}}. 8b oracle n-pilot の R=33 拡張実測は admission 機構の再設計が要り、当 wave では実装を見送り統合設計をinsightへ記録する

**決定:** indifference-zone 選択のサンプルサイズ較正 n-pilot を事前登録済み目標 R>=32
(コード上の制約により実質 33) まで拡張実測するための投入物を準備しようとしたが、
admission 機構自体の非自明な再設計が要ることが判明したため、当 wave では実装せず、
段2 codex plan と段3 敵対相談 2 レンズ (正しさ境界・整合実効性、計15件の real 所見) を
統合した改訂アーキテクチャ設計を
`output/insights/2026-08-20_t1142-n-pilot-r33-admission-redesign/README.md` へ記録する
に留める。実装は次の独立 wave へ送る。既存 R=11 実測 (`measured_distributions.md`) は
「予備的下限」として削除・改変せず保存し続ける。

**理由:**

- pegasus02 実機の admission ledger を直接確認したところ、n-pilot の観測許可
  (`reserve_n_pilot_holdout_observations()`) は cell を
  `(freeze_sha256, freeze_holdout_key, configuration_id, ccbench_pin, env_tag,
  observation_role)` の6項目 (campaign_run_id を含まない) で排他的に claim する
  一発勝負ロックであり、既存の R=11 実測がこのロックを既に消費済みだった。同一条件での
  「追加」は admission 機構の設計上、構造的に不可能である。
- この壁を解く方向性 (observation_role に新世代を追加し reserve/consume を分離する) は
  段2 codex plan が示したが、正しい実装には以下がすべて必要と段3 敵対相談 (2 レンズ、
  計15件の real 所見) で判明した: 世代の一回限り性を role allowlist だけに頼らない機構
  (role 追加自体を機械的に一回限りへ縛る仕組み)、consume-only job 間の build cache
  独立性の保証、`build_schedule(n=33)` を一括生成してから 132-row ずつ 3 allocation へ
  slice する canonical schedule 生成方式 (3 個の 11-round schedule を連結する方式は
  `complete-block-v1` の deterministic 生成と一致しない)、claim 発行の all-or-nothing
  transaction化、`consume_n_pilot_attempt_ticket()` の関数契約変更、
  `aggregate_results()`/`_result_document()` の同時書き換え、CLI の相互排他バリデーション、
  job script に加え submission wrapper の変更。これは「投入スクリプトの準備」という
  当初 scope を大きく超える規模である。
- 変更対象 (admission の排他 claim) は、事前登録が「不可逆・一度きり」と明記した観測承認
  を機械的に強制する安全装置であり、正しさゲートに準じる慎重さを要する。1 回の軽量 wave
  で拙速に実装するのは、必要なコンポーネントだけを段階的に足す方針と衝突する。
- 既存 R=11 実測は「対象条件の between-run 実測が0件だった状態を初めて埋めた予備的下限」
  として既に使用可能な形で保存済みであり、R=33 への精緻化は緊急ではない。

**却下した選択肢:**

- **そのまま段5実装へ進める** — admission 機構という正しさゲート隣接領域の再設計を、
  実装単位分割・敵対レビュー2本・変異matrix・受入まで含めて1軽量waveで安全にやりきる
  にはリスクが高すぎる。
- **scope を絞った部分実装** — durable receipt 無しでは CLI/job script だけを先に作っても
  「動く投入物」にならず、当初の目的 (投入スクリプトの準備) を達成しない。
- **新しい git clone で admission root を分離し既存 key を再 claim する** — 段2 codex
  plan が「一度きりの安全装置を回避する」として明示的に却下済み。本決定もこの回避策を
  前提にしない。
