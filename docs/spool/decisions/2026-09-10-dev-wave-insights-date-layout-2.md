---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-10
wave: dev-wave-insights-date-layout
seq: 2
---

## {{D:insights-date-layout}}. 新規insightを日付配下に置き、既存資料は参照を保って整理する

**決定:** 新規資料は `output/insights/YYYY-MM-DD/topic.md` または同日配下のtopicディレクトリへ置く。
既存資料はbytesを変えずに日付別配置へ移し、旧名索引を残す。固定パスを使う実験・凍結資料と、
移動で壊れる既存リンクは旧位置を保つ。歴史的な名前の観測だけを現役pinと同一視しない。

**理由:** 直下1077件で閲覧障害が実在した。588directoryの移動で534件まで減らせ、
基準の全17328fileを保存できた。過去の本文・hashを一括更新する必要はない。

**却下:** 旧名symlinkを全件残す案は直下件数を減らさない。索引だけで直下1000超を残す案も採らない。
証拠内部のraw過密は配置・記録を維持し、分割索引から全fileへ直接到達できるようにする。
