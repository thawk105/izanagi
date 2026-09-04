## 総括

指定された 3 file だけを新設しました。既存 tracked file、5-file pin、docs、公開 dataclass、現行 reason enum は変更しておらず、commit もしていません。

比較実験と production-route 診断は実装済みです。ただし正式な 78 走比較と非後退 suite は、指定 scratch root が read-only かつ test dispatch が `rc=16` で子を開始できなかったため、実装済み・未実走です。したがって採用候補の測定結論は出していません。

## 実装した file と構成

- [p3_b4_producer_auth_experiment.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-author/orchestrator/campaign/p3_b4_producer_auth_experiment.py:39)
  - issuer / raw assembly / 一時的 6-member frozen prototype
  - 固定 trust anchor と guard
  - exact prototype patch、12 負例 + POS-1
  - baseline / prototype 帰属、`BASELINE_REJECTED`、`ABORTED`
  - scratch tree、主 worktree 不変検査
  - prereg 内容再導出
  - canonical comparison report serializer
- [p3_b4_rogue_producer_support.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-author/orchestrator/tests/p3_b4_rogue_producer_support.py:212)
  - production producer を import しない別 path 実装
  - P/T/C の attempt artifact、raw analysis、source bytes を実生成
  - raw/source digest を自己整合に再構築
- [test_p3_b4_producer_auth_experiment.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-author/orchestrator/tests/test_p3_b4_producer_auth_experiment.py:560)
  - 期待 matrix、W01〜W09、callsite 一回性
  - frozen production route、C1 の 2 process
  - 78 走 harness、候補別 29-node 非後退走
  - 主 worktree、prereg、volatile payload の meta 検査

## 測定 harness の置き場所と理由

隔離、anchor 凍結、帰属、集計、serializer は experiment module に置きました。guard と測定規則を一つの実験境界に集約しつつ、production file から guard 実装を分離するためです。

具体的な 201-block production worker は test file に置きました。既存の実 producer fixture に依存するコードを campaign module へ逆流させないためです。rogue producer は別 path の専用 support file に分離しました。

## 実走した node と結果

pytest node は実走できていません。

- `python3 tools/run_tests.py orchestrator/tests/test_p3_b4_producer_auth_experiment.py -q`
  - `qstat -Q preflight rc=1`
  - wrapper `rc=16`
  - `child_started=false`
  - 全 24 test function、parameter 展開後 28 node は実装済み・未実走
- 非後退 node:
  - `...::test_candidate_enabled_producer_29_node_non_regression[issuer]`
  - `...[raw_assembly]`
  - `...[frozen_consumer]`
  - 各 node が既存 producer 29 node を走らせる構成。実装済み・未実走
- `...::test_full_baseline_and_prototype_comparison_in_external_scratch`
  - 13 case × 3 candidate × baseline/prototype = 78 走
  - 実装済み・未実走

node 外の配線診断では以下を実走しました。

- issuer/raw: 正規 anchor 受理、C0-P 改変拒否
- rogue P/T/C: attempt/raw/source file を各三種生成
- frozen 6-member receipt: 正規 producer を受理
- frozen production route: POS-1 受理、C0-P 拒否、C1-P の 2 process 拒否、R-P は evaluator まで到達して SURVIVED
- raw R-P: 既存 `source_rederivation` が拒否し、追加 guard の増分 KILL ではないことを確認
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし

## 赤の内訳

pytest の test failure は観測されていません。子 test が開始されていないため、緑とも報告しません。

wrapper infrastructure failure は計 4 回で、すべて `qstat -Q preflight rc=1`、`rc=16`、子未起動です。

途中の配線診断では rogue の Path 型判定、frozen authority context、C1 process 間 state の直列化に問題を検出しました。順に修正し、最終診断では該当経路が通っています。

## 制約 meta-test

親の名指しに加え、次を独自に洗い出して test 化しました。

- scratch root が全 registered worktree の外にある
- scratch 破棄失敗を `ABORTED` にし、比較値へ昇格しない
- 全 candidate anchor を最初の rogue 変異前に凍結する
- prototype patch と mutation old bytes の一意出現
- 実 callsite の guard 呼出しが各一回だけ
- frozen の順序が assembly → receipt → guard → evaluator
- frozen 述語が digest 不一致だけである
- rogue が production producer を import しない
- 既存 tracked prototype file と 5-file pin が base commit と同一
- canonical report に時刻、絶対 path、working-tree payload がない
- `observed_producer_sha256` を追加していない
- W01〜W09 と test node が一対一
- U+0300〜U+036F が新設 file に存在しない

これらの pytest node は実装済み・未実走です。AST、anchor、prereg 再導出、既存 file 差分、Unicode、scratch 破棄については node 外診断が成功しています。

## 波及可能性の静的列挙

所有外 caller と consumer test の候補は次のとおりです。

- `p3_b4_prerun_issuer`
  - caller: raw producer、material report
  - tests: prerun issuer、raw producer
- `p3_b4_raw_record_producer`
  - caller: material report
  - tests: raw producer、material report
- `p3_b4_analysis_path`
  - caller: material report、analysis prereg consumer
  - tests: analysis path、analysis prereg consumer、raw producer
- `p3_b4_analysis_prereg_consumer`
  - tests: analysis path、analysis prereg consumer
- `p3_b4_material_report`
  - tests: material report、real repo serialization

共有 fixture 依存は `_eligible_attempts`、`_planned`、`_build_full_publication_evidence`、`_publish_full_publication`、`_Evidence`、`_PublicationEvidence` です。fixture shape が変われば新設 harness に波及します。

## 受理・拒否挙動の変更点

現行 production の受理・拒否挙動は変えていません。既存 tracked production file は base commit と同一です。

変更は新規 experiment を scratch prototype として有効化した場合だけです。

- issuer: issuance 時点の producer bytes 不一致を拒否
- raw assembly: assembly 入口で専用 `producer_auth_mismatch` を拒否
- frozen: material-report の実入力構築後、evaluator 前に独立した `producer_auth_rejection`
- raw R 系の既存拒否は `BASELINE_REJECTED` として増分から除外
- D 系は追加 guard の対象外で、post-assembly authenticity は保証しない

## 裁定に従えなかった項目

- 指定 `/work/1/SFC/tanab/t2103-scratch/` は現在の sandbox で `EROFS` でした。このため正式な 78 走は実装済み・未実走です。
- Pegasus test wrapper は queue preflight で `rc=16` となり、全 pytest node と候補別 29-node 非後退走は実装済み・未実走です。
- このため比較測定の勝者、6/6 達成有無、非後退の最終結果は確定していません。

上記以外に、設計を迂回した項目はありません。