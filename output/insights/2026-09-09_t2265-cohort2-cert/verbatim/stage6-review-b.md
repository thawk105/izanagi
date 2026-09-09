## Must-fix

1. `[must-fix]` binding performance job は全件 build 前に停止する。

   `submit-perf.sh` は `CELLS="$P1+$P2"` だけを渡すが、performance 経路の `_validate_grid_contract` は `none:0:100:1000:10` と stock control を各 1 件要求する。条件 `len(disabled) != 1` が必ず成立し、12 job とも成果物を書かない。その後 `submit-cert.sh` も performance artifact 欠落で qsub 前に停止する。

   成果物影響: binding performance 成果物は 0 件、したがって certified 選択・group receipt・レポート参照も 0 件。

   根拠: `submit-perf.sh:10-12,27-51`、`t2187_adaptive_const_probe.py:687-696,3844-3869`、`submit-cert.sh:59-64`。

   最小修正: performance job ごとに `none` と stock control を含む有効な grid にする。R1 の裁定どおり、p1 専用 1 job と p2 seed 別 12 job に分ける。現状は p1 を各 p2 artifact に重複収録する 12 job で、裁定の 13 job とも不一致である。`ruling.md:22-23`。

2. `[must-fix]` 赤 2 件目の直接根因は、新設された `build_cache_key` singleton 条件である。

   public integration test は 24 request ごとに別 `TMPDIR` と `PBS_JOBID` を使い、producer は毎回新しい build context/admission から cache key を再計算する。一方 fake binary SHA は常に同じなので、追加された二条件のうち失敗するのは `len({row["build_cache_key"] ...}) != 1` である。これが `group-build-identity-mismatch` を発生させる。

   成果物影響: 24 result がすべて `certified` でも group receipt が生成されず、その group はレポートや台帳から certified として参照できない。

   根拠: `unitA.patch:1350-1351`、`test_t2187_adaptive_const_probe.py:222-247,1353-1359`、`t2187_adaptive_const_probe.py:3583-3607,3640,2743-2746,2810-2813`。

   最小修正: test fixture だけを固定して済ませず、24 独立 job でも同じ cell・seed・source・compiler・trace 設定から group-stable な `build_cache_key` が得られるよう producer 側を直す。job-local admission identity を除外できない設計なら、R6 の singleton 要求との両立不能として裁定へ戻す。

3. `[must-fix]` group 検証失敗が完全に握り潰される。

   全 24 path が存在した後でも `_group_receipt_payload` の全 `CertificationReject` を捕捉して `False` に変換する。その後、現在の request 自体が certified なら `_certify_main` は終了コード 0 を返す。今回の赤が `FileNotFoundError` だけになった理由でもある。

   成果物影響: group receipt 欠落が scheduler 上の成功として残り、レポートと台帳は失敗理由を取得できない。

   根拠: `t2187_adaptive_const_probe.py:3108-3121,3163-3175,3824-3841`。

   最小修正: `False` は「まだ path が欠けている」場合だけに限定し、24 path 存在後の検証失敗は reason/detail を保持して非 0 終了させる。

4. `[must-fix]` 既存 result を状態不問で skip するため、同じ attempt は永久に回復しない。

   `rejected`、破損途中、または `certified` だが group receipt 欠落のいずれでも、`-f "$target"` だけで skip する。24 certified 後に最後の process が finalize 前に停止した場合も、再実行では finalize を呼ぶ job が 1 件もない。skip や判断は ledger にも書かれない。

   成果物影響: rejected attempt または receipt 欠落 attempt が固定され、group の受理集合は空のまま、台帳にも失敗判断が残らない。

   根拠: `submit-cert.sh:111-115,140-142`、`ruling.md:107-116`。

   最小修正: 投入前に既存 24 result を分類する。欠落だけなら同 attempt の欠落 slot のみ許可、rejected・破損なら新 attempt で 24 件全部を要求、24 certified かつ receipt 欠落なら非 0 で停止して台帳へ理由を記録する。

5. `[must-fix]` pilot の引数契約が表示と実装で一致せず、0 job を成功終了できる。

   usage は `[slot ...]` と書くが、実装が受理するのは `write-heavy:0` のような `workload:slot` だけである。例えば表示どおり `0` を渡すと全 24 ループで不一致となり、qsub も ledger 行もないまま終了コード 0 になる。

   成果物影響: R15 pilot の成果物が 0 件でも投入成功に見え、波 1・2 の開始判定を誤る。

   根拠: `submit-cert.sh:3-6,88,101-110`、`ruling.md:174-181`。

   最小修正: usage を正確化し、各指定値を 24 個の閉表へ照合し、投入件数 0 をエラーにする。

6. `[must-fix]` stale performance artifact を自動的に再利用する。

   固定 directory に JSON が 1 件でもあれば、repo head や identity を検証せず performance 再作成を skip する。certify はその JSON を選択し、`document["repo_head"] != expected_repo_head` で build 前に拒否する。複数 JSON の場合も cert script は停止する。

   成果物影響: group の `performance_artifact` 参照が現行 commit に束縛できず、対応する認証結果は 0 件になる。

   根拠: `submit-perf.sh:33-37`、`submit-cert.sh:59-69`、`t2187_adaptive_const_probe.py:2221-2243`、`ruling.md:12-26`。

   最小修正: output directory を submit-tree の repo head で分離するか、skip 前に現行 identity を検証する。既存 artifact は上書きせず保存する。

7. `[must-fix]` fresh claim と legacy claim を同一視する consumer が残っている。

   fresh tuned receipt は `_certification_claim` の build 条件付き literal を出す一方、`ALLOWED_GROUP_CLAIM` は既発行 receipt 用の旧 literal のままである。赤 1 件目の test は旧定数との一致を要求している。

   成果物影響: fresh receipt の `claim` 参照が旧 literal 固定の consumer から拒否され、certified group の受理集合が欠落する。

   根拠: `t2187_adaptive_const_probe.py:145-150,416-480,2859-2867`、`test_t2187_adaptive_const_probe.py:1081-1094`。

   最小修正: legacy 定数は既発行 receipt 再検証用に維持し、fresh receipt の test/consumer は axes から生成した claim を参照する。

## nit

1. `[nit]` seed の値閉表は一致するが、入力 literal 閉表は一致しない。

   Python は `014481721328008317845` を整数化して許可 seed として受理するが、PBS の `case` は先頭ゼロ付き literal を拒否する。

   成果物影響:記録される seed 値は変わらないが、Python 直接起動と PBS 起動の受理入力集合が異なる。

   根拠: `t2187_adaptive_const_probe.py:756-762,1587-1598`、`t2187_adaptive_const_probe.pbs:28-36,145-147,203-210`。

2. `[nit]` queue 上限が 1 件ずれる。

   live job がちょうど 48 件でも `-le 48` で qsub へ進み、49 件目を投入する。

   成果物影響:成果物値は不変だが、同時滞留集合が裁定の 48 件を 1 件超える。

   根拠: `submit-cert.sh:89-98,116`、`ruling.md:118-125`。

3. `[nit]` 既定時間予算は正しいが、`WALLTIME` override は Python 側へ伝播しない。

   既定は `540+900+180+120+5400+300=7440 < 8100` で 660 秒残り、`02:15:00` と一致する。ただし `WALLTIME` を短くすると scheduler は先に殺す一方、driver は 8100 秒のまま判定する。

   成果物影響:既定値では不変。短い override 時だけ result JSON が生成されない可能性がある。

   根拠: `submit-cert.sh:17,135`、`t2187_adaptive_const_probe.pbs:90-94`、`t2187_adaptive_const_probe.py:1669-1682`。

## 確認できた整合

- Python/PBS の canonical seed 13 値と cell 別 thread 閉表は一致する。thread は tuned/cw-as-dyn が 48、p1/p2 が 24 または 48。
- p2 seed は `submit-cert.sh:132-134` → PBS `:102,203-210,448-450,477-480` → Python `:1587-1609,3431,3553-3557,3570` と届く。forward を落とすと Python が build 前に missing reject するため、「既定 seed で build して receipt だけ seed X」は通常経路では起こらない。
- `ATTEMPT_ID`、24 result path、PBS の output 名、dynamic certify/perf namespace は一致する。`submit-cert.sh:51-85,117-139`、`t2187_adaptive_const_probe.pbs:232-264,477-504`。
- performance artifact が生成できたと仮定すれば、cell、extime=6、24/48 row、p2 seed、p1 の既定 genome、repo head は `_performance_artifact_identity` を通る。現状はその前の performance grid gate で停止する。
- 24 threads や seed 別 build は job 数を増やすだけで、既定の per-job 内側予算 7440 秒は変わらない。

## Consumer 検査の限界

指定された差分内では `_certification_contract` の production caller と当該 test caller は新しい `(CertificationAxes, workload)` に更新され、削除された `CERT_THREADS` / `CERT_STEP_POLICY_SEED_BY_CELL` の参照も残っていない。

ただし、指定された `test_plot_dynamic_backoff.py` など 4 consumer は必読事項の射影に含まれておらず、「指定絶対パスだけを読む」という条件のため現物確認できない。`unitA.patch` にもそれらの変更はないため、DW-O26 はこの review では未決着である。根拠: `unitA.patch:1,775,886`、`stage5-author.md:70-76`。

## 総括

- 最初の実機停止点は `submit-perf.sh` の無効な performance grid で、binding artifact は 1 件も生成されない。
- 赤 2 件目の根因は job 別 `build_cache_key` を singleton 必須にした条件で、失敗は finalize 内で握り潰される。
- must-fix は 7 件。
- `submit-perf.sh` は有効 grid、13 job 構成、repo-head 別保存へ修正が必要。
- `submit-cert.sh` は既存 result の状態分類、pilot 引数検証、receipt 欠落の非 0 報告が必要。