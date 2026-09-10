結論は、既存 `_best_effort_qdel()` を低水準の qdel 実行 primitive として残し、その直後に新設する `_fresh_qstat_gated_qdel()` へ 4 呼出点を集約する案です。fresh qstat が「rc=0・対象 request 可視・正規化状態 QUE/HLD」の全条件を満たす場合だけ既存 primitive を呼びます。receipt schema は v2 のままとします。

以下の行番号は基準 commit の現行行です。静的読解のみで、pytest は実行していません。

## file:line 実装プラン

1. [_classify_qstat_response():186](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:186)

   実装は変更せず、docstring の「immediate qstat」を「qstat 応答」へ一般化する。新 gate でも同じ分類を利用するため。

2. [_print_terminal_handoff():879](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:879)

   共通の `_print_qdel_skip_handoff()` を近傍へ追加する。raw scheduler 出力は表示せず、正規化済み request ID、gate の rc/state/reason、および次を stderr へ出す。

   > fresh qstat gate により qdel を見送りました。ジョブが残っている可能性があります。ユーザー自身の端末で qstat を確認してください。

   request ID が得られない場合は job name を表示する。

3. [_best_effort_qdel():889](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:889)

   現行 qdel primitive は変更しない。その直後、`_persist_receipt()` の前に `_fresh_qstat_gated_qdel()` を新設する。

   helper は次の順で処理する。

   - request ID を正規化する。
   - `_run(..., ["qstat", "-f", normalized_id], ...)` をちょうど 1 回呼ぶ。loop、sleep、retry は置かない。
   - `_classify_qstat_response()` で rc/可視性を分類する。
   - rc=0 の場合だけ `_qstat_mentions_request()` を信頼する。
   - rc=0 かつ request 可視の場合だけ `_scheduler_state()` を判定に使う。
   - `_scheduler_state()` の結果が `QUE` または `HLD` の場合だけ `_best_effort_qdel()` を直ちに呼ぶ。STG は既存実装が QUE へ正規化する。
   - RUN、END、UNKNOWN、request 不在、rc≠0、例外はすべて `attempted=False` で返す。
   - 正規化から qstat capture までを `BaseException` 捕捉下に置き、signal・`TimeoutExpired`・`OSError` でも qdel へ進まない。
   - gate 観測を `state_history` へ追加しない。

   新 helper を選ぶ理由は、qstat の「取消判断」と qdel の「実行結果」を receipt 上もコード上も分離でき、4 箇所への条件実装の重複を避けつつ、qstat と qdel の間隔を最小化できるためです。既存 `_best_effort_qdel()` の production caller はこの helper だけにする。

4. [receipt 初期化:1003](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1003)

   `receipt["qdel"]["attempted"]` の意味は「qdel command を実際に起動したか」のまま維持する。gate 未到達の成功 receipt は現行 `{"attempted": false}` のままでよい。gate 到達時だけ後述の `gate` object を持つ。

5. [qsub 成功後のコメント:1091](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1091)

   「discovery + qdel」を「discovery + fresh-qstat gate、許可時のみ qdel」へ訂正する。

6. 4 呼出点を直接差し替える。

   - [permission error 経路:1143](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1143)
   - [request 不在経路:1164](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1164)
   - [compute marker 不在経路:1300](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1300)
   - [外側 except 経路:1391](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1391)

   各 `receipt["qdel"] = _best_effort_qdel(...)` を `receipt["qdel"] = _fresh_qstat_gated_qdel(...)` へ置換する。既存の `active=False`、latch、outcome、return rc、log relay の順序は変えない。

   receipt 永続化後、gate が見送った場合に共通 handoff message を出す。これにより receipt が先に残り、表示失敗が証拠作成を妨げにくい。

7. [request ID discovery 失敗分岐:1397](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1397)

   qstat 自体を打てないため、現行の `attempted=False` を維持しつつ、`gate.qstat.attempted=False`、`reason=request-id-unavailable` を追加する。job name/submission dir と「ジョブが残っている可能性」を残す。

## 4 経路の判断

| 経路 | gate 到達時の想定状態 | 判断 | 見送り時の記録・メッセージ |
|---|---|---|---|
| L1143 permission error | 直前観測は権限系 rc≠0 で状態不明。fresh qstat も同じエラーになる可能性が高い | fresh が rc=0・request 可視・QUE/HLD に回復した場合だけ取消可。それ以外は見送り | 通常は `classification=permission`, `scheduler_state=UNKNOWN`, `reason=qstat-nonzero`。F47 latch は従来どおり作り、ジョブ残存可能性を明示 |
| L1164 rc=0/request 不在 | 可視性遅延、無効 request、または可視性障害下の実行中ジョブを区別不能 | fresh でも不在なら見送り。fresh で対象が現れ QUE/HLD なら取消可 | `request_present=false`, `scheduler_state=UNKNOWN`, `reason=request-absent`。F47 latch/rc=16 は不変 |
| L1300 compute marker 不在 | 監視ループは既に END で抜けているため、通常は END または request purge 後の不在 | END/不在は見送り。矛盾した fresh 観測が QUE/HLD の場合のみ取消可 | `scheduler_state=END, reason=state-not-cancellable`、または `request-absent`。marker 不在 latch と log relay は不変 |
| L1391 外側 except | queue timeout は QUE/HLD/UNKNOWN、overall timeout は主に RUN/UNKNOWN、signal は任意、収集例外は通常 END/不在 | QUE/HLD のみ取消可。RUN/END/UNKNOWN/error は見送り | 元の `outcome.reason` は上書きせず、cleanup 判断を `qdel.gate` へ分離。通常の infra failure 表示に加え、残存可能性を表示 |

外側 except の qsub 応答解析失敗・signal during capture は、discovery 後の fresh state が通常 QUE なので、正例として qdel が引き続き可能です。`run_seen` は条件に加えません。

## receipt 構造

gate 見送り例は次の形にします。

```json
{
  "qdel": {
    "attempted": false,
    "request_id": "424242.nqsv",
    "reason": "fresh-qstat-gate-denied",
    "gate": {
      "qstat": {
        "attempted": true,
        "returncode": 0,
        "stdout": "...",
        "stderr": ""
      },
      "classification": "success-request-visible",
      "request_present": true,
      "scheduler_state": "RUN",
      "allowed": false,
      "reason": "state-not-cancellable"
    }
  }
}
```

設計上の要点は次です。

- `gate.qstat.returncode`: fresh qstat の rc。例外時は `null` とし、`exception` を置く。
- `gate.classification`: 既存 `_classify_qstat_response()` の値。例外・ID 不在時は `null`。
- `gate.request_present`: rc=0 のときだけ bool、それ以外は `null`。
- `gate.scheduler_state`: `QUE/HLD/RUN/END/UNKNOWN` の既存語彙だけを使う。非ゼロ・不在・解析不能は `UNKNOWN`。
- `gate.allowed` と `gate.reason`: destructive action の判定を一義化する。
- 許可時は既存 `_best_effort_qdel()` の結果へ同じ `gate` object を追加し、top-level `attempted=True` と qdel 自身の `returncode/stdout/stderr` を維持する。
- STG の raw 証拠は `gate.qstat.stdout` に残り、`scheduler_state` は既存正規化どおり QUE になる。
- `state_history` は[監視ループ:1197](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1197)の時系列専用とし、gate 観測を混ぜない。

`pegasus-dispatch-receipt/v2` は上げません。[schema 定数:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:79)に対する additive・optional な拡張で、`attempted` の意味も変わらないためです。

実在 consumer もこれを支持します。

- production caller の [`run_tests._default_dispatch()`:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/run_tests.py:826) は dispatch の整数 rc だけを消費する。
- [`mutation_harness._read_dispatch_stdout()`:1008](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/mutation_harness.py:1008) は receipt を実際に読むが、`submission_dir/outcome/request/request_id/scheduler_logs` を `.get()` するだけで、schema version や `qdel` の exact keys を検査しない。
- `qdel` object 自体の consumer は対象テストだけ。既存の v2 assertion [1616](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1616)・[1734](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1734)も維持する。
- 過去の v2 receipt は `gate` が無くても引き続き有効とする。

## 既存 qdel テスト 14 件の分類

分類は排他的に、(a) qdel assertion が変わるもの、(c) assertion は変わらないが gate が追加 state を消費するもの、(b) gate 未到達で完全に変わらないもの、の優先順とします。signal parametrization は 1 test 定義・2 node です。

| 分類 | 既存テスト | 更新後 |
|---|---|---|
| (a) | [interpreter stage failure:933](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:933) | 完了後の fresh qstat は request 不在。qdel 期待を「打たない」へ反転 |
| (a) | [M6 request absent:946](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:946) | fresh でも不在なので qdel なし。test 名も `skips_qdel_and_latches` へ変更 |
| (a) | [F47 permission:1013](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1013) | gate が第2 qstat を打ち、再び rc=153。`qstat_calls == 2`、qdel なし |
| (a) | [accounting grace failure:1096](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1096) | END 後の不在なので qdel なし |
| (a) | [scheduler exception:1295](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1295) | gate の `_run` も例外。qdel なし、`gate.qstat.exception` を期待 |
| (a) | [overall timeout/RUN:1324](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1324) | 既存3個目の RUN を gate が消費。qdel なしへ反転し、test 名も変更 |
| (a) | [post-run UNKNOWN:1389](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1389) | gate 用に `UNRECOGNIZED` を1個追加。`scheduler_state=UNKNOWN`、qdel なし |
| (a) | [nonzero qstat RUN stdout:1411](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1411) | untrusted tuple 末尾へ `ERROR` を追加。fresh rc=153 なので stdout の RUN に関係なく qdel なし |
| (c) | [HLD timeout:1174](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1174) | `states` を HLD 4 個へ増やす。最初の3個は state_history、4個目は gate。qdel 期待は維持 |
| (c) | [qsub parse/discovery:1253](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1253) | discovery の引数なし qstat は states を消費せず、gate が最初の QUE を消費。qdel 期待は維持 |
| (c) | [signal during qsub capture:1267](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1267) | 同じく discovery 後に gate が QUE を消費。qdel 期待は維持 |
| (b) | [queue wait budget:1350](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1350) | 正常完了で gate 未到達。qdel なしのまま |
| (b) | [done at deadline:1369](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1369) | 正常完了で gate 未到達。変更なし |
| (b) | [trusted RUN after error:1458](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1458) | 正常完了で gate 未到達。変更なし |

特に `_Scheduler` は[150–164 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:150)で引数付き qstat ごとに state を消費し、tuple 枯渇後は `DONE` になります。RUN/UNKNOWN/HLD の否定・正例が、枯渇後の request 不在で偶然通らないよう上記の末尾要素追加が必要です。

14 件外でも、4 経路を直接固定するため次を既存テストへ追記します。

- [immediate retries exhausted:1037](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1037): 4 回目の fresh qstat が QUE を返し、qdel を許すこと。
- [missing compute marker:1063](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1063): gate が不在を観測し、qdel を打たないこと。
- capsys を持つ M6/HLD テストで、見送り時だけ「ジョブが残っている可能性」が表示されること。

## 新規テストの提案

最低限の vector のうち、RUN、UNKNOWN、rc≠0、QUE、HLD は上記既存テストの更新で直接被覆できます。新規追加は既存にない次の vector だけに絞ります。

| 新規テスト | 純増検出力 |
|---|---|
| `test_fresh_qstat_gate_treats_stg_as_que_and_qdels` | parser 単体の STG→QUE テストではなく、その正規化が実際の qdel 許可へ結線されていることを検出する |
| `test_fresh_qstat_gate_skips_visible_end` | EXT→END parser が存在するだけでなく、END が destructive action を拒否する P3 を固定する |
| `test_request_id_discovery_failure_skips_gate_and_warns` | request ID が無いとき qstat-by-ID/qdel を一切打たず、receipt と人間向け handoff を残す未被覆分岐を固定する |

正例は QUE が qsub parse/discovery test、HLD が HLD timeout test、STG が新規 test です。これにより「単に qdel を全削除した変異」は正例で赤になります。

## 親 brief の P1–P3

- P1「fresh qstat で request 不在なら qdel しない」には賛成です。

  rc=0 不在は既に [`success-request-absent`:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:192)として区別されています。また監視ループ自身も、request 不在を END とみなすのは「一度可視だった」場合だけです（[1188](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1188)）。履歴のない不在には安全な取消状態の証拠がありません。F47 は一度も走らない無効 request でしたが（[failures.md:989](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/docs/failures.md:989)）、F49 は見かけ上の前提に反して実走した反例です（[failures.md:1039](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/docs/failures.md:1039)）。

  ただし「元の immediate qstat が不在だったから永久に禁止」ではありません。fresh gate で対象 request が QUE/HLD として可視になれば取消可です。

- P2「gate qstat は 1 回、retry なし」に賛成です。

  immediate retry [1108–1131](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1108)は投入直後の可視性遅延を吸収するためです。gate は destructive action の許可証拠なので、error/UNKNOWN を retry して後の一瞬の QUE を拾う必要はありません。1 回が判定不能なら、その cleanup は見送るのが fail-closed です。

- P3「END でも qdel しない」に賛成です。

  `_scheduler_state()` は EXT を END へ正規化し（[207–230](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:207)）、監視は END で停止します（[1209](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1209)）。特に marker 不在 qdel はその後の収集段にあるため、END に再度 qdel を打つ利益はありません。

## 危険箇所と扱い

| 危険 | 扱い |
|---|---|
| timeout 予算 | `_run()` の既定 timeout は30秒（[252–267](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:252)）。見送り時は最大30秒、許可後の qdel も timeout すれば cleanup 全体は最大約60秒。監視 deadline/rc は変えず、同期 caller の task duration に cleanup 時間が加算されることだけ明記する |
| signal handler 中の再入 | gate 全体で `BaseException` を捕捉し、`_SignalAbort` を receipt に記録して見送る。gate を再呼出しせず、既存 finally の handler 復元を維持する |
| `_run` が例外 | `qstat.returncode=null`, `scheduler_state=UNKNOWN`, `allowed=false`, `reason=qstat-exception`。元の outcome/rc を上書きしない |
| `request_id is None` | 現行 discovery を1回だけ行う。失敗時は qstat-by-ID も qdel も打たず、gate 未実行証拠・job name・残存警告を記録する |
| submission dir が既に消失 | 現行どおり root を cwd に使う。`exists()` 後に消える race は `_run` 例外として見送り、directory を作り直さない。receipt は既存 fallback 経路を使う |
| qstat と qdel の TOCTOU | atomic conditional qdel は存在しないため残余リスク。両 command を同一 helper 内で sleep/retry なしに連続実行し、receipt は「qdel 時点の保証」ではなく「直前 snapshot」と明示する |
| `active=False` の意味 | scheduler の非活動を意味させず、「この invocation で追加 cleanup をしない」内部 latch のまま維持する。skip receipt/message がジョブ残存可能性を補う |
| fake scheduler の tuple 枯渇 | 枯渇後の `DONE` で誤って negative test が通らないよう、RUN/UNKNOWN/HLD/error の gate 用 state を明示的に末尾追加する |
| scope 混入 | UNKNOWN の権威再確認、timeout 引数の有限性検査、tested-main cutoff は追加しない。T-368/T-370/T-366 は別件のまま |

## 総括

実装面は `dispatch_compute.py` に one-shot・fail-closed な `_fresh_qstat_gated_qdel()` と skip handoff を追加し、4 箇所を同 helper へ差し替えるだけです。許可集合は fresh qstat の「rc=0・request 可視・QUE/HLD」に厳密に縮小し、STG は既存正規化で QUE として扱います。receipt は v2 の additive 拡張、`state_history` は不変です。既存14テストは (a) 8件、(b) 3件、(c) 3件に分類され、純新規は STG、明示 END、request ID 不明の3 vectorです。