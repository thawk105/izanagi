## Q1. 904 秒はどの層が切ったのか

### 2026-09-03 時点

当日の実測 commit は提示されていないため、同日末の `229e030a313bb1a3f5510d4991e327c00b538250` を参照点とする。関連 file のうち今日と blob が異なるのは `tools/mutation_harness.py` だけで、当時の該当 harness blob は 2026-09-02 の `0bc1ab724b` から変わっていない。

| 層 | コード上の締切 | 904 秒付近で切るか |
|---|---|---|
| collection の `dispatch_compute` | 当時の `_collection_command` は `dispatch_compute.py` を直接起動し、timeout option を渡さない。`229e030a:tools/mutation_harness.py:1388-1419`。dispatcher の既定は queue 900 秒、grace 300 秒。`tools/pegasus/dispatch_compute.py:68-70` | **切る。904 秒の本命。** `submitted_at` から 900 秒以上で `queue-wait-timeout`。`tools/pegasus/dispatch_compute.py:3890-3895,3951-3968`。既定 poll は 5 秒で、qstat と setup の経過もあるため 902 秒や 904 秒は整合する |
| harness の外側 watchdog | collection は `spec.timeout_seconds` を `_run_tests` へ渡す。`229e030a:tools/mutation_harness.py:1445-1452`。`communicate(timeout=timeout_s)` が超過時に process group を止める。`229e030a:tools/mutation_harness.py:1914-1927` | 実測条件が 3600 秒なら **904 秒では切らない**。切るのは約 3600 秒後で、停止待ちが最大 5+5 秒付く |
| baseline / 通常 mutation の watchdog | baseline は `spec.timeout_seconds`、通常 mutation も同値。`229e030a:tools/mutation_harness.py:2049-2053,2169-2176` | 3600 秒設定なら **904 秒では切らない** |
| hang mutation の watchdog | `hang_timeout_seconds` を使う。`229e030a:tools/mutation_harness.py:2169-2176` | 値が約 900 秒なら競合し得るが、提示された「3600 秒設定」だけからは該当しない |
| 本走の `run_tests.py` | baseline / mutation は元の runner command を実行するため、`run_tests.py` を経由する。D612 変数は `_dispatch_environment` を通り、`_default_dispatch` が数値化して dispatcher へ渡す。`tools/run_tests.py:1290-1304,1307-1373` | 上書きが 3600 秒なら **900 秒では切らない**。ただし当時は、その前の collection が 900 秒で失敗したため本走へ到達しない |
| `deadline_at` / shard | `deadline_at` は acceptance shard の 5100 秒制限からのみ渡る。`tools/run_tests.py:79,2323-2352` | **904 秒では切らない。** また harness は `-rf` を必須化し `-p no:cacheprovider` を加える。`tools/mutation_harness.py:3067-3073`。`-p` は acceptance shape を外す。`tools/run_tests.py:708-716`。従って通常の mutation runner は shard deadline 経路に入らない |
| lease | `run_tests.py` の dispatch 呼び出しに lease TTL 由来の締切はない | **切らない** |
| dispatcher のその他 | 個々の scheduler command は 30 秒。`tools/pegasus/dispatch_compute.py:580-595`。RUN 後の total deadline は walltime 3600 秒 + grace 300 秒、終了後 accounting grace は 60 秒。`tools/pegasus/dispatch_compute.py:67-71,3890-3895,3980-3983` | 単一 qstat が固まれば約 30 秒の infra failure、RUN 後なら数千秒なので、固定的な 904 秒の説明ではない |
| fan-out driver | 120 秒は全 launcher を揃える開始 barrier だけ。`tools/mutation_fanout.py:797-819,1601-1655`。開始後の `_wait_for_children` は deadline なし。`tools/mutation_fanout.py:741-785` | **切らない** |
| worktree wrapper | harness child を `process.wait()` で無期限に待つ。`tools/mutation_worktree.py:805-833`。12 秒と 5 秒は外部 signal 後の回収だけ。`tools/mutation_worktree.py:760-771` | **切らない** |
| fan-out contract | execution process を監視せず、spec の timeout 値を束縛するだけ。`tools/mutation_fanout_contract.py:470-473,578-583,855-861` | **切らない** |

結論として、2026-09-03 の約 904 秒は、collection が直接呼んだ `dispatch_compute` の queue-wait 既定 900 秒で説明できる。外側 3600 秒 watchdog、`run_tests.py`、fan-out、worktree wrapper はその時刻を作らない。

### 今日の HEAD `2143a49c0c9037b303106eca4cfc346797d3f1b3`

- collection 経路は**塞がっている**。`_dispatch_timeout_overrides` が 2 変数を解釈し、`_collection_command` が `--queue-wait-timeout` と `--overall-grace` を直接 dispatcher argv へ渡す。`tools/mutation_harness.py:1395-1418,1421-1492`。
- 明示上書きがあり、`spec.timeout_seconds < Q_eff + G_eff` なら Popen 前に `HarnessError` となる。`tools/mutation_harness.py:1451-1469,1518-1527`。
- 上書き未設定時に option を省き、dispatcher の 900/300 を保つ挙動は意図的に固定されている。`orchestrator/tests/test_t2337_dispatch_timeout_overrides.py:98-120`。
- baseline / mutation では、harness の `runner_env` が除くのは pytest/Python 系だけで D612 変数は残る。`tools/mutation_harness.py:1933-1943`。さらに `run_tests.py` も D612 変数を落とさず dispatcher kwargs に変換する。`tools/run_tests.py:1290-1304,1343-1372`。
- fan-out の bounded scope は `os.environ.copy()` を渡し、launcher は `execv`、wrapper は非 `GIT_*` を維持する。`tools/mutation_fanout.py:1386-1395,1617-1624,797-819`、`tools/mutation_worktree.py:138-145,746-749,809-818`。

従って今日、正しく export された 3600 秒上書きが 904 秒で失われる実装経路はない。約 904 秒で切れるなら、変数が未設定または空だったことをまず疑うべきであり、fan-out / wrapper による削除ではない。

## Q2. 今日の HEAD に残る欠陥

届かない経路は 0 件である。残るのは、同じ一つの「mutation 本走前に実効 watchdog を再検査しない」欠陥が作る、次の 2 つの到達可能経路である。

### 1. fresh run の hang-risk mutation

再現条件は以下。

- `runner_mode == "dispatch"`。
- 少なくとも一方の D612 上書きが非空。
- `spec.timeout_seconds >= Q_eff + G_eff` なので collection は通る。
- `mutation.hang_risk is True` かつ `spec.hang_timeout_seconds < Q_eff + G_eff`。
- queue が `hang_timeout_seconds` まで RUN へ進まない。

collection は `timeout_seconds` だけを検査する。`tools/mutation_harness.py:1520-1527`。一方、mutation は hang-risk のとき別値 `hang_timeout_seconds` を使うが、事前検査がない。`tools/mutation_harness.py:2247-2254`。

症状は、約 `hang_timeout_seconds` 後に `communicate` が timeout となり、rc は `None`、`timed_out=true` になること。停止処理に最大約 10 秒が加わり得る。dispatch mode の timeout は `_dispatch_orphan_stop` が orphan hold に変換する。`tools/mutation_harness.py:327-390,1993-2008,2259-2269`。mutation source は復元せず保全される。`tools/mutation_harness.py:2317-2355`。最終的な harness / fan-out は infra rc=2 となる。

変異台帳・受入結果への影響は、**誤った KILLED / SURVIVED / TIMEOUT record は書かれない**。attempt sidecar に `timed_out=true` が残り、orphan-stop が作られ、mutation terminal record は追加されない。fan-out merger も wrapper rc が 0/1 でないため受理しない。`tools/mutation_fanout_contract.py:1315-1323`。影響は「誤判定」ではなく「変異走行を完了できず受入不能」である。

(P1) は「本走に gate がない」という点を支持するが、「TIMEOUT として mutant に帰属する」は反証される。(P2) は支持する。上書きは届いている。

### 2. `--resume` 後の pending mutation

再現条件は以下。

- 過去の低い上書きまたは上書きなしで、collection と baseline が完了した ledger がある。
- `--resume` 時に、より大きい D612 上書きを設定する。
- pending mutation の実効 watchdog が `Q_eff + G_eff` より短い。
- queue がその watchdog まで RUN へ進まない。

resume は保存済み collection を検証するだけで、今日の上書きに対する collection gate を再実行しない。`tools/mutation_harness.py:2643-2753,3141-3158`。ledger の procedure は spec の 2 timeout を束縛するが、D612 上書き値は束縛しない。`tools/mutation_harness.py:2415-2425,2695-2726`。

baseline は resume ledger の必須 recordとして検証されるため、正規の resume で baseline 未実行という経路はない。`tools/mutation_harness.py:2743-2753`。従ってこの欠陥の resume 面は pending mutation のみである。通常 mutation なら `timeout_seconds`、hang-risk なら `hang_timeout_seconds` が外側 watchdog になる。

症状と台帳への影響は Q2-1 と同じで、約その mutation の watchdog 秒後に orphan hold と rc=2になる。既存 ledger の過去 record は維持され、現在の mutation は terminal record にならない。受入結果への誤昇格は無し、走行完了不能という影響がある。

(P1) は resume mutation に関して支持する。ただし fresh baseline と fresh non-hang mutationは、同じ process の直前 collection が同じ `timeout_seconds` と同じ環境を検査済みなので、P1 が示す一般的な欠陥ではない。(P2) は支持する。

## Q3. 最小修正プラン

### 実装

変更先は `tools/mutation_harness.py` だけとする。

1. `tools/mutation_harness.py:1395-1418` の直後に、例えば `_checked_dispatch_timeout_overrides` を追加する。

   - 入力は `outer_timeout_s`, `environ`, `phase`。
   - `_dispatch_timeout_overrides` で現行と同じ 2 変数だけを解釈する。
   - 次の式だけを検査する。

   ```python
   overrides = _dispatch_timeout_overrides(environ=environ)
   if overrides:
       queue_s = overrides.get(
           "queue_wait_timeout_s",
           dispatch_compute.DEFAULT_QUEUE_WAIT_TIMEOUT_S,  # 900.0
       )
       grace_s = overrides.get(
           "overall_grace_s",
           dispatch_compute.DEFAULT_OVERALL_GRACE_S,       # 300.0
       )
       if outer_timeout_s < queue_s + grace_s:
           raise HarnessError(...)
   ```

   未設定時は `overrides == {}` のため検査せず、dispatcher の既定 900/300 を変更しない。明示された一方だけを上書きし、他方は現行既定を式の比較にだけ使う。

2. `tools/mutation_harness.py:1445-1478` の collection 内実装を上記 helper 呼び出しへ置き換え、返された dict から既存 argv を構築する。collection の受理集合と既存テストは変えない。

3. `tools/mutation_harness.py:2200-2212` で最初の orphan-stop 検査が通った直後に、現在 `2247-2249` にある `timeout_s` 選択を移す。

   ```python
   timeout_s = (
       spec.hang_timeout_seconds
       if mutation.hang_risk
       else spec.timeout_seconds
   )
   ```

   `runner_mode == "dispatch"` の場合だけ、新 helper へこの `timeout_s` を渡す。検査は `_mutated_sources` と source write より前に置き、拒否時に mutation bytes を一度も書かない。`2250-2254` は検査済みの同じ `timeout_s` を使う。

4. `_baseline` には新しい gate を足さない。fresh baseline は同じ `spec.timeout_seconds` の collection gate で既に覆われ、正規 resume は baseline record を必須とする。ここへの重複 gate は到達可能な欠陥を塞がず、scope 外の冗長検査になる。

拒否: `runner_mode == "dispatch" and bool(overrides) and timeout_s < Q_eff + G_eff` の mutation は、runner 起動と source write の前に拒否する。  
通過: `timeout_s == Q_eff + G_eff`、または D612 上書きが 2 本とも未設定または空の mutation は通す。

`tools/run_tests.py`、`tools/pegasus/dispatch_compute.py`、`tools/mutation_fanout.py`、`tools/mutation_worktree.py`、`tools/mutation_fanout_contract.py` は変更しない。status の読み替え、既定値変更、自動選択、受理集合拡張は行わない。

### テスト

既存の `orchestrator/tests/test_t2337_dispatch_timeout_overrides.py` に追加する。同 file は D612 parser、collection 転送、短い外側 watchdog を既にまとめており、新 file に分ける理由がない。

追加 nodeid 案は以下。

- `orchestrator/tests/test_t2337_dispatch_timeout_overrides.py::test_mutation_run_watchdog_contract_rejects_short_and_accepts_boundary[non-hang]`
- `orchestrator/tests/test_t2337_dispatch_timeout_overrides.py::test_mutation_run_watchdog_contract_rejects_short_and_accepts_boundary[hang]`

各 nodeid で、例えば `Q=1800`, `G=600` とし、次を一つの境界テストに含める。

- 2399 秒は `_run_tests` と source write の前に `HarnessError`。
- 2400 秒は拒否せず、fake runner 境界まで到達。
- 上書きなしなら短い timeout も新 gate では拒否しない。
- non-hang は `timeout_seconds`、hang は `hang_timeout_seconds` を実際に選択する。

修正前は短い側が mutation 適用または fake runner まで到達するため nodeid 全体が赤になる。修正後は短い側を事前拒否し、同じ nodeid 内の等号境界と未設定正例も通るため緑になる。実 scheduler は使わず、Popen と source write 境界を monkeypatch する。

### 変異注入候補

- 新 helper の比較演算子 `<` を `<=` に変える。2400 秒の等号正例が過剰拒否され、上記 2 nodeid が落ちる。
- `if overrides:` を無条件化する。未設定正例が暗黙の 900+300 gate で拒否され、上記 nodeid が落ちる。
- `_apply_mutation` の timeout 選択で `mutation.hang_risk` を反転する。non-hang / hang のいずれかが誤った timeout を使い、対応する parameter nodeid が落ちる。
- `_apply_mutation` から helper 呼び出しを除く変異では短い側が fake runner または source write へ到達し、両 nodeid が落ちる。

これらは `tools/mutation_harness.py`、つまり変異道具自身を対象にするため DW-M07 の自壊リスクがある。特に `_runner_identity`、`_collection_command` の dispatcher argv、`_run_tests` の entrypoint を変える候補は collection rc=16 や runner identity failure に化けるため除外する。純粋 helper と timeout 選択だけを候補にし、pytest child が変更後 module を新規 importして指定 nodeidの assertion で落ちた場合だけ kill と数える。テスト到達前の rc=16 は kill に数えない。

### 実装後の順序

`tools/mutation_fanout_contract.py:35-41` の `_FIXED_HEAD_PATHS` は harness、wrapper、runner、dispatcher、contract の HEAD blob を束縛する。従って実装者はコードとテストの静的確認後に commit を作り、その commit 後に初めて焦点走と変異走行を行う。未 commit の harness で焦点走を先行させない。

本段では pytest や dispatch を実走しておらず、緑は主張しない。実測は親が commit 後に `tools/run_tests.py` 経由で行う。

## Q4. 親 brief の誤り

親の読解 1、2、3、4、5、6 は、個別のコード事実としては正しい。ただし (P1) の到達可能性と影響評価に次の誤りがある。

1. **fresh baseline を残存欠陥に含めた点が過大。** collection と baseline は同じ `spec.timeout_seconds` を使い、同じ process の同じ D612 環境で順に動く。collection gate を通った fresh baseline が同じ式で短くなることはない。正規 resume も baseline record を必須とする。`tools/mutation_harness.py:1520-1527,2127-2131,2743-2753`。

2. **fresh non-hang mutation も同じ理由で通常は既に覆われる。** 到達可能な例外は、別の `hang_timeout_seconds` を使う fresh hang mutationと、環境上書きが変わった resume の pending mutationである。`tools/mutation_harness.py:2247-2254,3141-3158`。

3. **「watchdog timeout が mutant の TIMEOUT として台帳へ帰属する」は誤り。** dispatch mode の `timed_out=true` は、status 判定より前の `_dispatch_orphan_stop` で `OrphanHoldStop` になる。mutation record は返らず、source を保全し、harness は rc=2 で止まる。`tools/mutation_harness.py:327-390,2259-2269,2317-2355,3304-3313`。従って受入結果の誤昇格はなく、実害は完了不能である。

4. brief が要約した F762 の「collection / 本走の command 構築がともに dispatcher 直呼び」という記述は、2026-09-03 の本走コードには当てはまらない。本走は当時も runner command、すなわち `run_tests.py` を実行していた。約 904 秒を作ったのは本走ではなく、上書きなしで dispatcher を直接呼んだ collection である。

(P2) に誤りはない。

## 総括

- 904 秒の層: 2026-09-03 の collection が使った `dispatch_compute` の queue-wait 既定 900 秒。今日の明示上書き collection 経路は塞がっている。
- 今日残る欠陥: 到達可能経路は 2 件、根は mutation 本走前の watchdog 再検査漏れ 1 件。
- 推奨する最小修正: collection の既存式を helper 化し、`_apply_mutation` で実効 `timeout_s` を source write 前に同じ式で検査する。
- 実装しない方がよいもの: dispatcher の既定値・受理集合、自動選択、baseline の冗長 gate、timeout status の読み替え、resume 台帳 schema 拡張。