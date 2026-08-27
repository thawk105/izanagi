## 束縛の候補と可否

### (a) stdin bootstrap を計算ノードでも使う

実現可能であり、最小候補です。

- 現行 bootstrap は stdin の bytes を読み、`__file__` だけ canonical な作業ツリー path にして実行します。`tools/acceptance_launcher.py:51-61`、`tools/acceptance_launcher.py:213-227`
- bootstrap の namespace に実行中の `source` bytes と SHA-256 を非公開名で渡し、`tools/run_tests.py` がそれを保持します。`_REPO` は従来どおり canonical `__file__` から導出します。`tools/run_tests.py:55-58`
- `_default_dispatch` から `tests` task に限って source bytes と SHA-256 を渡します。変更点は `tools/run_tests.py:1307-1324` です。
- source は canonical base64 と SHA-256 として request JSON に含めます。request 全体は既存の SHA-256 で job script に束縛されます。`tools/pegasus/dispatch_compute.py:2857-2868`、同 `:640-645`、同 `:962-973`
- job script の argv は変更不要です。従来どおり dispatcher を `--job-run "$REQUEST"` で起動できます。`tools/pegasus/dispatch_compute.py:679-687`
- `_job_run` の `tests` 分岐だけ、子 argv を次に変えます。

```text
[python, -I, -c, RUNNER_BOOTSTRAP,
 <repo_root>/tools/run_tests.py, *argv]
```

  stdin は `DEVNULL` ではなく、request から復元して SHA-256 を再検証した source bytes にします。現行変更面は `tools/pegasus/dispatch_compute.py:1010-1021` です。

代償は request が約 4/3 倍の base64 payload を各 shard ごとに持つこと、source 上限・canonical base64・digest 検査が必要なこと、request schema の互換受理が増えることです。現行は待機中の旧 request を殺さない契約を明記しています。`tools/pegasus/dispatch_compute.py:160-174`、同 `:719-735`

fingerprint との衝突はありません。専用 runner file は作らず、既存 request に field を追加するだけです。現在の repo 内 dispatch artifact も Git から無視されています。`.gitignore:26`。ただし、専用 source file を作業ツリー内へ追加する派生案は採用不可です。

### (b) repo 外の絶対 path へ実体化する

共有 path を限定すれば実現可能ですが、(a) より条件と故障面が増えます。

- login 側で source を create-only、mode 0600 の blob file として置き、絶対 path と SHA-256 を request に入れます。
- `[python, <外部blob>, ...]` と直接実行してはいけません。そうすると `__file__` から導く `_REPO` が外部 directory になります。`tools/run_tests.py:55-58`
- 子 argv は bootstrap に「外部 source path」と「canonical runner path」の両方を渡す形にします。より安全なのは `_job_run` が file を一度だけ読み、検証した同じ bytes を stdin へ渡す形です。子に再 open させる形は検査後差替えの競合が残ります。
- job script 自体は変更不要で、path と digest を SHA 束縛済み request に保持できます。`tools/pegasus/dispatch_compute.py:640-687`

sharded acceptance の既存 `artifact_root` は repo 外を要求し、`submission_dir` の request、probe、script をそこへ作ります。`tools/pegasus/dispatch_compute.py:2716-2733`、同 `:2833-2882`。したがって、その `submission_dir` の隣に置く形が最小です。

fingerprint は、blob が本当に repo 外なら衝突しません。作業ツリー内へ置く案は、pre/post の `git status --untracked-files=all` と衝突し得るため不可です。`tools/dev_wave_wait.py:357-360`、同 `:3742-3760`、同 `:3821-3842`。land 側も `status_bytes == 0` と `diff_bytes == 0` を要求します。`tools/dev_wave_land.py:805-817`

### (c) Git object を計算ノードで読み直す

実現可能です。payload は最小ですが、Git への追加依存があります。

- launcher は既に immutable な `tested_main` から runner blob を読んでいます。`tools/acceptance_launcher.py:173-196`、同 `:435-441`
- bootstrap から `tested_main` または runner blob OID と expected SHA-256 を `run_tests.py` へ渡し、`tests` request にその小さい binding だけを入れます。
- `_job_run` は共有 repo で `git cat-file blob <tested_main>:tools/run_tests.py` を実行し、SHA-256 を照合した bytes を (a) と同じ bootstrap の stdin にします。
- job script と canonical `__file__` は変更不要です。

専用 file がないので fingerprint と衝突しません。base64 payload も不要です。一方、compute 側の Git executable、object store、Git 環境隔離まで受入実行経路に入ります。そのため、実装の単純さでは (a)、転送量では (c) が優ります。

## 共有 filesystem の前提

現行コードから確定できるのは、計算ノードが次の絶対 path を読めることです。

- repo、dispatcher、request、probe の path を job script に埋め込み、compute 側で `cd "$REPO"` して dispatcher を起動しています。`tools/pegasus/dispatch_compute.py:640-687`
- `_job_run` は同じ request から `repo_root` を読み、そこで子を起動します。`tools/pegasus/dispatch_compute.py:945-1021`
- sharded acceptance の shared root は repo 外であることを検証されます。`tools/acceptance_shards.py:177-199`
- その root は実際に各 shard の `artifact_root` として dispatch へ渡されます。`tools/acceptance_shards.py:970-989`、同 `:1000-1018`

したがって、(b) で既存 shard `submission_dir` に置く場合は、request や probe と同じ共有性を利用できます。任意の `/tmp` は不可です。`/scr` は compute node 専用です。`docs/pegasus-runbook.md:282-292`

repo 文書は `/home` が共有であることも記録しています。`docs/pegasus-runbook.md:693-695`。ただし任意の新規 path について、表記、権限、mount が同一かまでは証明しません。`/work` は node により実体表記が異なる可能性もあります。`docs/pegasus-runbook.md:290-292`

新しい外部 root を使うなら、login 側で既知 bytes を mode 0600 で作成し、同じ queue/account の小さい job がその絶対 pathを読み SHA-256 を返せるかを測る必要があります。realpath、uid、読取権限、job 終了後の login 側読取も同時に記録すべきです。(a) と (c) は新しい共有 root を要求しません。

## 鶏と卵の順序

現行 gate のままでは、この wave の受入ではどちらの版の runner も走りません。

1. waiter は claim 後に tested tip の fingerprint を確定します。`tools/dev_wave_wait.py:3656-3670`、同 `:3755-3788`
2. main に launcher が存在するため、実行する launcher source は tested main です。`tools/dev_wave_wait.py:2565-2577`
3. その旧 launcher は main と tip の runner blob を読み、差があれば runner 起動前に拒否します。`tools/acceptance_launcher.py:435-441`
4. tip 側で equality 判定を削除しても、実行される旧 main launcher の判定は変わりません。land 側にも別の main/tip equality があります。`tools/dev_wave_land.py:1065-1088`

一度だけ外部認可で equality を越えた場合、外側 runner は `source = tested_main` なので旧 main 版です。`tools/acceptance_launcher.py:436-441`。しかし束縛実装を新しい tip の `run_tests.py` に置いただけなら、そのコードは実行されず、現行 compute 子は tip 作業ツリーの pathname を起動します。`tools/pegasus/dispatch_compute.py:1010-1021`

したがって案 B は、単に両変更を同一 commit に入れるだけでは自己検証できません。一度だけの land 認可、または旧 main runnerでも利用できる専用 transition launcher/dispatcherが必要です。land 後の次回受入からは、新 main runner が (a) または (c) の束縛を駆動できます。

## 波及範囲

`tests` task だけに閉じられます。

- `tests`、`provenance`、`mutation`、`generic` は別々の `_TaskSpec` です。`tools/pegasus/dispatch_compute.py:110-158`
- `_job_run` の child argv 構築は現在共通なので、ここを一律変更してはいけません。`tools/pegasus/dispatch_compute.py:1010-1021`
- `task == "tests"` または `_TaskSpec` の専用 launch mode で分岐すれば、`provenance` と `generic` は不変です。
- `mutation` は argv 内の runner が live `tools/run_tests.py` であることを明示的に検証しています。`tools/pegasus/dispatch_compute.py:761-794`。この内部 runner まで自動変換すると別契約になるため、今回の対象外にすべきです。
- schema を変更する場合も、既存 v1/v2 tests job の互換受理が必要です。`tools/pegasus/dispatch_compute.py:160-174`、同 `:719-735`

## 採らない方がよい理由 (あれば)

(b) は source file の lifecycle、共有 mount、権限、差替え競合が増えるため、(a) より採用理由が弱いです。

受入だけ dispatch を禁止する案はコード量こそ小さくできます。shard 注入は `tools/dev_wave_wait.py:821-845`、LOGIN dispatch は `tools/run_tests.py:2620-2637` にあります。しかし login node の bounded 容量が足りない場合、受入を実行不能にする設計になります。可用性を犠牲にできる場合だけ有力です。

計算ノードで実行した pathname bytes の記録だけに留める案は、固定実行ではなく事後検出です。副作用は不一致判明前に発生します。また現行 receipt の `runner_executed_sha256` は外側 runner の値だけです。`tools/acceptance_launcher.py:454-459`。waiter もその値を受け取るだけで compute 子の digest を集約していません。`tools/dev_wave_wait.py:3813-3817`。厳密な「tested main blob から実行」を維持するなら代替になりません。

静的検査のみで、pytest や compute probe は実走していません。

## 総括

条件付きで実現可能  
最小形は (a): source bytes と SHA-256 を tests request に含め、compute 子も同じ stdin bootstrap で起動する。  
専用 file は作らず、`tests` task のみを分岐させれば fingerprint と他 task へ波及しない。  
ただし同一 wave の現行受入は旧 launcher の equality で runner 起動前に止まる。  
一度だけの明示的 transition 認可なしには、この修正自身を現行 gate で自己検証できない。