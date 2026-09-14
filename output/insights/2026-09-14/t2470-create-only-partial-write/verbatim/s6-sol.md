## R-1 — 撤去条件を片方だけ通して他者の成果物を消す攻撃

**refuted／scope 内。** [trial_registry.py:2451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2470-create-only-partial-write/orchestrator/campaign/trial_registry.py:2451) で総書込量をゼロから数え、2458 行で成功した write の返却量だけ加算する。2464–2471 行は、fd の size 一致、その後に名前の dev・ino 一致を要求する入れ子であり、片方の省略・逆順・恒真化による撤去経路は見つからなかった。照合中の `OSError` も unlink を飛ばす。

成果物への影響：想定攻撃なら他者が追記した試行台帳や差し替えた完成物が消えるが、この条件を既に破る変更は撤去されない。

受理：自分の書込量と size が一致し、名前が作成 fd と同じ inode を指す失敗ファイルは撤去対象になる。拒否：追記による size 不一致、または同名の別 inode は撤去対象にならない。通る正例は、1 byte 書いた後に write が失敗し、同一 inode・size 1 の残骸だけを撤去する場合。

## R-2 — `FileExistsError` から既存完成物を撤去する攻撃

**refuted／scope 内。** [trial_registry.py:2447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2470-create-only-partial-write/orchestrator/campaign/trial_registry.py:2447) の open と `FileExistsError` handler は、2452 行からの撤去対象 try より外側にある。既存名への失敗は2477 行で再送出され、実行される finally は親 fd の close だけである。

成果物への影響：二重作成を使った既存 genesis・受領証の消失経路は成立しなかった。

受理：未存在名への `O_EXCL` 作成成功だけが書込み・撤去の区間へ進む。拒否：既存名への作成は gate 付き `TrialRegistryError` になる。通る正例は、完成済み受領証に同じ引数で再分類を要求し、既存 bytes を保って拒否する場合。

## R-3 — 撤去失敗で元の write／fsync 例外を置き換える攻撃

**refuted／scope 内。** [trial_registry.py:2462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2470-create-only-partial-write/orchestrator/campaign/trial_registry.py:2462) は撤去中の `OSError` を2472–2473 行で握り、2474 行の裸の `raise` で元例外を再送出する。元例外が `OSError` なら2480 行で gate を保ち、`from exc` によって同じ例外を `__cause__` にする。`KeyboardInterrupt` は変換されず再送出される。

成果物への影響：撤去失敗を成功扱いして台帳更新へ進む経路、または撤去エラーで元の診断を置換する経路は成立しなかった。

受理：元の I/O 失敗を cause に持つ gate 付きエラーが呼出元へ届く。拒否：cleanup の `OSError` を元原因として採用したり、失敗を握り潰したりしない。通る正例は、write が EIO、unlink が EACCES となり、EIO が cause に残る場合。

## R-4 — 成功時の bytes・同期順・返り値を変える攻撃

**refuted／scope 内。** [trial_registry.py:2453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2470-create-only-partial-write/orchestrator/campaign/trial_registry.py:2453) の write ループは返却量だけ view を進め、2460–2461 行で file、parent の順に fsync する。正常時は撤去 handler を通らず、2483 行で従来の組立てによる Path を返す。追加されたカウンタは payload や返り値に流入しない。

成果物への影響：正常作成される台帳・受領証の bytes、digest、参照先が変わる経路は見つからなかった。

受理：全 bytes の書込みと両 fsync を完了した作成は従来どおり成功する。拒否：write の進捗なしや fsync 失敗は成功に変換されない。通る正例は、毎回1 byteの短い write を繰り返して payload 全体を保存する場合。

## R-5 — 禁止された拡張と競合窓の拡大

**refuted／scope 内。** 統合差分と現物を照合した範囲では、新規 lock・staging・hard-link publish・production 検査関数・gate・module・台帳・test file の追加、他 writer への横展開は見つからなかった。[trial_registry.py:2470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2470-create-only-partial-write/orchestrator/campaign/trial_registry.py:2470) の inode 比較直後は unlink であり、間に追加 I/O・ログ・検査呼出しはない。size 取得後の名前照合はあるため、競合窓そのものは残る。

成果物への影響：照合後の追記・差し替えによる消失可能性は残るが、今回の実装が余計な処理でその窓を広げる経路は見つからなかった。

受理：照合時点で両条件を満たす失敗ファイルは撤去される。拒否：原子的な所有保証や競合窓の解消まで達成したという主張はできない。通る正例は、競合のない file fsync 失敗後の撤去。

## R-6 — 分類受領証で照合が撤去を妨げ、参照を壊す攻撃

**refuted／scope 内。** [trial_registry.py:3297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2470-create-only-partial-write/orchestrator/campaign/trial_registry.py:3297) は実際に渡す receipt bytes の digest から名前を決める。受領証 writer が戻る3308 行より後に、3337 行の台帳更新がある。通常の受領証作成では追記も inode 交換もなく、短い write・進捗なし・両 fsync の失敗で照合を意図せず外す要因は見つからなかった。

成果物への影響：writer 失敗後に分類参照行だけが追記される経路はなく、撤去成功後は同じ payload の再試行が可能になる。

受理：残骸撤去後、同じ引数による受領証作成と分類行追記は再試行できる。拒否：受領証 writer が失敗した呼出しは台帳追記へ進まない。通る正例は、親 directory の fsync 失敗で受領証を撤去し、障害解除後に同じ digest の名前へ再作成する場合。

## R-7 — `close` 失敗による診断置換は残る

**real、nit／scope 外。** [trial_registry.py:2475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2470-create-only-partial-write/orchestrator/campaign/trial_registry.py:2475) の `os.close(fd)` が失敗すると元例外を置換し得る。2482 行の親 fd close が失敗すれば gate 付き例外も置換し得る。ただし、いずれも今回追加した経路ではない。

成果物の値・受理集合・参照が今回の差分によって変わる説明は立たず、must-fix にはしない。

受理：両 close が成功する通常経路では元原因の保持が成立する。拒否：close まで含めた無条件の診断保持は保証できない。通る正例は、unlink が失敗しても両 close が成功し、元 write 例外が cause に残る場合。

## 総括

正しさ境界の静的レビューでは、**scope 内の real must-fix は0件**。7つの攻撃対象について、新たな完成物消失・誤受理・参照破壊の経路は確認できなかった。残余競合窓と既存 close 例外による診断置換は残る。

編集・commit・pytest 実走は行っていない。テスト通過や変異の殺傷力は本レビューでは判定していない。