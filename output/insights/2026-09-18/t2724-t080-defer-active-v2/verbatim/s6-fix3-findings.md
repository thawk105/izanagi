# 段 6 fix-3 の指示 (親、2026-09-18 13:20 JST)

fix-2 統合 commit `7c007333b` の焦点走 (chain 有り scratch、7 file、request 5621 系の次走): **1088 passed / 2 failed / 2 errors / 7 skipped、388 秒**。**接続正例 `test_t080_active_v2_delegation_accepts_full_receipt` を含む接続系 6 node が緑になった** (fixture は C → G → A → X → load → launch → receipt まで到達)。残りは次の 2 点。chain 無し木 (`focus-nochain-4`) の結果は親が追記する。

chain 無し木 `focus-nochain-4` (7 file、request 5648、13:02→13:17): **1093 passed / 3 failed / 11 skipped、544 秒**。3 failed (`…rechecks_receipt[changed|missing]` と `…rejects_late_hit_file`) はいずれも H1 の rglob assertion。接続正例ほか 6 node は緑、lock deadline は今回は出なかった (発火は時機依存 = H2 の構造問題は残る)。

## H1. `test_t080_delegated_campaign_start_rechecks_receipt[changed|missing]` と `test_t080_delegated_campaign_start_rejects_late_hit_file` の assertion の射程 (test 側)

```
assert not list((tmp_path / "output").rglob("wal.jsonl"))
AssertionError: assert not [PosixPath('.../output/campaigns/p3-s8a-trigger-s.../wal.jsonl'), PosixPath('.../output/campaigns/s1-direct-block2-direct-comparison-9645b16a/runs/wal.jsonl'), ...]
```

`tmp_path / "output"` は接続 fixture が実 root から複製した tracked output (過去 campaign の WAL を含む) なので、「WAL を書かない」の証拠にならない。**run_block に渡した `output_root` (この block の campaign layout) と marker root・budget path に限定**して「WAL / marker / budget を書かない」を検査する (既存 `test_run_block_rejects_receipt_epoch_drift_before_campaign_start_g4` の side effect 検査と同型)。期待する refusal (epoch) と evaluate 不到達は不変。

## H2. 接続 fixture の実 root 読取りと real-repo lock (test 側、F945 型の再発防止)

同走で xdist worker が `RuntimeError: real-repo lock deadline exceeded; fails-closed: resource=ccbench mode=read` (conftest `_REAL_REPO_LOCK_TIMEOUT_S = 245`) で INTERNALERROR になり、`test_cli_subprocess_returns_rc_2_on_gate_refused` が crashitem になった (2 errors)。原因 (親の判定、現物で確かめよ): 新接続 9 node (+ seam 1) を fix-1 で `_REAL_REPO_BOTH_READER_NODES` (P 読 + S 読) に登録したため、各 node が **test 全体 (~150〜210 秒) の間 real-repo の read lock を保持**し、ccbench writer (`test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2` 等) が gate を握って待つ間に他の reader が 245 秒の deadline を超えた。既存の stub-free T-080 e2e 10 node は `_t080_stub_free_e2e_repo` → `_T080SharedBases.get(key)` で **session に 1 回だけ base を組み、各 test はその copy を使う**ため登録簿に無く、この問題を起こさない。

直し方:
1. `_build_t080_active_v2_repo` は `_build_t080_stub_free_e2e_repo(active_v2_base=True)` を直接呼ばず、`_t080_stub_free_e2e_repo` と同じ shared-base 経路 (`_T080SharedBases.get(key)`、key を `(r_trailer, extra_r_path, issue_receipt, distinct_basis_blob, active_v2_base)` の 5 要素へ拡張、`get` の builder 呼出しに `active_v2_base=key[4]` を渡す。既存 4 要素 key の呼出しは `active_v2_base=False` を補って digest を変えない形にするか、既存 key の digest が変わることを許容するか — 既存 test の挙動が変わらない方を選ぶ) で base を 1 回組み、各 test は copy に emitter の C → G → A → X を積む。R trailer 不正の負例 (`test_t080_active_v2_preserves_nonlayer2_receipt_refusal`) は `r_trailer` が key に入るので別 base になる。
2. その結果、各 test の実 root 読取りは「base を最初に組む 1 回」だけになり既存 stub-free e2e と同じ扱いになるので、fix-1 で足した登録 (`_REAL_REPO_NODE_INVENTORY` / `_REAL_REPO_BOTH_READER_NODES` の接続 9 node と draft 負例、serialization golden の対応行) を**既存 stub-free e2e と同じ状態 (未登録) に戻す**。`test_run_block_refuses_invalid_receipt_after_gate_seam` は実 root を読むか (`root=ROOT` を渡すか) を現物で確かめ、読むなら登録を残す。
3. `_T080SharedBases` の consumer pin (`test_s8b_oracle_driver.py:1284` 付近、6 関数 / 11 node と `test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary`) と `test_real_repo_serialization.py::test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default` が新 consumer で赤にならないよう、純増を明示追随 (期待値の緩和ではなく exact pin の追随)。

## H3. 変えないもの

production (driver / migration / ratified_freeze)、S、既存 tracked test の期待値、走査除外・hold・allowlist。sink pin は行番号が動かない限り不変。

## 対応表

H1〜H3 と、前巡までの partial 項目のうち状態が変わるものを closed / partial / regressed で書く。fixture 構築時間 (base 1 回 + copy) の見積りも書く。
