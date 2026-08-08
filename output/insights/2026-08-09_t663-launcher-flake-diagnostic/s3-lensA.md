結論として、段 2 プランはこのまま採用できない。指定資料はすべて実読できた。以下は静的検査のみで、pytest は実行していない。

### 1. 診断項目だけでは `accepted` の不成立条件を分離できない

**主張:** brief は「7択を自己申告する」ことを成果物にしているが、プランの診断項目はそのうち `codex_exit_code` と `validator_rc` を欠く。また「7択」は相互排他的ではなく、複数条件が同時に偽になり得る。

**根拠:** `tools/codex_worker_launch.py:1029-1038` の受理式に対し、`s2-plan.md:8-18` が列挙するのは `limit_trigger`、evidence、metering、residual、termination、wall のみ。`wall_clock_s` は受理式の直接条件ではなく、`codex_exit_code` と `validator_rc` は receipt に存在する (`tools/codex_worker_launch.py:1052-1074`) のに出力対象外である。さらに `not force_not_accepted` も第 8 の conjunct だが、これは通常 rc=2 経路になる (`tools/codex_worker_launch.py:1304-1307,1669-1682`)。

**影響:** 子 process 異常と validator reject を区別できず、「次回は7経路のどれかを自己申告する」という受入成果物を満たさない。誤帰属リスクが残る。

**提案:** attempt ごとに最低限 `accepted`、`codex_exit_code`、`validator_rc` と既存5条件を出し、receipt 全体の `outcome`、`stop_reason`、`launcher_rc` も付ける。「7択」ではなく「受理 conjunct の真理値組」と表現する。

### 2. wall 3→6 秒は具体的な正常経路回帰を隠せる

**主張:** 現在検出でき、拡大後に通る欠陥を構成できる。

**根拠:** `[構成例・未実測]` 正常 attempt 後の最初の `_audit_receipt_value` (`tools/codex_worker_launch.py:1705-1711`) が回帰により約4秒掛かる場合、3秒では直後の `_latch_final_job_limit` (`:1712`) が `max_wall_clock_s` を立てる。一方6秒なら accepted のまま進む。プランは通常 call を6秒へ広げる (`s2-plan.md:51-56`)。

**影響:** 3〜6秒の production 最終化遅延を、全て「負荷耐性」として受理してしまう。production の比較式を変えなくても、テストの受理集合は実際に広がる。

**提案:** 通常 fixture を6秒にするなら、post-attempt/audit 経路の3秒境界を fake clock で決定的に検査する別テストを残す。これは明示的な受理集合変更として段4で裁定すべきである。

### 3. evidence 1→2 秒も late-evidence 回帰を隠せる

**主張:** 現在検出でき、拡大後に通る具体例を構成できる。

**根拠:** `[構成例・未実測]` `delayed_thread` の開始遅延 (`test_codex_worker_launch.py:180-185`) を1.5秒にすると、現行1秒では evidence deadline (`tools/codex_worker_launch.py:1176-1178,1239-1248`) により強制停止し、成功期待 assert (`test_codex_worker_launch.py:1520-1526`) が赤になる。2秒なら evidence を発見して通る。

**影響:** thread/session/rollout が1〜2秒見えない回帰を検出しなくなる。missing を固定する2テストだけ1秒に据え置いても、late-but-eventually-complete の境界は保護できない。

**提案:** 通常値2秒とは別に、制御時計または専用 fake mode で1秒境界を検査する。1秒契約を放棄するなら、その変更を fixture hardening ではなく明示的な許容遅延変更として記録する。

### 4. termination 0.05→0.2 秒は終了処理の遅さを実際に隠す

**主張:** 具体的な回帰を構成できる。これは据え置き集合の実質的な漏れである。

**根拠:** `[構成例・未実測]` `term_success` の SIGTERM handler (`test_codex_worker_launch.py:293-299`) の冒頭に0.1秒の遅延が入ると、現行0.05秒では `terminate_verified_group` が SIGKILL へ進む (`tools/dev_waves/worker.py:190-204`) ため `codex_exit_code == 0` (`test_codex_worker_launch.py:587`) が失敗する。0.2秒なら正常 exit 0 となり通る。プランはこのテストの `max_wall="3"` は固定するが、termination grace は固定しない (`s2-plan.md:45,49,56`)。

**影響:** SIGTERM 応答が50ms未満から100msへ悪化する回帰を隠す。residual/PID 消滅だけでは、迅速な終了と猶予末尾まで待った終了を区別できない。

**提案:** 少なくとも `test_limit_stop_is_never_accepted` に `termination_grace="0.05"` を明示し、`codex_exit_code == 0` を維持する。token/evidence/exception cleanup 系 (`test_codex_worker_launch.py:638-723,789-816,1564-1658`) も、何を保護するかを個別裁定する。

### 5. harness 10→20 秒は inner wall gate の外側にある遅延を隠せる

**主張:** 現在 `TimeoutExpired` で検出され、拡大後は rc=0 になり得る production 回帰がある。

**根拠:** `[構成例・未実測]` `_stage_receipt_write` または最終 publication が12秒停滞する場合を考える。accepted の最終 latch と receipt 作成は `tools/codex_worker_launch.py:1739-1747` で既に終わっており、その後の stage/publication (`:1757-1761`) 後に再 latch はない。現行 `_run_case` の10秒 timeout (`test_codex_worker_launch.py:429-435`) はこれを赤にするが、20秒なら accepted rc=0 が返る。プランはまさにこの timeout を20秒へ上げる (`s2-plan.md:58`)。

**影響:** receipt fsync/publication の10〜20秒級回帰と wall-clock 過少記録を受入全走が見逃す。

**提案:** production no-touch を守るなら timeout=20 の採用前に、成功経路の外側実時間を制約するテストを追加する。根本的には最終 stage/publication 後にも wall gate を再評価する別 scope の production 修正が必要で、裁定パッケージ候補である。

### 6. `stop_reason` / `limit_trigger` / `evidence_status` の assert 棚卸し自体は正しい

**主張:** この3 fieldについて、プランの列挙漏れや、拡大だけで恒真になる既存 assert は見つからなかった。

**根拠:** `s2-plan.md:39-41` は、実ファイルの `stop_reason` (`test_codex_worker_launch.py:489,584,606,627,649,675,715,809,837,1445,1493,1524,1632,1652,1666,1832`)、`limit_trigger` (`:586,608,632,653-655,678,717,812-813,1447,1470,1490,1512,1594-1596,1634`)、`evidence_status` (`:1526,1635,1654,1667`) と一致する。

**影響:** この部分だけは反証された懸念である。ただし termination の数値境界は上記4のとおり別に漏れている。

**提案:** 棚卸しは維持する。一方、`test_check_receipt_marks_self_asserted_limits...` は正常 run に3秒を残して `"3"` を期待するだけ (`test_codex_worker_launch.py:1170-1204`) なので、同時に `"6"` へ変えても binding 検査は弱まらない。3秒のままなら F57 型の移動先を1つ残す。

### 7. meta-test は実装次第で診断未結線のまま通る

**主張:** `pytest.raises(AssertionError)` だけでは、どの assert が発火したかを固定できない。

**根拠:** `s2-plan.md:62-67` の実装時に、raises 内へ旧 `assert completed.returncode == 0` を残し、捕捉後ではなく別途 `_launcher_failure_message(...)` を直接検査すれば、launcher assert に診断が結線されていなくても通る。また `assert all(("limit_trigger", "evidence_status", ...))` や `assert "field"` は非空文字列だけを評価する恒真実装になる。

**影響:** meta-test が緑でも、実際の rc mismatch が旧 `assert 1 == 0` のままという最悪の偽保証になる。

**提案:** 専用 `LauncherReturncodeMismatch(AssertionError)` を用い、`pytest.raises(LauncherReturncodeMismatch) as caught` で捕捉した `str(caught.value)` だけを検査する。formatter を一時的に固有 sentinel へ差し替え、その sentinel が捕捉例外へ入る wiring test と、`all(token in message for token in REQUIRED)` の実データ testを分ける。

### 8. 全文診断は元の rc 不一致を二次障害へ変え得る

**主張:** stdout/stderr と raw receipt の全文読込は、UnicodeDecodeError、巨大 message、OOM、読取例外で一次失敗を覆う。

**根拠:** production は attempt stream を binary で開き (`tools/codex_worker_launch.py:1090-1097`)、総量上限を設けていない。存在するのは event 1行当たり4MiBの上限だけ (`:54-55`)。対してプランは全 attempt の stdout/stderr 全文と raw receipt を要求する (`s2-plan.md:16-20`)。さらに direct call の多くは rc assert より先に receipt を strict loadしている (`test_codex_worker_launch.py:708-714,803-808,831-836,871-876,898-901,946-949,1778-1783`)。

**影響:** 非UTF-8なら診断側例外、巨大出力なら worker/controller OOM、receipt破損なら JSON 例外になり、肝心の `actual rc / expected rc` が消える。`test_complete_receipt_publication...` は期待が unordered `[0,2]` (`:1110-1113`) なので、単一 expected-rc helper の機械置換も不正確である。

**提案:** byte 単位で上限付き head+tailを読み、`errors="backslashreplace"`、総 byte 数、hash、切詰め量、pathを出す。一次 mismatch の短い prefix を先に確定し、診断例外は `diagnostic_status=failed:<type>` として同じ専用 AssertionError 内へ畳む。direct call は receipt load 前へ helper を移し、unordered 競争は2 processをラベル付きでまとめる専用 helperにする。

### 9. 人間まで届く層が scope に入っていない

**主張:** 現行 meta-test は診断を内側で捕捉して「pass」するため、pytest表示、xdist転送、`run_tests.py`、dispatch relayを一度も検査しない。しかも診断 summary を先頭へ置く設計は dispatch の末尾切詰めと逆向きである。

**根拠:** `s2-plan.md:8,62-67,75-76`。local `tools/run_tests.py` は stdioをそのまま継承する (`:845-878,1859-1868`)。一方 dispatch は失敗ログを末尾64KiBだけ relayする (`tools/pegasus/dispatch_compute.py:33-35,759-803`)。tmp は環境既定 `/tmp` である (`orchestrator/tests/conftest.py:1-10`)。ローカルに入っている pytest 9.1.1 は custom assertion stringをサイズ制限せず整形し、xdist 3.8.0 は reportを丸ごとserializeすることも静的確認した (`_pytest/assertion/rewrite.py:446-465`, `_pytest/reports.py:596-605`, `xdist/remote.py:281-289`)。計算ノード上での実走確認はしていない。

**影響:** 大きな stdout が後ろに付くと、dispatchで先頭の receipt summaryが消える。逆にxdistまでは巨大 messageを丸ごと運び、OOMリスクを増やす。「artifact保存」も compute-local `/tmp` pathだけでは人間が後から読めない。

**提案:** message全体を例えば32KiB以下に固定し、短い truth-table summaryを末尾にも置く。nested pytest `-n 2` で意図的 failure sentinelがcontroller出力へ届く検査と、64KiB超のscheduler logでも末尾summaryがrelayされる検査を追加する。後者は `test_pegasus_dispatch_compute.py` まで scopeを広げる裁定パッケージ候補である。

### 10. brief の実測は提案値と原因帰属を支えない

**主張:** median/p90 は rare full-suite tailの根拠にならず、「evidence graceの方が薄い」という比較対象も誤っている。0.30秒 probeは原因証明ではない。

**根拠:** timingはlogin node上の84 receipt (`brief.md:21-24`) だが、F57は32/48-workerの数千件全走で発生している (`docs/failures.md:1342-1358,1388-1415,1439-1453`)。また evidence deadlineは「session IDとrollout発見まで」 (`tools/codex_worker_launch.py:1176-1178,1239-1248`) なのに、briefは完了後の総 `wall_clock_s` と1秒を比較している。`max_wall=0.30` は median 0.428秒より小さく、同じ空出力rc=1を作る正の対照にすぎない (`brief.md:25-27`)。F57自身も実障害の3秒超過を断定していない (`docs/failures.md:1349-1353`)。

**影響:** 6/2秒という値は、実際に失敗する負荷分布にも evidence-ready時間にも結び付かない。同じ署名の再現だけで historical T-663 を wall超過へ誤帰属し得る。

**提案:** probeは「観測署名が衝突することのpositive control」とだけ記録する。実際の再発receiptで `limit_trigger` を観測するまで原因は未確定とする。T-427/T-190のタスク本文は指定資料に含まれず未読なので同一性は確認できない。F57にはlauncher、git timeout、PBS walltimeという別producerが混在する (`docs/failures.md:1396-1403,1417-1437`) ため、計装タスクだけ閉じてもT-663の原因解決は閉じない。

## 総括

must-fix:

- 診断へ `codex_exit_code` / `validator_rc` / outcome系を追加し、「7択」ではなく真理値組を出す。
- wall・evidence・termination・harnessの4拡大すべてに、拡大後だけ通る具体的回帰がある。
- 全文読込を廃し、byte上限・非UTF-8・診断例外・receipt破損でも一次rc不一致を保持する。
- meta-testを専用例外＋捕捉message＋wiring sentinelで非恒真化する。
- xdist／dispatch末尾64KiBまで診断が届く契約をscopeへ追加する。
- 0.30秒probeを原因証明にせず、実再発artifactなしでT-663の原因をcloseしない。

nit:

- 3 fieldのassert棚卸し自体は正しく、そこには列挙漏れを確認できなかった。
- 実測値は総所要とevidence-ready時間を分け、対象全走と同じ負荷母集団で取り直す。