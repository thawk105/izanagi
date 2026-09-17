## 変更面

**S1〜S3 の範囲で実装可能。ただし P4 の「生存確認だけで決定的な中断テストになる」は修正が必要です。** 以下は静的検査による plan で、実装・テスト実走は行っていません。新規ファイルの行番号は配置目安です。

| file:line | 変更内容・理由 |
|---|---|
| `tools/cleanup_remove_dirs.py:1` 新規 | 固定 argv の directory 撤去 launcher。名称は採用する。branch や metadata も消す tool と誤認しにくい |
| 同 `:30` | 引数・path 検証。全件検証後にのみ起動する |
| 同 `:110` | signal 状態、子の起動、PGID 検査、有界な取消処理 |
| 同 `:210` | 終了・不在確認、4 値判定、JSON 出力、rc 集約 |
| `orchestrator/tests/test_cleanup_remove_dirs.py:1` 新規 | 実 subprocess による正例・負例、限定した ptrace 同期 fixture、自走 harness |
| `.claude/commands/cleanup-branches.md:56` | 重複する説明を 19 bytes 削減 |
| 同 `:58` | §3 手順 3 を launcher 呼び出しと rc 契約へ差し替え |
| `tools/check_docs.py:752` | whole-file SHA pin 更新 |
| `orchestrator/tests/test_check_docs.py:580`、`:627` | SHA pin と synthetic command を更新 |
| 同 `:9844` | 本文 byte 数の pin と超過 fixture の作り方を更新 |

`tools/dev_wave_cleanup.py:869` の同一 process 内 `shutil.rmtree` は変更しません。overlay skill、削除述語・閾値・評価順も変更対象外です。

## launcher 設計

### argv

```text
python3 tools/cleanup_remove_dirs.py [--timeout-seconds SECONDS] -- /absolute/a /absolute/b ...
```

- `--` は必須。以後は全て path。
- `--timeout-seconds` は省略可能・一度だけ・正の有限数。既定 **3600 秒**、各子の起動時刻から個別に測る。
- 3600 秒は現行の「各長い timeout」と brief の guard probe に合わせた運用上の初期値。性能実測で十分性を証明した値ではない。
- `--json` は設けない。stdout は常に JSON Lines。
- 未知 option、重複 option、欠けた値、非数・NaN・無限・0 以下、`--` 欠落、path ゼロは **64**。

path 検証も全て **64**、起動前に全件完了させる。

1. 空文字・NUL を拒否。
2. 絶対 path に限定。`/`、`//` 始まり、`.`・`..`、重複 slash、末尾 slash を拒否し、正規化で対象を変更しない。
3. 各構成要素を `lstat`。途中を含む symlink、不在、調査不能を拒否。
4. 最終要素は実在 directory。regular file 等を拒否。
5. `realpath` と指定 path の一致を確認。
6. 重複・包含関係を component 単位で拒否。文字列 prefix 比較にしない。
7. 実 cwd を取得し、対象自身・対象配下なら拒否。cwd を確定できない場合も拒否。

所有権・merge・占有の判定は既存 §1〜§3 が担当する。launcher はその代替 gate を追加しない。

### 起動・待機

```python
subprocess.Popen(
    ["rm", "-rf", "--", path],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
```

`start_new_session`、`preexec_fn`、`shell` は渡さない。1 path＝1 子とし、前の子の終了を待たず次を起動する。

起動直後、**poll/wait で reap する前に** `os.getpgid(child.pid) == os.getpgrp()` を確認する。

- 一致：通常の待機対象へ。
- 不一致：当該 path は `unknown / pgid-mismatch`。以後の起動を止め、生存子全てへ TERM → 有界待機 → rc 2。
- PGID 取得失敗：成功を推測せず `unknown`、同様に停止。

PIPE は全子について同時に drain する。逐次 `wait()` して stderr の満杯で停止する構成にしない。診断は各 stream の先頭一定量だけ保持し、超過分も drain して破棄する。

### signal と有界な停止

SIGTERM/SIGINT handler は**最初の signal 番号と取消要求を記録するだけ**にする。転送・待機は handler が要求した通常制御フローで行う。

handler 内では `wait`、`communicate`、JSON 出力、ロック取得、例外送出、子一覧の変更を行わない。二重 signal は取消要求を維持し、停止期限を延長しない。

通常フローでは：

1. 新しい子の起動を止める。
2. 登録済みの生存子へ受け取った同じ signal を送る。`killpg` は使わず、共有 group 内の無関係な process を巻き込まない。
3. 全子共通の猶予 **5 秒**で drain・wait。
4. 残存子へ SIGKILL、さらに **1 秒**待つ。
5. reap できない子は `unknown` とし、生存未確認 PID を報告、rc 2。

これは削除の再試行ではなく取消の終端処理です。TERM だけで必ず有界回収できるとはしません。

handler が `Popen` 中に発火しても例外を投げないため、戻った子を登録してから取消できる。取消フラグを各起動前後・最終集約前にも確認します。

### 判定表

結果は全件 `unknown / not-started` で初期化し、確認できたものだけ更新する。

| 判定 | 到達経路 |
|---|---|
| `removed` | PGID 一致、取消・timeout なし、子 rc 0、撤去後の不在確認成功の全条件成立 |
| `failed` | 通常終了 rc > 0、または rc 0 でも path が残存 |
| `interrupted` | launcher が TERM/INT を受信して取消対象になった／子 rc < 0／timeout。取消で未起動になった path も含む |
| `unknown` | spawn 失敗、PGID 不一致・取得失敗、wait/poll/drain の OSError、signal 送信失敗、停止後も終了未確認、不在確認不能、内部例外、異常停止で未起動 |

補足：

- **負の returncode は `failed` より先に判定**する。
- timeout では TERM を送り、同じ停止手順へ。回収成功なら `interrupted`、終了確認不能なら `unknown`。
- `ProcessLookupError` は即成功にせず、wait で終了状態を確認する。
- wait 中の OSError は `unknown`。取消が既に発生していても、終了状態不明を優先する。
- `lexists(False)` だけでは不在の十分な証拠にならない。`lexists` は一部の OSError を False にするため、追加の `lstat` で ENOENT を確認する。EACCES 等は `unknown`。
- 取消前に確定済みの `removed` は保持する。ただし launcher が signal を受信した実行全体を rc 0 に戻さない。
- 判定時点以後の外部からの path 再作成まで防ぐものではない。

### rc

| rc | 条件 |
|---:|---|
| 0 | 対象が 1 件以上あり、件数一致、全件 `removed`、実行全体の取消・内部障害なし |
| 1 | `failed` があり、`interrupted`・`unknown`・実行全体の取消なし |
| 2 | `interrupted` / `unknown`、または実行全体の取消・出力障害あり |
| 64 | 起動前の argv/path 検証違反 |

rc 0 は最後の一箇所だけで返す。空集合への `all()`、早期 return、例外処理から 0 に到達させない。

### 出力

正常に受理した入力について、入力順に **1 path 1 行＋総括 1 行**。

```json
{"type":"path","path":"/absolute/a","status":"removed","returncode":0,"reason":"absent"}
{"type":"summary","total":1,"removed":1,"failed":0,"interrupted":0,"unknown":0,"cancel_signal":null,"rc":0}
```

path 行には必要に応じ PID・観測 PGID・親 PGID を含める。診断本文と捕捉した子 stderr/stdout は、path を識別できる形で launcher の stderr へ出す。stdout に progress や生の子出力を混ぜない。

usage は stdout を空にし、stderr に理由と usage、rc 64。出力不能・総括欠落は成功扱いしない。

### やらないこと

prune、detach、branch 削除、撤去再試行、常駐監視、任意 command、汎用 supervisor、`PR_SET_PDEATHSIG` は実装しない。

docstring には次を明記する：

> 同じ process group でも、launcher PID だけへの SIGKILL は子へ伝播しない。SIGKILL は handler で捕捉できず、本 tool はその場合の子停止・JSON 出力を保証しない。PR_SET_PDEATHSIG は本 scope 外。

「PDEATHSIG 自体が親の SIGKILL に対応できない」という意味には書きません。

## test 設計

新規 `orchestrator/tests/test_cleanup_remove_dirs.py`。以下の行番号は配置目安です。

### fixture

| 配置 | fixture/helper |
|---|---|
| `:25` | `two_dirs(tmp_path)`：独立した 2 directory と sentinel |
| `:45` | `_launch()`：実 CLI を subprocess 起動。cwd は対象外。固定した実 `rm` を使用 |
| `:65` | `_read_results()`：行数・path 一意性・総括件数・rc 一致を検証 |
| `:90` | `traced_launcher`：実 launcher と実 rm を削除開始前に同期する Linux ptrace fixture |
| `:210` | `unwritable_parent`：親を chmod 500、finally で権限復旧 |

### 中断負例の推奨案

**(e) ptrace の exec-event stop で実 `rm` を削除開始前に止める案を推奨します。** product 側に test seam は追加しません。

1. test 自身を tracer とし、launcher の最初の exec stop から fork/vfork/clone/exec イベントを追う。
2. launcher は通常実行を進め、各 `rm` を exec-event stop に保持する。実 `rm` はまだ削除命令を実行していない。
3. `/proc/<launcher>/task/*/children` と捕捉 PID を照合し、`os.getpgid(rm_pid) == os.getpgid(launcher_pid)` を確認。
4. **launcher PID だけ**へ TERM を送る。
5. rm を再開し、signal-delivery stop で TERM を捕捉。`PTRACE_GETSIGINFO` の送信元 PID が launcher であることも検査する。
6. 捕捉した TERM を抑制せず、そのまま配送して終了させる。
7. launcher rc 2、path 行 `interrupted`、子 returncode `-SIGTERM`、対象 sentinel 残存を検証する。

削除開始前の kernel stop を同期点にするため、ファイル数や scheduler の速さに依存しません。signal 転送を削る変異では、TERM の配送観測が成立せず赤になります。後段の SIGKILL だけで test が緑になることも防げます。

fixture は syscall の返り値・argv・判定・signal を差し替えず、進行を同期するだけに限定します。全ての待機に期限を設け、finally で所有 PID を停止・回収します。

**未確認事項：ptrace が親の実行環境で許可されること。** 能力不足は明示 skip として集計し、その実行を中断契約の受入成功には数えません。親の実測で不成立なら段 4 で同期方法を再判断します。

候補比較：

| 候補 | 判断 |
|---|---|
| (a) 数万 file | 確率的に遅くなるだけ。決定性なし、生成負荷も大きい |
| (b) chmod | `failed` の test 用。中断を証明しない |
| (c) `/proc` 生存確認後 TERM | 観測から送信までに完了できるため不十分 |
| (d) FIFO / 深い木 | rm は FIFO の内容を読まない。深さも停止の同期点にならない |
| (e) exec-event stop | 実機構を置換せず、削除前に停止を保証できる |

### node

| 配置 | node と主張 |
|---|---|
| `:240` | `test_two_dirs_removed_in_parallel_same_pgid`：2 子を同時に exec stop に保持できること、両 PGID 一致を確認後に解放。rc 0、両 path 不在、両 `removed` |
| `:285` | `test_launcher_signal_is_forwarded_before_removal[TERM/INT]`：上記の最重要負例 |
| `:340` | `test_timeout_is_interrupted`：実 rm を保持し、実 CLI timeout を発火。rc 2、`interrupted`、残存 |
| `:375` | `test_child_signal_exit_is_interrupted`：保持中の実 rm だけへ signal。負の returncode を確認 |
| `:405` | `test_failed_path_does_not_hide_other_removal`：chmod 500 の親配下と通常 path。rc 1、`failed` と `removed` |
| `:445` | `test_usage_rejects_paths_without_removal[...]`：入れ子・重複・相対・不在・symlink・中間 symlink・非 directory・root・不正表記・ゼロ件 |
| `:490` | `test_usage_rejects_cwd_inside_target[exact/descendant]`：cwd を subprocess の実 cwd として指定、rc 64 |
| `:520` | `test_usage_rejects_invalid_options[...]`：timeout 不正・重複・未知 option・区切り欠落 |
| `:555` | `test_zero_returncode_with_existing_path_is_failed`：実判定関数を実在 path と rc 0 で直接呼ぶ。判定関数の置換なし |
| `:580` | `test_nonzero_returncode_with_absent_path_is_failed`：rc > 0 を残存検査から独立に検証 |
| `:605` | `test_summary_never_succeeds_for_incomplete_results`：空集合・未確定・取消・混合結果の実集約関数を検証 |
| 末尾 | `if __name__ == "__main__": sys.exit(pytest.main([__file__]))` |

chmod test は `os.geteuid() == 0` なら理由付き skip。root で chmod が効く前提の偽緑を避けます。権限回避 capability のある環境でも、この負例が成立したか確認します。

自走 harness は `test_dev_wave_cleanup.py:1384` の方式をそのまま採用し、allowlist は変更しません。

## docs 文案と byte 勘定

`.claude/commands/cleanup-branches.md:58` の手順 3 を次へ差し替えます。

```markdown
3. dir 撤去は `python3 tools/cleanup_remove_dirs.py -- <絶対path>...`。相互非包含のみ並列。
   子は親と同じ PGID、TERM/INT 転送。rc0 (全件 removed) 以外・不明は停止。
   detach・branch 削除・prune は直列。rc0 後 `git worktree prune --dry-run --verbose` の
   全候補＝今回所有確認済み対象なら `git worktree prune`。余分・不明候補時は real prune せず引渡し
```

D782 の削減を先に適用し、同 `:56` の次の補足を削ります。

```text
 (branch を解放)
```

`checkout --detach` と §0 の branch 解放説明に重複する補足であり、命令・条件は残ります。

| 項目 | UTF-8 bytes |
|---|---:|
| 現行全文 | 6203 |
| 現行手順 3 | 419 |
| 新手順 3 | 432 |
| 差し替えによる増加 | +13 |
| `:56` の補足削減 | −19 |
| **改訂全文** | **6197** |
| 上限／余裕 | 6204／7 |

メモリ上の差し替えで計算済み。86 行、最大行長 105 文字。**TextLimit の増分は 0**、`TextLimit(6_204, 110)` を維持します。

この exact 文案の SHA256：

```text
84a7d15fd2774014654d2e9b43d4b4bc40bc3a0e67afca45581e006915bc4bd8
```

pin 更新の閉包：

- `tools/check_docs.py:752`：上記 SHA。
- `orchestrator/tests/test_check_docs.py:580`：同じ SHA。
- 同 `:627`：synthetic command の本文も同じ変更。
- 同 `:9834`・`:9841`：既存 SHA 整合 assert を維持。
- 同 `:9848`・`:9853`：本文サイズを `6_197` に更新。
- 同 `:9854`：超過 fixture を `original + "\n" + "x" * 7` に変更。6205 bytes と既存の超過診断 assert を維持。
- 同 `:10109` の digest rebind helper は動的参照なので変更不要。定数の複数行書式を維持する。
- `tools/check_docs.py:285` の予算 pin は変更不要。

`CLEANUP_OCCUPANCY_CONTRACT` の exact 2 行が改訂全文に残ること、§1 が byte 単位で不変であることを静的確認しました。したがって §1 execution edge の文面には触れません。`test_branch_rescue_ledger.py` の実走確認は親に残ります。

## 変異候補

| id | 変異 | 期待 killer node／扱い |
|---|---|---|
| M-a | `start_new_session=True` を追加 | `test_two_dirs_removed_in_parallel_same_pgid`。PGID 観測または launcher の fail-closed により赤 |
| M-b | TERM/INT 転送を削除 | `test_launcher_signal_is_forwarded_before_removal`。実 signal と送信元の観測が成立しない |
| M-c | 中断を `removed`・rc 0 化 | 同中断 node。status と rc の双方を検査 |
| M-d | 撤去後の存在確認を丸ごと削除 | `test_zero_returncode_with_existing_path_is_failed` |
| M-e | 子 rc > 0 を成功扱い | `test_nonzero_returncode_with_absent_path_is_failed`。chmod 負例だけでは残存検査に隠れるため独立 node が必要 |
| M-f | 入れ子検査を削除 | `test_usage_rejects_paths_without_removal[nested]` |
| M-g | cwd 検査を削除 | `test_usage_rejects_cwd_inside_target` |
| M-h | PGID 比較を恒真化 | **現案の必須 kill 対象から除外**。通常の固定 Popen は同じ PGID なので、不一致分岐に到達しない |
| M-i | 動作に関係しない docstring 編集 | 等価変異として `SURVIVED` 期待。契約の意味を変更する文言編集は含めない |

M-d が「`lexists` 呼び出しだけの削除」で、追加した `lstat` が同じ残存を検出するなら SURVIVED が正当です。削除対象を「不在確認の除去」と「冗長な一方だけの除去」に分けて登録してください。

M-h は M-a との二重変異で検出したことにしません。単独検出には実 PGID 不一致を同期して作る別 fixture が必要であり、現案では未証明と明記します。

## 裁定パッケージ候補

scope 拡張の提案はありません。段 3／4 へ渡す設計上の論点は次のとおりです。

- **P1：同意。** 対象は §3 の手動並列撤去。`dev_wave_cleanup.py` は別機構。
- **P2：同意。** 固定 `rm` launcher は局所実装として成立する。常駐監視・汎用 framework は不要。
- **P3：条件付き同意。** PID 宛 TERM/INT の転送は必要。同じ PGID だけでは親 PID 宛 kill は伝播しない。有界停止には TERM 後の KILL escalation を提案するが、それでも kernel 内で終了不能な子の完全回収は保証せず `unknown` にする。
- **P4：例示に異論。** 生存観測だけでは決定性がない。ptrace 同期なら機構の置換なしに構成できる見込みだが、許可・wait イベント処理の実測が必要。成立未確認のまま受入済みにしない。
- **SIGKILL の境界。** launcher PID だけへの SIGKILL まで保証するなら別 scope の寿命制御が必要。本 wave では docstring に限界を記す。

## 総括

S1 は固定 `rm` launcher、S2 は実 process 検証、S3 は既存予算内の差し替えとします。
docs は **6197 bytes**、上限変更不要、occupancy literal と §1 は不変です。
最重要の未実測点は ptrace 同期 fixture の成立です。
PGID 比較の恒真化変異は、現案では単独 kill 未証明として扱います。
書き込み・pytest 実走は行っていません。
