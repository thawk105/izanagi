## 受理集合への影響

- `A-01 / refuted / 実体:` プランどおりの変更だけなら `CERTIFIED_ACCEPTANCE` の campaign 受理集合は広がらない。現行順序は通常 admission、purpose 別 epoch gate、全 COMMIT の persisted certification、token 付き view 発行である。[artifact_admission.py:1247-1287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1247)。`current-closure-unavailable` の catch は [artifact_admission.py:963-970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:963)、persisted 検査は同 1264-1271、token 発行は同 1278-1286、exact 型拒否は [artifact_admission.py:1311-1317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1311) に残る。  
  `成果物影響:` 記述どおり実装されれば、新たに certified 選択へ入る campaign はない。ただし optional schema field により historical report JSON の受理集合は意図的に広がる。

- `A-02 / real / 実体:` これはプラン起因ではないが、現行 token は module global の `_CERTIFIED_VIEW_TOKEN` である [artifact_admission.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:71)。外部コードはこの値を読み、E1 の historical view の exact fields を使って `CertifiedCampaignView(..., _certification_token=A._CERTIFIED_VIEW_TOKEN)` を構築できる。constructor は token identity と E1 だけを検査し [artifact_admission.py:339-367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:339)、`require_certified_campaign_view` は exact 型しか検査しない。既存テストは `object()` という誤 token だけを試している [test_artifact_admission.py:1619-1638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1619)。  
  `成果物影響:` current closure と persisted COMMIT を通っていない exact certified view が型境界を通る。replay capability を別途検査する consumer は拒否できるが、exact 型だけを頼る certified consumer は選択・レポートへ使用しうる。既存問題であり本プランによる拡張ではない。

手順 2〜5 の実装対象 `layer3_report.py` と `layer3_schema.json` は射影外なので、その実コードの順序は独立確認できない。上の `A-01` はプラン記述 [s2-plan.md:15-47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:15) がそのまま実装される場合の判定である。

## 正例の恒真性

- `P-01 / real / 実体:` 正例の構造部分は現行実装ですでに通る。既存テストは live closure を dirty にした後も `HISTORICAL_RAW` が exact `HistoricalCampaignView` と同じ E1 を返すことを確認済みである [test_artifact_admission.py:1590-1614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1590)。したがって新正例のうち「歴史閲覧成功」「E1 維持」「epoch rejection なし」は新機能を証明しない。early return の回帰 pin としては有効である。  
  `成果物影響:` この部分だけを新成果と数えると、実際には新表示が report まで届かなくても D1245 を実装済みと記録しうる。

- `P-02 / refuted / 実体:` 正例全体が無変更で通るわけではない。現行 `HistoricalCampaignView` には `current_verifier_conformance` が存在せず、最後の property は `verifier_assessment_basis` で終わる [artifact_admission.py:374-390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:374)。直接 `view.current_verifier_conformance == "unknown"` と書けば現行コードは `AttributeError` で赤になる。  
  `成果物影響:` direct attribute と report の direct key を assert する限り、field 未実装を緑にする恒真 assert にはならない。`getattr(..., "unknown")` や `.get(..., "unknown")` は使ってはならない。

- `P-03 / real / 実体:` property が常に `"unknown"` を返す設計 [s2-plan.md:15-19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:15) は、closure 不在との因果を検査しない。「historical purpose は current conformance を評価していない」という表示契約を固定するだけである。  
  `成果物影響:` property pin は report の意味値を固定するが、historical gate の fail-open や certified gate の fail-closed を保証しない。構造正例と診断値 pin を別テスト、別変異分類にすべきである。

## 負例の向き

- `N-01 / refuted / 実体:` 「catch が発火し、exact `CampaignVerifierEpochRejected(E1-stale, current-closure-unavailable)` に変換される」ことが目的なら向きは正しい。fixture で tracked file に bytes を追記すれば `disk != HEAD blob` が必ず成立し [contract_loader_binding.py:348-359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/contract_loader_binding.py:348)、中央 gate が exact reason へ変換する。  
  `成果物影響:` catch の削除や capture 全 bypass により、例外型・reason または certified view 発行が変われば確実に赤になる。

- `N-02 / real / 実体:` 「persisted COMMIT 検査より前に発火する」という時点までは固定できない。共通 fixture の COMMIT は正常であり [test_artifact_admission.py:501-530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:501)、検査順を COMMIT-first に変えても、最後に同じ closure 例外が上がって負例は通る。現行順は epoch gate が 1263、persisted 検査が 1264 以後である。  
  `成果物影響:` gate 順序が変わり、将来の不正 COMMIT で診断 reason や拒否時点が変わってもテストと変異台帳は検知しない。時点を要求するなら call-order sentinel が必要で、二重に不正な fixture を作るべきではない。

## 変異候補の単一理由性

| 候補 | 判定 | 独立検査 |
|---|---|---|
| 1. historical early return 削除 | `refuted` | 記録閉包検査は commit blob だけを読む [contract_loader_binding.py:386-401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/contract_loader_binding.py:386)。E1 fixture では前段を通り、削除時だけ live capture へ落ちる [artifact_admission.py:953-971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:953)。境界変異として単一理由。 |
| 2. certified capture/catch bypass | `real` | “bypass” が曖昧。capture 全体を除けば invalid campaign が view まで進む。一方、catch だけ除けば raw `ContractLoaderBindingError` で拒否されたままで、受理集合は広がらない。負例は両方を kill するが意味が違う。exact patch を事前登録すべき。 |
| 3. property の戻り値変更 | `real` | admission は変わらず direct property assert だけが赤になる。さらにプラン自身が schema に `const: "unknown"` を置くため [s2-plan.md:32-35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:32)、report 経路では後段 schema も同じ非 unknown 値を拒否しうる。境界変異でなく診断感度 pin として別枠に置くべき。 |
| 4. historical report 投影削除 | `refuted` 条件付き | プラン上は field が optional なので schema は欠落を拒否せず、report field 欠落 assert だけが赤になる [s2-plan.md:105-108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:105)。ただし実 source は射影外で独立確認不能。診断投影変異であり admission 変異ではない。 |
| 5. field を required 化 | `refuted` 条件付き | プラン上は field を欠く保存済み report の schema 拒否だけに絞れる [s2-plan.md:110-113](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:110)。後方互換性変異である。実 schema と fixture は射影外。 |
| 6. certified-field 禁止削除 | `refuted` 条件付き | well-formed certified report へ `"unknown"` を後注入して schema を直接呼ぶなら、禁止 conditional だけの fail-open になる [s2-plan.md:115-118](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:115)。campaign 受理ではなく certified report schema の変異。実 schema は射影外。 |
| 7. certified 昇格時の除去削除 | `real` | 同 field は後段 certified schema が拒否する設計なので、mutation は安全性の fail-open ではなく「正常 certified report が生成不能になる」liveness 変異である [s2-plan.md:120-123](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:120)。境界変異と同じ登録枠に置くと kill の意味が混ざる。 |

候補 3 と 4 は診断表示、5 は保存済み report 互換性、6 は certified report schema、7 は producer/schema liveness である。受理境界の変異は 1 と、exact に「capture 全体を除去」と定義した 2 だけである。

## fixture の過剰決定

- `F-01 / real / 実体:` 正例は一つの test 内で、実体 capture の事前エラー、exact view 型、E1、property 値、例外なしを同時に要求する [s2-plan.md:60-73](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:60)。複数の独立な変更で同じ node が赤になるため、mutation kill reason は pytest の赤だけでは一意にならない。  
  `成果物影響:` 変異台帳が「historical gate を kill」と記録しても、実際は property typo や fixture の recorded binding 失敗だった可能性が残る。

- `F-02 / real / 実体:` 負例の「certified view は発行されない」は exception assert の言い換えで、独立観測ではない [s2-plan.md:75-80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:75)。また直接 capture の事前確認と certified API の拒否は、capture 実装変異に対して二重の観測点になる。  
  `成果物影響:` capture 内部変異を誤って登録すると、一つの入力が setup と gate の両方で赤になり、単一理由性が崩れる。プランが capture 内部を候補外にした判断は正しい。

同一 fixture を正負で共有すること自体はよい。構造正例、診断 property、report 投影、certified 負例を別 node に分けるべきである。

## 親の実測の検証

- `E-01 / refuted / 実体:` 「中央 gate は `HISTORICAL_RAW` で current closure を読まない」は正しい。exact early return は [artifact_admission.py:953-960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:953)。  
  `成果物影響:` live closure drift だけを理由に historical view が `current-closure-unavailable` で拒否される経路は中央 gate にはない。

  ただし「historical API 全体が現行 source を読まない」まで一般化してはならない。前段 `_inspect_campaign` は current `artifact_admission.py` の hash を読む [artifact_admission.py:1033-1035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1033) ほか、current policy も再構築する。

- `E-02 / real / 実体:` 親の「current closure 可用性 = exact 24 path が HEAD と一致」は過大一般化である [handoff.md:152-156](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/handoff.md:152)。`capture_contract_loader_binding` は root 解決・Git top-level [contract_loader_binding.py:97-130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/contract_loader_binding.py:97)、no-follow/race [contract_loader_binding.py:158-248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/contract_loader_binding.py:158)、Git executable・ambient env・timeout [contract_loader_binding.py:251-315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/contract_loader_binding.py:251)、commit/blob 解決でも同じ `ContractLoaderBindingError` を上げる。  
  `成果物影響:` report の `current-closure-unavailable` は source drift だけでなく Git・root・race 障害も同じ reason に畳む。新しい real fixture は drift 一種だけを固定する。

- `E-03 / refuted / 実体:` `artifact_admission.py` が exact 24 path に含まれることは正しい。[campaign_lock.py:49-74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/campaign_lock.py:49) の line 57 にあり、列挙数は 24。  
  `成果物影響:` real worktree root を使う certified capture は、このファイルの未 commit 編集で fail-closed になる。

- `E-04 / real / 実体:` 「編集中は certified 経路のテストが赤」は全 certified test への一般化として誤り [handoff.md:57-60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/handoff.md:57)。`_committed_closure_repo` は独立した synthetic 24-path repo を commit し [test_artifact_admission.py:403-423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:403)、certified 正例は loader module の `_REPO_ROOT` をそこへ差し替える [test_artifact_admission.py:1174-1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:1174)。  
  `成果物影響:` isolated fixture の certified テストは production file の未 commit 編集中でも緑になりうる。期待赤として誤分類すると実際の回帰を見落とす。

- `E-05 / real / 実体:` 「凍結成果物への bytes pin は無い」は射影内では独立確認できない。親は `FROZEN_MANIFEST` と複数の外部 file を根拠にしている [handoff.md:125-132](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/handoff.md:125) が、それらは今回の射影対象ではない。射影内には closure membership pin はあるが [test_artifact_admission.py:46-71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:46)、closure source bytes の literal pin は確認できない。  
  `成果物影響:` 親の global negative claim を根拠に manifest 再発行を省く判断は、この consult 単体では保証されない。未発見 pin があれば凍結参照や provenance test が変わる。

## 規律 7 との整合

- `R-01 / real / 実体:` プランが固定するのは low-level historical view と Layer 3 historical report だけである。親自身が `replay.load_landscape` と S-1 report は `CERTIFIED_ACCEPTANCE` を使い、closure 不在で load failure または標本 0 に degrade すると記録している [handoff.md:64-68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/handoff.md:64)。プランは purpose 変更を明示的に行わない [s2-plan.md:176-187](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:176)。  
  `成果物影響:` 親の consumer 実測が正しければ、過去 landscape の選択結果は読めないまま、S-1 report の標本数は 0 のままであり、規律 7 の利用者可視な効果は未達である。

- `R-02 / real / 実体:` `HISTORICAL_RAW` 自体にも current policy 依存が残る。`_current_policy` は現行コードから policy を再構築し [artifact_admission.py:588-591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:588)、v2 campaign の記録 policy と異なれば purpose に関係なく前段で拒否する [artifact_admission.py:1148-1152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1148)。新 fixture は campaign 作成時に常に current policy を埋める [test_artifact_admission.py:440-490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/tests/test_artifact_admission.py:440) ため、この反例を構成しない。  
  `成果物影響:` 過去に正当だった v2 campaign の policy 版が更新されると、closure unknown 表示へ到達する前に historical view 自体が読めなくなる。

D1163 は撤去対象を一つに限定している [d1163.md:6-21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/verbatim/d1163.md:6)。したがって `R-01` と `R-02` をこの wave で直ちに変更するのではなく、規律 7 と「現行の正しさ主張に必要な意味互換性」の境界として再裁定が必要である。

## 所見一覧 (ID / real|refuted / 実体 / 成果物影響)

| ID | 判定 | 実体 | 成果物影響 |
|---|---|---|---|
| A-01 | refuted | certified gate、persisted COMMIT、token、exact 型は不変 | プランどおりなら certified campaign は増えない |
| A-02 | real | module global token で exact certified view を外部構築可能 | exact 型だけの consumer に未認証 view が入る |
| P-01 | real | dirty closure の historical success は既存テスト済み | 新表示なしでも構造部分を新成果と誤認しうる |
| P-02 | refuted | property は現行型に存在しない | direct assert なら無変更実装は赤 |
| P-03 | real | `"unknown"` は状態非依存の定数 property | 診断値は固定するが admission 境界は固定しない |
| N-01 | refuted | dirty bytes と exact catch/reason | 発火自体を目的とする負例の向きは正しい |
| N-02 | real | persisted COMMIT が正常で順序 sentinel がない | 拒否時点変更が検知されない |
| M-02 | real | “capture/catch bypass” が二義的 | 同じ kill が fail-open と別例外を混同する |
| M-03 | real | property と schema の二観測層 | 境界 mutation ledger の意味が過大になる |
| M-07 | real | producer 除去を後段 schema が拒否 | safety でなく certified report liveness の kill |
| F-01 | real | 一 node に setup、view、epoch、property を併記 | mutation kill reason を一意に帰属できない |
| F-02 | real | setup capture と gate capture の二重観測 | capture 変異では赤理由が複数になる |
| E-01 | refuted | historical early return | 中央 gate に live closure 拒否はない |
| E-02 | real | root、Git、race も同じ binding error | unavailable reason が drift 以外も表す |
| E-03 | refuted | exact 24-path tuple line 57 | self-edit は real-root certified capture を拒否する |
| E-04 | real | isolated committed closure fixture | certified テスト全体を期待赤とは扱えない |
| E-05 | real | global pin 検査の根拠が射影外 | frozen 参照不変を本 consult では保証できない |
| R-01 | real | historical consumer が certified purpose のまま | landscape 不読、S-1 標本 0 が残る |
| R-02 | real | historical 前段の current policy 比較 | 過去 v2 campaign が現行 policy 差で読めない |

## 裁定パッケージ候補 (scope 外)

1. `CertifiedCampaignView` 発行権限

   - 問い: module global token を使う既存 forge 経路を別 wave で閉じるか。
   - 推奨: replay capability と同様、issuer closure と発行 registry に束縛し、exact 型検査も発行済み authority を検査する。
   - 影響: certified consumer 全体の trust boundary 変更なので D1245 wave には混ぜない。

2. 過去の certified 測定を読む第三 purpose

   - 問い: `HISTORICAL_RAW` へ単純付替えせず、記録 commit・persisted receipt は検査するが current closure は要求しない historical-certified view を設けるか。
   - 推奨: 規律 7 を利用者可視経路まで通すなら第三 purpose を裁定し、`replay.load_landscape` と S-1 の移行を別 wave にする。
   - 影響: 過去 landscape と S-1 report を保持しつつ、記録 proof chain の検査を残せる。

3. Historical view と current build policy

   - 問い: [artifact_admission.py:1150-1152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1150) の current policy 一致を historical purpose にも課すことが、規律 7 の例外となる意味互換性検査か。
   - 推奨: D1163 の「撤去は一関門だけ」と衝突しうるため、この wave では変更せず明示裁定する。
   - 影響: 裁定なしでは、closure 対応だけ実装しても一部の過去 v2 campaign は読めないまま残る。

## 総括

プランどおりなら `CERTIFIED_ACCEPTANCE` の campaign 受理集合は広がらない。一方、正例の構造部分はすでに現行実装で成立しており、新規性は定数 property と report 投影だけである。候補 3、4、7 を acceptance/fail-closed mutation として扱うのは不適切で、診断・投影・liveness に分離すべきである。候補 2 は exact mutation を定義しないと、fail-open と fail-closed の別例外を同じ kill として数えてしまう。

また、親の中央 gate と 24-path membership の実測は正しいが、「closure 可用性は HEAD 一致だけ」「編集中は certified test が一律赤」「bytes pin はない」という一般化は、それぞれ誤りまたは未立証である。規律 7 は low-level historical view では固定されるものの、certified purpose のままの consumer と current policy 比較が残るため、利用者可視経路全体では未達である。

pytest は実行していない。静的検査のみ。