## S-1 — genesis の失敗 cleanup が、別 process の正常な追記まで削除する

**real／scope 内・must-fix。** プランの「作成成功＝削除時まで自分だけの file」という前提は、genesis では成立しない。

根拠は `trial_registry.py:2454` の canonical path への直接書き込み、`:2458` の fsync、`:2953` の追記側だけの flock、`:3027` の追記 fsync、`:3041` の正常 return。次の時系列が成立する。

1. A が genesis を O_EXCL 作成し、末尾改行まで書く。A は fsync 前で停止する。
2. B が `reserve_attempt_slot`（`:3172`）を呼ぶ。履歴に genesis がまだない場合も、`:2982` は `history_tip is None` を拒否しない。B は完全な genesis を読み、start・seal を追記し、fsync を完了して capability を受け取る（`:3159`、`:3165`）。
3. A が再開し、fsync が失敗する。プランの cleanup は、**B が正常に追記・同期した台帳ごと unlink** する。
4. canonical path が空いたため、次の genesis 作成が通る。作成 API 自体は Git 履歴を調べず、入力検証後に writer を呼ぶ（`:2492`、`:2530`）。

B の追記は同じ inode に行われるため、**`st_dev`／`st_ino` 照合だけでは防げない**。問題は名前の所有だけでなく、作成した inode が既に他者に利用・更新されていることにある。

成果物影響：正常に受理された slot 消費記録が消え、未コミットなら新しい genesis で試行台帳を再起動できる。certified 選択の誤受理まで実証したわけではないが、試行台帳の正しさの欠陥であり、可用性だけでは説明できない。

プランには、genesis 作成中に reader・追記が進めない既存の保証を示すか、この競合を扱う設計の修正が必要。inode 照合の追加だけで完了としてはならない。

## S-2 — 通常の create-only writer 同士では、敗者による完成物削除は成立しない

**refuted／scope 内。** 根拠は `trial_registry.py:2447` の open と `:2451` の書き込み try の分離、およびプランが cleanup を後者だけに置いていること。

同じ path を狙う2 process の時系列を、最低限次の3本で確認した。

| 時系列 | 結果 |
|---|---|
| A が作成→B が open して EEXIST→A が正常完了 | B は内側 try に入らず、A の完成物を削除しない。 |
| A が部分書き込み→B が EEXIST→A が失敗して unlink→B が再試行して正常完了 | A の unlink はBの作成より先。A はその後 close するだけで、B を削除しない。 |
| A が失敗して unlink→B が作成→A が close 中に失敗 | close の例外は外側へ進む。cleanup へ再入しないので、B を二重 unlink しない。 |

この閉じた実行集合では、A が名前を保持している間、B は O_EXCL を通れない。A が名前を解放する操作も cleanup の一度だけなので、inode 照合は必要条件ではない。

EEXIST 処理を cleanup の内側へ移せば既存完成物を削除し得るが、それはプランの明示した try 境界への違反になる。現在のプランは単なる捕捉順序ではなく、**open 成功後だけ cleanup に到達する構造**で排除している。

成果物影響：この3時系列では、既存完成物の値・参照と二重作成拒否は変わらない。ただし S-1 の追記 process は、この閉じた集合に含まれない。

## S-3 — P2 は「真の部分 bytes」と「fsync 未完了の完全 bytes」を分ける必要がある

**real／scope 内。** P2 の「本件は可用性だけ」という結論は、S-1 の時系列を除外できていない。一方、短い prefix が正当な genesis として通るという攻撃は反証された。

genesis は `trial_registry.py:2526` で canonical JSON **1行＋末尾改行**として構築される。reader は `attempt_registry_core.py:1547` で末尾改行を要求し、`:1560` で canonical JSON を確認する。通常の部分 write による真の prefix は末尾改行を持たず、拒否される。

また、genesis に bytes 照合が一切ないわけではない。

- `trial_registry.py:1462` は content commit の genesis blob を読み、`:1469` で binding の initial hash と照合する。
- `:3562`〜`:3573` の正式受入は、同じ hash と現在台帳の prefix 一致を要求する。

ただし `load_attempt_registry`（`:2649`）には writer の成功・fsync 完了を確認する仕組みがない。完全な1行が見えれば、初回の未コミット genesis も構文・履歴検査を通り得る。S-1 はこの窓を使う。

成果物影響：壊れた短い prefix の誤受理は確認できないが、未完了 writer の完全 bytes を起点に受理された台帳記録が cleanup で消える。DW-G05 はこの正しさへの影響を含めて訂正すべき。

## S-4 — 受領証 digest 検査には迂回経路があるが、今回の部分 write の誤受理には直結しない

**refuted／scope 内の部分書き込み攻撃。** 「すべての台帳利用で受領証 file の digest を検査する」という一般化は成立しない。

`_assert_attempt_registry_rows` は `repository_root=None` なら receipt 検査を省く（`trial_registry.py:2303`）。ただし worktree の production 呼び出しは `:2686` の1箇所で、そこは `repository_root=root` を渡している。省略呼び出しによる迂回は見つからなかった。

別経路は実在する。

- `_locked_attempt_registry_update` は `:2981` で core の bytes parser を直接使い、receipt storage 検査を呼ばない。
- `s8c_acceptance_receipt.py:1620` は digest 検証済み台帳 prefix を core で再生し、`:1660` で projection を導出する。個々の分類受領証 file の再読込ではない。

それでも、今回の writer 失敗では `classify_attempt` の `:3288` から戻らず、分類行追加（`:3322`）と capability 更新（`:3327`）へ進まない。上記の経路が再生する分類行自体が新たに作られないので、部分 receipt を正当な分類として受理する反例にはならない。

成果物影響：今回の部分 write だけから誤った分類値が受理される経路は確認できない。「検査迂回がない」ではなく、「失敗した発行から参照行が作られない」が根拠になる。

なお caller 列挙・gate・主要アンカーは現物の `:2530`、`:3288`、`:3336`、`p3_autonomous_workload_trial.py:4876` と一致した。

## S-5 — 再試行は同一入力に限定されず、分類側の「slot が恒久的に分類不能」も過大

**real／scope 内。ただし記述上の nit であり、単独では must-fix にしない。**

genesis の cleanup 後は、同じ引数だけでなく、検証を通る別の freeze・slot 集合でも作成できる。前回入力を保存・照合する処理は `trial_registry.py:2492`〜`:2534` にない。失敗した初回作成を撤去する指示から自然に生じる範囲であり、これだけを禁止する新規 gate は不要。しかしプランの「同じ引数による再試行」はテスト例であって、実装の受理集合全体ではない。

分類側は payload の digest が path を決める（`:3282`〜`:3286`）。`classified_at` を変えるだけでも別 path になり、production caller は `p3_autonomous_workload_trial.py:4884` で現在時刻を渡す。残骸が恒久的に塞ぐのは、直接には**同一 receipt bytes の path**であり、slot 全体とは限らない。分類行追加時の core 検査は引き続き残る（`trial_registry.py:3300`）。

成果物影響：genesis では失敗後に別の初回内容を選べる。分類では同一 payload の再試行が新たに通る一方、別 payload の試行は修正前から別 path を使えた。既存の正常 genesis の再作成拒否は S-2 のとおり残る。

## S-6 — cleanup の通常エラーは保存されるが、中断と close まで含む保証ではない

**refuted／scope 内：unlink の `OSError` による元原因の置換。**

プランの `except OSError: pass` と裸の `raise` は元の write／fsync 例外を再送出する。既存の `trial_registry.py:2465` は gate・原因文字列を含む `TrialRegistryError` を `from exc` で送出する。親 fd の close は `:2467` なので、通常の cleanup は有効な dir_fd を使う。

`BaseException` を選ぶ差は次のとおり。

- write／fsync 中の `KeyboardInterrupt`・`SystemExit`：cleanup 後に同じ例外を再送出し、再試行可能になる。
- `Exception` のみ：これらは cleanup を通らず、残骸が残る。
- unlink 前の追加割り込み、SIGKILL、既定動作で終了する signal：cleanup 完了は保証できない。
- unlink 成功後の割り込み：名前は既に消えている。再試行は可能だが、元の I/O エラーより中断例外が表面に出得る。

unlink が削除後にエラーを返した場合も、プランは再度 unlink しない。その間にBが作成した file を二度目の cleanup で消す経路はない。

成果物影響：通常の cleanup 失敗では診断を保持し、残骸による拒否が残る。中断については再試行可能になる範囲が広がるが、全 signal からの回復を保証するものではない。

## scope 外の所見

**S-7 — 名前の外部置換後には、別 inode の完成物を削除する。real／scope 外。**

A が inode I を作成→別操作が名前を unlink／rename→B が同名に inode J を作成して完了→A の write／fsync 失敗→cleanup が J を削除、という時系列は成立する。`dir_fd` は親ディレクトリを固定するだけで、basename の inode は固定しない。現物でもこの区別は `trial_registry.py:2731`〜`:2749` の既存 identity 検査に現れている。

成果物影響：B の完成物の参照が失われ、path が再作成可能になる。

通常 writer 同士だけでは外部置換の段階を作れないため、新しい一般防御を本件の must-fix にはしない。inode 照合は既に起きた置換を検出できるが、照合と unlink の間の置換まで原子的に防ぐものではない。

**S-8 — close の失敗は元の診断を置換する。real／scope 外。**

`trial_registry.py:2461` の close が失敗すれば、外側の `__cause__` は元の write エラーでなく close エラーになる。`:2467` の親 close が失敗すれば、構築済み `TrialRegistryError` 自体を上書きし、最上位から gate が消える。元例外が `__context__` に残る場合も、`__cause__` に保持する保証とは異なる。

成果物の値・受理集合への独立した変化は示せないため **診断の nit**。既存経路であり、今回の unlink の `OSError` 抑制とは分けて扱う。

## 総括

**プランは S-1 の解消が必要。** genesis の直接公開後、別 process が正常に追記した台帳を cleanup が削除できる。inode 照合だけでは防げず、P2 の「可用性だけ」という結論も維持できない。

通常 writer 同士の EEXIST、二重 unlink、通常の unlink エラーによる原因喪失は反証した。真の部分 genesis bytes の誤受理も、末尾改行検査で反証した。

必読6ファイルは読み取り可能だった。静的検査のみで、編集・commit・pytest 実走は行っていない。