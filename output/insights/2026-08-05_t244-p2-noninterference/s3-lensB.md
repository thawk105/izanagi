静的レビュー結果は **NO-GO**。現プランが検査できるのは平文 substring だけで、現行 baseline が既に持つ可逆な符号化漏洩を検出できません。

## BLOCKER

1. 現行 baseline は情報流として既に赤

critic は `outcome["variant"]` をそのまま受け取ります（[p3_autonomous_workload_trial.py:1653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1653)）。diff-quarantine ID は `genome + canonical predicate` の SHA-256 先頭12桁です（[p3_s4_loop.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:241)）。predicate は wire から一意に生成されます（[p3_s4_loop_trigger_gating.py:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:395)）。

同じ式で32点を静的列挙した結果は以下でした。

- ID は32/32すべて一意。
- ID中の自分自身の wire 字面 hit は0/32。
- したがって `variant → wire` は辞書逆引き可能だが、提案された substring gate は一度も発火しない。

build 到達 ID も `genome + src_token` の hash で（[pipeline.py:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/pipeline.py:92)）、`src_token` は候補述語を含む正規化 source の digest です（[source_digest.py:640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/source_digest.py:640)、[source_digest.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/source_digest.py:749)）。こちらの逆引きは同一 source/compiler 文脈と12桁衝突なしが条件ですが、依存自体は明白です。

従って親の「32点 universe では wire に戻せる」は diffq 経路では正しく、build 経路では条件付きで正しいです。一方、plan の「baseline は赤にならない」（[plan.md:33](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:33)）は lexical 検査についてしか成立せず、brief が定義した関数的非干渉（[brief.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/brief.md:46)）については成立しません。

M8/M9/M10 も新しい情報漏洩を作る変異ではありません。既に可逆な ID が運ぶ5 bitを、wire・diff・SHAの字面へ展開するだけです（[plan.md:188](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:188)）。これらが赤でも証明できるのは「平文コピー拒否」であって非干渉ではありません。

2. auditor 例外は brief の対象と正面衝突する

brief は planner/coder/auditor/critic をすべて untrusted とし、実効 diff と digest が入力に現れないことを要求しています（[brief.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/brief.md:8)）。しかし現行 auditor payload は `working_diff` と `diff_digest` を直接含みます（[p3_autonomous_workload_trial.py:1557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1557)）。plan はその二 path を検査から除外します（[plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:67)）。

現状は raw mask = effective mask なので、この `working_diff` は同時に実効 diff です。「raw として許す」だけでは「effective は見せない」を満たしません。全 untrusted role に対する検査を成立させるには、次のいずれかが必要で、いずれも親の裁量外です。

- auditor を trusted recipient に再分類する。
- auditor payload から diff/digest を除く、または別表現に変える。
- 性質名を「auditor 二 field を明示除外した literal tripwire」へ狭める。

前二案は payload の field/value 不変条件（[brief.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/brief.md:28)）を破るため、実装せず裁定へ返すべきです。

3. 「IR schema SHA」の preimage が未定義

`reflux_ir.py` に実在するのは識別子文字列 `SCHEMA_ID` だけです（[reflux_ir.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:19)）。plan が提示する値はその識別子26 bytesの hash であり、schema bytes や emitter の SHA ではありません（[plan.md:139](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:139)）。元設計は candidate IR schema と canonical emitter の SHA を origin に含める要求です（[README.md:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-01_t244-reflux-design/README.md:214)）。

`IR_SCHEMA_ID_SHA256` を新造しても brief の「IR schema SHA」を閉じたことにはなりません。schema bytes、schema ID、emitter source、raw/effective IR instance のどれを指すか裁定してからでなければ実装不能です。

## MAJOR

1. 必要層は9層あり、plan が閉じるのは一部だけ

確認した層は以下です。

1. wire→predicate→diff の producer（[p3_autonomous_workload_trial.py:653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:653)）
2. current/past material history
3. 四 role の payload constructor
4. `_invoke` entry
5. provider の artifact化・stdin sink（[claude_projected_provider.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/claude_projected_provider.py:253)）
6. role file + mediated contract の effective prompt（[claude_projected_provider.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/claude_projected_provider.py:156)）
7. trigger/sort の manual preview→main-session spawn 経路（[p3_s4_loop_trigger_gating.py:769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:769)、[p3_s4_loop_sort.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_sort.py:352)）
8. public provider/fixture の直接呼出し（[p3_autonomous_workload_trial.py:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:419)、[test_p3_autonomous_workload_trial.py:1800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:1800)）
9. journal/report/WAL/provenance/Layer-3 の公開面（[p3_s4_loop_trigger_gating.py:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:736)）

8c production 内の `provider.invoke` が `_invoke` 一点なのは正しいです（[p3_autonomous_workload_trial.py:922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:922)）。ただし repo 全体の role 入力経路は一点ではありません。`_journal_auditor_skip` は role を呼ばないため bypass ではありませんが、digest を journal に残す別観測面です（[p3_autonomous_workload_trial.py:981](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:981)）。

従って名乗れるのは「8c supervisor `_invoke` 経路の candidate-literal tripwire」までです。

2. 拒否後の consumer 結線が未確定

plan は gate を `_invoke` 冒頭へ置きますが（[plan.md:74](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:74)）、現行の例外捕捉は provider 呼出し直前からです（[p3_autonomous_workload_trial.py:921](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:921)）。そのままなら gate 例外は role-invalid ではなく generic `supervisor-error` になります（[p3_autonomous_workload_trial.py:1231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1231)）。

さらに build mode では、早期拒否後でも全 cell に Layer-3 finalization を無条件実行します（[p3_autonomous_workload_trial.py:1278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1278)）。planner/coder 段で止まると campaign の `reports/` がまだ無く、元の固定拒否を別例外で上書きして terminal report を作れません（[p3_autonomous_workload_trial.py:1147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1147)）。no-build fixture テストだけではこの欠落を検出できません。

新しい WAL stage は現プランに不要ですが、追加するなら `WAL_STAGES`（[model.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/model.py:27)）と Layer-3 の閉集合（[layer3_report.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/layer3_report.py:42)）の双方が consumer です。journal event を増やす場合も completeness の閉集合更新が必要です（[autonomous_trial_completeness.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/autonomous_trial_completeness.py:40)）。

3. mutation 表の帰属が4件成立しない

所有 A は driver を import しない契約です（[plan.md:166](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:166)）。従って次の production 変異を入れても、指定された A の unit test は変異箇所を通らず緑のままです。

- M3: planner callsite の role 変更。leaf の未知 role テストは常に同じ入力を自作する（[plan.md:183](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:183)）。
- M5: driver の `GATING_SPEC` 変更（[plan.md:185](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:185)）。
- M6: driver の designated context 変更（[plan.md:186](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:186)）。
- M11: production preview digest producer の破壊（[plan.md:191](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:191)）。

いずれも B 側の production integration assertion が必要です。

加えて `MAX_APPROVED_GENERATIONS = 1`（[p3_autonomous_workload_trial.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:143)）なので、history append や「次世代 planner/coder へ過去 material を渡す」結線を削除しても全 run_trial テストは緑です。cap-lift 後に初めて発火する恒真化候補です。

TOCTOU 主張にも、検査済み snapshot ではなく元の `payload` を provider へ渡す mutant が必要です。通常の dict fixture では両者が同値なため、現 mutant 表では生き残ります（[plan.md:56](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:56)）。

4. `noninterference` という名称は過大

既存 `projection_guard.py` は同種の検査を明確に「字面 tripwire」「origin 保証未実装」と名乗っています（[projection_guard.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/projection_guard.py:2)）。同じ限界を認めつつ `reflux_noninterference.py` とするのは、強い保証を示す既存用語との逆転です。

推奨名は `reflux_candidate_literal_tripwire.py`、例外は `RefluxCandidateLiteralError`。

記録文案:

> 8c supervisor の `_invoke` 経路に、role 別 exact schema と current/past candidate の平文 literal tripwire を追加した。可逆 hash・別符号化・auditor 許可二 field・provider 直呼び・manual driver・prompt・journal/report/WAL/provenance は未閉鎖である。D121 P2、観測面閉包、情報流非干渉、cap-lift 前提充足は主張しない。

## MINOR

1. 既存 payload key assert は維持可能だが、明示的な非弱体化条件にすべき

現行は planner/coder/critic を exact equality で検査しています（[test_p3_autonomous_workload_trial.py:788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:788)）。plan の auditor exact set 追加方針は正しいですが、既存三 assert を削除・subset 化・動的 allowlist 化せず、そのまま残すことを段5条件へ明記すべきです。

2. digest の内部命名案は妥当

auditor 出力の `diff_digest` は「監査した diff の echo」と既に定義されています（[auditor_gate.py:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/auditor_gate.py:114)）。plan の内部三名称への分離は妥当です。外部 payload/provenance key は不変条件のため維持し、`auditor_diff_digest = verdict echo` と明記すればよく、ここに payload rename を混ぜてはいけません。

3. brief の実行環境記述が正本違反

brief は login node で pytest を行う記述ですが（[brief.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/brief.md:58)）、現在地は `pegasus02` で、pytest は単一 nodeid も禁止です（[AGENTS.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/AGENTS.md:31)）。親は `tools/run_tests.py` で計算ノードへ dispatch する必要があります。

## 総括

**NO-GO。BLOCKER 3件。**
land 可能なのは「8c `_invoke` 経路の candidate-literal tripwire」まで。
D121 P2、payload 面閉包、情報流非干渉、cap-lift 前提充足とは記録できない。
auditor の扱いと IR SHA の preimage を裁定し、可逆 ID と consumer 結線を再設計してから再レビューが必要。