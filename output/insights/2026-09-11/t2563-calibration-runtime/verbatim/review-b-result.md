## 総括

**比較用候補は GO。差分に対する must-fix はなし。最終採用・land は NO-GO（after 未取得、既知の時間式不整合が未解決）。** 静的レビューのみで、テスト緑・変異 kill は未確認です。

- **refuted：テスト側が production の wait 欠落を隠す。**
  `test_pegasus_calibration_workload.py:1382–1386` は production から呼ばれた際に `builtin wait` を実行し、その結果を記録します。wait を削除すると `:1423` の「3回」検査で落ちます。`subprocess.run` が子の pipe 閉鎖を待っても、wait イベントは補完されません。成功時には全 done/wait が verifier より前であることも `:1433` で検査します。

- **refuted：copy 失敗を無視してもテストが通る。**
  `:1403–1409` は実際の欠損 source に対する `cp` の失敗を返します。各依存について非0終了・verifier 不実行・後続出力なしを `:1428–1439` で検査します。production の `certify_calibration.sh:614–628` も、全PIDを回収してから失敗終了する構造です。

- **real：テストの証明範囲は限定される。ただし比較の blocker ではない。**
  `test_pegasus_calibration_workload.py:1395–1407` の rendezvous は3つのラッパーが並行起動されることを保証しますが、実 `cp` の実行区間の重なりや短縮量までは保証しません。また抽出範囲は `:797–803` で build 前までです。後続不実行は fragment の終了と、production で verifier 後に build が続く構造を合わせて判断できます。

- **refuted：今回の候補が確定予算や consumer を変更している。**
  各copyの120秒上限は `certify_calibration.sh:605`、既存予約式は `:811–815` に維持されています。`test_pegasus_tools.py:200–214` は凍結式を検査し、`orchestrator/calibrator/cli.py:727–732` は CLI予算4990秒＋wrapper reserve600秒の包含条件を引き続き要求します。今回の差分はこれらを迂回していません。

**最終採用前の必須事項：** 親による関連テストとM1/M2の実走確認、固定候補commitでのafter 1回、同条件・同処理回数の確認、時間式と既存consumerの整合解決。

実時間比較は、親報告の baseline991694 の **scheduler Elapse 186秒同士を主比較**とし、開始→結果182秒は同じ区間同士で補助比較してください。after 未取得の現時点では短縮効果は未判定です。効果が示せなければ候補を残さず、短縮しても実測値で予約契約を置き換えない、という裁定に適合します。
