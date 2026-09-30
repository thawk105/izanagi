## 所見

- **R1｜must-fix｜`review/scripts/run_judge_v3.sh:54-65`**
  検査器の終了コードを `.rc` に保存した後、スクリプト自体は常に 0 で終了します。`run_ci_then_judge_v3.sh:20-25` はそのスクリプトの終了コードで成否を決めるため、D297 (b) が拒否されても「D297 script rc=0」となり、CI と D297 の両方が成功したように読めます。**推奨:** 結果ファイルと表示を出した後、検査器の `rc` をそのまま返す。

- **R2｜should｜`review/scripts/run_judge_v3.sh:63-65`**
  `printf` の書式は値を 5 個受け取りますが、6 個渡しています。表示上の `seconds` に rc、`report` に秒数、`stderr` に report のパスが入り、余った stderr のパスから余分な行が出ます。放置すると D297 の所要時間と生出力の所在を誤記し、push 依頼に添える結果の読みを妨げます。**推奨:** 重複している `$(cat "...rc")` 引数を削る。

- **R3｜should｜`review/scripts/launch_gate_liveness_v3.py:125-130`**
  `--fix-parent-oid` が F の子であることは確認しますが、裁定で固定された `7e5fa528…` との一致は確認しません。別の F 直後の commit を親に渡しても後続の trace 判定へ進めるため、単独実行時に別系列の新 tip の結果を今回の結果と読めます。**推奨:** `--fix-parent-oid` を `7e5fa528037805dfc0459c742e4a21d6114c9799` と照合する。

## 確認して問題なしとした点

- `review/files/cc/silo/transaction.cc:669,701,731,755` と `7e5fa528` の差は指定された `#line` 4 本の各 +3 だけです。前段の `#line 365/381` は不変で、update の +3 行と整合します。予測 probe でも Silo 単体の TRACE=0 出力は P′ と一致しています。本走の D297 全域一致は未確認です。
- `review/commit-msg.txt:1-11` は変更理由と診断行番号への影響を説明しており、上流の `fix(silo):` 形式に沿います。`#line` 変更は TRACE=1 の論理行番号にも及びますが、本文の「diagnostic line numbers change」はその範囲を含む読みです。
- F/L 計装 patch の差は `review/patches/instr-silo-gate-witness-L.patch:139` の文脈 1 行だけです。新 tip の該当行と一致し、hunk の文脈も整合します。
- `run_judge_v3.sh:25-60` の二つの bundle head、親子、tree、pin の照合と 4 path 指定は裁定に合います。4 path は実際の pin→F の差分 path と一致します。scratch の撤去 trap もあります。
- `run_ci_then_judge_v3.sh:17-23` の CI 引数は `run_ci_build_v2.sh` の契約に合い、CI が失敗しても D297 を実行します。trace の build 別 patch と判定条件も v2 から弱まっていません。
- `mk-line.sh` の 4 行照合と非 force の branch 作成、`mk-synth2.sh` の P‴ 親・tree と二 head bundle、`format-ci.sh` の `7e5fa528` 対照は裁定に沿います。追加の計算や不要な比較は見当たりません。

## 総括

NO-GO。R1 を直すまで、D297 が拒否された場合に結合 job が成功を返します。R2・R3 も本走前に局所修正してください。