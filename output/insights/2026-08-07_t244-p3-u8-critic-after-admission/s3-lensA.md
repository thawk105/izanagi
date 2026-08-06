結論は **NO-GO** です。静的検査のみで、ファイル変更・pytest 実行はしていません。

## real 所見

### 1. U-8 を満たすのは「通常時の時系列」だけで、commit-reveal は閉じない

裁定正本は critic を「Layer 3 admission・ledger seal・proof 書き込み」の後へ移し、proposal/raw response も seal 後に公開するとしています（[README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-05_t244-p3-design/README.md:248)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-05_t244-p3-design/README.md:252)）。一方、brief は ledger seal/proof を明示的に外しています（[brief.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-07_t244-p3-u8-critic-after-admission/brief.md:12)）。

しかも現行 critic は、既に `require_admitted_campaign()` の成功後に呼ばれます（[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1753)）。後置で増えるのは、同じ admission decision を載せた `layer3_report.json` が先に作られることだけです。critic に渡す連続値 metrics の量は変わりません。

さらに barrier は critic 後の `run-finish` を経て初めて journal hash に束縛される設計です（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:238)、[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1421)）。したがって barrier 自体は reveal 前の不変 commitment ではありません。

実際に減るのは「正常・非 crash・honest producer の実行で、metrics が `layer3_report.json` 作成より前に外部 critic へ届く」という時間窓だけです。情報量も、承認運転での candidate/admission への還流も減りません。proposal と pre-critic raw response は引き続き admission 前に書かれます（[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:990)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1682)）。

新イベントの漏洩面については、decision hash は plan どおりなら critic payload には入りません。しかし journal 読者には admission 成功時刻、処理時間を分割できる timestamp、decision の等値相関が新たに見えます。critic recipient 自身にも「呼ばれた」という事実から Layer 3 render 成功の 1 bit が追加されます。

成果物影響: certified 選択は現状変わらない一方、`attempts.jsonl` と proof chain に「commit-reveal 済み」と誤読可能な自己申告だけが増え、材料レポート・proposal/raw の pre-seal 公開は残ります。

これは D201 と U-8 の衝突として、scope を再裁定するか、保証名を「Layer 3 report 前の critic disclosure を後置した」に下げる必要があります。

### 2. schema v4 化が全 role の recipient 入力を変える

plan は `SCHEMA_VERSION` を v3 から v4 に上げます（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:382)）。しかしこの定数は journal 専用ではなく、planner/coder/auditor/critic 共通 payload に入ります（[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1058)）。Claude provider はその bytes をそのまま stdin へ渡します（[claude_projected_provider.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/claude_projected_provider.py:253)）。

したがって journal event を 1 種増やす変更が、全 role recipient への新しい disclosure になり、全 `input_payload_sha256` を変えます。実 Claude の応答、coder wire、auditor verdict、WAL、admission decision、metrics が不変とは一般化できません。

成果物影響: 全 role-attempt の payload hash、journal hash、formal lifecycle/acceptance receipt の report・journal hashが確実に変わり、LLM 応答次第では材料レポートと campaign の受理内容も変わります。

journal/run-start 用 version と role payload 用 version を分離するのが must-fix です。

### 3. decision hash gate は形式的には発火するが、意味的には自己参照

提案 checker は barrier の hash と `cells[].admission_decision` の hash を比較します（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:200)）。しかし completeness の build admission 検査は、現在は schema/status/classification の 3 値しか見ません（[autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:957)）。

したがって、任意の positive-looking decision `D` と `sha256(D)` を report/journal の両方へ置けば、barrier checker は同じ producer 由来の値同士を照合するだけです。通常 producer は後段の deep chain で緩和されていますが（[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1426)）、formal trial 受理は completeness だけを再実行し、campaign chain を呼びません（[trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/trial_registry.py:1807)）。

既存 build test も、3 field だけ設定する fake finalizer と chain 無効化で通しています（[test_p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:1908)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:1916)）。この近傍へ同型の順序テストを足しても、実 Layer 3 artifact の存在・内容・時系列は証明しません。

成果物影響: 自己整合した偽 barrier/report が formal trial receipt の受理集合へ入り、proof chain が実在しない admission 順序を参照できます。receipt は非認定なので現時点の certified 選択は変わりません。

callback 順テスト自体は M1 を kill できますが、実 finalizer・実 campaign chain を使う独立 integration test と formal registry 側の deep validation が必要です。

### 4. `partial` は trial status だけで、admitted material と正式 receipt に対して fail-closed ではない

plan は barrier 後の critic payload 構築失敗を、positive admission と barrier を残した `supervisor-error` partial として新規受理します（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:267)、[同](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:500)）。

具体的には以下が通る設計です。

1. build/harness と Layer 3 finalization が成功。
2. barrier を fsync。
3. `_build_post_admission_critic_payload` を fault injection で `ValueError` にする。
4. `supervisor-error`、positive admission、critic なし、status=`partial` として公開。

あるいは malformed critic response なら `role-invalid` partial ですが、admission は同様に残ります。

`require_admitted_campaign()` は trial status を読みません（[artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/artifact_admission.py:723)。formal lifecycle は `partial` を正規 terminal として受け（[trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/trial_registry.py:1622)）、acceptance は status が文字列であることしか追加要求せず receipt 行へ入れます（[trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/trial_registry.py:2350)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/trial_registry.py:2390)）。

また barrier 後に SIGKILL すれば Layer 3 material はあるが terminal report はない orphan ができます。`layer3_report.render()` は file fsync 後に hard-link しますが parent directory を fsync しておらず、電源断時の durability 順序もありません（[layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/layer3_report.py:584)）。

成果物影響: positive な Layer 3 材料と partial lifecycle/receipt が残ります。receipt と材料は `certifying=False` なので certified 選択は現在不変ですが、材料レポート・試行台帳・proof chain は「critic 未完了」を抱えたまま正式参照可能になります。

`partial` をどの consumer まで quarantine とするかは裁定パッケージが必要です。

### 5. direct `_run_workload` が critic を省略できる入口になる

D114 は `_run_workload()` を独立した第 3 入口として扱っています（[decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/docs/decisions.md:5335)）。現行関数は critic を実行してから戻ります（[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1781)）。

plan は同関数を planner/coder/auditor/harness までに狭め、pending queue を caller に返します（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:305)）。direct caller は queue を無視して終了できます。build drive 自体は campaign WAL と critic digest/admitted view を作り得ます（[p3_s4_loop_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_s4_loop_trigger_gating.py:751)）。

成果物影響: campaign WAL/provenance と admitted campaign view を作りながら、critic、barrier、trial report、試行台帳の terminal proof を持たない材料経路が成立します。

この direct 面を廃止・封印するか、opaque pending token を必ず消費する単一入口へ統合する裁定が必要です。

### 6. schema v3 の一律拒否は historical proof chain を壊す

plan は v3 journal を新たに拒否します（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:429)）。completeness は artifact 自身の version resolver ではなく、現在の producer 定数と比較します（[autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:450)）。standalone verifier も formal acceptance もこの入口を使います（[autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:1191)、[trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/trial_registry.py:1852)）。

成果物影響: 既存 v3 trial は bytes が不変でも current verifier と acceptance-receipt 発行の受理集合から外れ、過去 proof chain の再検証参照が切れます。

live v4 acceptance と historical v3 verification を別入口にするか、意図的破棄として再裁定すべきです。

### 7. plan が positive とする build partial の一部は producer が生成できない

generation 開始前 wall は campaign layout を materialize する前に戻ります（[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1538)）。planner/coder/auditor invalid も drive 前に戻ります（[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1583)）。しかし build finalizer は `reports/` の実在を要求します（[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1207)）。

したがって plan の「generation 開始前 wall」「planner invalid・barrier なし positive」が build を含むなら producer は出せません。fake finalizer を使う completeness test だけが緑になる consumer-only topology です。no-build なら成立します。

成果物影響: 実 build では `run-finish`/`report.json` が作れず、registered lifecycle は indeterminate になります。テスト上だけ受理された partial と実試行台帳が食い違います。

build/no-build を分けた real-finalizer test と、admission-finalizer 例外を supervisor catch の外へ置く境界テストが must-fix です。

## 疑い・nit

### 8. 新しい generation cap は現行構成では到達不能

`MAX_POST_ADMISSION_CRITIC_GENERATIONS=1` は、先行する `MAX_APPROVED_GENERATIONS=1` が既に `2` を拒否するため、land 時の production では発火しません。plan の monkeypatch test は「将来 approval cap だけを上げた変更」を模擬する change-time tripwire としては意味があります（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:350)、[同](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:521)）。

成果物影響: 現行成果物への実害はなく nit。ただし「現在の runtime で独立に発火する防壁」と名乗るのは誤りです。

### 9. barrier の extra-field 拒否がテストに明記されていない

plan は「exact shape」と書きますが、列挙された負例に unknown/extra field がありません（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u8-critic/s2-plan.md:489)）。実装前なので real とは断定しません。

成果物影響: exact-key 検査を落とした場合、barrier event に full decision、metrics、任意文字列を載せても acceptance receipt は hash で固定するだけとなり、試行台帳と proof chain に新しい無制限 disclosure 面ができます。

なお、同一 generation object を cell へ append してから `_partial` を clear する順序なら、現行の identity guard は二重 append を防げます。ただし提案テストは append と clear の間への fault injection を明示しておらず、この点は nit です。

## 規律 2 / 3 の直接判定

`_ROLE_ORDER` prefix、journal/report role 全単射、critic 後の status 再算出について、plan どおり per-cell exact checker を実装する限り、直接の緩和経路は見つかりませんでした。現行 prefix は厳密な集合一致です（[autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:631)）。role 全単射も barrier を非-role event として分離する設計自体は正しいです（[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:985)）。

ただし #3〜#5 により、completeness の外側、formal receipt、direct entry、material consumer では保証が抜けています。

## 親 brief の 3 前提

| 前提 | 判定 | 反例・過一般化 |
|---|---|---|
| (i) generations=1 なので critic 出力は制御流へ還らない | **狭義のみ正しい** | `reverse_recommended` の次世代還流はありません。しかし malformed 出力は `role-invalid` を作り（[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1796)）、trial status と lifecycle terminal を変えます。複数 workload では critic の所要時間も次 workload の wall gate に影響します。 |
| (ii) 3 anchor のうち 8c に実在するのは Layer 3 admission だけ | **言い方が過大** | origin ledger seal/proof が無い点は D201 と整合します。しかし campaign WAL hash、lock hash、overlay ledger hashを持つ artifact admission は既に critic 前にあります（[autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:55)）。「残りが無いから Layer 3 report だけで U-8 を満たす」という帰結は成立しません。 |
| (iii) certified 選択・材料レポート・試行台帳の現在値は不変 | **既存 bytes だけなら自明、一般化は誤り** | certified consumer は現状未配線なので現在値は不変です（[layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/layer3_report.py:517)）。一方、新 run の全 role payload/hash、journal、lifecycle/receipt、場合によって LLM 出力と材料レポートは #2 のとおり変わります。v3 の再検証受理集合も #6 のとおり変わります。 |

## 総括

- **(a) NO-GO:** Layer 3 report より後へ呼び出しを移す順序テストにはなるが、U-8 の seal/proof を欠いたまま commit-reveal を名乗り、formal receipt・direct entry・historical verifier が取り残されています。
- **(b) must-fix:** #1、#2、#3、#4、#5、#6、#7。
- **(c) 最も見落とされやすい 1 点:** `SCHEMA_VERSION` が journal 専用でなく全 role の stdin payload と共用されており、barrier 追加が planner/coder/auditor/critic 全 recipient と将来の材料値を変えること。
- **(d) 親 brief の誤り:** 「critic 出力が制御流へ還らない」は reverse feedback に限るべきであり、「Layer 3 だけ実在するから U-8 をそれだけで満たせる」「成果物値は一般に不変」も過一般化です。