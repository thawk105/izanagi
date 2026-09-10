## 所見 1 — 受入全走で commit 起因の赤は予測しない

- **所見:** must-fix なし。静的に再検査した赤候補は次の4 node だが、いずれも赤になる根拠は見つからなかった。

  - `orchestrator/tests/test_verifier.py::test_dense_cycle4_clean_g2`
  - `orchestrator/tests/test_verifier.py::test_all_v2_fixture_files_have_clean_framing`
  - `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
  - `orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`

- **根拠 (file:line):** fixture の4 read・4 write は宣言数と一致し、DSG は `0→1→2→3→0` の4辺だけを作る（[trace_0.log:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/r9_dense_cycle4/trace_0.log:1)、[trace_1.log:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/r9_dense_cycle4/trace_1.log:1)、[dsg.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/dsg.py:81)）。fixture root 全体の `trace_*.log` を完全一致で見る検査は [test_verifier.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:298) だけで、`orchestrator/tests/` と `tools/` の悉皆検索でも別の件数・集合 pin は見つからなかった。duration ledger の未知 node は fallback cost 扱いであり（[conftest.py:1583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/conftest.py:1583)）、検査も coverage 90% 以上だけを要求する（[test_acceptance_schedule_order.py:704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_acceptance_schedule_order.py:704)）。

- **失敗する具体例:** fixture の辺または framing が想定と違えば最初の2 node、runner 収集が固定列挙なら3番目、duration ledger が完全一致契約なら4番目が赤になる。しかし現行実装はいずれにも該当しない。

- **提案:** 修正不要。親の受入全走では上記4 nodeを観測対象にする。

- **放置時の成果物:** production の `certified` 値・レポート・台帳の受理集合は不変で、テスト側だけが clean な長さ4巡回を落とす実装を新たに拒否する。

## 所見 2 — 素の runner でも新テストを収集する

- **所見:** 問題なし。`parse_trace_dir` の import と新テストの収集は pytest に依存しない。

- **根拠 (file:line):** repo root を `sys.path` に加えた後、`parse_trace_dir` を module top-level で importしている（[test_verifier.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:16)、[test_verifier.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:26)）。新テストはその名前を直接参照し（[test_verifier.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:137)）、素の runner は `globals()` の callable な全 `test_*` を動的収集する（[test_verifier.py:1980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:1980)）。

- **失敗する具体例:** import が pytest fixture 内だけにあれば素の runner で `NameError`、runner が固定リストなら新テストが未実行になる。どちらでもない。

- **提案:** 修正不要。

- **放置時の成果物:** 素の runner の受理集合にも新テストが入り、失敗時は exit 1 になる。`certified`・レポート・台帳値には直接変更がない。

## 所見 3 — commit message は差分と一致する

- **所見:** message の指定4主張はいずれも事実と一致する。nit として、README の「どの fixture も担っていない」という既知の stale 文は残るが、message はそれを未変更・T-2177所有と正確に記録している。

- **根拠 (file:line):**

  - 差分は2 trace、test、READMEの4 fileだけで、production verifier の変更はない（[s4-ruling.md:35](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/s4-ruling.md:35>)、[s4-ruling.md:46](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/s4-ruling.md:46>)）。
  - README 差分は表の r9 1行だけ（[fixtures/README.md:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/README.md:30)）。
  - `(txid, thid, commit)` の4組を exact に pin している（[test_verifier.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:137)）。
  - parser は file 名を列挙して各 file を読むだけで、C行の `thid` と file suffix を比較しない（[parse.py:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:250)、[parse.py:410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/parse.py:410)）。したがって「file 名と thid の対応までは pin していない」も正しい。
  - stale 文を本 wave で触らないことは段4裁定そのもの（[s4-ruling.md:25](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/s4-ruling.md:25>)）。

- **失敗する具体例:** T3 frameを `trace_0.log`へ移し、空の`trace_1.log`を残しても4組のassertと在庫pinは通る。messageはこの未固定範囲を隠していない。一方、READMEのstale文だけを読む利用者はr9の検出範囲を誤認しうる。

- **提案:** T-2176のmessage・差分は修正不要。stale文は段4裁定どおりT-2177の既裁定訂正に委ねる。

- **放置時の成果物:** `certified`・レポート・台帳値は変わらない。影響はREADME参照者が検査範囲を誤読しうる点だけで、commit自身の記録は正確。

## 所見 4 — trailer は規約どおり

- **所見:** 問題なし。実装面を変更するcommitにCodex `role=author`があり、trailerは連続した最終blockにまとまっている。

- **根拠 (file:line):** raw messageの24〜26行はCodex author、Claude manager、`Co-Authored-By`の順で空行なく連続している。規約は最終段落への配置と連続を要求し（[ai-provenance.md:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/docs/ai-provenance.md:10)）、test-onlyも実装面としてCodex authorを要求する（[ai-provenance.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/docs/ai-provenance.md:46)、[ai-provenance.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/docs/ai-provenance.md:51)）。各slugも許可文字集合内にある（[ai-provenance.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/docs/ai-provenance.md:31)）。

- **失敗する具体例:** Codex author行が無い、または`Co-Authored-By`との間に空行があればprovenance監査対象になるが、実際のblockにはない。

- **提案:** 修正不要。Git trailer parserやprovenance checkerは本レビューでは実走していないため、親の実測結果を正本とする。

- **放置時の成果物:** provenance台帳からcommitはCodex author＋Claude managerとして一意に参照でき、productionの受理集合・レポート値には影響しない。

## 所見 5 — `_V2_FIXTURE_FILES` の順序は正しい

- **所見:** 問題なし。実ファイル29件のPython `sorted()`順とtupleが完全一致する。

- **根拠 (file:line):** 追加行は既存r8の4 fileの後に `r9.../trace_0.log`、`trace_1.log` の順で置かれている（[test_verifier.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:289)）。検査は実集合を`sorted(actual)`してtupleと比較する（[test_verifier.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:298)）。静的な実ファイル列挙も同じ29件・同順だった。

- **失敗する具体例:** r9をr8より前へ置く、`trace_1.log`を先に置く、または片方を登録しないと`test_all_v2_fixture_files_have_clean_framing`が赤になる。

- **提案:** 修正不要。

- **放置時の成果物:** fixture在庫の受理集合は実ファイル29件と一致し、r9の2 fileを共有fixtureとして受理する。`certified`・レポート値は不変。

## 所見 6 — 他 wave との現在の衝突はない

- **所見:** 問題なし。現在登録されている他の`.claude/worktrees` 21件と、関連する`.codex/worktrees` 31件について、対象pathのbranch固有tip差分・未commit差分は0件だった。

- **根拠 (file:line):** 各tipについて`merge-base main <tip>..<tip>`の`git log`と`git diff`、各worktreeの`git status -- orchestrator/tests/test_verifier.py orchestrator/tests/fixtures`を確認した。T-1851とT-2145ではmerge commitがlogに現れたが対象pathのnet diffは空。特に名前上もっとも近い`worktree-dev-wave-t2191-verifier-parallel`はtip `24b31d2a3`のままで、対象pathのcommit・未commit変更とも無い。mainもT-2176起点以後の対象path差分は無い。

- **失敗する具体例:** 別waveが同じREADME表位置や`_V2_FIXTURE_FILES`末尾を変更していればmerge conflict、r9を重複登録すれば在庫完全一致nodeの赤が起こりうるが、現在その実体はない。

- **提案:** 現時点でwave間調整は不要。

- **放置時の成果物:** branch tip統合によるfixture参照の上書き・重複は予測されず、certified判定・レポート・台帳の値や受理集合は変わらない。

## 総括

must-fixはない。commit起因で受入全走が赤になるnodeは静的には予測しない。最も重い残差は、T-2177所有として意図的に残したREADMEのstale文だけであり、T-2176のcommit message自体は正確である。他waveとの現在の衝突もない。

pytest、素のrunner、provenance checkerはいずれも本レビューでは実走しておらず、実測合格は主張しない。