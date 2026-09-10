## A-1 — BLOCKER

- 所見 ID / severity: A-1 / BLOCKER
- 主張: `W - max(worker_occupancy)` は全体の「report 外費用」ではなく、最大 report 合計を持つ一 worker に対する残差にすぎない。
- 根拠: `worker_occupancy` は setup・call・teardown の `report.duration` を node ごとに合算して worker へ載せるだけである (`tools/acceptance_shards.py:862-872,983-1018`)。一方、xdist が scheduling に使う item 所要は report 生成や送信も含む `pytest_runtest_protocol` 全体である (`xdist/remote.py:226-234`)。プランの D は明示的に別 worker の report 実行を含む (`stage2-plan.md:185-198`) ため、それ自体が report 外費用ではない。
- 内訳への影響: A・B・D の任意の部分が、実際には他 worker の report 実行や待ちを覆っていても「固定費」「非 report 費」と表示される。
- 直し方: A/B/D/C は「w* 相対の wall 露出区間」とだけ呼び、原因別費用とは分離する。全 worker の report 区間の union とその補集合も出し、さらに mechanism 別 service time は並行しうる非加法診断値として別表にする。

## A-2 — BLOCKER

- 所見 ID / severity: A-2 / BLOCKER
- 主張: E14 と item 間 gap では、プランが P3 として求める protocol 外費用を排他的に分類できない。
- 根拠: repo の `pytest_runtest_protocol` wrapper は `tryfirst=True` で、lock を取得してから内側へ `yield` する (`orchestrator/tests/conftest.py:2069-2086`)。probe の wrapper 優先度と実 hook 順序はプランにないため、E14 はこの取得待ちより内側になりうる。また phase の計時終了後に report 構築と logreport が走り (`_pytest/runner.py:249-256`)、hook 終了後にも xdist の protocol-complete 送信がある (`xdist/remote.py:226-234`)。したがって `next E14 begin - previous E14 end` は lock 解放・再取得、xdist 送信、controller の schedule 待ち、setproctitle などを混ぜた量であり、単なる item idle ではない。
- 内訳への影響: 同じ per-item 費用が最初の item では A、途中では B の idle、最後では C に分散し、P3 の数値が機構別内訳に見えてしまう。
- 直し方: probe の hook 順を実行時に列挙して fail-closed にし、lock 進入前後、各 phase、makereport、logreport、protocol-complete、次 item 受領を別々に測る。外側境界を取れない区間は `unclassified_outer_protocol` として残す。

## A-3 — MAJOR

- 所見 ID / severity: A-3 / MAJOR
- 主張: E18 `pytest_testnodedown` は worker process の終了時刻ではないため、`C_worker_finish` と `C_controller` の境界が誤っている。
- 根拠: worker は `pytest_sessionfinish` 後に `workerfinished` を送る (`xdist/remote.py:141-149`)。controller はその受信時に `pytest_testnodedown` を呼ぶ (`xdist/dsession.py:193-218`) が、worker の `pytest_unconfigure` は sessionfinish 後である (`_pytest/main.py:359-373`)。gateway の実終了待ちはさらに controller sessionfinish の `teardown_nodes()` にある (`xdist/dsession.py:94-100`)。加えてプランは「sessionfinish で JSON 一回書込み」と E21 unconfigure 終了の記録を同時に要求しており (`stage2-plan.md:84-109,417-425`)、一回書込みでは両立しない。
- 内訳への影響: worker unconfigure、probe flush、gateway 終了待ちが controller 固有費へ誤配賦され、C の内訳が数秒単位で動きうる。
- 直し方: E18 を `workerfinished_received` と改名し、OS process/gateway の実終了を外側 runner から別測定する。probe flush の開始・終了も独立区間にし、E21 を保存する時点と worker down の順序を acceptance 条件で検査する。

## A-4 — BLOCKER

- 所見 ID / severity: A-4 / BLOCKER
- 主張: A/B/B/A 各二走では「probe 効果が 0.5 秒以下」という同等性を立証できず、zero arm は plugin 登録自体の効果も対照していない。
- 根拠: real は probe 未ロード対 timing on だが、zero は A/B とも `PYTEST_PLUGINS` で同じ module をロードし、record flag だけを変える (`stage2-plan.md:285-296,340-363`)。controller は一つの event loop で report と protocol-complete を直列処理する (`xdist/dsession.py:146-166,326-341`) ため、controller hook の時計取得・list append・GIL・GC は次 item の配布自体を遅らせる。さらに worker ごとの JSON と controller buffer の flush は shutdown を直接延ばす。プランの受理判定は各 side 二値の平均差だけで、分散や同等性区間がない (`stage2-plan.md:428-449`)。
- 内訳への影響: probe が作った scheduling gap や終了 I/O を B/C の本来費用として採用するか、偶然の A/B 相殺で観測者効果を見逃す。
- 直し方: selector-only plugin と timing plugin を別実体にし、hook 登録数も対照する。複数 PBS job にまたがる無作為化 AB/BA pair を取り、paired 差の同等性区間全体が許容幅内に入った場合だけ採用する。memory-only、flush 有効、controller-only などの probe variant で負荷源も分離する。

## A-5 — BLOCKER

- 所見 ID / severity: A-5 / BLOCKER
- 主張: 計画の checkout は比較対象の 2026-09-01 08:15 実走と異なり、HEAD を記録するだけでは「同一 regime」を示せない。
- 根拠: 既存実走は `repo_root=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2080-c4-note-fix`、`tested_main=7899196330bf0aa3375ec768fcb36af47bb7e351` である (`shard-2/dispatch/shard-2/request.json:10-16`)。計画は別 worktree `dev-wave-t2097-fixed-cost-decomp` を固定している (`stage2-plan.md:271-281,313`)。read-only で確認した現 HEAD は `c6a94ec998bba8c20c302105f28af3850f8134a6` で、比較 commit から test suite に多数の差分がある。既存 artifact は runner hash と plugin 群も持つが、計画の一致条件は pytest/xdist version、node 数、digest が中心である。
- 内訳への影響: suite、fixture、prewarm、runner、plugin の世代差が A/B/C の変化として現れ、旧 56 秒の内訳だと誤認される。
- 直し方: 「旧 56 秒の再現」なら旧 commit、runner hash、submodule gitlinkと実 HEAD、plugin distribution rootまで一致させる。「現行値の再測定」なら旧値と同 regime とは呼ばず、新しい基準値として扱う。どちらでも tracked/untracked 状態と recursive submodule status/diff を保存する。

## A-6 — MAJOR

- 所見 ID / severity: A-6 / MAJOR
- 主張: 同一 job 内の固定順序は cache、TMPDIR、pycache、repo dirt の差を制御せず、P4 の regime を再現しない。
- 根拠: 順序は `Z,Z,R,R,R,R,Z,Z` で workload が交互化されていない (`stage2-plan.md:285-296`)。計画は `PYTHONDONTWRITEBYTECODE=1` を新たに設定する (`stage2-plan.md:319-323`) 一方、既存 PBS `dispatch.sh:46-54` には同設定がない。conftest は TMPDIR を設定せず ambient `/tmp` を使う契約で (`orchestrator/tests/conftest.py:1-26`)、real-repo lock も `/tmp` に置く (`orchestrator/tests/conftest.py:918-924`)。計画は TMPDIR、fstype、`/scr`、既存 `__pycache__` を記録せず、probe/PBS を untracked file として repo root に置く (`stage2-plan.md:531-546`)。先例は `/scr/$PBS_JOBID` を明示している (`tools/pegasus/probes/t1683_rr5_cost_probe.pbs:42-45`)。
- 内訳への影響: 後続 arm の import・collection・filesystem 所要が温まり、zero/real 差や probe 差へ cache 効果が混入する。
- 直し方: TMPDIR realpath、fstype、mount、空き量、pytest basetemp、pycache の事前状態を保存し、方針を全 arm で固定する。probe は repo 外へ置き、repo の full status/tree fingerprint を前後で照合する。cold/warm は別 regime として、job block ごとに arm 順を無作為化する。

## A-7 — BLOCKER

- 所見 ID / severity: A-7 / BLOCKER
- 主張: `Exclusive submit = OFF` に対する外乱検知がなく、48 CPU affinity は単独性の証拠にならない。
- 根拠: 既存 receipt 自体が `Exclusive = (none)`、`Share = 1` を記録する (`shard-2/dispatch/shard-2/receipt.json: immediate_qstat.stdout`)。計画の検査は主に affinity 48 だけである (`stage2-plan.md:415`)。既存 probe 先例には少なくとも arm 前後の process owner、load、affinity を取り、exclusivity を判定する経路がある (`tools/pegasus/probes/t316_sandbox_backend_probe.py:693-741,2069-2086,2157-2172`) が、本計画には対応手順がない。
- 内訳への影響: 同居 job、同じ UID の別 session、共有 filesystem 負荷が A/B/C のいずれにも加算され、ABBA の中央だけを汚す可能性もある。
- 直し方: arm 前後だけでなく走行中も、全非子孫 processを UID を問わず追跡し、対象 CPU の `/proc/stat`、CPU・IO・memory PSI、load、qstat 上の同居 jobを保存する。外乱、process visibility 欠落、monitor gap があれば pair 全体を無効化し、新 job で再測定する。monitor 自身の効果も別 A/B で上限化する。

## A-8 — MAJOR

- 所見 ID / severity: A-8 / MAJOR
- 主張: 計画の zero-test Z は D711 の 12.86 秒と同じ測定量だと立証されていない。
- 根拠: production plugin は全 allocation と大量 deselect を終えて state を保存する (`tools/acceptance_shards.py:825-852`)。その後 probe が残り items を空にするため (`stage2-plan.md:238-250`)、xdist が controller へ送る collection は空になる (`xdist/remote.py:256-262`)。pytest は zero collection 専用の rc=5 経路を取る (`_pytest/main.py:380-390`)。Z には新 selector、plugin hook 登録、zero 固有 shutdown、probe/report I/Oが含まれるが、D711 の逐語にはこれらの測点や同一手法の証拠がない。
- 内訳への影響: D711 との差を node 数増加や現在の collection 費へ帰属すると、probe方式と rc 経路の差まで P2 に算入する。
- 直し方: Z は `instrumented zero-selected calibration` と明記する。D711 を更新するなら当時の probe、endpoint、checkoutを再現するか、selector-only、selector+timing の差を独立に測り、共通 milestone の区間だけ比較する。

## A-9 — MAJOR

- 所見 ID / severity: A-9 / MAJOR
- 主張: `closure_error` は独立検査ではなく、定義を展開すると必ず 0 になる恒等式である。
- 根拠: プランの A+B+D+C は同じ S、F、L、E を使って望遠鏡和になる (`stage2-plan.md:24-32`)。そのまま `residual=W-R_w*` と比較している (`stage2-plan.md:217-225`) ため、event が誤った hook を測っていても同じ値を再利用すれば閉包する。
- 内訳への影響: 測点抜け、hook 順序違い、誤った worker 選択があっても 0.05 秒条件を通り、数値へ偽の検証済み印が付く。
- 直し方: この式は schema 内部の代数検査とだけ呼ぶ。独立検査には外側 wall、terminal の bound、直接 monotonic で取った phase 境界、report event 数・phase 数・worker対応、protocol spanを別経路で比較する。

## A-10 — MAJOR

- 所見 ID / severity: A-10 / MAJOR
- 主張: E0 は示された PBS では記録されず、仮に shell で囲んでも「pytest child」ではなく `run_tests.py` 全体の時刻になる。
- 根拠: E0 は pytest child 前後と定義され (`stage2-plan.md:88`)、`controller_pre_session=S-E0.child_start` を interpreter/plugin 費としている (`stage2-plan.md:152-159`)。しかし `run_arm` は `$PY tools/run_tests.py` を直接起動するだけで E0 record を作らない (`stage2-plan.md:325-374`)。さらに runner は pytest spawn 前に deletion、RuleOps、submodule preflight を実行する (`tools/run_tests.py:2588-2604`)。実 pytest child はその後の `subprocess.call` である (`tools/run_tests.py:1527-1533`)。
- 内訳への影響: runner import・site判定・preflight時間を controller interpreter/plugin 時間として報告するか、E0 自体が欠落する。
- 直し方: production runner 内の実 pytest spawn 境界を変更なしで観測できないなら、値を `runner_start_to_pytest_session` と改名する。pytest child境界が必須なら、sanctioned な runner-side eventを追加する別計画にし、PBS側も create-only metadataへ前後時刻を明示記録する。

## A-11 — MAJOR

- 所見 ID / severity: A-11 / MAJOR
- 主張: 親の 14 session 表は actual 最大 worker occupancy を引いておらず、その表から「約56秒が再現」とは言えない。
- 根拠: `measurements.md:131-142` は `resid = wall - max(max1, busy/48)` と定義する。主 session の shard-1 は同表で 78.3 秒だが、artifact の actual 最大 occupancy は `worker_occupancy.gw34.duration_s=119.707754523` なので、`176.01-119.707754523=56.302245477` 秒である。約 22 秒違う。README は別途 actual occupancy による中央値を述べるが (`README.md:48-50`)、指定された一次表にはその14走再計算がない。
- 内訳への影響: lower-bound 残差と actual worker 残差を混ぜると、共通成分の中央値・範囲・shard差が別の量になる。
- 直し方: 全14 artifact の `report.json.worker_occupancy` から actual 最大値を再計算する scriptと全行を成果物に残し、tested tip、selected digest、node、plugin versionごとに層別する。`max(max1,busy/48)` は理論下界残差として別列にする。

## A-12 — MAJOR

- 所見 ID / severity: A-12 / MAJOR
- 主張: 親の三つの実測値は記述的にはほぼ正しいが、そこから固定費や critical worker を一般化できない。
- 根拠: JUnit が setup/call/teardown を合算する読みは正しい (`pytest.ini:12-14`, `_pytest/junitxml.py:410-413,624-629`)。ただし shard-2 では read-only 再計算上、report 合計 2044.307856492 秒に対し丸め後 JUnit 合計は 2044.548 秒で 0.240144 秒違う。PBS Elapse 145 秒と pytest 130.63 秒の差は 14.37 秒だが、前者は job wrapperを含む別 endpoint である (`izdw-shard-2.e963740:9-14`, `izdw-shard-2.o963740:119`)。`gw0=74.25901433秒/2 item` は artifact field と一致し、他47 worker は平均 41.916 秒、範囲 41.708から43.192秒だが、report開始・終了時刻がないため gw0 が最後に終わった証拠はない。
- 内訳への影響: PBS差を56秒の一部へ入れたり、gw0を臨界 workerと仮定したりすると、開始費・tail・job外費用を誤配賦する。
- 直し方: PBS層、pytest wall層、worker report層を別 endpointとして維持し、複数の同一tip走で worker開始・終了と最終 workerを直接記録する。JUnitは表示用、内訳計算は非丸め `report.json` を用いる。

## 総括

BLOCKER は5件。新規実走は行っていない。  
この計画のまま得た A/B/D/C は代数的な区間表としては使えるが、56秒の原因別内訳としては信用できない。