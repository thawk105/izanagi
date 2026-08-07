結論は **NO-GO**。親実測の 209 passed は否定しないが、静的検査では「新設防壁の恒真化」「単一 kill node の誤認」「未裁定の受理集合変更」「report より先に公開される材料」という未検査経路が残る。pytest は実行していない。

## real 所見

### R1 — pending 残留検査は現在の producer 入力では発火不能（must-fix）

`_pending_critics` は helper 冒頭でリスト全体を `pop` され、その後に critic を処理する。[producer:1246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1246)

一方、すべての正常 cell は即 helper を通り、例外復元 cell も `admission_decision` がなければ後始末 helper を通る。[producer:1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1432) [producer:1442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1442)

したがって helper が正常復帰すれば key は必ず消え、helper が例外終了すれば残留検査へ到達しない。[producer:1467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1467) 発火させられるのは、現 producer が作らない「既に `admission_decision` があるのに pending key も残る cell」を monkeypatch 等で注入した場合だけである。

さらに多世代で critic 1 が invalid になると、リストは既に pop 済みなので critic 2 以降を呼ばず `break` しても残留検査は発火しない。[producer:1302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1302)

**成果物影響:** proof chain が「pending 消費漏れは専用 gate が検出する」と参照すると偽になる。現在は別の completeness 順序検査が report を止めるだけで、当該 gate 自身の発火証拠は作れない。

### R2 — role-invalid 優先テストは両条件を作れているが、単一理由ではない（must-fix）

`test_invalid_critic_overrides_harness_terminal_stop` は harness=`converged` と malformed critic を同時に成立させている。[test:2092](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2092)

しかし優先代入を削除する mutant では、明示 assert に届く前に completeness の「stopped cell の全 role は valid」検査が invalid critic を拒否する。[consumer:842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:842) 同様に M2 の代入削除も fixed-budget の valid-role 検査で先に落ちる。[consumer:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:771)

よって v3 の「他層は同じ入力を拒否しない」という単一理由性は誤りである。[v3:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-07_t244-p3-u8-critic-after-admission/s4-erratum-v3.md:87)

**成果物影響:** 変異台帳・proof chain の M2/M3 kill node が producer の優先 assert を指す一方、実際の kill は consumer completeness になる。

### R3 — critic phase 全体を workload `try` 外へ出し、1 世代の受理集合も変えている（must-fix）

仕様が外へ伝播させると明記したのは finalizer 例外だが、実装は critic 準備・provider lookup まで含む helper 全体を `try` 外に置いた。[v5:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-07_t244-p3-u8-critic-after-admission/s4-erratum-v5.md:29) [producer:1377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1377) [producer:1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1432)

具体例は、planner/coder/auditor だけを持ち critic key を欠く注入 providers である。旧実装では `providers["critic"]` が `_run_workload` 内で失敗し、外側の `except Exception` により `supervisor-error` partial report になった。[patch:190](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s5-impl.patch:190) 現実装では admission 確定後、helper 内の lookup が送出して report は作られない。[producer:1289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1289)

不正 campaign 上の `require_admitted_campaign`、critic digest 構築例外も同じ変更を受ける。これは v3 の「1 世代の受理集合は不変」に反する。[v3:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-07_t244-p3-u8-critic-after-admission/s4-erratum-v3.md:55)

**成果物影響:** 同じ 1 世代入力について `report.json: partial` と lifecycle `partial` だったものが、report 不在・formal lifecycle `indeterminate` へ変わる。fail-closed 方向だが未裁定の受理集合変更である。

### R4 — 多世代では critic reflux を捨ててから、遅すぎる fail-closed を行う（must-fix）

`prior_reverse` は `None` で初期化された後、一度も更新されない。[producer:1629](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1629) 旧代入 `prior_reverse = critic["reverse_recommended"]` は削除されている。[patch:205](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s5-impl.patch:205)

そのため cap-lift 時は generation 2 の proposal artifact と harness に `prior_critic_reverse=null` が渡り、generation 1 critic は両 generation の harness 終了後にしか呼ばれない。[producer:1782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1782) [producer:1848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1848)

completeness は report を止めるが、その時点では proposal、harness/WAL、critic raw、`run-finish`、build なら Layer 3 が既に書かれている。[producer:1512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1512) これは「結果を次の一手へ渡す」規律3とも衝突する。[CLAUDE.md:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/CLAUDE.md:73)

新設テストは report 不在と critic 2 回だけを見ており、generation 2 の `prior` や残留材料を検査しない。[test:2188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2188)

**成果物影響:** cap-lift 入力では generation 2 proposal/WAL の受理材料が critic 1 の指示を欠いた値へ変わり、journal は `run-finish` を持つ一方 report は不在、Layer 3 material は残りうる。

### R5 — report は partial でも positive Layer 3 material を公開する（仕様レベル、must-fix）

build cell は先に実 Layer 3 を永続化して `admission_status="admitted"` を得てから critic を呼ぶ。[producer:1239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1239) malformed critic は `role-invalid` にするだけで admission を巻き戻さない。[producer:1303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1303)

consumer は status に関係なく build admission を positive として検査し、critic-invalid cell を正規の `role-invalid` partial として受理する。[consumer:948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:948) [consumer:781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:781) その後 Layer 3 chain も status 非依存で検査され、report が書かれる。[producer:1525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1525)

新 critic-invalid テストは `do_build=False` なのでこの組合せを検査していない。[test:2063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2063) finalizer-failure テストも durable material を一切書かない fake である。

さらに critic が `BaseException` を送出、または critic journal durability が失敗すると、report は止まっても既に link 済みの Layer 3 は残る。[layer3_report.py:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/layer3_report.py:570)

**成果物影響:** certified 選択自体は partial filter が守る限り不変だが、材料受理集合には「critic invalid／critic attempt 不在でも positive admission の Layer 3」が残り、formal receipt・proof chain がそれを参照できる。既知 A4 を「scope 外」にした仕様判断では、この新しい公開時点を防御できない。

### R6 — generation-boundary wall の journal/report 不一致は real だが既存（今回の must-fix 外）

generation 内 wall event は `transport_receipt is not None` のときだけ journal へ書かれる。[producer:1638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1638)

receipt 無しでは report に `supervisor-wall-budget` cell があるのに terminal journal event がなく、consumer は明示的に受理する。[consumer:545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:545) [consumer test:522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_autonomous_trial_completeness.py:522) receipt 有りでは terminal projection が成立せず fail-closed になる。

**成果物影響:** 同じ wall exhaustion が transport 無しでは terminal event 不在の partial report、transport 有りでは report 不在となり、試行台帳の終端集合が transport に依存する。差分起因ではないため今回の must-fix 番号には含めない。

## journal/report 分岐監査

| 分岐 | 静的判定 |
|---|---|
| planner/coder/auditor invalid | pending は空。journal と report の role prefix は一致。no-build は partial 受理、build finalizer が成立しなければ report 前に fail-closed |
| preview reject | auditor `skipped` を含む P/C/A/critic の完全一致。machine preview・auditor gate の緩和なし |
| workload 前 wall | cell 無し、wall event が `run-finish` 直前。整合 |
| generation 前 wall | R6 の transport 非対称あり |
| supervisor-error、pending 無し | 復元 prefix と journal は一致し、partial report |
| supervisor-error、pending 有り | critic が terminal event 後に追加されるため terminal projection／sequence で fail-closed。critic invalid は黙って publish されない |
| 通常 cell の critic invalid | P/C/A/critic の順序は一致し、`role-invalid` partial report を publish。R5 の positive material 問題あり |
| 複数 workload・1世代 | cell ごとに critic が完了するため完全一致 |
| 複数 generation 完走 | journal=PCA/PCA/critic/critic、report=PCAcritic/PCAcritic。completeness で report 前に fail-closed。ただし R4 の先行成果物は残る |
| finalizer 失敗 | helper が workload `try` 外なので report は作られない。ただし link 後失敗なら Layer 3 自体は残りうる |

## 疑いを反証できた点

- private pending list の built-in 成果物漏洩は確認できない。proposal は独立した `proposal_value` のみ、critic payload は明示 projection、report は pop 後に構築される。direct `_run_workload` の Python 戻り値だけは仕様どおり private key を露出する。[producer:1790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1790) [test:2217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2217)
- 順序テストの期待値は実装から導出しておらず、literal `["admission", "critic"]` なので恒真ではない。[test:1986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:1986) ただし fake finalizer のため、証明できるのは Python 呼出順だけであり durable Layer 3 完了順ではない。
- `_ROLE_ORDER` prefix、status 再計算、machine preview、auditor skip、WAL admission 自体の緩和は見つからない。問題はそれらの後に置かれた critic と公開境界である。
- generation の早期 append と `_partial["generation"]=None` は、例外復元時の identity 重複防止により、現在の 1 世代 report shapeを直接は変えていない。

## 総括

- **(a) NO-GO** — 新防壁の一つが発火不能で、mutation の単一理由性が成立せず、さらに 1 世代受理集合と多世代材料生成が仕様記述から逸脱している。
- **(b) must-fix:** R1、R2、R3、R4、R5。
- **(c) 最も見落とされやすい点:** completeness が止めるのは `report.json` だけであり、その前に `run-finish`、proposal/WAL、場合によっては positive Layer 3 が既に永続化されていること。
- **(d) 仕様自体の誤り:** 「1 世代の受理集合は不変」、M2/M3 の単一理由性、「多世代は report publish 前に fail-closed だから十分」の3点。いずれも実装・consumer の実際の順序と一致しない。