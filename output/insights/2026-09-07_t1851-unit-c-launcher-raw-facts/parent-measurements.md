# [T-1851] 単位 C1a (起動層の raw facts 面) — 親の実測

すべて親が実走した。login node は `pegasus` の login node、計算ノードは `tools/run_tests.py` の自動 dispatch
(`| ` 前置の行は計算ノード側の出力)。時刻は JST。codex 子はいずれも sandbox で pytest を走らせられなかった
(Pegasus の `qstat -Q` preflight 失敗 → runner rc=16、`child_started=false`)。子の未実走を緑と数えていない。

## 起動と main 取り込み (checkout: `9f64a3d44` → `04f06d032`)

| 検査 | 結果 |
|---|---|
| `check_wave_startup.py --mode resume --external-handoff` (取り込み前) | rc=1 (`HEAD does not contain local main (9 commit behind)`、想定どおり) |
| 両親が共に変更した file (merge-base `8c07ded74`) | 0 件 |
| `external/ccbench` gitlink | 両親とも `511c9538e` |
| provenance `--message-file` 事前検査 | rc=0 |
| merge commit | `04f06d032` (integrator、local main `97ee3cd3a`) |
| `check_wave_startup.py --mode resume --external-handoff` (取り込み後) | rc=0 |
| `check_docs.py` | rc=0 |
| 全史 provenance (`check_ai_provenance.py`、計算ノード) | rc=0、**8,271 件、新規違反なし** |

## focus 走 (DW-O26、2-hop consumer 集合 38 file = 編集面 4 module の consumer 37 file + `test_plain_runner_coverage`)

| 走 | checkout | 結果 |
|---|---|---|
| baseline (実装前) | `04f06d032` | **4,717 passed / 16 skipped / rc=0**、計算ノード 978178.nqsv、199 s |
| focus 1 (段 5 統合後、未 commit) | `04f06d032` + s5 | **1 failed / 4,733 passed / 16 skipped**、201.8 s。赤 = `test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact` (`unreviewed: orchestrator/campaign/s8b_floor_attempt_launcher.py`)。launcher が `use_perf_from_receipt` を呼ぶようになったための在庫検査の設計どおりの発火 |
| focus 2 (fix1 統合後、未 commit) | `04f06d032` + s5 + fix1 | **infra 赤**: Pegasus dispatch が `queue-wait-timeout` で child 未起動 (`child_started=false`、rc=16)。test は 1 件も走っておらず、差分に帰属しない。fix2 統合後の focus 3 で代替した |
| focus 3 (fix2 統合後、未 commit) | `04f06d032` + s5 + fix1 + fix2 | **4,736 passed / 16 skipped / rc=0**、156.6 s |
| focus 4 (fix3 統合後、未 commit) | `04f06d032` + s5 + fix1 + fix2 + fix3 | **4,736 passed / 16 skipped / rc=0**、150.1 s |

変更した test file の単独走 (login node、自走 harness): `test_s8b_floor_attempt_launcher.py` **31 passed** (42.4 s)、
`test_official_perf_closure.py` **7 passed / 0 failed**。

実装 commit `35ba02e1a` は focus 4 と同じ bytes (3 file、+827 / −78。launcher +245 / −37、launcher test +567 / −41、
perf closure test +15)。commit 後の全史 provenance は rc=0、**8,272 件、新規違反なし** (既知違反 55 件のみ)。

## 変異 matrix (checkout: `35ba02e1a`、harness `tools/mutation_harness.py`、dispatch、runner = `test_s8b_floor_attempt_launcher.py` + `test_ccbench_spawn_sites.py` `-q -rf`)

- 段 4 で M1〜M12 を事前登録した。fix2 の後に M4 を「public `launch_floor_attempt` の `classification_authority=_CLASSIFICATION_AUTHORITY,`
  を caller-selected authority へ差し替える変異」へ再照準した (元の登録は定数側の digest 変異で、signature 検査だけでは殺せない形だった)。
  `mutation-spec-probe.json` が再照準前、`mutation-spec-probe-2.json` (sha256 `a867c987…`) が再照準後で、本走はこれを KILLED 期待へ書き換えた
  `mutation-spec-final.json` (sha256 `e2eefcae…`) を使う。fix3 の後、12 変異の anchor (old 逐語) は全件 count=1 で一意であることを再確認した。
- probe (全件 SURVIVED 登録、観測 node 収集目的): baseline PASSED (53.7 s)、**12 件すべて MISMATCH** (= 赤)。観測 node は 11 件が 1 node、
  M7 だけが 2 node (`test_pre_probe_competition_classifies_as_competing` と `test_pre_probe_competition_terminalizes_without_capture`)。
  計 13 node。各集合は段 4 で事前登録した観測 node を含む。
- 本走 (`mutation-spec-final.json`、KILLED 期待 = 観測完全集合、DW-M08): baseline PASSED (53.5 s)、
  **12/12 KILLED、`matching=12`**、harness rc=0、`repo_head=35ba02e1a`。各変異 52.7〜57.8 s (dispatch 込み)。
  `mutation-final-out.json` が台帳。probe と本走で観測 node の集合は一致した。

## 受入全走 (tested tip = 記録 commit `6194d4840`)

- **attempt 1 (06:54〜07:58 JST、64 分)**: 子は緑 — `raw_child_rc=0` / `normalized_child_rc=0` /
  `reason=child-verdict`、**21,039 passed / 68 skipped** (collected 21,107)。post-claim merge は
  `6f2a89818` (local main `425060bab`)。しかし receipt は発行されなかった:
  `stage=acceptance-receipt rc=70 reason=receipt-lease-check`、`state=held`。
  claim 時の main は `425060bab`、receipt 時の main は `9f093b61` で、走行が **lease の TTL 2,400 秒**
  (`_LEASE_TTL_SECONDS`) を超えたため lease が別 session (holder `3109466d80fe`、07:46) へ移っていた。
  テストの赤ではない。login 側の collection に約 3 分、shard 3 本の実行に約 60 分かかっている
  (`gen_S` は QUE 0 / RUN 49 で queue 待ちではなく、実行の並びによる)。
- **attempt 2 (08:01〜09:0x JST)**: 別 session が lease を保持している状態で投入した。DW-O27 (D662) の
  とおり `held` でも待たず wave digest の疑似 holder で走り、この経路は receipt 発行時の lease 再確認を
  行わない。結果は **rc=0、`verdict: child-green`、21,043 passed / 68 skipped** (collected 21,111)。
  receipt は `dev-wave-acceptance-receipt/v5`、`tested_main=9f093b612`、`tested_tip=061ecb1b1`、
  `red_nodeids` / `flake_nodeids` は空、pre / post fingerprint は一致 (`diff_bytes=0`、`status_bytes=0`)、
  `lease was not acquired` (fencing token は無い、既知の限界)。post-claim merge は `061ecb1b1`
  (local main `9f093b612`)。attempt 1 の tip との差は main 側 3 commit の取り込みだけで、実装面の
  差分は同じ bytes である。
