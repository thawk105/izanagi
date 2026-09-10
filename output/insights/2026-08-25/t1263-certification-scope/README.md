# T-1263 — 材料レポートの認証水準の明記と、載る packet の evidence 検査

wave branch `worktree-dev-wave-t1263-certification-scope`、統合 commit `24348da8`。
裁定は 2026-08-17 /rulings 全件 第 5 回 (明記 + 条件)。
worklog エントリと設計判断は fold 後の canonical 台帳が正本であり、本書は逐語と実測の置き場である。

## 何を変えたか

対象は A/B 実験装置 `tools/codex_reasoning_ab.py`。

1. `verify` / `aggregate` の返値へ `certification_scope` を足した。certified なのは `valid` だけ、
   adjudication の中間 artifact (packet、packet-state、verdict log、verdict freeze、revealed map)
   は未認証であることを機械可読に宣言する。宣言は公開 API の全 return path が付け、
   集計 helper `_aggregate_verified` の返値には付けない。
2. `_load_adjudication` (packet と run の唯一の join 点) へ、snapshot evidence 再走に成功した
   run 集合を必須引数で渡し、材料レポートに載る packet の由来 run が全部その集合に入ることを
   検査する。中間層には検査を足していない。
3. 宣言の閉世界主張を、`_load_adjudication` が実際に読む manifest descriptor key を AST で
   導出して突き合わせる node と対にした。
4. run ごとの pre/post evidence 一致を全 run で検査するようにした。以前は同一 oracle identity を
   共有する 2 本目以降で丸ごと省略されていた。

## 実測

### テスト

| 走行 | 対象 | 結果 |
|---|---|---|
| 焦点走 1 | 新規 node 5 件 | 5 passed / 106.16 秒 (dispatch 944918) |
| 焦点走 2 | 対象 file + consumer 4 file | 1 failed / 573 passed / 3 skipped / 184.63 秒 (dispatch 944919) |
| 焦点走 3 (fix 後) | 新規 node 6 件 | 6 passed / 128.14 秒 (dispatch 944994) |
| 焦点走 4 (fix 後) | 対象 file + メタテスト 5 file | 652 passed / 3 skipped / 206.90 秒 |

焦点走 2 の赤は本 wave の回帰である。新規 node 2 本が module scope 共有 fixture
`benchmark_snapshots` を使うのに `REAL_REPO_SERIAL_NODES` と独立 golden へ未登録で、
`test_real_repo_group_collection_exactly_matches_canonical_nodes` が落ちた。fix で両方へ登録した。

### 実行時間

新規の重い node 2 本の call 時間を計算ノードで実測した。

| node | fix 前 | fix 後 |
|---|---:|---:|
| `test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run` | 88.75 秒 | 9.09 秒 |
| `test_replay_forwards_only_successful_snapshot_evidence_to_adjudication` | 72.34 秒 | 11.04 秒 |
| 合計 | 161.09 秒 | 20.13 秒 |

短縮は manifest 構築段の `verify_snapshot` を `(解決済み snapshot path, case)` で memo 化した
ことによる。**replay 段 (= 検査対象) は本物の verifier のまま**である。memo が忠実でなければ
replay 段の canonical 比較が食い違って赤くなるので、テスト自身が memo の忠実性を示している。
参考: 既存 end-to-end node `test_verify_replays_complete_fake_codex_experiment` は
memo を使わず 92.83 秒 → 92.17 秒で不変である。

### 変異 matrix

spec は `mutation-spec.json`、本走の結果は `mutation-result.json`、期待 node を実測した
probe は `mutation-probe.json`。runner は
`python3 tools/run_tests.py orchestrator/tests/test_codex_reasoning_ab.py -k <焦点> -n 0 -rf -q --force-dispatch`。

baseline PASSED、**KILLED 7 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0 / matching 8**。

| ID | 変異 | 結果 |
|---|---|---|
| M1 | `certified_report_fields` へ `packet` を足す | KILLED |
| M2 | `uncertified_artifact_kinds` から `packet` を落とす | KILLED |
| M3 | `material_packet_requirement` を `packet_self_certified` にする | KILLED |
| M4 | evidence 集合でなく final attempt 全 run ID を join へ渡す | KILLED |
| M5 | join 点の membership 検査を削除する | KILLED |
| M6 | pre/post 比較を cache miss 分岐の内側へ戻す | KILLED |
| M7 | evidence 集合を常に空にする (過剰拒否の正例検査) | KILLED |
| M8 | cache key を path 単独へ退行させる | SURVIVED (等価) |

**期待 node は裁定文から転記せず、全件 SURVIVED 期待の probe を先に回して実測した。**

M8 は等価変異である。注入実在は harness の `anchor_counts` と `injection_diff_sha256` で
確認したうえで、`_artifact_path` が descriptor の `sha256` を実 bytes と照合して落とすため、
同じ path に別の sha または case が結び付く入力は identity を組む前に必ず拒否される。
tuple key は検出力ゼロの防御的変更として残した。

### 検出力の重複

M1〜M3 は新設の宣言 node だけでなく既存 end-to-end 正例でも殺される。M7 は既存正例だけで殺される。
したがって新 node のこれらに対する純増検出力はゼロである。純増があるのは M4 / M5 / M6 で、
M6 だけが公開 manifest 一本で受理集合を動かす。

## 反証された親の前提

段 1 brief の (P1)「未検証 snapshot 由来の packet が `valid: true` へ到達する経路が現行に実在する」は、
段 2 と段 3 レンズ A が独立に反証した。正規経路では `make_packets` が final attempt の `output`
descriptor を必須にするため packet を作れず、手で組んでも `output_sha256` の欠落で adjudication の
SHA 結線が別の理由を積む。同時に brief の「本検査で受理集合が狭まる」も撤回した。

## 逐語

`verbatim/` に段 1 brief、段 2 プラン、段 3 の 2 レンズ、段 4 裁定、段 5 実装報告、
段 6 レビュー 2 本と fix 報告を置く。
