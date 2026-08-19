判定は **NO-GO**。`generation.py` は現行 repo に存在せず、plan の `generation.py:new:*` は未検証の設計主張です。現行実装では brief の B4 (`run_tests.py:1549`) と TOCTOU 指摘は再現確認できます。

## blocker

### B1 — namespace 検査と create/open の TOCTOU が閉じていない

(a) 該当: `tools/task_runs/ledger.py:144-184,159-172,296-340,359-379`、brief `:20-34,38-46,101-109`、plan `:175-203,741-746`

(b) `_assert_safe_root()` は resolve 後に元の未解決 path を返し、`_ensure_root()` は path-based `mkdir()` と `lstat()` を別々に行います。`_open_directory()` の `O_NOFOLLOW` は最終 component にしか効かず、祖先の symlink 差し替えを防ぎません。plan の「検査済み parent fd」は、祖先 component の開き方、相対 `git-common-dir` の束縛、staging/lock/pilot の全操作を同一 fd chain で行う具体性が不足しています。

(c) 検出案・テスト案: repo 親、series base、generation parent を検査後・各 `openat/mkdirat/renameat` 前に symlink/non-directory へ差し替え、`pilot.json`、lock、staging、generation の全てが 1 byte も作られないことを確認する。`git-common-dir` が相対値の場合の解決基準も固定する。

(d) 重大度: blocker

### B2 — damaged/incomplete と pilot closed の優先順位が未分離

(a) 該当: `tools/task_runs/ledger.py:405-417,527-557`、`orchestrator/tests/test_task_run_ledger.py:821-852`、plan `:204-265,693-725`

(b) `pilot-final.json` は内容を検証せず root discovery から無条件に除外されます。final marker と damaged entry が同居すると、`start_run()` は damaged 検査より先に final として閉じます。さらに task marker 前の interrupted run は `incomplete` になりますが、現行 cap 判定 (`:551-554`) は `incomplete` を拒否も消費もしていません。`validate_series()` を start 前に必ず呼ぶ順序が plan に固定されていません。

(c) 検出案・テスト案: 壊れた/ symlink の final marker、final marker と damaged/unknown/incomplete の同居、task marker 前の crash 後の再 start を検査する。いずれも `pilot-closed:*` ではなく `series-invalid` となり、新規 generation/task marker を作らないことを確認する。

(d) 重大度: blocker

### B3 — explicit next generation が「明示裁定」ではなく呼出し規約に留まる

(a) 該当: D341 `:15122-15125,15149-15155`、plan `:204-232,595-618`、`tools/task_runs/__init__.py:3-13`

(b) `open_next_generation(repo_root)` に裁定 token、manual-only capability、approval record がありません。「automatic caller から到達不能」は Python の import/call graph 上の慣行であり、強制境界ではありません。CLI を拒否しても、public な `init_pilot()`/`start_run()` を直接呼べば managed generation と series lock を迂回できます。

(c) 検出案・テスト案: automatic API から explicit API への静的 call graph 検査だけでなく、opaque approval capability がない呼出しを runtime に拒否する設計を要求する。managed generation へ直接 `start_run/init_pilot` した場合も拒否する。

(d) 重大度: blocker

### B4 — series fail-closed reader が既存 consumer に束縛されていない

(a) 該当: plan `:234-265`、`tools/task_runs/aggregate.py:781-830`、`tools/task_runs/cli.py:217-238`、`tools/task_runs/ledger.py:519-524`

(b) plan は `validate_series()` を追加する一方、report は個別 generation のままとし、CLI の個別 `validate --all` も許可しています。`publish_report()` は渡された一つの root だけを読むため、健全な generation を直接指定すれば、別 generation の damaged/unknown を含む series を報告できます。既存 `discover_runs()` も damaged run を返します。

(c) 検出案・テスト案: generation-1 を健全、generation-2 を damaged にして、`validate-series`、individual validate、report、各 public reader を全て実行する。series validity を返す全入口は拒否し、generation-local report は明確に series validity を主張しないことを確認する。

(d) 重大度: blocker

### B5 — signal が dispatch/admission 経路で既に吸収される

(a) 該当: `tools/run_tests.py:953-970,1044-1077,1099-1145`、`tools/pegasus/dispatch_compute.py:2002-2007,2145-2177`、plan `:540-566,770-784`

(b) `_record_task_run()` 自体は `Exception` のみを捕捉しますが、実際の recording route の周辺には `KeyboardInterrupt` を捕捉する箇所があります。特に `_invoke_dispatch()` は KBI を rc=16 に変換し、その後 `_dispatch_and_record()` が通常の test event を記録できます。`dispatch_compute.py` は `BaseException` を捕捉するため `SystemExit` も receipt/infra rc に畳みます。plan の「dispatcher 固有契約と writer 契約を混同しない」だけでは task_end を誤追加しない保証になりません。

(c) 検出案・テスト案: bootstrap、admission、bounded scope、dispatch、sidecar read、append、finish、cleanup の各点で KBI/SystemExit を注入し、再送出、child rc 保持、task_end 未追加、sidecar cleanup 完了を確認する。dispatch の signal-abort は親が signal として認識できる型付き結果にする。

(d) 重大度: blocker

### B6 — 4 gate 凍結と recording session の配置が現行 route と衝突する

(a) 該当: `tools/run_tests.py:1717-1830,1832-1840,1856-1862,1913-1916`、brief `:20-29,118-124`、plan `:148-173,759-761`

(b) 現行 Pegasus login の local bounded scope は preflight (`:1832-1840`) より前に `_launch_local_scope()` (`:1804`) を起動します。plan は session 初期化を preflight 後としています。そこへ置くと local scope が自動記録を bypass し、前へ移すと preflight/caller order と受理集合を変更します。gate 本体を無差分にしても、caller order の変更で 1 bit の差が出ます。

(c) 検出案・テスト案: direct、login-local、login-dispatch、compute、suspect、bounded fallback の全 route について、session 前後の 4 gate 値、`PYTEST_ADDOPTS`、argv、preflight 結果、child 起動有無を truth table 化する。特に login-local の preflight 前後を固定する。

(d) 重大度: blocker

### B7 — `repo_root` は base commit ではなく caller の自己申告になる

(a) 該当: brief `:27-34,38-46`、plan `:458-485`、現行 `tools/task_runs/ledger.py:326-347,527-575`

(b) 直接の commit 文字列入力は除去されていますが、public API の `repo_root` 自体が caller 指定です。`root.parent` がその repo から導いた sibling base と一致する検査だけでは、repo B と repo B の正しい sibling を渡す caller を拒否できません。生成物には repo identity binding がなく、`base_commit_source: "git-observed"` も writer が自己設定する値です。Q2 の改竄検出非主張とは別に、A8 の caller-binding は未解決です。

(c) 検出案・テスト案: repo A/B と各 sibling を用意し、public automatic API に B を渡した場合を検査する。automatic API は内部で確定した repo fd/capability 以外を受け付けず、base commit はその identity からのみ得られることを確認する。

(d) 重大度: blocker

## must-fix

### M1 — Unit A の sidecar lease と Unit B の dispatch transport が未定義

(a) 該当: plan `:31-55,320-351`、`tools/run_tests.py:825-833,930-937,1396-1407,1678-1689`、`tools/pegasus/dispatch_compute.py:76-90,577-579,643-669`

(b) `AutomaticRun` には sidecar lease/capability がなく、B は path 文字列だけを transport する設計です。現行では bounded/dispatch が sidecar を削除し、job script と `_job_run()` も削除します。追加後も request JSON に sidecar の絶対 path が入り得ます。plan 自身も compute node から sibling transport が見えることを未確認としています (`s2-plan-v2.md:858-860`)。

(c) 検出案・テスト案: parent→request.json→job script→`_job_run()`→child→parent read の実経路で、manual ID/root は除去、sidecar/auto-off のみ transport、lease の symlink 差し替え・期限切れ・二重 read・child crash を検査する。compute node の filesystem visibility は実環境契約として別途確認する。

(d) 重大度: must-fix

### M2 — B4 の同一 session / 一度だけ finish が API に落ちていない

(a) 該当: `tools/run_tests.py:1521-1574,1804-1830`、plan `:353-381,728-734`

(b) 現行は `CHILD_RC` 以外を `:1549` で即 return し、scope event を記録しません。plan は fallback で同じ session を再利用するとしますが、public contract の `AutomaticRun` は generation/id/name だけで、scope result・lease・finish state を持ちません。`_dispatch_result()` も session を受けません。

(c) 検出案・テスト案: CHILD_RC、CAP_OOM、timeout、attestation failure、dispatch infra の全組合せで、同一 task-run に scope event、compute event、task_end が順序通り一度ずつ記録されることを確認する。

(d) 重大度: must-fix

### M3 — objective の blocklist と schema の同期だけでは privacy を保証しない

(a) 該当: `tools/task_runs/schema.py:161-183,216-220,266-306,436-449`、`schema_v1.json:61-86,141-149`、plan `:487-515`

(b) `/`、`\`、`::`、改行の拒否でも `test_file.py`、`test_secret` のような file/node 由来文字列は通ります。さらに `SAFE_SLUG_RE` は広く、CLI の `--suite-id` から任意の safe slug を直接書けます。Python validator と JSON schema は別実装で、`load_schema()` は Draft 7 の構文検査しかせず意味同期を検査しません。

(c) 検出案・テスト案: Python validator、JSON Schema、CLI、直接 ledger の全入口に path/node sentinel を通す。schema の片側だけ rule を変更する変異を、両 validator の negative test で殺す。automatic 以外の自由文 objective/suite_id を許すかも明示する。

(d) 重大度: must-fix

### M4 — 固定 diagnostic 以外の stderr/receipt/log に漏洩経路が残る

(a) 該当: `tools/task_runs/cli.py:240-249`、`tools/run_tests.py:963-969,1031-1039,1409-1415,1443-1447`、`tools/pegasus/dispatch_compute.py:1538-1562,2002-2069,2163-2177`、plan `:114-142,568-593`

(b) plan の固定一行 diagnostic は `_record_task_run()` 周辺だけを覆います。現行 CLI は raw exception、run_tests は dispatcher exception、dispatch receipt/request は repo path と raw argv を保存します。child stdout/stderr を保持する契約も、child 出力まで「path 不在」と読むなら両立しません。

(c) 検出案・テスト案: sentinel argv、selector、node ID、repo path、sidecar path を各例外・dispatch request/receipt・stderr に通し、wrapper-owned artifact と child-owned output の境界を明示して検査する。raw exception text を固定 diagnostic code へ射影する。

(d) 重大度: must-fix

### M5 — P3 と M3 の trigger 契約が矛盾している

(a) 該当: plan `:69-78,620-642`、`tools/run_tests.py:877-879,991-993,1537-1539`、`tools/pegasus/dispatch_compute.py:79-83`

(b) P3 は許可済み `IZANAGI_TEST_TRIGGER` を従来どおり使う一方、M3 は automatic trigger を明示的に `unspecified` としています。現行 route は `final` 等をそのまま読みます。automatic parent が valid な環境値を継承すると、ユーザーが自動観測を `final` と分類できます。

(c) 検出案・テスト案: valid/invalid/unset の全 trigger を direct/dispatch/bounded/fallback で検査し、automatic task event は常に `unspecified`、child の auto-off と親 event の trigger を別管理する。

(d) 重大度: must-fix

### M6 — series lock timeout だけでは既存 root flock の無期限 block を防げない

(a) 該当: `tools/task_runs/ledger.py:359-379,527-601,669-680`、plan `:435-456`

(b) `init_pilot()` の root flock (`:365`) と `start_run()` の root flock (`:541`) は blocking です。series lock が timeout しても、その後の root lock で無期限停止できます。`_acquire_flock()` の timeout は events fd 用で、これらを覆いません。

(c) 検出案・テスト案: series lock を取得した状態で root lock を別 process が保持し、automatic start が bounded diagnostic を返して pytest を続行することを確認する。

(d) 重大度: must-fix

### M7 — staging recovery と transport entry の許可集合が粗い

(a) 該当: plan `:248-260,293-318,693-705`、現行 `tools/task_runs/ledger.py:394-417`

(b) 「valid pilot の staging は rename」では、pilot は正しいが staging 内に unknown/damaged task を混ぜた場合の判定がありません。series base は `transport/` 全体を許可しますが、lease、stale sidecar、corrupt temporary file の状態機械がありません。`pilot-final.json` の内容検査も現行 reader にはありません。

(c) 検出案・テスト案: pilot 正常＋unknown、pilot 正常＋partial task、stale lease、corrupt sidecar、transport symlink、正式 generation と staging の番号衝突を各々 fail-closed にする。valid staging は厳密に空の generation としてのみ recovery する。

(d) 重大度: must-fix

### M8 — P1 ownership と見積りが安全な interface 量を過小評価している

(a) 該当: brief `:49-74`、plan `:31-55,815-839`

(b) brief の Unit B は run_tests 側だけでしたが、plan は `dispatch_compute.py` を追加しました。実際には Unit A が leaseを作り、Unit B が scheduler request/job/childを運び、再び Unit B が parent で読むため、単純な素集合ではありません。production 見積りも brief の 320–505 行に対し plan は 455–663 行です。

(c) 検出案・テスト案: Unit A/B 間の typed interface、所有者、cleanup authority、failure code、cross-node visibility を文書化し、dispatch 3段（request/job-run/child）を含む一つの integration contract test で固定する。行数を理由に fd/signal/privacy 面を削らない。

(d) 重大度: must-fix

## 裁定へ返す候補

1. **Q1 の「明示」の実体** — `open_next_generation()` の明示呼出しで足りるのか、ユーザー裁定を表す opaque token/manual command が必要か。推奨は後者です。

2. **P3 trigger の優先契約** — brief/plan M3 に合わせ、automatic は常に `unspecified` とするのか、既存環境値を許すのか。推奨は `unspecified` 固定です。

3. **Q2 と dispatch transport の境界** — compute node が repo sibling を共有 filesystem として見られない場合、dispatch の counts/digest 欠測を許容するのか、transport 方式を再設計するのか。request/receipt の raw argv・repo path を privacy 対象に含めるかも同時に確定が必要です。

## 総括

**NO-GO。blocker 7件、must-fix 8件、pytest未実施（sandbox=read-only）。**