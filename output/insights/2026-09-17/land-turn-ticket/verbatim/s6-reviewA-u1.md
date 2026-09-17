## 前提の検算

**判定：must-fix 4 件。現状の受入には反対します。** いずれも静的に反例が成立するという意味での **real** です。実走で再現したという意味ではありません。

指定資料を読み、指定 diff と現物の `git diff` が一致することを確認しました。現物は land 6,403 行、test 11,548 行です。以下は現物の行番号を使います。

- `land`：[tools/dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_land.py)
- `test`：[orchestrator/tests/test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/orchestrator/tests/test_dev_wave_land.py)
- `fold`：[tools/spool_fold.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/spool_fold.py)

ファイル変更、Git 状態変更、pytest・死亡 probe は行っていません。provenance 非ゼロの扱いは、依頼本文の訂正を正本として判定しました。

## 既存検査の保持 (a′)

**refuted／nit・修正不要：順番票によって、成功 payload の再取得後検査が省略されるという攻撃。**

`land:3118` の再取得 loop は、各回とも `_acquire_land_lock` を呼び、その成功時には `land:3244` の binding 検証を通ります。呼出し側には次が残っています。

| 境界 | 保持された検査 |
|---|---|
| initial | `_locked_preflight`、active state、cleanliness、heads、audited closure |
| provenance 後 | control 比較、fingerprint 比較 `5702`、完全 preflight、provenance receipt `5723` |
| acceptance | 完全検証と登録時 digest 比較 `5729`／`5738` |
| fold gate 後 | fingerprint 比較 `5986`、完全 preflight、active state 出現拒否、closure、pending 集合、gate receipt |
| gate 後の acceptance | 完全再検証と登録時 digest 比較 `6030`／`6036` |

反例候補「A の監査中に旧 driver B が main を進め、A が古い成功 receipt で ff」は fingerprint 不一致で拒否されます。main SHA が同じでも、index dirt や active state は別途検査されます。

ただし、**再検証で発生した retryable な拒否の分類が失われる問題は R4** として残ります。

## mutation 前の副作用 (b′)

**refuted／nit・修正不要：通常の順番待ち・監査・gate の拒否が、新たに main mutation を起こすという攻撃。**

順番 registry／journal の更新はありますが、これらは裁定で common flock 外の別面とされています。mutation 開始前の通常拒否から main ref・index・fold state を更新する新経路は確認しませんでした。

`_land_turn_mutating` は所有確認後、`_turn_append` → `_turn_write_all` → `fsync` を完了させてから戻ります。接続先も残っています。

- ff 前：`land:6200`
- apply 前：`land:5134`
- shape B の mark 前：`land:5319`
- shape B の finalize 前：`land:5348`

既存 `mutating` の再入では、binding／所有確認を再実施し、保存済み origin を保持します。

反例候補「ff 前の記録が永続化されるより先に merge が始まる」は、この呼出し順では成立しません。実 filesystem 上の crash durability は未実測です。

## 死亡票の完了照合

五つの観測分岐自体は、概ね裁定どおりです。

| 判定 | 現物 |
|---|---|
| 1：state 実在 | `land:3008`。他 key は RC27、同 key は既存 recovery 検証へ |
| 2：main_before に一致 | `3015`。`rolled-back` |
| 3：landing_tip・noop | `3017`。`done` |
| 4：finalize 済み | `3025`。既存 `verify_declared_fold_commit` を使用 |
| 5：その他 | `3039`。RC27、`mutating` 維持 |

判定 4 の `trusted_main_cutoff`、`landed_commits`、`wave_tip` は記録から復元されます。記録読取り時には audited digest も照合します。同 key・異なる landing_tip は `land:2901` で、新 ticket 作成・origin 上書きより前に拒否されます。

**R2 — real／must-fix：同じ死亡票の二重回収で journal が壊れる。**

根拠：[land:3047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_land.py:3047)、`3063`、`3083`。

具体的 schedule：

1. A が `mutating` record 番号 n を保存し、ff 前に死亡。state 不在、main は `main_before`。
2. B と C が、common flock 取得前に同じ entry と record n を読み取る。
3. B が common flock を取得し、A に `rolled-back` record n+1 を追記する。seq 保持なので registry の A entry は変わらない。
4. B の通常処理再開前に C が common flock を取得する。
5. C の entry 比較は一致する。最新 journal を検証し直さず、保存していた record n から、もう一つの n+1 を追記する。
6. `_turn_select` が journal を読み、連番不一致で拒否する。

**放置時の破損：registry が参照する journal に重複 record 番号が永続化され、以後の全登録・選出が失敗します。**

修正は、registry lock 内で最新の完全 record を再確認し、観測対象の番号・digest・phase が変わっていれば再追記しないこと。entry の一致だけでは不十分です。

**N1 — real／nit：自分自身の完了解消は `done` にならない。**

`land:3053` は、判定 4 で完了確認しても同 key なら `waiting` を追記します。finalize 後・終端前に死亡した A 自身が再入すると、その後の通常 preflight は main=C、landing_tip=L を stale-main と判定し得ます。完了済み seq が残ります。

main／fold の誤更新や通常 grant 停止には直結しないため nit とします。後続による解消だけでなく、同 key による完了解消の期待も明示すべきです。

## rc 別 seq 処理の対応表

`_finish_land_turn` は主に **rc・retryable・現在 phase・main_after・state 有無**で決定します。`status` と `release_safe` は判定に使っていません。

| 終端 | 実装の処理 | 対応 |
|---|---|---|
| RC0 | `done`、seq 削除、引渡し | 一致 |
| stale-main RC10、mutation 前 | `waiting`、seq 保持、引渡し | 一致 |
| 順番期限 RC11、mutation 前 | `waiting`、seq 保持 | 一致 |
| retryable 拒否、mutation 前 | `waiting`、seq 保持 | 一致。ただし R1／R4 で入力 flag が壊れる |
| 非 retryable 拒否、mutation 前 | `rejected`、seq 削除 | 一致 |
| RC26／31、main 復元・state 不在 | `rolled-back`、seq 保持、引渡し | 一致 |
| RC28／27／25、既存 `mutating` | `mutating` 維持、通常選出停止 | 一致 |
| finalize 失敗 RC30、既存 `mutating` | 同上 | 妥当 |
| その他の非成功、既存 `mutating` | 同上 | 保守的 |

`release_safe=True` だけで未解決 mutation を削除しない点は適切です。

ずれは **R1：非ゼロ provenance**、**R4：gate 後 acceptance の retryable 拒否**、および **N1：自己完了解消**です。

## 原子的引渡しと二重起動

**refuted／nit・修正不要：正常終端で grant 解放と次候補選出が別 registry 更新になるという攻撃。**

`land:2989` 以降で終端記録・FD close・必要なら seq 削除・grant 解放・`_turn_select` を行い、context 終了時の一回の rename で公開します。通常選出は生存 ticket の最小 seq、既存の生存 grant は維持します。

同 key 二重起動も `land:2897` の registry lock 内で拒否します。第二 ticket は作られません。R2 は死亡票回収の別問題です。

**R3 — real／must-fix：初回登録中の死亡で registry が永続的に起動不能になる。**

根拠：[land:2743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_land.py:2743)、`2911`、`2919`。

具体的 schedule：

1. 初利用で `registry.json` はない。
2. A が registry lock 内で最初の ticket を作成し、`waiting` を fsync する。
3. `_turn_save_registry` の rename 前に A が死亡する。
4. 次の B は「registry 不在、`.jsonl` 実在」を検出し、無条件で拒否する。
5. 元 A の再入も同じ拒否になる。

**放置時の破損：mutation 未開始の死亡だけで、共有 registry が全 request を恒久拒否する状態になります。**

ticket を作る前に空 registry を原子的・永続的に初期化するなど、正常 crash でこの曖昧状態を作らない順序が必要です。壊れた registry の無条件初期化を許す提案ではありません。

## 登録前提

**refuted／nit・修正不要：static 分割が互換 verdict を落とす、または固定入力の受理集合を狭めるという攻撃。**

`land:970` 以降に schema、authority、holder、tested-main／tip、argv、scheduler、env、fingerprint、blob／bytes、raw digest の検査が残っています。`non-attributable-only` と `child_rc==1` の分岐も維持されています。

bootstrap の locked-main 検査だけを `land:1190` に分け、完全 verifier から呼び直しています。

反例候補「bootstrap receipt 登録後に旧 driver が launcher を持つ main へ進める」は、lock 内 authority 検査または先行する既存検査で拒否されます。登録済みという理由で bootstrap authority が固定されることはありません。

ただし、gate 後に追加された完全検証の例外処理には R4 があります。

## 証拠保持と非ゼロ payload

runner は `land:4635` で一回だけ呼ばれます。成功 payload は再取得 loop の外側に保持され、期限切れでは RC11 と phase／turn 時間情報を返します。

**R1 — real／must-fix：非ゼロ provenance の既存分類が失われる。**

根拠：[land:4636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_land.py:4636)。既存分類は `land:3622`。

入力：checker が rc16、-9、-15 を返す。

現在は全て `release_safe=True`、`retryable_same_request=False` で即終端し、`_finish_land_turn` が seq を削除します。正しくは、rc1 のみ非 retryable、他の非ゼロは retryable です。

**放置時の破損：一時的な監査障害で registry の同一 request→seq 対応が削除され、再投入時の順位保持が失われます。**

即終端は維持し、既存 verifier と同じ rc 分類を共有すべきです。`test:9369`／`9375` の既存期待を変更して整合させてはいけません。

**R4 — real／must-fix：gate 後 acceptance 検証の retryable が非 retryable に変換される。**

根拠：[land:6030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_land.py:6030)、`6065`。receipt I/O の既存分類は `land:786`。

具体的 schedule：

1. 登録時・provenance 後の acceptance 検証は成功。
2. fold gate 後の追加再読で、一時的な receipt I/O エラーが発生。
3. `_verify_acceptance_receipt` が retryable な `_Reject` を投げる。
4. 汎用 `except (Exception, KeyboardInterrupt)` が捕捉し、KeyboardInterrupt でないため非 retryable の RC31 に変換する。

**放置時の破損：再試行可能な receipt 読取り障害で seq が削除され、registry の順位継承契約が壊れます。**

`_Reject` の分類を保持する処理が必要です。既存 `_FoldGateFailure` 自体の既定値・retryable 分類は変更されていません。

## 非接触

**refuted／nit・修正不要：無関係 child の除外が、自 wave や衝突 child まで除外するという攻撃。**

`land:1716` 以降は、protected 判定 → 非 protected の continue → 名前検査 → open → binding の順です。

保持されているもの：

- 自 wave の再 open と admin binding
- `protected_after != protected_before`
- handoff の名前集合
- `_CONTROL_CONTAINERS` 自体の保護
- protected child の observed identity

反転した五つの test の incoming は `wave.txt` または `base.txt` で、対象の alias、不正名、foreign child と非衝突です。`test:7603`／`7636` の差替え対象も foreign child で、自 wave ではありません。

`test:3740` 付近の cleanup race 正例と protected child 拒否例は追加されていますが、実走結果は未確認です。

## 順番票 file の安全条件

**refuted／nit・修正不要：通常の ticket／registry FD が子に漏れる、または registry lock 保持中に common flock を待つという攻撃。**

確認した条件：

| 条件 | 実装 |
|---|---|
| nofollow | ticket、registry lock、registry 読取りに適用 |
| inode・uid・nlink=1・0o022 | `_turn_file_binding` が既存 `_lock_metadata_is_safe` を使用 |
| directory binding | common と turn directory を再照合 |
| 生存 | 別 open file description の非 blocking flock |
| OSError | 死亡扱いにせず拒否 |
| registry 保存 | 一時 file → fsync → rename → directory fsync |
| 子への FD | 明示的 `pass_fds` は merge の common lock のみ |
| lock 順序 | 死亡観測の common 待機は registry context の外 |

反例候補「同名 ticket を別 inode に差し替えて mutation」は binding 検査で拒否されます。TTL・pid・mtime による生存判定はありません。

ただし、この安全な file 操作だけでは **R2 の古い record による再追記**と **R3 の初期化 crash**を防げません。共有 FS の実動作は未確認です。

## 所見一覧 (must-fix / nit、real / refuted / 未確認、file:line)

| ID | 分類 | file:line | 所見 |
|---|---|---|---|
| R1 | **must-fix／real** | `tools/dev_wave_land.py:4636` | 非ゼロ provenance を一律非 retryable にして seq を削除 |
| R2 | **must-fix／real** | `tools/dev_wave_land.py:3047`, `3063` | 二つの死亡票回収者が同じ record 番号を追記し、共有 journal を破壊 |
| R3 | **must-fix／real** | `tools/dev_wave_land.py:2743`, `2911` | 初回 registry 公開前の死亡で全登録が停止 |
| R4 | **must-fix／real** | `tools/dev_wave_land.py:6030`, `6065` | acceptance 再検証の retryable 例外を非 retryable に変換 |
| N1 | nit／real | `tools/dev_wave_land.py:3053` | 自己再入で finalize 済みを確認しても、完了済み seq が残り得る |
| N2 | nit／未確認 | `orchestrator/tests/test_dev_wave_land.py:3778` | 死亡観測 test は単独回収者。R2 の B／C 同時回収は被覆未確認 |
| N3 | nit／未確認 | `orchestrator/tests/test_dev_wave_land.py:3980` 付近 | scheduler・共有 FS・process 死亡の実動作、変異の専属帰属は未実測 |
| — | nit／refuted | `tools/dev_wave_land.py:3118`, `5702`, `5986` | 順番票による既存再検査の省略 |
| — | nit／refuted | `tools/dev_wave_land.py:2897`, `2997` | 正常経路の二重 ticket 作成、非原子的な引渡し |
| — | nit／refuted | `tools/dev_wave_land.py:1716` | 非接触変更による protected child 検査の脱落 |

## 総括

**R1〜R4 の修正が必要です。** 特に R2 と R3 は、main を変更しない死亡・回収処理から共有 registry を使用不能にします。

既存の common flock、成功 receipt の束縛、mutation 前記録、protected child 検査は維持されています。修正後は、二重死亡票回収・初回登録中の死亡・非 authoritative provenance・gate 後 receipt I/O 障害を反例どおりに検証してください。今回、テスト成功は申告しません。
