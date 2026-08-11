# 独立検証結果

結論は二段です。

- [T-798] の「state 消失・fold commit 未作成」の窓と、[T-799] の「state に HEAD／起源束縛がない」という核は実在します。
- ただし、裁定パッケージの幅、[T-766] との同型性、C2 の欠陥解釈、B4 の普遍性、Q1(b) の回復可能性は成立しません。現状のまま Q1(b)+Q2(a)+(b) を選ぶのは危険です。

指定資料・全 probe source／log は読了しました。read-only 制約に従い、新たな実測や pytest は行っていません。以下で `real` は「親の主張への攻撃が成立」、`refuted` は「攻撃不成立」を意味します。

| 攻撃点 | 判定 | 要旨 |
|---|---|---|
| 1. 窓の同定 | mixed | 注入点は窓内。ただし入口ではなく、commit 後の別残骸を未測定 |
| 2. fixture 差 | real | 本番 source は同じだが、実際の分岐・受理集合は同一でない |
| 3. 2.82 秒 | real | end-to-end 実測ではなく、commit・postcondition を除く代替値 |
| 4. [T-766] state | real | probe は pre-mutation state。rollback 失敗残存 state の代表ではない |
| 5. B1 誤 HEAD | mixed | 受理自体は real。測った HEAD 変更は安全かつ通常 land 外 |
| 6. C2 解釈 | refuted | 測ったケースは内容上正常。帰属欠陥は新規要件にすぎない |
| 7. B4「必ず」 | real | 現行の狭い形では成立するが、推奨 Q1(b) が直ちに反例を作る |
| 8. 見落とし | real | rollback 二重故障、post-commit crash、target 外入力、standalone race |

## 1. 窓の入口・出口

**[refuted] 注入点が窓外という攻撃は成立しません。**

state は [spool_fold.py:2357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/spool_fold.py:2357) で unlink され、directory fsync 後に `apply_fold` が返ります。land は [dev_wave_land.py:1872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/dev_wave_land.py:1872) の次行で docs 検査へ入るため、checker からの SIGKILL は確実に「state 無し・commit 前」です。P2 の狭い主張は崩せません。

**[real] ただし「窓の入口」という表現は誤りです。**

入口は `_validate_generated_docs` ではなく、論理上は `state_path.unlink()`、電源断に対する耐久境界なら直後の directory fsync です。注入までには fsync、関数 return、checker path 検査、環境構築があります。

さらに brief が定義した窓は postcondition までですが、probe は commit 前の一点しか殺していません。`git commit` 成功後から [postcommit 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/dev_wave_land.py:1920) の途中で死ぬと、残るのは「fold commit あり・state 無し・land 成否未報告」であり、probe の rc=20 dirty 残骸とは別物です。

成果物影響: findings／rulings は「単一の窓」を、少なくとも pre-commit journal-loss と post-commit unconfirmed の二相へ分け、残骸・復旧参照を別記する必要があります。

## 2. fixture と実物の差

**[real] P1 の「測っている制御フローは本番そのもの」は広すぎます。**

実 module を import している点は確認できました。しかし、checker も branch 名も repository tree も制御フローの入力です。

- fixture の `check_docs.py` は定数と rc=0／SIGKILL だけ、provenance checker も常時 rc=0 です。[fixture.py:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/fixture.py:30)、[test fixture:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/orchestrator/tests/test_dev_wave_land.py:121)
- probe branch は `wave/codex-*` なので、[supervised branch 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/dev_wave_land.py:1597)を通りません。`dev-wave/dw-*` なら C2 の旧 fragment wave は拒否され得ます。現在の `worktree-dev-wave-*` も非 supervised なので、C2 はこの branch family に限れば再現可能です。
- T-798 probe が実測した変更は worklog・FOLDED・fragment の3 pathだけです。[ログ](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/probe_t798.log:22)。「canonical 3 台帳が反映済み」は実測値ではありません。
- 元の C probe は fixture の `.codex/` 状態により rc=20、作り直した `probe_t799c` で rc=0でした。fixture の細部が受理分岐を実際に変えています。

狭い「state 削除後に checker が呼ばれる」という順序証明には問題ありません。C2 の一般化や checker に依存する回復結果には使えません。

成果物影響: C2 の rc=0 受理集合を「非 supervised branch・stub checker が受理する fixture」に縮小し、T-798 の実測変更 path も3 pathへ訂正する必要があります。

## 3. 「窓は 2.82 秒、96%、land 1回ごと」

**[real] これは窓幅の実測ではありません。**

probe 自身が出している値は「commit 自体を除く下限見積り」です。[probe_window_width.py:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/probe_window_width.py:63)、[保存 log:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/probe_window_width.log:9)

除外・代替されているものは次のとおりです。

- state unlink 後の directory fsync と `apply_fold` return
- `_pending_spool_paths`
- 実際の `git add`。代わりに clean tree への `git status -- docs`
- staged fold を持つ index 上での diff。probe は clean index
- `.git` 内での message tempfile 作成・flush・fsync
- `git commit` 全体
- commit 後の HEAD／parent／ref／wave／clean／pending／declared-fold 検査

したがって定義された窓に対しては強く過小評価する方向ですが、`git status` が実 `git add` より遅い可能性もあるため、数学的な下限ですらありません。別々の3回中央値を足しても end-to-end 中央値にはなりません。

「96%」は不完全な小計に対する 2.694/2.821 です。commit と postcondition を加えれば分母が変わります。また「2つの HEAD」は findings にしか残っておらず、保存 log は `974207ae` の1本だけです。runner は [毎回同じ log を上書き](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/run.sh:9)するため、`9abd23da` の標本列は監査不能です。

**[real] 「land 1回あたり」も誤りです。**

fragment なしなら plan は [noop](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/spool_fold.py:1951) で、`apply_fold`・checker・fold commit の窓へ入りません。`already-landed + noop` もそのまま返ります。既存テストも [zero-fragment の1 commitだけ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/orchestrator/tests/test_dev_wave_land.py:2102)を固定しています。

成果物影響: rulings の値は「約2.82秒/land、96%」から「非 noop fold の precommit 部分について得た代替小計 2.82秒」へ変更し、露出回数は全 land 数でなく non-noop fold 数で数える必要があります。

## 4. [T-799] state の生成法と [T-766]

**[real] 「[T-766] が増やす state と同じ形」は成立しません。**

`leave_active_state` は plan 後に fragment を変え、[直接 `apply_fold`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/probe_t799.py:27)を呼びます。実装は全 target と全 GC を検証してから書込みへ進むため、この失敗は canonical mutation 前です。その後 probe 自身が fragment を戻して clean tree にしています。land の `_rollback_fold` は一度も通っていません。

[T-766] の正本は rollback の ref・index・path 復元失敗です。既存テストにも別々の形があります。

- ref CAS 失敗: HEAD と worktree を戻さず state を残す
- read-tree 失敗: ref は戻ったが index/worktree が残り state を残す
- path restore 例外: ref/index は戻ったが第三状態 path と state が残る

該当テストは [test_dev_wave_land.py:2650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/orchestrator/tests/test_dev_wave_land.py:2650) 以降です。これらでは land preflight、standalone resume、before/after 判定の結果が変わります。

ただし、state schema に HEAD／origin がないこと自体と、提示した clean pre-mutation stateで B1 が成功することは崩せません。

**[real] 推奨する「新 field は省略可能、有るときだけ照合」も既存 state を保護しません。**

[T-766] が既に残した旧 state は field なしのまま無照合で通ります。互換性は保てても、本件の既存リスクは閉じません。

成果物影響: recovery の受理集合を rollback phase別・旧schema別に定義し直す必要があり、旧 state を無条件受理するなら proof-chain 保証は「新規 state のみ」に縮小されます。

## 5. B1 の「誤った HEAD」

**[refuted] HEAD 不一致を受理するという事実は崩せません。**

state に HEAD がなく、resume が `_git_clean_preflight` を飛ばすことはコード上も log 上も明白です。

**[real] ただし測った B1 は、誤った結果を示していません。**

挟んだ変更は `base.txt` だけです。fold の全入力は同じなので、元 HEAD で再計画しても同じ ledger bytesになります。残る dirty tree は HEAD を動かさなくても standalone resume が必ず作るものであり、T-799 固有の追加実害ではありません。

また通常の協調 land だけでは、この異なる HEAD は作れません。land-land は共通 lockで直列化され、active state があって `main != tested_tip` なら停止します。B1 の直接 commit と C2 の直接 `git merge --ff-only` は、helper が明示的に境界外とする [同一UIDの非協調writer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/dev_wave_land.py:4)です。実運用でこの操作があるかの証拠はパッケージにありません。

成果物影響: Q2 のリスク説明を「通常 land で起きる誤 HEAD」から「非協調 main mutation 後にも resume を拒否しない」へ縮小しないと、不要な HEAD 完全一致で安全な recovery まで受理集合から落とします。

**[real] 親が測っていない、値を本当に変え得る経路があります。**

plan は archive worklog を読み T 番号を決めます。[入力読取り](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/spool_fold.py:1965)、[採番](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/spool_fold.py:2008)。しかし state が hash 束縛するのは「出力が変わる target」だけです。[target構築](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/spool_fold.py:2127)

したがって、plan target でない archive／phase 入力を変えると、target hash を通過しながら旧 T 採番・旧 carry を適用できます。また `tools/check_docs.py` の `WORKLOG_ROTATE_BYTES` も [plan 入力](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/spool_fold.py:1806)ですが state に束縛されません。これを変えるコード commit なら、B1 と同じ「canonical 無変更」でも正しい再計画とは rotation 結果が変わります。

成果物影響: T/D/F 採番、worklog carry、rotation archive 名・README 参照が変わり得ます。Q2 の本質は HEAD そのものより「plan 入力 closure と fold engine/config の未束縛」です。

運用境界内により近い未測定例は、rollback failure 後に同じ commit SHA を指す別の非 supervised wave が land を再投入するケースです。HEAD は同じままでも land origin／wave_ref の誤帰属を試せます。

## 6. C2 は欠陥か

**[refuted] 測定された C2 を機能欠陥とする解釈は成立しません。**

fragment は main に既に pending であり、wave B はその main commitを祖先として unrelated fileを1つ足しただけです。[probe_t799c.py:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/probe_t799c.py:31)

このケースでは、

- 採番・canonical 入力は変わらない
- fragment の receipt は正しい `wave-a` を保持する
- fold commit の parent は実際の wave B tipを記録する
- `verify_declared_fold_commit` も通る

ため、同じ pending fragment を現在の main 上で fold する正常動作です。「plan を計算した瞬間の HEAD」を記録せよという既存契約も [spool README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/docs/spool/README.md:104)にはありません。

「計算時 HEAD が receipt にない」は、成果物値・受理集合・参照の誤りを示せないため nit、または新しい監査要件です。実害を立てるなら、前節の target 外入力を変えて「再計画結果と resume 結果が違う」ことを測る必要があります。

## 7. B4「standalone resume は必ず残骸」

**[refuted] 現行コードの狭い条件では、反例を作れませんでした。**

「現行 producer が commit 前に残した non-noop state」「外部 commitなし」に限れば、成功した standalone は少なくとも FOLDED／canonical変更か fragment削除を行い、commitを作らないため tracked dirtを残します。この限定下では親の説明どおりです。

**[real] しかし裁定パッケージの普遍命題と、Q1(b) 選択後の主張は偽です。**

Q1(b) は state を postcondition 後まで残します。すると次の正規状態が新たに発生します。

1. 全 target=after、GC済み、stateあり
2. `git commit` は成功して HEAD が fold commit
3. postcondition中、または最後の state unlink前に process death

この状態で standalone resume は全 targetを `resumed` としてskipし、stateだけ削除します。HEAD/worktree/indexは既に cleanな fold commitなので、これは「成功して健全に終わる standalone resume」の反例です。

一方、同じ land request の再投入は既存 active recoveryを使えません。fold commit は tested wave tipでも audited commitでもないため、[ `_main_is_allowed`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/dev_wave_land.py:1256) で `stale-main` になります。つまり rulings の「次の land は既存 active_plan 経路にそのまま入る」「新しい recovery 機構は要らない」は誤りです。

Q2(b) で standalone を同時に閉じると、この唯一の健全な回復路も消えます。必要なのは、fold commit の parent・message・author・treeを検証して stateだけfinalizeする post-commit recoveryです。これは実質的に新しい phase／protocolです。

成果物影響: Q1(b)+Q2(b) のままでは、有効な fold commitを持つ crash stateが recovery受理集合から消え、main history上は正しい receipt／台帳を人手介入なしに確定できません。

## 8. 見落とされた分岐

**[real] process death 以外でも T-798 型残骸を作れます。**

通常例外後に rollback が成功すれば安全ですが、check_docs／stage／commit／postcondition の通常例外に、ref CAS・read-tree・path restore の失敗が重なると、state は既に消えています。例えば check_docs失敗後に ref CAS rollbackが失敗すれば、HEAD=wave tip、canonical after、GC済み、stateなしのまま `fold-rollback-failed` を返します。親の「発火条件は process death に限る」は二重故障を除外しすぎています。

成果物影響: T-798 の発火集合と recovery 表に「通常例外 + rollback failure」を加え、journalなし第三状態を受理／拒否する手順を定義する必要があります。

**[real] noop／already-landed を測っていません。**

- fresh/noop: 窓なし
- already-landed/noop: 窓なし
- already-landedだが pending fragmentあり: foldを実行するので窓あり
- active-state recovery: foldを再実行するので再び窓へ入り得る

成果物影響: exposure の分母と頻度推定が変わり、裁定レポートの「land回数比例」は使えません。

**[real] land／standalone の同時実行が無排他です。**

land-land は flock で直列化されます。一方 standalone CLI は [state読込みからapplyまで](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window/tools/spool_fold.py:2497)一切 land lockを取りません。二つの resume が同じ stateを読み、一方が unlinkした後でもう一方が `FileNotFoundError` になる、または land rollbackが standalone の成功変更を巻き戻す競合が可能です。fresh standalone同士なら、異なる plan/state の上書き競合もあります。

これは README の「fold は land lock内」と「中断後は同じコマンドで resume」の間にある実際の開口部です。

成果物影響: state消失、dirty tree、第三状態、成功報告後の巻戻しのいずれが残るかで ledger／receipt の受理集合が変わります。

## 裁定前に必須の追加測定

1. Q1(b) を模した state-retained landで、commit成功直後・各postcondition・final unlink前にkillし、同一land再投入とstandaloneの両方を測る。
2. [T-766] の ref CAS／read-tree／path restore／main-moved各残存stateから、land・standaloneを実行する。
3. state作成後に、archive worklog、phase3、`WORKLOG_ROTATE_BYTES`、fold engineを個別に変え、stored-plan resumeとfresh replanの採番・carry・rotation差を比較する。
4. land-land、land-standalone、standalone-standaloneのbarrier付き競合を測る。
5. 幅は実main相当のpost-fold treeで、実 `git add`・実commit・全postconditionを含むend-to-end標本として取り直す。plan規模、cold/warm cache、全sample、tree/status digestを保存する。
6. 同一SHA別waveを、通常branchとsupervised branchの両方で試す。

## 総括

- 親の実測のうち撤回・縮小すべき主張:

  - 「窓は約2.82秒、96%、land 1回ごと」は撤回。commit／postconditionを除く代替小計にすぎない。
  - 「[T-766] と同じ形」は撤回。probe は rollback failureを経ていないpre-mutation state。
  - 「C2 は帰属が壊れた欠陥」は縮小。測った unrelated descendant では成果物値も参照も正しい。
  - 「standalone resume は必ず残骸」「閉じても失うものなし」は撤回。Q1(b) の post-commit state が健全な反例になる。
  - 「Q1(b) は既存 active recoveryをそのまま使え、新機構不要」は撤回。fold-commit HEADを認識するfinalize recoveryが必要。
  - 「発火条件は process deathのみ」は縮小。通常例外とrollback failureの二重故障でも起きる。
  - P1 は「本番sourceの狭い順序を通した」に限定し、checker・branch・fixtureによる受理分岐の同一性は主張しない。

- 裁定を出す前に必ず追加測定すべき点:

  - post-commit／pre-finalize crash recovery
  - [T-766] rollback残存stateの全形
  - target外plan入力とfold config変更後の再計画差
  - land／standalone競合
  - commit・postcondition込みのend-to-end幅
  - 同一SHA別waveとsupervised／unsupervisedの受理差