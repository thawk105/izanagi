## 実装

指定された 2 file のみ変更しました。

- [reflux_formal_consumer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-unit-c/orchestrator/campaign/reflux_formal_consumer.py:371)
  - disk 上の固定 path `origin/recovery-envelope.json` を再読し、lifecycle 束縛 digest と in-memory plan の双方に一致させます。
  - plan identity と `campaign_output_root` から canonical root を計算します。
  - `campaign.lock` を symlink 非追従で読み、物理 identity、attempt capability、query ordinal、論理 campaign ID を再導出します。
  - WAL projection と source WAL の双方を canonical root 配下に限定します。
  - native／legacy trigger shape の混在を拒否します。
  - FC05a の `build_attempt_id` 相異検査は未変更です。
- [test_reflux_formal_consumer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-unit-c/orchestrator/tests/test_reflux_formal_consumer.py:723)
  - envelope 差替え、別 path、q10/q11 config 交換、別 trial の 33 WAL、過去 attempt、非 canonical 配置、mixed shape の負例を追加しました。
  - q10/q11 などの負例では FC05a〜FC05c と topology を先に直接通す構造にしています。
  - `result-evidence/v1` の参照集合が従来の 2 本だけであることも固定しました。

受入要件 12・18・R2 は実装していません。

## 検査

実装済み・未実走です。

実行を試みた範囲:

- `test_reflux_formal_consumer.py::test_formal_consumer_requires_all_physical_binding_kwargs`
- `test_reflux_formal_consumer.py --collect-only`

どちらも `tools/run_tests.py` が Pegasus dispatch 前の `qstat -Q` で UID 認証エラーとなり、child は起動していません。したがって緑とは報告しません。変異実走も同じ理由で未実施です。

静的には以下を確認済みです。

- 2 file の AST parse 成功
- module import と公開 signature の確認成功
- `git diff --check` 成功
- 変更 file は所有対象の 2 file のみ

## 残る赤

未実走のため実測した赤ではありませんが、統合前に静的に残るものは次です。

- Unit A の v2 がこの worktree に未着地なので、現在の resolver は新 fixture の `execution-provenance/v2` を FC05b で拒否します。xfail 化していません。
- Unit B 所有の production caller は新しい必須 kwargs をまだ渡していないため、origin 実行時には `TypeError` になります。

## 他単位への波及

`evaluate_formal_origin` の caller は全 2 箇所です。

- `p3_autonomous_workload_trial.py:1654`: Unit B が `campaign_output_root`、`origin_run_plan_sha256`、`attempt_capability_sha256` を渡す必要があります。
- `test_reflux_formal_consumer.py:544`: 共通 kwargs は更新済みです。

commit は作成していません。

## 保証限界

実行後に、計算どおりの canonical root へ整合した `campaign.lock` と WAL を後置した入力は拒否できません。D1674 の trusted-writer 運用前提の外側であり、この限界は狭めていません。

## 総括

- 要件 14・15・17 を実装しました。
- FC05a は未変更です。
- `result-evidence` の ref は増やしていません。
- 所有 2 file 以外は未編集です。
- AST・import・diff check は成功しました。
- pytest と変異検査は dispatch 障害のため未実走です。
- Unit A の v2 と Unit B caller 更新が統合上必要です。