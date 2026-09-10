# T-2579 — 承認済みmodule fixture変更の回収

D1936項43と `output/insights/2026-09-10_rulings-all-verdicts/README.md` に従い、
旧commit `559bcbc29cfa27412f103b608e8ac708dcfae6b9` の実装3file・5hunkだけを回収した。
開始mainは `c68d08d9e452138c383e9b92076bf91451912700`。
旧worktreeの途中mergeへ触れず、新しい専用worktreeと別Codex authorを使った。

実装は138行追加・5行削除。author出力を親が内容監査し、元の限定patchとのbyte一致を確認した。
実snapshotはmodule fixture実体ごとに1回取得し、function fixture用と返却時のdeep copyを保持する。
全30関数・展開後51nodeを既存real-repo inventory、parent-only集合、独立golden二集合へ登録した。
production timeout・走査範囲・判定内容・既存test本体は維持する。
較正、patch materialize、旧commitの裁定fragmentは回収しない。

起動時にT-2273のhandoffとrulingがt1259/conftestを所有外とすることを確認した。
T-1851・T-2417・T-2514・T-2525/T-2526・T-2581の実装所有と対象3fileは非交差だった。
後続mainは正式受入の取り込み時にも再照合する。

## 独立検証と主張の限界

plan、敵対相談2本、別author、独立review2本は全て終了rc0・出力検査rc0。
逐語は `verbatim/`、親の採否は `ruling.md`。
reviewの修正必須所見はゼロ。既存79test関数のAST一致、4集合各30登録を確認した。

旧commitの「同一workerへ集める」という説明は現行schedulerに適合しない。
現行conftestはprocess-memo以外のloadgroup suffixを除去し、reader間の同時走査は残りうる。
D1936が承認したmodule fixtureを回収したもので、全worker合計1回・timeout解消・速度改善は未証明。
CC合成実走の前提を増やさない。個別deep copy削除の変異検出力も主張しない。

## 関連走で確認した事実

親が同一実装差分のauthor checkout（開始main上のstaged差分）でT1259 fileを単独実走した。
`tools/run_tests.py orchestrator/tests/test_t1259_qsub_env_delivery_probe.py -q` は
991394.nqsvで51 passed、child rc0、pytest 17.09秒。性能比較ではない。

serialization fileの最初の単独走991395.nqsvは55 passed / 1 skipped / 1 failed。
writer監査が関数内でS4をimportする一方、既存site中立化fixtureはsetup時にcanonical
site_policyが未importだと何もしないため、compute向けlockとlinux期待が不一致になった。
当該nodeの単独再走はbounded localでlogin拒否となった。追加登録の比較は通っており、
T1259 fixtureはこの選択走では使われない。失敗を除外・hold登録していない。

既存site_policyを `-p orchestrator.campaign.site_policy` で先にimportし、
既存autouse fixtureを発火させたfile単独走は991410.nqsvで56 passed / 1 skipped、
child rc0、pytest 19.12秒。先行bounded localはメモリ上限に達し、runnerが自動dispatchした。
skipは既存の明示opt-in成長testであり、全件実走と呼ばない。
site_policyにはpytest hookもfixtureもなく、先読みで判定や期待を差し替えていない。
本修正対象のT1259には追加site偽装を課していない。正式受入にはこの先読みoptionを追加しない。

分類consumerの `test_acceptance_schedule_order.py`、
`test_dev_waves_isolation_contract.py`、`test_run_tests_shards.py` は親wave上で
991408.nqsv、271 passed、child rc0、pytest 55.37秒。
check_codex_agentsとcheck_docsはrc0。原ログは `focused-logs/`。

全変異の事前登録は `mutation-spec.json`。M1は正常R1の拒否、M2はdetached負例の受理、
M3は登録漏れによる独立golden不一致を狙う。M2は親の既存harnessによる一時変異で、
恒久production変更ではない。実測前のKILLEDや正式受入成功は記録していない。

固定anchor `e28a62d26f69cc8c48c6cbbc6427c8bc11a71aa6` で既存harnessを実走した。
collection991432、baseline991433はrc0。M1=991435、M2=991440、M3=991442は
各1 failed / 2 passedで、すべて期待した1nodeと一致しKILLED（3/3）だった。
R1 evidenceの拒否、detached負例evidenceの受理、r1登録欠落だけのgolden不一致を
失敗本文で確認した。終了rc0、git diff無差分・porcelain空で復元確認。
原stdoutとSHA・単一anchor・失敗nodeは `mutation-report.json`、
各投入は `mutation-attempts.json` にある。正式受入はこの記録時点では未実施。

anchorのprovenance全史監査は9444件、新規違反なし、rc0（既知56件は別枠）。

記録後のT1259全件と集合meta-test再走は52 passed、rc0。
正式acceptance-3はtested main `e4e5fe053a16d9f454f88904679f79f40ce42465`、
tested tip `79cc9fc0635a38b78e32389aeff63ad656175a23` で22591 passed / 68 skipped、
child-greenとなった。受領証は `acceptance-3.json`。
受入前の2回は文書merge競合とmain前進で本走前に停止した。
その後も並行landが進み、T2525/T2526は無競合で保持統合したが、日本語結果・考察文書との
phase3追記競合は親が両方保持で解消した。無競合mergeだけの受領証再利用条件を超えるため、
最終統合状態の正式受入は取り直す。実装3fileとproduction probeはこの処理で変更しない。

## 逐語の可逆正規化

git diff --checkが拒否した行末ASCII space 2字だけを除去した。可視文字・行数は不変。
次の物理行のLF直前へspace 2字を戻すと原bytesを復元できる。

| file（verbatim内） | 原bytes | 原SHA-256 | 復元する物理行 |
|---|---:|---|---|
| consult-a.md | 5056 | 7bc727290bf9a3edba5a61a800d4b362cb4b8b1866d68a3b64cce961658c7073 | 9,12,15,20,23,26,29 |
| review-b.md | 4444 | c7bdccff5261707944b1fc464148e0b362fa2573185a55c9014c9736cda6cfda | 9,10,11,14,15,16,19,20,21,24,35,36,37 |
