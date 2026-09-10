## 実装したもの

- [backoff_sweep.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:88): 必須 keyword `backoff_fixed_physical_us: Mapping[int, int]` を追加。
- [backoff_sweep.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:108): 非負要求集合との key 完全一致、exact `int`、非負値を source capture 前に検査。
- [backoff_sweep.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:143): driver intent を float64 bits 化し、2 文脈へ複製。
- [backoff_sweep.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:178): 非負値へ pointwise 宣言を渡し、`-1` と他 macro の既存分岐を維持。
- 呼び出し面を [backoff_sweep.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:425)、[backoff_extended_sweep.py:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:527)、[backoff_profile.py:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_profile.py:344)、[backoff_repro.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_repro.py:64)、[backoff_requested_us.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_requested_us.py:110)、[backoff_overthrottle.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_overthrottle.py:61) で更新。overthrottle だけは指定どおり `_point_backoff_us` の decode 由来 intent。
- [test_backoff_sweep.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_backoff_sweep.py:145): raw 5、extended wrapper の raw 3000→1000、F718、写像契約の負例を追加・更新。M1〜M5 を静的に照準済み。

## 受理・拒否の変化

supply arm が green である場合の比較です。変更前は intent 写像自体がありませんでした。

| 生値 | intent | 変更前 | 変更後 |
|---:|---:|---|---|
| `-1` | entry なし | stock branch meaning green | 不変 |
| `5` | `5` | meaning unestablished、受理 | meaning green、受理 |
| `3000` | `1000` | meaning unestablished、受理 | meaning green、受理 |
| `1000` | `1000` | meaning unestablished、受理 | 観測 `0.0` と不一致で red、helper が拒否 |
| `1000` | `0` | meaning unestablished、受理 | 観測一致なら green、受理 |
| `12000` | `10000` | meaning unestablished、受理 | 観測一致なら green、受理 |
| 任意の非負値 | 観測と不一致 | meaning unestablished、受理 | meaning red、拒否 |
| 任意の非負値 | key 欠け・余り | 契約なし | capture/build 前に `RuntimeError` |
| 任意の非負値 | 負値・非 exact `int` | 契約なし | capture/build 前に `RuntimeError` |

生値 `1000..2999` や `12000` 以上を一律拒否する wire-domain 制約は追加していません。

## 実走した検査

PASS:

- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- 変更 7 file の AST parse、6 campaign module と test module の import
- 全 helper 呼び出し面の必須 keyword 静的検査
- 欠け・余り・bool・負 intent の事前拒否 runtime probe
- `git diff --check`

pytest は実装済み・未実走です。次の runner 実行はいずれも `qstat -Q` preflight 失敗、rc=16、`child_started=false` でした。

- `orchestrator/tests/test_backoff_sweep.py` 全体
- `test_backoff_extended_sweep.py` の codec、real wrapper、configure forwarding
- `test_backoff_profile_pegasus.py::test_real_profile_driver_gate_recomputes_preprocessed_file_digest`
- `test_backoff_requested_us.py::test_driver_gate_wrappers_bind_fixed_and_requested_us_macros`
- `test_backoff_overthrottle.py::test_condition_gate_uses_backoff_flags_from_imported_genomes`
- `test_backoff_consumers.py::test_backoff_repro_condition_gate_dominates_campaign_build_and_measurement`
- 指定された `test_condition_meaning_gate.py` の6 nodeid
- 制約 meta-test `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`

login node は最終観測で headroom `0` のため、直接実行へ切り替えていません。親の全走も代替していません。

## 波及の静的列挙

- repository 内の直接 caller は6 module・7呼び出しで、すべて更新済み。repository 外から private helper を呼ぶ場合は新 keyword が必要です。
- 共有 fixture は `condition_meaning_gate/supplied`、同 `stock`、`effectuation-ignored`。bytes と hash は変更していません。
- consumer test は `test_backoff_extended_sweep.py`、`test_backoff_profile_pegasus.py`、`test_backoff_requested_us.py`、`test_backoff_overthrottle.py`、`test_backoff_consumers.py`、`test_p2_2_site_aware.py`、`test_condition_meaning_gate.py`。
- `s1_known_axes_freeze` の live source hash consumer には `backoff_sweep.py` 変更が波及します。既存の hash 乖離を含め、freeze は再発行していません。
- T2418 の固定 `meaning_witness_status` は再走時には古い表現になり得ますが、裁定どおり scope 外で不変です。
- screening、B10 shape、extended report の codec API は変更していません。

## 申告と実物の対応

`git diff --name-only` は次の7 fileだけです。

- `backoff_sweep.py`
- `backoff_extended_sweep.py`
- `backoff_profile.py`
- `backoff_requested_us.py`
- `backoff_repro.py`
- `backoff_overthrottle.py`
- `test_backoff_sweep.py`

禁止対象、docs、patches、台帳、freeze はまとめた `git diff --exit-code` が rc=0。helper 範囲の codec 名検索は該当なしで、codec 定義は引き続き `backoff_extended_sweep.py:64,71` にあります。新 test file、commit、push はありません。

`git status` には対象外の未追跡 `output/insights/2026-09-09_t2419-meaning-decl/` もあります。今回編集していませんが、開始時 status がないため由来は断定していません。

## 総括

裁定 v2 の production 実装とテスト変更は完了しました。  
F718 は driver intent と実 C++ 観測の不一致として拒否されます。  
禁止面と codec 配置は不変です。  
pytest child が起動できていないため、検証は未完了であり closed とは申告しません。