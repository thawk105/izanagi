## 読んだ資料

指定された9資料はすべて読取可能でした。テストは実行していません。

- [s4-adjudication.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/prompts/s4-adjudication.md)
- [s5-author.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/prompts/s5-author.md)
- [実装子の完了報告](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s5-author.md)
- [s5-diff.txt](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/logs/s5-diff.txt)
- [focus-consumers.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/logs/focus-consumers.md)
- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py)
- [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py)
- [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh)
- [p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_b4_closed_critic.py)

## must-fix (成果物影響つき)

1. `[セッション死・救出]` `[手順漏れ]` `[テスト代表性]` 最終 file 名が内容完成前に公開され、強制 kill・同一 digest の並行 writer に耐えない。

   [p3_s4_loop.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:431) は supply → meaning → admission の順に処理し、[p3_s4_loop.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:445) で最終名を直接 `open("xb")` してから write・flush・file `fsync` しています。したがって次の実在する窓があります。

   - `open` 後、write/fsync 前の killで、空または途中までの最終 file が残る。
   - meaning-red のとき、supply 保存後・meaning 保存前の killで、拒否本文を持つ record が残らない。
   - 同じ digest の別 driverは、先行 writerが未完成でも `FileExistsError` になり、修復せず終了する。先行 writerがその後 killされると、不完全 fileだけが固定化される。
   - 同じ recordの再試行も既存 fileの内容を検証しないため、過去の途中 fileを回復できない。

   job bodyの `sync "$evidence_root"` は、driver開始前の [p3_s4_loop_pegasus.sh:578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:578) と、通常の `EXIT` trap内の [p3_s4_loop_pegasus.sh:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:153) だけです。SIGKILLでは trapは実行されません。また、driver自身はparent directoryをfsyncしていません。

   追加テストも、異なる digest の逐次再試行とfile `fsync` の呼出回数しか検査しておらず、同一 digest、並行 writer、途中 kill、directory durabilityを通しません（[s5-diff.txt:353](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/logs/s5-diff.txt:353)、[s5-diff.txt:452](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/logs/s5-diff.txt:452)）。

   **成果物影響:** scheduler killまたは同一 digest の競合時に拒否本文が欠落・破損し得るため、このwave唯一の耐久成果を満たしていません。

## real だが scope 外

1. `[ドリフト]` job bodyがcanonical化したrootを元の環境変数へ再exportしていない問題は実在します。

   raw値は [p3_s4_loop_pegasus.sh:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:102) で検査され、canonical値はline 111でshell変数 `evidence_root` にだけ入ります。その後line 212でrepoへ`cd`し、driverは [p3_s4_loop.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:424) で元の `IZANAGI_S4_EVIDENCE_ROOT` を読みます。

   - 絶対path・末尾slashは同じ場所へ到達する。
   - final-component symlinkと不在directoryはjob bodyが拒否する。
   - canonical rootへの書込権限は、driver前のqstat証拠とprebuild receipt作成で実際に使用される。
   - 相対pathだけは、job開始cwdでの検査・canonical rootと、repoへ`cd`した後のdriver解釈が分岐する。driverのfileが別場所へ出るか、3件とも書込失敗になる。job側の`sync`もcanonical rootにしか作用しない。

   親裁定が明示的にscope外・裁定パッケージ送りとした事項です。

   **成果物影響:** 相対値が投入された場合、job evidence rootに拒否本文が残らない可能性があります。

## refuted (実装が正しい点)

- 通常の非0終了では、各fileをflush・file `fsync`した後に閉じ、`EXIT` trapがevidence filesystemを同期します。強制 killが無い経路では永続化経路があります。

- file名はproduction recordでは固定集合のarm名とlowercase SHA-256に閉じています。armは [condition_meaning_gate.py:1019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1019)、digestはline 1034および4031で拘束されます。最大component長は supply 104、meaning 100、admission 94 bytesで、文字もASCII英小文字・hyphen・hexだけです。

- 異なるdigestの2回目は別名になり、`xb`なので前回を上書きしません。同じdigestの既存fileが完全なら、同じcanonical recordの一部として再利用できます。ただし途中fileを回復できない点はmust-fixです。

- `_run_process` はtimeout、実行不能、非0 rc、rc=0かつstderrありの4経路でargvを追加し、成功経路はargv整形を呼びません（[condition_meaning_gate.py:1576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1576)）。実process正例も実際のargv要素・rc・stderrを名指ししており、`[恒真ゲート]` の再発は見当たりません。

- `p3_s4_loop.py` はbase/sort/trigger共通のprojection closure memberです（[p3_b4_closed_critic.py:632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_b4_closed_critic.py:632)）。live hash比較はlines 687–707、production factoryではlines 1268–1285、receipt再検査ではline 1679で発火します。ただし親実測ではrepoにcommitted admission recordがなく、固定済み旧hashを受入全走で供給する経路もありません。したがって、今回の編集だけでrepoテストを赤にするstale golden consumerは、射影資料からは確認できません。テストを実走して緑とした判断ではありません。

- `condition_meaning_gate.py` はB-4 projection closure memberではありません。失敗detailが変わるため、evidenceを含めて算出するred arm digestは変わりますが、reason code・terminal status・admission判定は不変です。`focus-consumers.md` の直接consumer列挙にも、旧digest固定値との比較を示す証拠はありません。

- 差分は許可された4ファイルだけです。`[権限逸脱]` は見当たりません。

- 完了報告はpytestを緑と申告せず、`child_started=false`・未実走と明記しています。実走nodeidの捏造はありません。

## 受入台帳へ登録すべき nodeid

追加された9件すべてが登録対象です。

- `orchestrator/tests/test_condition_meaning_gate.py::test_run_process_real_failures_report_exact_argv_and_stderr`
- `orchestrator/tests/test_condition_meaning_gate.py::test_run_process_timeout_and_execution_failures_report_exact_argv`
- `orchestrator/tests/test_condition_meaning_gate.py::test_run_process_argv_detail_is_bounded_and_marks_truncation`
- `orchestrator/tests/test_condition_meaning_gate.py::test_run_process_success_returns_completed_process_unchanged`
- `orchestrator/tests/test_p3_s4_loop.py::test_condition_gate_rejection_persists_records_by_digest_across_retry`
- `orchestrator/tests/test_p3_s4_loop.py::test_condition_gate_rejection_without_evidence_root_does_not_write`
- `orchestrator/tests/test_p3_s4_loop.py::test_condition_gate_unwritable_destinations_preserve_gate_rejection`
- `orchestrator/tests/test_p3_s4_loop.py::test_condition_gate_serialization_failure_preserves_gate_rejection`
- `orchestrator/tests/test_p3_s4_loop.py::test_condition_gate_green_path_does_not_read_environment_or_write`

新規test fileはないため、file集合列挙型の自走harnessに新しいfile登録は不要です。ただし、台帳被覆meta-testにはこの9 nodeidの登録結果が反映される必要があります。

## nit

- `[手順漏れ]` 完了報告line 50は「追加8 nodeid一括」と書く一方、差分と同報告line 57は9 nodeidです。緑申告ではないため成果物への直接影響はありませんが、親が台帳登録数を誤らないよう9件を正とすべきです。

- 同じ完全なrecordが2度出た場合、2回目は`FileExistsError`として拒否本文にwrite failureが付くだけで、二度目の発生事実は別artifactになりません。今回の成果物要件は「本文が残ること」であり、発生回数の証明ではないためnitです。

## 総括

must-fixは1件です。通常の非0終了では証拠を残せますが、最終名への直接書込みにより、強制kill・同一digest競合・meaning-red途中終了で拒否本文を失う経路が残っています。このままではwave唯一の耐久成果を達成したとは判定できません。

テストは未実走です。受入台帳の正しい追加数は9 nodeidです。