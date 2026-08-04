結論は **NO-GO** です。現プランは、production で発火する経路・実在する origin 入力・実体のある anchor を持たず、段 5 へ進める条件を満たしません。

## B-1 — 未結線 leaf は「発火しない保証」と同型

**判定: real（blocker）**

brief は「P3 の四性質を実装する」としながら、既存 consumer へは結線しません（[brief.md 5–8 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-04_t244-p3-origin-ledger/brief.md:5)）。さらにプランは既存ファイルを一切編集せず、production registry も追加しません（[s2-plan.md 22–29 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:22)）。

これは因果構造として、

- live consumer が旧 policy を読み続けるため「索引」だけでは再編にならなかった D115（[decisions.md 5469–5473 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/decisions.md:5469)）
- production CLI へ届かなければ「解禁済み」は発火しない保証になるとした D122（[decisions.md 5915–5920 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/decisions.md:5915)）

と同型です。「P3 充足」ではなく「leaf 契約」と呼ぶことは虚偽の範囲を狭めるだけで、実効性を生みません。

**取るべき代替:** 現 wave は実装せず設計メモに留め、origin identity・anchor 運用・budget admission・formal consumer を裁定パッケージへ返すべきです。結線まで行う案は D96 を伴う別の縦断 wave として再起票すべきで、現在の二成果物 scope へ押し込むべきではありません。

**成果物影響:** 現行 certified 選択・材料レポート・proof chain・受理集合は全て不変です。この「影響ゼロ」自体が、leaf が発火しないことの証拠です。

## B-2 — `DW-G04` を満たさず、D121 (7) から例外も導けない

**判定: real（blocker）**

`DW-G04` は、条件を満たす既存 artifact path または計測 ID を brief に書けない条件付き機能を、設計メモに留めるよう要求します（[core.md 57–60 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/dev-wave/core.md:57)）。brief にあるのは将来の cap-lift 依存だけで、発火 artifact／計測 ID ではありません（[brief.md 49–53 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-04_t244-p3-origin-ledger/brief.md:49)）。

既存 artifact には `reflux:"on"` が実在しますが（[campaign.lock 1 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/campaign.lock:1)）、これは旧架構の ablation です。D121 自身が、新 draft の還流形とは別物であり、8c の treatment 定義も未裁定としています（[decisions.md 5856–5861 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/decisions.md:5856)）。

D121 (7) は P3 を cap-lift の必要条件として列挙しただけで、`DW-G04` の免除や実装順を認可していません。むしろ閉集合を先に定義しないと恒真化すると警告し、無条件義務は全件未充足としています（[decisions.md 5842–5854 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/decisions.md:5842)）。未解決前提を guard に固める案を既成事実化として却下した D121 (b) も反対方向の根拠です（[decisions.md 5870–5873 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/decisions.md:5870)）。

**成果物影響:** 現行四成果物は不変。将来だけを条件とする dead leaf が増え、cap-lift の実効 gate は増えません。

## B-3 — `DW-O13` 違反: `origin_id` が実在 field と結び付かない

**判定: real（blocker）**

`DW-O13` は「入力が実成果物のどの field に存在するか」を設計前に確認し、同名識別子を二義化しないよう要求します（[operations.md 74–76 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/dev-wave/operations.md:74)）。D75 の元事故も、実物 JSON に存在しない入力と同名 `H` の混用でした（[decisions.md 3031–3037 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/decisions.md:3031)）。

現行関係は次です。

- `trial` は `CampaignConfig` の field で、campaign identity に含まれる（[model.py 63–75 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/campaign/model.py:63)）。
- `campaign_id` は `spec_content / ccbench_commit / search_config / trial` の正準 preimage から導出される（[ident.py 125–156 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/campaign/ident.py:125)）。
- `run_id` は既存例では時刻等を含む実行単位 ID である（[s8b_floor_campaign.py 3167–3176 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/campaign/s8b_floor_campaign.py:3167)）。
- 設計上の `reflux-origin` はこれらより上位で、複数 campaign を束ね、`trial`／invocation ID／process 分割名を含めない（[README.md 193–219 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-01_t244-reflux-design/README.md:193)）。

ところがプランは `origin_id` を caller 提供の任意 64hex とし、preimage を計算・検証しません（[s2-plan.md 117–134 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:117)）。registry entry も `manifest_sha256` を持つだけで、その manifest schema や `origin_id = H(canonical origin preimage)` を検証しません（[s2-plan.md 251–256 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:251)）。

したがって `reflux_origin_id` は「設計本文の supra-campaign identity」と「caller が選ぶ不透明 handle」の二義になります。別 ID を渡して予算を新品化しない機械的根拠がありません。

**成果物影響:** 現行四成果物は不変。結線後は arbitrary origin 分割により予算受理集合が不当に広がり、formal proof が別 campaign 間の同一 origin を証明できません。

## B-4 — tracked registry は anchor ではなく、未実装の運用仮定

**判定: real（blocker）**

プランの削除耐性表そのものは比較的正直です。registry が保持される場合だけ ledger 削除を検出し、registry との協調 rollback／全面書換えは検出不能としています（[s2-plan.md 384–395 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:384)）。

ただし、次の主張は実装より強すぎます。

- brief は tracked registry を「anchor」と呼び、削除を budget reset ではなく使用不能にするとします（[brief.md 32–34 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-04_t244-p3-origin-ledger/brief.md:32)）。
- プランの総括も「append-only tracked registry」を実装の核と呼びます（[s2-plan.md 483–487 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:483)）。
- 実際には registry file を追加せず（[s2-plan.md 27–29 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:27)）、leaf は `git ls-files` も実行しません（[s2-plan.md 168–170 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:168)）。

区別すると、

1. **削除検出:** 保存された committed head と ledger の不一致は検出できる。
2. **予算 reset 防止:** leaf が全経路で必須の場合だけ fail-closed になる。現状は consumer 未結線なので保証しない。
3. **Git tracking:** 改竄の可視化であって改竄検出・真正性ではない。
4. **未 commit:** runtime head は working-tree diff にしか存在せず、registry を HEAD へ戻して ledger も消せば diff は消える。commit/fold の主体・頻度はプラン自身が未解決と認めています（[s2-plan.md 487 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:487)）。
5. **`anchor: absent`:** API の使用不能であって削除検出ではない。プラン自身もその点だけは明記しています（[s2-plan.md 393–395 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:393)）。

T-126 の committed policy は、単に tracked path を読むのではなく live bytes と指定 commit の Git blob を照合します（[identity.py 161–167 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/identity.py:161)）。本案には対応する trust anchor がありません。

**成果物影響:** 現行四成果物は不変。将来 mandatory consumer を付けても、同一 UID・別 worktree・checkout 巻戻しでは budget reset を防げず、誤った origin proof を受理し得ます。

## B-5 — 値の default は避けたが、`constraints=()` が既定政策になる

**判定: real（admission blocker）**

狭い疑い、すなわち「missing I/Q/K が暗黙の 0 または unlimited になる」は反証されました。プランは三値を必須にし、`0` は明示政策、`None`／欠落 fallback は禁止しています（[s2-plan.md 399–408 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:399)）。

しかし下限制約は `constraints=()` を明示的に受理します（[s2-plan.md 410–421 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:410)）。ユーザー裁定は `Q >= 1 + 32R + E_min` を予算決定の制約として使うことであり、値だけを未決定としています（[worklog.md 584–586 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/worklog.md:584)）。空 tuple を許すと、authority がこの下限を一度も適用しない policy を正規値として発行できます。

カウンタ構造自体は値非依存にできます。しかし「U4 を必須にする mode」「R/E_min の根拠」「下限を持たない origin が存在してよいか」は構造です。本案はそれを「任意 constraint tuple」として既成事実化しています。

また consumer 未結線の現行経路では、policy 欠落は fail-closed ではなく、そもそも ledger を通らないため実質 unlimited です。

**成果物影響:** 現行四成果物は不変。結線後、空 constraint policy が受理されれば予算受理集合が裁定済み下限より広がります。

## B-6 — P3 単独には局所的意味しかなく、P7 不在では保証にならない

**判定: real（記録上の blocker）**

D121 は P3 と P7 を別条件としているため、P3 の局所契約に意味が全く無いわけではありません。しかし P7 は formal consumer が origin proof を要求する条件であり、D96 対象です（[decisions.md 5846–5849 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/decisions.md:5846)）。

P7 が無い状態で ledger が保証できるのは、「正しい registry と policy を渡し、この API だけを使う協調 caller」に対する FSM/CAS/replay だけです。次は保証しません。

- planner/provider 前に予約されたこと
- campaign と origin の正しい束縛
- 全正式経路が budget を通ったこと
- 材料レポート／proof chain が ledger head を参照すること
- ledger proof のない候補が certified 集合へ入らないこと

記録上の芽は、brief の表題が `D121 P3` で、scope が「P3 の四性質を実装する」と書く点（[brief.md 1–8 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-04_t244-p3-origin-ledger/brief.md:1)）と、「実装しなければ P3 未充足」という片方向表現です（[brief.md 51–53 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-04_t244-p3-origin-ledger/brief.md:51)）。現時点で実 worklog/decision fragment はありませんが、段 7 で「P3 実装済み」へ短縮される危険があります。

許容できる記録は「fixture-only leaf prototype、production anchor/consumer 不在、P3 は未充足」のみです。

**成果物影響:** 現行四成果物は不変。誤った完了記録が後の cap-lift 判定へ使われると、受理集合だけが不正に広がります。

## B-7 — 親 brief の四つの実測値

**判定: nit（四項目とも事実反証はできなかった。射程限定のみ）**

1. **「§8 の択一 7 件は全件裁定済み、予算値だけ未確定」:** 反証できませんでした。6 件は推奨どおり、択一 4 も対話で裁定され（[archive worklog 316–355 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/archive/worklog-phase3-0803-125-126.md:316)）、同 entry が全 7 件裁定済みと記録しています（[同 380–389 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/archive/worklog-phase3-0803-125-126.md:380)）。ただしこれは高位択一の決着であり、schema や運用まで確定した意味ではありません。

2. **「origin authority は repo 内 tracked registry から始める」:** 反証できませんでした（[同 327–328 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/archive/worklog-phase3-0803-125-126.md:327)）。ただし mutable head を同じ tracked JSONL に追記すること、commit/fold、Git blob 照合は裁定されていません。

3. **「軸 (iii) 必須化により P4 は無条件義務へ移った」:** cap-lift 前提という射程では反証できませんでした。batch cardinality・事前 commit・seal まで非公開をセットで必須化しています（[同 322–324 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/archive/worklog-phase3-0803-125-126.md:322)）。現在の一世代運転すべてに直ちに課される、という一般化だけは不可です。

4. **「本 wave では certified 選択・材料レポート・proof chain の値は変わらない」:** 反証できませんでした。consumer 非結線なら当然の帰結です（[brief.md 25–28 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-04_t244-p3-origin-ledger/brief.md:25)）。

**成果物影響:** 四項目に基づく現行成果物影響はありません。最後の項目はむしろ B-1/B-2 の非発火性を補強します。

## B-8 — T-126 との差はあるが、erratum の「ほぼ同型」も過大

**判定: real（一部反証・主張範囲の修正）**

「新規 leaf の正当化がプランに無い」は反証されました。プランは T-126 の qualification 固有 lineage・FSM・create-only 連番形式を理由に、直接共有化しないと説明しています（[s2-plan.md 474–475 行](/work/1/SFC/tanab/dev-wave-jobs/t244-p3-origin-ledger/s2-plan.md:474)）。実コードも `t126-only` lineage と専用 event grammar を強制します（[attempt_ledger.py 192–207 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/attempt_ledger.py:192)）。

一方、erratum の「crash replay とほぼ同型」は強すぎます（[brief-erratum-1.md 11–15 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-04_t244-p3-origin-ledger/brief-erratum-1.md:11)）。

T-126 が既に持つのは、

- event hash chain と replay
- pending/final の payload 同一性
- create-only event の exact-idempotence（[attempt_ledger.py 344–373 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/attempt_ledger.py:344)）
- committed policy の Git blob 照合

です。対して `SeriesFSM` は明示的に single-controller です（[series.py 243–265 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/orchestrator/qualification/series.py:243)）。T-126 は caller CAS、単一 pending origin slot、registry→ledger→registry の二ファイル durable transaction を解いていません。したがって純増は「削除耐性と予算注入だけ」ではなく、CAS・並行 writer・cross-file crash recovery も含みます。

`DW-G03` は異なる producer/consumer の独立 2 例を要求します（[core.md 52–55 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/dev-wave/core.md:52)）。T-126 内の二台帳は同一 qualification 系であり、族一般化の二例とは数えにくいです。reflux の live 縦断例が完成して初めて二例目として評価し、その後の wave で共通化を検討すべきです。今の共通化も、孤立 leaf の新設も時期尚早です。

**成果物影響:** 現行四成果物は不変。早すぎる共有化だけが T-126 qualification の受理集合へ回帰を持ち込み得ます。

## B-9 — 実効性に必要な層の大半が scope 外

**判定: real（blocker）**

| 層 | 必要な内容 | 現プラン | 扱い |
|---|---|---|---|
| Authority / identity | canonical origin preimage、issuer、scientific cell 重複発行拒否 | opaque 64hex、実 registry なし | 裁定パッケージ |
| Static authority | tracked/committed manifest と Git blob 照合 | trackedness は将来 deployment 義務 | 裁定パッケージ |
| Mutable head anchor | head の保存先、commit/fold、別 worktree、rollback、復旧 | 同一 tracked JSONL へ runtime append、運用未定 | 裁定パッケージ |
| Ledger leaf | FSM、CAS、single pending、crash replay | scope 内 | trigger/authority 決定まで設計メモ |
| Production producer | planner/provider 前の予約、trusted translator、no-refund | consumer 側として除外 | 裁定パッケージ |
| P4/P5 | batch cardinality・seal 非公開、provider/session/token 拒否 | seam だけ残し証明しない | 裁定パッケージ |
| WAL/report | ordered control events、候補集計との分離 | `WAL_STAGES` / `layer3_report.py` 非接触 | 裁定パッケージ |
| Formal proof | origin proof の必須化、issuer/schema、負例 | P7 非接触 | D96 付き独立 wave |
| Cap-lift | P1〜P10 の同時 gate と `MAX_APPROVED_GENERATIONS` | 上限 1 のまま | 全前提後の独立 wave |

producer と origin binding は設計本文が要求しています（[README.md 289–304 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-01_t244-reflux-design/README.md:289)。WAL/report の二つの consumer 問題も既知です（[同 306–331 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/output/insights/2026-08-01_t244-reflux-design/README.md:306)）。formal consumer を変える場合、D96 は新 D と境界テストの同時更新を要求します（[decisions.md 4271–4279 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p3-origin-ledger/docs/decisions.md:4271)）。

**成果物影響:** 上表の Authority、Production producer、WAL/report、Formal proof が欠ける限り、certified 選択・材料レポート・proof chain・受理集合には何も効きません。

## 総括

**NO-GO。** 現プランのまま段 5 へ進めるべきではありません。

理由は次の四点です。

- `DW-G04` を満たす既存発火 artifact／計測 ID がない。
- `DW-O13` が要求する origin 入力 field と既存 ID への機械的関係がない。
- tracked registry は実体も Git 検証も運用契約もなく、削除耐性の anchor ではない。
- consumer・P7・正式 proof が scope 外で、D115/D122 と同じ非発火構造になっている。

推奨は、現 wave を「実装しない」と裁定し、現在のプランを設計メモとして保持することです。次に、origin preimage schema、static authority と mutable head の分離、U4 policy mode、registry の commit/anchor 運用、production producer、formal consumer/D96 を一つの裁定パッケージへ返してください。

確信を持てなかった点は、`DW-G04` が「将来 prerequisite の単体 library」を例外扱いする意図を持つ可能性です。ただし正本文言にその例外はなく、仮に例外を認めても、実 registry 不在・`origin_id` 未束縛・trackedness 未検証の三 blocker は残ります。また T-126 の低層 `create_json` の耐久化実装までは監査対象外としたため、T-126 の fsync 細部は断定していません。

pytest・build は実行しておらず、緑とは報告しません。