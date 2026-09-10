## 差分確認

指定7ファイルを絶対パスで全文確認した。さらに、tracked 7ファイルの全差分（166追加・2削除）と、新規 `tools/ruleops.py` 1,436行、`test_ruleops.py` 745行、RuleOps docs/ledgerを全文確認した。staged差分はない。

`output/insights/...t143-ruleops-wave/` は未追跡のjob artifact群であり、指定された裁定・author要約をデータとして確認した。編集・commit・pytest・RuleOps CLI・受入テストは実行していない。author記載の実走結果も本レビューの緑とは扱わない。

静的Git照会では現HEADは835 commits、対象97 tests／251 insights。例示query `偽緑` の単一 `git log -S` は最初の10秒yield内に完了せず、41 events、HEAD literal hitも41 filesだった。

## findings

### RB-1 — BLOCKER: test候補に必須のreceiptを作る運用導線がない

- **根拠:** `inspect --draft` は `mutation_receipts: []` を出す一方、`check` は最低1件を要求する。[tools/ruleops.py:827-848](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:827)、[tools/ruleops.py:1133-1138](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1133)。CLIは3 commandだけで、docsはreceiptの参照形しか説明せず、12-key本体schemaを示さない。[docs/ruleops.md:71-77](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/ruleops.md:71)。実際の作成者はtest helperだけである。[test_ruleops.py:153-177](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:153)。mutation producerは明示的にscope外。[s4-adjudication-plan-v2.md:99-100](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s4-adjudication-plan-v2.md:99)
- **放置時の成果物影響:** 文書化された journey だけではtest候補を非空ledgerから人間裁定へ送れない。production ledgerは空のまま緑になり、T-143の主要目的である陳腐test/guard回収はprototype止まりになる。
- **最小fix:** producer追加はせず、`inspect --draft` に完全なadvisory receipt skeletonを出し、docsへexact schemaと手作業手順を記載する。これを使った非空test候補のE2Eを追加する。そこまで持たないなら、v1ではreceiptをoptionalにする。

### RB-2 — BLOCKER: 非空ledgerは「軽量preflight」にならず、60秒timeoutと構造的に衝突する

- **根拠:** snapshotだけで6 Git subprocess。その後、候補・tokenごとに`git grep`、hit fileごとに`cat-file`、token×controlごとに全履歴`git log -S`を直列実行する。[tools/ruleops.py:312-356](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:312)、[tools/ruleops.py:623-647](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:623)、[tools/ruleops.py:687-718](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:687)。これを最大256候補で再計算する。[tools/ruleops.py:30-39](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:30)、[tools/ruleops.py:1361-1375](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1361)。runner全体は60秒で殺す。[tools/run_tests.py:524-530](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:524)
- **放置時の成果物影響:** 正当な候補を追加した瞬間にrc=15 timeoutとなり、空ledgerだけが実用的に通るgateになる。複数候補の人間裁定packageを維持できない。
- **最小fix:** snapshot単位でblob、grep、pickaxeをmemoizeし、hit blobはbatch取得する。`inspect`も全97/251件のinventoryを構築せず対象だけ読む。実測予算に合わせ候補/query上限を下げ、実履歴由来の非空複数候補を60秒内で通す境界を置く。

### RB-3 — MUST: M8の意図変異は現fixtureを生存できる

- **根拠:** M8 fixtureは同名`note.md`を2件作るが、どのblob内容にも文字列`note.md`を置いていない。[test_ruleops.py:551-561](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:551)。したがって `_unique_basename()` を恒真化してbasename tokenを常時追加しても、content検索と`-S`はいずれもrowを生成せず、assertはそのまま通る。[tools/ruleops.py:737-781](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:737)
- **放置時の成果物影響:** M8をkill済みと誤記録でき、曖昧basenameによる無関係hit・候補永久赤の回帰を検出できない。
- **最小fix:** 別blobへliteral `note.md`とその履歴を置き、unique gateを外した場合だけbasename signalが現れる単一理由fixtureにする。

### RB-4 — MUST: M5/M6が単一理由fixtureになっていない

- **根拠:** M6は第1候補をdeep-copyしてpath/blobだけ変更するため、第2候補には第1候補用receiptとreviewed signalsが残る。[test_ruleops.py:465-480](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:465)。cycle gateを外してもsignal mismatchまたは`receipt-target`で赤になる。[tools/ruleops.py:1080-1083](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1080)。M5もcontrol除外を広く外すとobservedとpickaxeの双方が変化する。[test_ruleops.py:428-448](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:428)。これは事前登録の「複数理由なら採用しない」に反する。[s4-adjudication-plan-v2.md:94-95](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s4-adjudication-plan-v2.md:94)
- **放置時の成果物影響:** mutation matrixの赤が対象gateの検出力を証明せず、恒真・冗長gateを12/12 killとして凍結できる。
- **最小fix:** M6は独立にvalidな候補2件を各自のreceipt/signalsで作り、cross-referenceだけを変える。M5はobserved/pickaxeを分割するか、一方が空のfixtureへ再照準する。

### RB-5 — MUST: real checkout dry-runは非空gateの実証になっていない

- **根拠:** inventory側はroot keyと`all(...)`だけで、`items=[]`でも恒真。inspect側もhard-coded pathの`kind == insight`だけである。[test_ruleops.py:697-745](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:697)。queryも`check`も非空production ledgerも通さない。
- **放置時の成果物影響:** synthetic producer/validatorの自己整合、実履歴のwall、default ledger接続が壊れてもreal-checkout acceptanceは通り得る。
- **最小fix:** 現HEAD由来の一時clone/worktreeで、独立literal hitと`git rev-parse` blobをpinし、`inspect --draft`から非空candidateを組み立てて`check`まで通す。inventoryは非空・既知path存在をassertする。

### RB-6 — MUST: replacement nodeとreceiptが実在・相互関係へ接続されていない

- **根拠:** 裁定はsymbolをinspect signalとして残すとしている。[s4-adjudication-plan-v2.md:33](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/insights/2026-07-29_t143-ruleops-wave/s4-adjudication-plan-v2.md:33)。実装は`file::任意文字列`、module file、blobだけを検査し、symbol実在を見ない。[tools/ruleops.py:1177-1199](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1177)。receipt内の`guard_path`/`failed_nodes`も、ledgerの`replacement_guards`/`replacement_nodes`と照合されない。[tools/ruleops.py:1095-1118](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1095)
- **放置時の成果物影響:** typoや架空node、無関係なmutation receiptを持つpackageが構造validとなり、人間裁定へ「代替防壁あり」と誤った材料を運ぶ。
- **最小fix:** 限定AST等でsymbol実在をadvisory signalとして出し、receiptのguard/failed node集合をledger参照と照合する。安全証明とは呼ばず、dynamic/未対応形は明示的にunverifiedとする。

### RB-7 — MUST: 「冒頭の正準marker」契約を実装していない

- **根拠:** docsは冒頭の正準markerを要求する。[docs/ruleops.md:85-87](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/ruleops.md:85)。実装は先頭64行のどこかにある文字列を、code fence・引用・否定文脈を区別せず受理する。[tools/ruleops.py:500-522](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:500)
- **放置時の成果物影響:** marker例を本文に引用したauthoritative insightをnon-authority候補としてpackage化でき、高価値証拠を誤ったretention裁定へ送る。
- **最小fix:** 先頭の明示front matterまたは固定metadata blockだけを解析し、code fence・重複・競合markerを拒否するnegative testを加える。

### RB-8 — SHOULD: default ledger pathが二重正本化している

- **根拠:** CLIの`DEFAULT_LEDGER`とrunnerの`_RULEOPS_LEDGER`が別定数で、runnerはCLI defaultを使わず同じliteralを再指定する。[tools/ruleops.py:28](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:28)、[tools/run_tests.py:100-101](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:100)、[tools/run_tests.py:515-522](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:515)。runner testは後者だけをpinし、両者の一致を検査しない。
- **放置時の成果物影響:** 将来のrenameで手動`check`とacceptanceが別ledgerを検査し、一方の空ledgerだけが緑になり得る。
- **最小fix:** runnerから`--ledger`を外しCLIのproduction defaultを単一正本にする。接続testはdefault利用をpinする。

### RB-9 — SHOULD: 空白だけの人間rationaleが通る

- **根拠:** `_string()`はlengthだけを見てtrimしない。[tools/ruleops.py:203-215](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:203)。candidateと全review rationaleにそのまま使われる。[tools/ruleops.py:964-980](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:964)、[tools/ruleops.py:1353-1357](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1353)
- **放置時の成果物影響:** `" "`だけで「全hitを人間が理由付きで裁定した」形を満たし、裁定packageに判断根拠が残らない。
- **最小fix:** `.strip()`後の非空を要求し、空白・制御文字だけのnegative testを加える。

### RB-10 — SHOULD: 引数エラーのstable reason-code契約が実装と不一致

- **根拠:** docsは引数エラーもstderrへ安定reason codeを出すとする。[docs/ruleops.md:93-95](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/ruleops.md:93)。しかし`parse_args()`は`try`の外で、argparse既定の英語`invalid choice`を出す。[tools/ruleops.py:1406-1408](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1406)。M11 testもその不安定文言を期待する。[test_ruleops.py:639-648](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:639)
- **放置時の成果物影響:** CLIを使う運用スクリプトがreason codeで失敗分類できず、Python/argparse版やlocale依存の文字列解析になる。
- **最小fix:** parser errorを`RuleOpsError("cli-args", ...)`へ変換し、rc=2・stable prefixをliteral pinする。

## positive controls

- Git操作はclosed read-only set、Git env scrub、optional lock無効化、replace/graft/shallow拒否になっており、削除系subcommandもない。[tools/ruleops.py:48-50](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:48)、[tools/ruleops.py:253-301](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:253)
- syntheticでは非空test/insight packageの成功経路自体は存在する。したがってvalidatorが数学的に「空しか受けない」わけではない。ただしtest側receiptはtest helper生成で、RB-1のproduction導線を補わない。
- runnerは deletion → RuleOps → submodule → xdist の順で、rc=13/15/14を分離する。targeted非発火、rc=15、stderr reason、timeout、後段非発火も静的にtest接続されている。[tools/run_tests.py:787-797](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:787)
- `human_approved:false`、禁止claimなし、候補集合全体のcycle検査は実装されており、削除安全を過大主張していない。
- living doc登録、docs map、output map、pytest-only allowlistはすべて接続済み。[tools/check_docs.py:47-51](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/check_docs.py:47)、[docs/README.md:28-29](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/README.md:28)、[output/README.md:73-75](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/output/README.md:73)、[orchestrator/tests/README.md:103-107](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/README.md:103)
- real-checkout testはworking-tree上の新規`_TOOL`を実際に起動し、before/after statusを比較するため、HEAD版scriptだけを見る恒真検査ではない。ただしRB-5のとおり検出内容はsmokeに留まる。
- M1〜M4、M7、M9〜M12には対応するliteral/negative test面がある。これは静的な接続確認であり、mutation killやpytest緑の主張ではない。

## scope 外の裁定候補

### RB-11 — MUST（scope外）: selection-neutral `PYTEST_ADDOPTS`で全走しても全preflightを迂回する

- **根拠:** `PYTEST_ADDOPTS`が空白以外なら無条件にnon-acceptanceとなる。[tools/run_tests.py:368-373](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:368)。したがって `PYTEST_ADDOPTS=-q python3 tools/run_tests.py` はdefault full targetを実行しながらRuleOps/deletion/submodule acceptance gateを外れる。
- **成果物影響:** 見た目が全走でもproduction ledger未検査の受入結果を記録できる。
- **裁定候補:** shared classifierと既存rc13/14の受理集合を変えるため、本waveで暗黙修正しない。selection-neutral addoptsを解析するか、default target時の非空addoptsをfail-closedにするかD97境界として裁定する。

### RB-12 — SHOULD（scope外）: rc=15 refusalはtask-run台帳へ残らない

- **根拠:** 全preflightは`IZANAGI_TASK_RUN_ID`取得と`_call_and_record()`より前にreturnする。[tools/run_tests.py:787-797](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:787)、[tools/run_tests.py:824-833](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:824)
- **成果物影響:** candidate driftやtimeoutで拒否された受入試行が再現可能なtask-run台帳から消え、stderrだけに残る。
- **裁定候補:** rc13/14も同じ既存設計なので、RuleOpsだけを局所変更しない。preflight-refusal eventをtask-run schemaへ加えるか、「pytest未起動なので非記録」を明文化するか横断裁定する。

既裁定のC-1（staged deletionとhuman approval receiptの機械束縛）、C-2（mutation producer）、nested test外延は依然scope外であり、本レビューから実装範囲へ戻していない。

## 総括

段6レビューBの判定は **NO-GO**。現在の空ledger canary、read-only境界、runner/docs接続は成立しているが、test候補のdocumented journeyが閉じず、非空候補の履歴scanは60秒予算に対してスケールせず、M6/M8とreal-checkout検査も要求された検出力を証明しない。

少なくともRB-1〜RB-7を直し、単一理由mutation matrixと実履歴由来の非空candidate acceptanceを親環境で実走するまでは、T-143を運用機構として完了扱いできない。今回pytestは非実走であり、緑の記録はない。