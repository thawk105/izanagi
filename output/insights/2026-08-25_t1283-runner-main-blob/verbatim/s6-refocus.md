| 所見 | closed・partial・regressed | 根拠 (file:line) |
|---|---|---|
| レビュー A 所見 1（M2、must-fix） | closed | main digest を明示し tip digest との差も固定した。[test_dev_wave_land.py:1534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1534)、[test_dev_wave_land.py:1540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1540) |
| レビュー A 所見 2（M5、must-fix） | closed | `locked_main != tested_main` と runner 差を作り、tested pair の lookup と着地成功を固定した。[test_dev_wave_land.py:1583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1583)、[test_dev_wave_land.py:1597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1597)、[test_dev_wave_land.py:1616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1616) |
| レビュー A 所見 3（完全 rollback） | closed | launcher の4負例・正例に加え、land の新しい優先順位テストも旧実装で赤になる。[test_acceptance_launcher.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:87)、[test_dev_wave_land.py:1646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1646) |
| レビュー A 所見 4（テスト分類） | closed | M2 は main digest で単一理由化され、M5 も locked/tested を分離した。非帰属互換負例は tip digest のまま別分類である。[test_dev_wave_land.py:1537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1537)、[test_dev_wave_land.py:1630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1630) |
| レビュー A 所見 5（恒真 SHA 再検査） | partial | helper が形式を保証する一方、main 側の再検査は残る。[dev_wave_land.py:838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:838)、[dev_wave_land.py:1082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:1082) |
| レビュー A 所見 6（launcher 順序） | closed | main、tip、equality の後にだけ runner を呼ぶ。[acceptance_launcher.py:436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:436)、[acceptance_launcher.py:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:441) |
| レビュー A 所見 7（実 Git reader／malformed 未検査） | partial | production 分岐は残るが、欠落テストは fake reader の例外であり実 reader を通らない。[acceptance_launcher.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:173)、[test_acceptance_launcher.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:169)、[dev_wave_land.py:843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:843) |
| レビュー A 所見 8（M1・M3・M4、禁止変更） | closed | 指定テストの oracle は維持され、schema v5 と素の `python3` も不変。[test_acceptance_launcher.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:133)、[test_acceptance_launcher.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:224)、[acceptance_launcher.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:22) |
| レビュー B 所見 1（複合故障、must-fix） | closed | 親の訂正どおり divergence を先行させ、checker lookup が呼ばれず恒久拒否となることを固定した。[s4-adjudication.md:211](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1283-runner-main-blob/s6re/s4-adjudication.md:211)、[test_dev_wave_land.py:1646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1646)、[test_dev_wave_land.py:1680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1680) |
| レビュー B 所見 2（既存受理経路） | closed | receipt 検証は active-plan／着地分岐より前で、matching child-green、非帰属、forward-main の正例も維持される。[dev_wave_land.py:5035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:5035)、[test_dev_wave_land.py:1451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1451)、[test_dev_wave_land.py:6831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:6831) |
| レビュー B 所見 3（型・初期化） | closed | main/tip の `None` guard 後に添字参照し、checker 変数も分岐前に初期化される。[dev_wave_land.py:1065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:1065)、[dev_wave_land.py:1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:1089) |
| レビュー B 所見 4（メモリ・早期診断） | partial | `tip_source` は equality 後も保持され、3回目の main 読取まで生存する。[acceptance_launcher.py:436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:436)、[acceptance_launcher.py:446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:446) |
| レビュー B 所見 5（共有 fixture） | closed | 引数既定は `None`、digest の既定は引き続き tested tip である。[test_dev_wave_land.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:254)、[test_dev_wave_land.py:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:354) |
| レビュー B 所見 6（名前重複・duration） | partial | test 収集構造と新 nodeid は正常だが、duration 台帳は射影外で未確認。[test_dev_wave_land.py:1646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1646)、[test_dev_wave_land.py:9724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:9724) |
| レビュー B 所見 7（自己申告との不一致） | closed | retryable 維持という旧指示は親が明示的に訂正し、新しい優先順位を現行契約として採用した。[s4-adjudication.md:211](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1283-runner-main-blob/s6re/s4-adjudication.md:211)、[s4-adjudication.md:223](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1283-runner-main-blob/s6re/s4-adjudication.md:223) |

### 変異 M1〜M5

- **M1: 殺す。** `test_main_tip_runner_blob_mismatch_is_rejected_before_execution` は divergent bytes を返し、runner を `_unreachable` にしている。[test_acceptance_launcher.py:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:140)、[test_acceptance_launcher.py:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:149)。equality を `_run_blob` 後へ移すと、現行の拒否 [acceptance_launcher.py:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:438) より先に `_unreachable` が発火して赤になる。

- **M2: 殺す。** 現行は main/tip object ID の不一致を [dev_wave_land.py:1084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:1084) で検出し、1088 で恒久拒否する。変異で equality を非帰属枝へ戻すと、child-green はその枝を通らない。受領証 digest は main blob と一致するため [dev_wave_land.py:1085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:1085) も通り、1130 の verification return まで進む。結果は着地成功となり、RC_AUDIT を期待する [test_dev_wave_land.py:1563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1563) が赤になる。別検査による先取りはない。

- **M3: 殺す。** 現行の revision 列は main、tip、main である。[acceptance_launcher.py:436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:436)、[acceptance_launcher.py:446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/acceptance_launcher.py:446)。main 指定を tip へ戻すと [test_acceptance_launcher.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:125) の exact revision 列が不一致になる。実行 buffer を tip 側 object へ替える変形は identity 検査 [test_acceptance_launcher.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:127) でも赤になる。

- **M4: 殺す。** tip 読取失敗は現在 runner 呼出し前に伝播する。[test_acceptance_launcher.py:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:200)。main bytes で代用すると処理が runner へ進み、`_unreachable` [test_acceptance_launcher.py:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_acceptance_launcher.py:211) が発火して赤になる。

- **M5: 殺す。** 現行 lookup は明示的に `tested_main` を使う。[dev_wave_land.py:1066](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:1066)。指定テストでは locked main の runner だけを変え、tested main/tip の runner は同一である。[test_dev_wave_land.py:1571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1571)、[test_dev_wave_land.py:1583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1583)。`tested_main` を呼出元から渡される `locked_main` [dev_wave_land.py:5041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:5041) に置換すると、共通 equality [dev_wave_land.py:1084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:1084) で恒久拒否される。spy は `[tip, locked_main]` となって [test_dev_wave_land.py:1616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1616) が最初に赤となり、成功期待 1617 も満たさない。

### fix の射程と新規破れ

`impl.diff` と現在の `git diff --no-ext-diff` は byte 単位で一致した。全 wave 差分は4ファイルだが、レビュー時の旧内容と最終差分を比較すると、訂正3件の差分はいずれも `test_dev_wave_land.py` 内である。射影には独立した fix 前 diff がないため fix-only delta 自体の `cmp` はできないが、観測可能な訂正箇所に production／launcher test の変更はない。

静的確認結果は次のとおり。

- fixture の既定は `runner_digest_revision or tested_tip` のまま。
- M2 の拒否期待、M5 の成功期待は維持され、反転・緩和・削除されていない。複合故障テストは純粋な追加。
- AST 走査では launcher 13 test、land 215 test。ファイル内・両ファイル間の test 名重複は 0。
- `_Repo.request` は186 call、明示 revision は6、既定利用は180。fix 前から増えた1件は新しい複合故障テストの既定利用である。
- `git diff --check` は rc=0。
- 私は pytest を実走していない。親報告の 304 passed / 1 failed の唯一の赤は既知 F57 と一致するため、本差分の回帰には数えない。

### 残る未閉鎖

いずれも nit であり、新しい must-fix はない。

- A5: `_runner_tree_entry` 後の main object ID 形式再検査は恒真のまま。
- A7: 実 `_read_runner_blob` の Git 非ゼロ分岐と、main runner の malformed `ls-tree -z` 分岐に直接テストがない。
- B4: equality 後も `tip_source` を保持する peak memory 増加と、早期 rc=70 の waiter 診断契約を固定する統合テストが残る。
- B6: test 名・収集形は静的に正常だが、新 nodeid の duration 台帳 coverage は射影外のため未確認。

## 総括

- 段6の must-fix 3件はすべて closed。
- M1〜M5 は現在の指定殺し手で静的に殺せる。
- M2 は main digest 化により equality 欠落だけで受理へ反転する。
- M5 は locked main と tested main の実 runner を分離し、置換変異を equality で拒否させる。
- fixture 既定、既存期待値、test 名に新しい破れはない。
- 残るのは A5、A7、B4、B6 の nit のみ。
- 私自身は pytest 未実走で、親の既知 F57 を回帰とは扱っていない。