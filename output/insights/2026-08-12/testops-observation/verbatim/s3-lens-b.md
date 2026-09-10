必読の brief／段 2 プランは読了しました。pytest は未実施で、以下は静的レビューのみです。`run_tests.py:1721-1849` と `ledger.py:61-819` は指定範囲外のため、詳細は未確認です。

## blocker

### B1. cap 判定が並行 wave で破れる

- 該当 path: [s2-plan.md:23-29,73-90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:23)、[output/task-runs/README.md:94-98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:94)
- 筋: `start_run()` は `published` 数で cap を判定する案だが、自動 run は start 後、test event と `task_end` を書く。10 件が実行中の間に別 wave が同時 start すると、series lock は順序しか直さず、全プロセスが未完 run を cap に数えず同じ generation に作成できる。
- 壊れ方: 第1世代に10件を超える run が入り、cap／rollover／report の世代境界が崩れる。
- 検出案: start 後に finish を遅延させる barrier 付きで20プロセスを投入し、generation ごとの task directory 数と `validate_root` の cap 判定を照合する。
- 重大度: **blocker**

### B2. rollover が crash で永久停止する

- 該当 path: [s2-plan.md:86-114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:86)
- 筋: `create_next_generation()` と `init_pilot()` が別操作である。mkdir 後、pilot 初期化前にプロセスが落ちると、次回は最新世代を damaged と見て fail-open し、前世代へ戻らず新世代も作らない。
- 壊れ方: 一度の中断後、以後すべての自動記録が無言で欠測になる。
- 検出案: mkdir と `init_pilot` の間で強制終了し、次回起動が recovery するか、恒久的に記録不能になるかを確認する。
- 重大度: **blocker**

### B3. dispatch／bounded scope は「走った」だけで payload が欠ける

- 該当 path: [run_tests.py:820-840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:820)、[run_tests.py:948-997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:948)、[run_tests.py:1484-1534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:1484)、[s2-plan.md:150-154](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:150)
- 筋: direct 経路は sidecar から counts/digest を読むが、dispatch と bounded scope は `sidecar=None` のまま記録する。lazy session を共有しても child の test statistics は親へ戻らない。
- 壊れ方: 3経路すべてに event は存在しても、dispatch／scope の collected/passed/failed/skipped/digest が欠測となり、経路間の比較ができない。
- 検出案: 同一 fake suite を direct／fake dispatch／bounded scope で走らせ、生成された event の payload を完全比較する。
- 重大度: **blocker**

### B4. bounded scope の OOM／timeout が未記録になる

- 該当 path: [run_tests.py:1508-1510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:1508)
- 筋: `CHILD_RC` 以外は記録処理へ進まず return する。fallback dispatch が起きない scope failure では、実際に pytest child を起動した invocation に task-run が残らない。
- 壊れ方: 資源制限で落ちた重要な実行ほど台帳から消え、「遅い／重い／OOM になった」事実を検出できない。
- 検出案: CAP_OOM、timeout、scope setup failure を個別に返す fake runner で、各 invocation に event が残るか確認する。
- 重大度: **blocker**

### B5. 親の実測値から P2 を一般化できていない

- 該当 path: [brief.md:19-27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/brief.md:19)、[run_tests.py:845-857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:845)、[run_tests.py:1641-1649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:1641)
- 筋: 8/10 の有効値は pilot 中に自動配線された既存 test_run の実績であり、IDなしの新経路、login direct、dispatch、bounded、compute direct、mutation local の層別実測ではない。9/10 の `unclassified_rate=1` は親の stage/CLI event 欠落で、`run_tests.py` の test event 自動化だけでは直らない。
- 壊れ方: 「手番が原因」と誤認したまま実装し、ID不要にした後も別の層で記録されない。
- 検出案: IDなしで、direct／force-dispatch／bounded／compute／mutation-local を各々複数回走らせ、入口別の分母・記録率・payload 欠測率を測る。
- 重大度: **blocker**

## must-fix

### M1. fail-open が完全に無言で、無手番化の失敗を検出できない

- 該当 path: [s2-plan.md:63-112,142-145](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:63)、[s2-plan.md:231-240](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:231)、[output/task-runs/README.md:64-73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:64)
- 筋: XDG/HOME が相対・repo 内・書込不能、git common-dir 解決失敗、filesystem 初期化失敗、実装バグのすべてを `Exception` 捕捉して通常実行へ倒す。しかも提案テストは stderr/stdout の警告も拒否する。
- 壊れ方: 全実行が旧来の「記録なし」と同じ状態になっても、ユーザーも agent も記録停止を知れない。
- 検出案: env／権限／git／import／lock を故障注入し、child rc を保ったまま out-of-band の欠測診断が残るか確認する。
- 重大度: **must-fix**

### M2. manual CLI が series lock を迂回する

- 該当 path: [cli.py:40-62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/task_runs/cli.py:40)、[cli.py:197-218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/task_runs/cli.py:197)、[s2-plan.md:176-180](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:176)
- 筋: help を変更するだけで、`--root generation-NNNNNN` に対する `start`／`event`／`finish`／`init-pilot` の書込みは禁止されない。auto manager と CLI が同じ generation を同時に更新できる。
- 壊れ方: CLI の start が cap を消費せず、または final marker 後の世代へ追記し、auto rollover と台帳状態が食い違う。
- 検出案: auto start と外部 generation への CLI start/event を同時実行し、cap・final marker・validate 結果を照合する。
- 重大度: **must-fix**

### M3. `trigger` の無手番化が残っていない

- 該当 path: [run_tests.py:852-855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:852)、[run_tests.py:963-968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:963)、[run_tests.py:1497-1502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:1497)、[s2-plan.md:154](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:154)
- 筋: `IZANAGI_TEST_TRIGGER` 未設定時は全経路で `unspecified`。IDだけを自動化しても trigger の分類には環境設定という手番が残る。
- 壊れ方: 新しく蓄積される test_run も既存 report の `unspecified` 問題を再生し、cohort 分けができない。
- 検出案: すべての task-run 関連 env を unset にした direct／dispatch／scope 実行で trigger 値を確認する。
- 重大度: **must-fix**

### M4. default root の filesystem 契約がない

- 該当 path: [s2-plan.md:63-110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:63)、[output/task-runs/README.md:78-81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:78)、[pegasus-runbook.md:357-363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/docs/pegasus-runbook.md:357)
- 筋: XDG/HOME の実体が tmpfs、NFS、Lustre のどれかを確認せず `flock`／O_APPEND／fsync を前提にする。existing `selfcheck` は自動 manager の起動手順にない。
- 壊れ方: 並行 wave の同時追記が本当に直列化されず、events.jsonl 破損または generation 衝突が起きる。
- 検出案: 実際の default root で selfcheck と複数プロセス同時 append を行い、kill 中断後も validate が通るか測る。
- 重大度: **must-fix**

### M5. 150行制約と要求された安全面が両立していない

- 該当 path: [brief.md:43-44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/brief.md:43)、[s2-plan.md:10,56-154](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:10)
- 筋: 約75行で base 解決、git namespace、symlink／regular-file 検査、exclusive lock、世代探索、atomic rollover、fail-open、破損区別まで実装し、さらに約55行で3経路の session／finish／fallback を配線する案になっている。
- 壊れ方: 行数目標を守るため、lock・crash recovery・診断・経路別結果処理のいずれかが実装から抜ける。
- 検出案: production diff の行数だけでなく、要件ごとの実装行・テスト対応表を作り、各 failure injection が実コード上の分岐に対応するか確認する。
- 重大度: **must-fix**

## 裁定候補（scope 外だが real）

### R1. 素の pytest と mutation local は対象外

- 該当 path: [mutation_harness.py:450-464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/mutation_harness.py:450)、[pegasus-runbook.md:887-902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/docs/pegasus-runbook.md:887)、[pegasus-runbook.md:597-601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/docs/pegasus-runbook.md:597)
- 筋: `python -m pytest` は mutation harness の local mode で正規に許されるが、`run_tests.py` の session を通らない。通常のユーザー／Codex／IDE／cron の direct pytest も wrapper 外である。
- 壊れ方: report は「自動 test_run が蓄積された」と見えても、mutation local と direct pytest の走行は台帳に存在しない。
- 検出案: 同一 mutation を local mode と `tools/run_tests.py --force-dispatch` で実行し、記録率を比較する。
- 重大度: **裁定候補**

### R2. 記録 field だけでは実行時間 regression を信頼して検出できない

- 該当 path: [run_tests.py:488-502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:488)、[run_tests.py:970-997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:970)、[run_tests.py:1508-1530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:1508)、[pegasus-runbook.md:607-610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/docs/pegasus-runbook.md:607)
- 筋: `suite_id` は target 集合中心で `-n`／`--dist` を区別せず、direct は pytest wall time、dispatch は queue 待ち込み、scope は scope overhead 込みになる。site、route、interpreter、dirty-tree、memory cap も event にない。
- 壊れ方: node／queue／並列度の差をコード回帰と誤認する。
- 検出案: 同一 suite を local、dispatch、scope、異なる `-n` で測り、現行 field だけで cohort が分離できるか確認する。
- 重大度: **裁定候補**（P1で分析を後段に送るなら本 wave の実装外。ただし「比較可能」を成果として書くのは不可）

### R3. cross-clone 共有と世代横断利用が実現していない

- 該当 path: [s2-plan.md:69-110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:69)、[s2-plan.md:112-114,194-198](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:112)
- 筋: namespace は常に `git-common-dir` digest の下に作られるため、同じ `IZANAGI_TASK_RUNS_BASE` を設定しても別 clone は別系列になる。さらに generation 単位の reader しかなく、旧 tracked pilot と新 external series を連続 cohort として読めない。
- 壊れ方: clone／ジョブごとに台帳が分裂し、generation rollover 後の連続比較には人が path を探して手で束ねる必要がある。
- 検出案: 同一 base 下の linked worktree、別 clone、再作成した clone path でそれぞれ1 runを作り、namespace と report の可視範囲を比較する。
- 重大度: **裁定候補**

### R4. 自動世代に retention／発見手段がない

- 該当 path: [s2-plan.md:112-114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:112)、[output/task-runs/README.md:68-81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:68)
- 筋: 1 invocation 1 directoryで世代だけが無期限に増え、自動 report、世代横断 index、quota／retention policy がない。
- 壊れ方: 長期運用で external root が容量枯渇し、その後は fail-open により全記録が消える。
- 検出案: wave 相当の run 数を長時間相当まで増やし、容量、generation 数、report の発見性を測る。
- 重大度: **裁定候補**

## 実行経路の被覆表

| 層 | プラン上の扱い | 実効性の判定 |
|---|---|---|
| login node direct、`run_tests.py` | lazy session を `_call_and_record` に通す | **条件付き被覆**。root／bootstrap failure は無言欠測 |
| login node → compute dispatch | 親だけ記録、child は `AUTO_RECORD=0` | **event は被覆**。counts/digest 欠測、dispatch失敗も test_run 風に残る |
| compute node 上の `run_tests.py` direct | env marker がなければ auto session | **未実証の条件付き**。HOME/XDG、clone、FS共有性に依存 |
| bounded scope | 同一 session を scope／fallback で再利用 | **部分被覆**。CAP_OOM／timeout と sidecar 欠測が残る |
| 素の `python3 -m pytest` | 変更対象外 | **未被覆** |
| mutation harness の dispatch mode | runbookどおり `run_tests.py --force-dispatch` なら親 event | **条件付き被覆**。local mode の `python -m pytest` は未被覆 |
| 並行 linked worktree | common-dir digest で同一系列、既存 ledger lock を利用 | **部分被覆**。cap race、CLI迂回、FS契約、世代横断が未解決 |
| 別 clone／別 job | digest が異なれば別系列 | **共有されない**。P3の「明示 base で共有」と実装が一致していない |

## nit

- 該当 path: [s2-plan.md:201-202](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-testops-observation/out/s2-plan.md:201)、[output/task-runs/README.md:80-81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:80)
- 新しい start/event/end/fsync overhead を親が測るとはあるが、どの分母・経路・許容幅で報告するかが未定義。
- 壊れ方: overhead の下限値を route 間で誤比較する。
- 検出案: direct／dispatch／scope別に wrapper duration と recording duration を分離して測る。
- 重大度: **nit**

## 総括

- **結論: NO-GO。**
- 最大の穴は、「event が1件できる」ことを「全層で実効的な観測ができる」ことと扱っている点です。
- 段4で最低限、B1〜B5を real として再裁定し、R1〜R4を scope外の裁定候補として明示する必要があります。
- 狭い生死確認だけに縮めるなら、まず direct の IDなし1走、child rc保持、1 event、外部 root の実FS selfcheckに限定し、世代横断・mutation local・raw pytest・cross-clone共有を成功条件から外すべきです。
- 本レビューでは編集・pytest実走はしていません。