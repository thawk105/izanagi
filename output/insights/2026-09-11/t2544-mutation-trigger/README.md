# T-2544 条件15の局所訂正

authority: none
default_effect: no-state-change

## 裁定と範囲

正本は `docs/decisions.md` D1936項31、実害の記録は
`docs/archive/worklog-phase3-0910-1410.md` のT-2544。
fixゼロのT-2503でDW-M07のrunner契約に到達せず中止した穴を、条件15の訂正で閉じる。
DW-M07本文、段構成、権限、correctness受理集合、byte予算、検査数は変更しない。

親が入口の「fix 後に」だけを削除し、Codex authorがcheckerの条件15pinと、既存テストの
入口実byte数pinを整合した。実byte数は9517から9507へ減り、上限9520と9521の超過拒否は不変。
`codex_reasoning_ab.py` のwhole-file pinは固定BASE_COMMITの歴史実験に属し、追随対象でない。

## 所有と検証方針

開始時に登録worktree、main handoff、外部handoff、裁定inbox、稼働workerを照合し、
今回の条件15・checker pinを所有する別稼働waveは見つからなかった。
DW-C00の既定軽量版。設計択一、correctness gate、受理集合の変更がないため段2/3とreview子を省略。
実装とfixは別Codex subprocessに委譲し、親が全差分を照合した。

authorはgpt-6-astra/medium、workspace-write、accepted/rc0、出力検査rc0。
子のテストはqstat preflight失敗rc16、child_started=falseで実走0。
親初回の関連2file走は1 failed、588 passed、8 skipped。唯一の赤は入口実byte数pinの追随漏れ。
ユーザー明示の既存pin同時整合の範囲でfixを追加し、上限・plus-one拒否・assertは維持した。
fixも同じmodel/effort/sandboxでaccepted/rc0、出力検査rc0。子の未実走を成功とは数えない。
親の訂正後test_check_docs.py単独走は574 passed、3 skipped、12.86s、request 991690.nqsv、rc0。
3 skippedは既存growth holdであり解除していない。byte-pin所見は親実走によりclosed。

## 変異事前登録の訂正

初版はtest_real_repo_cleanを期待nodeに指定したが、親焦点走で既存growth holdと確認した。
初版は実走0件のまま取り下げ、D753に従いholdを維持する。実repoは必須check_docs明示実行で検証する。
既存の非hold test_synthetic_repo_baseline_cleanへ再照準し、次の2件を本走前に登録した。

- M1: 既存合成fixtureの条件15セルだけ旧文言へ変更。正しいcheckerが契約不一致を拒否する。
- M2: checker条件15を旧pinへ変更し、同じfixtureセルだけ正しい新文言に固定する両層変異。
  fixtureがchecker定数から共生成されるmaskを外し、旧pinによる正常文言の過剰拒否を検出する。

両者の期待失敗集合は `orchestrator/tests/test_check_docs.py::test_synthetic_repo_baseline_clean`
の1node、KILLED。恒久fixture、assert、テストを追加せず、既存harnessが固定commitの使い捨て木で走らせる。
原登録は `mutation-spec-initial.json`、再登録は `mutation-spec.json`。

## 変異結果と復元

anchorは `3293e2bd89aa837c9bf5385828829d93df02f2a5`。
baselineはPASSED、M1/M2は2/2 KILLED、期待node完全集合一致。
どちらもcheckerの違反は条件15の不一致1件だけで、他のgateによるmaskはなかった。
collection/baseline/M1/M2は991705/991709/991722/991729.nqsv。
job stdoutのpytest所要はbaseline 1.70s、M1 1.58s、M2 1.33s。
baselineのrunner所要548.741sは投入待ち込みであり、pytest所要として使わない。

`mutation-ledger.json` がraw結果、`mutation-attempt.json` が投入の記録、
`mutation-wrapper-receipt.json` が復元・撤去の記録。
wrapper rc0、terminal_ledger=true、shared_snapshot_matches=true、teardown_completed=true。
dispatch生証拠はrepo外の
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2544-mutation-trigger/mutation-ledger.json.dispatch-evidence/`
へ既存wrapperが退避した。

## 終端の自己改善

`docs/skill-self-improvement.md`を再読した。追加改善候補はなし。
byte pinの追随漏れは既存DW-O26の適用、held nodeの事前登録訂正はD753の適用で解決した。
本題以外の手順・gate・検査・台帳の機構は追加しない。
