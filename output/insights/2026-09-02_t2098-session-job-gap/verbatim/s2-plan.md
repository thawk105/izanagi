## estimand

母集合は、`/work/SFC/tanab/.izanagi-acceptance-shards/` 直下に存在する 2026-09-02 時点の session 743 本とする。主推定量の分母は、後述する完全性条件を満たした session 数 `n_paired` とし、実行時に確定して必ず表示する。

session `s`、shard `j in {0,1,2}` について次を定義する。

- `F_sj`: `shard-j.confirm.json` の Lustre mtime
- `H_sj`: `shard-j.handled.json` の Lustre mtime
- `C_sj`: NQSV `Created Request Time`
- `E_sj`: NQSV `Ended Request Time`
- `S_s = max_j(H_sj) - min_j(F_sj)`
- `J_s = max_j(E_sj - C_sj)`
- `R_s = S_s - J_s`

主推定量は `R_s` の per-session 分布であり、中央値、p25、p75、p90、最小、最大、負値件数を出す。`median(R_s)` が中心値である。分布統計量どうしを引いた `median(S)-median(J)` は主推定量ではない。

親の P1 は正しい。338 秒は 549 session、263 秒は 1297 job の中央値なので、`338-263=75` 秒は母集合も観測単位も異なる非対差である。script は次も併記して、この違いを数値で検査する。

- D1320 再現用の `median(session span)` とその `n`
- 全 parse 済み job の `median(Created→Ended)` とその `n`
- 同一の完全対集合に限定した `median(S_s)-median(J_s)`
- 主値である `median(S_s-J_s)`

後二者も一般には一致しない。区間ごとの中央値を足して残差中央値を再構成することもしない。加法性は per-session 行についてのみ主張する。

`S_s` は「最初の confirm から最後の handled まで」という session envelope とする。参考列として `max_j(H_sj-F_sj)` も出し、両定義の差を隠さない。

## 区間分解

`b` を `E_sj-C_sj` が最大の shard とする。同率なら主残差自体は不変だが内訳が一意でないため、全候補の内訳を保存し、要約用 canonical 値だけ shard 番号最小を使う。

各 session について次の 4 項を作る。

| 項 | 始点 | 終点 | 時計 |
|---|---|---|---|
| `start_skew` | `min_j mtime(confirm_j)` | `mtime(confirm_b)` | Lustre |
| `pre_created_raw` | `mtime(confirm_b)` | NQSV `Created_b` | 時計跨ぎ |
| `post_ended_raw` | NQSV `Ended_b` | `mtime(handled_b)` | 時計跨ぎ |
| `end_skew` | `mtime(handled_b)` | `max_j mtime(handled_j)` | Lustre |

表示値による恒等式は、

```text
R_s
= start_skew
+ pre_created_raw
+ post_ended_raw
+ end_skew
```

である。実際、

```text
(F_b-F_min) + (C_b-F_b) + (H_b-E_b) + (H_max-H_b)
= (H_max-F_min) - (E_b-C_b)
= S_s-J_s
```

となる。script は浮動小数ではなく `mtime_ns` と整数秒を ns に変換して計算し、各行で恒等式の差が 0 ns であることを確認する。ただし、これは代数的 closure であって独立検査には数えない。

`b` が最後に handled された shard とは限らない。`start_skew` と `end_skew` は、その shard の違いを明示的に吸収する項である。併せて次の一致率を出す。

- `argmax job span == argmax handled mtime`
- `argmax job span == argmax shard confirm→handled span`
- 最大 job span の同率 session 数

`login-collection.log` は加法項へ入れない。[acceptance_shards.py:1306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/acceptance_shards.py:1306) から全 worker を開始し、[acceptance_shards.py:1335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/acceptance_shards.py:1335) で collection を呼び、その後 [acceptance_shards.py:1353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/acceptance_shards.py:1353) から worker 結果を待つため、collection は job と重なる。独立の overlap 診断として扱う。

## 時計

静的な時計 offset を `o = NQSV clock - Lustre clock` とする。

残差 `R_s` 自体は、`S_s` と `J_s` がそれぞれ同一時計内の duration なので、一定の offset には依存しない。一方、区間内訳では、

```text
pre_created_raw = pre_created_physical + o_created
post_ended_raw  = post_ended_physical - o_ended
```

となる。したがって静的 offset は二項の和で相殺するが、`o_ended-o_created` という clock drift は残る。個別の跨時計項を raw 値のまま「遅延」と呼ばない。

保存済み marker の因果順序から offset を挟む。NQSV 表示の 1 秒分解能を `q=1s` として外向きに広げる。

- Created より前の Lustre marker: `intent`, `confirm`
- Created より後の marker: `compute-visible`, `report.json`, shard `junit.xml`, accounting stderr, `handled`
- Ended より前の marker: `intent`, `confirm`、存在すれば `compute-visible`, `report.json`, shard `junit.xml`
- Ended より後の marker: accounting summary を含む stderr、`handled`

各 endpoint の範囲は次とする。

```text
o_created_lo = max(Created - later_lustre_mtime - q)
o_created_hi = min(Created - earlier_lustre_mtime + q)

o_ended_lo = max(Ended - later_lustre_mtime - q)
o_ended_hi = min(Ended - earlier_lustre_mtime + q)
```

そこから、

```text
pre_created_physical:
  [pre_created_raw-o_created_hi,
   pre_created_raw-o_created_lo]

post_ended_physical:
  [post_ended_raw+o_ended_lo,
   post_ended_raw+o_ended_hi]

drift = o_ended-o_created:
  [o_ended_lo-o_created_hi,
   o_ended_hi-o_created_lo]

physical residual:
  [R_s+drift_lo, R_s+drift_hi]
```

を出す。因果順序から duration は非負なので各 duration 範囲を `[0,+inf)` と交差させる。範囲が空なら値を補正せず `clock_bound_inconsistent` として auxiliary 集計から落とすが、raw の主推定量からは落とさない。

「job 中は offset 一定」と置いた共通交差範囲も参考値として出せるが、仮定付きと明記する。endpoint 別範囲と drift 範囲を権威とし、offset の midpoint を採用した一点補正は行わない。

login collection については、[run_tests.py:1435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/run_tests.py:1435) の subprocess 完了後、[run_tests.py:1446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/run_tests.py:1446) からログを組み立て、[run_tests.py:1450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/run_tests.py:1450) で書く。従って log mtime は collection 完了の上側 proxy である。

- log mtime が最後の shard report/junit mtime 以下なら、同一時計だけで「少なくとも最後の job 完了より前」を証明できる。
- NQSV の最終 `Ended` と比較する場合は、その shard の `o_ended` 範囲を使う。
- log 書込み時刻が最終 Ended より後でも、collection 自体が後だったとは断定しない。subprocess return から log 書込みまでが未計測だからである。

## 除外規則

母集合 743 本すべてを `sessions.csv` に 1 行ずつ残す。除外 session も捨てず、全理由を列に保持する。

主推定量から除外する条件は次である。

- session directory を list/stat できない
- shard `{0,1,2}` のいずれかが完全に欠落
- いずれかの `confirm` または `handled` が欠落、非 regular file、stat 失敗
- shard に対応する accounting stderr が 0 本、複数で曖昧、または summary を一意に parse できない
- `Created` または `Ended` が欠落
- `Request Name` が対象 shard と不一致
- 同一時計内で `Created > Ended` または `min(confirm) > max(handled)`
- timestamp が非有限、timezone 解釈不能

次は主推定量からは除外しない。

- `queue-wait-timeout` や qdel。必要な Created/Ended と marker があれば含め、outcome 別に層別する。
- `Started` 欠落。queue 診断と一部 offset bound だけを欠測にする。
- `report.json`、shard `junit.xml`、`login-collection.log`、`receipt.json` の欠落。それぞれ auxiliary 分母だけを減らす。
- 負の raw residual。観測結果として保持し、件数を出す。
- 最大 job span の同率。候補を全保存する。

`summary.json` では、少なくとも次の counter をゼロでも省略せず出す。

```text
inventory_sessions
primary_included_sessions
primary_excluded_sessions
unreadable_session_dirs
file_stat_failures
missing_shards
missing_confirm
missing_handled
accounting_missing
accounting_ambiguous
accounting_parse_failures
missing_created
missing_started
missing_ended
missing_receipt
receipt_parse_failures
missing_report
missing_shard_junit
missing_login_collection
queue_wait_timeout_shards
qdel_or_nonstarted_shards
clock_bound_unavailable
clock_bound_inconsistent
negative_residual_sessions
```

複数理由 counter と別に、優先順位付きの `primary_exclusion_reason` を 1 個持たせ、`included + exclusive exclusions = 743` を確認できるようにする。これにより「読めなかった 0 件」「parse 失敗 0 件」を明示できる。

## script 契約

script の予定 path は `tools/analyze_acceptance_session_job_gap.py`。repo 内に一時作成するが commit せず、親が実行後に repo 外へ退避する。

実行形は次とする。

```text
python3 tools/analyze_acceptance_session_job_gap.py \
  --root /work/SFC/tanab/.izanagi-acceptance-shards \
  --output-dir <parentが指定する保存先> \
  --expected-sessions 743 \
  --shard-count 3 \
  --scheduler-timezone Asia/Tokyo \
  --scheduler-resolution-s 1
```

読む path は次だけである。

```text
<root>/<sid>/dispatch-intents/shard-N.{intent,confirm,handled}.json
<root>/<sid>/shard-N/dispatch/shard-N/izdw-shard-N.e*
<root>/<sid>/shard-N/dispatch/shard-N/receipt.json
<root>/<sid>/shard-N/dispatch/shard-N/compute-visible.json
<root>/<sid>/shard-N/report.json
<root>/<sid>/shard-N/junit.xml
<root>/<sid>/login-collection.log
```

marker、report、junit、login log は `stat` の mtime/size だけを読む。内容を読むのは accounting stderr と receipt JSON だけとする。receipt の `queue_wait_s` は NQSV accounting の代用品にしない。

書くものは `--output-dir` 配下だけとする。

- `sessions.csv`: 743 session 全行、適格性、残差、4 項、時計範囲、除外理由
- `shards.csv`: shard 単位の元測点、accounting 値、receipt 診断、欠測理由
- `summary.json`: estimand、分母、分布、counter、独立検査結果、引数
- `critical-ties.csv`: 最大 job span が同率だった session の全候補。0 件でも header を書く

標準出力は自由文を混ぜず、最後に次の 1 行だけ出す。

```text
T2098_RESULT {"status":"ok","inventory_sessions":743,"primary_included_sessions":N,...}
```

診断は標準エラーへ `T2098_DIAGNOSTIC <json>` 形式で出す。`--expected-sessions` 不一致、入力 root 不正、出力不能は非 0 終了とし、部分結果を成功扱いしない。

## file:line 実装プラン

予定する 1 script 内の責務は次の行帯に固定する。

- `tools/analyze_acceptance_session_job_gap.py:1-42`: stdlib import、path pattern、既定値、estimand の module docstring
- `:43-96`: CLI。root、output-dir、743、K=3、timezone、NQSV 分解能を受ける
- `:97-154`: `SessionRow`、`ShardRow`、parse/status dataclass。全 counter key を初期値 0 で定義
- `:155-205`: read-only の `stat` helper、mtime_ns 変換、エラー分類。入力側では write/open append を使わない
- `:206-286`: accounting block parser。Request ID/Name、Created/Started/Ended、Elapse を一意に抽出
- `:287-330`: receipt parser。`outcome`、`queue_wait_s`、`state_history[].elapsed_s` を auxiliary 値として抽出
- `:331-410`: 743 session の sorted inventory、K=3 shard の完全性判定、複数理由と exclusive reason の作成
- `:411-478`: `S_s`、`J_s`、`R_s`、critical shard 集合、4 項の計算と ns 単位 closure
- `:479-548`: endpoint 別 offset bounds、drift bounds、login collection の off-path/indeterminate 分類
- `:549-602`: legacy 非対統計、paired 統計、outcome 層別、決定的 quantile 計算
- `:603-660`: 独立検査、coverage partition、異常例の session/shard ID 収集
- `:661-732`: CSV/JSON の固定 schema 出力、JSON 1 行 stdout、終了 code
- `:733-750`: `main()`。予期しない例外も traceback だけでなく構造化 failure summary を標準エラーへ出す

既存実装との静的対応は次である。

- worker 全起動: `tools/acceptance_shards.py:1306-1321`
- login collection 呼出し: `tools/acceptance_shards.py:1334-1351`
- collection 後の worker 結果待ち: `tools/acceptance_shards.py:1353-1379`
- 並行実行という契約: `tools/run_tests.py:1402-1407`
- collection subprocess: `tools/run_tests.py:1431-1445`
- 完了後の log 書込み: `tools/run_tests.py:1446-1455`

## 独立検査

加法 closure とは別に、次を実施する。

- D1320 の外部基準との照合: legacy 集計が session `n=549, median=338`、job `n=1297, median=263` を再現するかを値と差で出す。不一致でも合わせ込まず、母集合または選択規則の相違として報告する。
- NQSV 内部検査: `Created <= Started <= Ended`。`Elapse` と `Ended-Started` の差の分布も出すが、同値とは仮定しない。
- receipt 独立比較: `queue_wait_s` と NQSV `Started-Created`、terminal `state_history[].elapsed_s` と mtime span の差を別々に出す。出所が異なるため一致を合否条件にしない。
- critical shard 検査: 最大 job span shard と最後の handled shardの一致率を出し、alignment 項が実際に必要か確認する。
- 時計因果検査: endpoint ごとの lower bound が upper bound 以下か、共通 offset 交差が空でないかを数える。空の session を推測補正しない。
- collection 検査: `login-collection.log` mtime が最終 shard report/junit mtime以前の session 数、時計補正後も最終 Ended 以前と証明できる数、判定不能数を別々に出す。
- coverage 検査: 743 全 session が `sessions.csv` に一度だけ現れ、primary included と exclusive exclusions が 743 に一致することを確認する。
- sample の静的期待値: 提示標本では shard-0 の Created 02:24:47、Ended 02:32:09 なので job span は 442 秒。session envelope は最初の confirm 02:24:46 から最後の handled 02:32:23 までの 457 秒で、残差は 15 秒。critical shard-0 の項は `1 + 0 + 14 + 0 = 15` 秒となる。この照合値を parser の review oracle とする。

pytest はこの read-only plan 段では実走せず、緑は主張しない。

## 測れない残り

- confirm marker 作成から qsub 呼出し、qsub 受理、NQSV Created までの内部境界: `_dispatch_worker` と dispatch helper に同一 monotonic clock の `before_qsub`, `qsub_returned`, `confirm_written` を記録する。
- Ended から handled までの poll、成果物収集、receipt、handled 書込みの内訳: `terminal_observed`, `collect_start/end`, `receipt_written`, `handled_written` を同一 monotonic clock で記録する。
- NQSV controller clock と Lustre clock の一点 offset および drift: session 前後に scheduler server time と login node realtime を同時取得する calibration record を保存する。
- login collection の正確な開始、subprocess return、log 書込み時間: `_collect_login_universe` の呼出し直前、subprocess return 直後、log write 後を monotonic timestamp で保存する。
- collection が親の最終完了を何秒遅らせたか: `collect_login` return と各 worker payload ready を同じ親 process の monotonic clock で記録する。
- parent の join、merge、root junit 作成、最終 return: 各境界の monotonic timestamp を parent session artifact に保存する。現行の `handled` endpoint より後は主 estimandに含まれていない。
- report/junit が無い qdel shard の Ended 直前側 anchor: compute job の正常終了直前または qdel 観測時に terminal marker を Lustre へ記録する。
- mtime と意味上の event の間の write delay: JSON 本文へ event 直前・直後の monotonic/realtime を保存する。

これらは必要な計装点の列挙だけであり、新規走行や計装実装は本件に含めない。欠測区間を推測値で埋めない。

## 親 brief への異議

- P1 は採用する。ただし「paired」は session 単位の対応を意味し、最大 job span shard と最後の handled shard が同一とは限らない。4 項のうち `start_skew` と `end_skew` がその差を受け持つ。
- P2 は指定コードから支持される。ただし log mtime は collection 終了そのものではなく、終了後の log materialization である。「遅延に寄与した」と逆向きに断定できる測点ではない。
- P3 は仮説としてのみ扱う。主項かどうかは 743 本の paired 分布を得る前には確定できない。また `Ended→handled` を poll、収集、merge に分ける保存測点はない。特に parent merge が handled より後なら、この区間には含まれない。
- P4 は採用するが、一定 offset は残差全体では相殺する。問題になるのは跨時計項を個別解釈するときと、Created から Ended までの offset drift である。
- D1420 の約 51.7 秒は compute job 内の 48 worker collection であり、ここで扱う login 親の `--collect-only` と別物である。job/session 層へ転用しない。
- brief は D1320 の「session 合計」が `max(H)-min(F)` か `max(H-F)` かを式で固定していない。本 plan は実 session envelope である前者を主値とし、後者も参考列として出して差を可視化する。

## 総括

実装対象は read-only 解析 script 1 本だけである。743 session を全件台帳化し、完全な session だけで `S_s-max_j(job span)` を対にして求める。残差は 4 項で per-session に恒等分解する一方、その closure を検証扱いせず、D1320 再現、receipt、時計因果範囲、critical shard 一致率、collection overlap、coverage partition を独立検査に置く。

保存記録で確定できる raw 値と、clock offset/drift のため範囲にしかならない物理区間を分離する。測点のない poll、収集、merge、正確な collection 境界は未分解として残し、推測では埋めない。