| 所見 | 判定 | 根拠と残件 |
|---|---|---|
| A1：生存子の停止・回収 | **partial** | T:1632–1667、4717–4737。通常経路は harness 内で完結し、N1 も統一。ただし `/proc` 読取例外で回収前に終了する穴が残る。 |
| A2：timeout 時の launcher 所有 | **partial** | T:1628–1632、4684–4714。登録済み launcher の停止対象漏れは修正。harness 強制終了後の回収は外部祖先に依存する。 |
| A3：M1 の kill 定義 | **closed** | s4-ruling:58、L:1851、1868、1984–1993。erratum は妥当。期待 node 集合と検査対象 field が変わらないため、この訂正自体に code 変更は不要。 |
| A4：rc 97・成果物欠落の観測 | **closed** | T:4582–4617、4671。rc と report を先に記録し、receipt／sidecar 欠落を `missing` として比較できる。 |
| A5：受入負荷での決定性 | **partial** | s4-ruling:60、focus-3.log:1、18、24。fix2 は実測された一時 unknown を処理したが、受入形の決定性確認と insight 条件表の完成は提示資料から確認できない。 |
| B1：共有 helper の変更 | **closed** | T:1124–1149、4673–4683。callback を撤去し、専用 helper 内で observe → rc 検査を実施。 |
| B2：timeout 時の所有・回収 | **partial** | A2 と同じ。PID 登録は改善だが、停止と回収の両方が保証されたわけではない。 |
| B3：N4 の固定3秒待機 | **closed** | T:1645–1663。先に生存子を kill し、回収完了なら即終了。毎回3秒を消費する構造は解消。 |

以下、T＝[test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2620-zombie-residual/orchestrator/tests/test_codex_worker_launch.py)、L＝[codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2620-zombie-residual/tools/codex_worker_launch.py)。行番号は現在の統合済みコード。静的検査のみ実施した。

## must-fix

**F1：harness の全 `/proc` 走査にも、fix2 の契機と同種の読取競争が残る。**

- **根拠：T:1635–1644。** `read_text` は PPID 判定より前で、捕捉するのは `FileNotFoundError` だけ。無関係な process の消滅による `ProcessLookupError`／その他の `OSError` では、SIGKILL・waitpid・JSON 出力へ到達しない。production 側は同種の例外を L:1732–1735 で処理している。
- **成果物への影響：** 残存数が正しくても baseline が環境依存で赤になり、養子回収も外部祖先に移るため、「fix 後は回収を所有できる」という裁定結論が成立しない。
- **是正案：** 消滅競争の ENOENT／ESRCH を処理し、それ以外の走査失敗でも cleanup を実行して構造化報告へ残す。走査例外を注入し、生存子・Z の回収完了まで確認する。

これは提示ログでの harness 障害の実測認定ではなく、コードから導出した未処理経路である。

**F2：外側 timeout では、回収責任を持つ harness が先に失われる。**

- **根拠：T:4675–4680、4701–4714。** `subprocess.run` の直接の子は harness。timeout 後の finally は登録 PID を kill して `/proc` 消滅を待つだけで、養子を reap できない。外部祖先が回収を保留する条件では、登録済み launcher も Z として残り得る。
- **成果物への影響：** 「timeout・receipt 不在でも同じ後始末が完了する」という裁定材料にはできず、後続走行への残存と teardown の赤が残る。
- **是正案：** timeout を harness への終了要求として伝え、harness が launcher と養子を停止・回収して応答する段階を設ける。launcher 停滞を注入し、元の timeout と cleanup 結果を両方保持して確認する。

PID ファイルは **Popen が戻り、T:1629–1631 の書込みが完了した後の launcher 停滞なら存在する**。ただし Popen と書込みは不可分ではない。書込み前の停止・書込み失敗まで「必ずある」とは言えない。裁定指定の PID 登録処置は実装済みだが、元所見の回収保証全体は閉じていない。

## should

**S1：決定性の結論は、期限ごとの失敗条件を付けて限定する。**

- **根拠：** 下表。focus-2.log:18 は **216 passed／11.61秒**、focus-3.log:18 は **216 passed／11.90秒**。両ログの1・24行は受入形でないと明記している。
- **成果物への影響：** 焦点走の緑を48 worker・3 shardでの決定性の証拠にすると、insight と裁定パッケージが実測範囲を超える。
- **是正案：** 条件表を insight に反映し、修正後の受入形 baseline と変異走を別々に記録する。

| 期限・窓 | fix 後も赤になる条件 |
|---|---|
| fake の PID／Z poll 各5秒 | T:1563–1581。期限確認時にも PID 登録／Z 化が済んでいなければ rc 66。N4 は二つの待機が直列。 |
| 正常系 `max_wall=10` 秒 | T:4568–4569。起動・I/O・二つの poll の累積で正常終了前に limit が発火し、`limit=None`／rc 0 の前提が崩れる。 |
| N2b `max_wall=3` 秒 | T:1557–1560。TERM 無視設定・子生成・PID 登録の readiness handshake がなく、準備前の limit 発火で期待する rc・残存数・回収 PID が崩れる。 |
| residual poll 0.5／1秒 | L:1745–1764、1845–1868。**期限を越えた走査の結果が `None` なら、そのまま final unknown を返す。** 一時 unknown が一度出たこと自体は fix2 後の失敗理由ではない。 |
| harness 回収3秒 | T:1652–1663。SIGKILL 後も子が waitable にならず、期限後の `waitpid` が0を返すと終了する。既に waitable なら、期限後でも先に回収するため「harness の再開が遅れただけ」で回収を飛ばす旧構造は解消。 |
| finally の3秒 | T:4706–4714。外部祖先の回収保留、停止処理の遅延などで登録 PID が残れば赤。全 PID 共通の3秒であり、PID ごとに3秒ではない。 |
| 外側20秒 | T:4675–4677。起動・走査・launcher 終了・harness 回収の累積超過で timeout。F2 の経路へ入る。 |

N3 は別に checker 呼出し各10秒を持つ（T:4743–4752）。上表の harness 経路には入らない。

## nit

**N1：数値 PID の再利用窓は残るが、提示資料には発生証拠がない。**

- **根拠：T:4694–4705。** 通常成功時にも、既に回収した PID 番号へ再度 SIGKILL を送る。tmp_path は PID ファイルの取り違えを防ぐが、OS の PID 再利用を防がない。20秒程度の短い窓でも確率をゼロとは評価できない。
- **成果物への影響：** 現在の負例表・実測結論が変わった証拠はないため nit。再利用が起きれば別 process を停止し、後続走行を汚染し得る。
- **是正案：** 将来強化するなら、回収済み PID を再 kill せず、所有中に取得した pidfd などで対象を保持する。start-time 照合だけでは照合後の競争は残る。

**N2：単回の養子列挙を、任意の子孫木の回収保証へ一般化しない。**

- **根拠：T:1635–1664。** 養子が生存する孫を持つ場合、養子を kill してから新しく引き取った孫は kill 対象一覧にない。`unreaped` も最初の `adoptees` だけから作る。
- **成果物への影響：** 今回の fake の残存子は sleep または即 exit であり（T:1389–1399、1570–1572）、5本の負例表は変わらないため nit。
- **是正案：** 今回の限定された process 構造を明記する。一般化する場合だけ、再列挙・停止・回収を繰り返す。

## 検算・閉じた点

**harness の正常経路の順序は妥当。** launcher を T:1632 で回収してから養子を列挙するため、元の launcher 自身は一覧に混ざらない。生存する直系養子の PID は、この harness が reap するまでは再利用されない。

`fields[1]` が PPID なのも正しい。Linux の出力順は `pid (comm) state ppid pgid ...` なので、末尾の `)` より後では添字0が state、1が PPID、2が PGID になる。[Linux `do_task_stat`](https://github.com/torvalds/linux/blob/master/fs/proc/array.c)

**fix2 は final unknown の検出能力を落としていない。** T:4610–4615 が正規化するのは履歴集合だけで、T:4620、4629–4632 は receipt residual、`final_count`、`final_unknown_source=None`、`proc_stat_malformed=False` を固定している。最終値が `None`、残存数が違う、または別の unknown source を含む場合は赤になる。失うのは、許容した読取エラーが途中にあったかどうかの区別であり、元 sidecar 自体は変更しない。

**親の機序説明は、例外経路について正しい。ただし実際の errno まではログから確定しない。**

1. L:1715、1732–1735：`read_text` の `OSError` → `proc_stat_read_error` → `None`。
2. L:1724–1731：ENOENT は別扱い。path が消えていれば continue、存在すれば unknown。
3. L:1762–1764：`None` は0ではないため、期限前なら再 poll。
4. L:606–608：一度見た source を集合へ保持。
5. L:2431–2433：最終 residual が非 `None` なら final unknown を解除。

baseline stdout:112、222 は、最終数1／2・final unknownなし・履歴だけ非空という結果を裏付ける。ただし source 名だけでは ESRCH と他の読取エラーを区別できず、「無関係 process の消滅」はコードと整合する機序の説明である。

**`proc_stat_malformed=False` を同様に緩める根拠はない。** 空文字列なら L:1718–1721 が malformed を立てる。しかし、確認した upstream Linux では task 消滅時に `proc_single_show` が `-ESRCH` を返し、task を取得できた場合は stat 本文を生成する。通常の消滅競争から「成功した読取が空文字列になる」とする経路は確認できない。これは稼働ノードの kernel 差分まで検証した主張ではない。[Linux `proc_single_show`](https://github.com/torvalds/linux/blob/master/fs/proc/base.c)、[stat 生成処理](https://github.com/torvalds/linux/blob/master/fs/proc/array.c)

**A3 の erratum は局所変異ログとも一致する。**

| M1 対象 | 実際に変わる値 | 局所ログ根拠 |
|---|---|---|
| N2a | residual 1→0、verified false→true、accepted false→true、rc 1→0 | o19-m1.pytest.log:119–127 |
| N2b | residual 1→0、verified false→true。受理は不変 | 同:300–303 |
| N4 | residual 2→1。verified・受理は不変 | 同:474–476 |

同ログ:742 は **3 failed、2 passed、211 deselected**。したがって「受理集合の変化」と「構造化シグナルの変化」を分ける訂正は妥当。ただし、この fix1 局所走は fix2 後の変異本走を代替しない。

## 総括

**NO-GO — fix2 の正規化と M1 erratum は妥当だが、harness の読取例外時と外側 timeout 時の回収責任が未完結で、A1・A2・B2 は partial。**