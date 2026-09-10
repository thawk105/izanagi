## 静的調査の範囲

指定資料、production 経路、pytest 9.1.1、pytest-xdist 3.8.0、既存 artifact を静的に確認した。pytest の実走、ファイル編集、repo 状態変更は行っていない。

## P1 の検証結果

P1 の 3 項分解は、そのままでは成立しない。理由は二つある。

- `worker_occupancy` は worker の連続した「稼働窓」ではなく、setup・call・teardown の `TestReport.duration` の離散的な総和である。
- 最大 occupancy の worker が、全 worker 中で最後に report を終えるとは限らない。したがって「最繁 worker の最後」と「全体の最後」の間が P1 から抜ける。

さらに、controller の interpreter 起動と plugin import は pytest 表示 wall の開始前であり、56 秒には入らない。pytest 表示 wall は terminal plugin が `pytest_sessionstart` で作る `_session_start` から始まる。`_pytest/terminal.py:846-849,1252-1275`。plugin import は config parse 中で、これより前である。`_pytest/config/__init__.py:1558-1607`。

以下で定義し直す。

- `S`: controller の terminal `_session_start`
- `E`: terminal が summary duration を読む時刻
- `R_w`: worker `w` の全 report duration 合計
- `w* = argmax_w R_w`
- `F_w`, `L_w`: worker `w` の最初の report 開始、最後の report 終了
- `L_all = max_w L_w`
- `W = E - S`

成立する加法分解は次の 4 項である。

```text
W - R_w*
  = (F_w* - S)
  + ((L_w* - F_w*) - R_w*)
  + (L_all - L_w*)
  + (E - L_all)
```

| 成分 | 定義 | 意味 |
|---|---|---|
| A | `F_w* - S` | session wall 開始から最繁 worker の最初の report 開始まで |
| B | `(L_w* - F_w*) - R_w*` | 最繁 worker の report 窓内にある非 report 時間 |
| D | `L_all - L_w*` | 最繁 worker の最終 report 後も、別 worker が report を出していた tail |
| C | `E - L_all` | 全 worker の最後の report 後から terminal の wall 測定終点まで |

P1 の 3 項を保つなら、`C' = E - L_w*` と定義すれば代数的には成立する。しかし `C'` は別 worker のテスト実行を含むため「終端費用」とは呼べない。したがって A+B+D+C の 4 項を正本にする。

これは wall 上の露出区間の分解であり、全 worker の CPU 時間の因果的な総和ではない。collection や IPC は互いに並行するので、各 worker の raw duration を足し合わせて 56 秒と比較してはいけない。

## worker_occupancy が含む範囲

`tools/acceptance_shards.py:862-872` は controller が受けた各 report の `duration` を node ごとに加算する。`tools/acceptance_shards.py:973-989` が node を worker に対応付け、`tools/acceptance_shards.py:1013-1018` が worker ごとの合計を `worker_occupancy` に書く。

pytest 側では一つの item に対して次の順で report が作られる。

- setup: `_pytest/runner.py:132`
- call: `_pytest/runner.py:139`
- teardown: `_pytest/runner.py:144`
- 各 phase の hook 呼出しを `CallInfo.from_call` が計時: `_pytest/runner.py:236-256,340-375`
- `TestReport` へ `duration/start/stop` を転記: `_pytest/reports.py:383-452`

したがって `R_w` に含まれるものは次である。

- fixture setup、test body、fixture teardown
- setup/call/teardown hook の内側で行われた処理
- setup で skip/fail した場合は、実際に生成された report の phase だけ

JUnit も現設定では `junit_duration_report=total` が既定であり、三 phase を加算する。`_pytest/junitxml.py:400-413,624-629`。ただし XML は小数 3 桁へ丸めるので、occupancy の再計算には `report.json` を優先する。

`R_w` に含まれないものは次である。

- controller の interpreter 起動、pytest/plugin import、初期 config
- worker 起動、worker plugin import
- 各 worker の全 collection と shard deselect
- collection の controller 集約と初期 item 配布
- `pytest_runtest_protocol` wrapper のうち内側 phase より前後の処理
- `pytest_runtest_makereport` による report 構築
- report serialization、xdist IPC、controller 側 report 処理
- item 間の配布待ち
- worker sessionfinish、worker 終了、controller sessionfinish
- JUnit、`report.json`、summary の生成

具体例として、repo の外側 wrapper は lock を取得してから内側 protocol へ `yield` する。`orchestrator/tests/conftest.py:2069-2086`。この取得待ちは setup report より前なので occupancy 外である。一方、通常の fixture setup/teardown は `_pytest/runner.py:168-200` の report 内である。sessionfinish に残った最終 cleanup は `_pytest/runner.py:107-112` で occupancy 外になりうる。

controller の pytest wall は `_pytest/terminal.py:846-849` で開始し、sessionfinish の内側処理が完了した後、同 `:957-994,1252-1275` で測られる。JUnit は `_pytest/junitxml.py:647-653`、shard report は `tools/acceptance_shards.py:955-1023` で sessionfinish 中に書かれるため、表示 wall に含まれる。xdist worker の終了待ちも `xdist/dsession.py:94-100,129-144,193-218` の経路を通る。

## 測点

probe は 22 種の event を記録する。繰返し event は process 内でメモリに蓄積し、worker ごとに一度だけ JSON を書く。

| ID | event と取得点 | role・識別子 | 記録内容 |
|---|---|---|---|
| E0 | pytest child の開始・終了。probe PBS の subprocess 前後 | 外側 runner | argv、環境、rc、epoch/monotonic |
| E1 | probe module の top-level import | controller または worker | pid、hostname、両時計。worker は `PYTEST_XDIST_WORKER` |
| E2 | `pytest_load_initial_conftests` wrapper。`_pytest/config/__init__.py:1605-1607` | 両方 | enter/exit |
| E3 | `pytest_configure`。`_pytest/config/__init__.py:1202-1205` | 両方 | role、worker id、pytest/xdist version |
| E4 | `pytest_sessionstart` wrapper。`_pytest/main.py:317-330` | 両方 | enter/exit。controller は terminal `_session_start.time/perf_count` も保存 |
| E5 | `pytest_xdist_setupnodes`。`xdist/workermanage.py:91-97` | controller | worker 数、開始時刻 |
| E6 | `pytest_xdist_newgateway`。同 `:99-113` | controller、gateway id | worker process gateway 作成時刻 |
| E7 | `pytest_configure_node`。同 `:325-349` | controller、gateway id | remote pytest bootstrap 開始側の時刻 |
| E8 | `pytest_testnodeready`。`xdist/dsession.py:172-191` | controller、gateway id | worker ready |
| E9 | `pytest_collection` wrapper。`_pytest/main.py:393-394` | worker | collection enter/exit |
| E10 | `pytest_collection_modifyitems` wrapper の yield 後 | worker | 全 universe、shard 選択数、zero mode 後の件数 |
| E11 | `pytest_collection_finish`。`xdist/remote.py:256-262` | worker | collection 完了、selected digest |
| E12 | `pytest_xdist_node_collection_finished`。`xdist/dsession.py:274-306` | controller、gateway id | controller 受信時刻、node 数 |
| E13 | `pytest_runtestloop` wrapper。worker は `xdist/remote.py:200-209` | 両方 | loop enter/exit |
| E14 | `pytest_runtest_protocol` wrapper。`_pytest/runner.py:115-120` | worker | item ごとの begin/end |
| E15 | `pytest_runtest_makereport` wrapper。`_pytest/runner.py:249-256` | worker | phase ごとの report 構築時間 |
| E16 | `pytest_runtest_logreport` wrapper | worker/controller | `when/start/stop/duration`、worker 送信側と controller 受信側 |
| E17 | `pytest_report_to_serializable` wrapper。`xdist/remote.py:281-289` | worker | serialization 時間。E16 の内数として扱う |
| E18 | `pytest_testnodedown`。`xdist/dsession.py:193-218` | controller、gateway id | worker down |
| E19 | `pytest_sessionfinish` wrapper。`_pytest/main.py:359-372` | 両方 | enter/exit、exitstatus |
| E20 | `pytest_terminal_summary` wrapper | controller | enter/exit、および sessionfinish wrapper の最終 exit |
| E21 | `pytest_unconfigure`。`_pytest/config/__init__.py:1207-1219` | 両方 | cleanup 終了 |

worker id は次の順で確定できる。

- module import 時: `PYTEST_XDIST_WORKER`
- configure 以降: `config.workerinput["workerid"]`
- controller から見た node: `node.gateway.id`
- controller に届く report: xdist が `worker_id` を付加する。`xdist/remote.py:281-289`

環境変数は worker pytest 構築前に設定される。`xdist/remote.py:403-425`。production shard plugin も controller report の `worker_id` を使用する。`tools/acceptance_shards.py:862-869`。

## 時計

主時計は `time.perf_counter_ns()` とする。同一 gen_S job の controller と全 worker は同一 host・同一 kernel clock を使うため、process 間で比較できる。pytest 自身も duration に `perf_counter` を使う。`_pytest/timing.py:14,24-47,54-64`。

各 event では同じ箇所で `time.time_ns()` も記録する。理由は `TestReport.start/stop` が epoch だからである。`_pytest/runner.py:299-304,359-371`。

各 process の import、configure、sessionfinish で取得した `(epoch_ns, perf_counter_ns)` の対応から offset の変化を検査する。

- offset drift が 5 ms 以下なら、report の epoch start/stop を monotonic 軸へ射影する。
- 5 ms を超える、時計が逆行する、worker hostname が controller と異なる場合は分解を indeterminate とする。
- wall 分解の独立確認には E14 の protocol begin/end を使い、epoch 変換に依存しない式も計算する。

## 成分の算出

**A: session 開始包絡**

```text
A = F_w* - S
T_ready = 全 pytest_testnodeready の最大時刻
T_collect = 全 pytest_xdist_node_collection_finished の最大時刻

A_ready        = T_ready - S
A_collect_tail = T_collect - T_ready
A_schedule     = F_w* - T_collect

A = A_ready + A_collect_tail + A_schedule
```

`T_collect` の後に collection 一致確認と initial schedule が行われる。`xdist/dsession.py:287-306`、`xdist/scheduler/loadscope.py:338-407`。worker は ready event の後に collection へ進む。`xdist/remote.py:135-153`。

`A_ready` は純粋な「worker 起動時間」ではない。早い worker の collection と遅い worker の bootstrap が重なるため、「全 worker ready までの露出 wall」と記録する。各 worker の `E7→E1→E8` と `E9` は raw service time として別掲するが、A へ重複加算しない。

controller の interpreter/plugin 費用は次で測るが、A および 56 秒には入れない。

```text
controller_pre_session = S - E0.child_start
controller_post_session = E0.child_end - E
```

E1/E2/E3 により `interpreter + E1 より前の plugin import`、initial conftest、configure を区別する。interpreter 単独と E1 より前の import は production の `python -m pytest` を変えずには分離できないため、合算値として出す。

**B: 最繁 worker の report 窓内 gap**

```text
B = (L_w* - F_w*) - R_w*
```

E14から得る protocol 窓による独立形は次である。

```text
P_w* = w* の最初の protocol begin
Q_w* = w* の最後の protocol end
B_protocol = (Q_w* - P_w*) - R_w*
```

`B_protocol` は次へ分類する。

- item 間 idle: `next protocol begin - previous protocol end`
- report 構築: E15
- worker logreport/transport: E16
- serialization: E17。E16 の内数であり重複加算しない
- その他 protocol 外側: `B_protocol` から上記の排他的区間を引いた残り

controller 受信時刻と worker 送信時刻の差は IPC 診断値だが、worker の次 item と並行しうるため B へ raw 加算しない。

**D: 最繁 worker 後の別 worker tail**

```text
D = L_all - L_w*
```

protocol 軸では次も出す。

```text
Q_all = 全 worker の最後の protocol end
D_protocol = Q_all - Q_w*
```

D が 0 であることを確認できた場合だけ、P1 の 3 項表現へ戻せる。

**C: 全体終端**

```text
C = E - L_all
```

さらに次を補助表示する。

```text
C_worker_finish = T_down_all - Q_all
C_controller     = E - T_down_all
```

`T_down_all` は最後の `pytest_testnodedown`。`C_controller` は controller sessionfinish、JUnit、shard report、terminal summary を含む。

terminal の正確な E は公開 hook では直接得られないため、`pytest_terminal_summary` exit と最外 `pytest_sessionfinish` exit で挟む。terminal 実装上、duration 取得はその間にある。`_pytest/terminal.py:957-994,1252-1275`。C はこの上下限を併記し、幅を測定誤差とする。

**閉包検査**

```text
residual = W - R_w*
parts = A + B + D + C
closure_error = residual - parts
```

`|closure_error| <= max(0.05 秒, 時計 offset drift の 5 倍)` を必須条件とする。pytest stdout の wall は 0.01 秒丸めなので、probe の未丸め wall と stdout は別に比較する。

**zero-test 走**

zero-test では `R=0` なので、同じ milestone で次を得る。

```text
Z = E_zero - S_zero
Z = ready envelope + collection tail + aggregation/shutdown/sessionfinish
```

ただし `Z` を実 shard の A や Cから機械的に引かない。real 走と zero 走では test execution と page-cache 状態が異なるため、D711 の再測定値は独立な calibration とする。

## zero-test の作り方

probe の `pytest_collection_modifyitems` を wrapper とし、内側の production shard plugin が全 collection・割付・state 保存を終えた後で `items[:] = []` にする。

この順序により以下を同時に満たす。

- production shard plugin は全 universe を見る。`tools/acceptance_shards.py:825-852`
- `observed_universe` と selected digest は current collection に基づく
- 実行 item は 0 件
- production の plugin、runner、scheduler は変更しない
- この走は acceptance 判定として扱わず、pytest rc=5 を calibration の期待値とする

19215 node、48 worker collection digest、0 finished を検査する。node 数が 19215 でなければ D711 との比較条件が変わったものとして停止する。

## production shard 起動契約

production plugin の env 名は `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1`。`tools/acceptance_shards.py:49-52`。

JSON spec は次の 3 field exactly でなければならない。`tools/acceptance_shards.py:778-791`。

```json
{
  "session_root": "/absolute/path",
  "shard_count": 3,
  "shard_index": 2
}
```

ただし計画上、この env を手で作らない。compute 上で internal runner を呼び、`tools/run_tests.py:1460-1533` に production と同じ JSON と pytest argv を構築させる。

runner が作る実 pytest argv は次の形になる。`tools/run_tests.py:550-572,1495-1508`。

```text
python -m pytest \
  /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/orchestrator/tests \
  -n 48 --dist loadgroup \
  --junitxml=<session>/shard-2/junit.xml \
  -p tools.acceptance_shards \
  -p no:cacheprovider
```

probe だけを `PYTEST_PLUGINS=_t2097_fixed_cost_probe` で追加する。`IZANAGI_TEST_NPROC=48` は `_default_nproc` の production override である。`tools/run_tests.py:385-399`。

`session_root` は `/work/1/SFC/tanab/.izanagi-acceptance-shards/` の直下、`shard-2` は実在ディレクトリでなければならない。`tools/run_tests.py:1473-1488`。cwd は repo root 固定で、shard plugin も cwd を唯一の実 repo root とする。`tools/acceptance_shards.py:830-833`。

## 実行計画

一つの gen_S job で、zero と real をそれぞれ A/B/B/A にする。A は timing 無効、B は timing 有効である。

| 順序 | arm | workload | probe |
|---:|---|---|---|
| 1 | Z-A1 | zero-test | selector のみ、timing off |
| 2 | Z-B1 | zero-test | timing on |
| 3 | R-A1 | 実 shard-2 | probe 未ロード |
| 4 | R-B1 | 実 shard-2 | timing on |
| 5 | R-B2 | 実 shard-2 | timing on |
| 6 | R-A2 | 実 shard-2 | probe 未ロード |
| 7 | Z-B2 | zero-test | timing on |
| 8 | Z-A2 | zero-test | selector のみ、timing off |

最初の zero report の `observed_universe` を再度 `allocate(records, 3)` し、shard-2 が group-free であることを検査する。`group_to_workers != {}` なら real arm を開始せず停止する。これにより D1384 の shard-0 固有計測へ逸脱しない。

PBS header は次とする。`tools/pegasus/probes/t1683_rr5_cost_probe.pbs:1-5` と同じ gen_S・単一 job 形である。

```bash
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=00:30:00
#PBS -b 1
#PBS -N t2097-fixed-cost

set -Eeuo pipefail
umask 077

REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp
SHARED=/work/1/SFC/tanab/.izanagi-acceptance-shards
PROBE="$REPO/_t2097_fixed_cost_probe.py"
PY=$(realpath -e -- "$(command -v python3)")
JOB_TAG="t2097-${PBS_JOBID//:/_}"

cd "$REPO"
unset PYTHONHOME PYTHONSTARTUP PYTHONPATH PYTEST_ADDOPTS
export PYTHONDONTWRITEBYTECODE=1
export IZANAGI_TEST_NPROC=48
export IZANAGI_TASK_RUN_AUTO_RECORD=0

run_arm() {
    label=$1
    kind=$2
    timing=$3
    session="$SHARED/$JOB_TAG-$label"
    mkdir -m 700 -- "$session"
    mkdir -m 700 -- "$session/shard-2"

    argv=(
      "$PY" -B "$REPO/tools/run_tests.py"
      "--izanagi-acceptance-shard-session=$session"
      "--izanagi-acceptance-shard-count=3"
      "--izanagi-acceptance-shard-index=2"
    )

    set +e
    if [[ "$kind" == zero ]]; then
        env \
          PYTEST_PLUGINS=_t2097_fixed_cost_probe \
          IZANAGI_T2097_MODE=zero \
          IZANAGI_T2097_RECORD="$timing" \
          IZANAGI_T2097_OUTPUT="$session/shard-2/probe" \
          "${argv[@]}" \
          >"$session/shard-2/pytest.stdout" \
          2>"$session/shard-2/pytest.stderr"
    elif [[ "$timing" == 1 ]]; then
        env \
          PYTEST_PLUGINS=_t2097_fixed_cost_probe \
          IZANAGI_T2097_MODE=real \
          IZANAGI_T2097_RECORD=1 \
          IZANAGI_T2097_OUTPUT="$session/shard-2/probe" \
          "${argv[@]}" \
          >"$session/shard-2/pytest.stdout" \
          2>"$session/shard-2/pytest.stderr"
    else
        env -u PYTEST_PLUGINS \
          "${argv[@]}" \
          >"$session/shard-2/pytest.stdout" \
          2>"$session/shard-2/pytest.stderr"
    fi
    rc=$?
    set -e
    printf '%s\n' "$rc" >"$session/shard-2/runner.rc"

    if [[ "$kind" == zero ]]; then
        [[ "$rc" -eq 5 ]]
    else
        [[ "$rc" -eq 0 ]]
    fi
}

run_arm zero-a1 zero 0
run_arm zero-b1 zero 1
run_arm real-a1 real 0
run_arm real-b1 real 1
run_arm real-b2 real 1
run_arm real-a2 real 0
run_arm zero-b2 zero 1
run_arm zero-a2 zero 0

"$PY" -B "$PROBE" summarize \
  --root "$SHARED" \
  --job-tag "$JOB_TAG" \
  --out "$SHARED/$JOB_TAG-summary.json"
```

login node からの投入は次とする。PBS stdout/stderr も repo 外に置く。

```bash
REPO=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp
JOBDIR=/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp
qsub \
  -o "$JOBDIR/t2097-fixed-cost.pbs.stdout" \
  -e "$JOBDIR/t2097-fixed-cost.pbs.stderr" \
  "$REPO/_t2097_fixed_cost_probe.pbs"
```

各 arm の出力は次になる。

```text
/work/1/SFC/tanab/.izanagi-acceptance-shards/<job-tag>-<arm>/shard-2/
  report.json
  junit.xml
  pytest.stdout
  pytest.stderr
  runner.rc
  probe/controller.json
  probe/gw0.json ... probe/gw47.json
```

各 arm で HEAD、probe/PBS の SHA-256、hostname、PBS job id、affinity CPU 数、pytest/xdist version、argv、選択 digest を保存する。affinity が 48 でない場合は実行前に停止する。

## 観測者効果

見積り上の主な負荷は次である。

- 約 19215 report に対する controller/worker hook 呼出しと時計取得
- 約 6405 protocol pair
- process ごとのメモリ buffer
- worker sessionfinish での JSON 一回書込み

短い整数 tuple を list へ append し、nodeid の重複保存や report ごとの file writeを避ければ、予想 wall 増加は 0.1〜1 秒程度である。これは 56 秒の 0.2〜1.8%だが、推定だけで採用しない。

A/B/B/A から次を計算する。

```text
probe_effect_real =
    mean(W_R-B1, W_R-B2) - mean(W_R-A1, W_R-A2)

probe_effect_zero =
    mean(W_Z-B1, W_Z-B2) - mean(W_Z-A1, W_Z-A2)
```

同様に residual、最大 occupancy、collection 包絡についても差を出す。

受理条件は次とする。

- real: `|probe_effect| <= max(0.5 秒, control wall の 1%)`
- zero: `|probe_effect| <= 0.5 秒`
- selected digest と universe digest が全 arm で一致
- real B の `finished == selected`
- timing on/off で report duration 分布に系統差がない
- clock closure error が 0.05 秒以内

超えた場合は、その probe の内訳値を採用しない。効果を各成分から機械的に差し引くこともしない。

## P2・P3・P4 の扱い

- P2: D711 の zero-test 費用は再測定するが、それが real residual の独立成分だとは事前に仮定しない。real の A/C と event 境界が一致した範囲だけ対応付ける。
- P3: report 構築・serialization・item 間 gap は E14〜E17で測れる。ただし controller IPC latency は他 worker の実行と並行するので、raw 合計を residual へ足さない。
- P4: 同一 PBS job は node、checkout、interpreter、affinity を揃えるが、page cache と温度は揃えない。ABBA と arm 順序を記録し、zero と real の単純差を因果効果とはしない。

## 時間予算

既存 shard-2 は pytest wall 130.63 秒、PBS Elapse 145 秒だった。既存 stdout `shard-2/...o963740:119`、PBS stderr `shard-2/...e963740:9-14`。

D711 の 12.86 秒を node 数比だけで外挿すると、

```text
12.86 × 19215 / 14479 = 約 17.1 秒
```

ただし全費用が node 数へ線形ではないため、zero は 1 走 30 秒を見込む。

| 種類 | 数 | 1 走見積り | 合計 |
|---|---:|---:|---:|
| zero | 4 | 20〜30 秒 | 1.3〜2.0 分 |
| real shard-2 | 4 | 2.4〜3.6 分 | 9.6〜14.4 分 |
| 検査・summary | 1 | 1〜2 分 | 1〜2 分 |
| 合計 | 8 走 |  | 約 12〜18 分 |

したがって `elapstim_req=00:30:00` とする。これは既存 shard-2 の実績と、14 session での shard-2 wall 最大約 200 秒に対して余裕を持つ。

## 既存 artifact だけで確定できる量

既存 artifact から次は新規実行なしで確定できる。

| shard | stdout wall | max occupancy | 差 |
|---|---:|---:|---:|
| 0 | 213.91 | 135.676294339 | 78.233705661 秒 |
| 1 | 176.01 | 119.707754523 | 56.302245477 秒 |
| 2 | 130.63 | 74.259014330 | 56.370985670 秒 |

wall は各 stdout の `:144`、`:102`、`:119`、occupancy は各 `report.json:1` から取れる。stdout wall は 0.01 秒丸めなので差も約 ±0.005 秒である。

さらに取得できるものは次である。

- selected/finished 件数、worker 数、worker 別 occupancy、group 配置
- JUnit の全 testcase duration、最大 testcase、三 phase 合計の丸め値
- JUnit suite time、timestamp、hostname
- pytest 9.1.1、xdist 3.8.0、48 worker
- PBS job Elapse: shard-0/1/2 が 227/189/145 秒
- request の internal spec と tested repo
- receipt の compute hostname と PBS job id

抽出は例えば次で行える。

```bash
python3 -B - <<'PY'
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

root = Path("/work/1/SFC/tanab/.izanagi-acceptance-shards/349543d56cdc8d141798abb3626121e9")
wall_re = re.compile(r" in ([0-9]+(?:[.][0-9]+)?)s ")

for index in range(3):
    shard = root / f"shard-{index}"
    report = json.loads((shard / "report.json").read_text())
    stdout = next((shard / "dispatch" / f"shard-{index}").glob("*.o*")).read_text()
    wall = float(wall_re.findall(stdout)[-1])
    worker, entry = max(
        report["worker_occupancy"].items(),
        key=lambda pair: pair[1]["duration_s"],
    )
    suite = ET.parse(shard / "junit.xml").getroot().find("testsuite")
    print(index, wall, worker, entry["duration_s"],
          wall - entry["duration_s"], suite.attrib["time"])
PY
```

既存 artifact だけでは A/B/D/C のどれも分離できない。理由は、report の開始・終了時刻、protocol 窓、collection milestone、worker down 時刻が保存されていないためである。JUnit/report の mtime も同じ秒へ丸められており、sessionfinish 内の順序証拠にはならない。

## 実装単位

repo の production file は変更しない。`role=author` は worktree root に次の 2 fileだけを作る。

- `_t2097_fixed_cost_probe.py`、概算 350〜430 行  
  pytest plugin、zero selector、process 別 event buffer、clock validation、summary CLI、artifact schema validationを担当する。
- `_t2097_fixed_cost_probe.pbs`、概算 100〜140 行  
  compute-only guard、48 CPU確認、8 arm の実行、session directory、rc、stdout/stderr、最終 summary を担当する。

`tools/pegasus/probes/` には置かない。そこへ未登録 `.py/.pbs` を置くと `orchestrator/tests/test_hooks.py:3849-3875` の execution inventory が変わり、実 shard の workload 自体を赤へ変えるためである。worktree root なら既定 target `orchestrator/tests` の collection 外であり、`tools/` の bytecode guard 列挙にも入らない。

実行後、親が SHA-256 を記録して次へ移動する。

```text
/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/probe-verbatim/
```

repo へ commit しない。移動後に worktree に probe source、PBS、pytest output、`__pycache__` が残っていないことを確認する。

## 総括

(P1) は 3 項のままでは不成立で、最繁 worker 後の別 worker tail を加えた 4 項なら加法的に成立する。  
測点は 22 種で、controller・48 worker・外側 runner の共通時系列を取る。  
新規実行は 8 走、見積り合計 12〜18 分、PBS は `elapstim_req=00:30:00` とする。