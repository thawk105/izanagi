NO-GO です。current staged bytes には、live qsub 前に閉じるべき blocker 5件を含む must-fix 9件があります。

- staged SHA-256 は開始時・終了時とも `bda3aa8f76aa0ef8e3068c4e5fd96d8ae9148eee63d4cef340c7c8dd1b905b22` で一致。
- 指定された root の `mutation-prereg.md` は不存在でした。scheduler/contract 配下の2コピーは byte-identical、SHA-256 `6d719bcb…5206bc8b7c` だったため、それらを全文監査しました。
- pytest/build/qsub/qstat/qdel は未実走。green は主張しません。実施したのは静的読解と isolated import/function probe のみです。

## Current blocker / must-fix

| ID | 重要度 | current file:line | 攻撃入力 | artifact impact |
|---|---|---|---|---|
| R1 | BLOCKER | [buildcache.py:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:35) | `sys.modules["pegasus_policy"]` に、canonical `__file__`/`spec.origin`、canonical filename でcompileした関数、`__module__="pegasus_policy"` を持つ偽moduleを置く | 実 caller probe で `buildcache.pegasus_policy is fake == True`、偽 `observe_site()` の OTHER も受理された。login build missを許可できる。通常の `importlib.reload` は通るため、legitimate reloadを拒否せず残る穴。 |
| R2 | BLOCKER | [test_dispatch.py:1738](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1738)、[submit_tests.py:312](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/submit_tests.py:312)、[run_tests.py:1014](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:1014) | `test_campaign.py`を選択し、manifest後にそれがimportする `orchestrator/campaign/buildcache.py` を置換 | closureは選択test・conftest・固定runner類だけで、import先production moduleを含まない。full-tree検査はsubmit receipt待ちより前、その後とrunner終了時はclosureのみ。finalのsnapshot digestと実行bytesが乖離する。 |
| R3 | BLOCKER | [test_dispatch.py:2977](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:2977)、[同:4371](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:4371) | test自身がstderr途中に四fieldを出し、後ろに通常stderrを続ける | footerの連続性・順序・末尾separatorを見ず、四行が任意位置にあれば受理。probeでも偽四行＋trailing garbageが通った。さらにaccounting grace中に本物footerが追記されると、parse対象は新bytes、`stderr_sha256`はgrace前の古いreceiptとなりfinal検証が例外化する。 |
| R4 | BLOCKER | [test_dispatch.py:103](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:103)、[同:4849](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:4849)、[同:5151](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:5151)、[同:5389](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:5389) | qsub受理後のtempfile read/wait `OSError`、`qsub-intent`直後crash、cancel後のfinal publish失敗 | `SubprocessScheduler`の広い`OSError`捕捉は受理不明でもrc127 definite failureにし、lookupせず`SUBMIT_FAILED`。resumeは完全なqsub-result＋qsub-returnを先に要求し、intent/result/submit/cancel/final各境界のcrashを回収できない。monitorがqdel済みでも外側exceptが再度qdelする。 |
| R5 | BLOCKER | [test_dispatch.py:2851](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:2851)、[同:2871](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:2871)、[同:4299](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:4299) | `qstat -f 123.nqsv` が `Request ID: 999.nqsv` を返す、または同じ35-byte job nameの先行decoyを一件だけ可視化 | monitor parserはRequest IDを検査せずterminal化できる。lookupはname/stateのみで、created time・worker claimとの結合がないため、同一userのdecoy/旧terminal requestを実jobとしてqdelできる。running hostも「bnodeが一つ」だけでrunner hostnameと比較しない。 |
| R6 | HIGH | [test_dispatch.py:4353](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:4353)、[同:4495](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:4495) | terminal後にstdout=20、stderr=20、combined limit=32へ成長 | `failure_reason`を設定してlog loopを抜けるだけ。各fileが個別上限以下ならreceiptsは残り、valid child/accountingで`CHILD_RESULT`になる。quota超過成功artifactを生成する。 |
| R7 | HIGH | [test_dispatch.py:3195](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:3195) | task-run ledgerをreceipt size以上の別内容へ置換し、同じevent IDを一度だけ含めて追記 | ledgerが成長した場合、receipt-size prefixのSHAを検証しない。producer時点のhashと現在のdurable event bytesが無関係でもrunner/finalが受理する。 |
| R8 | HIGH | [test_dispatch.py:3348](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:3348)、[同:3986](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:3986)、[同:4575](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:4575) | lookup resultをWALに置き、別IDのsubmit receiptへ接続／global deadline後にresume | validatorはintent/resultの一対一・順序・matched candidateとsubmit IDの結合を要求しない。lookupは呼出しごとに新しいvisibility deadlineを作り、qsub absolute deadlineを受け取らない。accounting再試行成功後も古い`failure_reason`が残り、成功schemaが自己矛盾する。 |
| R9 | MEDIUM | [pegasus_policy.py:351](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus_policy.py:351)、[run_tests.py:285](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:285) | computeで`-n auto`または`-n logical` | U1 APIはaffinity数へ解決するが、実callerはAPIへ渡さずrc2で拒否する。OTHER互換は直ったが、U1 fix artifactが明記したcompute統合は未完。 |

実在NQSV footerはseparatorを含む末尾blockです。[実stderr fixture](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/output/env/pegasus/t140-setsize/job.sh.e872886:3>) と current validatorの受理集合は一致していません。

### Scheduler lookupの攻撃別判定

- 実在形式: `Request ID`、完全な`Request Name =`、`Current State =` の列挙自体は[実qstat fixture](</home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/output/env/pegasus/smoke/0:867860.nqsv/qstat_all_detail.stdout:1>)をparseできる。
- Request Name truncation: current nameは35 bytes。NQSV仕様の上限63 bytes未満なので、この攻撃はrefutedです。[NQSV User’s Guide Reference](https://sxauroratsubasa.sakura.ne.jp/documents/nqsv/pdfs/g2ad04e-NQSVUG-Reference.pdf)
- 他user job: productionの`qstat -f`はrequest ID省略時にcommand executor所有requestだけを対象とし、scheduler envもprivilege変数を渡さないため、通常経路のforeign-user混入はrefuted。同一userによる同名decoyは未解決です。
- zero/transient/multiple/malformed/unknown state: bounded retryまたはfail-closedになっている。
- ended/history: parserは`Ended`を候補として受理する。clusterでの終了request可視期間は未実走であり、作成時刻との結合もない。
- output limit: memory/receiptはboundedだが、ID不明のまま`SUBMIT_UNKNOWN`になりqdel不能。偽成功ではないが、accepted jobを残さないというclosureは成立しない。
- exact monitor ID:未実装。current fake `_qstat()` もRequest IDを出さず、この欠陥を肯定している。

## 初回review A 再判定

| ID | 判定 | current file:line | 攻撃入力 → artifact impact |
|---|---|---|---|
| A F1 policy所有 | closed | [test_dispatch.py:474](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:474) | 既存policy変更 → staged対象外かつHEAD/index/worktree SHA `b1c42e49…961ac`一致。新policyはU2所有。 |
| A F2 execution bytes | partial | [test_dispatch.py:1738](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1738) | imported production module置換 → closure外なのでfinalが未実行bytesを証明。job symlink自体はclosed。 |
| A F3 local Git config | closed | [test_dispatch.py:811](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:811) | fsmonitor/filter/info attributes → qsub前に拒否、Git env/configもscrub。 |
| A F4 quota/log | partial | [test_dispatch.py:1982](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1982)、[同:4353](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:4353) | aggregate/per-file/copy cleanupはclosed。terminal後combined spool増大はR6で成功化。 |
| A F5 accounting | partial | [test_dispatch.py:2977](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:2977) | qstat-as-accountingは除去。ただし偽四行・非footer・receipt raceで偽/壊れたaccounting artifact。 |
| A F6 scheduler state | partial | [test_dispatch.py:2851](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:2851)、[同:4203](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:4203) | allowlist/transient/monitor absolute deadlineはclosed。wrong Request IDとlookup deadline resetが残る。 |
| A F7 orphan window | partial | [test_dispatch.py:4849](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:4849)、[同:5389](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:5389) | timeout/signal/既知ID例外は改善。OSError、crash境界、double qdel、decoy lookupでorphan可能。 |
| A F8 final/negative rc | closed | [test_dispatch.py:3478](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:3478)、[run_tests.py:930](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:930) | 不完全status 0、rc=-15 → exact schema拒否またはsignal/143へ正規化。 |
| A F9 qsub provenance/WAL | partial | [test_dispatch.py:2114](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:2114)、[同:3348](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:3348) | argv/env/policy/job/raw結果/hash chainは追加。lookup matched IDとsubmit/finalの結合、crash transition closureが不足。 |
| A F10 canonical policy | partial | [buildcache.py:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:35) | 通常path poisonは拒否。canonical-looking forged metadataは実probeで受理されloginをOTHER化。 |
| A F11 worker/task-run | partial | [run_tests_job.sh:60](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/run_tests_job.sh:60)、[test_dispatch.py:3195](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:3195) | closed env、affinity receipt、durable rootは追加。ledger prefix hashとqstat-host/runner-host一致が不足。 |
| A F12 fake tests | partial | [test_pegasus_test_dispatch.py:57](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_test_dispatch.py:57)、[同:109](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_test_dispatch.py:109) | exact argv/raw canonical JSONへ改善。ただしfinalは`verify_files=False`、qstat fixtureはIDなし、dynamic spool・crash境界を表現できない。 |

A計: closed 3 / partial 9 / regressed 0 / refuted 0。

## 初回review B 再判定

| ID | 判定 | current file:line | 攻撃入力 → artifact impact |
|---|---|---|---|
| B F1 existing policy | closed | [test_pegasus_tools.py:139](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_tools.py:139) | 既存policy SHA差替え → byte-exact testと実SHA一致。 |
| B F2 accounting | partial | [test_dispatch.py:2977](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:2977) | 任意qstat rc0は証拠にしないが、非footer四行で`CHILD_RESULT`可能。 |
| B F3 OTHER/affinity | closed | [pegasus_policy.py:250](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus_policy.py:250)、[同:311](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus_policy.py:311) | unrelated non-NQSV PBSとaffinity API欠落 → OTHERのみfallback。NQSV/Pegasus-like/bnodeはfail-closed維持。 |
| B F4 task-run root | partial | [test_dispatch.py:1278](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:1278)、[同:3195](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:3195) | rootは保存・closed envへ渡る。ただし成長ledgerのproducer-time bytesを束縛できない。 |
| B F5 s8a freq gate | closed | [s8a_trigger_freq.py:118](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/s8a_trigger_freq.py:118) | login invocation → pin/patch/tempdirより前に拒否し、同じobservationをhelperへ渡す。 |
| B F6 env split | closed | [guard_bash.py:205](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/hooks/guard_bash.py:205) | literal `env -S 'pytest -q'`等 → 再tokenizeしてlogin拒否。不正payloadもloginだけfail-closed。 |
| B F7 OTHER symbolic | closed | [run_tests.py:285](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/run_tests.py:285) | OTHERの`-n auto/logical` → pytestへsymbolicのまま到達。compute統合のR9は別途残る。 |
| B F8 safe ADDOPTS/core | closed | [test_dispatch.py:624](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:624) | safe `PYTEST_ADDOPTS`/`-h` → stage。argsfile/plugin/outside pathは拒否。 |
| B F9 interpreter | closed | [run_tests_job.sh:25](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/run_tests_job.sh:25)、[submit_tests.py:42](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/submit_tests.py:42) | 最初のPythonにdependencyなし → 同一interpreter dependency probeで後続候補を選ぶ。 |
| B F10 helper M18 | closed | [test_campaign.py:389](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_campaign.py:389) | helper gateを移動/削除 → mainを経ずhelper直呼び、login sentinelとcompute/OTHER `-j16`到達で検出可能。 |
| B F11 qsub resource gate | closed | [test_pegasus_test_dispatch.py:749](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_test_dispatch.py:749) | `-A/-q/-b/-l`変更 → policy由来の全argv exact tuple比較で赤。 |

B計: closed 9 / partial 2 / regressed 0 / refuted 0。

## U3/U4非回帰

- buildcache v1/v2ともvalid hitがmiss gateより先。miss gateはstale clear、makedirs、claim、configure/build前です。[v2:618](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:618)、[v1:749](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/campaign/buildcache.py:749)
- 4 direct helperと各mainは副作用前site gateを持ち、`s8a_trigger_freq`もmain先頭。compute/OTHERの`-j 16`は維持。
- U4はrunner、submitter、qsub、configure、read-only commandをsite観測なしで許可し、compute/OTHERのdirect heavyも維持。変数・alias・encoded arbitrary commandはU4 artifact自身が明記した保証外surfaceで、今回のdirect literal `env -S`裁定をregressionとはしません。

## Reviewer期待赤node / M1〜M20

期待赤nodeは、A2/A5–A7/A9–A12およびB2/B4が部分的です。特にfooter正例、qstat exact ID、post-terminal増大、WAL crash境界、canonical-looking module、task-ledger prefixは現testが実branchへ届きません。その他の初回期待赤nodeは、同名または同等のdirect branch testが追加されています。

| Mutation | 判定 | current test effectiveness |
|---|---|---|
| M1 unknown NQSV→OTHER | kill | unknown NQSV/Pegasus-like exact-cause test。 |
| M2 hostname canonicalization除去 | kill | short/FQDN/case/trailing-dot＋evil suffix。 |
| M3 compute default=32 | kill | affinity48をexact期待。 |
| M4 oversubscribe受理 | kill | affinity境界の直接API/caller test。 |
| M5 login dispatch後置 | kill | preflight/subprocess fatal sentinel。 |
| M6 targetを元repoのまま | kill | caller cwd正規化＋snapshot target検査。 |
| M7 cached applyの`--index`除去 | kill | snapshot Git status/diffがsourceと一致しなくなる。 |
| M8 argsfile/plugin無hash受理 | kill | actual argv encoderの拒否test。 |
| M9 login collect-onlyをlocal扱い | kill | collect-onlyがdispatch sentinelへ到達。 |
| M10 qsub前WAL fsync除去 | survives | 完成WALの構造しか見ず、fsync/order durabilityを観測しない。 |
| M11 qstat rc1をterminal化 | kill | Running→transient→Running ordered trace。 |
| M12 runner-result不在をrc0化 | partial | production schemaはfail-closedだが、専用missing-result end-to-end赤nodeなし。 |
| M13 cancel後late success | kill | canceled branchのvalid fake childを消さないとCANCELED exact schemaが破れる。 |
| M14 qdel retry除去 | survives | first qdel failure→second successのtestなし。 |
| M15 task-runを成功正本化 | partial | producer rc9非上書きは見るが、accounting failure＋green task eventのcontroller branchなし。 |
| M16 v2 miss gate後置 | kill | makedirs/claim/staging/run fatal sentinel。 |
| M17 login hit拒否 | kill | valid-hit positive control。 |
| M18 helper gate後置 | kill | 4 helper直呼びと`-j16`到達。 |
| M19 heavy gate後置 | kill | direct heavy actual `decide()`とsanctioned positive controls。 |
| M20 dual-load identity | partial | ordinary path/module poisonはkillするが、R1のmetadata/code-filename forgeを通す。 |

### 黙って通る具体的mutation 3件

1. [append_journal:459](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:459) の`os.fsync(fd)`を除去する。canonical WAL testは通る。
2. [cancel_job:3264](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:3264) を常に一回だけ試行にする。全qdel testは初回成功fixture。
3. [monitor_job:4353](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py:4353) のpost-terminal combined spool判定を除去する。現quota testはpoll前に既に超過しており、別branchで赤にならない。

## Ownership / scope

- 実装・test・設定22 pathはU1 2、U2 10、U3 8、U4 2の各owner worktreeと全てbyte-identical。
- `s8a_trigger_freq.py`は追加U3 consumer再裁定に一致。
- docs/insight以外の親独自実装hunkなし。
- 既存`tools/pegasus/policy.json`は未stagedかつHEAD/index/worktree byte-exact。
- qlogin markerless、buildcache v3、system-wide enforcement、network namespace、build-jobs resolverを実装済みとは記録していない。
- protocol/selector/submodule/freeze本体へのhunkなし。buildcache cache key、completion exact keys、`BuildResult`、既定`-j16`を変更するhunkもない。

## 総括

初回23所見の再判定は **closed 12 / partial 11 / regressed 0 / refuted 0** です。

current blockerは **5件**、blockerを含むmust-fixは **9件**。特に canonical policy forge、実行closure欠落、非exact accountingとreceipt race、qsub crash/resume/qdel補償欠落、scheduler lookup identity誤同定を閉じる必要があります。

開始・終了のstaged SHA-256はいずれも固定値 `bda3aa8f76aa0ef8e3068c4e5fd96d8ae9148eee63d4cef340c7c8dd1b905b22`。pytest/build/qsubは未実走で、green証拠はありません。

**判定: NO-GO。**
