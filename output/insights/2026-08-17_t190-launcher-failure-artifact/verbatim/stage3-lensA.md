**所見 1: 退避 hook は実運用で一度も呼ばれなくても新設テストが緑になり得る**

分類: `恒真化`  
深刻度: Major

根拠: [stage2-plan.md:220](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage2-plan.md:220>) は動的 plugin の `pytest_runtest_makereport` を使い、テストは「登録済み」と hook method の直接呼出しだけである。同 hook は [`_pytest/hookspec.py:757`](</home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/hookspec.py:757>) で `firstresult=True`、既定実装は [`_pytest/runner.py:384`](</home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/runner.py:384>) で直ちに `TestReport` を返す。

**失敗シナリオ:** 実装後に `@pytest.hookimpl(tryfirst=True)` を `trylast=True` へ変える。登録確認テストと `plugin.pytest_runtest_makereport(...)` の直接単体テストは緑のままだが、実 pytest では既定実装が先に値を返し、退避 hook は一度も発火しない。

提案: `pytester` などで子 pytest を起動し、未処理の `LauncherReturncodeMismatch` を実際に 1 件発生させ、終了後に bundle が生成されたことを外側から確認する live wiring test を必須にする。`tryfirst` の HookImpl 属性も固定する。

---

**所見 2: call phase の専用例外だけを捕捉する設計では setup、KeyboardInterrupt、xdist worker crash を退避できない**

分類: `scope`  
深刻度: Major

根拠: [stage2-plan.md:233](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage2-plan.md:233>) の発火条件は `call.when == "call"` かつ `LauncherReturncodeMismatch` に限定される。pytest は [`_pytest/runner.py:249`](</home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/runner.py:249>) で `KeyboardInterrupt` を再送出してから `pytest_runtest_makereport` を呼ぶ。xdist worker crash は controller 側の [`xdist/dsession.py:432`](</home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:432>) が nodeid だけから synthetic report を作るため、worker 内 plugin と `tmp_path` は利用できない。

**失敗シナリオ:** launcher を fixture から起動した後、その fixture が setup 中に例外を投げると `when="setup"` で除外される。Ctrl-C なら makereport 自体に届かない。`gw17` が SIGKILL されれば controller は `"worker 'gw17' crashed..."` だけを報告し、当該 worker の bundle は作られない。

提案: 対応範囲を「未処理の call-phase rc mismatch」に明示的に縮めるか、fixture setup 時に nodeid・worker・tmp path を耐久 root へ事前登録し、`pytest_keyboard_interrupt` と controller の `pytest_testnodedown` / `pytest_handlecrashitem` から salvage する。後者を実装しないなら worker crash まで原因分離できるとは記録しない。

---

**所見 3: 現行 test file には専用例外を経由しない launcher rc 判定が残っている**

分類: `scope`  
深刻度: Major

根拠: [`test_codex_worker_launch.py:1917`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1917>) は launcher を生の `subprocess.run(..., timeout=10)` で起動し、`:1927` で `assert completed.returncode == 2` とする。さらに [`:2333`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:2333>) も `assert LAUNCHER.main(...) == 2` である。どちらも `LauncherReturncodeMismatch` にならない。

**失敗シナリオ:** unsafe evidence grace の拒否が回帰して launcher が rc=0 で child を起動すると、`:1927` は通常の `AssertionError` で落ち、生成済み receipt・attempt artifact は退避されない。同じ呼出しが 10 秒を超えると、生の `TimeoutExpired` で落ちてやはり退避されない。

提案: launcher の起動と rc 検査をすべて共通 helper へ寄せる。AST meta-test で launcher command に対する生の `subprocess.run`、`LAUNCHER.main` の bare rc assert を拒否する。

---

**所見 4: `Popen.communicate()` timeout 時は生存中の source をコピーするため、bundle が一点整合しない**

分類: `正しさ境界`  
深刻度: Major

根拠: [`test_codex_worker_launch.py:567`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:567>) と [`:623`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:623>) は `TimeoutExpired` 後に process を kill / wait せず、そのまま専用例外を投げる。plan は [stage2-plan.md:241](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage2-plan.md:241>) で call report 中に `tmp_path` 全体を同期コピーする。

**失敗シナリオ:** launcher が 10 秒を超えても attempt log を書き続ける。hook はその最中に receipt、JSONL、sidecar を順次コピーし、コピー済み JSONL と後から現れた receipt/sidecar が異なる時点の状態になる。receipt がまだ無ければ、保存目的だった stop reason 自体が bundle に入らない。

提案: timeout 時は launcher の process group を停止し、wait と最終 drain を完了してから例外を生成する。これができない場合は bundle を `live-source/incomplete` と明記し、完全 snapshot と扱わない。

---

**所見 5: phase 計装は late wall gate より前に実行されるため、実時間上の受理集合不変は成立しない**

分類: `正しさ境界`  
深刻度: Major

根拠: plan は [stage2-plan.md:141](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage2-plan.md:141>) から多数の phase timestamp と状態更新を追加する。一方、現行コードは `_seal_attempt` の [`codex_worker_launch.py:1250`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1250>) および `_latch_final_job_limit` の [`:1971`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1971>) で、それ以前に費やした全実時間を wall gate に入れる。後者は `:2077`、`:2093`、`:2132` から複数回呼ばれる。

また [stage2-plan.md:190](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage2-plan.md:190>) の `finally` は正常 run にも sidecar を write/fsync する形であり、外側 test harness の 10 秒 timeoutにも加算される。

**失敗シナリオ:** 従来なら最後の gate sample が 2.999999 秒だった正常 runで、timestamp の取得・dict/set 更新が先に入り、sample が 3.000001 秒になる。`limit_trigger=max_wall_clock_s` へ反転する。内部 receipt が accepted でも、その後の sidecar fsync が共有 FS で止まれば外側の 10 秒 timeout が発火する。

提案: 「値と述語は不変」と「実時間上の受理集合不変」を分け、後者は保証不能だと brief を訂正する。既存 clock sample の再利用、空 snapshot を蓄積しない疎記録、正常 run の sidecar 要否を再裁定し、計装あり/なしの clock-call 数と追加時間を検査する。

---

**所見 6: receipt SHA-256 は同じ run の receipt であることを証明しない**

分類: `整合`  
深刻度: Major

根拠: [stage2-plan.md:88](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage2-plan.md:88>) は receipt hash により「組み違いを検出できる」とする。しかし現行テストには [`test_codex_worker_launch.py:3265`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:3265>) のように 2 launcher が同一 receipt path を競合し、一方だけが公開する実経路がある。plan の consumer 表は [stage2-plan.md:369](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage2-plan.md:369>) で checker が sidecar を読まないと明記し、binding 自体の検査テストもない。

**失敗シナリオ:** launcher A が receipt を公開し、B が create-only 競合で敗れる。B の `finally` が path 上の A の receipt を hash し、B の診断 sidecarへ `"status":"sealed"` と記録する。hash は完全一致するが、diagnostics と receipt は別 run である。

提案: receipt を自分が公開できたことを run-local flag で束縛し、敗者は `foreign/not-owned` とする。既存 receipt race testへ、勝者だけが sealed binding、敗者は非束縛になる assert を追加する。同一 job_id の並行まで扱うなら receipt schema を変えずに publisher ownership を得る公開 API が要る。

---

**所見 7: 退避 root の source 内包とコピー量無制限が、元の失敗を hook failure で覆い隠し得る**

分類: `正しさ境界`  
深刻度: Major

根拠: [stage2-plan.md:253](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage2-plan.md:253>) は環境変数で任意 root を許し、`:272` は `tmp_path` 全体を再帰保存する。特殊 file を避ける記述はあるが、source/destination の包含拒否、最大 file 数・byte 数・時間、コピー失敗時の原 failure 保持がない。

**失敗シナリオ:** `IZANAGI_LAUNCHER_FAILURE_ARTIFACT_ROOT=$tmp_path/archive` とする。作成した destination が walk 対象へ入り、自己再帰または指数的コピーになる。別例では 21 failure が大きな rollout を同時コピーして ENOSPC となり、makereport hook の例外が元の `LauncherReturncodeMismatch` を pytest internal error へ変える。

提案: resolve 後に source と destination の祖先関係を拒否する。receipt、diagnostics、manifestを優先し、file 数・byte 数・時間の上限と omitted reason を manifest に記録する。copy 失敗は必ず捕捉し、原 failure を上書きせず incomplete marker を残す。

---

**所見 8: 親 brief の「純増」基線は検索方法もコード認識も誤っている**

分類: `整合`  
深刻度: Major

根拠: [brief.md:45](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/brief.md:45>) の `grep -rn "A|B|C"` は `-E` がなく、`|` を選択として扱わない。実際、このコマンドは rc=1 だが `grep -Ern` なら `artifact_dir` が多数ヒットする。

さらに [brief.md:59](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/brief.md:59>) は「診断に出るのは limits/actuals の 2 dictだけで attempts 個別は出ない」とするが、現行 `_receipt_diagnostic` は [`test_codex_worker_launch.py:296`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:296>) から全 attempt の `accepted`、`limit_trigger`、status、exit code、residual、termination、`wall_clock_s` と stdout/stderr 抜粋を出している。

**失敗シナリオ:** 実装後、既存から出ていた attempt 情報を「新たに観測可能になった」と台帳へ記録し、archive の実効性が不十分でも純増検出力を達成したと誤判定する。

提案: 基線を「bounded message には attempt 個別値と stream 抜粋が既にある。欠けているのは full bytes の耐久保存と ①〜④の新規診断量」に訂正する。性質検索は `rg` または `grep -E` で再実施する。

---

**所見 9: sidecar の新設テストは positive-only で、誤診断を恒真化する変異が複数生存する**

分類: `恒真化`  
深刻度: Major

根拠: [stage2-plan.md:280](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage2-plan.md:280>) は evidence stop の真例、`:286` は三条件同時成立の真例、`:399` は phase の順序と正値だけを検査する。正常時の偽、閾値未満・exact-limit、各 site 固有値を検査しない。

**失敗シナリオ:** 次の変異はいずれも計画済みテストが緑のままになり得る。

- [`codex_worker_launch.py:353`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:353>) の既定を `evidence_forced_stop=True` にする。真例は通り、正常 run を全て強制停止と誤診断する。
- 新しい条件計算を比較式ではなく常に `list(_LIMIT_REASONS)` を返す形にする。同時三条件テストは通る。
- 全 phase boundary を終了時へ移して連続した monotonic sample を記録する。単調順序と正 duration は成立するが phase 分離は虚偽になる。
- natural-exit 診断だけ `>` を `>=` にする。既存の exact-limit accepted testは receiptしか見ないため、sidecarだけ「limit成立」と誤記録できる。

提案: 正常 run の `evidence_forced_stop=False`、閾値未満・exact-limit・各判定 site の空集合、論理時計で phase ごとの固有差分を exact assertする負例を追加する。上記変異を事前登録する。

---

**所見 10: residual reason のテストは normal reap しか通さず、実際の強制停止経路を壊しても緑になる**

分類: `恒真化`  
深刻度: Major

根拠: plan は [stage2-plan.md:115](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage2-plan.md:115>) で `_terminate` と `_normal_reap` の両方へ callback を通すが、新設 propagation test は [`:306`](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage2-plan.md:306>) で normal reap だけである。現行の二経路は [`codex_worker_launch.py:1207`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1207>) と `:1215` に分かれている。

加えて既存 [`test_codex_worker_launch.py:2692`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:2692>) は `_group_member_count` を引数 1 個の lambda に差し替えるが、plan の改名・更新一覧から漏れている。

**失敗シナリオ:** `_terminate` だけ `on_unknown` を `_wait_for_group_exit` へ渡さない変異にする。4 source 単体テストと normal-reap propagation はすべて緑だが、F57 の evidence/limit forced stop では reason が消える。別実装では `on_unknown=None` を常に keyword 渡しし、既存 transient test が `unexpected keyword argument` で赤になる。

提案: evidence forced stopから `_terminate` を通り、identity 不在または `/proc` errorが sidecarまで届く統合テストを追加する。既存 monkeypatch consumerも明示更新する。

---

**所見 11: 実装が緑でも実際の F57 原因分離は完了していないため、T-190 を閉じる終端条件が不足している**

分類: `scope`  
深刻度: Major

根拠: 現行 phase task は [`docs/phase3.md:998`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/docs/phase3.md:998>) で receipt / stop reasonを保持し、対照から原因を分離した後に fixture対応を裁定する契約である。brief は [brief.md:27](</work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/brief.md:27>) で失敗時 receipt と stop reasonを保存し、診断成果を台帳へ残すとしている。一方、plan の reporter は handled mismatchや緑走では bundleを作らず、最終結論も「検出可能にする」に留まる。

**失敗シナリオ:** 受入全走が偶然緑になり、synthetic testだけで退避機構を検証して T-190/F57 を完了扱いする。実 F57 bundleは 0 件で、P1〜P3 の近接原因も fixture harden値も未決定のままになる。

提案: 実装完了時の記録は「次回再発を観測可能にした」に限定する。実 F57 bundleを取得して原因を台帳へ帰属するまでは原因分離と fixture hardenを open に残す。T-190 を計装部分だけで閉じるなら、phase taskを分割する裁定が必要である。

## 総括

must-fix は所見 1〜7、9、10 である。特に現案は、退避 hook 全体が死んでもテストが緑になる変異、未退避の setup・interrupt・worker crash、並行 run の receipt 組違いを残している。

receipt schema、`accepted` の式、`_LIMIT_REASONS` 自体を直接緩める変更はplan上には見つからなかった。ただし計装が wall gate より前に時間を消費するため、実時間上の受理集合まで不変とは言えない。pytest・build・実走は行っておらず、以上は指定資料と対象行周辺の静的検査結果である。