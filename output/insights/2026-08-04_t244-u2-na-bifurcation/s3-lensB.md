結論は **NO-GO**。親の前提実測 (3) は反証され、段 2 プランは裁定済みの P4 を未裁定として扱っています。blocker は 2 件です。

### B-B1 — 親の「択一 3 は未裁定」が事実誤認

- **主張:** 択一 3 は未裁定ではない。ユーザーは候補 batch の事前凍結を多世代開放の必須前提として既に採用している。brief と plan の P4=`FAIL` は誤った前提に立つ。

- **根拠:**
  - worklog (126) は択一 3 を明示的に「必須にする」と裁定し、batch cardinality・全候補事前 commit・seal までの非公開をセットで要求する。[worklog archive:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/archive/worklog-phase3-0803-125-126.md:314)、[同:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/archive/worklog-phase3-0803-125-126.md:322)
  - 前 wave の brief も「択一 3 は採用済み」と認識していた。[前 wave brief:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-03_t244-p6-contract/brief.md:19)、[同:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-03_t244-p6-contract/brief.md:26)
  - 現 brief はこれを未裁定とし、plan も P4=`FAIL` としている。[brief:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/brief.md:14)、[plan:18](/work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:18)
  - 前提実測 5 件の再監査では、(1) U2 の新 D は未記録、(2) 機械 gate は上限定数と比較だけ、(4) decisions は byte budget/pin 対象外、(5) D138 の二分は確認できた。一方、(3) だけが上記一次記録で反証された。[実 gate:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/p3_autonomous_workload_trial.py:132)、[同:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/p3_autonomous_workload_trial.py:247)、[D138:6760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6760)
  - 承認済み裁定との不整合は停止条件である。[core.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/dev-wave/core.md:17)

- **反証されうる条件:** worklog (126) の択一 3 を撤回・上書きした後続の明示的ユーザー裁定が存在する場合。今回検索した後続 worklog、D、spool には存在しない。

- **成果物影響:** 放置すると P4=`FAIL` により多世代受理集合を誤って狭め、certified 選択を 1 世代に固定し、proof chain と試行台帳へ偽の「択一未裁定」を記録する。

### B-B2 — U2 を新しい cap-lift protocol 一式へ拡張している

- **主張:** U2 の射程は P6 の「未実装」と「実装済み非主張」の二分までである。plan の五値語彙・完全 witness・未知状態規則は新規設計であり、そのまま決定にしてはならない。

- **根拠:** U2 の確定文は二分だけを承認し、新 D で書くとしている。[worklog.md:1110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:1110)、[同:1114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:1114)。元の裁定パッケージも P6 未実装の穴だけを対象にする。[s4-adjudication.md:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-03_t244-p6-contract/s4-adjudication.md:117)。対して plan は五値語彙、判定入力、証拠閉包、P4 評価順を新しい「決定」としている。[plan:35](/work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:35)

  | 親 P | 射程判定 | 扱い |
  |---|---|---|
  | P1 | `NOT_IMPLEMENTED` / `NOT_CLAIMED` の二分だけ射程内。第三種と五値 enum は射程外 | 裁定パッケージへ返す |
  | P2 | 実装有無を判別する必要性は射程内。revision-bound path・検査 ID・結果の完全閉包は新規追加 | 証拠形式は裁定パッケージへ返す |
  | P3 | 未実装を FAIL とする部分だけ射程内。宣言欠落・未知・依存裁定未了を一律 FAIL にする規則は射程外 | 裁定パッケージへ返す |
  | P4 | 「残存義務だけで実効性 > 0」は U2 の外で、P1〜P10 自体を変更する | plan のとおり別裁定へ返し、新 D には入れない |

  scope 外の real 所見は実装せずユーザーへ返す契約である。[core.md:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/dev-wave/core.md:69)

- **反証されうる条件:** ユーザーが U2 と同時に、五値 enum・witness schema・未知状態規則・実効性条件まで明示承認していた場合。

- **成果物影響:** 放置すると証拠様式の不足だけで cap-lift を拒否したり、反対に第三種免責で P4 を外したりでき、certified 受理集合と proof chain の status が裁定範囲を越えて変わる。

### B-M1 — P4 と P6 は同じ status 語彙で扱わず、P4 を別扱いにすべき

- **主張:** 「別扱い」がよい。P4 は択一 3 の既裁定により現在は必須条件、P6 は実装後の claim intent で分岐する。P4 を黙って規則外にすると D121 の旧文言が残るため、別条項で既裁定を参照する。

- **根拠:** D121 は当初 P4 を択一 3 に条件付けた。[decisions.md:5846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5846)。その択一は後に必須採用された。[worklog archive:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/archive/worklog-phase3-0803-125-126.md:322)。P6 の二分は claim の有無を基準にする。[decisions.md:6760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6760)

- **反証されうる条件:** 択一 3 を不採用へ変更する新しいユーザー裁定があり、P4 の非発火状態を再び現実に表現する必要が生じた場合。

- **成果物影響:** 同一語彙を残すと P4 を偽の未裁定 FAIL または将来の免責へ倒せ、複数世代の受理集合・P4 proof 参照・試行行数が分岐する。

### B-M2 — 中核の実装要求は裁定内だが、witness 形式が過剰拘束

- **主張:** P4/P6 の機構実装自体は「採らない設計オプション」の強制ではない。P4 は択一 3、P6 は U3/U5 で選ばれている。ただし plan は「実装」と「完全な証拠 package」を同一視し、別の cap-hostage を作っている。

- **根拠:**
  - U2 は実装済み非主張だけを免責するため、P6 実装を要求すること自体は意図的である。[worklog.md:1110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:1110)
  - U3 は帰納段を踏み、U5 は sort の構造化 witness を新設すると裁定済みである。[worklog.md:1115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:1115)、[同:1129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:1129)
  - D138 の `NOT_IMPLEMENTED` は実装構成要素を列挙するが、plan はさらに全要素の revision-bound path・検査 ID・検査結果を要求する。[decisions.md:6762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6762)、[plan:74](/work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:74)

- **反証されうる条件:** その厳密な witness package が別のユーザー裁定または既存 decision で cap-lift の必要条件として固定済みの場合。

- **成果物影響:** 放置すると機構が実装済みでも証拠 packaging の不足を `NOT_IMPLEMENTED` と誤記し、certified 選択を 1 世代へ過剰拘束し、proof chain の失敗理由と試行台帳を歪める。

### B-M3 — 裁定待ちを P4=`FAIL` と数えるのは P10 の二重計上

- **主張:** cap を上げないという結果は正しい fail-closed だが、未裁定を個別 P4 の FAIL と記録するのは不適切。P10 未充足として申請を未成熟のまま停止すれば足りる。

- **根拠:** D121 は P10 自体を予算値・origin authority・軸 (iii) の人間 gate として置く。[decisions.md:5842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5842)、[同:5850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5850)。dev-wave もユーザー裁定待ちは該当段へ進まず停止すると定める。[core.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/dev-wave/core.md:17)。しかも brief 自身、cap-lift application artifact/status field は存在しないと認めている。[brief.md:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/brief.md:33)

- **反証されうる条件:** 実在する cap-lift schema が「未裁定を各義務の FAIL に写像する」と既裁定で定めている場合。

- **成果物影響:** cap と受理集合は同じく閉じるが、proof chain と試行台帳が本来の `P10 unmet` を `P4 FAIL` と誤記し、後続 wave が誤った解除条件を追う。

### B-M4 — 「他文書の更新 0 件」は誤り

- **主張:** living docs に複数の stale 記述がある。`decisions.md` の byte budget は障害ではなく、更新を省く理由にならない。

- **根拠 — 更新すべき箇所:**
  - `docs/phase3.md:463-477`: 択一 3 を未裁定、未裁定択一 6 件としている。択一 3 採用、D138、U2/U3/U5、機構未実装という現在地へ更新する。[phase3.md:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3.md:463)
  - `docs/phase3-s8c-autonomous-trial-runbook.md:104-121` と `:196-207`: 「択一 7 件未裁定」が stale。P4 必須、P6 二分、新 D を cap-lift 条件へ参照させる。[runbook:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:104)、[同:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:205)
  - `docs/phase3-8c-preregistration.md:44-48`: budget=1 の主張可否は既に「不可」と裁定済みなのに未裁定とする。[prereg:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-8c-preregistration.md:44)、[裁定記録:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/archive/worklog-phase3-0803-122.md:8)
  - `docs/phase3-8c-preregistration.md:69-72,118-124`: 「T-244 の裁定」だけを条件とし、condition 11 を未裁定扱いする。実装・P1〜P10・D96・新 D の評価を明示する必要がある。[prereg:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-8c-preregistration.md:69)、[同:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-8c-preregistration.md:118)

- **根拠 — 触ってはいけない箇所:**
  - `docs/phase3-main-experiment.md` は全体を変更しない。特に旧 architecture の ablation は凍結履歴である。[main experiment:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-main-experiment.md:40)、[pin:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/s1-freeze/known_axes_freeze.json:623)、[D121:5856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5856)
  - prereg の 8b 正本を指す表・判定基準は U2 のついでに書き換えない。[prereg:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-8c-preregistration.md:52)
  - 前 wave README と裁定資料は凍結スナップショットなので更新しない。[README.md:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-03_t244-p6-contract/README.md:6)
  - D121/D138 本文は in-place 編集せず、新 D で supersede する。

- **根拠 — budget:** `decisions.md` は living-doc budget 対象外で、`check_docs.py` は D 見出し重複を検査するだけである。[check_docs.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/check_docs.py:29)、[同:3183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/check_docs.py:3183)。hook テストもサイズの下限検査なので追記で壊れない。[test_hooks.py:1377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/tests/test_hooks.py:1377)

- **反証されうる条件:** 現 checkout より後の commit で上記 living docs が既に更新され、この wave がその commit を取り込む場合。

- **成果物影響:** stale runbook/prereg は、満たしていない U2/P4/P6 条件を飛ばして多世代を受理するか、逆に解決済み裁定を待ち続け、certified 集合・proof 参照・正式試行台帳を分岐させる。

### B-M5 — 未実装・未評価の状態を「決定済みの status」として書きすぎる

- **主張:** 現在の P4/P6 status は実 artifact を評価した結果ではない。新 D は U2 の規範、既裁定、現在の実装事実を分離し、合成した評価結果を決定として記録してはならない。

- **根拠:** cap-lift application と入力 field は存在しない。[brief.md:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/brief.md:33)。D138 は機構を実装しないと明記する。[decisions.md:6774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6774)。それでも plan は「現況 P4=`FAIL`、P6=`NOT_IMPLEMENTED`」を決定 (7) として置く。[plan:55](/work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:55)

  新 D に必要なのは次の分離である。

  - **新規決定:** P6 の `NOT_IMPLEMENTED` は失敗、実装済み `NOT_CLAIMED` だけ免責。
  - **既裁定の参照:** P4 は択一 3 採用により必須、U3 は帰納段採用、U5 は構造化 witness 新設。
  - **現在の事実:** P6 機構は未実装、上限は 1、cap-lift は未結線。
  - **未裁定:** 五値 enum、完全 witness schema、未知状態の個別 status、全体の正効果条件。

- **反証されうる条件:** 実在する cap-lift application をこの wave で評価済み、または上記追加規則が別途ユーザー承認済みの場合。

- **成果物影響:** 放置すると proof chain が存在しない評価を測定済み status として引用し、試行台帳と後続の cap-lift 判定が provisional 規則を確定 decision と誤認する。

## 総括

- blocker: **2 件**
- major: **5 件**
- nit: **0 件**
- 判定: **本 wave は現 brief / plan のまま進めてはならない。** worklog (126) を取り込んで段 1 brief と段 2 plan を再作成し、P4 は既裁定の必須条件として別扱い、U2 の新 D は P6 二分へ縮めるべきである。
- pytest、`check_docs.py`、その他のテストは実行していない。静的読取と grep のみであり、緑は主張しない。