判定は **NO-GO**。静的検査のみで、pytest・wrapper は実走していない。親既知の interpreter 選定文字列テスト赤は新規所見に含めない。

## 所見

### 1. source commit に束縛されるのは adapter だけで、実 admission 本体は現 worktree から import される

[severity: must-fix]

何が壊れる / 効かないか:

wrapper は commit A の `certified_writer_preflight.py` を stdin 実行するが、adapter は `--repo-root` の現 worktree B を `sys.path` に加え、`certified_writer_admission` と全依存を B から import する。したがって A→B drift、dirty worktree、import API 変更によって受理・拒否が変わり、source-commit 隔離になっていない。

さらに `-B` は `.pyc` を抑止するが、import された B の module の任意の副作用までは抑止しない。`-I` も `-S` ではないため、「いかなる場合もファイルを変更しない」という契約を Python 起動全体について保証しない。

根拠:

- commit A から streaming するのは単一 adapter blobだけ。[floor_campaign.sh:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:83)、[t126_qualification.sh:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:101)
- adapter は現 worktree の `orchestrator` を先頭へ挿入して importする。[certified_writer_preflight.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/certified_writer_preflight.py:44)、[certified_writer_preflight.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/certified_writer_preflight.py:48)
- admission 本体も多数の現 worktree moduleを importする。[certified_writer_admission.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/certified_writer_admission.py:16)
- 段4契約は A/B drift 非依存と無変更を要求している。[s4-ruling.md:75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s4-ruling.md:75)、[s4-ruling.md:165](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t609-certified-writer-closure/s4-ruling.md:165)

提案:

source commit から adapter と検証コード closure を一体でロードする read-only import loaderを用意する。current registry/calibrationのように実行時 current を意図する入力は、source code importとは分離して明示的な data leafとして読む。少なくとも、依存 module をBで互換破壊・副作用化するA→B driftテストを追加する。

成果物影響: 放置すると同じ commit A の submissionでもworktree Bの内容により受理集合が変わり、attempt/result/台帳は「Aに束縛された admission」の証拠にならない。

---

### 2. floor の A→B drift は preflight 通過後、既存 current-HEAD gate で必ず拒否される

[severity: must-fix]

何が壊れる / 効かないか:

floor preflightはreceiptのcommit Aを使うが、最初の書込み後に現HEAD Bとreceipt Aの一致を要求する。A≠Bならattemptを作った後に `source_identity` failure artifactを書いて終了する。実装子Bの「A/B driftは誤拒否しない」はwrapper全体では成立しない。

根拠:

- preflightはreceipt由来commitを使う。[floor_campaign.sh:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:54)
- その後scratch・attemptを作る。[floor_campaign.sh:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:97)、[floor_campaign.sh:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:163)
- 現HEADとreceipt commitが違えばfailure writer経由で拒否する。[floor_campaign.sh:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:524)、[floor_campaign.sh:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:535)
- 新正例テストは最初の `mkdir` を故意に失敗させ、後段gateへ到達しない。[test_pegasus_floor_tools.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_pegasus_floor_tools.py:443)、[test_pegasus_floor_tools.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_pegasus_floor_tools.py:456)

提案:

floorもreceipt commitからsource stageを構成するか、現HEAD一致gateをreceipt commitのblob検証へ置換する。A→B driftで実driver直前まで到達し、source-identity failureが作られないwrapper結合テストが必要。

成果物影響: 放置すると正当なqueued floor runが受理集合から除外され、floor resultの代わりに `source_identity` failure artifactが台帳へ残る。

---

### 3. T126 request gate がT126固有reservation policyではなくfloor walltimeを参照する

[severity: must-fix]

何が壊れる / 効かないか:

T126は固有reservation policyを正本とするが、共通 `_validate_request()` は常に共有policyの `floor_walltime_s` と比較する。現在はいずれも36000秒なので偶然通る。将来どちらかだけ正当に更新すると、valid T126 receiptを誤拒否する。逆に、T126固有policyとの一致は最初の書込み前に確認されない。

根拠:

- T126 submitterはreservation policyを独立正本と明記する。[submit_t126_qualification.sh:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_t126_qualification.sh:34)
- receiptのwalltimeはその固有policyから渡される。[submit_t126_qualification.sh:731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_t126_qualification.sh:731)、[submit_t126_qualification.sh:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_t126_qualification.sh:764)
- admissionは共有policyを読み、常に `floor_walltime_s` と比較する。[certified_writer_admission.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/certified_writer_admission.py:84)、[certified_writer_admission.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/certified_writer_admission.py:91)
- T126固有policyの実検査はjob-staging/trap後。[t126_qualification.sh:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:503)

提案:

request validatorをmode別にし、T126ではcommit由来 `t126_reservation_policy_v1.json` の `t126_qualification_walltime_s` を使う。共有policyからはproject/queue/nodesだけを取得する。floor/T126 walltimeを意図的に異ならせた正例を追加する。

成果物影響: 放置すると正当なpolicy更新後のT126 submissionがpreflight受理集合から消え、series/attempt/result参照が発行されなくなる。

---

### 4. 実装子Aが列挙しなかった既存signature consumerが確実に赤になる

[severity: must-fix]

何が壊れる / 効かないか:

`test_trigger_gate_binding.py` は `loop.run_campaign` と `pipeline.evaluate` を、`authorization_contract` なしで `Signature.bind()` している。両APIとも必須keyword-onlyになったため、`trigger_gate_binding` のassertへ到達する前に `TypeError` となる。実装子Aの「直接影響7本」一覧から漏れている。

根拠:

- 既存テストの2件のbind入力にauthorizationがない。[test_trigger_gate_binding.py:401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_trigger_gate_binding.py:401)、[test_trigger_gate_binding.py:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_trigger_gate_binding.py:419)
- 両signatureは必須引数である。[loop.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:92)、[pipeline.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:476)

提案:

このfixtureのkwargsへ `authorization_contract=object()` を追加する。型検査を実行するテストではなくsignature bindingだけなので、期待値変更は不要。同時にsignature参照もcaller inventoryへ含める。

成果物影響: 放置すると受入全走は少なくともこのnodeでも赤になり、全走成功を参照する受入レポート・land台帳を正当に発行できない。

---

### 5. wrapper正例は実helper/domain admissionを一度も通していない

[severity: should-fix]

何が壊れる / 効かないか:

両wrapper結合テストは、環境変数で0/3/4を返す専用stubをcommitしている。Python側の「正例」も `admission.admit` をmockしている。このため実際のreceipt、ledger、protocol、registry、calibrationを組み合わせたexit 0経路が無被覆で、所見1・3を検出できない。

根拠:

- floor stubは入力をほぼ見ず環境変数からrcを返す。[test_pegasus_floor_tools.py:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_pegasus_floor_tools.py:200)
- T126も同型。[test_t126_pegasus_tools.py:735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_t126_pegasus_tools.py:735)
- Python正例はdomain admissionをmockする。[test_campaign.py:2431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:2431)、[test_campaign.py:2440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:2440)

提案:

実 submitter形式のreceipt/ledger/qsub evidenceを組み、siteとcalibrationのOS境界だけを注入して実 `admit()` を通す正例をmodeごとに追加する。stub wrapperテストはshell rc/順序専用として残してよい。

---

### 6. caller inventoryテストはalias・partial・追加callを閉じない

[severity: should-fix]

何が壊れる / 効かないか:

現在のAST検査は、決め打ちfileと単純な `ast.Name` だけを数える。direct sink側は「どれか1 callにauthorizationがある」ことしか要求しない。今回、`functools.partial` はなく、monkeypatch/injected fakeは `**kwargs` を受けるため追加の実破損は見つからなかったが、将来同じfileへ未配線callを足しても通り得る。

根拠:

- run inventoryは固定12 fileだけを走査する。[test_campaign.py:2332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:2332)
- direct sinkは `any(...)` 判定である。[test_campaign.py:2357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:2357)、[test_campaign.py:2372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:2372)

提案:

repo全体でimport aliasを解決し、全 resolved `pipeline.evaluate` / injected default / `run_campaign` callについて必須keywordを検査する。関数参照、`partial`、signature binding、monkeypatch置換も別カテゴリで棚卸しする。

## 呼び手・shell・identity の確認結果

productionの15 `run_campaign` callは、`backoff_repro`、`backoff_sweep`、`demo`×2、`p2_2`、`p3_kickoff`×2、`p3_s4_loop`、`p3_s4_loop_sort`、`p3_s4_loop_trigger_gating`、`p3_s4_red`×2、`s6_sort_sweep`、`s8a_trigger_sweep`、`sanity_silo`のすべてに配線済みだった。

直接sinkは `loop`、`screening_driver`、`s1_direct_comparison`、`s8b_oracle_driver`、`t126_driver`で配線済み。直接call test 7本も更新済みで、意図的なM1負例を除く未配線callは見つからなかった。`functools.partial` は0件。monkeypatch/injected `evaluate_fn` はすべて `**kwargs` を受け、追加keywordで壊れるものは見つからなかった。実破損は所見4のsignature consumerだけである。

shellについては、preflight前にtrapはなく、floorのtrapはline 254以降、T126はline 356以降なので、preflight非0だけでfailure artifactを書く経路はない。`set -o pipefail` と `|| preflight_rc=$?` の組合せはpipeline全体のrcを保持し、`git cat-file`失敗を空stdin＋Python exit 0で握り潰さない。`umask`、`unset`、`pwd -P`、時刻取得、receipt待ちはfilesystem mutationではない。PBS directive、dirty-tree検査、operational interpreter marker、driver rc処理には実装差分による変更を見つけなかった。

identityの波及は次のとおり。

- floorのfuture `job_script_sha256` は変わり、submit receipt、wrapper照合、job-result、新preflightが消費する。
- T126のfuture `script_identity` が変わり、それを入力に `series_identity`、submission、attempt/job-result、collector、external identity verifierが連鎖して変わる。
- `REQUIRED_SCRIPT_IDENTITY_PATHS` のkey集合は不変。[contract.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/contract.py:67)
- verifierは記録されたhistorical commitのblobを再取得するため、既発行seriesは引き続き検証可能。[identity.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/identity.py:112)、[identity.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/identity.py:137)

新テストの通常時1件所要は未実測。構造上、floor 2件で計2回の`git init`・6 commit、T126 2件で計2回の`git init`・4 commitを作る。各repoとjob IDは`tmp_path`由来で独立し、`mkdir` shimが最初の `/scr` mutationを遮るため、xdist相互干渉や実 `/scr` 作成は見当たらない。4件のtimeout上限は各20秒だが通常経路は最初のmkdirまでで、30分全走を大きく押し上げたと静的には判断できない。遅さが実測された場合は、module-scoped template repoを作り各testへcopy/cloneするのが具体的な削減策になる。

追加期待値にworking-tree hash、時刻、hostname、commit SHAの固定焼込みは見つからなかった。job IDとcommit/hashはfixtureから動的導出されている。

## 総括

must-fixは **4件**。

1. source commitに束縛されないPython admission closure
2. floorの後段current-HEAD gateによるA→B queued-job誤拒否
3. T126 request gateのfloor walltime誤参照
4. `test_trigger_gate_binding.py` の取り残したsignature consumer

判断は **NO-GO**。

親が全走する前の修正順序:

1. source-bound import closureを確定する。
2. floorのcurrent-HEAD gateをreceipt/source-blob基準へ直す。
3. T126 requestを固有reservation policyへ結線する。
4. 実helper正例とA→B完走テストを追加する。
5. `test_trigger_gate_binding.py` と親既知のinterpreter順序テストを直す。
6. focused tests、consumer test全体、最後に受入全走を実行する。