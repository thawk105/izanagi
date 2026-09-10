## 所見

1. **[blocker] 未分類の consumer を `finish_run()` の前段へ置くため、admission 違反と gate 化が同時に起きる。**  
   台帳は最大 1,000 file・512 MiB・100万 record・25万 request を扱う上限であり、入力 byte 上限は memory 上限ではない（[claude_session_ledger.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:28)、[同:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:552)）。未計測処理は `unknown`、`dispatch-required` と同じ扱いであり、AI が自ら測って軽量認定してはならない（[tools/README.md:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/README.md:11)、[同:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/README.md:17)、[pegasus-runbook.md:411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/docs/pegasus-runbook.md:411)、[同:484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/docs/pegasus-runbook.md:484)）。したがって現状の分類は **`unknown`** で、自動結線不可。  
   さらにプランは collector を `task_end` より前へ置く（[s2-plan-out.md:105](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:105)）。checker は `task_end.outcome=completed` を必須にするため（[checker.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/dev_waves/checker.py:180)、[同:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/dev_waves/checker.py:668)）、例外捕捉では止められない hang・SIGKILL・OOM・timeout、または usage append 後の stream 破損で consumer が実質 gate になる。予定された「usage 0件でも valid」テストは schema 層では有効だが、end-to-end の非 gate 化を保証しない。  
   **放置時:** task-run は未完了または damaged となり、dev-wave checker と task-run report が赤になる。certified 選択・材料 report・campaign WAL の値は変わらないが、wave 完了経路が停止する。

2. **[blocker] population payload は現行 privacy 契約のままでは git 追跡を許可できない。**  
   現契約は記録が事実上削除不能であることを前提に、selector/node 名を禁止する（[output/task-runs/README.md:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/README.md:21)、[同:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/README.md:62)）。project/cwd の無 salt SHA-256 は暗号化ではなく、候補 path を推測できる環境では辞書照合可能な永続 pseudonym である。64 hex は現行 safe-slug 正規表現へ構文上入る（[schema.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/schema.py:25)）が、それは privacy 上の許可を意味しない。正確な時間窓と走査件数も、作業時刻・会話量を恒久的に関連付ける。段 2 自身も裁定事項と認めている（[s2-plan-out.md:118](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:118)）。  
   **放置時:** task-run event/report に worktree identity の照合可能な digest、作業時間窓、transcript 量が不可逆に残る。campaign WAL と certified 選択は不変だが、開発観測台帳の公開値から撤回不能な相関が作られる。

3. **[must-fix] D66 への直接結線は見つからないが、新 sibling root の非証拠分類が正本化されていない。**  
   現 writer は realpath 上の evidence namespace を拒否し（[ledger.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/ledger.py:49)、[同:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/ledger.py:144)）、task に authority 定数を埋める（[同:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/ledger.py:564)）。campaign 側の通常 layout も `output/campaigns/` 固定である（[layout.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/orchestrator/campaign/layout.py:222)）。したがって、プラン内に task-run report から proof chain へ値を渡す直接経路はない。  
   ただし namespace 地図が非証拠と認めるのは `task-runs/` だけである（[output/README.md:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/README.md:30)、[同:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/README.md:46)）。段 2 は新 root README だけを挙げ、`output/README.md` 更新を落としている（[s2-plan-out.md:143](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:143)）。加えて `check_docs.py` の living-doc 列挙も旧 root 固定で、新 README は lint 外になる（[check_docs.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/check_docs.py:33)、[同:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/check_docs.py:40)）。  
   **放置時:** v2 台帳の authority・privacy・参照契約が namespace 正本と lint の外へ出る。certified 選択/WAL は直ちには変わらないが、v2 report を非証拠として参照できる根拠が欠落する。

4. **[blocker] 選択肢 B は凍結済み `task-run/v1` の受理集合を拡張する。**  
   現 validator は version と event 閉集合を固定している（[schema.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/schema.py:18)、[同:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/schema.py:40)）。既存 pilot は10 runで final report とその SHA-256を凍結済み（[report:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/reports/20260720-20260722_task-efficiency.md:6)、[pilot-final.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/task-runs/pilot-final.json:1)）。  
   optional event 追加なら既存10件は静的には引き続き valid だが、新 validator が受理する `task-run/v1` を旧 validator は拒否する。同じ version 文字列が異なる受理集合を表し、aggregate を version 分岐しなければ historic report の再生成 bytes も final marker と一致しなくなる。  
   **放置時:** 既存 tracked bytes 自体は不変でも、`task-run/v1` の再検証結果が validator revision 依存になる。campaign 成果物は不変、開発試行台帳の受理集合と report 再現性が変わる。

5. **[must-fix] sibling root 切替の実 default は6箇所で、初期化手順も必要。**  
   機能上の既定 root 構築点は次の **6箇所**。

   - CLI 1件: [cli.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/cli.py:26)
   - test wrapper 3件: [run_tests.py:855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/run_tests.py:855)、[同:966](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/run_tests.py:966)、[同:1479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/run_tests.py:1479)
   - fixed-check wrapper 1件: [task_run_check.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_run_check.py:33)
   - daemon 1件: [daemon.py:1126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/dev_waves/daemon.py:1126)

   CLI help も別途1件ドリフトする（[cli.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/cli.py:45)）。`checker.py` の hard-coded default は **0件**で、daemon から渡された `task_runs_root` を使う（[checker.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/dev_waves/checker.py:96)）。段 2 の production file 列挙は概ね正しい。  
   一方、`start_run()` は root を作らず既存 `pilot.json` を要求する（[ledger.py:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/ledger.py:527)、[同:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/ledger.py:538)）。default 切替と v2 pilot 初期化の原子的な順序がプランにない。  
   「現行 CLI だけで別 v1 root を作れる」は正しい。任意 root を受ける `init-pilot`（[cli.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/cli.py:42)）が v1 の `SCHEMA_VERSION` を書く（[ledger.py:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/task_runs/ledger.py:359)）。ただし v2 root は実装前には作れない。  
   **放置時:** test event は旧 root への append 失敗を黙って捨て、daemon/checker は別 root の task を未完了と判定しうる。task-run report の件数・欠測率・参照先が分裂する。

6. **[must-fix] private な path→Claude slug 複製は、欠測でなく偽ゼロを作りうる。**  
   現 ledger は literal project slug を受けるだけで（[claude_session_ledger.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:186)）、段 2 は repo 外 private rule を複製する（[s2-plan-out.md:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:55)）。Claude 側の符号化が変わっても旧 directory が残っていれば「directory 不在」にはならず、古い directory を走査して model call 0/token 0を正常観測として保存できる。現 collector は「0件」を issue にしない（[claude_session_ledger.py:896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:896)）。  
   **放置時:** task-run report の usage 値が欠測ではなく偽ゼロになり、before/after 系列を下方に歪める。certified 選択・campaign WAL は不変。

7. **[nit] 明示された文書変更そのものに byte 予算違反はない。**  
   `TextLimit` は dev-wave 4文書と `tools/README.md` に掛かる（[check_docs.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/check_docs.py:176)、[同:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/check_docs.py:185)）。静的 `wc -c` で dev-wave 合計 25,187/25,200、tools README 2,989/3,000 を再確認した。段 2 は両者を変更せず、`docs/README.md` と新 root README を変更するため、この部分は land 可能。`docs/decisions.md`、`docs/README.md`、`output/*.md` はこの TextLimit 対象外である。  
   ただし `tools/README.md` へ12 bytes以上を足す案はそのままでは land 不能。新 root README の lint 列挙漏れは所見3の must-fix。  
   **放置時:** 現プラン記載どおりなら成果物値は変わらない。予算対象文書への追加を後付けした場合だけ `check_docs` が land を拒否する。

## scope 肥大の判定

**(d-v2) は D205 に照らして過大であり、推奨としては NO-GO。** D205 は「最小で研究が進む選択肢」を既定とする（[decisions.md:9840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/docs/decisions.md:9840)）。段 2 自身の見積りを合算すると、schema 330–370、adapter 100–130、validator 80–120、aggregate 50–70、ledger/finish 38–57、collector 抽出・slug resolver 45–65、公開 API 2–4で、production 差分だけでも約 **645–816行**。9本の専用テスト、default path、文書は別であり、350–500行見積りは過少である（[s2-plan-out.md:40](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:40)、[同:95](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-ledger-consumer/s2-plan-out.md:95)）。

最小代替案として名指しするのは、**repo 外 wave-job directory への per-wave canonical JSON 保存を append-only 集合として運用する案**である。現 CLI は project/cwd/window/max-files/sidechain/JSON を既に受ける（[claude_session_ledger.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:108)）。

| 小さい設計 | 失うもの |
|---|---|
| repo 外へ既存 `--json` 出力を wave ごとに1ファイル保存し、外側で集計する | task-run validator/report との統合、自動 coverage、git durability。実行漏れは運用上の欠測になる |
| repo 外の単一 JSONL へ既存 CLI 出力を追記する | 並行 append/crash consistency の強い保証、wave 単位ファイルの独立性 |
| `output/insights/` へ canonical JSON を1 wave 1件で追跡する | task-run 型検査と completion linkage。さらに raw population を入れるなら privacy 裁定が必要 |
| CLI invocation だけを運用手順として文書化する | 保存・系列化・実行完全性。観測を都度再実行できるだけで、永続系列にはならない |

いずれも transcript の第3 parser は作らず、既存 canonical ledger の JSON を消費する。最小案が失うのは自動 completeness と task-run report 統合であり、「消費観測を系列として残す」という研究目的そのものではない。

## 親 brief の却下理由の検算

- **(P2) refuted。** 3台帳は直接編集禁止だが、spool fragment が正規経路である（[docs/spool/README.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/docs/spool/README.md:3)、[dev-wave/core.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/docs/dev-wave/core.md:84)）。worklog は dev-wave 25,200-byte 予算の対象でもない。また insights は自由書式限定ではなく、実際に構造化 JSON が多数存在する（例: [task-run-ledger-mutation-ledger.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/output/insights/2026-07-20_task-run-ledger-mutation-ledger.json:1)）。したがって、typed な wave artifact または repo 外 wave record は (d-v2) より小さく目的を達しうる。

- **(P3) real（自動 cron 案について）。** production caller/scheduler は static grep で見つからず、現物は CLI `main()` のみ（[claude_session_ledger.py:905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/claude_session_ledger.py:905)）。自動化は admission 再分類を要し、観察値は workload/stage と交絡するという D207 の理由も実在する（[decisions.md:9896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/docs/decisions.md:9896)）。ただし、cron を伴わない手動・wave-end 保存まで却下する根拠にはならない。

- **(P4) real。** `codex_reasoning_ab.py` は Codex binary、model、`max/high` effort、Codex session ledger を固定している（[codex_reasoning_ab.py:1800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/codex_reasoning_ab.py:1800)、[同:2172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/codex_reasoning_ab.py:2172)、[同:2781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/codex_reasoning_ab.py:2781)、[同:5220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-ledger-consumer/tools/codex_reasoning_ab.py:5220)）。汎用 provider seam や Claude arm runner はなく、Claude A/B を成立させるには新 harness/receipt/parser binding が必要で、今回は小さい候補ではない。

## 総括

(d-v2) は D205 に対して過大で、現状のまま land は NO-GO。  
最重件は、未計測で `unknown` の consumer を `task_end` 前へ自動結線し、admission 違反と completion gate 化を同時に起こす点である。  
選択肢 B は凍結 v1 の受理集合を壊し、選択肢 A は6箇所の default 切替・v2 pilot 初期化・namespace 正本化が必要。  
tracked SHA-256 binding と正確な時間窓は現 privacy 契約では未許可で、裁定前に保存してはならない。  
最小案は、既存 canonical CLI の JSON を repo 外 wave artifact として前向きに保存する方式。  
pytest・collector・`check_docs` は実行しておらず、本回答は read-only の静的検査結果である。