---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t425-floor-bounded-prep
seq: 2
---

## {{D:t425-floor-schema-lightweight}}. between_run_floor.py の receipt schema は D581 の理由文を類推適用して軽量に保つ、D145決定5・公式H1/H2 registration の先取りではない

**決定:** `orchestrator/campaign/between_run_floor.py` の出力 JSON へ `schema_version`
(`"between-run-noise-floor/v1"`) を追加するにあたり、次の3点を確定する。

1. D581 (床値measurementの official mode 相当の事前登録儀式撤廃) は、between_run_floor.py が
   そもそも `official`/`pilot` 儀式を経ない設計であるため、この driver の手続きを直接は変更しない。
   D581の直接の適用対象は `s8b_floor_campaign.py` の official mode である。D581の理由文
   (「粗い provenance で足りる」既定方針) は、今回追加する receipt schema を D488型の重い
   事前登録・凍結儀式に寄せない上限根拠として類推使用するに留める。
2. schema_version は screening_driver.py 側との互換性契約 (欠落は legacy として許容、存在時のみ
   完全一致を要求) であり、将来の公式 H1/H2 registration receipt の契約を先取り・予約するもの
   ではない。
3. schema付与および screening 側の型/バージョン検証硬化は、D145決定5 が制限する「真正floor専用
   infra の新設」「floor値の正式floor昇格」のいずれにも当たらない。測定経路・compare閾値・
   admission ledger・公式artifactへの変更を一切含まないためである。D145決定5 自体はこの判断で
   再訪しない。

**理由:**
- 2026-08-20 の between-run floor 実験路依存鎖再監査 (`output/insights/2026-08-20_
  t425-dependency-reaudit/README.md`) が、この3点の確認を続 wave の段1 brief の最優先事項として
  指定していた。段2 codex plan と段3 敵対レンズ2本 (正確性・設計論) が実装前にこの3点を独立に
  検証し、段4 で親が裁定として確定した。
- 「D581 が本 schema 設計を承認した」と読める記録を残すと、将来この schema を公式 registration
  receipt へ格上げする際の判断を誤誘導する。D581 は間接的な類推根拠であり、直接の適用対象では
  ないことを明記する必要がある。

**却下した選択肢:**
- schema_version 欠落時も拒否する厳格版 — 公式儀式を経ていない既存 calibration JSON を全て
  無効化することになり、D581 の「粗い provenance で足りる」既定方針と逆行するため見送った。
- D488型の重い事前登録・凍結儀式 (durable admission 台帳・pre-commitment・launch certificate)
  をこの schema に持ち込む — 同上、対象が screening 用の軽量メタデータ検証にすぎない規模へは
  不釣り合いである。
