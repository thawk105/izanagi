# 段 1 実測 (親、2026-09-20 20:55〜21:08 JST、着手 commit f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad = local main)

測定道具は T-2344 一次資料の probe 原本 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability/probe_closure_v2.py`、
`probe_producer_universe.py`、`probe_lock_grammars.py`) を書き直さずに実行した。出力 JSON は本 job dir。

## 1. 閉包の寸法 (`closure-head.json`、`producer-universe.json`)

| 集合 | 2026-09-09 (2143a49c0) | 2026-09-16 (a1b40608c、T-2482) | **2026-09-20 (f94b61fc8)** |
|---|---:|---:|---:|
| 収載 tuple `CONTRACT_LOADER_RELATIVE_PATHS` | 63 | 63 | **63** |
| tuple 起点の静的 import 発見集合 | 140 | 162 | **163** |
| 未収載 (tuple 起点) | 77 | 99 | **100** |
| 現行 63 起点の 1 段目 (直接 import 先 + package 初期化) | 81 (未収載 18) | 未測 | **85 (未収載 22)** |
| 発行器 6 本起点の発見集合 | 160 | 未測 | **168** |
| 両者の和 | 165 (未収載 102) | 未測 | **173 (未収載 110)** |
| 発行器起点にだけ居る module | 25 | 未測 | **10** |
| 2 段目まで広げたときの追加数 | — | — | 23 (参考) |

引数の「候補 165、未収載 102」は 2026-09-09 の値であり、着手時点では 173 / 110 である。
unresolved import 参照は 0 件。

## 2. 1 段目の未収載 22 本と import 元 (`layer1-edges.json`)

- `orchestrator/calibrator/analyze.py` ← `calibrator/stability.py`, `campaign/pipeline.py`
- `orchestrator/calibrator/benchparse.py` ← `calibrator/runner.py`
- `orchestrator/calibrator/model.py` ← `calibrator/runner.py`, `calibrator/stability.py`
- `orchestrator/calibrator/perfparse.py` ← `calibrator/runner.py`
- `orchestrator/calibrator/tsc.py` ← `campaign/env_attestation.py`
- `orchestrator/campaign/agent_outputs.py` ← `campaign/layout.py`
- `orchestrator/campaign/backoff_hole_grammar.py` ← `campaign/loop.py`, `campaign/wal.py`
- `orchestrator/campaign/durable_root.py` ← `campaign/layout.py`
- `orchestrator/campaign/materializer_admission.py` ← `campaign/build_admission.py`
- `orchestrator/campaign/p3_b4_admission_record.py` ← `campaign/p3_b4_launcher.py`
- `orchestrator/campaign/p3_b4_closed_critic.py` ← `campaign/p3_b4_launcher.py`
- `orchestrator/campaign/p3_s4_loop.py` ← `campaign/p3_b4_launcher.py`
- `orchestrator/campaign/p3_s4_loop_sort.py` ← `campaign/p3_b4_launcher.py`
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py` ← `campaign/p3_b4_launcher.py`
- `orchestrator/campaign/paper_story_a1_source.py` ← `campaign/pipeline.py`
- `orchestrator/campaign/pin.py` ← `campaign/axis_trigger_gating.py`, `campaign/build_admission.py`
- `orchestrator/campaign/reflux_result_evidence.py` ← `campaign/loop.py`
- `orchestrator/campaign/s8b_compiler_input.py` ← `campaign/buildcache.py`
- `orchestrator/campaign/s8b_expected_materialization.py` ← `campaign/buildcache.py`
- `orchestrator/campaign/silo_ladder_rung1.py` ← `qualification/identity.py`
- `orchestrator/campaign/sort_swo_dependency_material.py` ← `campaign/buildcache.py`
- `orchestrator/critic/digest.py` ← `campaign/search_baselines.py`, `critic/__init__.py`, `critic/online_digest.py`

一次資料が 2026-09-09 に挙げた「1 段目の drift 2 本」(`calibrator/analyze.py`、`campaign/backoff_hole_grammar.py`) と、
認証受理 API で関数本体まで実行された未収載 4 本のうち 2 本 (`materializer_admission.py`、`backoff_hole_grammar.py`) は、この 22 本に含まれる。

## 3. 記録済み campaign.lock の grammar 分布 (`lock-grammars.json`、root 19 個、lock 92 本)

| key 数 | 本数 |
|---|---:|
| authority 無し (E0) | 32 |
| 24 (pre-T733) | 29 |
| 62 (T-733) | 6 |
| **63 (現行、T-2429 以降)** | **20** |
| 12 / 8 (旧 exploration、収載外) | 4 / 1 |

**exact-63 の 20 本の所在:** B-10 formal `b10-backoff-grid-t2500-formal` 6 本 (09-15、09-19 の 2 走 × 3 workload)、
`b10-backoff-grid-t2266-formal` 3 本、`b10-backoff-grid-t2418-explore` 3 本、paper-story A-2 `t2489-20260918a` rr5/rr50 の 2 本、
A-6 `a6-20260909b` rr95 1 本、B-7 fixed5 `b7f5-20260919a` rr5/rr50/rr95 の 3 本、`izanagi-job-evidence/t2228/attempt-20260917b-official` 1 本、
`t1998-balanced-stock-inline-runs` 1 本。D1653 の「収載する grammar は実在 corpus が確認できたものだけ」は exact-63 について成立する。
走査 root に K2 手動 loop (p3-s4-loop) の durable root は含んでいない (job root 側にあり列挙していない)。exact-63 の実在は上記だけで十分。

## 4. pin 閉包 (`pin_closure.log`、DW-O09)

変更候補 3 file (`campaign_lock.py` / `artifact_admission.py` / `contract_loader_binding.py`) の path と変更前 sha256 で走査した。

- **test の独立 literal (同 commit で追随が必要):**
  `orchestrator/tests/test_t671_source_binding.py:104` `_EXPECTED_ENFORCEMENT_SOURCE_PATHS` (+ `:264-272` の件数 24/39/63)、
  `orchestrator/tests/test_artifact_admission.py:283` `_EXPECTED_E1_CLOSURE_PATHS`、`:349` `_FIXED_SYNTHETIC_E1_EPOCH`、
  `:352` `_FIXED_ORDERED_CLOSURE_PATHS_SHA256`、`:1447` scope 文言、`:1574/1581` の 63、
  `orchestrator/tests/test_layer3_report.py:1933` 歴史 epoch 表 (62/24) と `:1993` `grammar == 63` param、
  `orchestrator/tests/test_s1_9pair_figure_provenance.py:74-90` `CURRENT_E0_EPOCH` (live scope 文言と一致を要求、`FROZEN_E0_EPOCH` は凍結のまま)、
  `orchestrator/tests/test_campaign_lock_codec.py:19` exact-62 literal (不変) と `:112` 以降の合成。
- **docstring の「63」:** `contract_loader_binding.py:2,58,61`、`campaign_lock.py:47`。
- **記録としての sha256 pin (変えない・変わらない):** A-1 receipts (`output/insights/2026-09-18/t1505-.../receipts/*.json`、`2026-09-20/t2792-.../receipts/*.json`) の
  `working_sha256` = 変更前 `campaign_lock.py` (A-1 非認証 source closure が同 file を数える。記録は当時の事実、規律 7)。
  K2 round2/3 `layer3_report.json` の `artifact_admission.py` sha (記録)。T-2344 insight の trace JSON (記録)。
- **B-4 projection hash / admission receipt validator:** `artifact_admission.py` の全 bytes sha256 が入る (D2081 が既に限界として記す)。
  `test_s1_9pair_figure_provenance.py:661` は live 同士の比較で、凍結側 `FROZEN_E0_EPOCH` は不変。
- **FROZEN_MANIFEST / generator source pin:** 3 file の path を pin する凍結 manifest は 0 件 (path 検索)。
- **tests/fixtures の lock:** `b10_backoff_shape_locks/*.campaign.lock` は 24-key (pre-T733)。不変。
- **他 worktree との編集面重複 (`overlap_scan.log`):** `dev-wave-t1851-c3c-official-floor` の 6 file が bytes 相違 — branch tip `0709a4018` (09-15) は HEAD の祖先、
  process 0 件 (着地済みの古い木)。`.codex/worktrees/t2724-g1-gen` の `test_layer3_report.py` も同型。稼働中 wave との重複なし。

## 5. 受理集合への影響の実測根拠

- certified decoder `_validate_authority` は `set(keys) == set(CONTRACT_LOADER_RELATIVE_PATHS)` を要求する (`campaign_lock.py:402-404`)。tuple を N へ動かすと
  exact-63 lock は certified 経路で decode 段拒否になる。`_require_verifier_epoch_for_purpose` (`artifact_admission.py:1157-1176`) は E1 の blob 差 (epoch 差) を拒否しない
  (D1163、current closure の可用性だけ) ので、**閉包の bytes が変わる commit は既存 campaign の certified 受理を変えないが、tuple の変更は変える**。
- CERTIFIED_ACCEPTANCE で記録済み campaign を読む production consumer: `b10_backoff_static_tail_formal.py:393` (`load_formal_campaign`)、
  `paper_story_a2_certification.py:3300` (`decode_campaign_lock_bytes`)、`t1998_stock_inline_pair.py:981`、`backoff_*` 系、`p3_s4_loop*.py`、`s8b_oracle_report.py:562` ほか
  (grep 30 件)。A-2 系の collect は記録 commit の submit-tree の module で呼ぶ運用 (memory: receipt が policy 絶対 path を束縛) で、tuple 前進後の checkout から
  exact-63 campaign を certified で読み直す経路は「記録 commit の checkout で読む」か「HISTORICAL_RAW で読む」の 2 つになる。exact-62 のとき (T-2429) と同じ帰結で、D1653 / D1770 が裁定済み。
- 受入検査の増分: exact-62 の per-path 負例 (`test_t733_exact62_rejects_each_recorded_commit_blob_mismatch`) は 62 件 × 約 0.05 s (ledger)。exact-63 で同型を作ると 63 件 × 0.05 s ≈ 3 s。
  収載 tuple 全 path を fixture repo へ複製する test (`test_t1998_stock_inline_pair.py:164,507`、`campaign_lock_test_support.py:17`) は path 数に線形。
