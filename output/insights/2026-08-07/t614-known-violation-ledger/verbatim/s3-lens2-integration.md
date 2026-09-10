## 所見

### 1. P1 のままでは DW-O17 に従って wave を完了できない

**仮判定:** real

**根拠:** 既定監査には台帳対象外の `3f2c43d…` が残り、P1 は意図的に rc=1 を維持します（[brief.md:18–20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:18)、[brief.md:31–34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:31)、[plan.md:109](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:109)）。一方 DW-O17 は commit 後の既定 full-history 監査が赤なら停止を要求します（[operations.md:89–96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/dev-wave/operations.md:89)）。`dev_wave_land.py` は申告された commit closure を照合するだけで、監査結果自体は検証しません（[dev_wave_land.py:932–965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/dev_wave_land.py:932)）。

**影響:** 正しく運用すれば実装 commit 後に停止し、land 不能です。赤を「設計どおり」として続行すれば DW-O17 違反です。brief の「A 未実装なら gate が赤に固定」という DW-G05 記述も、A 実装後なお既定 gate が赤である点を表現できていません（[brief.md:37–39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:37)）。

**推奨対処:** 段4で P1 を hard blocker として裁定し、`3f2c43d…` の台帳追加、別の明示的 ratification、または wave 停止のいずれかを決めてから段5へ進むべきです。期待 rc=1 を受入成功として扱ってはいけません。

### 2. dispatch 経路では B の警告が手元へ届かない場合がある

**仮判定:** real

**根拠:** login 親は proposed 位置より前で dispatch 結果を return するため警告を出さず（[run_tests.py:1780–1788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1780)）、compute 子だけが出します。子 stderr は親へ常時ストリームされるのではなく、成功時は末尾 4 KiB、失敗時も末尾 64 KiB だけ中継されます（[dispatch_compute.py:759–778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/pegasus/dispatch_compute.py:759)）。既存テストも成功時に先頭が捨てられることを固定しています（[test_pegasus_dispatch_compute.py:316–338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_pegasus_dispatch_compute.py:316)）。

**影響:** 警告後に pytest が十分な stderr を出すと、警告は scheduler log の先頭から脱落し、login 端末では観測できません。B の主目的である誤記録防止が dispatch 走行で実効しません。plan の login-parent テストは「親が出さない」ことしか確認せず、この欠落を検出しません（[plan.md:94–100](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:94)）。

**推奨対処:** 警告を dispatcher の構造化結果・receipt に持たせて収集後に親が表示するか、login 親で表示して子には偽装不能な「表示済み」状態を渡してください。警告の後ろに 4 KiB/64 KiB 超の stderr を置く end-to-end test が必要です。

### 3. proposed 位置は「実際に pytest を起動する process」という説明と一致しない

**仮判定:** real

**根拠:** 警告は現行 `use_xdist = False` の直前に入ります（[plan.md:50–54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:50)）。しかし compute 側の xdist 検査はその後で、要件不成立なら rc=16 を返し（[run_tests.py:1788–1805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1788)）、pytest の child launch はさらに後です（[run_tests.py:1831–1840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1831)）。逆に dispatcher 起動失敗や site 拒否では警告を出さないと plan 自身が認めています（[plan.md:126](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:126)）。

**影響:** pytest 結果が存在しない xdist refusal では「この結果」警告が出る一方、同じく結果がない dispatcher failure では出ません。警告契約が invocation shape と completed result のどちらを指すのか不定です。

**推奨対処:** 「非受入形の invocation を常時表示」か「pytest 結果が得られた場合だけ表示」かを先に裁定し、compute xdist refusal、site refusal、dispatcher failure をテストに加えてください。

### 4. B は Pegasus dispatch receipt の値も変える

**仮判定:** real

**根拠:** compute 子の stderr は最大 2 MiB の tail として収集され（[dispatch_compute.py:33–35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/pegasus/dispatch_compute.py:33)、[dispatch_compute.py:664–684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/pegasus/dispatch_compute.py:664)）、`scheduler_logs.stderr` として receipt に永続化されます（[dispatch_compute.py:1728–1734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/pegasus/dispatch_compute.py:1728)）。一方、task-run の suite fingerprint は argv と `PYTEST_ADDOPTS` だけから作られ、標準出力は記録しません（[run_tests.py:782–799](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:782)、[run_tests.py:813–841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:813)）。

**影響:** rc、suite ID、件数は不変ですが、警告が tail 内に残る dispatch receipt と raw scheduler stderr は変化します。brief の B に対する「受理集合・値は不変」は、全 operational receipt を含む表現としては不正確です（[brief.md:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:39)）。

**推奨対処:** DW-G05 を「test result/task-run ledger は不変、Pegasus scheduler-log receipt は変更対象」と限定してください。

### 5. ローカル経路の二重表示と既存 run_tests テスト破壊は確認できない

**仮判定:** refuted

**根拠:** OTHER・直接 compute は proposed 箇所を一度だけ通ります。bounded 親は child rc で先に return し（[run_tests.py:1728–1740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1728)）、stderr を継承した child だけが表示します（[run_tests.py:1337–1349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1337)）。起動される pytest child は `run_tests.py` を再実行しないため二重表示もしません（[run_tests.py:1837–1840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1837)。`dev_wave_land.py` に run-tests 経路はなく、あるのは provenance message preflight です（[dev_wave_land.py:1387–1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/dev_wave_land.py:1387)）。標準 dev-wave check は acceptance shape の `orchestrator/tests` を渡します（[cli.py:188–195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/dev_waves/cli.py:188)）。

既存出力テストも、影響経路では substring assertion のみです（[test_run_tests_nproc.py:174–196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_nproc.py:174)）。exact stream テストは `_call_and_record()` 等の直接テスト（[test_run_tests_task_run.py:407–459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_task_run.py:407)）か、wrapper を通さない `python -m pytest` です（[test_run_tests_task_run.py:702–714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_task_run.py:702）。`PYTEST_ADDOPTS` 群も classifier/preflight の直接検査です（[test_run_tests_preflight.py:250–286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:250)）。

**影響:** 静的には既存 assertion の修正対象はありません。ただし dispatch 可視性は所見2のまま残ります。

**推奨対処:** 新規 exact-output test では `_ensure_xdist` と version も固定し、環境依存の stdout を排除してください。

### 6. 台帳 validator の実行時点が未確定で、rc=2 と message-file 不変を同時に保証できていない

**仮判定:** real

**根拠:** plan は定数付近で registry を構築し、破損時は `RuntimeError → rc=2` とします（[plan.md:3–14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:3)）。しかし `main()` が `RuntimeError` を rc=2 に変換する try は history/message 分岐直前にしかありません（[check_ai_provenance.py:1790–1830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1790)）。import 時に validator が raise すれば try に到達せず、traceback＋通常の import failure rc になります。また `--message-file` まで壊れ、brief の不変条件に反します（[brief.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:28)）。

**影響:** 壊れた台帳に対する rc=2 契約が成立せず、`dev_wave_land.py` の fold message preflight も無関係な履歴台帳破損で拒否され得ます。

**推奨対処:** validator を history 分岐内、かつ既存 try の内側で lazy に呼んでください。malformed registry の history rc=2/no traceback と、同じ状態での message-file 逐語不変を別々に固定すべきです。

### 7. finding と kind の並行 tuple、および stale 条件が閉じていない

**仮判定:** real

**根拠:** plan は `normal_findings` と同順の `normal_finding_kinds` を要求しますが（[plan.md:16–23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:16)）、現実の `_normal_commit_audit()` は message、scope、CAB、waiver、implementation の複数 finding 群を順に連結します（[check_ai_provenance.py:816–846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:816)）。plan は抑止可能な2種以外に何を格納するか定義していません。

また brief は「台帳 entry の期待 finding が出ない」場合を stale と読めますが（[brief.md:25–26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/brief.md:25)）、plan は「全実効 finding が0」の場合だけ stale とします（[plan.md:30–31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:30)）。期待種別が消え、別種 finding だけ残る場合は stale が報告されません。

**影響:** `zip` の長さ不一致や誤分類で別 finding を落とすと受理集合を広げます。stale の不一致は rc を緑にはしませんが、不要な台帳 entry の検出を遅らせます。

**推奨対処:** `NormalFinding(text, suppressible_kind | None)` のような単一構造にし、並行配列を避けてください。stale は「selected entry の期待種別が不在」を基準にするか、brief を「全 finding が0」に修正し、期待種別＋別種 finding の混在テストを追加すべきです。

### 8. exact-match テスト案の短縮 SHA ケースは validator 契約と衝突し、negative control 単独では恒真になる

**仮判定:** real

**根拠:** plan は短縮 SHA entry を registry 構築時に拒否すると定める一方（[plan.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:14)）、`test_known_violation_requires_exact_full_sha_and_finding_kind` は短縮 entry を「既知扱いされない」ケースとして扱います（[plan.md:68–70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:68)）。期待値が rc=2 なのか、単なる lookup miss なのか不明です。またこの negative test、範囲外 test、`3f2c43d…` test は、抑止機構を丸ごと外しても単独では通り得ます（[plan.md:80–90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:80)）。

**影響:** exactness を主張する個別テストが、exact lookup の存在を証明しません。ただし literal six、real six、stale、known stdout の positive tests は台帳削除で落ちるため、追加 suite 全体が恒真という疑いは refuted です（[plan.md:60–86](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:60)）。

**推奨対処:** 短縮 registry entry は明示的に rc=2 test とし、lookup exactness は「有効な full entry では既知→同一 finding の別 full SHA では新規」という正負対で検査してください。さらに registry を空にすると六件が新規へ戻る mutation control を一つ置くべきです。

### 9. 既存 provenance テストの rc・件数前提が直ちに壊れるという懸念と、exact pin が実装不能という懸念は refuted

**仮判定:** refuted

**根拠:** 既存の rc=1・件数 assertion は tmp repo の synthetic SHA を使うものです（例: [test_check_ai_provenance.py:707–742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:707)、[test_check_ai_provenance.py:1605–1625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1605)）。exact six SHA とは一致しないため件数は変わりません。real repo を使う既存テストは固定 correction target の `_normal_commit_audit()`（[test_check_ai_provenance.py:1309–1336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1309)）と policy epoch pin（[test_check_ai_provenance.py:2351–2355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:2351)）で、六 SHA の history 抑止経路ではありません。

`HistoryAudit` 末尾 field に既定値を持たせる計画なので、既存3引数構築も維持できます（[test_check_ai_provenance.py:4059–4078](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:4059)）。message-file exact outputも history 分岐外です（[test_check_ai_provenance.py:2167–2187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:2167)）。literal tuple pin は real repo 不要で、behavior pin の real-object 依存も既存テストがすでに無条件で採用しており、skip にはなっていません。

**影響:** plan どおり known=0 の既存出力を逐語維持すれば、静的に更新必須な既存期待値はありません。浅い checkout なら新テストは skip ではなく失敗するため、CI の object-availability 契約は既存と同じです。

**推奨対処:** plan 記載どおり worker/empty/correction テストに `known_violations` assertion だけを加え、親が実測してください。

### 10. A の通常 dispatch、message-file、AGENTS/CLAUDE 更新に関する懸念は refuted

**仮判定:** refuted

**根拠:** 履歴 audit は site 判定・login dispatch の後で実行されます（[check_ai_provenance.py:1685–1788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1685)、[check_ai_provenance.py:1790–1827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1790)）。したがって台帳照合は compute/bounded execution child 側だけです。bounded child は親 stream を継承し（[check_ai_provenance.py:1522–1532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1522)）、compute log も親へ中継されます（[dispatch_compute.py:1766–1773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/pegasus/dispatch_compute.py:1766)）。固定六件の terminal stdout は 4 KiB 未満なので、末尾に配置すれば既知-only 成功時にも戻ります。

`--message-file` は history 分岐へ入らないため、正常な固定台帳からは影響を受けません（[check_ai_provenance.py:1795–1827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1795)）。`dev_wave_land.py:1388` の preflight もこの mode だけです。AGENTS/CLAUDE は監査実行と自己 dispatch を要求するだけで rc 詳細を複製しておらず、記述はそのまま正しいです（[AGENTS.md:26–30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/AGENTS.md:26)、[CLAUDE.md:120–123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/CLAUDE.md:120)）。履歴 semantics は既に `PR-A02` へ routing されています（[ai-provenance.md:86–93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/ai-provenance.md:86)）。

**影響:** 所見1と所見6を除けば、message preflight、実行場所判定、AGENTS/CLAUDE の受理集合に変更は不要です。

**推奨対処:** validator を history-lazy にし、既知 stdout を terminal tail に置いて dispatch relay test を追加してください。文書変更は plan どおり `PR-A02` に限定し、親実測は DW-O18 に従い repo root から行うべきです（[operations.md:98–103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/dev-wave/operations.md:98)）。

### 11. 段5の二並列に同一ファイル編集競合はない

**仮判定:** refuted

**根拠:** A は checker と `test_check_ai_provenance.py`、B は runner と `test_run_tests_preflight.py`、文書は親、と排他的に割り当てられています（[plan.md:129](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t614-provenance-ledger/s2/plan.md:129)）。

**影響:** plan 記載のままなら編集競合はありません。ただし A の既存テストは `run_tests.py` を読み込む node を含むため（[test_check_ai_provenance.py:3800–3808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:3800)）、B の編集中に走らせた子テストを最終証拠にはできません。

**推奨対処:** ファイル所有は維持し、両子完了後に親が関連2ファイルと受入全走を直列に再実行してください。

## 総括

現 plan は、P1 により DW-O17 の terminal gate が必ず赤になるため、段5へ進む前に NO-GO 裁定が必要です。  
B は login 親で出さず bounded log に依存するため、dispatch 成功時に警告が手元から消える実効性欠陥があります。  
台帳 validator の実行時点、finding-kind の構造、stale 定義、短縮 SHA test も plan 修正が必要です。  
既存 run-tests/provenance テストが静的に壊れる証拠はなく、exact six の pin 自体も実装可能です。  
段5の編集所有競合はありませんが、親の統合実測は必須です。  
read-only の静的検査のみであり、pytest は実行しておらず、緑は主張しません。