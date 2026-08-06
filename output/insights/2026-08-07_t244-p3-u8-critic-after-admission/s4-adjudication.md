# [T-244] P3 critic 後置 (U-8) — 段 4 裁定とプラン v2

両レンズが独立に **NO-GO** を返し、**同じ最安案**へ収束した。親はこれを採り、プランを v2 へ差し替える。
親自身も追加実測を行い、レンズが提案した「新 cap」「barrier event」「schema bump」がいずれも不要である
ことを確認した。

## 1. 所見の裁定表

| # | 所見 | 判定 | 採否 | 成果物影響 (放置した場合) |
|---|---|---|---|---|
| A1 | 本 wave では U-8 は閉じない (ledger seal・proof 書き込み・proposal/raw の seal 後公開が不在) | **real** | **採用 (名乗りの限定)** | 記録が「commit-reveal を閉じた」と読める → 材料レポートと台帳が実態より強い保証を参照する |
| A2 / B R-02,R-05 | `SCHEMA_VERSION` は全 role の payload と共用で、bump すると全 role の入力 bytes と `input_payload_sha256` が変わり、既存 v3 artifact が verifier・台帳の受理集合から外れる | **real** | **採用 (bump しない)** | 全 role payload hash と journal hash が変わり、既存 v3 trial の再検証参照が切れる |
| B R-01 | 新 journal event `critic-admission-barrier` は U-8 の射程外の新設統治 | **real** | **採用 (実装しない)** | barrier のない build trial が新たに拒否され、journal/report bytes が変わる |
| A3 / B R-04 | barrier の decision hash 照合は同一 producer 由来の自己参照で、durable な順序を証明しない | **real** | **採用 (barrier 廃止の根拠)** | 自己整合した偽 barrier が受理集合へ入り、proof chain が実在しない順序を参照する |
| B R-03 | 新定数 `MAX_POST_ADMISSION_CRITIC_GENERATIONS` は D114 の「上限は 1 定数」と衝突し、cap-lift 後に承認外の過剰拒否になる | **real** | **採用 (実装しない)** | cap を正当に上げても 2〜10 世代が拒否される潜在的過剰拒否 |
| A5 | critic を `_finish_trial` へ持ち上げると direct `_run_workload` が critic 抜きで campaign WAL と admitted view を作れる入口になる | **real** | **採用 (設計変更で回避)** | critic・terminal proof を持たない材料経路が成立する |
| B R-06b | `_pending_critics` 必須引数化は直接 call 4 箇所以上を `TypeError` で壊し、run-scope gate へ届かない | **real** | **採用 (引数を増やさない設計で回避)** | direct 入口の受理契約が `TrialRegistryError` から `TypeError` へ変わる |
| B S-01 | per-cell finalize を `_finish_trial` の try 内へ置くと、finalizer 失敗が `supervisor-error` partial へ化ける | **real** | **採用 (must-fix)** | 「report 非公開」だった finalizer 失敗が「positive decision を持つ partial report」へ変わる |
| B R-06a | 現行 1800-1802 の harness terminal break を critic block と一緒に消すと、複数世代経路が無条件に第 1 世代終了になる | **real** | **採用 (優先順位を保存)** | cap-lift 経路の第 2 世代以降の role attempt・WAL・report cell が消える |
| A7 / B R-06d | 既存 build test は finalizer を fake にし campaign chain を無効化しているため、実 Layer 3 の durable write は発火していない | **real** | **採用 (名乗りの限定 + 可能な範囲で実 finalizer)** | 誤順序の実装でも fake decision で既存検査を通過しうる |
| B R-07 | 変異 M1〜M6 は帰属不成立・kill node 不在 | **real** | **採用 (再登録)** | 別 gate に殺された mutant を「順序 test が殺した」と誤記録し、変異台帳の kill 理由が偽になる |
| A4 | `partial` trial と positive Layer 3 material の quarantine 境界が無い | **real** | **scope 外 (既存条件)** | 本 wave 前から全 cell が stop_reason に関わらず finalize される。本 wave が作る状態ではない |
| A6 | v3 の一律拒否が historical proof chain を壊す | real だが **moot** | bump しないため消滅 | — |
| A8 / A9 | 新 cap は到達不能 / barrier の extra-field 拒否が未明記 | nit | **moot** | — |
| B N-01 | `C:949 直後` の位置指定ずれ | nit | moot (barrier 廃止) | — |
| B 既存所見 | transport 付き generation-boundary wall の terminal projection 不整合 / `layer3_report.render` の parent dir fsync 欠落 | **real だが scope 外** | **見送り (防御的堅牢化)** | 既存不整合。U-8 と独立。D205 の基準で研究前進に直接効かない |

## 2. 親 brief の前提訂正 (両レンズ + 親の追加実測)

1. **「実装上限 10 の経路」は通常到達不能。** `main` / `run_trial` / `_run_workload` の 3 入口すべてが
   `MAX_APPROVED_GENERATIONS = 1` を通る。2 世代へ到達しているのは monkeypatch した test だけである。
   brief の (P4) はこの点で誤り。
2. **「critic 出力が制御流へ還らない」は `reverse_recommended` に限る。** critic の parse 失敗は
   `None` を返し、`stop_reason = "role-invalid"` を通じて cell stop・trial status・lifecycle terminal を
   変える。brief の (i) は一般化しすぎ。
3. **「Layer 3 admission だけ実在するから、それだけで U-8 を満たせる」は誤り。** 実在するのは事実だが、
   critic は依然 ledger seal / proof issuance より前に metrics を受け取る。本 wave を「U-8 完了」と
   記録してはならない。
4. **親の追加実測 (レンズの主張の裏取り):**
   - `_check_attempt_sequence` (`autonomous_trial_completeness.py:857-865`) は journal の
     `(workload, generation, role)` 順と report 平坦化順の**完全一致**を要求する。
     **generations=1 では後置しても順序は不変**なので、完了性検査は変えなくてよい。
   - 完了した多世代 `run_trial` を completeness まで通す既存テストは**存在しない**
     (`test_p3:1365` は第 1 世代で planner-invalid 停止、`test_p3:1634` は `_run_workload` 直呼びで
     report を作らない、`test_completeness:894` は手組み fixture で producer 出力ではない)。
     よって後置は既存テストの順序軸を壊さない。
   - cap を上げて多世代 full trial を回した場合、後置設計では journal 順が report 順と食い違い、
     `assert_autonomous_trial_completeness` (`p3_autonomous_workload_trial.py:1422`) が
     `_write_json_atomic` (`:1442`) の**前**に例外を出す。すなわち**新定数を足さなくても既に
     fail-closed** である。B R-03 の懸念は新 cap 無しで満たされる。
   - `_finalize_build_cell_admission` は全 cell に対し `stop_reason` に関わらず無条件に回る
     (`:1363-1369`)。「admitted material + 非正常 cell」は本 wave が作る状態ではない (A4 の根拠)。

## 3. プラン v2 (確定)

**方針: critic を `_run_workload` の外へ出さない。同関数の generation ループの後で cell の
Layer 3 admission を確定し、その後で pending critic をまとめて呼ぶ。**

これにより A5 (direct 入口の critic 省略)、B R-06b (必須引数追加による破壊)、
`status` 算出順序の問題 (A の指摘) がまとめて消える。`_run_workload` は関数冒頭で
`active_scope.admission` を既に取得しているため、**新しい引数を 1 つも増やさない**。

1. **`_run_workload` の generation ループ**を planner / coder / auditor / harness までに狭める。
   - harness 結果確定 (`:1739-1741`) の直後に generation を cell へ append し、`_partial["generation"]`
     を `None` にする。
   - critic 用の最小情報 (generation 番号、`common` payload の copy、outcome の copy、
     metric projection、raw variant、reflux flag) を関数ローカルの pending list へ積む。
   - harness stop が `continue` 以外ならループを抜け、その理由を cell の暫定 `stop_reason` に保存する
     (B R-06a: break を消さない)。
2. **ループ後に cell の admission を確定する。**
   `do_build` なら `_finalize_build_cell_admission(result, launch_admission=active_admission)`、
   そうでなければ `result["admission_decision"] = {"admission_status": "not-applicable"}`。
   **finalizer 由来の例外は `supervisor-error` へ化けさせない** (B S-01)。
   `_finish_trial` の except が握り潰さないよう、専用の再送出経路を通す。
3. **admission 確定後に pending critic を順に呼ぶ。** critic digest 生成と
   `require_admitted_campaign` もここで行う。critic が `None` を返したら
   `stop_reason = "role-invalid"` とし、**harness 由来の stop より優先**する (現行の優先順位を保存)。
   admission decision は巻き戻さない。
4. **`_finish_trial` の一括 finalize ループ (`:1363-1369`) は fallback に残す。**
   `admission_decision` を既に持つ cell は再 finalize しない
   (`_finalize_build_cell_admission` は `layer3_report.json` の既存を拒否するため二重実行は必ず落ちる)。
   `supervisor-error` で復元された cell だけがここを通る。
5. **`status` 算出 (`:1352-1362`) はそのまま。** critic は `_run_workload` 内で完了するため、
   cell の `stop_reason` は `_finish_trial` へ戻る時点で確定している。
6. **変えないもの:** `SCHEMA_VERSION` (v3 のまま)、`REPORT_SCHEMA_VERSION` (v2 のまま)、
   journal event 集合、`_ROLE_ORDER`、`_check_attempt_sequence`、`MAX_APPROVED_GENERATIONS`、
   新定数なし、新 journal event なし、critic payload の key 集合。

### 受理集合の変更 (D96 の対象)

- **変更前:** cap を上げて多世代 full trial を回すと、journal 順と report 順が一致し report が publish される。
- **変更後:** 同じ条件で journal 順が report 順と食い違い、`assert_autonomous_trial_completeness` が
  publish 前に fail-closed で止める。**1 世代の運転 (承認済み唯一の運転) の受理集合は不変。**
- これは U-8 を実装した結果の不可避な帰結であり、D96 に従い新しい D と境界テストを同一変更単位に含める。

## 4. テスト (新設・更新)

1. `test_build_cell_admission_precedes_critic_invocation` — 共有 `order` list に
   finalizer と critic provider が append し、`order == ["admission", "critic"]` を検査する。
   可能な限り**実 `_finalize_build_cell_admission` を spy で包む**。実 Layer 3 render を
   fixture で発火できない場合は、その限界を test の docstring と worklog に明記し、緑と偽らない (A7/B R-06d)。
2. `test_post_admission_invalid_critic_marks_cell_role_invalid` — critic 応答だけ malformed。
   `stop_reason == "role-invalid"`、`report["status"] == "partial"`、`admission_decision` が残ることを検査。
3. `test_invalid_critic_overrides_harness_terminal_stop` — harness stop を `continue` 以外にしても
   critic invalid が優先することを検査 (優先順位の保存)。
4. `test_cell_admission_failure_is_not_converted_to_supervisor_error` — finalizer を失敗させ、
   `supervisor-error` partial ではなく例外で止まり report が publish されないことを検査 (B S-01)。
5. `test_multi_generation_deferred_critic_fails_closed` — `MAX_APPROVED_GENERATIONS` を 2 へ
   monkeypatch した full `run_trial` が、report publish 前に completeness で fail-closed になることを検査。
   **これが受理集合縮小の境界テスト (D96)。**
6. **正例 (承認外の過剰拒否の検出、DW-M01):**
   既存の 1 世代 build/no-build positive path が従来どおり受理され report を publish することを、
   既存テストで確認する (新規追加不要。既存が緑であることを以て正例とする)。
7. 既存テストの追随: `_run_workload` の直呼びテスト群 (`test_p3:1466, 1486, 1634, 3427, 3453`) と
   `test_claude_transport.py:2086` を、**引数を増やさない**設計により無変更で通す。
   critic call-count を pin している箇所 (`test_p3:1763, 1828`) は挙動が保存されるため無変更で通るはず。
   通らない場合は実装側の誤りとして扱い、期待値を変更しない。

## 5. 変異事前登録 (DW-M01)

| # | 位置 | 変異 | 期待 kill node | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | `_run_workload` の cell admission 確定と pending critic 呼び出し | 2 つの呼び出し順を交換 | `test_build_cell_admission_precedes_critic_invocation` (新設) | 1 世代では journal/report 順が変わらず completeness は通る。order spy だけが検出する |
| M2 | pending critic 処理内の `critic is None` 分岐 | `stop_reason = "role-invalid"` 代入を削除 | `test_post_admission_invalid_critic_marks_cell_role_invalid` (新設) | fixed-budget cell の valid-role gate へ届く前に、cell の stop/status assert が先に落ちる direct 経路で検査する |
| M3 | critic invalid と harness stop の優先順位 | harness stop を後勝ちにする | `test_invalid_critic_overrides_harness_terminal_stop` (新設) | 優先順位だけを変える 1 行。他層は同じ入力を拒否しない |
| M4 | finalizer 例外の再送出 guard | guard を外し `supervisor-error` へ落とす | `test_cell_admission_failure_is_not_converted_to_supervisor_error` (新設) | 例外種別の変換だけを変える。completeness は partial report を受理してしまうため、この test だけが検出する |
| M5 | cell admission 確定の呼び出し | 呼び出しを削除 (decision 未設定のまま critic へ) | `test_build_cell_admission_precedes_critic_invocation` (新設) + `_finish_trial` fallback が拾うため build positive も赤 | 削除は 2 node を落とす。単一理由でないので **diagnostic sensitivity pin として別枠に記録**する (DW-M08) |

落とした候補と理由:
- barrier 系 (旧 M2/M3/M4): barrier を実装しないため消滅。
- 旧 M6 (`_ROLE_ORDER` prefix の subset 化): 本 wave の変更行ではなく、既存テストが既に殺す。
- generation 上限行: D114 gate が先に拒否し、monkeypatch 無しでは後段が mask される (B R-07 の指摘どおり)。

## 6. scope 外 real 所見 → 裁定パッケージ (ユーザーへ返す)

1. **U-8 の残余。** 本 wave 後も ledger seal・proof 書き込み・proposal / raw response の seal 後公開は
   未実装。「U-8 完了」「commit-reveal を閉じた」と名乗ってはならない。名乗ってよいのは
   **「8c 非認定 pilot の critic 呼び出しを cell の Layer 3 admission 確定後へ後置した」**まで。
   残余をどの順で起票するかは裁定が要る。
2. **cap-lift との相互作用。** `MAX_APPROVED_GENERATIONS` を 2 以上へ上げる将来の裁定は、
   後置設計により多世代 journal 順が completeness と食い違い fail-closed になる事実を前提にしなければ
   ならない。cap-lift 時に「critic reflux をどう成立させるか」を同時に裁定する必要がある。
3. **`partial` trial と positive Layer 3 material の quarantine 境界** (A4、既存条件)。
   formal receipt が `partial` を正規 terminal として受けるため、材料と受理の境界に裁定が要る。

見送り (D205 の基準、防御的堅牢化): transport 付き generation-boundary wall の terminal projection
不整合、`layer3_report.render` の parent directory fsync 欠落。いずれも既存・U-8 と独立。

## 7. 規模と分割

変更面は `p3_autonomous_workload_trial.py` の 1 ファイルと、そのテスト 1 ファイルに収まる。
完了性検査は**変更しない**。段 5 は Codex `role=author` 1 単位。段 6 の敵対レビューは 2 レンズ並列。
