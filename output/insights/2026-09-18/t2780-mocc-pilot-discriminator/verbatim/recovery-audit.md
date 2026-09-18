固定 HEAD `f93281e55c59e8a69fda2fc4295986929e123e2a` を `c8e8dc06f` と比較しました。差分は pilot と既存テスト2本、497追加・12削除です。**本題の配線・受理条件・receipt 束縛に must-fix は見つかりませんでした。**

ファイル変更、pytest、build、変異実行、大きい trace の読取りは行っていません。

## must-fix

**0件。**

- **HYDRATE_PY:** 候補を絶対パスへ解決し、Python ≥3.10 と driver import を probe。その選択結果を実際の `timeout 20 "$HYDRATE_PY" … hydrate` に渡しています。全候補拒否時は `third_party` で停止します。probe の2つの import root は fetch 側の driver 読込みと整合します。
- **build 前 X/P patch:** T1943 限定で numstat・touch set・check・apply・patch再hash・source hash の順に実行し、その後に両 build が同じ `BUILD_SOURCE` を使用します。general では適用しません。
- **verifier source:** T1943 だけ patched `BUILD_SOURCE` を渡します。verifier は指定 root の CMake と実 source 本文を読むため、変更は X/P evidence の入力へ届きます。general の引数値は従来どおりです。
- **receipt:** writer が patch/source の実 bytes と sidecar を再照合し、job-result writer が v2 の必須5 field・型・値を検査します。旧 T1943 v1、general v3、binding 欠落の拒否は維持されています。
- **判定:** verifier rc∉{0,1} の停止は維持され、rc=3 を通す変更はありません。rc=1 の診断成果物を finalization できることと、異常 variant を certified にすることは別であり、今回の差分に後者の変更はありません。

主な根拠は [pilot](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2780-mocc-pilot-discriminator/tools/pegasus/mocc_trace_pilot.sh:1564) の1564–1591、1742–1868、2348–2416、3113–3268、3512–3539行です。

## should

**S1 — 正式変異の完了実績は、再実行結果が揃うまで未確定とする。**

親の再整理は妥当です。M8 は job-result writer の binding 欠落拒否によって、[テストの正常終了 assertion](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2780-mocc-pilot-discriminator/orchestrator/tests/test_mocc_trace_job_contract.py:4838) が先に失敗する構造です。後段の field assertion が殺したとは言えません。M2 は条件文字列、M3 は診断記録の検出なので、correctness kill と分離する裁定を支持します。

具体的な影響は**検証結果の帰属と集計**です。本番 gate の追加・削除は不要です。旧 local probe を正式 harness の成功として扱わない方針を維持してください。

**S2 — 焦点走の実行場所を記録時に訂正する。**

[focus-1.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2780-mocc-pilot-discriminator/focus-1.log:2) は local のメモリ上限到達後、`5893.nqsv` に dispatch し、`1591 passed, 3 skipped` で終了しています。「login 実走完了」「受入全走」とする記述は不正確です。receipt の値や受理集合への影響はありません。

## nit

**N1 — 新 marker の一意性検査の重複は残っています。**

専用契約テストに加え、既存2つの marker tuple にも登録されています。保守上の重複であり、成果物・受理集合への影響はありません。今回の GO を妨げません。

## job5905 の独立照合

[accounting](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2780-mocc-pilot-discriminator/attempts/submissions/780695e588d9487f74a3c7610a298270/pbs-job.stderr) には request `5905.nqsv`、終了時刻 **2026-09-18 16:09:44**、Elapse **127S** が記録されています。単なる stderr の存在とは区別できる終端証拠です。

[実 receipt](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2780-compute/output/env/pegasus/mocc-trace/job-staging/0:5905.nqsv/mocc-trace-pilot-receipt.json) から、回収判定の真偽値に依存せず次を再照合しました。

| 対象 | 結果 |
|---|---|
| receipt → sidecar → job-result | SHA-256一致。receipt は T1943 v2、`completed` |
| 投入スクリプト | job-result の digest と固定 HEAD の pilot bytes が一致 |
| patch | 固定 HEAD の patch、receipt、sidecar が一致（`e9e65b78…`） |
| patched source | receipt と sidecar が一致（`bd0add59…`）。実 source bytes の再hashは今回未実施 |
| numstat | `65 / 0 / cc/mocc/transaction.cc` の1行 |
| configure argv | TRACE=0/1 とも `/scr/0_5905.nqsv/ccbench-source` |
| discriminator・両 manifest・TRACE0 absence・identity report・verifier | 対応する receipt digest と一致 |
| gate と結論 | workload/verifier/discriminator/identity は全て rc=0、`no-g2` |
| 成果物状態 | `failure.json` 不在、5 artifact の分類が契約どおり |
| 認証の扱い | `official_certification=false`、discriminator の `serializable_elevation_allowed=false` |

qstat の独立再照会は `EACCTAUTH: Unknown user-id` で失敗しました。**qstat 不在は親の実測報告として扱い、今回独立確認したとはしません。** 終了時刻入り accounting は直接確認できています。

## 旧所見・親裁定との対応

ここでの closed は今回の対象についての解消を意味します。

| 旧所見／親裁定 | 状態 | 根拠・残る範囲 |
|---|---|---|
| B-MF1：終端未確認 | **closed（job5905）** | 終了時刻入り accounting と完了成果物を直接確認。qstat 不在の再確認には上記制限あり |
| B-S1：staging 名の実測不足 | **closed（job5905）** | `0:5905.nqsv` の実ディレクトリと job-result 内 jobid が一致 |
| A-S1 / B-S3：M8 の検出帰属 | **partial** | job-result writer を実効 gate とする裁定は正確。正式 harness の再実行実績は未確認 |
| M2/M3・旧 local probe の扱い | **partial** | sensitivity の分離・正式結果への非流用は妥当。再実行は予定段階 |
| A-N1：hydrate 実呼出の環境被覆 | **closed（保証限定）** | interpreter・argv・cwd の被覆。実呼出の PYTHONPATH 観測済みとは主張しない |
| A-N2 / B-S2：焦点走の場所 | **partial** | 一次ログで compute dispatch を確認。最終記録への訂正反映は本監査外 |
| B-N1：marker 重複 | **partial** | 残存。nit のみ |
| B-N2：準備 done の意味 | **closed（今回の投入）** | done に頼らず、実成果物の固定 HEAD・script digest・configure argv を確認 |

**regressed と判断する所見はありません。**

## 保証範囲

今回確認したのは、固定差分の静的整合と、job5905 の小さい既存証拠の整合です。general-v4 正例と旧schema拒否の fixture は維持されていますが、今回は実行していません。

`trace0_built_from_patched_source=true` は build 配線に基づく記録であり、コンパイラが読んだ bytes の独立証明ではありません。また、manifest 自体の digest 一致は確認しましたが、大きい trace/witness leaf の再hashや verifier の再計算は行っていません。rc=1 の compute 実走、正式変異、受入全走の完了も保証に含めません。

## 総括

**GO — must-fix 0件。**

固定 HEAD の実装取り込みを支持します。job5905 は現行契約の `no-g2 / rc0` 正例として finalization 到達を裏付けます。B-MF1 を今回の job について閉じる裁定は妥当です。正式 harness・受入全走の完了認定は、この GO には含めません。