# 親の実測 (現行 code = local main 1042a1bc9 と同一の layer3_report.py sha256 abe0529d…)

probe: /home/SFC/tanab/.claude/jobs/f3d94a9d/tmp/probe_render_real.py (build_report を呼び、結果か例外を JSON で出す。読取り専用)
実行: worktree で `PYTHONPATH=. python3 probe_render_real.py <campaign_dir> <output_root>`、output_root = `<...>/jobs/<rrN>`。

## exact-62 実 lock: t2364-20260907b rr5 (…-certification-rr5-1af9fc2b)
{
 "status": "Layer3ReportError",
 "message": "campaign.lock schema が不正",
 "cause": "CampaignLockCodecError: authority.contract_loader_blob_sha256s の exact key 集合が不正",
 "lock_bytes_unchanged": true
}
→ 中央 admission (HISTORICAL_RAW、build_report:733) は通り、_read_campaign_lock (755) で拒否。起票どおり。

## exact-24 実 lock: t2022-20260827 rr5 (…-certification-rr5-df07b695)
同じ拒否 (message / cause とも同一)。

## 現行 63 対照: a6-20260909b rr95 (…-certification-rr95-a4efd902)
{
 "status": "Layer3ReportError",
 "message": "campaign search_config の records/threads が整数でない",
 "cause": null,
 "lock_bytes_unchanged": true
}
→ decoder は通過し、WAL 読取・bytes 照合・knowledge provenance も通過した後、layer3_report.py の records/threads 整数検査で止まる。

## exact-62 実 lock の search_config (jq で読取)
records: null、threads: null。keys: aggregate, attempt_id, build_admission, current_pin, effect, historical_pin_role, ordered_cells, ordered_genomes, protocol_schema, protocol_sha256, reps, screening, study, verify, workload。
→ paper-story 認証 campaign の形であり、`build_report` の s4/s8a-loop 形 (records/threads 必須) と合わない。grammar と無関係。

## 実 corpus の所在 (repo 外、読取専用)
/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b/jobs/rr5/campaigns/paper-story-a2-rr5-paper-story-a2-certification-rr5-1af9fc2b
/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b/jobs/rr50/campaigns/paper-story-a2-rr50-paper-story-a2-certification-rr50-5efd479e
/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/jobs/rr95/campaigns/paper-story-a2-rr95-paper-story-a6-certification-rr95-1e7d99f2
(63 対照) /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260909b/jobs/rr95/campaigns/paper-story-a2-rr95-paper-story-a6-certification-rr95-a4efd902

## wal.py の型検査 (wal.py:1733-1769、親の読解)
`_decoded_campaign_lock_value`: `type(x) is DecodedCampaignLock` → そのまま、`DecodedNonCertifyingCampaignLock` → そのまま、dict で schema_version 無し → None (identity 扱い)、dict 以外 → `AttemptTopologyError("campaign.lock value が object でない")`。
`_campaign_lock_identity`: decoded が None でなければ `.identity`、None なら値そのもの。
→ `DecodedHistoricalCampaignLock` を渡すと AttemptTopologyError → build_report:817 で `Layer3ReportError("knowledge provenance 検証に失敗")`。これは decoder を直しただけでは残る第 2 の拒否点。

## 編集面重複 (親の実測)
layer3_report.py: 未着地 branch 0、dirty worktree 0。test_layer3_report.py: 未着地 branch 3 本は三点 diff 空、dirty worktree 3 本 (t2125-fix1/impl、t2566-b) は cmdline 0 件の残骸。
