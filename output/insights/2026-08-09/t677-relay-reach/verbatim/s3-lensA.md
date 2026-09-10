静的反証のみを行い、pytest は実走していない。must-fix 10 件、nit 1 件。

## 1 — must-fix : 「失敗ごとに node id と診断本体」は 49,152-byte 予算と両立しない

(i) brief は全 failure ごとの node id・診断本体を不変条件にしている。一方プランが保証するのは最悪時 9 ブロックだけで、残りは人間が逆引きできない `omitted_manifest_sha256` に畳む。さらに選択された node id も 256 bytes で切る。96/110 failures の走行では、明示された不変条件を構造上満たせない。

(ii) 一次資料: [s1-brief.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s1-brief.md:63)、[s2-plan.md:53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:53)、[s2-plan.md:119](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:119)、[s2-plan.md:126](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:126)、[s2-plan.md:138](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:138)

(iii) **成果物への影響**: digest の `selected` と `omitted_failures` が示す受理集合は全 failures ではなく標本になり、真因が非選択 failure にある場合、材料レポート・受入記録の原因参照が別 failure を指す。

(iv) 「全件」要求を維持するなら別 transport または全ログへの耐久参照が必要。64 KiB を維持するなら、段 4 前に「決定的な代表 failure＋正確な省略会計」へ不変条件を明示的に弱め、receipt 内の完全な scheduler log を正本として併記する裁定が必要。

## 2 — must-fix : `terminalreporter.stats` は pytest の正しさ判定ではなく、差し替え可能な表示カテゴリである

(i) `TerminalReporter` は `pytest_report_teststatus` が返すカテゴリへ report を格納する。この hook は `firstresult` なので、別 plugin は失敗を `"custom"` へ、成功を `"failed"` へ分類できる。一方 pytest の rc は `report.failed` から増える `session.testsfailed` で決まる。したがって rc=1 なのに digest 無し、または rc=0 なのに digest 有りが構成できる。`terminalreporter` が無い・互換でない場合に fallback ERROR 行を出せば、緑走行も 4 KiB 枠を汚す。

また、テスト (b) が空の fake `stats={}` だけなら、`if reporter.stats:` という壊れた実装でも緑になる。実走では pass、skip、xfail、warning の stats は非空である。逆に `error` カテゴリを無視する実装は、通常 assertion の E2E を通しつつ setup/teardown/collection error を落とせる。

(ii) 一次資料: [s2-plan.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:63)、[s2-plan.md:183](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:183)、[terminal.py:625](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/terminal.py:625)、[hookspec.py:1067](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/hookspec.py:1067)、[main.py:386](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/main.py:386)、[main.py:698](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/main.py:698)、[pytest_stats.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/task_runs/pytest_stats.py:55)

(iii) **成果物への影響**: 実際の acceptance rc と表示 digest が食い違い、赤の原因が材料レポートから消えるか、緑走行の最終 summary が成功中継 4 KiB から押し出される。

(iv) `pytest_runtest_logreport` / `pytest_collectreport` で `report.failed` を独立 stash し、unconfigure 前に snapshot する。pass、skip、xfail、非 strict xpass、warning、0 collected、成功 collect-only は無出力、setup/teardown/collection error、strict failure、`-x` は出力、と明示した行列を追加する。terminal 無効化・差替え・カテゴリ改変も検査する。

## 3 — must-fix : xdist worker crash の一部には `failed/error` report が存在しない

(i) 通常の worker report と「実行中 test を伴う crash」は controller に届く。後者は xdist が synthetic failed report を作る。しかし worker internal error は `pytest_internalerror` を呼ぶだけで TestReport を作らず、scheduled item が無い crash も `crashitem=None` なら synthetic report が無い。よって「全 worker の failed/error report が stats に集まる」から「全 worker 異常が digest に入る」は導けない。96 assertion failures の E2E はこの穴を踏まない。

(ii) 一次資料: [s2-plan.md:149](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:149)、[s2-plan.md:162](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:162)、[dsession.py:220](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:220)、[dsession.py:238](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:238)、[dsession.py:432](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:432)、[terminal.py:580](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/terminal.py:580)

(iii) **成果物への影響**: worker internal/pre-item crash による受入赤では digest が空になり、受入記録が実装 failure と基盤 crash を区別できず、材料レポートの原因分類が変わる。

(iv) `pytest_internalerror` と `pytest_testnodedown` 相当を別診断項目として収集するか、対象外であることを明記して既存 xdist summary を正本にする裁定が必要。E2E は「実行中 crash」と「collection/internal crash」を分ける。

## 4 — must-fix : outer wrapper の例外境界をテスト (f) が固定していない

(i) Pluggy は inner hook の例外を wrapper の `yield` 位置へ `throw()` する。プランの「`finally` で出力」と「worker は冒頭で return」を素直に組み合わせ、`finally: if worker: return` と書くと、StopIteration が元例外を消す。controller 側でも `yield` を含む広い `except Exception` は同じ欠陥になる。逆方向には digest 例外が `_ensure_unconfigure()` から逃げて元 session rc を上書きできる。fake builder の RuntimeError だけでは両方を検出できない。

また brief の「生成中の例外すべて」とプランの `except Exception` は一致しない。KeyboardInterrupt/SystemExit を握るべきではないため、brief 側を「通常例外」に狭める必要がある。

(ii) 一次資料: [s2-plan.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:33)、[s2-plan.md:151](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:151)、[s2-plan.md:187](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:187)、[_callers.py:134](/home/SFC/tanab/.local/lib/python3.10/site-packages/pluggy/_callers.py:134)、[_callers.py:157](/home/SFC/tanab/.local/lib/python3.10/site-packages/pluggy/_callers.py:157)、[config/__init__.py:1207](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/config/__init__.py:1207)、[main.py:359](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/main.py:359)

(iii) **成果物への影響**: 既存 plugin の unconfigure 異常が握り潰されれば本来不受理の session が元 rc で受理され、逆に digest 異常が逃げれば本来の acceptance rc が失われる。

(iv) `yield` を digest 用 catch の外へ置き、`finally` 内は `if not worker: _safe_write()` として `return` しない。controller/worker の双方で sentinel 例外を generator に投げ、同一 object が再送出されるテストを追加する。digest 自身の通常例外だけを内部で処理し、`BaseException` は伝播させる。

## 5 — must-fix : E2E は xdist の実診断が 0 件でも緑になる恒真ゲートである

(i) E2E が検査する内容は marker、`failures=96`、サイズ、順序だけで、`selected>0`、実 nodeid、excerpt、tail sentinel を一つも要求しない。例えば「xdist が付ける `report.node` 属性がある report はすべて非選択にするが、account の failures は stats 長から数える」実装なら、SimpleNamespace の単体テストは通り、E2E も `failures=96 selected=0 omitted_failures=96` で通る。

(ii) 一次資料: [s2-plan.md:182](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:182)、[s2-plan.md:189](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:189)、[s2-plan.md:202](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:202)、[dsession.py:326](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:326)

(iii) **成果物への影響**: acceptance は「診断到達 gate が緑」と記録される一方、実 digest には原因がなく、材料レポートは node 名・診断参照を作れない。

(iv) 実 xdist report 由来の既知 nodeid、4 KiB 超の head decoy、末尾 sentinel を digest frame 内で直接検査する。`selected`、全 account 値、hash をテスト側の独立 oracle で検算し、sentinel が digest 外に偶然存在するだけでは通さない。

## 6 — must-fix : この「E2E」は人間到達までの全層を通らず、relay 自体も best-effort である

(i) 必要な経路は次の全層である。

`pytest → run_tests.py → compute job script → scheduler stdout file → 2 MiB収集 → 64 KiB中継 → | 接頭辞 → 親stdout/stderr → 人間が読む場所`

プランの subprocess は最初の pytest stdout で止まり、run_tests、job、scheduler file、`_bounded_log`、`_relay_scheduler_logs` を呼ばない。現行の run_tests/job は pytest 後に stdout を足さないため通常経路は成立するが、relay は明記どおり best-effort で、BrokenPipe/relay error を握り、child rc を保存する。さらに stdout の後に stderr relay が続くため、digest が親の結合端末でも最末尾になるとは限らない。親端末側の追加切り詰め有無は未確認である。

(ii) 一次資料: [s2-plan.md:189](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:189)、[run_tests.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/run_tests.py:367)、[run_tests.py:845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/run_tests.py:845)、[dispatch_compute.py:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/pegasus/dispatch_compute.py:501)、[dispatch_compute.py:588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/pegasus/dispatch_compute.py:588)、[dispatch_compute.py:664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/pegasus/dispatch_compute.py:664)、[dispatch_compute.py:741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/pegasus/dispatch_compute.py:741)、[test_pegasus_dispatch_compute.py:362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pegasus_dispatch_compute.py:362)

(iii) **成果物への影響**: relay error 時も acceptance rc は保持される一方、親の受入記録には診断が無く、完全ログの receipt 参照を材料レポートへ転記できない。

(iv) 最低限、subprocess stdout を実 scheduler-log file として `_bounded_log` と `_relay_scheduler_logs` に通す結合検査を追加する。それでも broken pipe は保証できないため、主張を「正常 relay 経路で末尾に残る」へ狭め、receipt の `scheduler_logs.stdout.path` を人間向け耐久 fallback として手順・検査へ追加する。真に「確実」を維持するなら dispatcher/human consumer を scope 外裁定へ返す。

## 7 — must-fix : excerpt の `| FAILED ...` が変異 harness の偽 failure node になる

(i) digest は全 excerpt 行へ `| ` を付ける。変異 harness は raw scheduler stdout 全文を読み、各行の先頭 `|` をすべて剥がしてから `FAILED ` を node として抽出する。したがって diagnostic 本文に `FAILED tests/test_gate.py::test_fake` が含まれるだけで、実際には落ちていない node が `failed_nodes` に混入する。外側 dispatch prefix が付けば `| | FAILED ...` になるが、抽出器は両方剥がす。

これは F65/F71 が警告している consumer 取り残しの再発である。task-run 台帳は sidecar を使うため同じ parser 事故は確認されなかったが、変異 harness は直接壊れる。

(ii) 一次資料: [s2-plan.md:85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:85)、[s2-plan.md:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:97)、[mutation_harness.py:791](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/mutation_harness.py:791)、[mutation_harness.py:816](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/mutation_harness.py:816)、[mutation_harness.py:1067](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/mutation_harness.py:1067)、[failures.md:1669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/docs/failures.md:1669)、[failures.md:1822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/docs/failures.md:1822)

(iii) **成果物への影響**: 試行台帳の `failed_nodes` 集合へ偽 node が入り、正しい変異が `KILLED` ではなく `MISMATCH/PARSE_ERROR` と記録される。

(iv) 内部 excerpt prefix を `> ` など `_strip_relay_prefix` が除去しない文字へ変更する。diagnostic に有効な偽 `FAILED path::node` 行を入れ、local/raw-log/dispatch-prefix の三形で抽出集合が変わらない consumer テストを追加する。

## 8 — must-fix : 87.5% の算術は正しいが、launcher 診断消失の実測にはなっていない

(i) `size` は scheduler stdout file の `stat().st_size`、表示 `omitted_bytes` は収集済み record の省略と `size - relayed_size` の最大値である。`_utf8_tail` は decode 済み Unicode を文字境界で戻るため、64 KiB より1 byte少ない 65,535 bytes が残り得る。該当値は、

`523,987 - 458,452 = 65,535`、`458,452 / 523,987 = 87.493010%`

なので 87.5% は正しい。

しかし当該 110-failure log の short summary に `test_codex_worker_launch` はなく、launcher の `truth_summary` 消失を再現した artifact ではない。他の切り詰め log には実際の DescriptorError 本体が残っており、「切り詰め発生」から「診断本体消失」への全称一般化はできない。invalid UTF-8 では replacement decode 後の再 encode を挟むため、`omitted_bytes` の raw-byte 厳密性も一般には未証明である。

(ii) 一次資料: [dispatch_compute.py:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/pegasus/dispatch_compute.py:668)、[dispatch_compute.py:687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/pegasus/dispatch_compute.py:687)、[dispatch_compute.py:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/tools/pegasus/dispatch_compute.py:771)、[acceptance-2.log:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/acceptance-2.log:8)、[acceptance-2.log:1023](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/acceptance-2.log:1023)、[fix5-tests.log:8](/work/1/SFC/tanab/dev-wave-jobs/wave-t325-trial-registry/s6/fix5-tests.log:8)、[fix5-tests.log:20](/work/1/SFC/tanab/dev-wave-jobs/wave-t325-trial-registry/s6/fix5-tests.log:20)、[s1-brief.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s1-brief.md:34)

(iii) **成果物への影響**: generic failure marker の gate を launcher 診断到達の証明として受理すると、材料レポートに `truth_summary` が無いまま T-677 を閉じる誤った参照が残る。

(iv) brief を「generic truncation は再現済み、launcher 固有の消失は推論」に訂正する。E2E の failure 本文には実 `_bounded_failure_message` 相当の 16 KiB payload と末尾 `truth_summary` sentinel を用い、sentinel が digest 内に残ることを直接固定する。

## 9 — must-fix : 代表選択の事前登録変異は fixture 条件次第で新テストも緑のままになる

(i) `source-file representative tier` を空にする変異は、テスト (c) の report が全て同一 source、全件が予算内、または期待が account 値だけなら出力を変えない。プランは「単一 file 独占を検出」と書くが、予算を実際に飽和させる複数 source fixture と独立期待集合を指定していない。

登録6件について、旧テストが直接同じ新規 helper を検出する経路は静的には見つからなかった。一方、補助説明にある「dispatcher limit だけを縮める」ケースは既存 literal test も必ず赤にするため、新規 (e) 単独の検出力としては帰属できない。

(ii) 一次資料: [s2-plan.md:126](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:126)、[s2-plan.md:132](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:132)、[s2-plan.md:170](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:170)、[s2-plan.md:184](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:184)、[s2-plan.md:225](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:225)、[test_pegasus_dispatch_compute.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pegasus_dispatch_compute.py:357)、[mutation.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/docs/dev-wave/mutation.md:49)

(iii) **成果物への影響**: 試行台帳で representative 変異が偽 SURVIVED になるか、dispatcher-limit 赤を新規 test の sensitivity と誤帰属し、`failed_nodes` と detector 参照が不正になる。

(iv) 予算超過する件数、複数 source、最大 longrepr を多数持つ支配 source、短い少数 source を fixture に固定し、少数 source の既知 node が選択されることを独立 oracle で確認する。段 6 では新旧 test 集合の実 node を別々に記録し、既存 literal test の赤を新規検出力へ数えない。

## 10 — must-fix : P2 の全称と top-level `tools` import は既存 plain-runner 契約を壊す

(i) brief の「tracked test file 150件すべて `orchestrator/tests`」には反例があり、少なくとも `output/.../test_run_probes_evaluator.py` は tracked pytest test である。canonical acceptance からは `pytest.ini` により除外されるため、「canonical suite」なら成立するが「全 tracked tests」は成立しない。

さらにプランの top-level `from tools...` は repo root が `sys.path` にあることを要求する。既存 `test_real_repo_serialization.py` の plain runner は `HERE` と `ORCHESTRATOR` だけを追加して `conftest.py` を隔離ロードするため、root が `PYTHONPATH` に無い環境では `ModuleNotFoundError` が collection/test 観測を変える。現行 conftest の観測 hook はこの種の影響を避けるため lazy import＋fail-open である。

(ii) 一次資料: [s1-brief.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s1-brief.md:52)、[s2-plan.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:47)、[s2-plan.md:166](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:166)、[test_run_probes_evaluator.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/output/insights/2026-08-03_t361-t362-cluster-probes/driver/test_run_probes_evaluator.py:1)、[pytest.ini:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/pytest.ini:12)、[test_real_repo_serialization.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_real_repo_serialization.py:26)、[test_real_repo_serialization.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_real_repo_serialization.py:86)、[conftest.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/conftest.py:249)

(iii) **成果物への影響**: 対応する plain-runner 検査が conftest import 前に赤くなり、受入証拠を生成できない。また canonical 外 test の赤には digest が出ず、P2 が主張する診断受理集合から漏れる。

(iv) relay 定数 import は failure 検出後の lazy path へ移し、import 失敗時は無出力にする。repo root を除いた隔離 load テストを追加する。P2 は「`pytest.ini` の canonical acceptance testpaths 149 files」に限定して記述する。

## 11 — nit : 新規 test file の plain-runner/allowlist 手順がプランから漏れている

(i) 新設予定の `test_pytest_failure_digest.py` について、`__main__` harness または README allowlist のどちらを採るかが書かれていない。既存 meta-test はこの状態を必ず赤にするため、恒真な受理にはならないが、F42 と同じ受入全走の空振りになる。

(ii) 一次資料: [s2-plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:71)、[s2-plan.md:236](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/s2-plan.md:236)、[test_plain_runner_coverage.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_plain_runner_coverage.py:44)、[test_plain_runner_coverage.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_plain_runner_coverage.py:60)、[failures.md:996](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/docs/failures.md:996)

(iii) **成果物への影響**: acceptance は meta-test で fail-closed になるため誤った certified 選択は生じないが、受入全走結果が本機構の判定前に赤となり、再走が必要になる。

(iv) `pytest.main([__file__, ...])` の self-run harness を追加するか、根拠付きで allowlist へ載せ、`test_plain_runner_coverage.py` を新規 test と同じ先行走に含める。

## 総括

must-fix は以下。

- 全 failure 保存という不可能な不変条件を、代表診断＋完全ログ参照へ裁定し直す。
- `terminalreporter.stats` 依存をやめ、pytest の実 report と全終了形を独立収集する。
- xdist internal/pre-item crash を別経路で扱うか、保証対象外と明記する。
- wrapper の `yield` 例外を絶対に握り潰さない構造と検査を入れる。
- E2E で実 xdist node・診断末尾を直接検査し、全 transport 層との結合を固定する。
- best-effort relay の限界に合わせて「確実に人間へ届く」という主張を狭めるか、receipt fallback を scope に入れる。
- `| FAILED` による変異 harness の consumer 取り残しを解消する。
- launcher 固有の実測不足を訂正し、`truth_summary` sentinel を代表入力にする。
- 代表選択変異の予算飽和 fixtureと新旧テスト帰属を固定する。
- top-level `tools` import を除き、canonical scope と plain-runner scopeを分離する。