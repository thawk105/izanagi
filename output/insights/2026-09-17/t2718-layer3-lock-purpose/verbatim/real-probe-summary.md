# 実 corpus probe の結果 (親が patch 適用後の wave worktree で実行、2026-09-17)

probe: Codex author が書いた `tools/t2718_real_corpus_probe.py` を repo 外 (`wave-t2718/t2718_real_corpus_probe.py`) へ退避して実行。生 JSON は `wave-t2718/real-probe/*.json`。campaign 配下へは書いていない。

| 主体 | HISTORICAL_RAW `_read_campaign_lock` | CERTIFIED_ACCEPTANCE `_read_campaign_lock` | `build_report` | lock/WAL bytes |
|---|---|---|---|---|
| exact-62 t2364-20260907b rr5 (…-1af9fc2b) | 成功、`DecodedHistoricalCampaignLock`、記録 grammar 62 path | `Layer3ReportError: campaign.lock schema が不正` (cause `CampaignLockCodecError: authority.contract_loader_blob_sha256s の exact key 集合が不正`) | `Layer3ReportError: campaign search_config の records/threads が整数でない` (cause None) | 不変 |
| exact-62 t2364-20260907b rr50 (…-5efd479e) | 同上 | 同上 | 同上 | 不変 |
| exact-62 a6-20260908b rr95 (…-1e7d99f2) | 同上 | 同上 | 同上 | 不変 |
| exact-24 t2022-20260827 rr5 (…-df07b695) | 成功、記録 grammar 24 path | 同上 (拒否) | 同上 | 不変 |
| 63 対照 a6-20260909b rr95 (…-a4efd902) | 成功、63 path | 成功、`DecodedCampaignLock` | 同上 (records/threads) | 不変 |

変更前 (親の段 1 実測): exact-62 / exact-24 は `build_report` が `campaign.lock schema が不正` で 755 行 (decoder) で止まっていた。変更後は 5 本すべてが同じ到達点 (records/threads 整数検査) で止まる。

# I5 検査 (変更前 W / 変更後 I で tracked campaign 3 本の build_report 出力を比較、generator sha256 を除く)
- output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90 (v1 lock): report OK、bytes 同一。
- p3-s8a-trigger-loop-…-3f72ecd5 / p3-s8a-trigger-sweep-read-heavy-sweep-654d5cd7: 変更前後とも同じ admission 拒否文 (legacy-unclassified)。
- diff: IDENTICAL。
