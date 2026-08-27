判定は「要修正」です。静的にはD987へ到達する入力を作れますが、検証順序と変異matrixに成果物へ影響する穴があります。

## 主要所見

1. P1: D987をreceipt verifier内へ置くと、provenance失敗が恒久拒否をretryableへ上書きします。

   現行順序は、locked preflight、provenance実行、再preflight、receipt検証です。[dev_wave_land.py:4975](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:4975) [dev_wave_land.py:5035](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:5035)

   planどおりD987を`_verify_acceptance_receipt()`内へ追加すると、forward-mainがrunnerを変更済みでも、先行するprovenance infrastructure failureが`retryable_same_request=True`、`release_safe=False`を返します。その結果、再受入が必要な古いreceiptを保持したまま同一requestを再試行します。D987の「拒否して再受入」という運用結果になりません。

   forward topologyとreplayの成功後、provenanceより前にD987専用preflightを置くべきです。テストも、runner変更入力へprovenance rc 16を重ね、D987の恒久拒否が先行することを固定してください。

2. P1: 「最後のincorporated mainだけを見る」というP1を、予定テストは識別できません。

   topologyはmain履歴の単調前進を保証しており、最終main snapshotを採用する設計自体は静的に成立します。[dev_wave_land.py:2041](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:2041)

   ただし予定されている1段の変更負例と、全段runner不変の既存複数段正例では、`[-1]`を`[0]`や`any(...)`へ変えた実装を区別できません。[test_dev_wave_land.py:6904](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:6904)

   少なくとも次の2段chainが必要です。

   - 第1mainはrunner不変、第2mainが変更: 拒否。`[0]`比較の誤実装を殺す。
   - 第1mainがrunner変更、第2mainがtested-mainと同じblobへ復元: 受理。全段比較の過剰拒否を殺す。

   前者を欠くと最終runner変更を見逃し、後者を欠くと不要な再受入を発生させます。

3. P1: P2の片側欠落、非blob維持は、既存landテストでは片側ごとに証明されません。

   現在の非blobテストはmainとtipの両方を同じtreeにしています。[test_dev_wave_land.py:1858](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:1858) 片側のtype guardを消しても他方が拒否します。両guardを外しても、後段の`cat-file blob`失敗がretryable拒否としてmaskし、現在のrcとreasonだけのassertでは検出できません。

   次を分離してください。

   - main blob、tip tree
   - main tree、tip blob。後段maskを区別するため`release_safe=True`、`retryable_same_request=False`もassert
   - main blob、tip欠落

   main欠落、tip blobは既存テストがあります。[test_dev_wave_land.py:1690](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:1690)

## D987到達性と既存正例

通常のprovenance成功時には、現在の[test_dev_wave_land.py:1568](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:1568)を反転する負例はD987へ到達します。

- receiptのtested-main runnerはA。
- tested tipもAなので旧main-tip gate以外のrunner条件を通る。
- receipt作成後、mainだけがrunner Cへ進む。
- clean forward merge、topology、replay、locked-main検査を通る。
- incorporated mainだけがAと異なるため、D987が単独の拒否理由になる。

一方、[test_dev_wave_land.py:1523](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:1523)を「tip runner B、main側は非runner変更」に直す正例は、旧等値拒否とD987の誤比較を同時に識別できます。既存のforward-chain正例より強い正例です。

ただし1568側の現在のlookup assertは`[tip, tested_main]`です。verifier内実装を採るなら`incorporated_main`を加え、テスト名も成功名からD987拒否名へ変更する必要があります。planにこのassert改訂が明記されていない点はnitです。

## Consumerとfixture波及

射影内での`_verify_acceptance_receipt()` consumerは、[dev_wave_land.py:5035](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:5035)のproduction call 1個だけです。直接呼ぶテストconsumerはありません。`land()`経由の間接consumerだけです。

fixture既定をtested tipからtested mainへ変える方針は正しいです。[test_dev_wave_land.py:354](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:354) 同時にbaseline helperもtested mainへ直す必要があります。[test_dev_wave_land.py:680](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:680)

全`tools/run_tests.py`参照を静的に追った範囲では、暗黙の既定変更で意味が変わる既存ケースは主に1646のchecker lookup順序テストです。tip digestを意図する1622、欠落系、1824は明示overrideを残せば波及を隔離できます。

分類は次のとおりです。

- D987不一致、active foldなし: non-retryable、release-safe。
- incorporated runner lookupのGit失敗: retryable、release-safeではない。
- active fold中の恒久receipt拒否: release-safeではない。
- ただし現planの順序では、先行provenance失敗がこれらをmaskします。

## Exact 2述語の証拠上限

`dev_wave_land.py`では、撤去対象のmain-tip runner同値述語は[dev_wave_land.py:1084](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1084)の1個だけです。receiptとtested-main digestの照合、両側の実在、blob型、checker同値は同義拒否ではありません。

launcher側production sourceは今回の必読射影に含まれていないため、このconsult単独では「全productionでexact 2個、同義拒否なし」を静的に確定できません。新しいlauncher正例は残存する同義拒否を実走時に検出できますが、今回は未実走です。親のexact-2実測値を、このconsultで独立確認済みとは報告できません。

## 専用裁定候補

scope外の別裁定候補として、runner identityへGit modeを含めるかを分離すべきです。

`_runner_tree_entry()`はmodeを捨て、`(object_type, object_id)`だけを返します。[dev_wave_land.py:824](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:824) 同じblob IDのまま`100644`から`120000`へ変えるとD987を通過しますが、着地後のpathname実行はregular fileからsymlinkへ変わり得ます。

これは既存parser契約と一般runner設計へ広がるためQへ混ぜません。ただし「runner変更」を実行bytesだけと定義するか、pathname種別も含めるかは専用裁定が必要です。

テスト、build、checkerはread-only指示に従い実行しておらず、緑とは判定していません。

## 総括

D987の基本入力は到達可能で、fixture既定変更も局所的です。ただしplan v1のままでは、provenanceがD987の恒久分類をmaskし、最後のincorporated mainという選択と片側非blob条件が変異matrixで固定されません。実装前に、D987のpreflight順序、2段forward-mainの両方向テスト、片側ごとの欠落、非blobテストをplanへ追加すべきです。