## 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| 1. envelope root 分裂 | partial | 実装済み・未実走。保存先と consumer 引数を、runtime が保持する同一 `campaign_output_root` に統一 |
| 2. lifecycle terminal 欠落 | partial | producer 結線と terminal assertion を実装。共有台帳の変更待ち |
| 3. 物理錠前 fixture | partial | 実装済み・未実走。33 canonical root に lock、WAL、projection、provenance を実体化 |
| 4. 相異の二重検査 | partial | 未変更。拒否入力集合が不変と証明できず、既存期待値の変更禁止に従った |
| 必須 kwarg 3 件 | partial | 前巡差分を維持し、`campaign_output_root` の値だけ所見 1 に合わせて是正 |

`closed` は実走できていないため申告していません。`regressed` はありません。

## 実装内容

[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix1/orchestrator/campaign/p3_autonomous_workload_trial.py) では次を変更しました。

- `OriginTrialRuntime.campaign_output_root` を追加し、`run_root` を一度だけ格納。
- envelope writer と formal consumer の両方が、その同じ field を使用。
- projection 未生成の origin failure に限り、`failure_reason="origin-producer-failure"` を terminal API へ渡す。
- origin の budget insufficient も、非空の失敗理由付きで終端。
- originless では `failure_reason` を渡さないため、既存 wire bytes と受理集合は不変。

[test_p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix1/orchestrator/tests/test_p3_autonomous_workload_trial.py) では次を追加しました。

- envelope 保存 root と consumer の root が同一であることを直接 assertion。
- producer-derived 33 identity の canonical root に `campaign.lock`、source WAL、ordered projection、v2 provenance を生成。
- provenance の `fixture-run-*` を producer-derived identity に置換。
- observation 開始失敗後の台帳が `start`、`terminal` の順で永続化され、非空 `failure_reason` を持つことを assertion。

## 所見 4 の保留理由

topology builder は33個の `planned_campaign_run_identity` 相異を拒否しますが、`identity_preimage` 自体は受け取りません。また `_derive_origin_campaign_runs` を直接呼ぶ既存テストは、producer 側で重複を拒否する期待値を固定しています。

したがって検査を除くと、この直接呼出し面の拒否入力集合が変わります。既存期待値の変更・削除が禁止されているため、「除いても集合が変わらない」と確認できず、指示どおり除去していません。

## 波及可能性

- production の formal consumer caller は `_complete_origin_runtime` の1件で、更新済みです。
- private helper `_prepare_origin_trial_runtime` の既知 caller 2件は、新しい root 引数へ更新済みです。
- 共有 fixture `reflux_origin_fixture_builder.py` は未変更で、P3 fixture 内で物理証拠を複製・整合させています。
- `test_reflux_formal_consumer.py` は未変更です。同ファイルの `_materialize_physical_evidence` と同じ物理構成です。
- `trial_registry.py` には現在まだ `failure_reason` kwarg がなく、共有変更の取り込みまで所見 2 の追加 test は赤になります。
- 将来の実 producer は、33 campaign layout を `run_root` 配下へ作る必要があります。

## 検査

- `git diff --check`: 成功
- 対象2 file の AST parse: 成功
- 対象2 module の import: 成功
- 焦点 nodeid `test_origin_public_path_preserves_capability_identity_and_projects_terminal`: runner が `qstat -Q` preflight で rc=16、子 process 未起動
- test runner が生成した一時 dispatch artifact は除去済み
- 差分は所有2 file のみ
- commit、docs 編集なし

## 総括

所見 1 は単一の `run_root` 由来へ結線し、同一性 assertion を追加しました。  
所見 2 は失敗理由付き terminal 呼出しと永続 terminal assertion を実装しました。  
共有台帳未統合のため、所見 2 は想定赤のままです。  
所見 3 は33個の canonical physical evidence を実体化しました。  
所見 4 は拒否集合不変を確認できず、既存期待値を守って未変更です。  
焦点 test は rc=16 で未実走、静的検査と import は成功しました。  
変更は所有2 file のみで、commit は作成していません。