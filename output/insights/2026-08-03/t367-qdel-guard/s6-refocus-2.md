結論は受理不可です。G1・G3 は closed、G2・G4 は partial です。加えて destructive gate の受理集合拡大を 1 件確認しました。以下は静的読解のみで、pytest・変異実行は行っていません。

## G1〜G4 対応表

| 指示 | 判定 | 根拠 |
|---|---|---|
| G1 | **closed** | `_GATE_STATE_FIELD_RE` の空白位置は `_STATE_RE` / `_CURRENT_STATE_RE` を包含し、非 space/tab 空白も「見落とさず」検出後に拒否する。[dispatch_compute.py:112–127](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:112)、[dispatch_compute.py:266–329](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:266)。form-feed、vertical-tab、NBSP、CR/LF 組合せで新規迂回を試みたが、既存 parser が認識し scanner が不在扱いする入力は構成できなかった。テストも parser 認識と qdel ゼロを結んでいる。[test_pegasus_dispatch_compute.py:953–991](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:953) |
| G2 | **partial** | `cleanup_claimed` は helper 前に立ち、再呼出しは同じ record を返すため qdel 二重発行は防げる。[dispatch_compute.py:1428–1454](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1428)。テストも `signal.getsignal()` で実際の登録 handler を呼んでいる。[test_pegasus_dispatch_compute.py:1252–1326](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1252)。ただし永続化中／直後の signal は disk receipt に反映されない競合窓が残る。 |
| G3 | **closed** | `request_id is None` が初回 `clock()` より先に確定し、旧 `qdel.reason`、`job_name`、`submission_dir` を保持する。[dispatch_compute.py:1070–1082](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1070)。テストは clock 呼出しゼロと metadata を固定している。[test_pegasus_dispatch_compute.py:2014–2044](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:2014) |
| G4 | **partial** | 指摘された `deleter = dc._best_effort_qdel` は検出するようになったが、alias 伝播は `Assign` / `AnnAssign` の単純名 target だけであり、既定引数や unpacking を迂回できる。[test_pegasus_dispatch_compute.py:1329–1378](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1329) |

### [所見 1] field 非依存の正規化が裁定外の state 文法を取消可能として受理する / 深刻度 blocker

根拠: 既存 parser は `Request State` / bare `State` には略号だけ、`Current State` には full form だけを認める。一方 `_gate_state_value()` は両語彙を全 field に適用し、bare `State` だけを個別制限している。[dispatch_compute.py:112–115](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:112)、[dispatch_compute.py:241–263](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:241)、[dispatch_compute.py:319–328](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:319)。

再現または成立条件:

```text
Request ID = 424242.nqsv
Request State = Queued
```

または:

```text
Request ID = 424242.nqsv
Current State = QUE
```

いずれも `_scheduler_state()` は `None` だが gate は `QUE` を返し、`allowed=true`、`qdel` 発行へ進む。正例テストは `Request State=QUE/HLD/STG` と `Current State=Queued/Held/Staging` だけで、この交差形を拒否していない。[test_pegasus_dispatch_compute.py:820–885](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:820)

成果物影響: receipt が本来の `scheduler_state=UNKNOWN, allowed=false, attempted=false` ではなく `QUE, true, true` となる。tests/provenance job を未裁定文法で取消し、受入レポートの transport proof chain を無効にする。現行 certified 選択への直接経路はないが、将来 T-360 の試行台帳にも波及する。

提案: field ごとに既存 parser の値文法を使う。上記交差形と `Request State=Waiting` を helper 経由で qdel ゼロに固定する。

### [所見 2] pending signal が永続 receipt の snapshot 後に到着すると原因が消える / 深刻度 major

根拠: handler は memory 上の `receipt["outcome"]` を更新するが、各経路は `_persist_receipt()` を一度呼んだ後に pending flag を確認するだけで、再永続化しない。[dispatch_compute.py:1412–1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1412)、[dispatch_compute.py:1555–1557](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1555)、[dispatch_compute.py:1803–1805](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1803)。テストの `persist` seam は handler を実永続化の「前」に呼んでいるだけである。[test_pegasus_dispatch_compute.py:1292–1301](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1292)

再現または成立条件:

1. qdel 結果まで確定する。
2. `_persist_receipt()` が primary receipt を書き終える。
3. return 直後、pending check 前に SIGTERM を処理する。
4. memory 上は signal outcome になるが、create-only の disk receipt は旧 F47/timeout 理由のまま。
5. dispatcher は rc=16 で終了する。

qdel は一回のままで process-facing rc も 16 だが、receipt への signal 伝播だけが失敗する。永続化自体が両候補で失敗した場合も戻り値を検査していない。

成果物影響: transport receipt の `outcome.reason` と受入レポートの原因参照が実 signal から旧 infra 理由へ変わる。整数 rc は同じでも proof chain は原因を偽る。

提案: post-claim 終了処理を一箇所へ集約し、signal の block/snapshot、永続化成功確認、終了伝播を一つの critical section にする。`real_persist()` の完了後に登録 handler を呼ぶテストを追加する。

### [所見 3] default-argument alias が caller 閉包を迂回する / 深刻度 minor

根拠: scanner は function default を alias binding として扱わない。[test_pegasus_dispatch_compute.py:1338–1378](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1338)

再現または成立条件:

```python
from tools.pegasus import dispatch_compute as dc

def cleanup(deleter=dc._best_effort_qdel):
    deleter(...)
```

default の `ast.Attribute` は `Assign` ではなく、call は未知の `ast.Name` なので imports/callers とも空になり得る。

成果物影響: 現ソースにはこの caller がなく、現在の receipt・certified 値は変わらないため minor とする。M10 や将来変更では gate を持たない qdel が偽緑となる。

提案: alias 伝播を増築し続けるより、`_best_effort_qdel` の全 Load reference を許可箇所以外で拒否する。上記 default、tuple unpacking、`getattr` の synthetic test を追加する。

### [所見 4] M11 の guard-only 除去は現 signal テストを通過する / 深刻度 major

根拠: `claim_cleanup_once()` の再入防止本体は `if cleanup_claimed: return receipt["qdel"]` だが、現テストの handler は claim 後に例外を送出せず return する。そのためこの guard だけを削除しても二回目の claim 自体が発生しない。[dispatch_compute.py:1414–1426](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1414)、[dispatch_compute.py:1428–1439](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1428)、[test_pegasus_dispatch_compute.py:1262–1301](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1262)

再現または成立条件: `dispatch_compute.py:1430–1431` の guard だけを削除する。3 seam とも handler が戻るため一回しか `claim_cleanup_once()` が呼ばれず、既存期待は維持される。

成果物影響: mutation trial ledger の M11 は `SURVIVED / matches_expectation=false` になる。これを別の coupled mutation の KILL で代用すると、受入レポートが latch 自体の検出力を偽る。

提案: qdel result 固定後に `_capture` などから非 signal 例外を送出し、outer `except` が `claim_cleanup_once()` を再度呼ぶテストを追加する。guard 除去時に record 上書きまたは二回目の gate/qdel が観測される形にする。

## 回帰の検査

- 2 回目 fix の空白変更について、既存 parser が認識する state の見落としは再構成できなかった。ただし現在の受理集合全体は所見1の field 非依存正規化により裁定より広い。
- fix2 の焦点テストに assert 削除、skip、xfail、期待緩和はない。全 diff にある旧 qdel 期待の反転は RUN・END・UNKNOWN・permission・request 不在を拒否する裁定済み縮小に対応している。
- `_scheduler_state()` は不変。[dispatch_compute.py:214–238](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:214)
- `state_history` の生成値は不変で、追加された `terminal_history_end` は cleanup gate への side channel に留まる。[dispatch_compute.py:1590–1619](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1590)
- child rc の意味は不変。pending signal は既存 infra rc=16 へ畳まれる。CLI は最終的に `sys.exit()` するが、library API 自体は signal を再送出せず 16 を返す。
- claim 前の signal は従来どおり `_SignalAbort` として outer `except` へ入る。claim 後は pending 経路となる。早期 `return` でも `finally` による inner handler 復元、その後 outer handler 復元は静的には維持される。[dispatch_compute.py:1778–1826](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1778)、[dispatch_compute.py:1916–1921](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1916)
- receipt schema は v2 のまま。ただし所見2の競合窓では同じ v2 receipt の原因値が実際の signal と食い違う。

## 変異生存の最終予測

| ID | 予測 | 静的根拠 |
|---|---|---|
| M01 | KILL | fresh RUN で qdel ゼロを要求。[test:2126](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:2126) |
| M02 | KILL | rc=153＋対象ID＋QUEを3回返し、qdelゼロを固定。[test:1069](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1069) |
| M03 | KILL | mixed block、重複、矛盾で global scan への退行が赤になる。[test:905](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:905) |
| M04 | KILL | `request-absent` 語彙を固定。ただし diagnostic pin であり受理集合 KILL には数えない。[test:1599](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1599) |
| M05 | KILL | END 履歴後の fresh QUE で qdelゼロと conflict reason を固定。[test:1728](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1728) |
| M06 | KILL（semantic mutant） | observable な最終 `job_may_remain` を false/欠落にすれば非ゼロ・例外テストが赤。[test:1884](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1884)。単一代入削除は冗長性による等価変異なので再 anchor が必要。 |
| M07 | KILL | 3 budget check の一括除去は qstat回数・sleep列・reasonを変える。[test:1099](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1099) |
| M08 | **KILL** | QUE/HLD/STG と Current State-only の両正例が qstat→qdel 完全列を要求する。[test:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:820)、[test:859](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:859) |
| M09 | KILL | malformed ID で scheduler command ゼロを固定。[test:1007](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1007) |
| M10 | **SURVIVE** | default-argument alias なら scanner が caller を検出しない。 |
| M11 | **SURVIVE** | guard-only 除去では handler suppression が再入を mask する。 |

SURVIVE を KILL する追加テスト:

- M10: `def cleanup(deleter=dc._best_effort_qdel): deleter()` を synthetic source に追加し、caller `cleanup` の検出を要求する。
- M11: qdel return 後に `_capture` から例外を送出して outer `except` へ再入させ、qstat一回・qdel一回・最初の結果 record を要求する。

## 残存リスク

- qstat→qdel は非 atomic で、snapshot 後の QUE→RUN を防がない。これは docstring と characterization test では適切に限定されている。[dispatch_compute.py:1043–1047](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1043)、[test:1184](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1184)
- 「fresh」は直前に command を発行したという意味だけで、scheduler 応答のキャッシュ・時刻・権威性は検証しない。
- gate 拒否、permission、request 不在、qdel failure では孤児 job が残る。reconciliation、source 復元、次回投入との lifecycle 統合は scope 外。
- qdel rc=0 後の不在確認はない。したがって `job_may_remain=false` は「qdel rc=0」の言い換えであり、実際の消滅保証ではない。
- cleanup 90 秒は hard wall-clock bound ではない。各 `_run` は固定30秒 timeout のままで、最後の command 分だけ超過し得る。[dispatch_compute.py:350–365](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:350)
- request discovery は job name / submission directory に依存し、旧 job 誤同定の強化は裁定上 scope 外。[dispatch_compute.py:893–952](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:893)
- fake scheduler だけであり、実 NQSV の output grammar、RUN 中 qdel の実挙動、OS signal delivery は未検証。[test:1–5](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1)
- SIGINT/SIGTERM だけを扱い、claim 後の複数 signal は最初の一件へ畳む。cleanup 中は終了が最大 cleanup 所要分遅れる。
- primary/fallback receipt の双方が失敗し得る。error 経路は `_persist_receipt()` の `None` を検査していない。
- brief は実機 kill 未実測と正しく限定する一方、成果物影響で「走行中ジョブが殺される」と断定しており過大。[brief.md:27–28](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/output/insights/2026-08-03_t367-qdel-guard/brief.md:27)、[brief.md:68–69](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/output/insights/2026-08-03_t367-qdel-guard/brief.md:68)
- `test_cleanup_signal_after_qdel_is_once_only_and_preserves_first_result` と `test_best_effort_qdel_production_caller_is_only_fresh_gate` は、所見2・3の未検査窓に対してテスト名が保証を盛っている。
- dispatcher source SHA が変わるため、旧 mutation ledger の resume は保証されない。

## 総括

2 回目の fix は G1 と G3 を閉じたが、G2 と G4 は閉じていません。さらに field 非依存の state 正規化が destructive gate の受理集合を裁定より広げています。変異予測は M10・M11 が SURVIVE、特に M11 は現在の handler suppression による mask です。

したがって段 6 は NO-GO です。3巡目の静的最終確認としては、これ以上「所見ゼロ」や pytest 緑を推定して閉じる根拠はありません。