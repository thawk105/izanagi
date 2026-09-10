## 総括

静的レビューでは、変更前に拒否され変更後に受理される経路は見つからなかった。  
must-fix は A-01: A-2 consumer に裁定で削除された `commits > 0` と `batch_commit_counts == 0` が残存する。  
S8B の helper 起動抑制は最終 verdict を受理へ変えず、backoff の旧独自判定削除も helper が補完する。  
二度読み SHA 比較には ABA 窓が残るが、有効な lock 束縛 receipt なしの受理経路は見つからなかった。  
A-01 を直すまで land 非推奨。pytest は実走せず、提示された親の結果を前提とした。

## 所見

- A-01 / real / scope 内 / `orchestrator/campaign/paper_story_a2_certification.py:1939-1945,2417-2426,2692-2699`
  
  A-2 は helper 通過後も `_classify_verify_repetition()` で `commit_counts > 0` と `batch_commit_counts == 0` を要求する。これは裁定で削除された述語の consumer 側再実装である。
  
  成果物影響: 将来、正当な batch commit を含む receipt が helper を通っても A-2 が `observed-positive` を出せず、承認以上に受理集合を狭める。

- A-02 / real / scope 内 / `orchestrator/campaign/backoff_repro.py:84-103`, `s1_report.py:438-475`, `s6_sort_sweep.py:402-431`, `s8a_trigger_sweep.py:501-530`, `s8b_oracle_report.py:573-575,1788-1807`, `paper_story_a2_certification.py:2604-2623`, `backoff_requested_us.py:575-589`
  
  7 site はすべて lock A、WAL、lock A の二度読みを実行する。ただし A→B→A の ABA、二度目の読取後の差替え、WAL 自体の読取後差替えは検出しない。
  
  成果物影響: 出力が参照する捕捉済み bytes と処理終了時の disk bytes が異なる余地は残る。ただし helper は receipt の lock SHA を A に束縛するため、無効 receipt を受理へ変える具体的経路は確認できなかった。

- A-03 / refuted / scope 内 / `orchestrator/campaign/s8b_oracle_report.py:1630-1650,1668-1670,2036-2043,2076-2111`; `orchestrator/campaign/s8b_oracle_judge.py:480-508`
  
  「別 issue を追加して helper を回避する」ことは可能だが、その窓は既に `protocol_violation` となり `bench_values` も空になる。`certified_eligible=False` の行が report 上 `completed` でも judge が必ず top-level rejection を追加する。
  
  成果物影響: 診断名は変えられても certified verdict を受理へ昇格できない。

- A-04 / refuted / scope 内 / `orchestrator/campaign/backoff_requested_us.py:470-494,575-604`; `orchestrator/verifier/commit_receipt.py:188-255`
  
  削除された backoff 独自判定は、全 COMMIT への helper、attempt topology、receipt validator に置換されている。旧 `certified is True`、operation、variant、receipt ID はすべて同等以上に拒否される。
  
  成果物影響: 弱い旧判定の削除による reference artifact の認証抜けはない。

- A-05 / refuted / scope 内 / `orchestrator/campaign/artifact_admission.py:652-735,1261-1269`
  
  helper は採用 7 述語を実装している。`anomalies` は exact int zero、attempt と variant は COMMIT 前 verify に束縛され、receipt は lock、variant、terminal payload、operation、順序付き evidence に束縛される。
  
  成果物影響: receipt または WAL verify の片側だけを改変した COMMIT は certified view を得られない。

- A-06 / refuted / scope 内 / `orchestrator/campaign/s1_report.py:346-360,961-967`; `s8b_oracle_report.py:1641-1650,1668-1670`; `paper_story_a2_certification.py:2691-2699,4154-4161`
  
  例外は S1 では certified hard gate fail、S8B では `protocol_violation`、A-2 では `CertificationError` と rc=2 になる。backoff、S6、S8A は上位へ伝播する。
  
  成果物影響: 診断化される consumer でも認証済み成果物としては採用されない。

- A-07 / refuted / scope 内 / `orchestrator/campaign/artifact_admission.py:1151-1205,1261-1269`; `orchestrator/campaign/pipeline.py:1246-1306`
  
  live anomaly gate、epoch gate、環境契約、source binding は変更されていない。中央 helper は epoch gate 後、view 発行前に全 COMMITへ適用される。
  
  成果物影響: 絶対規律 2 の live reject または既存 source/environment binding の弱化はない。

## 受理集合が広がる経路

該当なし。

特に S8B の三つの絞込みは次の理由で受理集合を広げない。

- `certified_eligible=False`: judge が必ず拒否理由を追加する。
- attempt 不明または COMMIT 非一意: 既存 issue により `protocol_violation`。
- 既存 global/lifecycle/row issue: 最終行が `protocol_violation` となり性能値も消去される。

一方 A-01 は逆方向、つまり承認外の過剰拒否である。

## 恒真の疑いがある検査

- `orchestrator/campaign/artifact_admission.py:676-679` の verify 1 件以上は、receipt validator が evidence 非空を要求し、最後に evidence 列を完全一致させるため論理的には含意される。削除して新たに受理される入力は示せない。
- `artifact_admission.py:697-706` の workload tag 非空 exact str も receipt evidence の非空 str 契約と完全一致に含意される。削除だけで受理される入力は示せない。
- `artifact_admission.py:684-691` の verdict/certified は意味論上は evidence 完全一致に含意される。ただし現在の `wal_evidence` が定数 `"serializable", True` を格納するため、行だけ削除すると不正 WAL が通る。現実装では機械的に除去可能な恒真検査ではない。
- S8B の `certified_eligible`、COMMIT 一意性、既存 issue 条件は診断重複を避ける call guard であり、独立した admission gate として数えるべきではない。

## 変異 M1-M13 の実効性

| 変異 | 静的判定 | 最初に殺す層 |
|---|---|---|
| M1 | effective | helper の exact `anomalies == 0` |
| M2 | effective | receipt terminal payload hash |
| M3 | effective | helper の operation/attempt 一致 |
| M4 | effective | helper の順序付き evidence 完全一致 |
| M5 | effective | topology-valid な A abort/B commit 後、helper の attempt 選択 |
| M6 | effective | topology は commit 後 retry を許し、中央の全 COMMIT loop が 2 件目を拒否 |
| M7 | effective | S1 の helper。既存 verify_configs gate は anomaly を見ない |
| M8 | effective | A-2 helper。後段 `_classify_verify_repetition` は certified anomaly を単独では拒否しない |
| M9 | effective | S6 resume helper |
| M10 | effective | 現行全体は後続 red attempt を許容し、campaign 全 verify 正常化なら失敗する |
| M11 | effective、命名 nit | no-COMMIT campaign は現行で通る。実際の変異点は helper 本体ではなく caller/chokepoint になる |
| M12 | effective | `HISTORICAL_RAW` は破損 receipt を検査しない |
| M13 | effective | verify の `aborts=17` は現行 helper、topology、receipt のいずれも拒否しない |

M10-M13 は過剰拒否を殺す正例として機能する。ただし A-01 の batch witness 過剰拒否はこの集合で覆われていない。

## must-fix と nit の切り分け

must-fix:

- A-01: A-2 の `_classify_verify_repetition()` から `commit_counts > 0` と `batch_commit_counts == 0` を certified admission 条件として使う処理を外し、正当な batch/non-witness shape の正例を追加する。

nit:

- 二度読み SHA 契約が ABA や終了時 disk identity まで保証しないことを明記する。
- M11 の変異名を「certified chokepoint が campaign に COMMIT を必須化」へ直す。
- 恒真な verify 非空/workload tag 検査は、独立 gate や変異 kill として数えない。