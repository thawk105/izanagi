1.
- 所見: t2195 型の 5 件は外側 watchdog で停止するが、mutant の `TIMEOUT` としては記録されないため、親 brief の帰属は誤りである。
- 根拠: `tools/mutation_harness.py:1994-2003` の `process.communicate(timeout=timeout_s)` は超過時に `timed_out=True`, `rc=None` とするが、`:2259-2269` は `_observed_status` より先に `_dispatch_orphan_stop` を呼び、`:369-390` が `OrphanHoldStop` を返す。`:3304-3313` はこれを rc=2 にする。`orchestrator/tests/test_mutation_harness.py:1894-1909` も `ledger["mutations"] == []` を要求する。
- 判定: real
- 影響: 親が予測した `summary.TIMEOUT=5` にはならず、attempt sidecar の `timed_out=true`、orphan-stop、rc=2、変異 bytes 保全になるため、誤った前提で修正範囲を決める。
- 対処: 親 brief から「TIMEOUT として mutant に帰属」を削除し、本案を採るなら目的を「遅い orphan-stop を source write 前の早期拒否へ変える」と限定する。

2.
- 所見: dispatcher の queue 待ち失敗や通常の infra 異常が KILLED、SURVIVED、TIMEOUT、MISMATCH または baseline PASSED へ化ける経路は、確認した consumer にはない。
- 根拠: `tools/pegasus/dispatch_compute.py:43` は `INFRA_RC = 16`、`:4147-4155` は infra outcome の `rc` を同値にし、`tools/mutation_harness.py:2089-2094` は `rc not in PYTEST_NORMAL_RCS` を `PARSE_ERROR` にする。baseline も `:2155-2160` で同じ分類となる。`:2365-2379` は `PARSE_ERROR` を `completed` に数えない。
- 判定: refuted
- 影響: 誤受理は無し。ただし mutation の非終端 `PARSE_ERROR` record は一度 ledger に書かれ、resume 時に `nonterminal_history` へ移る。
- 対処: 現行の rc=16 と `PARSE_ERROR`、orphan-stop の区別を維持し、status の読み替えは加えない。

3.
- 所見: 親 P1 が fresh baseline と fresh non-hang mutation まで同じ不足として含めた点は過大である。
- 根拠: collection は `tools/mutation_harness.py:1520-1526` で `outer_timeout_s=spec.timeout_seconds` を検査し、baseline は `:2127-2131`、non-hang mutation は `:2247-2254` で同じ `spec.timeout_seconds` を使う。別値になるのは `mutation.hang_risk` が真の場合だけである。resume は `:3141-3158` で collection を再実行しない。
- 判定: real
- 影響: fresh baseline と fresh non-hang を修正対象にすると冗長 gate と到達不能な負例を増やし、変更の帰属が崩れる。
- 対処: plan のとおり baseline には追加せず、fresh hang-risk と、環境が変わり得る resume pending mutation に限定する。

4.
- 所見: F762 を「collection と本走がともに dispatcher を直接呼んだ」と一般化した親 brief の読みは誤りである。
- 根拠: `229e030a:tools/mutation_harness.py:1408-1418` の collection は `dispatch_compute.py` を直接構築する一方、同 commit の `:2049-2053` と `:2172-2176` は baseline と mutation に元の `command` を渡す。現行 `tools/mutation_harness.py:799-810` はその entrypoint を `tools/run_tests.py` に束縛する。
- 判定: real
- 影響: 上書き欠落の原因を本走まで広げると、既に届いている `run_tests.py` 経路を誤って修正対象にする。
- 対処: 歴史的根本原因を「2026-09-03 の collection 直呼び」に限定し、本走は伝播不足でなく watchdog の別問題として扱う。

5.
- 所見: plan の `timeout_s == Q_eff + G_eff` を安全な正例とする保証は、dispatcher の実際の期限式と一致しない。
- 根拠: plan の比較元は `tools/mutation_harness.py:1462` の `outer_timeout_s < queue_wait_timeout_s + overall_grace_s` だが、dispatcher は `tools/pegasus/dispatch_compute.py:3942-3946` で RUN 観測後の期限を `run_observed_at + walltime_s + overall_grace_s` に置き直し、既定 walltime は `:67` の 3600 秒である。具体的に Q=1800、G=600、outer=2400 は比較を通るが、即 RUN でも内側期限は約4200秒、1800秒待って RUN なら約6000秒で、外側 `communicate(timeout=2400)` が先に切れる。
- 判定: real
- 影響: 2400秒正例が緑でも実 dispatch の安全性は証明されず、受入本走は orphan-stop、rc=2、未完了 ledger になり得る。ただし所見1の防壁により terminal mutant status への誤帰属はしない。
- 対処: scope 内ではこの検査を「既知の静的早期拒否」以上の保証として扱わず、2400秒を実 dispatch 安全性の正例と呼ばない。queue 待ちと実行時間を分離した完全な期限契約は scope 外・裁定パッケージ候補。

6.
- 所見: 新 gate 自体は恒真ではなく、拒否側と通過側の具体入力を構成できる。
- 根拠: `tools/mutation_harness.py:1451-1462` の現行式では、Q=1800、G=600、outer=2399 なら `2399 < 2400` で拒否し、outer=2400 なら通る。`:1407-1409` で未設定または空値は `overrides == {}` となり gate を通らない。
- 判定: refuted
- 影響: 無し。ただし `if overrides:` 無条件化 mutant を殺す未設定正例は outer=2399 では足りず、既定900+300より短い値が必要である。
- 対処: 未設定正例を outer=1199 と明記し、元実装は通過、無条件化 mutant は `1199 < 900+300` で拒否されることを固定する。

7.
- 所見: 提案テストは real な `_apply_mutation` を呼ぶ限り修正実体を通せるため、fake runner の使用だけでは両層 stub の恒真テストにならない。
- 根拠: 実体は `tools/mutation_harness.py:2184` の `_apply_mutation` であり、plan の挿入位置は現行 `:2212` の `_mutated_sources` より前、runner seam は `:2250-2254` の `_run_tests` である。従って `_run_tests` を fake にしても、新 helper call、timeout 選択、source write 前順序は実コードを通せる。
- 判定: refuted
- 影響: 無し。ただし helper 単体だけを呼ぶ実装に落ちると resume/main の callsite 被覆を失う。
- 対処: nodeid 内で real な `harness._apply_mutation` を呼び、helper 自体は monkeypatch せず、`_run_tests` と write を spy 境界に限定する。

8.
- 所見: 4 つの変異候補はすべて `tools/mutation_harness.py` を対象にするが、plan は DW-M07 の危険な runner 経路との交差を認識している。
- 根拠: 候補は helper の `<` から `<=`、`if overrides:` の無条件化、`mutation.hang_risk` の反転、helper call の除去である。`docs/dev-wave/mutation.md:47-49` は runner 経路の変異が collection rc=16 に自壊すると定める。一方、main は `tools/mutation_harness.py:3180-3191` で collection を先に完了し、`:3262-3277` で後から各 mutation を適用するため、これらの候補は active harness の既読 bytecode を置き換えない。
- 判定: refuted
- 影響: plan の除外を守れば無し。`_runner_identity`、`_collection_command`、`_run_tests` の entrypoint 側へ候補を広げると、rc=16 を kill と誤計上する自壊リスクが生じる。
- 対処: 名指しした4候補だけに限定し、test child が変更後 module を新規 importして期待 node で落ちた場合だけ kill とする。

9.
- 所見: 約904秒を当時の collection queue timeout で説明する読みと、1e22c4cbd 以後に明示上書きが collection argv へ届くという狭い意味の「閉じた」はコードに支持される。
- 根拠: `229e030a:tools/mutation_harness.py:1408-1418` は timeout option なしで dispatcher を直呼びし、同時点の `tools/pegasus/dispatch_compute.py:68-71` は queue=900、poll=5、`:3951-3965` は `now - queue_started >= queue_wait_timeout_s` で `queue-wait-timeout` とする。現行 `tools/mutation_harness.py:1471-1478` は2 optionを argv に入れる。
- 判定: refuted
- 影響: 無し。ただし経過秒数だけでは receipt の reason まで実証できず、「閉じた」は伝播についてだけで、所見5の lifetime 保証までは含まない。
- 対処: 904秒は「コードと整合する本命」と表現し、実測断定には receipt の `queue-wait-timeout` を要求する。

10.
- 所見: P2 の fan-out、worktree、harness が D612 変数を落とさないという判断は正しい。
- 根拠: `tools/mutation_fanout.py:1387-1395` は `os.environ.copy()` を渡し、`:1617-1624` の launcher は env 指定なしで継承し、`:819` は `os.execv` する。`tools/mutation_worktree.py:138-145` は `GIT_*` だけを除き、`:809-817` で `_child_env()` を渡す。`tools/mutation_harness.py:1933-1943` は Python系だけを除く。
- 判定: refuted
- 影響: 無し。上書き不達を fan-out または wrapper の責任とする修正は誤りになる。
- 対処: 変更不要。

11.
- 所見: plan は D612 の未設定時挙動、既定900/300、自動選択しない性質を変えない。
- 根拠: `docs/decisions.md:24543-24550` は未設定時900/300維持と自動切替不採用を定め、`tools/mutation_harness.py:1407-1409` は空値を省き、`:1451` は `if timeout_overrides` の場合だけ gate を発火させる。dispatcher の既定は `tools/pegasus/dispatch_compute.py:68-69` の900/300のままである。
- 判定: refuted
- 影響: 未設定時の受理集合への影響は無し。明示上書き時だけ mutation の早期拒否が純増する。
- 対処: `bool(overrides)` 条件と未設定、空値の正例を維持する。

## 総括

- (a) real の件数: 4件。
- (b) 最も重い1件: Q+G の等号境界が実 dispatch の lifetime 安全性を保証しない所見5。
- (c) プランを採用してよいか: as-is では不可。親の誤帰属を訂正し、変更を早期拒否だけと位置付け、real `_apply_mutation` 正例と未設定1199秒例を固定する場合に限り採用可能。
- (d) 親 brief の誤り: 有り。mutant TIMEOUT 帰属、fresh baseline/non-hang への一般化、F762 の本走直呼び一般化が誤りで、904秒の collection 説明、P2、collection への上書き到達は正しい。