# 段 1 実測 — [T-2344] 発行器先行の次段 (着手 commit 5efd69367)

実測は親が repo 外 (job dir) の script で行った。閉包の数え方は T-2344 一次資料の probe 原本
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability/probe_closure_v2.py` の `Tree` / `expand` /
`imports_of` / `package_inits`、`ast.walk` + package 初期化、D1650 と同規則) を書き直さずに import して使った
(`measure_head.py` → `closure-head.json`)。

## 1. 閉包寸法 (着手 commit `5efd69367b641b9bfbd6fb426478f66ae5762783`、HEAD == local main)

| 集合 | 09-20 (f94b61fc8、前 wave) | **09-21 (5efd69367)** |
|---|---:|---:|
| 収載 tuple `CONTRACT_LOADER_RELATIVE_PATHS` | 63 → 85 | **85** |
| tuple 起点の発見集合 | 163 | **163** |
| tuple 起点の未収載 | 78 (85 seed) | **78** |
| tuple 起点の 2 段目 (現行 85 起点の 1 段目の未収載) | 23 (参考) | **23** |
| 発行器 6 本起点の発見集合 | 168 | **168** |
| 和 | 173 | **173** (未収載 88) |
| 発行器起点にだけ居る module | 10 | **10** (顔ぶれも同一) |
| unresolved import 参照 | 0 | **0** |

**発行器 6 本の現状:** `s8b_oracle_report` / `b10_backoff_shape_sweep` / `backoff_extended_sweep` / `backoff_extended_sweep_report` /
`backoff_overthrottle` の 5 本は tuple 起点の発見集合の外 (= 発行器起点にだけ居る 10 本に含まれる)。
`autonomous_trial_completeness` は tuple 起点の発見集合に既に居る (未収載、import 元 = `p3_autonomous_workload_trial.py` /
`s8c_acceptance_receipt.py` / `trial_registry.py`)。6 本とも収載されていない。

**収載対象 = 発行器 6 本 ∪ 発行器起点にだけ居る 10 本 = 11 本** (10 本のうち 5 本は発行器自身なので重複 5、「6 + 10 = 16」ではない):

| path | import 元 (発見集合内) |
|---|---|
| `orchestrator/campaign/autonomous_trial_completeness.py` | `p3_autonomous_workload_trial.py`、`s8c_acceptance_receipt.py`、`trial_registry.py` (発行器) |
| `orchestrator/campaign/b10_backoff_shape_sweep.py` | (seed、発行器) |
| `orchestrator/campaign/backoff_extended_sweep.py` | `backoff_extended_sweep_report.py`、`backoff_overthrottle.py` (発行器) |
| `orchestrator/campaign/backoff_extended_sweep_report.py` | (seed、発行器) |
| `orchestrator/campaign/backoff_overthrottle.py` | `backoff_extended_sweep_report.py` (発行器) |
| `orchestrator/campaign/s8b_abort_reason_contract.py` | `s8b_oracle_report.py` |
| `orchestrator/campaign/s8b_oracle_report.py` | (seed、発行器) |
| `orchestrator/campaign/s8b_outcome_stage_contract.py` | `s8b_oracle_report.py` |
| `orchestrator/reports/__init__.py` | `backoff_extended_sweep_report.py` ほか (package 初期化) |
| `orchestrator/reports/calibration_report.py` | `reports/__init__.py` |
| `orchestrator/reports/plot.py` | `backoff_extended_sweep_report.py`、`reports/__init__.py`、`calibration_report.py` |

`reports/` の 3 本は標準 library だけを import する (matplotlib 等の重い依存なし、`plot.py` は gnuplot を subprocess で呼ぶ)。

**2 段目 23 本との重なり 0** (23 本は 1 本も含めない、依頼どおり)。

**提案 tuple (既存 85 の宣言順を保ち 11 本を path の sorted 順で末尾へ) = exact 96**。96 本を seed にした発見集合は
**173 module = 和集合と同一集合** (`proposed_rooted_equals_union: true`)、未収載 **77** (= 88 − 11)。

## 2. 記録済み campaign.lock の grammar (exact-85 の実在 corpus)

`scan_recent_locks.py` → `recent-locks.json` (08:31〜08:45 JST)。走査範囲 = `/work/1/SFC/tanab` と `/home/SFC/tanab` の全域
(`.git` / `external` / `__pycache__` / `node_modules` / `.cache` の dir は除外、628,967 dir)。対象 = exact-85 化 commit `65e94a3a7`
(2026-09-20 21:55 JST、main への land は 09-21 00:15〜00:21 JST の前進 merge `c383bac07` / fold `285477c00`) 以降に mtime を持つ `campaign.lock`。

| 区分 | 本数 | 所在 |
|---|---:|---|
| 全体 (mtime ≥ 09-20 21:55) | 821 | mtime 09-20 22:02 〜 09-21 08:41 |
| authority 無し (schema_version 無し = v1 形) | 768 | worktree 内 (`.claude/worktrees` 608、`.codex/worktrees` 96) と dev-wave job dir 2 個 (各 32) |
| 63-key v2 | 53 | すべて `dev-wave-jobs/dev-wave-t2797-b5-contrast` (B-5 試走)、記録 commit はすべて `11d46a74a` (exact-85 化より前) |
| **85-key v2 (exact-85 の実在 corpus)** | **0** | — |

**exact-85 grammar の実在 corpus は着手時点で 0 本。** D1653 の収載条件 (実在 corpus の確認) は着手時点では満たされない。
exact-85 は 09-21 00:21 JST ごろから main の現行 grammar であり、以後 main から起動した certified campaign はすべてこの grammar を記録する
(着手までの約 8.5 時間では 0 本)。並走 wave (K2 4 巡目の前提となる T-2795、B-8 の T-2807 など) が本 wave の land までに campaign を起動すれば
exact-85 lock が生まれうる。

**到達可能性 (DW-O13、`probe_exact85_reachable.py` → `exact85-reachable.json`):** clean な wave 木 (HEAD 5efd69367、tracked dirty 0) で production の
`contract_loader_binding.capture_contract_loader_binding()` を 1 回呼ぶと、binding commit = HEAD、key 85 本が現行宣言順で返る (lock への encode 時に
canonical JSON で sorted wire 順になる)。campaign・lock は作っていない。exact-85 は実在 0 本だが、現行 production が生成する grammar である。

前 wave の exact-63 corpus 20 本 (走査 19 root) に加え、B-5 試走の exact-63 lock 53 本が新たに存在する (歴史 grammar exact-63 で読める、D2194 項 4 (2) の (c) の対象と同型、本 wave は触れない)。

## 3. pin 閉包 (DW-O09、`pin_closure.log`)

- 変更候補 3 file の変更前 sha256 (campaign_lock.py `737ddfc2…`、artifact_admission.py `7ec05378…`、contract_loader_binding.py `4686a8ab…`) は
  tracked 0 件・`output/` (untracked 含む) 0 件。前 wave の hash (A-1 receipts・K2 layer3 report が持つ) は旧版のもので、本 wave では変わらない (記録済み、規律 7)。
- 新規収載 11 本は bytes を変えない。path を pin する既存物: `s8b_oracle_manifest.py` (report / outcome_stage_contract の source を凍結 manifest で束縛)、
  `s8c_preregistration_evidence_contract.v1.json` (autonomous_trial_completeness の path)、`test_official_perf_closure.py` (perf 権限の review 台帳、本件と無関係)、
  `test_ccbench_spawn_sites.py` (起動点目録)。いずれも bytes 不変なので影響なし。
- identifier `CONTRACT_LOADER_RELATIVE_PATHS` / scope 定数を参照する file: production 4 (`artifact_admission` / `campaign_lock` / `contract_loader_binding` /
  `b10_backoff_shape_sweep` (`PRE_T733_…` だけ) / `s8b_oracle_report` (現行 scope 2 定数を `unavailable` 分岐の出力へ写す))、test 14。
- 数値 85 の派生 literal: `test_artifact_admission.py` (fixture docstring・scope 文言・`== 85` 2 か所)、`test_s1_9pair_figure_provenance.py` (`CURRENT_E0_EPOCH` の scope 文言)、
  `test_t671_source_binding.py` (`== 85`、git timeout `850` = 10 秒 × 85 が 5 か所)。
- `s8b_oracle_report` の `unavailable` 分岐は現行 scope 文言を report に写す (`s8b_oracle_report.py:595-601`)。新しく作る report の文言だけが変わり、
  記録済み report の bytes は変わらない (DW-O10: 凍結 producer の出力を再生成しないので不成立)。

## 4. 編集面の重複 (`overlap_scan.log`、08:35)

他 worktree の作業ツリーで本 wave の編集候補 20 file と bytes が違うものは 56 件、すべて mtime 09-15〜09-19 (古い基点の木)。
08:25 時点の並走 8 wave の編集は 0 件。受入直前に main の前進を再確認する。

---

## 訂正 (段 6 レビュー A-2 / B-2 / B-3 を受けて、2026-09-21 09:3x JST)

§2 の「**exact-85 grammar の実在 corpus は着手時点で 0 本**」および「着手までの約 8.5 時間では 0 本」は、走査結果を越えた断定である。
正しくは次のとおり (元の記述は消さず、この注記で訂正する)。

- 言えること: **指定した走査条件** (2 root、`.git` / `external` / `__pycache__` / `node_modules` / `.cache` を除外、
  mtime ≥ 2026-09-20 21:55、走査は 08:31〜08:45 の区間で全域の同一時点 snapshot ではない) で **85-key v2 の campaign.lock は未検出**。
- 言えないこと: 走査範囲外・除外 dir 配下・mtime を古い値で保存した複製の不在。件数分類 (85-key) は exact grammar の照合とは別で、
  **exact 照合済みの exact-85 corpus は「確認できていない」** (0 本であることの証明ではない)。
- 63-key 53 本についても、mtime は**発行時刻ではない**。記録 commit (`11d46a74a`) は pre-85 で、25 本は mtime が main の land (00:21) より後だが、
  これは同一の固定木による反復であり、exact-85 について同じ発生を保証するものではない。
- 将来 85-key の記録を得た場合は、wire key 列と記録 commit の宣言順を exact 照合してから「corpus」と呼ぶ (前 wave が exact-63 で行った手順)。
