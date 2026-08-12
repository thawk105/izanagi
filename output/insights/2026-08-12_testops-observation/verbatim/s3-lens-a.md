結論は **NO-GO** です。`dev-wave` 段 3 契約に従い、親 brief の前提も含めて静的に攻撃しました。pytest は実行しておらず、緑とは判定していません。

## Blocker

### 1. sidecar の書込失敗が default-on で pytest の rc を壊す

- (a) 該当: [pytest_stats.py:87-144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/task_runs/pytest_stats.py:87)、[run_tests.py:845-878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:845)、[s2-plan.md:144-161](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:144)
- (b) `_create_sidecar()` は `lstat/open/write/fsync` から `OSError`・`PermissionError`・`ENOSPC` を送出し得る一方、`write_session_stats()` は `ValueError` しか捕捉しない。plan はこのファイルを無変更のまま、sidecar を全走行で有効にする。指定範囲では上位 hook の追加捕捉も確認できないため、pytest が内部エラー化し、本来の test rc を置換する経路が残る。
- (c) `_create_sidecar` の各 I/O 点へ `PermissionError`、`OSError(ENOSPC)`、`fsync` 失敗を注入し、hook が例外を外へ出さず、元の pytest rc/stdout/stderrを保つテスト。bootstrap だけでなく pytest 子内の sidecar 書込を対象にする。
- (d) 重大度: **blocker**
- 直さない場合: 記録先の権限・容量障害だけで受入全走が赤または停止し、「書く側 fail-open」が破れる。

### 2. 「4 gate 本体無差分」では受理集合を固定できない

- (a) 該当: [brief.md:48-50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/brief.md:48)、[run_tests.py:74-122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:74)、[run_tests.py:388-560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:388)、[run_tests.py:1667-1710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:1667)、[s2-plan.md:257-260](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:257)
- (b) 4 gate は関数本体だけでなく、`_NONSELECT_*`、`_SELECT_FLAGS`、`_NO_EXECUTION_FLAGS`、dispatch-exempt 表と、caller が渡す `args`・`PYTEST_ADDOPTS` に依存する。plan は定数近傍 `:65-68` と main wiring を変更するのに、静的検査は `:367-560` の hunk だけを見る。例えば `_NO_EXECUTION_FLAGS` から1項目を落とす変異や、caller が記録初期化前後で `PYTEST_ADDOPTS` を変える変異は、この検査を通過する。
- (c) 4関数すべてについて、空白・非空・壊れた quoting の `PYTEST_ADDOPTS`、値付き/compact/unknown/selector/no-execution flag を含む truth-table characterization test を作り、recording 初期化前後と direct/dispatch/scope で全 bit が同じことを固定する。定数表 `:74-122` も無差分面に含める。
- (d) 重大度: **blocker**
- 直さない場合: gate 本体を触らずに受入形が False/True へ倒れ、事前検査が黙って不発になる既知事故を再現できる。

### 3. 外部 base が証拠 namespace を指せる

- (a) 該当: [ledger.py:49-51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/task_runs/ledger.py:49)、[decisions.md:2512-2517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/docs/decisions.md:2512)、[s2-plan.md:63-110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:63)、[schema.py:300-303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/task_runs/schema.py:300)
- (b) `IZANAGI_TASK_RUNS_BASE` の契約は「絶対 path・現在 repo 外」だけで、D66 の `campaigns/env/exploration/.../runs` 禁止を series manager 自身へ要求していない。外部の証拠 tree、別 checkout の証拠 namespace、またはそこへ解決する symlink を base にできる。さらに skeleton は `start_run()` より先に `.generation.lock`、generation、`pilot.json` を作るため、ledger 側拒否があっても既に混線する。`authority` 定数は場所への書込権限ではない。
- (c) 全 banned namespace と、外部 symlink→repo内/証拠 namespace を base にし、lock を含む一切の byte を作らず pytest rc を保つテスト。`O_NOFOLLOW` 削除を殺すには、事前 symlink 検査とは別に検査後差替えの TOCTOU テストが必要。
- (d) 重大度: **blocker**
- 直さない場合: 開発観測物が proof-addressable な場所へ生成され、「証拠から構造的に分離」の前提が崩れる。

### 4. 自動 rollover が D66 の pilot 停止・ユーザー裁定を迂回する

- (a) 該当: [README.md:14-23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:14)、[README.md:91-99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:91)、[decisions.md:2507-2510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/docs/decisions.md:2507)、[s2-plan.md:73-114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:73)、[s2-plan.md:219-221](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:219)
- (b) 現契約では10 run/14日/finalで新規 start を止め、最終 report 後に継続・縮小・撤去をユーザー裁定へ返す。plan は同じ状態を捕捉して無条件に次世代を作り、自動 final report も作らない。ユーザーの「TestOps=(A)」選択は、無期限 rollover の明示承認ではない。段7の decisions fragment は事後記録であり、事前裁定の代用にならない。
- (c) 閉鎖済み generation について、明示的な継続裁定がない状態では generation-2 を作らないテストを置く。現行の `test_cap_rollover_creates_second_v1_generation` は、逆に防壁緩和を期待値として固定している。
- (d) 重大度: **blocker**
- 直さない場合: bounded pilot が無期限の常時計装へ黙って変わり、cap と最終レビューが無意味になる。

### 5. 新しい series 全体には fail-closed reader が存在しない

- (a) 該当: [s2-plan.md:109-114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:109)、[s2-plan.md:194-198](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:194)、[README.md:64-73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:64)、[decisions.md:2521-2523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/docs/decisions.md:2521)
- (b) writer の正本は series になるのに、validate/report は利用者が選んだ個別 generation しか読まない。古い generation の破損、unknown entry、symlink を writer が検出しても、wrapper は fail-open で無言停止し、series 全体を赤にする consumer がない。健全な1世代だけを選択して report できる。
- (c) 有効 generation、破損 generation、unknown/symlink entry を混在させ、series の公開検査入口が必ず非0になるテスト。さらに damaged+cap、damaged+expired、壊れた final marker の組合せでも rollover せず赤にする。
- (d) 重大度: **blocker**
- 直さない場合: 破損や選択的欠落が「記録なし」として沈黙し、読む側 fail-closed を系列単位では満たせない。

## Must-fix

### 6. direct pytest 子だけ再帰記録の抑止対象から漏れている

- (a) 該当: [run_tests.py:845-878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:845)、[s2-plan.md:148-153](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:148)、[s2-plan.md:231-236](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:231)
- (b) plan は dispatch/scope 子の環境へ `AUTO_RECORD=0` を入れるが、direct path の pytest 子へ渡す `child_env` について同じ所有 marker を要求していない。pytest 内のテストや hook が `tools/run_tests.py` を起動すると、unset marker を継承して別 synthetic run を作る。
- (c) direct pytest 子が一度だけ nested `run_tests` を起動する probe を使い、外部系列の run が1件だけであること、direct child env に所有 marker があることを確認する。
- (d) 重大度: **must-fix**
- 直さない場合: 1回の受入全走から多数の run が生まれ、cap/rollover・lock contention・集計値が壊れる。

### 7. series lock は例外にならず pytest を無期限に止め得る

- (a) 該当: [ledger.py:43-44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/task_runs/ledger.py:43)、[s2-plan.md:73-76](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:73)、[s2-plan.md:109](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:109)、[s2-plan.md:223](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:223)
- (b) lock の timeout/nonblocking 契約がない。`Exception` 捕捉は blocking `flock` には効かず、linked worktree 共有により競合は通常状態になる。また「10件目と11件目」のテストは、lock を削っても自然に直列化すれば正常終了し、変異が緑のままになり得る。
- (c) 別 process が lock を保持した状態で、規定時間内に記録を諦め pytest を起動するテスト。lock 削除を確実に殺すテストは barrier で両 worker の discovery 進入を固定する。
- (d) 重大度: **must-fix**
- 直さない場合: 観測層の競合だけで pytest 自体が始まらず、fail-open にならない。

### 8. `repo_root` は base commit の間接的な caller 指定になる

- (a) 該当: [s2-plan.md:35-50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:35)、[s2-plan.md:78-89](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:78)、[s2-plan.md:217](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:217)、[decisions.md:2524-2527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/docs/decisions.md:2524)
- (b) public `start_run(..., repo_root=...)` の caller は任意 repo B を選んで、その HEAD を repo A 用 generation へ `"git-observed"` と記録できる。commit値を直接渡さないだけで、値の選択権は caller に戻る。schema に repo identity がないため後から対応関係も検証できない。
- (c) repo A/Bを作り、A namespaceへBの `repo_root` を渡した場合を拒否するテスト。提案済みテストは「supplied repo の HEAD を採用する」ことしか見ず、この変異を正当化してしまう。
- (d) 重大度: **must-fix**
- 直さない場合: `base_commit_source=git-observed` が実質的な自己申告になり、台帳の出所が偽装可能になる。

### 9. privacy テスト自身が plan 内の file-path 保存を見逃す

- (a) 該当: [s2-plan.md:78-84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:78)、[s2-plan.md:200-201](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:200)、[s2-plan.md:239-260](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:239)、[schema.py:436-449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/task_runs/schema.py:436)
- (b) synthetic task の objective に文字列 `tools/run_tests.py`、すなわち repo file path を保存する設計になっている。後段の禁止は argv/selector/node ID に限定される。また `suite_id` は `_slug` 検査だけなので、safe-slug 形のテスト名を意味的には拒否しない。
- (c) schema-valid な秘密 sentinel 名と path を入力し、`task.json`、`events.jsonl`、sidecar、生成 path、stdout/stderr の全 bytes に sentinel/path が無く、digest だけがあることを確認する。追加 field の exact-key 赤だけに依存しない。
- (d) 重大度: **must-fix**
- 直さない場合: node IDを直接保存しなくても、test名やfile pathが objective/suite_id/logへ漏れ、privacy 不変条件が破れる。

### 10. 親 brief の実測から P1/P2 への一般化が成立していない

- (a) 該当: [brief.md:21-39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/brief.md:21)、[README.md:70-75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:70)、[README.md:101-116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:101)
- (b) brief は11 run directory・10 run のデータを挙げた直後に「現在ゼロ」「台帳が空」と呼ぶ。さらに `unclassified_rate=1` と `trigger=unspecified` は stage/wait・trigger の欠測を示すだけで、`IZANAGI_TASK_RUN_ID` のない `run_tests.py` invocation の総数を測っていない。README 自身も「書けなかった event は台帳内から検出不能」とするため、この台帳だけから「手番を要する面は機能しなかった」と一般化できない。pilot/report 実物は指定範囲外なので数値自体は未確認。
- (c) 「age/countで新規 start が閉鎖」「final markerで凍結」「期間内の新規 event 数」「全 wrapper invocation に対する記録率」を別々に測る親側検査を置き、分母のないゼロ主張を拒否する。
- (d) 重大度: **must-fix**
- 直さない場合: P1/P2 と default-on 化が、観測できない母集団をゼロとみなす非 sequitur に依存する。

### 11. SIGINT/SystemExit の契約が brief とD66で衝突している

- (a) 該当: [brief.md:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/brief.md:51)、[decisions.md:2521-2523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/docs/decisions.md:2521)、[s2-plan.md:140-151](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:140)、[run_tests.py:820-842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:820)
- (b) brief は「記録失敗が child rc を置換しない」と無条件に書く一方、D66 と plan は `KeyboardInterrupt/SystemExit` の再送出を要求する。child rc を得た後の event/finish 中に SIGINT が来れば、rc は interrupt に置換される。逆に広く飲めば D66 違反になる。
- (c) bootstrap前、child実行中、child rc取得後のrecord、finishの4時点で `KeyboardInterrupt/SystemExit` を注入し、D66どおりの期待を固定する。brief は通常の `Exception` と operator signal を区別する。
- (d) 重大度: **must-fix**
- 直さない場合: 実装者が signal を飲むか rc を保つかを一意に判断できず、どちらの変異もレビューを通り得る。

## 裁定へ返す候補

### 12. repo外化は、D66が依存した git anchor を失う

- (a) 該当: [README.md:21-22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:21)、[README.md:68-71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:68)、[s2-plan.md:194-206](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:194)
- (b) D66 は hash chain を持たない代わりに、tracked files の git 履歴を外部 anchor としていた。XDG/HOME 配下へ移すと、schema-valid な event の事後書換えは validateを通り、gitにも差分が残らない。これは clean-tree 回避以上の integrity threat-model 変更である。
- (c) 実証案: valid event の duration等をschema-validな別値へ書き換え、validateが通り、gitでも検出不能であることを示す。
- (d) 重大度: **裁定候補**
- 直さない場合: 観測 report が改変済みデータを正常として受理し得る。対処は本waveの範囲を広げるため、実装案を既成事実化せずユーザー裁定へ返すべきである。

## 総括

- **判定: NO-GO**
- 最大の穴は、default-on 化が `pytest_stats.py` の未捕捉 I/O 例外を全 pytest へ拡大し、記録障害で test rc を変え得ること。
- 4 gate の凍結範囲が関数本体だけで、依存定数・caller・`PYTEST_ADDOPTS` を固定していない。
- 自動 rollover は現行 pilot の停止・最終 report・ユーザー裁定を迂回するため、明示裁定なしでは実装不可。
- series 全体の fail-closed validatorと、証拠 namespaceへの無副作用拒否が必要。
- 指定外だった `ledger.py:527-563`、`run_tests.py:905-912/948-995/1721-1849`、pilot/report実物、既存テスト本文は未確認。範囲は広げていない。
- pytest・mutation・受入全走は未実施であり、緑の主張はない。