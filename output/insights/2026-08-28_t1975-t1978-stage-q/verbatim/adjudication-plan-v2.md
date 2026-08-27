# 段4裁定と plan v2

## 裁定

- C-1「D987は各forward-main区間を比較すべき」: refuted / 不採用。D987の理由は着地保証対象がtested mainから変わった時だけ再検査すること。途中で変更後に最終blobが戻れば着地物のrunner bytesは同じで、再受入は不要。最後のincorporated mainとtested mainのnet blob差を採る。
- C-2「main!=tipのreal waiter/launcher/land proofが必要」: real / 採用 / scope内。単体seamだけでproduction activationを主張しない。
- I-1「D987をreceipt verifier末尾へ置くと先行provenance失敗が恒久拒否をretryableへmaskする」: real / 採用 / scope内。locked forward-main preflight後、provenance前にD987 net差を検査する。
- I-2「最後のforward-mainを選ぶ実装の検出力不足」: real / 採用 / scope内。2段chainで最後だけ変更の拒否と、途中変更後に最終blobへ復元した正例を置く。
- I-3「片側runner欠落/非blobが他層にmaskされる」: real / 採用 / scope内。main/tip片側ずつのfixtureとretryable/release-safe分類を固定する。
- plan補正「Q後に到達するchecker lookup失敗はretryable拒否」: real / 採用 / scope内。旧orderingを保存しない。
- Git modeをrunner identityへ含める案: realな設計択一 / scope外。今回はユーザーがrunner blobへ限定したため実装しない。専用handoffへ残す。

## production plan

1. `tools/acceptance_launcher.py`ではtested main sourceを取得しtested tip blobを独立に読むが、両bytesの等値raiseだけを削除する。tested main sourceを実行し、再読・binding report・receipt main digestを維持する。
2. `tools/dev_wave_land.py`ではtested main/tip runner entryの実在・blob/type・SHA形式を残し、両blob IDの等値項だけを削除する。receipt digestはtested main contentに照合する。
3. forward-main列が非空のときだけ、最後の`incorporated_main_sha`のrunner entryをtested main runner entryと比較するD987 helperを置く。不一致・欠落・非blobはgeneric acceptance rejection、non-retryableとする。Git lookup失敗だけretryableとする。
4. D987 helperは最初のlocked preflight成功後、provenanceをlock外で走らせる前に呼ぶ。provenance成功後の再preflightでも同じhelperを再実行し、TOCTOU後の値を再照合する。
5. schema v5とreceipt fieldは変更しない。`_verify_acceptance_receipt`の引数を増やす必要はない。

## test plan

1. launcher: main!=tipでtested main sourceだけが実行され、read順がmain/tip/main、binding reportとreceipt digestがmainになる正例。
2. launcher: main!=tipでreportがtip digestを名乗る負例、main再読drift負例、片側欠落を維持する。
3. land: main!=tip、receipt main digest、forward-main runner不変の正例。tip digest負例を分離する。
4. land: receipt後のfinal incorporated mainがrunnerを変更したD987負例。provenance rc=16を重ねてもD987が先にnon-retryable/release-safeで拒否する。
5. land: 2段chainで第1main runner不変・第2main runner変更を拒否する。第1main変更・第2mainでtested-main blobへ復元した最終物は受理する。
6. land: main blob/tip tree、main tree/tip blob、main blob/tip欠落を分離し、恒久拒否分類を固定する。
7. real waiter E2E: tip runnerをmainと異なる失敗sourceにし、real waiter/launcherがmainだけを実行してmain digest receiptを作りlandが受理する。
8. existing consumerとmeta-testを静的列挙し、変更test file単独走とconsumer走を親が`tools/run_tests.py`経由で行う。

## 禁止と通る正例

- 禁止: tested main以外のrunner bytesを実行またはreceipt digestの基準にしない。
- 禁止: forward-main最終物のrunner blobがtested mainから変わった古いreceiptを再利用しない。
- 通る正例: tipだけrunnerが変わり、実行・report・receiptはtested main、forward-main最終runnerはtested mainと同じなら受理する。

## scope外

- 段階R、非dispatch receipt、既定shard数3、schema拡張、一般receipt再設計、Git mode identity、waiter/checker/dispatcherのproduction変更。
