# 段 1 で親が実測した事実 (子はこれを再確認してよいが、勝手に置き換えない)

測定日: 2026-09-16。測定した checkout: `/work/1/SFC/tanab/izanagi` の `main` = `d97c423bd`。
wave worktree はこの main から作った同一 tip。

## 1. 対象 3 本の絶対 path (repo 外・読み取りのみ)

```
/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b/jobs/rr5/campaigns/paper-story-a2-rr5-paper-story-a2-certification-rr5-1af9fc2b/campaign.lock
/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b/jobs/rr50/campaigns/paper-story-a2-rr50-paper-story-a2-certification-rr50-5efd479e/campaign.lock
/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/jobs/rr95/campaigns/paper-story-a2-rr95-paper-story-a6-certification-rr95-1e7d99f2/campaign.lock
```

同 root には他に exact-24 の 10 本と exact-63 (現行) の 1 本
(`dev-wave-paper-story-a6-cert-20260902/a6-20260909b/jobs/rr95/...`) があり、
これらは現状で読める。**scope はこの 3 本だけ**である。

## 2. 3 本の grammar は完全に同一

`authority.contract_loader_blob_sha256s` の key 列 (wire 上の順序 = sorted) を改行区切りで
sha256 したところ、3 本とも
`ea217fefb2565a3f7d8f811bed864aedab0b5a461a4947ac0d1abaad9cb6ff59` で一致した。
key 数は 62。

同じ正規化で、`2a9ba783f^` 時点の `CONTRACT_LOADER_RELATIVE_PATHS` (62 path) を sorted した列も
`ea217fefb2565a3f7d8f811bed864aedab0b5a461a4947ac0d1abaad9cb6ff59` である。
すなわち **3 本の記録 grammar は T-733 が導入した 62 path 閉包そのもの**である。

## 3. 62 path の宣言順 (親の実測値。子は `git show 2a9ba783f^:orchestrator/campaign/campaign_lock.py` で必ず自分で取り直し、この写しと突き合わせること)

```
orchestrator/campaign/env_contract.py
orchestrator/campaign/env_contract_activation.py
orchestrator/campaign/execution_guard.py
orchestrator/campaign/loop.py
orchestrator/campaign/pipeline.py
orchestrator/campaign/wal.py
orchestrator/campaign/ident.py
orchestrator/campaign/artifact_admission.py
orchestrator/verifier/core.py
orchestrator/verifier/dsg.py
orchestrator/verifier/model.py
orchestrator/verifier/parse.py
orchestrator/verifier/__init__.py
orchestrator/verifier/report.py
orchestrator/campaign/s8c_preregistration.py
orchestrator/campaign/s8c_preregistration_evidence.py
orchestrator/campaign/s8c_generation_projection.py
orchestrator/campaign/campaign_lock.py
orchestrator/campaign/contract_loader_binding.py
orchestrator/campaign/guided.py
orchestrator/campaign/replay.py
orchestrator/qualification/artifacts.py
orchestrator/qualification/t126_driver.py
orchestrator/verifier/commit_receipt.py
orchestrator/calibrator/__init__.py
orchestrator/calibrator/effective_clock_policy.py
orchestrator/calibrator/perf_preflight.py
orchestrator/calibrator/runner.py
orchestrator/calibrator/schema_v2.py
orchestrator/calibrator/stability.py
orchestrator/campaign/__init__.py
orchestrator/campaign/axis_trigger_gating.py
orchestrator/campaign/build_admission.py
orchestrator/campaign/buildcache.py
orchestrator/campaign/calibration_verify.py
orchestrator/campaign/campaign_claim.py
orchestrator/campaign/diff_quarantine.py
orchestrator/campaign/env_attestation.py
orchestrator/campaign/genome.py
orchestrator/campaign/layout.py
orchestrator/campaign/lock.py
orchestrator/campaign/model.py
orchestrator/campaign/p2_2.py
orchestrator/campaign/p3_b4_launcher.py
orchestrator/campaign/p3_b4_protocol.py
orchestrator/campaign/reflux_ir.py
orchestrator/campaign/reservation.py
orchestrator/campaign/search_baselines.py
orchestrator/campaign/site_policy.py
orchestrator/campaign/source_digest.py
orchestrator/campaign/trigger_gate_binding.py
orchestrator/critic/__init__.py
orchestrator/critic/online_digest.py
orchestrator/holdout_observation.py
orchestrator/qualification/__init__.py
orchestrator/qualification/attempt_ledger.py
orchestrator/qualification/collector.py
orchestrator/qualification/contract.py
orchestrator/qualification/identity.py
orchestrator/qualification/qsub_binding.py
orchestrator/qualification/retry_index.py
orchestrator/qualification/series.py
```

現行 63 path との差は `orchestrator/campaign/verify_fanout_worker.py` 1 件だけで、
現行では tuple 末尾に置かれている (`54813f6e7` が index 5 から末尾へ移した)。
先頭 24 path は `PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS` と一致する。

## 4. 関連 commit

- `a94ba713b` [T-733] enforcement source closure を exact 62 path へ広げる
- `da44dc7b1` [T-733] 歴史閲覧に限って pre-T733 exact-24 grammar を読めるようにする
- `2a9ba783f` [T-2429] verify_fanout_worker.py を足して 63 にする (index 5)
- `54813f6e7` [T-2429] fix 2: worker を末尾へ移す

## 5. 現状の失敗の仕方 (子が再現してよい)

- `decode_campaign_lock` は `_validate_authority` の
  `tuple(sorted(blob_sha256s)) != tuple(sorted(CONTRACT_LOADER_RELATIVE_PATHS))` で拒否する。
- `decode_historical_campaign_lock` は、現行 wire 順序と一致しないので pre-T733 枝へ落ち、
  `_validate_pre_t733_historical_authority` の
  `tuple(blob_sha256s) != tuple(sorted(PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS))` で拒否する。
- よって 3 本はどちらの decoder からも読めない。

## 6. [T-2125] が本件を塞がないことの実測

3 本の `identity_preimage` → `search_config.build_admission` を key 昇順・区切り無しの JSON へ
正規化した sha256 は 3 本とも `949ddcc2951935405f661ce70cb7df1031fedfd162788655e78faaadac671a44`。
現行 `artifact_admission._current_policy().as_preimage()` を同じ正規化で hash した値と**一致**する。
したがって `require_admitted_campaign` の
`search["build_admission"] != policy.as_preimage()` は 3 本に対して現に発火しない。

## 7. 並行編集が無いことの実測

- `git diff --name-only main...<branch>` を main 以外の 114 branch すべてに対して
  `orchestrator/campaign/campaign_lock.py` と `orchestrator/campaign/artifact_admission.py` に
  限定して実行した結果、差分を持つ branch は 0 件。
- `.codex/worktrees/` 89 本と `.claude/worktrees/` 27 本の作業ツリーにある同 2 file の md5 は
  全て main の値 (`4d55bbbb074908bdd2b08c3f6595c751` / `cc52fcdae1dfe8cf54ab0d6e5db6816b`) と一致。
  未 commit の並行編集は無い。
