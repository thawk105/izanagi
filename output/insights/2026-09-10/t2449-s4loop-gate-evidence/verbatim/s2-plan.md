## 読んだ資料

指定された8資料はすべて読取可能だった。別 checkout は読んでいない。

- 親 brief: [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/prompts/s1-brief.md:1)
- gate 実装: [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:327)
- loop driver: [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:378)
- Pegasus job body: [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:1)
- 既存テスト2本: [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_condition_meaning_gate.py:1)、[test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_p3_s4_loop.py:1)
- 前 wave 一次資料: [README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/output/insights/2026-09-08_t2406-s4loop-gflags-prologue/README.md:33)
- 失敗実物: [job.stderr](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/output/insights/2026-09-08_t2406-s4loop-gflags-prologue/evidence/attempt-0001/job.stderr:13)。実際に本文は line 26 の `supply=preprocess-failed meaning=declared-meaning-observed` だけで、argv・stderr detail は無い。

P1b 検証のため、repository root 全域（`.git` を除き、`external/` も別途検索）を `ConditionArmRecord`、`canonical_json()`、`record_digest`、`admission_digest`、`record_ids`、`preprocess-failed`、`sha256/hash/digest`、`golden/freeze/frozen/manifest/prereg`、`condition-gate/{arm}/{64hex}` で検索した。

## 実装プラン (file:line)

最重要結論として、後述の P1b は反証された。このため親 brief の指示どおり、採用プランは「driver 側だけ・argv 追記断念」へ後退させる。

- [p3_s4_loop.py:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:378) の直前に、red 専用の小さい保存 helper と固定ファイル名を置く。

  - `condition-gate-supply-record.json`
  - `condition-gate-meaning-record.json`
  - 各ファイルの bytes は、それぞれ `record.canonical_json().encode("ascii")` そのものとし、改行や外側 envelope を加えない。serializer は [condition_meaning_gate.py:782-790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:782)。
  - `os.open(..., O_CREAT|O_EXCL|O_WRONLY[, O_NOFOLLOW], 0o600)`、flush、file `fsync` とする。既存ファイルを上書きしない。
  - 2 arm は独立に保存を試み、I/O エラーを収集する。一方が成功し他方が失敗した場合、成功済みの証拠は消さない。

- [p3_s4_loop.py:404-411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:404) は admission 計算を一切変えず、`if not admission.admitted` 内だけを変更する。

  1. 環境変数 `IZANAGI_S4_EVIDENCE_ROOT` が設定されていれば両 record を保存する。
  2. その成否にかかわらず必ず `RuntimeError` を送出する。
  3. 本文へ現在の reason code に加えて、`supply_detail={supply.evidence.get("detail")!r}` と `meaning_detail={meaning.evidence.get("detail")!r}` を載せる。
  4. 保存失敗時は `evidence_write_failures=...` も加え、最初の `OSError` を `RuntimeError` の cause にする。
  5. [p3_s4_loop.py:412-415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:412) の green 戻り値は変更しない。

- [condition_meaning_gate.py:1559-1588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1559) は本 wave では編集しない。argv 追記案は P1b の明示条件により採用不能。

- job body は `IZANAGI_S4_EVIDENCE_ROOT` を必須環境入力として列挙・検査している（[p3_s4_loop_pegasus.sh:17-24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:17)）。directory を検査し canonical な shell 変数へ解決するのは [同:99-112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:99)、driver 起動は [同:580-592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:580)。

  ただし、スクリプト内に `export IZANAGI_S4_EVIDENCE_ROOT=...` という明示行は無い。qsub から環境として入った export 属性が子 Python へ継承される形であり、canonical 化したローカル変数 `evidence_root` は再 export されていない。採用プランでは shell を変更せず、Python は指示どおり `os.environ` の元の名前を読む。

- offline configure 引数を gate へ渡す現行 seam は [p3_s4_loop.py:1825-1837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:1825)。ここも変更しない。

## (P1b) red record の hash 束縛の有無

**断定: 存在する。したがって依頼 (2) の `_run_process` への argv 追記は採用不能。**

区別すると、`canonical_json()` を直接 `sha256()` する live コード経路は見つからなかった。しかし、red record の canonical JSON を内包する過去の実測ファイルを whole-file SHA-256 で凍結した manifest が repo 内に存在する。依頼が「凍結 manifest も含め、存在すれば不採用」と定めているため反証になる。

- record 自身の動的 proof chain:

  - `ConditionArmRecord.canonical_json()` は [condition_meaning_gate.py:656-677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:656)。
  - `evidence` を含む payload を canonical SHA-256 にして `record_digest` / `record_id` を作るのは [同:1009-1045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1009)。
  - consumer は同 payload から digest を再導出する [同:3979-4024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:3979)。
  - admission は record ID 群をさらに hash する [同:4074-4088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:4074)。これは期待値との固定比較ではないが、detail を変えれば red record ID と admission digest が連鎖して変わる。

- red canonical JSON の凍結:

  - T2228 probe は `record.canonical_json()` を result 内へ逐語格納する [t2228_driver_gate_liveness_probe.py:353-364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:353)。
  - 実物の red canonical records は attempt A の [repro.json:238-309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/attempt-20260907a/repro.json:238)、attempt B の [repro.json:316-387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/attempt-20260907b/repro.json:316)。
  - その full result を SHA-256 で束縛する manifest は [full-file-sha256.json:1-10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/full-file-sha256.json:1)。README も full evidence の所在と hash を明示する [README.md:239-247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/output/insights/2026-09-07_t2228-driver-gate-liveness/README.md:239)。
  - 同 result は producer source `condition_meaning_gate.py` 自体の hash も保持する [attempt B repro.json:457-473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/attempt-20260907b/repro.json:457)。

- golden / 事前登録:

  - red record digest、`preprocess-failed` canonical bytes、`ConditionArmRecord` を固定する test golden や preregistration は検索ヒットなし。
  - [test_condition_meaning_gate.py:1756-1777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_condition_meaning_gate.py:1756) は動的な ID・digest・admission 関係だけを検査し、固定 digest を持たない。
  - B4 preregistration は別物で、projection hash の書式と live 再導出を規定するだけである [phase3-b4-reflux-ablation-preregistration.md:242-257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/docs/phase3-b4-reflux-ablation-preregistration.md:242)。

`evidence.detail` への argv 追加は green record bytes を動かさない。`_run_process` の detail は失敗を raise する分岐だけにある [condition_meaning_gate.py:1575-1587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:1575)。供給 arm はその例外だけを red detail へ写す [同:2553-2571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:2553)、meaning arm も同様 [同:3321-3334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:3321)、[同:3396-3408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:3396)。green record はそれぞれ別の成功分岐で組み立てる [同:2623-2664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:2623)、[同:3335-3364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:3335)、[同:3409-3438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/condition_meaning_gate.py:3409)。

したがって技術的には red-only に閉じられるが、凍結 red bytes の存在という親の禁止条件が先に効く。

## 失敗時・未設定時の挙動

- evidence root が正常: 両 arm の canonical bytes を create-only で保存してから、元の admission rejection を `RuntimeError` として送出する。
- directory 不在・権限不足: 各保存を試みて `OSError` を収集し、最終的には必ず gate rejection の `RuntimeError` を送出する。message に両 arm の reason/detail と保存エラーを残す。
- 既存 file: `O_EXCL` により上書きせず失敗扱いとする。既存 bytes は不変。もう一方の arm は独立に保存を試みる。
- 一方だけ保存済みで後続が失敗: 成功済み証拠は削除しない。partial であることを RuntimeError に記録する。
- `IZANAGI_S4_EVIDENCE_ROOT` 未設定または空: 保存を省略し、`evidence_root=unset` を RuntimeError に載せる。従来どおり gate は拒否され、ローカルテストや他 driver に新しい directory 要件を課さない。
- green: [p3_s4_loop.py:407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:407) の red 分岐に限定するため、環境変数の参照もファイル書込みも行わない。受理集合・reason code・admission 判定は不変。

## テストの設計

[test_p3_s4_loop.py:80-110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_p3_s4_loop.py:80) の既存 condition-gate 契約群へ、fixture 引数を持たない次の4 test を追加する。

- `test_condition_gate_rejection_persists_both_arm_records_and_details`

  fake supply/meaning/admission を返すよう依存だけを patch し、両ファイルが各 `canonical_json().encode("ascii")` と byte exact、RuntimeError が両 detail を含むことを検査する。

- `test_condition_gate_rejection_io_failures_remain_rejections`

  directory 不在、`PermissionError`、既存 target の3ケースを内部で順に検査する。すべて `RuntimeError`、元の reason/detail 保持、既存 bytes 不変、可能なもう一方の保存試行を要求する。

- `test_condition_gate_rejection_without_evidence_root_still_raises`

  環境変数を除去し、ファイル操作なしで同じ admission rejection が送出されることを検査する。

- `test_condition_gate_green_path_has_no_rejection_evidence_side_effect`

  `admitted=True` で evidence root が空のまま、既存 return shape が [p3_s4_loop.py:412-415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:412) と一致することを検査する。

P1b により `_run_process` を変えないため、[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_condition_meaning_gate.py:1559) への argv test は追加しない。

新規 test file は作らない。既存2ファイルは自走 harness を持つ。

- condition gate test: [test_condition_meaning_gate.py:2756-2762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_condition_meaning_gate.py:2756)
- loop test: [test_p3_s4_loop.py:8496-8509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_p3_s4_loop.py:8496)
- 自走 harness メタテスト: [test_plain_runner_coverage.py:25-41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_plain_runner_coverage.py:25)、[同:60-74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_plain_runner_coverage.py:60)

受入台帳は [acceptance_duration_ledger.json:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/acceptance_duration_ledger.json:2) へ上記4 nodeid を登録し、`nodeid_count` も更新する。手書き時間ではなく、JUnit 実走後に正本 producer [update_acceptance_duration_ledger.py:57-95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/update_acceptance_duration_ledger.py:57) の `--add-only` を使う。既存 entry bytes を保った追加処理は [同:362-441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/update_acceptance_duration_ledger.py:362)、出力処理は [同:476-508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/update_acceptance_duration_ledger.py:476)。

本段では pytest を実走しておらず、緑とは報告しない。

## 裁定パッケージ候補 (scope 外の所見)

- argv をどうしても保存する場合は、T2228 の凍結 red record bytes を維持したまま新しい versioned record 契約へ進むか、過去 manifest が producer 互換性を拘束しないと再裁定する必要がある。どちらも本段では採用しない。
- job body は canonical 化した `evidence_root` を元の環境変数名へ再 export していない。明示的な canonical-path export と job-contract test を求めるなら、`p3_s4_loop_pegasus.sh` を変更面へ加える別裁定が必要。
- preprocess 失敗そのものや gflags/config.h 供給経路の修正は親 brief の scope 外のまま。

## 総括

P1b は「直接 `sha256(canonical_json)` consumer は無いが、red canonical JSON を含む full result の凍結 SHA-256 manifest は存在する」という反証になった。指定された判定規則に従い、`condition_meaning_gate._run_process` の argv 追記は断念する。

実装可能な最小形は、`p3_s4_loop._require_condition_gate` の red 分岐だけで両 arm record を create-only 保存し、I/O 成否にかかわらず両 `evidence.detail` を含む `RuntimeError` を送出する形である。`p3_s4_loop.py` は B4 projection closure の共通 memberなので、編集すると base / sort / trigger の live hash 3値すべてが動く（[p3_b4_closed_critic.py:623-684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_b4_closed_critic.py:623)）。`condition_meaning_gate.py`、test、受入台帳はこの closure の member ではない。事前登録は live 値の再導出を要求する書式であり、固定値 errata は不要。