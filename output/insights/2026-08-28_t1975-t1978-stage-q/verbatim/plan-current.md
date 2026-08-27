# plan v1

静的再検証の結論は、段階QとD987を同一変更で実装可能です。critical anchorに意味上のdriftはありません。ただしaccepted planには1点修正があります。runner差分を有効なtested-main digestで通した後のchecker lookup失敗は、旧orderingを温存せず、到達可能になったretryable拒否としてテストすべきです。

テストは実走していません。以下の行番号は、提示されたmain `f34e19be9` の射影ファイルに対するものです。

## 1. productionの削除対象

briefがproduction変更対象と定める2ファイルを再検索した結果、tested mainとtested tipのrunnerを直接等値比較するproduction述語はexact 2個です。

| 対象 | 現行アンカー | 変更 |
|---|---|---|
| launcher bytes等値 | [acceptance_launcher.py:566](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:566) | 567行のtip読取は残し、568-569行の`source != tip_source`拒否だけ削除 |
| land blob ID等値 | [dev_wave_land.py:1065](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1065) | 1084行の`main_runner_entry[1] != tip_runner_entry[1]`だけ削除 |

3個目はありません。次は削除対象ではありません。

- [dev_wave_land.py:1067](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1067) の両runner実在検査。
- [dev_wave_land.py:1080](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1080) の両runner blob型検査。
- [dev_wave_land.py:1085](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1085) のreceipt digestとtested main内容の等値。
- [dev_wave_land.py:1124](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1124) のchecker main-tip等値。
- [acceptance_launcher.py:602](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:602) の実行bytesと実行後tested main再読の等値。

## 2. 維持する束縛

Launcherでは次をそのまま残します。

- `_read_runner_blob()`は`git cat-file blob`を使うため、tested mainとtested tipの欠落、tree化、読取失敗を拒否する: [acceptance_launcher.py:208](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:208)
- 実行元はtested mainの`source`: [acceptance_launcher.py:566](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:566)、[同:584](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:584)
- digestもtested mainの`source`から計算: [同:570](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:570)
- 実行後にtested mainを独立再読し、実行bytesと再照合するM3: [同:597](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:597)
- 全shardについてexact K、index集合、nonce、tested main、runner digestを検査: [同:341](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:341)、[同:616](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:616)
- receiptの`runner_executed_sha256`も同じtested main digest: [同:477](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:477)、[同:629](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:629)
- shard数の明示注入`1/2/3`要求: [同:136](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:136)

Landでは次を維持します。

- launcher自身を選択revisionのblob IDと内容digestへ束縛: [dev_wave_land.py:1021](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1021)
- waiterをtested tipのblob IDと実行内容digestへ束縛: [同:1054](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1054)、[同:1115](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1115)
- runner双方の実在、blob型、SHA形式とreceiptのtested-main digest照合: [同:1065](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1065)
- `non-attributable-only`のchecker main-tip blob等値とreceipt束縛: [同:1093](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1093)
- schema v5とcanonical field集合: [同:94](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:94)、[acceptance_launcher.py:21](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/acceptance_launcher.py:21)

## 3. D987の最小実装

変更する呼出し規約は`_verify_acceptance_receipt()`だけです。

1. [dev_wave_land.py:908](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:908) のkeyword-only引数へ追加する。

```python
forward_main_merges: Sequence[_ForwardMainMerge],
```

2. 唯一のproduction consumerである[同:5035](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:5035)で追加する。

```python
forward_main_merges=preflight.forward_main_merges,
```

直接呼び出すテストconsumerはありません。テストはすべて`land()`経由です。

渡す値は、lock内で再計算されprelocked列とのexact一致を検査済みです: [同:2716](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:2716)、[同:2722](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:2722)、[同:2788](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:2788)。

3. 既存runner gateの直後、checker lookupの前へ追加する。

```python
if forward_main_merges:
    incorporated_runner_entry = _runner_tree_entry(
        repository,
        forward_main_merges[-1].incorporated_main_sha,
    )
    if incorporated_runner_entry != main_runner_entry:
        raise _acceptance_rejected()
```

比較対象は次の2つです。

- receiptの`tested_main`にある`(object_type, object_id)`
- 最後のforward-main mergeが取り込んだmain commitにある同じentry

tested tip、landing tip、locked mainとの比較にはしません。forward-main列はmain履歴の単調前進を既に検査しているため、最終incorporated mainがlandingへ持ち込むrunner bytesの判定には最後のentryで十分です: [同:2041](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:2041)。

この比較では欠落、非blob、別blobを変更として拒否します。一度変更後に最終mainで元のexact blobへ戻った場合は受理します。modeだけの差は`_runner_tree_entry()`の戻り値に含まれず、stdin実行するbytesを変えないため拒否しません。

schema、receipt field、producer出力には変更を加えません。

## 4. 到達可能な正負例と分類

| ケース | 期待結果 |
|---|---|
| launcherでmain bytesとtip bytesが異なり、実行、再読、binding reportがmain digest | receipt作成まで成功 |
| launcherでbinding reportがtip digest | `runner binding report digest mismatch`、receipt未作成 |
| landでmainとtipのrunnerが異なり、receiptはmain digest、forward-mainのrunnerはmainと同一 | `RC_OK` |
| landでreceiptがtip digest | `RC_AUDIT`、generic拒否、non-retryable |
| receipt作成後のforward-mainがrunnerを変更 | `RC_AUDIT`、`acceptance-receipt-rejected`、non-retryable |
| incorporated-main runnerの`ls-tree`自体が失敗 | `RC_AUDIT`、retryable |
| 有効なmain digestのrunner差分後にchecker lookupが失敗 | checkerまで到達し、retryable |

通常のactive foldなし経路では、non-retryableなtip digest拒否とD987拒否は`release_safe=True`になります。lookup失敗は`retryable_same_request=True`かつ`release_safe=False`です。[dev_wave_land.py:5034](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:5034)、[同:5527](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:5527)

active fold中は同じnon-retryable拒否でも自動的にはrelease safeになりません。Launcherにはこの2分類はなく、失敗時は`LauncherFailure`からrc 70になります。

## 5. テスト改訂

### Launcher

[orchestrator/tests/test_acceptance_launcher.py:175](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_acceptance_launcher.py:175)

- mainとtipを実際に異なるbytesへ変更する。
- 読取順が`main, tip, main`であることを維持する。
- 実行buffer、outcome digest、receipt digestがmain由来でtip由来でないことをassertする。
- test名を`test_different_main_and_tip_runner_blobs_execute_tested_main_source`へ変更する。

[同:222](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_acceptance_launcher.py:222)

- 旧事前拒否テストを、tip digestをbinding reportへ申告する負例へ変更する。
- main runnerが一度実行されること、binding digest mismatchになること、completionを読まずreceiptが空のままであることを固定する。

[同:313](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_acceptance_launcher.py:313)

- M3を`main`, `異なるtip`, `driftしたmain再読`の3 bytesにし、tip差分ではなくmain再読差分で拒否することを固定する。

### Land fixture

[orchestrator/tests/test_dev_wave_land.py:354](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:354)

```python
runner_digest_revision or tested_main
```

へ変更します。これは実producerのtested-main digest規約への修正です。

[同:677](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:677)のbaseline helperもrunner entryと内容digestの基準を`request.tested_main_sha`へ変更します。waiterのtested-tip基準は変更しません。

### Landの正負例

[同:1523](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:1523)

- tested tipだけrunnerを変更する。
- receiptはtested main digest。
- main側は`main-new.txt`だけを変更してclean forward-main mergeする。
- `tested_main runner == incorporated_main runner != tested_tip runner`をassertし、成功させる。
- D987追加後のrunner lookup順は`tip, tested main, incorporated main`。

[同:1568](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:1568)

- 現fixtureはreceipt作成後にmain側runnerを変更しており、D987負例としてそのまま利用できる。
- 成功期待をgeneric拒否へ反転する。
- `RC_AUDIT`、`release_safe=True`、`retryable_same_request=False`、mainがlanding tipへ進まないことをassertする。

[同:1622](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:1622)

- mainとtipのrunner差分を保ち、`runner_digest_revision=tip`を明示する。
- receipt digestがtipと一致しmainとは異なることをassertする。
- 拒否理由はgeneric、non-retryableのままとする。

[同:1646](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:1646)

- accepted planの「tip digestを明示して旧orderingを維持」は採用しない。
- fixture既定をmain digestへ変え、runner差分がrunner gateを通過してchecker lookupへ到達することをassertする。
- checker lookup失敗による`retryable=True`, `release_safe=False`へ期待を更新する。

加えて、forward-mainのincorporated runner lookupだけを失敗させる小さい負例を同じtest群へ追加し、新しいlookup failureのretryable分類を固定します。

既存の欠落、非blob、main digest mismatch、checker等値、runnerを変更しないforward-main chainのテストは残します。特に[同:6903](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:6903)は、runner不変の1段および複数段forward-main receipt再利用を引き続き証明します。

## 6. scope外

このauthor変更で編集するのは次の4ファイルだけです。

- `tools/acceptance_launcher.py`
- `tools/dev_wave_land.py`
- `orchestrator/tests/test_acceptance_launcher.py`
- `orchestrator/tests/test_dev_wave_land.py`

次は変更しません。

- 段階R、bounded local、non-dispatch receipt
- `tools/run_tests.py`
- `tools/dev_wave_wait.py`
- dispatcher、`tools/pegasus/dispatch_compute.py`、`tools/acceptance_shards.py`
- `tools/check_acceptance_reds.py`
- hooks、supervisor
- schema v5、canonical field集合、既存receipt fieldの意味
- shard既定数3への変更
- `_runner_tree_entry()`のparserと戻り値契約
- 一般的なreceipt再設計
- 運用docs、変異matrix、台帳fragment、insight。briefどおり親の統合範囲とする

read-only plan段なのでpytest、build、checkerは実走しておらず、緑とは判定していません。実装後のテスト実走は親が指定経路から行います。

## 総括

削除対象はlauncherのbytes等値とlandのblob ID等値のexact 2述語です。tested-main実行、実行後再読、全shard binding report、receipt main digest、launcher、waiter、checker束縛は残します。

D987は、検証済みforward-main列を唯一のreceipt verifier callへ渡し、最後のincorporated main runner entryをtested main entryと比較する最小変更で閉じます。main-tip差分の正例、tip digest負例、forward-main runner変更負例、および新たに到達するretryable拒否を直接テストします。