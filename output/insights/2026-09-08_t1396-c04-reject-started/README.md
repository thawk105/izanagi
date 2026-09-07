# [T-1396] 判定器 C04 の到達対象へ reject_started_trial を足す

- wave branch: `worktree-dev-wave-t1396-c04-reject-started`
- 実装 commit: `c0a770838f03e17a21cef1b3cde76ef2138c6420`
- 起点 main: `80ece589701ced404f52524e8dc545fa6d3be807`
- 正本: `docs/decisions.md` D1292 (2026-08-29 裁定、推奨どおり)

## 何をしたか

`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` の condition 4 は
到達経路を 3 件要求している。判定器 `_evaluate_c04` は 2 件しか見ておらず、3 件目の
`run_trial preflight -> reject_started_trial` が検査されていなかった。この 1 件を足した。

契約側の exact-set (`orchestrator/tests/test_s8c_preregistration_invariant.py` の
`MACHINE_CONTRACT_FUNCTION_CHECKS`) は既に C04 の 5 symbol を pin しており、
`reject_started_trial` も含まれていた。欠けていたのは判定器だけだった。

## 実測

### brief 前の read-only probe

判定器を変えずに `_declared_call` を process 内で包み、3 件目を同時に問い合わせた。
現行 main (`0e02169b0`) で `reject_started_trial=True` が返り、C04 は
`EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` のままだった。

**この実測の射程**: 同一 commit・実 resolver に限定した結論である。token-only fixture、
過去 commit、将来の production source、activation / source-binding の結果へ一般化しない。

### production の到達経路 (実体)

`p3_autonomous_workload_trial.py:4602` の `run_trial` → 同 `:1430`
`_reject_registered_lifecycle_duplicate` → 同 `:1432`
`trial_registry.reject_started_trial` → 定義は `trial_registry.py:4796`。

### 焦点走 (統合 commit 後)

判定器は `campaign_lock.py` の contract loader path 一覧に載る HEAD blob 束縛 file なので、
未 commit のまま走らせると `contract-loader-drift` で偽赤になる。統合 commit 後に走らせた。

| 対象 | 結果 |
|---|---|
| `test_s8c_preregistration_predicates.py` 単独 | 218 passed |
| `test_s8c_preregistration_core.py` / `test_artifact_admission.py` / `test_t671_source_binding.py` / `test_campaign_lock_codec.py` / `test_s8c_preregistration_invariant.py` | 927 passed, 5 skipped |
| `test_s8c_cli_entrypoints.py` / `test_s8c_gate_report.py` (段 6 レビューが指摘した広義 consumer) | 25 passed |

新しい負例 2 本の実走も名指しで確認した (2 passed)。

### 変異

`mutation-probe-report.json` (全件 SURVIVED 登録で観測 node を集める probe) と
`mutation-main-report.json` (観測集合を完全一致の期待 node として登録した本走) を置く。

| 変異 | 内容 | 本走の結果 |
|---|---|---|
| MU-1 | 判定器の対象 tuple から 3 件目を削除 | KILLED |
| MU-2 | 3 件目を `forbid_trial_restart` の重複へ書き換え (恒真へ戻す) | KILLED |
| MU-3-equivalent | tuple を list へ変える等価変異 | SURVIVED (登録どおり) |

**帰属**: MU-1 / MU-2 が赤にした node は、新しい負例 2 本
(`test_c04_rejects_missing_started_trial_preflight` と
`test_current_repository_c04_rejects_missing_started_trial_preflight@s8c-predicate-snapshot`)
**だけ**である。判定器は contract loader 束縛 file なので drift mask の混入を懸念したが、
この 2 本は `evaluate_all` を直接呼び `capture_contract_loader_binding` を通らないため、
mask ではなく固有の kill である。runner argv を当該 test file 1 本に絞ったので、
repo-wide の mask はそもそも走行に入っていない。

MU-3 の SURVIVED は、この matrix が「殺せないこと」も報告できる状態にあることの正例である。

### 受入全走

4 回投入した。緑は 4 回目 (tested_main `240ee6360` / tested_tip `160c6902d`)。

| 回 | 結果 | 判定 |
|---|---|---|
| 1 | 21568 collected / 2 failed | **当 wave 起因**。新しい実 repo 負例へ付けた `xdist_group` mark が `test_real_repo_serialization.py` の group golden に未登録だった (F42 の再発) |
| 2 | 21571 collected / 1 error | 非帰属。`parent` lock の EX 取得が他 6 process の READ 保持で deadline 超過。単独再走は緑 (`DW-O18`) |
| 3 | merge-message-provenance rc=70 | main が進み、両親がともに `test_real_repo_serialization.py` を触ったため Codex `role=author` の merge message が必要になった |
| 4 | 21598 collected / **21530 passed / 68 skipped / 赤 0** | `verdict=child-green` |

1 回目の赤は、単純な登録追加では閉じなかった。group の golden
(`_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN`) と、その group の共有 fixture の consumer 集合
(`_REAL_REPO_FIXTURE_ACCESS_GOLDEN` の `current_commit_snapshot[module]`) は**同一の
frozenset を共有**しており、group にだけ足すと fixture consumer 側の実測一致検査が破れる。
負例を共有 fixture の consumer へ変え、共有 snapshot の working tree は書き換えず
tracked bytes を自前の repo へ複製して変異させる形で閉じた
(`verbatim/s6-fix1.md`)。検査の内容は 1 つも弱めていない。

3 回目の merge については Codex `role=author` が合成を監査した (`verbatim/s6-merge-author.md`)。
両親の変更は同じ file の別々の frozenset に入り、group の exact golden も fixture consumer
閉包も保たれる。集合から 1 要素だけ取り出す箇所で辞書順の先頭が変わるが、file と group が
固定値なので意味は不変である。起草された message は `verbatim/merge-message.txt`。

## 判定器へ足さなかったもの

registry 側の `_functions(registry)` 存在検査は足していない。段 3 の相談 2 本が独立に
「先行する `_declared_call` が真なら後段の存在検査は必ず真になり、定義欠落は先行層の
`crash-policy-cell-partial` で先に return するので `restart-guard-absent` へは到達しない」と
指摘した。冗長な層は負例の単一理由性を壊すため足さない。

## 残る限界 (裁定へ返した)

`verbatim/s4-adjudication.md` の「scope 外の real 所見」を正本とする。要点は 3 つ。

1. C04 は到達可能性だけを見て、契約が書く呼出し**位置** (preflight、crash handler) を見ない。
   既存の 2 件も同じく位置未検査である。
2. callee 本体を見ない。`reject_started_trial` の本体を `pass` にしても判定は変わらない。
3. 契約の `field_paths` (`trial_lifecycle.started_once` / `restart_forbidden`) を判定器が読まない。

いずれも D1292 の「reachable target を 1 件足す」を超えるため、この wave では実装していない。
