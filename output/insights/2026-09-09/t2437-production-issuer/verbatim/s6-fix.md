## 所見ごとの対応表

| 所見 ID | 状態 | 対応 | 根拠 |
|---|---|---|---|
| P1 | closed | context なしでは issuer 引数自体を評価しない call-site guardを追加。番人 `AuthorizedContract` / `EvalResult` 負例も追加 | [loop.py:643](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix1/orchestrator/campaign/loop.py:643)、[test_reflux_campaign_issuer.py:754](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix1/orchestrator/tests/test_reflux_campaign_issuer.py:754) |
| P2 | closed | 第1選択を採用。contextへ env/mode/calibration を追加し、issuerを実 `receipt_matches_contract()` に接続。required中心正例と schema/env/mode 負例を追加 | [reflux_result_evidence.py:238](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix1/orchestrator/campaign/reflux_result_evidence.py:238)、[reflux_result_evidence.py:1223](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix1/orchestrator/campaign/reflux_result_evidence.py:1223)、[test_reflux_result_evidence.py:1219](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix1/orchestrator/tests/test_reflux_result_evidence.py:1219) |
| P3 | closed | identity 解決失敗側・通常 recovery 側の既存 terminal skipを無条件拒否。旧 attempt 推測 helperを削除 | [loop.py:634](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix1/orchestrator/campaign/loop.py:634)、[loop.py:688](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix1/orchestrator/campaign/loop.py:688)、[test_reflux_campaign_issuer.py:931](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix1/orchestrator/tests/test_reflux_campaign_issuer.py:931) |
| P4 | closed | originless の file/stage/payload-keyを具体的 literal 集合へ固定 | [test_reflux_campaign_issuer.py:688](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix1/orchestrator/tests/test_reflux_campaign_issuer.py:688) |
| P5 | closed | identity-error、terminal skip、eval-exception の attempt IDあり/なしで拒否前後の evidence file不変を検査 | [test_reflux_campaign_issuer.py:1006](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix1/orchestrator/tests/test_reflux_campaign_issuer.py:1006)、[test_reflux_campaign_issuer.py:1127](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2437-fix1/orchestrator/tests/test_reflux_campaign_issuer.py:1127) |

## 実走した検査

- `orchestrator/tests/test_reflux_result_evidence.py` 全78 node: **78 passed**
- `orchestrator/tests/test_pipeline_verify_result_retention.py` 全5 node: **5 passed**
- `orchestrator/tests/test_reflux_campaign_issuer.py` 全13 node:
  - 通常走: **5 passed / 8 failed**
  - 8件すべて、指示に記載された未 commit `loop.py` の `contract-loader-drift`
  - 診断走ではこの closure checkだけを明示的に迂回し、**13 passed**
- 親の焦点3 node:
  - `test_paper_story_a2_certification.py::test_official_run_observes_dependency_receipt_after_condition_prebuild`: passed
  - `test_paper_story_a1_paired.py::test_a1_exact_marker_routes_loop_to_dedicated_replay_and_append`: passed
  - `test_t1416_backoff_compiler_binding.py::test_run_campaign_forwards_expected_toolchain_to_evaluate_for_each_genome`: 通常走は sandboxの `/tmp/.git` による output-root拒否。該当環境判定だけを迂回した診断走は passed
  - 元の `contract_sha256` / `build_attempt_id` `AttributeError` は3件とも再現しなかった
- AST parse、`git diff --check`: passed
- 変更 path: 指定された4 fileのみ

## 正例が通した実 callee の列

中心正例は実 `run_campaign()`、実 `_authorize_measurement()`、実 calibration loader、実 v2 receipt builder、実 `receipt_matches_contract()`、実 verifier、deriver、assembler、create-only issuer、WAL、resolverを通過しました。

stub / seam:

- trace file生成のみ `trace_runner` seam
- 物理 attestation probeの観測値を deterministic profileへ差し替え。receipt生成・比較・検証本体は実 callee
- sandbox tmp rootの `_has_git_ancestor` 環境 seam
- 再発行負例だけ campaign claim再取得を差し替え。最初の正例発行では未使用
- 13-node診断走だけ、既知の未 commit source-closure checkを迂回。正式な緑には数えていない

## 現行の受理・拒否挙動

| 経路 | fix前 | fix後 |
|---|---|---|
| originless | issuer専用属性を評価し `AttributeError` の可能性 | 属性を評価せず、result-evidence file 0、WAL/file集合はliteral baselineどおり |
| receipt | contract hashを含む任意 dictを受理 | 権威 verifierが schema、env、mode、calibration bindingを検証。不一致は書込み前拒否 |
| required attestation | 中心正例がmode-none receiptを合成 | 実 `_authorize_measurement()` が実 v2 receiptを生成 |
| mode-none production | 合成receiptで発行可能に見せていた | 実経路はreceiptなしのため発行拒否 |
| accepted terminal recovery | 過去WALと現在receiptを混ぜて発行可能 | contextありは両skip分岐とも無条件拒否、file追加なし |
| eval-exception | contextありの判断が未検査 | attempt IDあり/なし双方で拒否伝播、file追加なし |

## 所有外 caller・共有 fixture・consumer test への波及

- `ResultEvidenceIssuanceContext` constructorはrepository内では所有2 test fileだけ。
- `issue_campaign_result_evidence()` のproduction callerは `loop.py`だけ。
- `run_campaign()` signatureは本fixで変更なし。既存callerの指定変更なし。
- 焦点consumerは `paper_story_a1_paired`、`paper_story_a2_certification`、`t1416_backoff_compiler_binding`。
- 共有 `test_campaign.py` fixture、`execution_guard.py`、formal consumer、既存 `EvalResult` consumerは未編集。
- 既存期待値の弱体化なし。originless自己比較は具体集合へ強化した。

## 受入所要台帳へ登録すべき nodeid と実測所要

campaignの秒数はclosure-checkだけを迂回してassertion本文まで完走した診断JUnit値です。

- `test_pipeline_verify_result_retention.py`: local-retention `0.251s`; remote-fanout `0.287s`; exact-type `0.307s`; accepted-none `0.191s`; prebuild-attempt-id `0.119s`
- `test_reflux_campaign_issuer.py`: center `4.079s`; originless-literal `1.882s`; originless-sentinel `0.003s`; context-shape `0.003s`; context-root/type `0.004s`; accepted-skip `[False] 0.216s`, `[True] 0.217s`; identity-error `0.186s`; legacy-eval-exception `0.184s`; context-eval `[False] 0.188s`, `[True] 0.260s`; invalid-capability `0.003s`; signature `0.001s`
- `test_reflux_result_evidence.py`: producer-success `0.301s`; nonzero-offset `0.401s`; absent-receipt `0.165s`; unauthenticated `[schema] 0.156s`, `[env_tag] 0.158s`, `[attestation_mode] 0.183s`; interleaved `0.184s`; nonexact-result `0.186s`; collision `0.297s`; append-survival `0.308s`

## 契約の問題

無し。

## 総括

P1〜P5をすべて実装・検査しました。通常 issuer 全走の残る赤8件は、指示どおり未 commit `loop.py` の enforcement-source closure driftであり、実装回帰ではありません。commit、docs編集、push、branch操作は行っていません。