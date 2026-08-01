結論から言うと、現 plan はそのまま段5へ渡せません。特に、元 worktree 実行への逃げ、危険な no-execution 判定、policy import 不成立、qsub 後の復旧不能が blocking です。

指定された brief / plan は両方全文読了しました。以下は read-only の静的検査結果であり、編集・pytest・build・qsub は実行していません。緑は主張しません。

分類は `real`＝現 scope 内の欠陥、`scope外real`＝脅威は実在するが現 scope では閉じられないもの、`refuted`＝証拠上成立しない指摘、です。

## 1. site 分類・FQDN・PBS・qlogin・affinity

### 所見 1-A — `real / Critical`：三値分類の `OTHER` が fail-open になる

[brief.md:35](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/brief.md:35) と [plan.md:38](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:38) は Pegasus に合致しない hostname を、NQSV PBS ID があっても `OTHER` に落とします。

- 攻撃入力: `hostname=bnode1000`, `PBS_JOBID=0:874129.nqsv`, affinity 48。
- 誤結果: 将来 node 名は `OTHER` となり、テスト・ビルドをその場で実行できます。
- 攻撃入力: `PEGASUS01.CCS.TSUKUBA.AC.JP.`。DNS identity としては同じでも、case-sensitive・末尾 dot 未正規化なら `OTHER` です。
- 攻撃入力: actual login を UTS namespace / 注入 observation で `ci-host` と見せ、PBS env を消す。
- 誤結果: hostname/PBS/affinity は hostile な security identity ではなく、repo-level policy を迂回できます。

成果物影響: login load 拒否 receipt が作られず、`OTHER` のローカル task-run/build provenance が正規結果として残ります。

最小修正:

- raw hostname と、ASCII lowercase＋末尾 dot 一個だけを除いた canonical hostname を別 field にする。
- `NQSV ID + unknown hostname`、`*.ccs.tsukuba.ac.jp` の未知 host、`bnode` 風未知名を `OTHER` にせず `PEGASUS_AMBIGUOUS` または `SitePolicyError` にする。
- 保証文を「正直な OS observation に対する運用 gate」に限定し、security boundary と呼ばない。
- future node は policy data 更新まで停止する設計にする。

### 所見 1-B — `real / High`：qlogin と affinity 契約が未実測で矛盾する

[plan.md:39](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:39) は compute に PBS ID を必須とする一方、[plan.md:104](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:104) は markerless qlogin を compute 実行可とします。しかし runbook が実測しているのは qlogin 後の `bnodeXXX` prompt だけで、`PBS_JOBID` の有無・形式は記録していません。[pegasus-runbook.md:52](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/pegasus-runbook.md:52)

- 攻撃入力: qlogin 上で `hostname=bnode114`, `PBS_JOBID` 未設定。
- 誤結果: 正規 compute allocation を `SitePolicyError` で拒否する可能性があります。
- 攻撃入力: compute で `taskset` 等により affinity が4件。
- 結果: 安全側に停止しますが、allocation 自体は正規でも過大拒否です。
- 攻撃入力: `-n 999`。
- 誤結果: [plan.md:53](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:53) により affinity 超過を無条件受理し、負荷 policy を破ります。
- 攻撃入力: `-n0`, `-n auto`, `-n logical`, `IZANAGI_TEST_NPROC=max/all`。
- 誤結果: 「正値だけ」に狭めると、現在の `-n0` serial 判定と `max/all` を壊します。[run_tests.py:123](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:123) [run_tests.py:235](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:235)

成果物影響: `nproc_source` が同じでも意味が異なり、qlogin を誤拒否する一方、明示999 worker を正規 receipt として残せます。

最小修正: qlogin の hostname/PBS/affinity を実測してから分類規則を確定し、affinity 超過は明示 `allow_oversubscribe` 裁定がない限り拒否する。CLI、`PYTEST_ADDOPTS`、環境変数それぞれの `0/auto/logical/max/all/integer` precedence を表にする。

## 2. `campaign/pegasus_policy.py` の import 実効性

### 所見 2-A — `real / Critical`：計画した import graph は実行形ごとに成立しない

[plan.md:24](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:24) と [plan.md:55](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:55) は import 方向だけを規定し、`sys.path` を規定していません。

- `python3 tools/run_tests.py` の初期 `sys.path[0]` は `tools/` です。`campaign.pegasus_policy` も `orchestrator.campaign.pegasus_policy` も、環境汚染なしには安定して読めません。
- hook も `hooks/` から直接実行されます。[settings.json:20](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/.claude/settings.json:20)
- campaign の直接実行形は `<repo>/orchestrator` を挿入し、top-level `campaign` を import します。[s2_verify_calibration.py:45](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s2_verify_calibration.py:45)
- tests は `spec_from_file_location` で runner を直接ロードします。[test_run_tests_nproc.py:18](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_run_tests_nproc.py:18)
- 同一ファイルを `campaign.*` と `orchestrator.campaign.*` で読むと別 module object になります。既存文書にも実害が記録済みです。[orchestrator/tests/README.md:48](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/README.md:48)

攻撃結果: `SiteKind` Enum と `SiteObservation` dataclass が二重定義され、`isinstance`、Enum 比較、monkeypatch が静かに外れるか、起動直後に `ModuleNotFoundError` で停止します。

さらに [run_tests.py:39](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:39) は `packaging` を module import 時に要求します。stdlib-only policy を作っても、login の早期 dispatch / help より前に packaging 不在で停止します。

成果物影響: runner、hook、submitter の全てが同じ site 判定を使うという中心不変条件が成立しません。

最小修正:

- 全 surface が使う canonical fully-qualified import 名を一つ決め、各 script はその import より前に `__file__` 由来の絶対 bootstrap を行う。
- `campaign.*` と `orchestrator.campaign.*` の二重ロードを禁止または明示 alias し、型 object identity まで検査する。
- policy は stdlib-only を維持し、buildcache/runner/`packaging` を import しない。
- `packaging` は xdist 実行 branch まで lazy import する。
- `python -I -B`、`spec_from_file_location`、直接 campaign 実行、hook subprocess の4 import testを必須化する。

## 3. snapshot の exactness

### 所見 3-A — `real / Critical`：pytest target が元 worktree の絶対パスへ固定される

現在の `_normalize_args` は既存 target と path option を呼出し元 cwd 基準の絶対パスにします。[run_tests.py:176](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:176)

- 攻撃入力: `python3 tools/run_tests.py orchestrator/tests/test_hooks.py`
- 誤結果: worker に同じ argv を渡すと `/元repo/orchestrator/tests/test_hooks.py` を実行し、[plan.md:93](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:93) の「共有 worktree は一切実行対象にしない」を破ります。
- 元 tree を qsub 後に変更すれば、manifest と異なる test bytes が実行されます。
- `--rootdir`, `--confcutdir`, `--basetemp`, `--junitxml`, `--log-file` も同じ問題を持ちます。
- pytest 9.1.1 は `@argsfile` を実際に展開します。[argparsing.py:390](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/config/argparsing.py:390)
  `/tmp/args.txt` を投入後に変更すれば、target/plugin/option が manifest 外から注入されます。
- `-p plugin`、`PYTEST_PLUGINS`、entry-point plugin autoload、`--pyargs` も snapshot 外の executable input です。

成果物影響: `snapshot_manifest_sha256` と実際の pytest source/plugin が一致しない偽 provenance になります。

最小修正: dispatch 判定までは raw argv を保持し、repo 内 path は snapshot-relative AST に変換して worker 側で snapshot root へ解決する。外部 target、symlink escape、argsfile、plugin、rootdir は hash-bound staging または拒否。出力 path は dispatch 専用領域へ明示 remapする。

### 所見 3-B — `real / Critical`：staged/unstaged の index 意味論が失われる

[plan.md:87](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:87) は cached patch と unstaged patch を「順番に適用」としか定義していません。

- 攻撃入力: tracked file を `git rm` して staged deletion にする。
- plain `git apply` で cached patch を clone worktree に当てる。
- 誤結果: clone index は file を追跡したまま worktree だけ消えるため、staged deletion が unstaged deletion に変わります。
- その snapshot で acceptance を走らせると、deletion gate が rc13 で停止します。[run_tests.py:454](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:454)
- staged mode change、staged symlink、staged＋unstaged 同居でも同じ index drift が起きます。

成果物影響: source bytes が同じでも Git state と preflight 結果が元 tree と異なります。

最小修正: cached patch は detached HEAD clone に `git apply --index`、unstaged patchはその後に worktree-onlyで適用する。最終的に source と snapshot の `status --porcelain=v2 -z`、cached diff、unstaged diff、mode、deletionを比較する。untracked symlink は `O_NOFOLLOW` readではなく `readlink()` bytesを束縛する。

### 所見 3-C — `real / High`：clone は自己完結・入力閉包になっていない

攻撃面は複数あります。

- `git clone --no-local` でも `origin` は元 worktree を指します。snapshot 内の `git fetch origin` が投入後の bytes を再導入できます。
- system Git config には必須 LFS filter が実在します。[/etc/gitconfig:1](/etc/gitconfig:1) checkout filter、template hook、`core.hooksPath`、global attributes が clone/checkout 時に外部 code を起動し得ます。
- `lstat → open(O_NOFOLLOW)` は symlink 自体を読めず `ELOOP` になります。
- submodule を単なる別 clone にすると、superproject gitlink、nested HEAD/index/worktree、`.git` 管理形、remote/alternates の整合が未定義です。
- ignored input を `output/runs/silo-sample` だけに限定すると、別の `output/runs/*` target、`external/ccbench/build`、`.venv` plugin は欠落します。.gitignore はこれらを包括的に無視しています。[.gitignore:18](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/.gitignore:18)
- source 内の `output/.../test-dispatch` に snapshot を作るため、dirty `.gitignore` が新 ignore rule を消すと untracked scan が snapshot 自身を再帰的に取り込みます。
- 実 Silo fixtureだけでも66MBです。[orchestrator/tests/README.md:144](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/README.md:144) untracked の file/count/total-byte 上限がなく、S1 snapshot が S2 `check_quota` より先なので、quota check 前に共有 home を埋められます。
- snapshotを永久保持するため、正常 wave の反復だけでも quota DoS になります。

成果物影響: snapshot SHA が repo source closure を表さず、外部 filter/plugin/remote や欠落 ignored fixture によって collected/skip集合が変わります。

最小修正:

- global/system config・attributes・hooksを無効化し、checkout後に remote と alternates を除去・検査する。
- snapshot source と receipts/manifest を sibling directory に分け、destination を Git ignore に依存せず hard-excludeする。
- 許可 ignored input を宣言型 manifest にし、それ以外を参照する argvは拒否する。
- file count、per-file/total bytes、free-space、quotaをclone前に検査し、retention/GC裁定を置く。
- nested submoduleにも同じ remote/config/hash規律を適用する。

### 所見 3-D — `scope外real / Critical`：二回 scan だけでは敵対的 concurrent writer に対する瞬間 snapshot は作れない

攻撃入力: writer が clone中に A/B を交互変更し、二回目 scan 前に最初の状態へ戻す ABA race。

誤結果: 最初と最後の manifest は一致しても、copyされた複数 file は同時には存在しなかった組合せになり得ます。「投入時 bytes」という瞬間は定義できません。

成果物影響: adversarial exact snapshot という保証が偽になります。

最小修正: 現 wave では保証を「copyされた manifest bytesを固定し、通常の並行変更を二回 scan で検出」に狭める。真の瞬間 snapshot は、clean committed tree限定、writer全員が従うrepo lock、または filesystem snapshotが必要で、後二者は別裁定です。

## 4. login の no-execution shape

### 所見 4-A — `real / Critical`：現 closed set は「test bodyを呼ばない」だけで、login上のcode executionを許す

[run_tests.py:83](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:83) の no-execution setを [plan.md:71](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:71) がそのまま local扱いします。

- `--setup-only`: pytest自身が「fixture setupだけ行う」と定義しています。[setuponly.py:15](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/setuponly.py:15) 任意fixture codeがloginで実行されます。
- `--collect-only`: test module と conftest を importします。top-level subprocessやwriteが実行可能です。
- `--help`, `--version`, `--markers`, `--trace-config`: pytest 9.1.1 は entry-point pluginと`PYTEST_PLUGINS`を読み込みます。[config/__init__.py:1577](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/config/__init__.py:1577)
- 攻撃入力: `PYTHONPATH=/tmp PYTEST_ADDOPTS='-p evilplug' ... --help`。`evilplug` の import side effectがloginで動きます。
- 攻撃入力: `--help --unknown-plugin-option`。現判定は「どれか一個 no-execution flag」があれば localです。[run_tests.py:357](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:357)
- `@response-file` 内の `--collect-only` は早期判定から見えず、逆に不要なqsub、外部file drift、unknown optionの誤分類が起きます。

成果物影響: 「preflight/task-run/xdist/pipはcompute側一回だけ」という [plan.md:108](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:108) の保証を破り、login側plugin/fixture codeがreceiptなしで動きます。

最小修正:

- local許可を wrapper自身が応答する exact `run_tests.py --help` / `--version` のみに狭め、pytestをimport・起動しない。
- plugin固有help等、実pytestが必要な形はcomputeへ送る。
- raw argv、`PYTEST_ADDOPTS`、response fileを同じparserで一度だけ展開し、unknown/compound/external inputはexecuting扱いまたはrc2。
- local branchで deletion/ruleops/submodule、packaging、xdist/pip、pytest、task-run が全て0回であることをsentinelで検査する。

## 5. qsubからfinalまでの状態機械

### 所見 5-A — `real / Critical`：qsub後の親死亡・ID不明から復旧できない

[plan.md:74](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:74) から [plan.md:79](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:79) は一process内の前進しか定義していません。

攻撃系列:

1. qsub rc=0、job生成。
2. qsub stdout保存後、ID parseまたはsubmit receipt公開前に親をSIGKILL。
3. jobは継続するが、qdelもfinal receiptもない。
4. 親再起動時に「未投入」と誤って再qsubすれば二重jobになる。

また worker は submit receiptとjob IDを検証する設計ですが、jobがqsub直後に開始し、controllerのS4 receipt公開を追い越せます。既存実測の「7秒後開始」は最短保証ではありません。[pegasus-runbook.md:103](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/pegasus-runbook.md:103)

成果物影響: orphan job、二重job、runner receiptの早期失敗、task-run重複が発生します。

最小修正:

- qsub前から fsync済み write-ahead `dispatch-journal` を作り、各transitionとraw stdout/rcを追記する。
- `dispatch_id`をjob name/env/receipt pathに入れる。
- `resume --dispatch-id` を設け、`SUBMIT_UNKNOWN` では自動再qsubしない。
- workerはhash-bound pre-submit authorizationを先に検証し、submit receiptをbounded waitする。
- ID不明時はraw qsub出力、unique name、owner、worker-start receiptを突合し、単一に確定できなければ unresolved orphanとして停止する。

### 所見 5-B — `real / Critical`：qstatの状態別fieldと一時失敗が定義されていない

既存 wrapperはqsub直後の一回のqstat失敗でexitし、qdelしません。[submit_silo_ladder_rung1.sh:431](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/submit_silo_ladder_rung1.sh:431)

実在 fixtureでは:

- `Current State=Running`, `Previous State=Pre-running`。[qstat-f.stdout:7](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/output/env/pegasus/calibration/job-staging/0:867870.nqsv/qstat-f.stdout:7>)
- execution hostはrunning後の `bnode003`。[qstat-f.stdout:50](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/output/env/pegasus/calibration/job-staging/0:867870.nqsv/qstat-f.stdout:50>)
- `Number of Jobs=1` はnode数ではありません。[qstat-f.stdout:29](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/output/env/pegasus/calibration/job-staging/0:867870.nqsv/qstat-f.stdout:29>)
- qstatにはCPU Max 48はありますが、requested `-b 1` の明白な同名fieldはありません。

したがって [plan.md:117](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:117) の「parent/worker双方で1 node、bnodeを確認」はpending時には成立しません。

攻撃入力:

- 最初のqstatだけrc1、次はQueued。
- 長時間Queued、HLD、Pre-running、Running、qstat一時障害、job disappearance。
- 誤結果: 一時障害をterminalと誤認、またはpendingにhostがないため正規jobをqdelします。

成果物影響: scheduler正常待ちをinfra failureとし、逆にqstat障害を完了と誤認して不完全receiptを作れます。

最小修正: `submitted → visibility-grace → queued/held → pre-running → running → terminal/disappeared → log-grace → accounting` を明文化する。queue待ちtimeout、run walltime、log/accounting graceを別時計にする。各pollのraw/rcを保存し、generic qstat failureをdisappearanceにしない。`-b1` はjob script/request receiptで束縛し、running後のunique execution host数で実効性を照合する。

### 所見 5-C — `real / High`：取消・walltime・巨大log・publish契約が不足する

- [plan.md:81](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:81) はqdel「一回だけ」。一時的qdel失敗ならjobが走り続けます。
- walltime killでは `runner-result.json` が存在しません。child rcを124/125として捏造してはいけません。
- SIGTERMのcontroller rcが125なのか143なのか未定義です。
- qstat fixtureではstdout/stderr sizeが `UNLIMITED` です。[qstat-f.stdout:68](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/output/env/pegasus/calibration/job-staging/0:867870.nqsv/qstat-f.stdout:68>) 巨大stdoutを`capture_output`やJSON埋込みで扱えばRAM・quotaを枯渇させます。
- 同名jobをfile名globで探すと別IDの `.o/.e` を拾えます。
- `/home` ではrenameat2 no-replaceがEINVALであり、link+unlink fallbackが必要です。[pegasus-runbook.md:327](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/pegasus-runbook.md:327) planの [temp+fsync+no-replace:123](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:123) だけでは実機で停止し得ます。

成果物影響: cancel後もCPU消費、child rc偽装、final receipt未発行、巨大JSON、不正な同名log束縛が起きます。

最小修正:

- 「cancel intentは一回、qdel attemptはbounded retry」に変更し、各attemptを記録する。
- walltime・parent timeout・SIGINT・SIGTERM・qdel failureを別 `dispatch_outcome` にする。
- child rcはrunner-resultがある場合だけ設定する。
- stdout/stderrは直接fileへspoolし、receiptにはpath/size/hashだけを置く。replayはstreaming＋表示上限。
- qstatが宣言したpathとnormalized job IDでexactに一件だけ照合する。
- existing link+unlink no-replace helperの再利用を明記する。

## 6. compute環境と親実測の一般化

### 所見 6-A — `real / High`：bnode114一件はpackage/toolchainの継続可用性を証明しない

親実測は [brief.md:5](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/brief.md:5) の一allocationです。runbookには別jobでdefault `python3` が3.9.13だった事実があります。[pegasus-runbook.md:157](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/pegasus-runbook.md:157)

攻撃入力: 別nodeまたは後日の同nodeで、`/usr/bin/python3.10` はあるがuser-site pytest/xdist/packagingがない、PATHにgit/g++-13がない、plugin版が変わる。

結果: planのper-job gateは停止できるので偽緑にはなりませんが、常時実行可能という一般化は成立しません。またversionだけ合っても、mutable user siteのplugin sourceは束縛されません。

19 skippedも重要です。checkout依存でSilo sample、submodule、g++-13、gnuplot、Codex runtimeの検出力が消えることが既存文書にあります。[orchestrator/tests/README.md:135](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/README.md:135) 同じ `3891 passed / 19 skipped` でも同じnode ID・skip理由・plugin集合を意味しません。

成果物影響: 環境driftを同じsource/test結果と誤って比較し、skipによる検出力蒸発を隠します。

最小修正: 各jobで interpreter realpath/version、pytest/xdist/packagingのversion・distribution path・hash、`sys.path`、loaded plugin、PATH、git/toolchain、submodule HEAD/status、skip理由とcollected-node digestを記録する。より強い保証には、login側でhash-bound dependency bundle/venvをstagingしてcomputeでnetwork非依存に使う。

## 7. `guard_bash` の実効面

### 所見 7-A — `scope外real / Critical`：Claude Bash以外は覆えない

[hooks/README.md:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/hooks/README.md:15) のとおりCodexには未配線です。hook自身もsandboxではなく、変数・script越しを見られません。[hooks/README.md:163](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/hooks/README.md:163)

実装後も残る迂回は少なくとも次です。

- Codex `exec`、SSH terminal、IDE task、MCP/外部runner。
- `P=pytest; "$P"`、alias/function、symlink/renamed binary。
- `bash script.sh` 内のpytest/build、nested `sh -c`、`eval`、encoded command。
- `python -c 'import pytest; pytest.main(...)'`。
- `uv run`、`poetry run`、任意Python `subprocess`。
- raw compiler、別build system、自走 `python3 orchestrator/tests/test_*.py`。

成果物影響: hookを「強制」と文書化すると、実際には覆わないsurfaceでlogin負荷が発生してもpolicy breachとして検出できません。

最小修正は実装ではなく保証の限定です。正確な文言は次です。

> production entrypoint enforcement は `tools/run_tests.py` と列挙したbuild/campaign APIに適用する。Claude Code Bash PreToolUseはPegasus loginと判定したhost上の既知command形をbest-effortで拒否する第二防壁であり、Codex、直接shell、任意script、OS全体を覆うsecurity boundaryではない。

### 所見 7-B — `real / High`：briefの成果物表現がhookの範囲を越えている

[brief.md:31](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/brief.md:31) の「実装後は直接実行を拒否」は、上のsurface限定なしでは過大です。

最小修正: brief、decision、runbook、最終成果物をすべて上記限定表現へ揃える。

## 8. direct build route と実際に効くlayer

### 所見 8-A — `real / High`：ユーザーの広い要求とplanのbuild閉包が一致しない

planは任意campaign/buildのauto-qsubをscope外にし、`t152_write_intent_coverage.py` も明示除外します。[plan.md:275](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:275)

しかしt152は実際にdirect CMake buildを持ちます。[t152_write_intent_coverage.py:340](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/t152_write_intent_coverage.py:340) ほかにも `silo_ladder_rung1.py` のdirect buildがあります。[silo_ladder_rung1.py:2111](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/silo_ladder_rung1.py:2111)

実装後に効くlayerは次だけです。

| layer | 実効性 | 残る穴 |
|---|---|---|
| shared site policy | 分類のみ | 単独では拒否しない |
| `tools/run_tests.py` | loginからsync qsub | direct pytest/self-runを覆わない |
| worker marker | 再dispatch防止 | 認証境界ではない |
| buildcache v1/v2 | API呼出しをlogin拒否 | direct CMakeを覆わない |
| pipeline | 入口gate | gate外producerを覆わない |
| coverage 4経路 | 列挙helperを拒否 | t152等を覆わない |
| Claude guard | 既知text形を拒否 | Codex・script・変数を覆わない |
| docs/runbook | 人間の運用規律 | 機械執行ではない |

成果物影響: 「ビルドやテストは計算ノードで」という全称命題に対し、実装保証は列挙entrypointだけです。

最小修正: 今回のacceptance文を「standard runner＋named build entrypoints」に狭めるか、scopeを広げる裁定が必要です。

### 所見 8-B — `real / High`：fresh実argvをそのままfloorへ流すとnonceがprovenanceを汚す

v2 buildの実argvは `.staging-<pid>-<nonce>` を含みます。[buildcache.py:487](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:487) planはこれをfresh `BuildResult`へ返す設計です。[plan.md:160](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:160)

一方portable変換は `${OUT_ROOT}` と `${CCBENCH_ROOT}` しか置換しません。[s8b_floor_campaign.py:1065](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8b_floor_campaign.py:1065)

- 攻撃入力: 同じsource/contractを二回fresh build。
- 誤結果: PID/nonceだけ異なる `build_argv` がfuture manifest driftになり、ratified比較を不必要に赤くします。

成果物影響: 実行argvの正直さを直す変更が、再現比較不能なrandom artifactを作ります。

最小修正: display-only portable viewではstaging componentを `${BUILD_STAGING}` に正規化し、実際に実行したraw argv/hashはbuild-local receiptに別保存する。二nonceが同じportable argvになる検査を追加する。

### 裁定候補

- A（最小・推奨）: 今回はstandard surface保証と明記し、未列挙routeを保証外にする。
- B: t152、全direct campaign helper、自走testを含む全repo production entrypointへ共通早期拒否gateを追加する。
- C: campaign/buildもsync auto-dispatchする別waveを立てる。
- D（`scope外real`）: literalなsystem-wide強制にはscheduler/PAM/cgroup等の管理者側policyが必要。repo/hookだけでは閉じられない。

## 9. gate field・receipt・rc・ledger・識別子

### 所見 9-A — `real / High`：同名概念の正本が未確定

task-run schemaは`additionalProperties:false`で、PBS job、dispatch ID、receipt hashを格納できません。[schema_v1.json:110](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/task_runs/schema_v1.json:110)

さらに runnerはtask-run記録失敗を握り潰し、返されたeventも捨てます。[run_tests.py:693](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:693) ledger API自体はeventを返します。[ledger.py:851](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/task_runs/ledger.py:851)

したがって:

- task-run eventはbest-effort観測であり、dispatch成功の正本にはできない。
- pytest rc=0のledger eventがあっても、post-budget/accounting失敗でparent rc=125になり得る。
- `source_digest` は既存buildの`src_token`概念と衝突します。[buildcache.py:121](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:121)
- qsub返却IDとworkerの`PBS_JOBID`はraw表記が異なる可能性があります。
- markerはnonce/source hashだけですが、本文はsubmit receipt/job IDまで一致させると書いています。[plan.md:99](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:99)
- qstatの「1 node」入力fieldも実在成果物上未確定です。これはDW-O13違反です。[operations.md:70](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/dev-wave/operations.md:70)

成果物影響: 同じ「rc」「source」「job ID」が別の真実を表し、後日の監査でどれを信じるべきか決まりません。

最小修正として正本を次に固定します。

| 概念 | 正本field |
|---|---|
| dispatch identity | `dispatch_id` |
| qsub raw ID | `qsub_request_id_raw` |
| worker raw ID | `pbs_job_id_raw` |
| scheduler比較用ID | `job_id_normalized` |
| snapshot全体 | `snapshot_manifest_sha256` |
| pytest child結果 | `runner-result.json.pytest_exit_status` |
| scheduler/controller結果 | `final-receipt.dispatch_outcome` / `controller_exit_status` |
| lifecycle | append-only `dispatch-journal` |
| task-run | observational event。`event_id`をreceiptへlinkするだけ |
| build source | 既存`src_token` / build source digest。snapshot名を流用しない |

task-run記録は「一回attempt」を保証し、成功eventがなければその事実をrunner receiptへ残すべきです。

## 10. acceptance / mutation のmask

### 所見 10-A — `real / High`：同じrcや「subprocess未呼出し」だけではscheduler branchを通った証明にならない

[plan.md:209](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:209) と [plan.md:224](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:224) の検査は広いですが、前段mask防止が明文化されていません。

具体例:

- fake scheduler testがrc125だけを見ると、site分類、snapshot、preflightで先に失敗しても緑になります。
- 「loginではconfigure未実行」だけを見ると、`_assert_single_tenant` やpin検査で先に落ちても緑です。現coverage mainはそれらをbuildより先に実行します。[s3_lock_coverage.py:153](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s3_lock_coverage.py:153)
- no-execution testが「qsub 0回」だけなら、help/version処理自体が一度も動かない偽緑を許します。
- compute上の受入だけではlogin dispatch branchを通りません。
- snapshot testがdefault targetだけなら、絶対path targetの元worktree escapeを殺せません。
- qdel mutationも、timeout前に別gateが落ちれば生存します。

成果物影響: mutationを「殺した」と記録しても、目的branchに到達していない偽検出になります。

最小修正:

- 各testにordered traceを持たせ、`site → snapshot → qsub → visible → queued/running → disappearance → logs → accounting → final` をassertする。
- branch前後に異なるfatal sentinelを置き、期待branch以外の呼出しを即失敗させる。
- site observation、clock、scheduler responseを明示注入する。
- no-execでは期待output/rcを一回確認し、preflight/xdist/pip/pytest/task-run/qsubは全て0回を確認する。
- snapshotでは明示targetがsnapshot rootを指すことを確認し、submit後に元fileを変更する。
- qstat transient、HLD、queue timeout、walltime kill、qdel failure、unknown ID、同名job、巨大stdoutを独立caseにする。
- task-run event ID取得、target remap、qstat retry、portable staging placeholderのmutationも追加する。

## 反証済み所見

- `refuted / Info`：planのabsolute `file:line` targetを静的に63件検査し、missing/OOBは0件でした。[plan.md:3](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:3) の不存在 `docs/runbooks/pegasus.md` も正しく申告され、正本へ切り替えています。
- `refuted / Info`：「48 workerが常に最速と主張した」は成立しません。briefは明示否定しています。[brief.md:7](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/brief.md:7) 205.12秒対206.94秒は一回ずつ・差1.82秒、約0.88%で性能一般化不能です。default 48はaffinity policyとしてのみ扱うべきです。
- `refuted / Info`：「planはcompute network利用を仮定する」は成立しません。runbookには二jobのnetwork不可観測があり、planもpip/fetchを禁止しています。[pegasus-runbook.md:341](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/docs/pegasus-runbook.md:341) [plan.md:114](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:114)
- `refuted / Info`：`pegasus01.ccs.tsukuba.ac.jp.evil` のsuffix spoofは、planどおりexact matchを実装すればlogin扱いされません。問題はsuffix matchではなく、正規化未定義と観測自体のspoofabilityです。
- `refuted / Info`：cancel開始後の遅着successを成功へ反転しないこと、およびNQSV accountingをchild rc正本にしないことはplanに明記済みです。[plan.md:81](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:81) [plan.md:121](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:121)
- `refuted / Info`：新test fileの自走harness欠落はplan自身が検査対象にしています。[plan.md:221](/home/SFC/tanab/.codex/dev-wave-improve-wave/s3-scheduler/plan.md:221)

## 総括

現 plan の blocking は、canonical import、`OTHER` fail-open、snapshot外target、staged/index drift、危険なno-execution、qsub後復旧不能、qstat状態別field未定義です。

段5へ進む最小条件は次の5点です。

1. Pegasus-like不明状態をfail-closedにし、qloginを実測する。
2. raw argvからsnapshot-relative入力closureを作り、dirty snapshotの保証を現実的に狭める。
3. local no-executionをwrapper自身のpure help/versionだけへ再定義する。
4. durable journal＋resumeを持つscheduler状態機械へ改稿する。
5. named entrypoint保証とsystem-wide強制を分離し、receipt/rc/IDの正本名を固定する。

本レビューではpytest、build、qsub、mutation、実機受入を一切実走していません。したがって、上記は静的な敵対所見であり、緑判定ではありません。