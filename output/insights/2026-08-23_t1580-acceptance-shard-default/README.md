# 受入全走の分割を Pegasus 既定にした wave — 変異 matrix の逐語

authority: none
default_effect: no-state-change

wave: dev-wave-t1580-shard-default-pegasus / 2026-08-23 / anchor `6c7ae156`

段 4 が事前登録した変異 M1〜M9 を、fix 2 巡後の統合 commit に対して実施した記録である。
この wave は実装差分が非ゼロ (893 insertions / 39 deletions) のため、`DW-S04` の変異 matrix 免除
(「実装しない」裁定かつ実装差分ゼロ) に当たらない。

## 変異 matrix (本走 = 2 巡目)

anchor commit `6c7ae1566cd6edda178bd41e2831b9dad691e260` の使い捨て worktree
(`tools/mutation_worktree.py --runner-mode dispatch --detached`)。
runner は `tools/run_tests.py --force-dispatch orchestrator/tests/test_run_tests_shards.py -rf`。
spec sha256 = `e281623b19f02b5a63e0b890acb2da32cef180d777fd3d968d68a59c043429d3`。

| ID | 変異 | 結果 | 期待赤 node 数 |
|---|---|---|---|
| M1 | 既定 K の定数 `2` → `1` | KILLED | 6 |
| M2 | 適格条件から `is_acceptance` を落とす | KILLED | 5 |
| M3 | 適格条件から Pegasus LOGIN 条件を落とす | KILLED | 5 |
| M4 | 適格条件から `bounded_membership is not True` を落とす | KILLED | 5 |
| M5 | 明示 2/3 の不適格を `raise` せず K=1 へ縮退 | KILLED | 14 |
| M6 | admission guard を `and not shard_mode` へ戻す | KILLED | 4 |
| M7 | 親が child 起動済みでも集約 attestation を許す | KILLED | 2 |
| M8 | 集約 attestation を恒常的に不発火にする | KILLED | 7 |
| M9 | 適格判定を常に `False` にする (過剰拒否の正例) | KILLED | 8 |

baseline = PASSED (rc=0)。summary = KILLED 9 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 /
PARSE_ERROR 0。総所要 5.2 分。期待赤 node の完全集合は
`verbatim/mutation-spec.json` の `expected_nodes`、観測は `verbatim/mutation-ledger.json` の
`failed_nodes` が逐語である。

**単独変異の kill 証拠から外した冗長 gate**: 適格条件のうち `positional`、`internal_shard_spec`、
`_validate_shard_outer_args` の 3 述語は実入力では互いに mask し合う (positional を渡せば
`raw_args` が非空になり outer-argv 述語が先に false になり、internal spec は必ず COMPUTE site を
伴う)。resolver の論理関数としては検査するが、`DW-M03` に従い単独変異の証拠にはしない。

## erratum — 1 巡目の MISMATCH 1 件は probe の計測汚染だった

1 巡目 (spec sha256 = `c8f893b51df6f670dc5c76da46b4dc1c80c8dfb5c39f89b29bbe88387865c3d5`、
逐語 = `verbatim/mutation-ledger-probe.json`) は baseline PASSED・KILLED 8・**MISMATCH 1 (M3)**・
SURVIVED 0、総所要 12.0 分だった。1 巡目と 2 巡目の spec の差は **M3 の `expected_nodes` だけ**で、
1 巡目の sha は同 ledger の `spec_sha256` に記録されている。

M3 の期待 node を確定するために親が行った probe (`verbatim/probe-nodes.json`) は、
統合 commit 上で 1 変異ずつ適用して `python3 tools/run_tests.py <対象 file>` を走らせ
`git checkout --` で復元する形だった (`DW-O19`)。この経路は login node の**ローカル bounded scope
の中**で pytest を走らせるため、テスト process 自身の `_bounded_scope_membership()` が `True` を
返す。M3 は適格条件から LOGIN 条件だけを落とす変異なので、bounded 条件が残っている probe 環境では
`test_explicit_shards_reject_nonlogin_without_fallback[2]` と `[3]` が
`eligible=False` のまま従来どおり rc=16 を返して pass してしまい、期待集合が 5 node から
3 node へ縮んだ。計算ノードには bounded scope marker が無いため、本走ではこの 2 node も赤になる。

**得た規律**: 期待 node の probe は本走と同じ実行経路で取る。実行経路が違うとテスト process 自身が
読む環境述語が変わり、期待集合が縮む。1 巡目の結果は `DW-M02` に従い消さずに本節へ残す。
この規律の `docs/dev-wave/mutation.md` への入庫は docs 予算超過で保留し、裁定へ返した。

## 変更面

- `tools/run_tests.py` — K の解決を env 字句解析と純粋な解決関数へ分離し、admission-first を配線した。
- `tools/acceptance_shards.py` — 集約 no-verdict attestation を infra 失敗 6 分岐へ接続した。
- `orchestrator/tests/test_run_tests_shards.py` — 168 node。
- `orchestrator/tests/test_run_tests_preflight.py` — 既存 2 テストへ明示 K=1 の opt-out を足した。

## 親の焦点走 (受入全走とは別)

- `orchestrator/tests/test_run_tests_shards.py` = 168 passed / 6.52 秒
- consumer 9 file (`test_run_tests_preflight` / `test_run_tests_nproc` / `test_run_tests_task_run` /
  `test_run_tests_testops_observation` / `test_pytest_collection_config` / `test_acceptance_launcher` /
  `test_dev_wave_wait` / `test_dev_wave_land` / `test_pegasus_dispatch_compute`)
  = 1191 passed / 1 skipped / 64.93 秒
