静的確認の結論は、段階 Q を実装可能です。削除対象は親の把握どおり 2 述語だけです。ただし Q によって到達可能になる D987 は同じ wave で閉じるべきです。受領証 schema は v5 のまま、段階 R と非 dispatch 経路には触れません。

テストは実走しておらず、以下は現行コードに基づく実装プランです。

## 1. 削除する述語

### Launcher の byte 等値

[tools/acceptance_launcher.py:567-569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/acceptance_launcher.py:567)

現行:

```python
tip_source = blob_reader(config.repo_root, config.tested_tip)
if source != tip_source:
    raise LauncherFailure("tested-main and tested-tip runner blobs differ")
```

変更後:

```python
blob_reader(config.repo_root, config.tested_tip)
```

`_launch` は次の順に読めるようになります。

1. tested main の runner bytes を取得する。
2. tested tip に runner が blob として読めることだけ確認する。
3. tested main の bytes を実行する。
4. 実行後に tested main を独立再読して実行 digest と照合する。
5. 全 shard の binding report が同じ tested main digest を申告したことを確認して受領証を書く。

### Land の blob-ID 等値

[tools/dev_wave_land.py:1074-1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:1074)

現行の `or` 連鎖から次の一項だけを削除します。

```python
or main_runner_entry[1] != tip_runner_entry[1]
```

削除後は、tested main と tested tip の runner が双方存在する blob であることを確認し、受領証の `runner_executed_sha256` を tested main の blob 内容だけと照合します。

### 3 か所目の検索結果

検索範囲は repo の production source である `tools/**`、`hooks/**`、`orchestrator/**` から `orchestrator/tests/**` と `__pycache__` を除いた全ファイルです。加えて repo 全体の Python source も検索しました。

検索語は以下です。

- `source != tip_source`
- `tested-main and tested-tip runner blobs differ`
- `main_runner_entry`
- `tip_runner_entry`
- `runner_executed_sha256`
- `run_tests.py` または `runner` と、`tested_main` / `tested_tip` / `==` / `!=` / `differ` / `match` の組合せ

main/tip runner の bytes または blob ID を比較する production 述語は上記 2 点だけでした。

[tools/acceptance_launcher.py:360-363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/acceptance_launcher.py:360) の binding report digest 比較は tested main の実行束縛であり、削除対象の main/tip 等値ではありません。また [tools/dev_wave_land.py:1114-1128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:1114) は checker の別境界です。

## 2. 残す述語

### Launcher

- [tools/acceptance_launcher.py:136-142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/acceptance_launcher.py:136)
  shard 数が明示された `1/2/3` であること。未注入の bounded local 走行を拒否し、D1186 の fail-closed を保ちます。

- [tools/acceptance_launcher.py:208-231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/acceptance_launcher.py:208)
  `git cat-file blob <revision>:tools/run_tests.py` が成功すること。main または tip の runner を削除・tree 化する置換を拒否します。

- [tools/acceptance_launcher.py:566-570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/acceptance_launcher.py:566) と [同:584-590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/acceptance_launcher.py:584)
  実行 buffer と digest を tested main の `source` から取ります。tip bytes を `blob_runner` へ渡す置換を殺します。

- [tools/acceptance_launcher.py:597-603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/acceptance_launcher.py:597)
  実行後に tested main を独立再読する M3。最初に hash した bytes と、実行後に観測した main blob が異なる置換を拒否します。

- [tools/acceptance_launcher.py:341-363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/acceptance_launcher.py:341) と [同:616-623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/acceptance_launcher.py:616)
  exact K、`0..K-1`、nonce、tested main、runner digest を検査します。計算ノードで tip pathname の runner を再実行して tip digest を申告する置換を拒否します。

### 段階 P の計算ノード束縛

[tools/pegasus/dispatch_compute.py:856-899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/pegasus/dispatch_compute.py:856) は tested main の blob を同じ buffer から hash・stdin 実行し、[同:1276-1285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/pegasus/dispatch_compute.py:1276) が binding のある受入子をこの経路へ送ります。どちらも無変更で残します。

### Land

- [tools/dev_wave_land.py:950-953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:950)
  receipt digest の SHA-256 形式検査。ただし後続の main 内容 digest 等値が成立すれば形式も必ず成立するため、最終受理条件としては防御的重複です。

- [tools/dev_wave_land.py:1065-1068](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:1065)
  main/tip 双方の runner entry の実在。片側の削除を拒否します。

- [tools/dev_wave_land.py:1080-1081](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:1080)
  双方の object type が `blob`。runner を tree 等へ置換する入力を拒否します。

- [tools/dev_wave_land.py:1082-1083](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:1082)
  object ID の SHA 形式。これは `_runner_tree_entry` が [同:838-846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:838) ですでに 40/64 桁 hex に限定しているため、到達時には恒真です。防御的重複として残せますが、独立した保証には数えません。

- [tools/dev_wave_land.py:1085-1086](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:1085)
  receipt digest と tested main runner 内容の照合。tip digest を名乗る receipt を拒否する中心述語です。

## 3. 受理集合の差分

全ての既存条件から runner main/tip 等値だけを除いたものを `C`、D987 の新条件を `F` とします。

- 変更前: `C ∧ main_runner_blob == tip_runner_blob`
- 変更後: `C ∧ F`
- `F`: forward-main receipt 再利用でない、または最後に取り込んだ main の runner entry が tested main の runner entry と同じ

したがって新たに受理される完全な集合は、次をすべて満たす入力です。

- tested main と tested tip の `tools/run_tests.py` が異なる blob である。
- 双方が実在する blob である。
- 実行 bytes、binding reports、receipt の `runner_executed_sha256` が tested main の内容に一致する。
- shard、nonce、waiter、launcher、checker、fingerprint、schema 等の既存条件を全て満たす。
- forward-main を伴う場合、取り込んだ main の runner は tested main から変わっていない。

変更後も以下は拒否されます。

- main または tip の runner の欠落、読取不能、非 blob。
- receipt が tip digest、任意 digest、実行前 main から drift した digestを名乗る。
- binding report の欠落、余分、重複 index、nonce/main/digest 不一致。
- shard 数が注入されない非 dispatch 受入。
- waiter の tip 束縛違反。
- `non-attributable-only` における checker main/tip 不一致。
- forward-main が tested main 以降で runner を変更している receipt 再利用。
- その他の v5 schema、topology、tree、audit、cleanliness 条件違反。

D987 の追加により、従来受理されていた「receipt の tested main/tip runner は同一だが、その後取り込んだ main が runner を変えた forward-main」は新たに拒否されます。これは受理集合の縮小です。

### 拒否分類の反転

active fold がなく `quiescent_rejection=True` の通常経路を前提とします。

- main≠tip で他が全て正常:
  現在は `RC_AUDIT`、non-retryable、release safe。変更後は成功します。

- main≠tip、receipt は main digestだが、main blob の `cat-file` が失敗:
  現在は等値で先に non-retryable、release safe。変更後は [tools/dev_wave_land.py:898-905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:898) まで進み、retryable、release unsafeになります。

- main≠tip の `non-attributable-only` receipt で checker lookup が失敗:
  現在は等値で先に non-retryable、release safe。変更後は [同:1093-1108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:1093) まで進み、retryable、release unsafeになります。

- receipt が tip digestを名乗る:
  main digest 照合で引き続き non-retryable、通常は release safeです。分類は反転しません。

- D987 の runner 変更:
  現在は成功しえますが、変更後は generic な `acceptance-receipt-rejected`、non-retryable、通常は release safeになります。新しい incorporated-main lookup 自体が失敗した場合だけ retryable、release unsafeです。

Launcher には `retryable_same_request` / `release_safe` 分類はありません。現在の事前 rc=70 が消え、後続の main 実行、binding report、completion の成否まで進む点が観測差になります。

## 4. テスト改訂計画

### (a) 等値述語を削除すると落ちるテスト

- [orchestrator/tests/test_acceptance_launcher.py:222-249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_acceptance_launcher.py:222)
  `test_main_tip_runner_blob_mismatch_is_rejected_before_execution`。差分自体は正常になるため、事前拒否期待が落ちます。

- [orchestrator/tests/test_dev_wave_land.py:1523-1566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:1523)
  `test_land_rejects_child_green_runner_blob_divergence`。現在すでに main digest を名乗っているため、Q 後は正常受理されます。

### (b) 緑のままだが main/tip の byte 選択を区別できないテスト

- [orchestrator/tests/test_acceptance_launcher.py:175-220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_acceptance_launcher.py:175)
  main と tip が別 object でも bytes は同一です。tip を実行しても結果を区別できません。

- [orchestrator/tests/test_dev_wave_land.py:1568-1620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:1568)
  receipt 作成時の main/tip runner が同一です。また、この test は forward-main 側で runner を変更して成功させており、D987 の未実装穴そのものでもあります。Q の正例と D987 の負例へ分割します。

### (c) 等値削除後も同じ保証で通るテスト

Launcher:

- main/tip 欠落拒否: [test_acceptance_launcher.py:251-310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_acceptance_launcher.py:251)
- M3 main 再読拒否: [同:313-349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_acceptance_launcher.py:313)
- argv と pathname bootstrap: [同:352-410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_acceptance_launcher.py:352)
- binding report の K、digest、nonce、index、tested main: [同:413-630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_acceptance_launcher.py:413)
- canonical v5、authority、scheduler: [同:633-749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_acceptance_launcher.py:633)

Land:

- main runner digest mismatch: [test_dev_wave_land.py:1062-1080](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:1062)
- non-attributable の tip digest 拒否: [同:1622-1644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:1622)
- runner 欠落: [同:1690-1749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:1690)
- lookup failure の retryable 分類: [同:1752-1821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:1752)
- tested main digest の選択: [同:1824-1855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:1824)
- 非 blob 拒否: [同:1858-1883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:1858)
- runner を変えない forward-main receipt 再利用: [同:6903-6928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:6903)

Waiter の [test_dev_wave_wait.py:2997-3018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_wait.py:2997) は schema-level の test であり、Git blob の byte 選択を検査していません。そのまま通し、編集しません。

### main≠tip 正例と tip digest 負例

Launcher:

- (b) を `test_different_main_and_tip_runner_blobs_execute_tested_main_source` に改名。
- `main_source != tip_source`、再読 main は最初の main と同じにする。
- 読取順 `[tested_main, tested_tip, tested_main]`、実行 source は main、receipt digest も main と assertする。
- (a) は、実行自体は main で成功させつつ binding report に `sha256(tip_source)` を申告させ、`runner binding report digest mismatch` と receipt 未作成を確認する負例へ変える。
- M3 test も main、異なる tip、drift した再読 main の 3 bytes にし、tip 不一致ではなく main 再読差分で落ちることを固定する。

Land:

- main≠tip 正例は、tested tip で runner を変更し receipt は main digestを名乗らせる。その後 main は `main-new.txt` のみ変更して clean forward-mergeする。tested main と incorporated main の runner ID が同じ、tip は異なることを assertして成功させる。
- tip digest 負例は同じ divergent fixtureに `runner_digest_revision=tip` を明示し、receipt digest が tip と一致し main と異なることを assertして拒否させる。
- `non-attributable-only` の既存負例も tip digest の明示を維持する。
- [test_dev_wave_land.py:1646-1687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:1646) は fixture 既定変更後も ordering を保つため、`runner_digest_revision=tip` を明示します。

### Fixture の既定値

[orchestrator/tests/test_dev_wave_land.py:354-357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:354) を次の意味へ変更します。

```python
runner_digest_revision or tested_main
```

これは producer の実仕様に合わせる変更です。引数自体は残し、tip digest 負例や main 欠落 fixtureだけが明示的に tip を指定します。

[同:677-692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:677) の `_assert_v5_binding_baseline` も runner entry と内容 SHA-256 の基準を `request.tested_main_sha` へ変更します。waiter の tested tip 基準は変えません。

## 5. D987 は本 wave で閉じる

親の provisional 裁定 P3 に賛成です。

[tools/dev_wave_land.py:2041-2158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:2041) は ancestry、parent 列、merge base、tree を検査し、[同:2168-2292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:2168) は merge tree を再演します。[同:2295-2310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:2295) も incorporated main と locked main の ancestry だけです。runner を読む処理はありません。

現在は receipt 検証へ `tested_main`、`tested_tip`、`locked_main` しか渡していません。[同:5035-5042](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:5035)

実装は次の形にします。

1. [同:908-916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:908) の署名へ追加:

```python
forward_main_merges: Sequence[_ForwardMainMerge],
```

2. [同:5035-5042](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:5035) から、locked preflight で再確認済みの値を渡す:

```python
forward_main_merges=preflight.forward_main_merges,
```

3. 現在の runner blob/type/main-digest gate直後、checker lookupより前に追加:

```python
if forward_main_merges:
    incorporated_runner_entry = _runner_tree_entry(
        repository,
        forward_main_merges[-1].incorporated_main_sha,
    )
    if incorporated_runner_entry != main_runner_entry:
        raise _acceptance_rejected()
```

比較対象は、receipt の `tested_main` にある `(object_type, blob ID)` と、最後に取り込んだ main commit にある同じ entryです。欠落、非 blob、別 blobを変更として拒否します。最終 incorporated main が一度変更後に元の exact blobへ戻していれば、保証対象 bytes は同じなので再利用できます。modeだけの変更も実行 bytes を変えないため、この entry比較では拒否しません。

拒否理由は既存の秘匿境界に合わせて `acceptance-receipt-rejected` とし、entry不一致は non-retryableです。`ls-tree` 自体の失敗だけは既存 `_runner_tree_entry` により retryableです。

通る正例は、「tested tip が runner を変更して main≠tip、receipt は tested main digest、受入後に main が `main-new.txt` だけを変更し、その main を clean forward-mergeしたもの」です。tested main と incorporated main の runner blob ID は同じなので、Q と D987 の双方を通ります。

D987 の負例は、[test_dev_wave_land.py:1568-1620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/orchestrator/tests/test_dev_wave_land.py:1568) に現在含まれる synthetic 経路を独立 test にします。receipt 作成後に main の `tools/run_tests.py` を変更して forward-mergeし、generic rejection、non-retryable、release safe、main不変を確認します。

D987 を閉じず Q だけ着地させると、別 wave が新 runner を mainへ landした後、古い runnerで作った receiptを持つ waveがその mainを forward-mergeし、古い `runner_executed_sha256` のまま新 runnerを含む landing tipを着地できます。

## 6. `docs/pegasus-runbook.md` 改訂文案

### 現行 930-945

[docs/pegasus-runbook.md:930-945](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/docs/pegasus-runbook.md:930)

現行の該当文:

> 実行前に `tested_tip:tools/run_tests.py` の bytes も別に読み、**一致しなければ suite を一度も起動せずに** rc=70 で止まる。

置換案:

> 実行前に `tested_tip:tools/run_tests.py` も blob として別に読み、欠落または読取不能なら suite を一度も起動せず rc=70 で止まるが、tested main との byte 等値は要求しない。実行する bytes は常に `tested_main:tools/run_tests.py` から取得する。実行後の独立再読と全 shard の binding reportも tested main の内容 SHA-256 に照合し、いずれかが異なれば受領証を書く前に fail-closed する。

### 現行 962-970

[docs/pegasus-runbook.md:962-970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/docs/pegasus-runbook.md:962)

現行文:

> **`tools/run_tests.py` を変更した wave は、どの verdict でも受入を通せない (D838)。** launcher は suite 起動前に、land は verdict によらず共通に、`tested_main:tools/run_tests.py` と `tested_tip:tools/run_tests.py` の object type が `blob` であることと blob SHA の等値を要求する。受領証の `runner_executed_sha256` の照合先も `tested_main` 側の blob である。実行器を触る wave は受入そのものが通らないので、**実行器の変更と他の変更を同じ wave に載せない**こと。
> この等値は、claim 後・待ち手の内部 merge 前に**別の wave が実行器の変更を main へ land した**場合にも破れる。実行器を触っていない wave が一度拒否され、受入をやり直すことになる。そのときは新しい main を取り込んでから再投入する。

置換案:

> **`tools/run_tests.py` を変更した wave も受入を通せる。** launcher と land は `tested_main:tools/run_tests.py` と `tested_tip:tools/run_tests.py` が双方 blob として実在することを要求するが、両者の blob SHA または bytes の等値は要求しない。実行する runner、全 shard の binding report、受領証の `runner_executed_sha256` の照合先は常に tested main 側の blobである。
> 受入後に clean な forward-main mergeを追加して同じ受領証を再利用する場合、landは tested main と最後に取り込んだ main の runner blobを比較する。取り込んだ mainが runnerを変更していれば受領証の再利用を拒否し、新しい mainを基準に受入をやり直させる。runnerを変更しない main取り込みは従来どおり再走を要求しない。

## 7. 編集しない境界

- `tools/run_tests.py`。bounded local の main blob 化は段階 R。
- `tools/pegasus/dispatch_compute.py` と `tools/acceptance_shards.py`。段階 P の束縛をそのまま使う。
- `tools/dev_wave_wait.py`。特に waiter の tip bytes 等値 [2195-2274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_wait.py:2195) と shard 注入 [821-845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_wait.py:821)。
- `tools/check_acceptance_reds.py`。
- land の checker main/tip 等値 [tools/dev_wave_land.py:1093-1128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:1093)。
- `_runner_tree_entry` の parser と戻り値契約 [tools/dev_wave_land.py:821-848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:821)。
- `hooks/**` と `tools/dev_waves/**`。
- schema literalと field集合: [tools/acceptance_launcher.py:21-49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/acceptance_launcher.py:21)、[tools/dev_wave_land.py:94-130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1975-runner-tip-equality/tools/dev_wave_land.py:94)。
- `dev-wave-acceptance-receipt/v5` の canonical JSON、既存 field、`runner_executed_sha256` の意味。
- 等値撤去とD987の限定拒否以外の受入述語。追加の緩和が必要になった場合は実装せず、別裁定へ返す。

## 総括

削除は launcher の byte 比較と land の blob-ID 比較の2点だけ。
tested main実行、独立再読、binding reports、receipt main digest、D1186を維持する。
main≠tipの main digest正例と tip digest負例を launcher・land双方へ置く。
Qで到達可能になるD987は最終 incorporated mainの runner blob比較で同時に閉じる。
schema v5、waiter、checker、hooks、段階Rの経路は変更しない。