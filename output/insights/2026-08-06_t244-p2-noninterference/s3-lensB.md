判定は **NO-GO**。必読資料はすべて読めた。`cfda4abec7ec` を基準に静的読取と独立 `rg` を行った。ホストは `pegasus02` であり、指示どおり `pytest` は実行していない。

## BLOCKER

### BLOCKER-1 — U-1(i) を別仕様へすり替えている

- **(a) 何が壊れるか:** 親 brief の authority は「origin scope の不透明 ID」だが、プランが実装するのは campaign-local な出現順ラベルである。プラン自身が「origin-scope ID ではない」と認めているため、このまま `U-1 実装済み` と台帳へ記録することはできない。また同じ `variant` という field が、trusted report では実 ID、critic payload では `candidate-0001` を意味する二義的な型になる。
- **(b) 根拠:** [brief.md:11](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/brief.md:11>) に対し、[plan.md:64](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:64>)、[plan.md:77](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:77>)、[plan.md:317](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:317>) は明示的に campaign-local としている。既存 `origin_id` は manifest 全体から導出される 64 hex である [reflux_origin_ledger.py:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_origin_ledger.py:450)。authority は実際に空である [reflux_origin_authority_v2.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_origin_authority_v2.json:1)。独立 grep では `candidate-0001` の既存出現は 0 件だったため、字面衝突ではなく意味・型の衝突である。
- **(c) 最小是正案:** U-10/authority を解かずに進むなら、ユーザーへ再裁定を返して U-1 を「8c campaign-local label」に縮小し、U-1 完了を名乗らない。既存裁定を維持するなら origin authority へ束縛する設計が必要である。どちらでも `variant` を流用せず、versioned な `critic_candidate_label` 等の別型にする。

### BLOCKER-2 — 独立棚卸しで、射影されない現役 critic consumer が残った

- **(a) 何が壊れるか:** 8c の再描画だけを修正しても、standalone loop、sort、trigger-gating、red consumer、critic CLI からは生 `variant/src_token` が引き続き critic へ届く。「全棚卸し」および P4 は成立しない。
- **(b) 根拠:** プランは projector の既定値を `None` とし、既存 caller の生描画を意図的に維持する [plan.md:10](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:10>)。独立 `rg` では production の `make_critic_digest()` 呼出しが 5 箇所あった: [p3_s4_loop.py:847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:847)、同 `:959`、[p3_s4_loop_sort.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_sort.py:340)、同 `:477`、[p3_s4_loop_trigger_gating.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:749)。さらに直接描画が [p3_s4_red.py:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_red.py:199) と [digest.py:709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:709) にある。前者は自ら「critic の読みに渡す」と規定している `p3_s4_red.py:25-29`。runbook も digest を critic に渡す [phase3-s4b-runbook.md:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/phase3-s4b-runbook.md:102)。親 brief の「production 3」はこの二つの直接 consumer を落としている。
- **(c) 最小是正案:** critic-facing API では projector を必須にし、`None` 既定を廃止する。上記 7 箇所を移行し、直接 `render_rejections()` を critic 用に呼べない静的検査を置く。歴史 fixture/CLI を scope 外にするなら、raw diagnostic と改名して critic handoff を機械的に禁止する裁定が必要である。

### BLOCKER-3 — baseline-red／関係テストは記述どおりには成立しない

- **(a) 何が壊れるか:** no-WAL fallback は `variant` しか登録しないのに、fixture digest は非空の `src_token` sentinel も射影させる。src-token を実際に試験すれば「未知 ID」で失敗し、無視すればそのチャネルを検査していない。さらに structure-aware fake renderer は実物の loader/renderer を通らないため、production の取り残しがあっても critic bytes を同一にできる。
- **(b) 根拠:** factory は `fallback_variants` のみ [plan.md:47](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:47>)、未知の非空 ID は拒否する `plan.md:60-61`。一方、試験は no-build/no-WAL `plan.md:130-140` で variant と src-token sentinel を入れ、`make_critic_digest` を fake renderer に置換する `plan.md:141`。実物 `make_critic_digest()` は admitted campaign を要求する [p3_s4_loop.py:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:285)。
- **(c) 最小是正案:** 実 `BUILD_START` を含む admitted synthetic WAL を作り、実物の loader、`make_critic_digest()`、`render_rejections()` を通す。軽量 fallback を残すなら、variant/src-token/attempt/receipt の構造化 tuple を一括登録する。fake renderer を baseline-red の受入根拠にしてはならない。

### BLOCKER-4 — legacy 許容が同じ v2 のまま fail-open になっている

- **(a) 何が壊れるか:** 将来 producer が `declassifications` を黙って出さなくなっても、formal completeness はそれを legacy v2 と解釈して受理する。producer unit test は CI 上の退行を検出できても、artifact gate の欠落受理を閉じない。また `variant` の意味と report 内 role-event の形を変えながら、payload/report とも同じ v2 を名乗る。
- **(b) 根拠:** 欠落を legacy として許す設計は [plan.md:202-205](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:202>)。現行は payload/report とも v2 [p3_autonomous_workload_trial.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:142)。completeness は role-event の必須 subset だけを見る [autonomous_trial_completeness.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/autonomous_trial_completeness.py:183) うえ、report/start が現 producer version と一致することしか識別しない `:450-454`。D118 は payload の意味変更時に version を上げると明記する [decisions.md:5647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/decisions.md:5647)。なお plan の account 例は object `plan.md:172-188`、skip は `declassifications: []` `plan.md:200` で、field の単一型も未定義である。
- **(c) 最小是正案:** payload と report を v3 に上げ、v3 の全 auditor attempt では account を必須かつ exact shape にする。v2 は明示的な legacy parser 分岐だけで受理する。v3 artifact から field を削除すると completeness と registry acceptance が必ず拒否する負例を追加する。`declassifications` は常に list とし、通常 auditor は 1 要素、非開示は空 list と固定する。

## MAJOR

### MAJOR-1 — declassification account が開示値を独立検証できない

- **(a) 何が壊れるか:** account と value hash は開示 payload を作った同じ producer が同時生成する。completeness が持つのは payload 全体の SHA-256 と自己申告した leaf hash だけであり、`/working_diff` の存在・値や `diff_digest = sha256(working_diff)` を再計算できない。これは前 wave の自己参照所見を会計形式へ移しただけである。
- **(b) 根拠:** `_invoke()` は payload 全体の hash だけを event に入れる [p3_autonomous_workload_trial.py:917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:917)。report preview は `working_diff` を除去する `:1586-1589`。fixture provider は payload artifact を永続化しない `:421-431`。Claude provider は payload file を保存するが [claude_projected_provider.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/claude_projected_provider.py:253)、valid role-event はその path を束縛しない。
- **(c) 最小是正案:** canonical provider payload の path、bytes hash、role/invocation binding を event/report に含め、completeness が対象 JSON pointer と transform を再計算する。あるいは leaf commitment/Merkle proof を記録する。そこまでしないなら「自己申告 annotation」と呼び、completeness gate や U-2 解決を名乗らない。

### MAJOR-2 — U-3 は checkout 回帰テストであって artifact の schema identity ではない

- **(a) 何が壊れるか:** test-only の二値を追加しても、既存 artifact consumer は引き続き `SCHEMA_ID` または `schema_ref + canonical_emitter_sha256` だけを見る。emitter+32-golden の複合 identity を欠く artifact が ledger 上で同じ schema として受理されるため、`U-3 実装済み` は過大である。
- **(b) 根拠:** production 無変更は [plan.md:209-231](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:209>)。現行 `SCHEMA_ID` は単一文字列 [reflux_ir.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:19) で、trigger binding もそれだけを記録・検証する [trigger_gate_binding.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/trigger_gate_binding.py:178)。origin manifest の candidate IR は二 fieldだけ [reflux_origin_ledger.py:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_origin_ledger.py:260)。
- **(c) 最小是正案:** domain-separated な複合 identity の canonical schema を定義し、検証済み literal digest を production manifest/binding validator が読む形にする。production が golden module を importする必要はない。artifact identity に接続しないなら `EXPECTED_IR_EMITTER_GOLDEN_REGRESSION_ID` 等へ改名し、既存 `SCHEMA_ID` とは別物で U-3 未完と明記する。

### MAJOR-3 — 「公開 P」への分類で候補由来の開いた文字列を隠している

- **(a) 何が壊れるか:** liveness `extra` は任意 key/value の開集合で、renderer は全値を critic に出す。二つの ID key だけを射影しても、`error` などへ候補依存文字列を追加できる。anomaly edge、integrity notes、diff evidence も同様であり、それらを P と宣言して固定するだけでは情報依存を制約しない。
- **(b) 根拠:** loader は abort payload のほぼ全 field を `extra` に入れる [digest.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:301) うえ、renderer は全部を描画する `:624-631`。producer は `extra` を無制限に mergeする [pipeline.py:711](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/pipeline.py:711) し、`trace-parse-error` では例外文字列を入れる `:859-860`。diff evidence は candidate text の長さと短縮 hash を含む [diff_quarantine.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/diff_quarantine.py:319)。プランはこれらを P または広い S domain 外とするだけ `plan.md:92-93`。
- **(c) 最小是正案:** critic renderer ごとに exact recipient schema を設け、未知 `extra` key は拒否する。公開する failure reason/count と明示 declassification を分離し、候補依存値を一つずつ変える関係テストを置く。非 canonical diff evidence は正当な scope 外候補になり得るが、D パッケージで残余として明示し、P2 closure には数えない。

### MAJOR-4 — 「候補集合不変」は WAL に限ればよいが、report/acceptance への波及が欠落している

- **(a) 何が壊れるか:** build/certify/reject の WAL 集合は射影が drive 後なので静的には不変と見込める。しかし未知 ID 拒否は候補処理後に generation を partial にでき、role-event 追加は report bytes と acceptance receipt hash を変える。親 brief の影響記述を formal trial 全体へ一般化できない。
- **(b) 根拠:** plan 自身も boundary acceptance policy の変更を認める [plan.md:235-249](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:235>)。raw harness は先に report recordへ置かれ [p3_autonomous_workload_trial.py:1696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1696)、その後 critic payload を作る。例外は partial/supervisor-error 化される `:1273-1307`。formal registry は completeness を実行 [trial_registry.py:1852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/trial_registry.py:1852) し、report/journal bytes を receiptへ hashする `:2398-2402`。
- **(c) 最小是正案:** 「不変」は WAL candidate decision set に限定する。D96 の影響面へ trial terminal status、report schema、journal、acceptance receipt を追加し、certified WAL 後の projection failure が complete report/receiptにならない境界テストを置く。

### MAJOR-5 — mutant 12件のうち複数が帰属不成立または非 production である

- **(a) 何が壊れるか:** mutant kill 数をそのまま非干渉検出力として記録すると、複合変異、将来 policy pin、test 自身の変異が production leakage mutation と混在する。
- **(b) 根拠:** 事前登録表は [plan.md:294-313](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:294>)。静的判定は次のとおり。実測はしていない。

| # | 静的帰属判定 |
|---:|---|
| 1 | raw harness leak を戻すので本来は成立。ただし指定関係 test が BLOCKER-3 により現状実行不能。 |
| 2 | raw digest leak を戻すので方向は成立。ただし fake renderer が殺すのは再描画 plumbing だけで、実 renderer/caller の帰属にならない。 |
| 3 | kill 見込みだが `variant` と `src_token` の二変異を束ねており非原子的。 |
| 4 | 同上。liveness header の二チャネルを分割すべき。 |
| 5 | 同上。diff header の二チャネルを分割すべき。 |
| 6 | atomic な raw verify-abort leak。指定 test での kill は静的に妥当。 |
| 7 | attempt と receipt の二変異を束ねる。さらに未知 `extra` key の漏洩を検出しない。 |
| 8 | module-global reuse の具体的 patch が未定義で、指定 test も BLOCKER-3 の影響を受ける。cross-campaign linkability mutant として exact singleton を定義すべき。 |
| 9 | WAL fixture が複数候補なら unit test は落ちる見込みだが、cap=1 の現発火範囲では観測差がない。現行漏洩 mutant ではなく将来 ordering contract pin。 |
| 10 | 既存の意図的開示を未会計にする mutation。U-2 の会計 mutationとしては有効だが、新しい recipient leakage を作るものではない。 |
| 11 | successor の将来 policy metadata だけを弱める。現 sink bytes は不変で、current noninterference mutationではない。 |
| 12 | test helper 自身の変異で production behavior は変わらない。production mutation として帰属不成立。 |

- **(c) 最小是正案:** 3/4/5/7を一 field 一 mutant に分割する。9/11を diagnostic policy pin と明記する。12は実 artifact identity consumer の変異へ置換する。さらに「v3 account 欠落」「alternate critic caller が projector を渡さない」「未知 liveness extra」「composite identityから golden hashを除く」を登録する。

### MAJOR-6 — 親 brief の所有分割と production 編集点が一致しない

- **(a) 何が壊れるか:** 同一ファイルを A/B が同時編集する衝突は現計画にはないが、projector の正本となる `p3_s4_loop.py` が誰の所有にも入っていない。mutant #8/#9も「所有範囲内」という主張が成立しない。
- **(b) 根拠:** 親 brief の Owner A は autonomous trial と digest の二ファイルだけ、Owner B は tests のみ [brief.md:80-84](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/brief.md:80>)。一方、プラン最初の production 編集点は `p3_s4_loop.py` [plan.md:9-10](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:9>)。
- **(c) 最小是正案:** 実装前に brief を更新し、Owner A または親へ `p3_s4_loop.py` と全 critic consumer 移行を明示的に割り当てる。B は test-only patch に限定する。

### MAJOR-7 — 前 wave の real 所見を閉じた扱いにできない

- **(a) 何が壊れるか:** `docs/phase3.md` に U-1〜U-3 実装済みと書くと、前 wave の real 所見のうち少なくとも次を誤って close する。
- **(b) 根拠:** 前 wave 台帳は [s4-adjudication.md:96-118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/s4-adjudication.md:96)。対して phase 更新案は [plan.md:29](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:29>)。

| 前 wave 所見 | 閉じられない理由 |
|---|---|
| A-B1 / B-B1 | 8c 一経路以外の raw critic consumer が残り、U-1 自体も origin scope でない。 |
| A-B2 / B-B2 | policy 選択はユーザーが解いたが、account は自己申告かつ同一 v2 欠落許容。 |
| A-B3 / A-B4 | fake renderer と開いた `extra` により、値依存 closure は未成立。 |
| B-B3 / A-M2 | preimage の選択は解けたが、test-only identity は artifact consumer に接続されない。 |
| A-M3 / B-M3 | mutant の複合変異、cap=1 dormant mutation、test mutation が残る。 |
| B-M4 | 「非干渉」は実 renderer全体・全 consumer・artifact外観測を閉じておらず、8c cap=1 conditional sink test が名乗りの上限。 |

  A-M1/B-M1 の payload 外観測と B-M2 の terminal-report 問題は、プランが残余化または runtime gate 回避しているだけで、解決ではない。B-N1 の exact key維持と B-N3 の計算ノード dispatch は計画上は是正方向にある。
- **(c) 最小是正案:** phase/decision の close matrix を所見 ID 単位で書き、上表は open のまま残す。実装名は「8c cap=1 critic recipient projection + conditional sink equality」までに限定する。

## 総括

- **NO-GO。現プランを U-1〜U-3 実装 wave として land してはならない。**
- 最大の理由は、origin-scope ID という裁定を campaign-local ordinal に無断で置き換えていること。
- projector が opt-in のため、独立棚卸しで複数の現役 critic consumer が生 ID のまま残った。
- baseline-red の fixture は fallback の情報不足で、全チャネルを試せば実装後にも失敗する。
- `declassifications` 欠落を同じ v2 で許す completeness は fail-open である。
- declassification account は開示 payload を独立再計算できず、自己申告会計に留まる。
- U-3 の二値は test 回帰 pin であり、既存 schema/origin artifact identity には接続されない。
- mutant 12件には複合変異・将来 policy pin・test-only変異が混在し、全件を production kill と数えられない。
- 所有分割も production 正本 `p3_s4_loop.py` を落としている。
- `pytest` は実行しておらず、緑は主張しない。