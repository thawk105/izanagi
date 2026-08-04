## 所見ごとの対応表

| ID | 所見の要旨 | fix の所在 (file:line) | 判定 | 根拠 |
|---|---|---|---|---|
| RA-B1 | supersede が 1 文だけで、旧「7 件」と新「8 件」が矛盾。引用も原文不一致 | [新 D:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:24)、[同:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:29)、[同:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:33) | **closed** | 引用記号と箇条書き接頭辞だけを除いて比較し、2 文とも D121 原文 [5851–5854](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5851) と改行・強調・句点込みで byte 一致。間の P8 文も非置換と明記されている。 |
| RA-B2 | worklog、V4、fold 後の参照更新が欠落 | [worklog:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:37)、[同:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:68)、[同:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:80)、[同:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:88) | **closed** | V1 は T-244 に残し、V2・V3・V4 は別 placeholder、採番後 pointer も新規 T として保存された。 |
| RA-M1 | ユーザー裁定の一次記録を派生資料 directory としていた | [新 D:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:19)、[worklog:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:12) | **partial** | 新 D は worklog (153) U2・archive (126)・`s4-adjudication.md` を分離した。一方、worklog は再び `逐語 = output/insights/.../` と directory 全体を指す。 |
| RA-M2 | 「状態語 2 語」が D138 の実行結果型 4 値を潰す | [新 D:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:56) | **closed** | 2 語は「非適用理由」だけ、D138 の P6 実行結果 4 値は不変と明記された。 |
| RA-M3 | completeness の consumer 2 gate が living docs から脱落 | [runbook:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:209)、[phase3.md:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3.md:466) | **partial** | runbook は 2 consumer を追記し、実コードとも一致する。しかし `phase3.md` は引き続き producer 3 入口＋freshness だけである。 |
| RA-M4 | runbook が旧 D121 単独経路を残す | [runbook:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:119)、[worklog:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:88) | **closed** | P4/P6 の改訂規則が番号なしで逐語化され、fold 後の実 D 参照も新規 T へ保存された。 |
| RB-B1 | 空実装＋恒真 calibration で `NOT_CLAIMED` を自己申告できる | [新 D:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:72)、[同:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:115) | **regressed** | 自己申告穴を閉じる代わりに、未裁定の semantic contract と receipt の欠如を `NOT_IMPLEMENTED` 判定へ転用した。U2/D138 の二分より受理集合を狭め、同 D の却下案とも矛盾する。RC-B1。 |
| RB-B2 | 「既裁定の帰結」を理由に D96 手続を外していた | [新 D:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:45) | **closed** | 現行機械受理集合は cap=1 で不変と分離し、将来の結線時に P4 正例・非適用拒否境界テストを同一変更単位へ要求した。D96 [4271–4279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:4271) と整合する。 |
| RB-B3 | runbook の旧 D121 経路から迂回可能 | [runbook:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:122) | **closed** | P4 無条件・P6 未実装失敗が逐語化され、旧単一「非適用」では通らない。ただし RC-B1 の過剰拒否も同時に転記されている。 |
| RB-M1 | 将来裁定だけで P4 を再条件化できる | [新 D:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:51) | **closed** | 明示 supersede、代替状態、D96 記録・境界テストを同一変更単位に要求する遷移契約が入った。 |
| RB-M2 | T-244 を完了すると未解決本体が消える | [worklog:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:66) | **closed** | `更新` を使用し、`base:` は canonical T-244 本文 [614–620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:614) の SHA-256 `561133…c9cf` と完全一致。 |
| RB-M3 | stale preregistration が専用 T になっていない | [新 D:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:96)、[worklog:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:86) | **closed** | 現 preregistration は cap-lift 証拠にならないと明記し、V4 を専用裁定 T にした。 |
| RB-M4 | 今回の非実装 scope が将来の機械束縛まで却下する | [新 D:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:101) | **closed** | 「本 wave／本 D」に限定し、択一 2 の将来 machine binding を却下・延期しないと明記した。 |
| RB-M5 | living docs が未確定項目の内訳を示さない | [runbook:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:212)、[phase3.md:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3.md:474) | **partial** | runbook は予算、P6/receipt、off-arm、機械束縛、crash/replicate/0-bit を列挙した。`phase3.md` は後三者のうち D138 の crash/replicate/0-bit を落としている。 |
| RB-N1 | 「逐語の正本」が directory 単位で非一意 | [新 D:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:19)、[worklog:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:13) | **partial** | 新 D は非一意性を解消したが、worklog が同じ directory 指定を再導入した。 |

## 新規所見

### RC-B1 — 決定 (4-b) が U2 の免責経路を未裁定条件で停止する（blocker）

- **主張:** 決定 (4) と (4-b) は、単なる「現在 P6 が未実装」という時間的併存なら矛盾しない。しかし実際の (4-b) は、semantic contract と cap-lift receipt の両方が revision に束縛されるまで P6 を `NOT_IMPLEMENTED` と分類する。これは U2 が残した `NOT_CLAIMED` 経路を、未裁定 V2/V3 の成立まで実効無効化する新規条件である。永久削除ではないが、再開条件自体を未裁定事項で先取りしている。

- **根拠:** U2 は「主張しない」だけを免責し「実装が無い」を失敗としただけである [worklog:568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:568)。D138 の `NOT_IMPLEMENTED` 定義は handler・adapter・calibration・未知 kind fail-closed の実装有無であり、receipt は含まない [D138:6760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6760)。新 D は一方で receipt 未定義を `NOT_IMPLEMENTED` 判定へ使い [新 D:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:72)、他方で packaging 不足を `NOT_IMPLEMENTED` と誤記する案を明示的に却下している [同:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:115)。さらに semantic contract・receipt・`NOT_CLAIMED` cap-lift 可否は未確定と自認する [同:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:123)。

- **成果物影響:** 実装済み P6 でも receipt 未整備を理由に `NOT_IMPLEMENTED` と誤記でき、cap-lift の規範受理集合、proof chain の P6 status、試行台帳の世代数が読む条項によって分岐する。

- **修正案:** (4-b) は「現行 tree には D138 の 4 実装要素が無いため、現在の P6 は事実として `NOT_IMPLEMENTED`」までに限定する。証拠不足時は cap-lift を fail-closed に拒否しても、実装状態を `NOT_IMPLEMENTED` へ再分類しない。semantic contract と receipt を必須条件にするなら、V2/V3 のユーザー裁定を得て P6 status と別の approval gate として記録する。runbook [122–125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:122) も同時に直す。

### RC-M1 — `phase3.md` が consumer 閉包と D138 残余を引き続き落とす（major）

- **主張:** runbook だけが修正され、もう一方の living doc は不完全なままである。

- **根拠:** `phase3.md` は producer 3 入口と freshness だけを記す [phase3.md:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3.md:466)。実コードは run-envelope [autonomous_trial_completeness.py:414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/autonomous_trial_completeness.py:414) と campaign-chain [同:1003](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/autonomous_trial_completeness.py:1003) でも同じ producer 定数を読む。未確定項目も `phase3.md` [474–479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3.md:474) は D138 の crash 回復・replicate・0-bit 証明 [D138:6796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6796) を落とす。

- **成果物影響:** `phase3.md` を入口に変更審査すると consumer 2 gate が変更閉包から漏れ、将来の上限変更で producer と completeness verifier の受理集合が分岐し得る。

- **修正案:** runbook [209–216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:209) と同じ consumer 2 gate・残余列挙を `phase3.md` にも反映する。

### RC-M2 — worklog が修正済みの authority 分離を再び壊した（major）

- **主張:** 新 D では一次裁定・wave 裁定・erratum 履歴を分離したのに、worklog が U2 の「逐語」を再び directory 全体へ戻した。

- **根拠:** [worklog:12–13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:12) と、新 D の正しい分離 [19–22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:19) が不一致である。

- **成果物影響:** canonical worklog を辿る consumer が、U2 の一次記録ではなく誤前提を含む `brief.md` を逐語 authority として選び得る。

- **修正案:** worklog も「U2 一次記録 = worklog (153)、択一 3 = archive (126)、wave 裁定 = `s4-adjudication.md`、brief は非規範履歴」と書き分ける。

### RC-M3 — worklog の「blocker 5 件を全件 fix」が事実でない（major）

- **主張:** RB-B1 は回帰し、RA-M3 なども partial なのに全閉鎖を記録している。

- **根拠:** [worklog:27–32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:27) は全件 fix と断定するが、RC-B1 の矛盾が残る。

- **成果物影響:** 台帳上は段 6 が閉じたように見え、未裁定の受理集合変更を含む新 D が段 7／land へ進む。

- **修正案:** 現状は「blocker 5 件中 4 件 closed、RB-B1 regressed」と記録し、RC-B1 解消後にのみ全閉鎖へ更新する。

### RC-N1 — provenance 結果の射程が未記載（nit）

- **主張:** 実行自体を否定する証拠はないが、現在の fix は未 commit なので、記載された provenance 結果は最終 wave commit を監査した証拠ではない。

- **根拠:** [worklog:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/2026-08-04-dev-wave-t244-u2-na-bifurcation-2.md:60)。現在の HEAD は `fc8f070` で、fix は modified/untracked。完了監査は commit 後に行う契約である [AGENTS.md:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/AGENTS.md:26)。

- **成果物影響:** worklog が未 commit fix まで provenance 済みと誤読される。

- **修正案:** 現結果を「pre-commit HEAD `fc8f070` まで」と限定し、最終 commit 後の監査は pending とする。

## 検証済み事項（新規所見なし）

- worklog の形式は静的には契約どおり。H2 は `本文` → `次の一手差分` の 2 個、title は無引用符、`更新` の `base:` は正しい digest、新規 T は placeholder、継続行は 2 space である。
- V1 は T-244 に保持し、V2＝semantic contract、V3＝receipt、V4＝prereg refresh、新規 pointer T という分配は妥当。
- 既知赤 1 件の帰属は妥当。canonical worklog も同 node・同件数を [T-407] として記録し [docs/worklog.md:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:295)、`ruleops.py` は実際に strict UTF-8 decode で停止する [tools/ruleops.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/ruleops.py:191)。ただし本 reviewer は pytest を再実行しておらず、`5430 passed` を独立に緑認定しない。
- producer 側は `_validate_generation_budget()` を CLI・`run_trial()`・`_run_workload()` の 3 入口から呼ぶ [p3_autonomous_workload_trial.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/p3_autonomous_workload_trial.py:247)。consumer 2 gate の記述も実コード上正しい。

## 総括

**NO-GO。**

- 対応結果: **closed 10 / partial 4 / regressed 1**
- 残る blocker: **RC-B1（RB-B1 の回帰）**
- `NOT_CLAIMED` の免責を保存したまま自己申告穴を処理できておらず、未裁定 V2/V3 を先取りして受理集合を狭めている。
- pytest・受入試験・provenance 検査は本レビューでは実行していない。既存テスト期待値の変更も提案していない。