結論は受理不可です。静的読解で blocker 1 件、major 1 件、minor 2 件を確認しました。テストは実行しておらず、pytest 緑は主張しません。

## 所見ごとの対応表

| 対象 | 判定 | 静的根拠 |
|---|---|---|
| レビュー1 所見1 | partial | 通常の bare `State`、ID 前 state、重複・矛盾例は追加されたが、既存 parser と scanner の先頭空白 grammar が不一致で迂回可能。`tools/pegasus/dispatch_compute.py:112-127,266-319`、`orchestrator/tests/test_pegasus_dispatch_compute.py:905-963` |
| レビュー1 所見2 | regressed | mutable record と cleanup latch は追加されたが、claim 後の実 SIGINT/SIGTERM を無条件に握り潰す。テストは signal handler を通さず `_SignalAbort` を直接送出している。`tools/pegasus/dispatch_compute.py:977-1014,1195-1226,1390-1423`、`orchestrator/tests/test_pegasus_dispatch_compute.py:1211-1274` |
| レビュー1 所見3 | closed | qdel 前の clock 例外は拒否、sleep は残予算で制限、qdel 後の計時失敗は結果と別 field に保存される。`tools/pegasus/dispatch_compute.py:1062-1093,1126-1169,1197-1225` |
| レビュー1 所見4 | closed | fake scheduler の射程、provenance caller、現在/将来影響、旧 ledger resume 不可が訂正済み。`output/insights/2026-08-03_t367-qdel-guard/brief.md:23-41,52-53,64-72` |
| レビュー1 所見5 | partial | tools/orchestrator 全走査、直接 alias、class、直接 import は追加されたが、attribute を別名へ束縛する caller は漏れる。`orchestrator/tests/test_pegasus_dispatch_compute.py:1277-1321,1359-1372` |
| レビュー2 所見1 | partial | M02 と multi-replacement M07 は検出可能になった。一方、意味論的 M10 には生存形が残る。`orchestrator/tests/test_pegasus_dispatch_compute.py:1028-1140,1277-1372` |
| レビュー2 所見2 | closed | `Current State = Queued/Held/Staging` 単独形を qstat→qdel 完全列で固定。`orchestrator/tests/test_pegasus_dispatch_compute.py:859-885` |
| レビュー2 所見3 | closed | qdel 非ゼロ・例外の双方で gate qstat 1 回、qdel 1 回を含む全 command 列を固定。`orchestrator/tests/test_pegasus_dispatch_compute.py:1814-1858` |
| レビュー2 所見4 | partial | 通常の discovery 失敗では旧 reason を復元したが、初回 cleanup clock 例外との複合経路では再び壊れる。`tools/pegasus/dispatch_compute.py:1062-1076,1099-1113` |
| レビュー2 所見5 | closed | 指定6テストへ総 qstat 回数または gate attempt 件数が追加された。`orchestrator/tests/test_pegasus_dispatch_compute.py:681-727,1143-1208,1819-1853` |
| F1 | partial | ASCII の指定2例は閉じたが、既存 `_STATE_RE` が認識する非 space/tab 空白付き state を統合 scanner が見落とす。`tools/pegasus/dispatch_compute.py:112-127,291-319` |
| F2 | regressed | qdel 最大1回と結果固定は成立する一方、実 signal は claim 後に無視され、テストの注入経路と本番経路が一致しない。`tools/pegasus/dispatch_compute.py:1390-1423` |
| F3 | closed | clock 失敗、長い retry sleep、qdel 後計時失敗は指示どおり処理される。裁定どおり `_run` の30秒 timeout 自体は残予算へ縮めていない。`tools/pegasus/dispatch_compute.py:1078-1093,1126-1169,1197-1225` |
| F4 | closed | rc=153かつ対象ID＋QUEを3回返しても qdel ゼロを固定。`orchestrator/tests/test_pegasus_dispatch_compute.py:1028-1055` |
| F5 | closed | 3つの Current State-only 正例がある。`orchestrator/tests/test_pegasus_dispatch_compute.py:859-885` |
| F6 | closed | 非ゼロ・例外とも command 列が完全一致。`orchestrator/tests/test_pegasus_dispatch_compute.py:1814-1858` |
| F7 | partial | 通常経路は復元したが、`request_id=None` かつ初回 clock 例外では旧 reason と旧 job metadata が失われる。`tools/pegasus/dispatch_compute.py:1062-1076,1099-1113` |
| F8 | closed | 指定6箇所すべてに件数 assert がある。`orchestrator/tests/test_pegasus_dispatch_compute.py:681-727,1143-1208,1819-1853` |
| F9 | partial | 指示された基本形は検出するが、attribute-alias 形で迂回できる。`orchestrator/tests/test_pegasus_dispatch_compute.py:1284-1321` |

### [所見 1] state scanner の空白 grammar 不一致で RUN→QUE を迂回できる / 深刻度 blocker

根拠: 既存 `_STATE_RE` は行頭に `\s*` を使う一方、gate scanner は `[ \t]*` しか許さない。`tools/pegasus/dispatch_compute.py:112-127`。したがって form-feed、vertical-tab、NBSP 等を先頭に置いた既存認識可能 state は scanner から消える。追加テストは通常の ASCII 行だけである。`orchestrator/tests/test_pegasus_dispatch_compute.py:905-963`

再現または成立条件: 次の `\x0c` は4文字ではなく、実際の form-feed 1 byte とする。

```text
Request ID = 424242.nqsv
\x0cState = RUN
Request State = QUE
```

`_STATE_RE` は先にある bare `State = RUN` を認識するが、`_GATE_STATE_FIELD_RE` はその行を認識しない。gate が数えるのは `Request State = QUE` だけなので、`_target_bound_qstat_state()` は `QUE` を返し、`qdel 424242.nqsv` へ進む。

ID 前 state も同様に迂回できる。

```text
\x0cState = RUN
Request ID = 424242.nqsv
Current State = Queued
```

成果物影響: transport receipt は `qdel.gate.scheduler_state="QUE"`、`allowed=true`、`qdel.attempted=true` を記録する。実際には RUN と認識可能な tests/provenance job が取消対象となり、当該 receipt と受入レポートの proof chain は無効になる。将来 mutation trial がこの経路を使う場合、attempt と結果の対応も失われ、certified 選択の証拠集合から除外が必要になる。

提案: 行頭を既存 parser と同じ認識集合にするか、`splitlines()` 後の field-specific scanner に統一する。少なくとも `\x0c`、`\x0b`、NBSP を付けた bare state の前置・後置・矛盾テストを追加する。

### [所見 2] once-only fix が claim 後の SIGINT/SIGTERM を無言で破棄する / 深刻度 major

根拠: `cleanup_claimed` が真なら signal handler は例外を送出せず return する。`tools/pegasus/dispatch_compute.py:1390-1395`。一方、3 seam テストは signal handler を呼ばず、patch 内から `_SignalAbort` を直接 raise している。`orchestrator/tests/test_pegasus_dispatch_compute.py:1221-1256`

再現または成立条件:

1. fresh gate が QUE/HLD を許可し、qdel が結果を返す。
2. qdel return 後から receipt 永続化前までに実 SIGTERM を送る。
3. handler は `cleanup_claimed=True` を見て return する。
4. outer exception 境界には入らず、receipt の `outcome.reason` に signal は残らず、プロセスも termination 要求を無視して処理を続ける。

qdel の二重発行自体は latch により防げるが、signal を握り潰す必要はない。現在のテストが示す `_SignalAbort` 経路は、本番 signal では到達しない。

成果物影響: `qdel` の最初の結果は残る一方、transport receipt の `outcome.reason` は `_SignalAbort: signal 15` ではなく、元の timeout/F47理由のままになる。外部 supervisor の取消と scheduler/transport failure の分類が混ざる。supervisor が無応答後に SIGKILL へ昇格する条件では、receipt 自体が永続化前に失われる。受入レポートの transport 原因参照を信用できない。

提案: handler は `pending_cleanup_signal` を記録し、once-only record の永続化後に signal を再送出または明示的に返す。テストは `_SignalAbort` を直接投げず、実際に登録された handler を呼び、signal field・qdel回数・receipt永続化を同時に固定する。

### [所見 3] 初回 clock 例外が復元済みの旧 `qdel.reason` を再び壊す / 深刻度 minor

根拠: helper は `request_id is None` の判定より先に `clock()` を呼ぶ。初回 clock 例外の専用 return は `reason="fresh-qstat-gate-denied"` を直接書く。`tools/pegasus/dispatch_compute.py:1062-1076`。旧 reason への変換と `job_name` / `submission_dir` の付与は後段の `denied()` にしかない。`:1099-1113`。現テストは正常な clock の discovery 失敗だけである。`orchestrator/tests/test_pegasus_dispatch_compute.py:1920-1941`

再現または成立条件: qsub 出力の解析と discovery が失敗して `request_id=None` となり、cleanup 最初の clock 取得も例外になる。

成果物影響: v2 receipt の `qdel.reason` が旧値 `"qsub accepted but request ID discovery failed"` から `"fresh-qstat-gate-denied"` に変わり、`job_name` と `submission_dir` も欠落する。既存の整数 rc consumer と現行 certified 選択値には直接影響しないため、深刻度は minor とする。

提案: request ID 不在を clock より先に処理するか、初回 clock 例外も共通 `denied()` 相当の builder を通し、旧 reason と既存 metadata を保持する。複合条件のテストを追加する。

### [所見 4] F9 scanner は attribute-alias 版 M10 を見逃す / 深刻度 minor

根拠: alias 伝播は代入右辺が `ast.Name` の場合だけである。`orchestrator/tests/test_pegasus_dispatch_compute.py:1292-1299`。`ast.Attribute` は直接 call の場合だけ検出される。`:1314-1319`

再現または成立条件:

```python
from tools.pegasus import dispatch_compute as dc

deleter = dc._best_effort_qdel

def cleanup():
    deleter(...)
```

代入右辺は `ast.Attribute`、call は alias 名の `ast.Name` なので、scanner は import も caller も報告しない。

成果物影響: 現在のソースにはこの caller がなく、現在の receipt・レポート・certified 選択値は変わらないため minor とする。ただし M10 や将来変更で混入すると、`cleanup_policy` / `gate` を持たない直接 qdel が偽緑になり、transport proof chain を壊す。

提案: `_best_effort_qdel` を指す `ast.Attribute` からの alias 伝播も解析し、この文字列を scanner 自己テストへ追加する。さらに強くするなら、primitive 名ではなく生の `["qdel", ...]` 発行箇所を閉包検査する。

## 回帰の検査

- qdel 受理集合は、通常の ASCII 入力では裁定どおり QUE/HLD/STG と対応する Current State-only に限定されている。RUN、END、UNKNOWN、permission、request 不在は拒否される。
- ただし所見1の制御空白形では malformed RUN＋QUE を `QUE` と受理するため、実効受理集合は裁定より広い。ここが受理拒否の主因である。
- fix 前 snapshot との差分では、既存 assert の削除、skip、xfail、期待緩和は見つからない。指定箇所への assert 追加と新規テストが中心である。全 `git diff` にある旧 qdel 期待の反転は前段の裁定済み許可集合縮小であり、今回の fix による緩和ではない。
- `_scheduler_state()`、監視用 `state_history`、task enum、qsub・収集・child rc の意味変更は見つからない。
- receipt schema は v2 のままで、通常成功時の `request_id/returncode/stdout/stderr` は維持される。ただし所見3の複合経路では既存 reason と metadata が壊れる。
- 現在の静的 repo-wide 検索では `_best_effort_qdel` の production caller は `_fresh_qstat_gated_qdel()` だけである。ただし F9 の検査能力自体は閉じていない。
- claim 後に signal を無視する変更は受理集合ではなく、process termination と receipt の原因語彙を回帰させている。

## 変異生存の再予測

| ID | 予測 | 根拠 |
|---|---|---|
| M01 | KILL | fresh RUN で qdel ゼロを固定。`orchestrator/tests/test_pegasus_dispatch_compute.py:2023-2051` |
| M02 | KILL | rc=153＋対象ID＋QUEを3回返しても qdel ゼロ。`:1028-1055` |
| M03 | KILL | mixed block、同一 field 重複、矛盾、通常 bare state の直接 parser assert が赤になる。`:905-950` |
| M04 | KILL | `gate.reason="request-absent"` を固定。ただし ruling どおり診断 pin であり、受理集合 kill ではない。`:1529-1549` |
| M05 | KILL | terminal END 後の fresh QUE で qdel ゼロと `terminal-history-conflict` を固定。`:1658-1673` |
| M06 | KILL | observable な最終 `job_may_remain` を落とす意味論版なら、非ゼロ・例外の双方が赤になる。`:1819-1858` |
| M07 | KILL | 3予算検査の multi-replacement は qstat回数または reason を変える。`:1058-1140` |
| M08 | KILL | QUE/HLD/STG と Current State-only の正例が qdel 完全列を要求する。`:824-885` |
| M09 | KILL | malformed ID で command ゼロを要求する。`:966-980,1944-1956` |
| M10 | **SURVIVE** | attribute-alias 形なら scanner を迂回できる。`:1277-1321` |
| M11 | KILL | latch を外すと3 seamのいずれかで最初の qdel record が上書きされる。`:1211-1274` |

M10 を KILL するには、次の synthetic source を `_best_effort_qdel_references()` へ渡し、caller を検出するテストを追加する必要があります。

```python
from tools.pegasus import dispatch_compute as dc
deleter = dc._best_effort_qdel

def cleanup():
    deleter(...)
```

なお M06 は単一の代入削除では、初期値・low-level設定・最終再計算が冗長なため等価変異になり得ます。実際に最終 field を欠落または false にする semantic multi-replacement として anchor を確定しなければなりません。

## 総括

fix は所見を閉じ切っていません。F1 は制御空白による具体的な RUN→QUE 迂回が残るため blocker、F2 は once-only の代償として実 signal を無言で捨てる回帰があります。F7 と F9 も partial です。変異では M10 の生存形が残ります。

静的読解のみであり、pytest・変異・その他の実行検査は行っていません。