## 所見 1: 共有 scratch の削除が並列テストと競合する

**real／must-fix。**

判定材料: `test_mocc_mutation_proof.py:93–112` は共有 `.scratch-t2772` の存在確認を所有権判定に使い、作成した worker が最後に親ディレクトリを削除する。他 worker の一時ディレクトリが残っていると失敗する。親の `focus-1.log:17–58` で、48 workers 実行中の `scratch.rmdir()` が `ENOTEMPTY` となり、**303 passed／1 failed／2 skipped** を実測している。

**成果物影響:** 新 JSON が正しくても、並列受入が scratch の競合で赤になり、wave 1 を受理できない。

是正案（逐語、`orchestrator/tests/test_mocc_mutation_proof.py:93`）:

> 「共有 `.scratch-t2772` と `created` 判定を削除し、`tempfile.TemporaryDirectory(prefix=".scratch-t2772-", dir=_ROOT)` が所有する固有ディレクトリを直接 source root にする。共有親への `rmdir()` を削除する。」

検査の直列化や例外の握り潰しは不要。

## 所見 2: 焦点走の場所・赤の内訳・consumer 除外の証跡を区別する必要がある

**real／nit。`--deselect` 未使用との断定は不確実。**

判定材料:

- 依頼の「login」に対し、`focus-1.log:2–10` は **gen_S、request 5029.nqsv** の実行を記録している。
- `s5-author-1.md:62` の「JSON 不在のみ」は author 自身の検査報告。親の焦点走の赤は所見 1 であり、同じ結果として扱えない。
- 焦点走ログには起動 argv と `--deselect` の記録がない。consumer が失敗一覧にないことだけでは、R8 指定の明示除外を証明できない。
- 現在の `git status --short` は空だが、`.scratch-t2772` は空ディレクトリとして残存している。Git は空ディレクトリを表示しない。author 時点の削除報告を虚偽とする根拠にはならない。

是正案（逐語、`s5-author-1.md:71` に対応する親 handoff）:

> 「親焦点走は gen_S／5029.nqsv、303 passed・1 failed・2 skipped。失敗は共有 scratch の削除競合。consumer の除外 argv を記録し、compute 後は除外なしの焦点走、その後に受入全走を行う。」

## 所見 3: 登録簿閉包の漏れ・過剰登録は確認されない

**refuted／nit（修正不要）。**

判定材料:

- AST 再集計は `_DEFINE_SPECS` **39**、witness **15**、CXX_FLAGS route **17**。`condition_meaning_gate.py:73,249` と author 報告 `:41` が一致。
- cross-product pin は **35／39／25／25**（`test_ccbench_spawn_sites.py:3469,3472,3496,3505`）。
- 新 allowlist entry に rr0 のコメントがある（同 `:64–65`）。新 module の直接 subprocess 呼出しは `_run_trace:205` の一箇所のみ。
- build authority の二登録（`test_p3_build_authority_cli.py:165,183`）、B-3 entry（`test_p3_s4_loop.py:7923`）、W/U 四定数の検査（`test_ccbench_spawn_sites.py:4116`）が揃う。
- 統合 diff に `_DEFERRED_GATE_MEMBERS` の変更、旧 `_run_checked`／`_install_dependency` の重複登録はない。
- `_run()` と main 呼出しがあるため、plain-runner の文字列契約を満たす（新 test `:493,511`、`test_plain_runner_coverage.py:35`）。
- duration ledger の既定 weight 1 秒は author 報告 `:69` による。ledger 本体は射影外のため独立確認は不確実。今回の追加登録必須とは判定しない。

是正案（逐語、`s4-ruling.md:49`）:

> 「登録簿の追加修正なし。旧 helper の再登録、deferred lineno の更新、plain-runner allowlist の追加を行わない。」

## 所見 4: compute 配線に明白な新規阻害はないが、成功の実証は未完了

**配線欠陥の疑いは refuted／nit。実 gate 成功は不確実。**

判定材料（`s3_mocc_mutation_proof.py`）:

- site evidence、heavy-work 拒否 rc=2、単独占有確認が依存準備前にある（`:493–505`）。benchmark 直前にも確認する（`:313`）。
- cache は絶対 path を要求し、既存 dependency helper に渡す（`:504,534`）。
- checkout の context 内で build → run → verify を完了する（`:542–554`）。
- 新 driver ID、macro の CXX_FLAGS 供給、verifier cwd／root は指定どおり（`:134,177,221–227`）。
- TRACE=0 の build 名 `trace0-base`／`trace0-inst` は等長（`:556–564`）。
- JSON 既定出力先も指定どおり（`:502`）。
- generic dispatch は clean env（`dispatch_compute.py:154–159,1442`）。新 driver 自身には `PBS_JOBID` 必須条件の追加はない。ただし、射影外の再利用 helper 内部までの成立は今回断定できない。
- 新規 configure 引数に未使用 CMake 変数の追加は見られない（`:170–180`）。再利用 `_common_configure_args` と実 gate の成功は、author も未確認とする（報告 `:71`）。

120／900 秒は R6 と一致するが、上限和は **36,720 秒**。gen_S 3600 秒内の完了保証にはならない。先行して分割機構を追加する理由にはならない。

是正案（逐語、`s5-author-1.md:71`）:

> 「compute で実 condition gate と36走を確認するまで、実行可能・時間内完了を実証済みと記さない。時間不足の実測が出た場合だけ R6 の最小分割を検討する。」

## 所見 5: 要求外の機構はなく、経過時間の記録だけ plan から落ちている

**過剰実装の疑いは refuted。経過時間の欠落は real／nit。**

判定材料:

- 統合 diff は新規3・既存7の計10ファイルで author 報告と一致。旧 driver／旧 proof test は file 集合に含まれず、旧14 check・4 patch・3 witness を変更していない。
- 32 check（driver `:88–106`）、36走（`:72–87`）、11 test node は R4／R8 に対応する。成果物影響を説明できない追加 node は見つからない。
- resume、分割、統合、汎用台帳、template、`n1_*` は追加されていない。
- `legacy_proof` は path／sha256 のみ（`:516`）。integrity は raw record 内に保持し、consumer が要約との一致を検査する（test `:353,369–373`）。
- `s2-plan.md:526` は各 stage の実経過時間を記録するとするが、process record（driver `:194–239`）にはない。32 check の受理集合への影響は示せないため must-fix にはしない。

是正案（逐語、`s2-plan.md:526`）:

> 「各 stage の実経過時間の記録は現実装にないため、実装済みとは報告しない。追加する場合も局所的な時間記録に留め、汎用台帳を導入しない。」

## 総括

**NO-GO。must-fix は共有 scratch の削除競合の1件。**

- **削除すべき要素:** test の共有 scratch 所有権判定と共有親 `rmdir()`。production の要求外機構は確認されない。
- **閉包の追加一覧:** なし。R7 とレンズ B の登録先・件数 pin は揃っている。
- **報告との不一致:** 実装ファイル数・登録件数は一致。親焦点走は login ではなく gen_S、赤は JSON 不在ではなく scratch 競合。author 自身の過去結果とは区別する。明示 `--deselect` は提示ログから確認不能。
- **残る確認:** 修正後の並列焦点走、compute の新 JSON 生成、consumer を含む焦点走、受入全走。

本レビューでは pytest・build・benchmark を実行していない。