## 前提の検算

指定された必読資料、780 行の diff、適用後の実装・関連テストを確認しました。通常の起動手順は単独段 dispatch の例外により省略しています。ファイル変更、Git 状態変更、pytest 実行は行っていません。

「131 passed / 8.0 秒」は親から提供された結果であり、本レビューの実測ではありません。以下の **real はコード上で成立する反例**を意味し、実行再現とは区別します。

結論は **must-fix 1 件**です。通常の対象限定削除と部分削除 recovery は成立していますが、preflight 後の index 差替えを新しい削除対象として受け入れる穴があります。

## 他 wave 非削除の反例

**refuted / nit：名前衝突・複数一致だけで他 admin を削除する。**

`tools/dev_wave_cleanup.py:613,644,1137` は basename ではなく backpointer を使います。

- `foo` が対象、`foo1` が別 wave を指す場合、対象は `foo` のみ。
- 両方が対象 wave を指す場合、一意性検査で拒否。
- 通常経路で一致が 0 件なら拒否。recovery 時だけ、journal と inode の束縛を使って backpointer 欠損を許容します。
- admin の別 inode 差替え・symlink 化・別 common、binding file の inode／bytes 変更は `:803,831,838,866,906` で拒否します。
- `locked`、`index.lock`、`HEAD.lock` の再出現は snapshot 検査で拒否します（`:773`）。

**real / must-fix：preflight 後の index 変更を削除対象へ取り込む。**

根拠：[dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_cleanup.py:844)、同 `:905`。

具体的な入力・順序：

1. state `c`：wave directory は不在、admin は detached、HEAD と branch は main に到達可能。
2. `_bind_admin` が index を含む snapshot を取得する。
3. 別 process が対象 admin の index を更新し、main に含まれない blob を stage する。更新を完了し、`index.lock` は残さない。HEAD・reflog・backpointer は不変。
4. `_recheck_admin` は更新後の index を新しい snapshot として採用する。
5. index を journal に保存して削除し、最後に journal 自体も削除する。

保持している preflight snapshot は `gitdir` と `commondir` だけです。index の bytes／inode が変わっても、以後安定していれば通ります。Git の index 更新は、この directory flock と競合しません。

**放置時の成果物破壊：registry 内の更新された index と、その staged 内容への参照が削除され、journal も消えるため、未保存作業を失います。**

state `c` では preflight snapshot の維持、live 経路では正規の detach 等を終えた安全確認時点との比較が必要です。index の bytes 変更・同内容別 inode 差替えを、最初の `_recheck_admin` 前に注入する負例が不足しています。

**未確認 / nit：非協調 writer に対する syscall 間の完全保護。**

`:939–941` の読取り後・unlink 前に entry を差し替える窓、`:983–984` の照合後・rmdir 前に directory を差し替える窓は残ります。FD 相対操作は親 directory を固定しますが、entry の条件付き削除ではありません。この窓で他 wave の有効な成果物を壊す実行再現は未確認です。無条件の race-free 保証までは認定しません。

## journal の安全性

**refuted / nit：別 wave の journal をそのまま読み、誤 recovery する。**

`tools/dev_wave_cleanup.py:797,859,831,838` により、名前の SHA-256 に加えて wave・branch・tested tip・common、directory inode、backpointer を照合します。例えば wave B の journal を wave A の名前へコピーしても、本文の wave 不一致で拒否します。

作成は `O_EXCL | O_NOFOLLOW`、mode 指定 `0o600`（`:960`）。読取りは regular file・nlink 1・読取り中の安定性を確認し、さらに uid と group/other 権限を検査します（`:750,855`）。ただし読取り時に「正確に 0600」を要求しているわけではありません。

**real / nit：journal 書込み中の死亡で、自動再入できない残骸が残る。**

反例：`:960` の作成成功直後、`:963–965` の書込み・fsync 完了前に死亡。空または途中の JSON が最終名で残ります。次回は `:858` で拒否し、通常経路へ戻れません。live 経路では wave directory は既に撤去済みです。

追加の誤削除には進まないため、安全性破壊ではなく再入性の欠落として nit とします。完全な journal を公開する手順と、その前の残骸を区別できる設計が望まれます。

**real / nit：容量・読取りコストに上限がない。**

`:789,958` は index を含む全 file を hex 化します。親 worktree の index は read-only の `stat` 実測で **4,597,918 bytes**。index 部分だけで JSON 内では **9,195,836 文字**になります。snapshot は削除中にも繰り返し全体を読みます。巨大 index／多数 entry の負荷は未測定です。

**refuted / nit：journal の存在だけで land の指定検査が拒否する。**

次の経路に新 journal を列挙・解釈する処理はありません。

- `tools/dev_wave_land.py:1426`：shallow、grafts、replace refs。
- `:1450`：Git config の指定項目。
- `:1739`：handoff と worktree container。
- `:3460`：`git worktree list --porcelain`。

journal は `common/worktrees` の外です。通常の設定では Git の worktree 登録にはなりません。admin 部分撤去による porcelain の変化と、journal 自体の影響は分ける必要があります。

## partial removal と再入

**refuted / nit：HEAD／gitdir／logs の欠損を、残存物未確認のまま完了扱いする。**

`tools/dev_wave_cleanup.py:883,909` は、現在の entry が journal snapshot の部分集合であることを要求します。

例えば HEAD と gitdir が消え、index と空の logs directory が残る場合：

- 消えた entry は許容。
- 残る directory／file の種類・inode は一致が必要。
- 残る file の bytes も一致が必要。
- 新規 entry、lock、symlink は拒否。
- HEAD・reflog の安全性は journal 内の元 snapshot で再検査。

その後、**現在残っている entry** を撤去し、rmdir と record 不在確認を通して初めて branch 削除へ進みます（`:981–987,1254`）。空 snapshot だけで成功する構造ではありません。

porcelain が record を返す場合も返さない場合も、journal があれば synthetic record で state `c` に入ります（`:1055`）。ただし、その前の `_worktree_records` 自体がエラーになる状態は recovery に入れず拒否です。

**refuted / nit：synthetic record が branch safety 等を省略する。**

`:1107,1110,1118,1134,1141` に他 holder、commit 存在、tested ancestry、branch ancestry／reflog、journal 内 HEAD reflog の検査が残ります。occupancy を省くのは wave path 不在を要求する経路で、既存 stale 経路と同様です。

**real / nit：死亡位置の網羅性は不足。**

実テストは HEAD・gitdir・admin directory の撤去後を対象とします。logs/HEAD 撤去直後、journal 書込み途中、journal unlink 失敗は対象外です。これらの実 Git 出力を含む結果は未確認です。

## fail-closed の保持

**refuted / nit：admin 撤去の partial error 後も branch 削除へ進む。**

`tools/dev_wave_cleanup.py:1273` が mutation 全体の例外・割込みを partial として終了させます。branch 削除は admin 撤去・record 不在確認の後です。

具体例：

- `_remove_admin_entries` の途中で unlink が失敗：journal を保持して終了。
- 未知の entry が増える：subset 検査で終了。
- 最終 rmdir 時に非空になる：rmdir が失敗して終了。
- admin 撤去後、journal unlink が失敗：journal を保持して終了し、次回は admin 不在の recovery が可能。
- journal unlink 後の fsync が失敗：branch は残り、次回は通常の state `d` で処理可能。

ただし、残存 entry が変更されている場合の再入は意図どおり拒否です。「journal が残れば必ず再入成功」ではありません。

## _directory_identity と親環境

実測結果：

```text
readlink -f /work/1/SFC/tanab/izanagi
→ /work/1/SFC/tanab/izanagi

readlink -f /work/SFC/tanab/izanagi
→ /work/1/SFC/tanab/izanagi
```

`/work/SFC` は `/work/1/SFC` への symlink です。現在の worktree の `.git` は `/work/1/SFC/tanab/izanagi/.git/worktrees/dev-wave-land-turn-ticket` を指しています。

**refuted / nit：今回の親 worktree の正常な絶対 gitdir を誤拒否する。**

この binding は `tools/dev_wave_cleanup.py:387` の比較で変わりません。`.codex/worktrees`／`dev-wave-jobs` という配置名自体にも依存しません。

**real / nit：Git が解決できる非 canonical binding の受理は狭まる。**

例えば canonical な wave path 内の `.git` が `/work/SFC/.../.git/worktrees/foo` を指す場合、新検査は拒否します。`..` を含む相対 gitdir も同様です。旧実装は resolve 後に検査していました。

なお CLI 引数そのものに symlink component を使う入力は、既存の `:187,201` ですでに拒否されます。今回追加された差は `.git` 内容側です。成果物を壊す反例ではないため nit とします。

## flock と同時起動

**refuted / nit：admin が存在する同 wave 二重起動を止められない。**

`tools/dev_wave_cleanup.py:816` で同じ inode を別 open した cleanup 同士は競合します。取得失敗は preflight の例外処理に入り、mutation 前に拒否されます。`EWOULDBLOCK` 以外の OSError も続行せず拒否します。成功した FD は `ExitStack` により invocation 終了まで保持されます。

**real / nit：admin 消失後は invocation 全体の排他にならない。**

反例：A が `:984` で admin を消し、journal 削除前に停止。B は `:811` で `admin_fd=None` として入り、flock を取得せず recovery を進められます。両者の journal 読取り／unlink が競合し、一方が partial になる schedule は成立します。

同様に journal 消失後の state `d` には admin lock がありません。他 wave の誤削除はこの二重起動だけでは導けませんが、「同 wave の全 cleanup を直列化する lock」という説明はできません。実 concurrency test はありません。

## test の代表性と M10

**real / nit：他 admin 保持は実物の bytes・inode を検査しているが、branch は SHA のみ。**

`orchestrator/tests/test_dev_wave_cleanup.py:1072,1089` は実 Git registry に live／stale の他 wave を作り、admin 全体の dev・inode・file bytes を比較します。一方、branch は `:1086` の SHA 比較だけで、ref／reflog の bytes・inode 保持までは検査していません。live worktree 内容も directory 存在確認までです。

**refuted / nit：partial-removal test は削除を stub しているだけ。**

`:1112,1118` は実 unlink／rmdir を先に実行し、その直後に `KeyboardInterrupt` を注入します。実 registry に部分削除状態を作り、branch 残存と他 admin 不変、再入結果を検査します。

ただし process の強制終了ではなく、Python の例外処理と `ExitStack` が走る割込みです。また `admin-directory` ケースの tamper 3 種は、どれも directory 再作成に帰着します（`:1132`）。

**real / nit：提示された M10 anchor の単純置換では、保持 assertion より argv 禁止で先に止まる。**

author の anchor `tools/dev_wave_cleanup.py:1249` を `_must_git(..., "worktree", "prune", "--expire=now")` に置き換えると、`:208` の allowlist が拒否します。対象 test は `:1081` の成功 assertion で落ち、`:1085` の他 admin 保持比較まで到達しません。

したがって、この置換の赤だけでは「他 wave admin 保持によって M10 を殺した」と帰属できません。実 prune へ到達する変異を明示し、stale parameter の保持 assertion が失敗する結果を確認する必要があります。M10 の KILLED は本レビューでは未認定です。

## 所見一覧 (must-fix / nit、real / refuted / 未確認、file:line)

| ID | 分類 | 状態 | 箇所 | 所見 |
|---|---|---|---|---|
| A1 | **must-fix** | **real** | `tools/dev_wave_cleanup.py:844,905` | preflight 後の更新 index を取り込み、staged 内容への参照を削除する |
| A2 | nit | real | `tools/dev_wave_cleanup.py:960,858` | journal 作成途中の死亡で再入不能 |
| A3 | nit | real | `tools/dev_wave_cleanup.py:789,958` | 全 file hex 化と反復 snapshot の容量・負荷に上限なし |
| A4 | nit | real | `tools/dev_wave_cleanup.py:811,984` | admin 消失後は同 wave invocation の排他なし |
| A5 | nit | real | `tools/dev_wave_cleanup.py:387` | 非 canonical な有効 gitdir binding の受理が狭まる |
| A6 | nit | real | `orchestrator/tests/test_dev_wave_cleanup.py:1086` | 他 branch の bytes・inode 保持は未検査 |
| A7 | nit | real | `orchestrator/tests/test_dev_wave_cleanup.py:1095` | logs／journal 境界の死亡注入なし |
| A8 | nit | real | `tools/dev_wave_cleanup.py:208,1249` | 単純 M10 は argv 禁止で先に停止 |
| A9 | nit | 未確認 | `tools/dev_wave_cleanup.py:939,983` | 最終照合と削除 syscall 間の非協調差替え |
| R1 | nit | refuted | `tools/dev_wave_cleanup.py:613,1137` | 名前衝突・複数一致だけで他 admin を削除 |
| R2 | nit | refuted | `tools/dev_wave_cleanup.py:859,1134` | 他 wave journal の単純流用／branch safety 省略 |
| R3 | nit | refuted | `tools/dev_wave_cleanup.py:883,1273` | 残存物未確認の完了／partial 後の branch 削除 |
| R4 | nit | refuted | `tools/dev_wave_land.py:1426,1450,1739,3460` | journal 存在だけによる指定 control-plane 検査の拒否 |

## 総括

**A1 の修正が必要です。** 他 wave の通常の admin を対象限定で保持する構造、残存物を照合した recovery、partial error 後の branch 削除停止は確認できました。

journal 作成途中の死亡、admin 消失後の二重起動、M10 の帰属は追加確認が必要です。完全非接触化・手動 cleanup 手順・land 側変更は must-fix に含めていません。
