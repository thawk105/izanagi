## 対応表

| 所見 | 状態 | 結果 |
|---|---|---|
| 1. envelope root 分裂 | partial | 未修正。停止条件に従い、追加実装を中止 |
| 2. lifecycle terminal 欠落 | partial | 台帳側に projection 無しの origin terminal 形が存在しない |
| 3. 物理錠前 fixture | partial | 未修正 |
| 4. 相異の二重検査 | partial | 未修正 |
| 前巡の必須 kwarg 3 件 | closed | 未コミット差分を維持 |

## 停止理由

[trial_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix1/orchestrator/campaign/trial_registry.py:4900) の `record_trial_terminal` は、origin lifecycle start に対して `origin_terminal_projection` の存在を必須とします。projection 未生成時に使える別の terminal API・wire shape はありません。

したがって、observation 開始失敗を producer 側の呼び方だけで永続 terminal にすることはできません。指定どおり所有外の台帳実装には触れず、ここで停止しました。

## 波及可能性

- production caller は `_complete_origin_runtime` の 1 件です。
- P3 の `_origin_public_inputs` は canonical physical root に lock/WAL を作らないため、FC03 が残ります。
- consumer test の `_materialize_physical_evidence` は必要な物理証拠を既に生成しています。
- lifecycle grammar/API に失敗 terminal 形が追加された後、producer の terminal 呼出しと terminal 存在 assertion を結線する必要があります。
- originless の bytes・受理集合には変更を加えていません。

## 検査

追加編集を行っていないため、テストは実走していません。commit、docs 編集、所有外ファイルの編集も行っていません。

## 総括

前巡の必須 kwarg 3 件の未コミット差分は維持しました。  
台帳には projection 無し origin failure 用の terminal 形がありません。  
producer 側だけでは所見 2 を閉じられません。  
明示された停止条件に従い、追加実装を行わず停止しました。  
実走した検査はありません。  
所見 1、2、3、4 は partial のままです。