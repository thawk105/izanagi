静的読解の結論は**受理不可**です。blocker 2件、major 2件、minor 1件です。pytest その他のテストは実行しておらず、緑は主張しません。

## 裁定11項目の実装忠実性

| # | 判定 | 根拠 |
|---|---|---|
| 1 | **部分的** | target-bound parser 自体は追加されたが、既存 parser が認識する bare `State` を数えず、RUN/QUE 矛盾を通す。`tools/pegasus/dispatch_compute.py:112-115,268-314` |
| 2 | **実装済み** | 先頭英数字 grammar、qstat/qdel 前の拒否、`--` 非導入。`tools/pegasus/dispatch_compute.py:123,1076-1081,1375-1380` |
| 3 | **実装済み** | transient のみ既定3回、permission・rc=0 absent/state 不許可は即拒否。`tools/pegasus/dispatch_compute.py:1084-1139` |
| 4 | **部分的** | 開始時刻・elapsed はあるが、途中の clock 例外を握り潰し、sleep も残予算で切らない。`tools/pegasus/dispatch_compute.py:1037-1051,1085-1126` |
| 5 | **実装済み** | END 観測 latch と fresh QUE/HLD 矛盾拒否を実装。`tools/pegasus/dispatch_compute.py:1323,1508-1515,1142-1143` |
| 6 | **部分的** | 判定部と qdel は分離され、pre-spawn OSError の `attempted=true` も裁定どおり。一方、once-only latch がなく、qdel 後 signal で再実行・結果喪失が可能。`tools/pegasus/dispatch_compute.py:972-999,1002-1165,1684-1721` |
| 7 | **実装済み** | qdel rc≠0/例外を `job_may_remain=true` とし、production 各経路で警告。`tools/pegasus/dispatch_compute.py:1162-1187,1444-1446,1475-1477,1623-1627,1728-1730` |
| 8 | **部分的** | helper の通常 return は policy/gate を必ず持つが、qdel 後 signal が外へ漏れると setup receipt だけが残り得る。`tools/pegasus/dispatch_compute.py:1053-1069,1159-1165,1798-1824` |
| 9 | **実装済み** | docstring とテスト名はいずれも snapshot 限定を明記。`tools/pegasus/dispatch_compute.py:1017-1025`、`orchestrator/tests/test_pegasus_dispatch_compute.py:1004-1028` |
| 10 | **実装済み** | 問題だったテスト列へ gate 用状態と qstat 回数を明示。`orchestrator/tests/test_pegasus_dispatch_compute.py:1479-1516,1783-1864` |
| 11 | **部分的** | meta-test は同一ファイルの top-level 関数内にある直接 `ast.Name` 呼出ししか検査しない。`orchestrator/tests/test_pegasus_dispatch_compute.py:1063-1077` |

### [所見 1] target-bound parser は同一 block の RUN を捨て、QUE と裁定できる / 深刻度 blocker

- **根拠 (`file:line`):** 既存 `_STATE_RE` は `Request State` だけでなく bare `State` も正規の状態 field として認識する一方、gate は `_GATE_REQUEST_STATE_RE` と `_GATE_CURRENT_STATE_RE` しか数えない。`tools/pegasus/dispatch_compute.py:112-115,124-129,216-240,291-314`。追加テストも mixed ID、重複 `Request State`、Request/Current 矛盾だけで、bare `State` との矛盾を試していない。`orchestrator/tests/test_pegasus_dispatch_compute.py:867-901`

- **再現または成立条件:** request ID を `0:424242.nqsv` とし、fresh rc=0 の stdout を次にする。

```text
Request ID = 424242.nqsv
State = RUN
Request State = QUE
```

`_scheduler_state()` は最初の `State = RUN` を返す。しかし `_target_bound_qstat_state()` はその行を無視し、`Request State = QUE` だけを「一意な状態」として返す。結果は `gate.scheduler_state="QUE"`, `allowed=true` となり、`qdel 424242.nqsv` が発行される。これは要求された具体的な RUN→QUE 迂回入力である。

同型として、ID より前の認識可能な state も無条件に捨てられる。

```text
Request State = RUN
Request ID = 424242.nqsv
Current State = Queued
```

- **成果物影響:** transport receipt は `qdel.gate.scheduler_state=QUE`, `allowed=true`, `attempted=true` と偽記録し、実際には RUN と解釈される tests/provenance job を取消対象にする。該当 receipt と child result の対応は受理不能となる。将来この経路を mutation trial に再利用した場合、試行台帳の request/job 対応も失われ、当該 attempt をレポートおよび certified 選択の証拠集合から除外する必要がある。

- **提案:** block 内にある**全ての既存認識形**を一つの scanner で列挙し、bare `State`、`Request State`、`Current State` の重複・矛盾をまとめて拒否する。最初の ID より前に認識可能な state がある出力も malformed/UNKNOWN とする。上記2文字列を negative test に固定する。

### [所見 2] qdel 後 signal に対する once-only latch がなく、再 qdel または偽 receipt になる / 深刻度 blocker

- **根拠 (`file:line`):** signal handler は `_SignalAbort` を非同期に送出する。`tools/pegasus/dispatch_compute.py:1328-1329`。qdel の `_run` が戻った後、`_capture()` と gate metadata の組立ては例外境界外である。`tools/pegasus/dispatch_compute.py:982-999,1152-1165`。さらに3つの内側 callsite は helper が完全 return してから `active=False` にする。`tools/pegasus/dispatch_compute.py:1422-1435,1453-1466,1600-1614`。この間の例外は外側 handler に入り、`active=True` のため gate を再度呼ぶ。`tools/pegasus/dispatch_compute.py:1684-1721`

  「post-qdel exception」テストは `elapsed()` がもともと握り潰す clock 例外しか注入しておらず、この signal seam を踏まない。`orchestrator/tests/test_pegasus_dispatch_compute.py:1031-1060`

- **再現または成立条件:**

  1. permission/absent 経路の fresh gate が QUE を許可する。
  2. 最初の `qdel` の `_run` が戻る。
  3. `tools/pegasus/dispatch_compute.py:995-999` または `:1159-1164` で SIGTERM が到着する。
  4. outer except が同じ request にもう一度 fresh gate を実行する。
  5. stale QUE が返れば qdel は二重実行される。RUN/absent が返れば、最終 receipt は `attempted=false` となり、先に発行済みの qdel が消える。

  queue/overall timeout から既に outer except 内で cleanup 中だった場合、同じ signal は `dispatch()` まで漏れ、`receipt-setup-*.json` のみが残り、実行済み qdel の gate/result 全体が失われ得る。`tools/pegasus/dispatch_compute.py:1798-1824`

- **成果物影響:** `qdel.attempted`、`cleanup_policy`、snapshot、実際の destructive command 数が一致しない。transport receipt を guarded-qdel の proof chain として受理できず、そこを参照する受入レポートも無効になる。

- **提案:** helper 呼出し**前**に create-once の cleanup claim を立て、`active` とは別の latch で二度目を拒否する。qdel 起動要求を receipt の mutable record へ先に確定し、戻り値・例外を同じ record に追記する。qdel return 直後、metadata 各代入位置、receipt 永続化直前へ SIGINT/SIGTERM を注入し、「qdel 最大1回」と「最初の結果が残る」を検査する。

### [所見 3] cleanup の絶対予算は clock 例外と長い retry sleep で無効化される / 深刻度 major

- **根拠 (`file:line`):** 最初の `clock()` 例外だけは拒否するが、その後の `elapsed()` は `BaseException` を無条件に握り潰して直前値を返す。`tools/pegasus/dispatch_compute.py:1037-1051,1071-1074`。予算判定はこの値だけに依存する。`tools/pegasus/dispatch_compute.py:1084-1086,1115-1125`。また transient 後の `sleep(retry_interval_s)` は残予算で切られない。`tools/pegasus/dispatch_compute.py:1125`。現テストは qstat runner 自身が時計を91秒進める形だけである。`orchestrator/tests/test_pegasus_dispatch_compute.py:974-1001`

- **再現または成立条件:**

  - clock が初回だけ `0.0` を返し、2回目以降に OSError を投げる。fresh qstat が QUE なら全予算検査が `0.0` を見て qdel まで進み、receipt は `cleanup_elapsed_s=0.0` と偽記録する。
  - OSError の代わりに signal handler の `_SignalAbort` が `clock()` 中に発生しても握り潰され、signal 後に qdel へ進める。
  - 有限だが大きい `retry_interval_s`、例えば3600秒を渡すと、90秒予算でも1回の sleep が1時間続き、起床後に初めて拒否する。これは「絶対予算」ではない。

- **成果物影響:** `qdel.cleanup_elapsed_s` と90秒 bound が偽になり、cleanup boundedness を受入証拠として参照できない。同期 caller が予算外に停止すれば transport attempt の timeout 分類も変わり、対応する試行・レポート参照を受理集合から外す必要がある。

- **提案:** qdel 前の clock 取得不能は `gate-exception` として必ず拒否する。signal 系 `BaseException` を握り潰さない。sleep は `min(retry_interval_s, remaining_budget)` にする。qdel 後の計時失敗だけは結果を維持しつつ、`cleanup_elapsed_s=null` と `cleanup_elapsed_exception` を記録する。

### [所見 4] ruling が命じた brief 訂正が一件も反映されていない / 深刻度 major

- **根拠 (`file:line`):** ruling は fake scheduler が qdel command を観測しただけで実 NQSV の RUN kill 証拠ではないこと、production caller に provenance があること、campaign 影響は将来影響であること、旧 mutation ledger を resume できないことを明記するよう要求している。`output/insights/2026-08-03_t367-qdel-guard/ruling.md:117-126`

  しかし brief は依然として以下を主張・省略している。

  - タイトルが「走行中ジョブへの qdel を禁じる」と絶対保証を謳う。`brief.md:1`
  - fake test を「RUN 中に qdel を打つことの実証」と一般化する。`brief.md:24-27`
  - F47 の qdel cleanup が恒久対応と衝突しないという撤回済み根拠を残す。`brief.md:32-33`
  - production 経路として run_tests だけを挙げ、provenance を落とす。`brief.md:43`
  - 現行 task enum を通らない campaign trial を現在の直接影響として書く。`brief.md:56-60`
  - dispatcher SHA 変更後に旧 mutation ledger を resume できない旨がない。

- **再現または成立条件:** 段7以降のレポート作成者が canonical ruling ではなく親 brief の前提・実測節を引用する。

- **成果物影響:** レポートの証拠参照が「fake command sequencing」から「実 scheduler の RUN kill 実証」へ不正に格上げされる。現行の直接受理対象も tests/provenance transport から campaign trial へ誤拡張される。旧 ledger の runner identity 不一致も記録されず、fresh ledger 必須性の proof chain が欠ける。

- **提案:** ruling §4 の4項目を brief に反映し、タイトルも「直前 cancellable snapshot 以外では qdel を発行しない」に限定する。実機 kill は未実測、campaign は将来影響、mutation ledger は fresh 必須と明記する。

### [所見 5] caller meta-test は repository closure ではなく局所 direct-call 検査にすぎない / 深刻度 minor

- **根拠 (`file:line`):** テストは `DC.__file__` 一ファイルだけを読み、`tree.body` の top-level 関数と `ast.Name("_best_effort_qdel")` 形式だけを数える。`orchestrator/tests/test_pegasus_dispatch_compute.py:1063-1077`

- **再現または成立条件:** 次のいずれでも meta-test は変わらず通る。

  - 別 production module から `_best_effort_qdel` を import して直接呼ぶ。
  - class method 内から呼ぶ。
  - `deleter = _best_effort_qdel; deleter(...)` と alias 経由で呼ぶ。

  現在の source については静的 repo-wide 検索で追加 caller は見つからず、現時点の実行結果を変える bypass はない。

- **成果物影響:** 現在の receipt・レポート・試行台帳を直接変更する所見ではないため、指定どおり minor とする。将来の bypass 追加時には `cleanup_policy` のない destructive path を偽緑にできる。

- **提案:** repo 全 Python file を対象に import/call を検査するか、低水準 primitive を gate のローカル closure にして外部から名前解決不能にする。少なくとも別 module、class、alias の3変異を meta-test 自身へ当てる。

## その他の観点

- **scope 外2件:** orphan lifecycle は追加されず、discovery の同定規則も `tools/pegasus/dispatch_compute.py:878-937` のまま。receipt は v2 のまま (`:80`)。この2件の混入はない。
- **監視ループ:** `_scheduler_state()` は差分なし (`:216-240`)。gate の観測は `qdel.gate` にのみ入り、`state_history` の append (`:1496-1504`) へ混入しない。`total_deadline`、queue deadline、child/infra rc の意味変更も見つからない。
- **fail-closed:** qstat OSError、permission、request absent、RUN/END/UNKNOWN は通常経路では qdel を拒否する。逆転経路は所見1と所見3。
- **pre-spawn OSError:** qdel runner が起動前に OSError を投げても `attempted=true`, `exception`, `job_may_remain=true` となり、「起動を要求した」という裁定済み意味には合う。`tools/pegasus/dispatch_compute.py:981-999,1162-1164`
- **TOCTOU:** helper docstring と characterization test は snapshot 限定で適切。保証以上を謳う箇所は未訂正の brief であり、所見4の対象。

## 総括

この実装はまだ走行中ジョブ防壁として受理できません。最優先は、既存認識形を漏らす target-bound parser と、qdel 後 signal に対する once-only/receipt 真実性の欠落です。次に cleanup 予算を fail-closed にし、裁定どおり brief を訂正する必要があります。

本レビューは静的読解のみであり、pytest は実行していません。