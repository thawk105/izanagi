結論は **NO-GO** です。pytest・変異・CLI はすべて未実走であり、以下は静的読解だけに基づく判定です。ファイル変更は行っていません。

最大の問題は、親 P6 が「既存 8c CLI」と「fixture ledger」を足し合わせて発火 path と数えている一方、その二つを結ぶ経路が存在しないことです。

- CLI は origin binding/client を受け取らず、plan 自身も「通常 CLI から origin binding は発火しない」と認めています。[plan.md:203](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-8c-wiring/s2/plan.md:203)
- `origin_binding is None` なら ledger は一切呼ばれません。[plan.md:181](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-8c-wiring/s2/plan.md:181)
- `claude-headless` は binding/client 注入を両方拒否する計画なので、実 provider 側にも正の入口がありません。[plan.md:212](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-8c-wiring/s2/plan.md:212)
- fixture ledger は完全な一時 Git repo を要求する private seam だけです。[reflux_origin_ledger.py:2969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/orchestrator/campaign/reflux_origin_ledger.py:2969)
- N8 の既存 receipt は 8c caller を通らず、probe が event を直接構築しています。[liveness_probe.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:89) しかも `fixture_only=true`、`p3_evidence=false`、`production_evidence=false` です。[receipt:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/output/insights/2026-08-05_t244-p3-liveness/receipt:35)
- plan 自身も最終的に P6 を「不成立」と評価しています。[plan.md:307](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-8c-wiring/s2/plan.md:307)

したがって、これは「条件付き production 機能」ではなく、実装後に新しく作る direct-call fixture test だけで発火する test-only branch です。`DW-G04` の「既存 artifact path」を満たしません。[core.md:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/docs/dev-wave/core.md:57)

## (a) 11 層の会計

11 層の定義は `output/insights/2026-08-05_t244-p3-design/s3-lensB.md:13-25` に従います。

| 層 | 本 plan 後 | 判定 |
|---:|---|---|
| 1. authority 値・発行 | production authority は空のまま | **空** |
| 2. public authority reader / live-cell binding | caller 提供の `origin_id` を読むだけで、workload/descriptor と authority cell の一致を検証できない | **空** |
| 3. runtime bootstrap/storage/migration | production 初期化は禁止のまま。fixture runtime のみ | **空** |
| 4. producer translator / batch journal | R=1・no-build・tombstone 用 event translator のコード面だけ | **部分** |
| 5. production caller | binding を供給する CLI/registry/headless 経路がない | **空** |
| 6. durable origin-proof issuance | sidecar を scope 外化 | **空** |
| 7. report schema/current consumer | origin field と schema 変更を明示的に禁止 | **空** |
| 8. trial registry origin binding | `TrialBinding` に origin field がない | **空** |
| 9. P7 formal consumer | scope 外 | **空** |
| 10. Layer 3/WAL/formal material report | scope 外 | **空** |
| 11. positive runbook/audit/crash recovery | direct fixture tests案だけ。committed/prepared 後の recovery なし | **空** |

`TrialBinding` の現行 field に origin はありません。[trial_registry.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/orchestrator/campaign/trial_registry.py:124) また report は origin 参照を持たず、plan も bytes 不変を要求しています。[p3_autonomous_workload_trial.py:1370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1370) [plan.md:241](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-8c-wiring/s2/plan.md:241)

よって、コード面では第4層が部分的に増えるだけです。研究成果・proof chain として閉じる増分は **0/11** です。brief の「origin ledger の caller 制御流を入れる」は、第5層まで埋まるように読めますが、実際には空です。[brief.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/output/insights/2026-08-06_t244-p3-8c-wiring/brief.md:7)

## (b) scope 外へ落ちている必要層

次を裁定パッケージ候補として返すべきです。

1. **activation bundle（層1〜3・5・8）**  
   U-10 の authority/budget、production provisioning、公開 authority reader、trial registry の origin binding、headless/CLI が安全に binding を取得する経路を同じ裁定面に置く必要があります。U-10 だけ決まっても、現 plan の headless 拒否と CLI 無引数により発火しません。`brief.md:16-18`、`plan.md:214-220`。

2. **実 execution result contract（層4）**  
   `accepted/rejected` の正式な `evidence_digest` と `constraint_sha256` の producer を決める必要があります。plan 自身が現 `drive()` 戻り値では埋められないと認めています。`plan.md:100-109`。

3. **proof/reference consumer bundle（層6・7・9・10）**  
   sidecar、report v3、completeness、P7、Layer 3/WAL/material report を閉じない限り、ledger batch と trial/report の間に辿れる辺がありません。設計パッケージもこれらを残余としています。`output/insights/2026-08-05_t244-p3-design/README.md:256-273`。

4. **namespace/crash recovery（層11）**  
   reserve/commit の receipt 後に process が落ちた場合の再開、committed/prepared batch の reconciliation、operation ID 再送を裁定する必要があります。plan は seal failure を伝播するだけで、open origin を回復しません。`plan.md:164-179`。

これらを scope 外にしたまま第4層だけ land するのは、「実装したふり」を避けるという本 wave の目的と両立しません。

## (c) 名乗りの上限

brief の上限はまだ広すぎます。特に「oracle query」は撤回が必要です。

本 plan は `do_build=False` だけを許しますが、実 `drive()` はこの場合 workload を実行せず `outcome="dry-pass"` を返します。[p3_s4_loop_trigger_gating.py:553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:553) ledger 自身も `queries_used` は reserved member row で、物理 query の証明ではないと明記しています。[reflux_origin_ledger.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/orchestrator/campaign/reflux_origin_ledger.py:2)

実測後に許せる最大表現は次です。

> 一時 Git fixture の placeholder authority（Bmin=1）に対し、programmatic に注入した 8c no-build branch が、R=1 の reserve → candidate commit → dry-run drive → tombstone prepare/seal を通した。

名乗れないものは、production caller integration、oracle query、実 result binding、production budget binding、trial artifact integration、proof chain です。

## 提案テストの正例・負例評価

以下はすべて未実走です。「成立」は静的に到達可能という意味で、緑の主張ではありません。

| テスト | 正例 | 負例・変異 | 判定 |
|---|---|---|---|
| `test_originless_path_preserves_pre_wiring_artifact_bytes` (`plan.md:260`) | 起点 `3143302b` の literal golden、固定時刻、決定的 fake drive なら成立可能 | artifact field 追加は SHA map 差になる | **条件付き成立**。golden を実装後に再生成できないよう起点 hash を固定すべき |
| `test_originless_path_never_touches_injected_ledger_client` (`:261`) | binding 無し＋例外 client で完走 | guard 恒真化で例外 | **成立見込み**。ただし機能全削除でも通るのはこのテストの責務上正常 |
| `test_fixture_origin_binding_real_ledger_seals_one_tombstoned_member` (`:262`) | 未確立 | event 削除は reducer が拒否 | **不成立のまま**。参照 fixture の既定 `batch_member_row_count_min=2` に対し plan は R=1。[test_reflux_origin_ledger.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/orchestrator/tests/test_reflux_origin_ledger.py:60) Bmin=1 authority の明記が必要 |
| `test_origin_events_surround...` (`:263`) | recording client/provider なら順序観測可能 | reserve/commit の移動で順序差 | **成立見込み**。ledger の受理や public forwarding は証明しない |
| planner abandon (`:264`) | real Bmin=1 store と planner-invalid が必要 | shared abandon 削除で reserved のまま | **条件付き成立** |
| coder abandon (`:265`) | 同上 | shared abandon 削除は検出可能 | **条件付き成立**。ただし「break を return に変更」は `finally` が実行されるため負例にならない。`plan.md:166,265` |
| auditor abandon (`:266`) | preview pass にして auditor を実際に呼ぶ必要 | commit を auditor 前へ動かせば state が変わる | **条件付き成立** |
| wall-budget no reserve (`:267`) | `_run_workload` 直呼びで内部 wall gate を踏めば成立 | reserve を内部 gate 前へ移動 | **条件付き成立**。public `run_trial` では外側 wall gate が先に落とし、変異を mask しうる。`p3_autonomous_workload_trial.py:1283-1294` |
| precommit exception (`:268`) | direct `_run_workload`、元例外 identity、forfeit counter の三点が必要 | abandon 欠落・swallow | **条件付き成立**。public `run_trial` は例外を partial report に変換する。`p3_autonomous_workload_trial.py:1316-1350` |
| postcommit exception (`:269`) | sealed batch を読み、tombstone・forfeit=0・元例外を照合 | committed abandon、accepted 捏造 | **条件付き成立** |
| harness stop sealed (`:270`) | fake drive が非`continue`を返し、sealed batch を読む | seal を break 後へ移す | **成立見込み** |
| build-enabled reject (`:271`) | 現行 build admissionを全部通る valid context が必要 | origin-specific guard 削除 | **現状は恒真化リスク**。既存 build/site/context gate が先に拒否すれば、新 guard を削除しても赤のまま。`p3_autonomous_workload_trial.py:1488-1515` |
| prior-sealed origin reject (`:272`) | 「例外」だけでなく ledger call 0、counter/state 不変を要求 | guard 削除 | **条件付き成立**。任意例外だけなら後段 replicate 検査も拒否するため恒真 |
| claude-headless injection reject (`:273`) | binding-only と client-only を別 node にする必要 | 各 predicate の削除 | **現状は過剰決定**。両方同時注入では片方の predicate が残っても拒否される |
| ledger failure propagation (`:274`) | exact sentinel 例外と provider 非呼出を照合 | `except: pass` | **条件付き成立**。単に「何らかの例外」では後続 `AttributeError` 等による偽 kill になる |

さらに、全正例を `_run_workload` 直接呼出しに置くと、`run_trial → _finish_trial → _run_workload` の forwarding を `None` 固定に壊しても全 ledger 正例が通ります。これは F127 と同型です。plan は forwarding を追加しますが、public positive control を一つも登録していません。`plan.md:194-210,276`、`docs/failures.md:2950-2962`。

## (d) 変異の帰属が成立しない候補

1. **`query_ordinal_start=snapshot.queries_used` → `0`**  
   `plan.md:293`。初期 origin の `queries_used` は 0 なので、提案された一件目正例では等価変異です。非ゼロの正例がありません。prior abandon 後（batch_count=0、distinct=0、queries_used>0）を専用正例にする必要があります。

2. **candidate bytes を proposal JSON に変更**  
   `plan.md:297`。proposal JSON は先に canonical five-bit wire 検査で拒否されます。[reflux_origin_ledger.py:1504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/orchestrator/campaign/reflux_origin_ledger.py:1504) したがって「coder wire と ledger candidate の一致」を検出した kill とは帰属できません。別の有効な five-bit wire へ変異し、seal 後 bytes の不一致で落とすべきです。

3. **3 salt を同じ定数にする**  
   `plan.md:299`。plan 自身が driver で相異性を検査するため、real ledger 正例は ledger 到達前に落ちます。kill 自体は有効でも、「real ledger が salt 再利用を拒否した」証拠ではなく driver-local gate の証拠として再分類が必要です。`plan.md:63-64`。

4. **coder の `break` を `return` にする負例**  
   `plan.md:265`。提案された `try/finally` では return でも abandon が走るため、この一行変更は abandon 欠落を作りません。

5. **build-enabled guard の削除**  
   `plan.md:271`。valid build admission を通す正例が無い限り、既存の前段拒否が変異を mask します。F126 型です。`docs/failures.md:2934-2948`。

6. **headless の binding/client 条件**  
   `plan.md:273,304`。両入力を一つの node に入れると片方の guard がもう片方の変異を mask します。条件ごとに独立 node が必要です。

7. **`except Exception: pass`**  
   `plan.md:305`。期待 node が exact sentinel の再送出を要求しなければ、swallow 後の別例外で赤くなる F113 型です。`docs/failures.md:2651-2667`。

8. **R=1→member_row_count=2**  
   `plan.md:291`。Bmin=1 の通る正例を先に定義しない限り baseline 自体が赤で、変異帰属以前の問題です。

加えて candidate commitment の式は `base64.b64encode(...)` の返す `bytes` を JSON 値へ直接入れています。`plan.md:75`。ledger の実装は `.decode("ascii")` しています。[reflux_origin_ledger.py:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-8c-wiring/orchestrator/campaign/reflux_origin_ledger.py:668) plan の式を文字どおり実装すると正例は commit 前に停止します。

## 親実測の再評価

- **N1/N2/N3 は静的に再確認でき、むしろ NO-GO を支持します。** authority は実際に 71 bytes・空で、公開 API は production store 固定です。`reflux_origin_authority_v2.json:1`、`reflux_origin_ledger.py:1747-1754,3454-3477`。
- **N4 の「早期 break 5 経路」は誤りです。** critic-invalid も break するため明示 break は6経路です。`parent-measured.md:60`、`p3_autonomous_workload_trial.py:1796-1802`。ただし critic は計画上 seal 後なので、これは成果物影響を書けない nit です。
- **N5 は seam の構文的先例しか証明しません。** `drive/preview` は default production function を持ちますが、origin binding は default producer を持たず、headless が唯一の注入経路を拒否します。両者を「同型」と一般化できません。`parent-measured.md:62-69`、`plan.md:214-220`。
- **N8 は現在の 8c caller の生死ではありません。** R=2・Bmin=2 の手書き probe が event を直接 commit した receipt です。`liveness_probe.py:42-45,89-140`。planned R=1/no-build caller への一般化は不成立です。
- **N10 は 8c CLI 自体の dry-pass を示すだけです。** origin binding のない CLI と private fixture ledger を結ぶ証拠ではありません。`parent-measured.md:102-106`。

## (e) must-fix

1. **P6 を撤回し、本 wave は設計メモのみとして実装を止める。** 再開条件は「binding を供給して同じ 8c caller を通る既存 artifact path または measurement ID」の提示です。  
   **DW-G05 成果物影響:** 未修正なら certified 選択は不変、材料レポートは origin 参照なし、production 試行台帳の受理集合は空のままなのに「caller wiring 済み」という偽参照だけが増えます。

2. **再起票時は public positive control を追加する。** Bmin=1 の明示 fixture authority、正しい base64 string preimage、`run_trial` から real fixture client までの forwarding、sealed candidate bytes/counters を一つの正例で固定します。  
   **DW-G05 成果物影響:** 未修正なら forwarding を `None` に壊しても direct test は通り、public trial report は complete のまま、origin ledger の `iterations_used/queries_used/batch_count` は一件も増えません。

3. **変異事前登録を再構成する。** 固定0の等価変異、proposal JSON の過剰決定、非一意な salt 帰属を除き、非ゼロ query 正例・別の有効 wire・期待 state を使います。  
   **DW-G05 成果物影響:** 未修正なら abandon 後の正当な次 batch が誤拒否されるか、proposal と異なる candidate bytes が台帳へ seal され、材料レポートが参照する候補 identity が変わります。

4. **build/headless/failure の負例を単一理由化する。** valid build positive、binding-only/client-only の別 node、exact sentinel 再送出を要求します。  
   **DW-G05 成果物影響:** 未修正なら caller 注入や捏造 result mapping により ledger の受理集合が広がっても、report は origin field 不在のまま差異を露出せず、テストだけが緑を名乗れます。

5. **名乗りを no-build tombstone に狭める。** 「oracle query」「production caller integration」「予算束縛」を削除し、物理 query ではなく reserved member row counter であると記録します。  
   **DW-G05 成果物影響:** 未修正なら `sealed_queries=0 / tombstoned_queries=1` の台帳値が「oracle query 1 回」と材料レポートへ誤参照され、証拠の意味が反転します。

nit/backlog は、N4 の break 件数訂正、変異表の「同上」「real-ledger 正例」を exact nodeid 完全集合へ直すこと、coder `return` 負例の差替えです。これら単独では certified 選択・材料レポート・試行台帳への具体的影響を一行化できないため must-fix 件数には含めません。

## 総括

- **判定: NO-GO**
- **must-fix: 5件**
- 最重要3件:
  1. `DW-G04` を満たす既存の結合済み発火 path がないため、実装せず設計メモへ戻す。
  2. private `_run_workload` 正例ではなく、public forwarding を含む実 ledger 正例を要求する。
  3. query固定0・candidate JSON・masked guard など、帰属しない変異を再登録する。
- 親 brief で撤回すべき裁定:
  - **P4** — build outcome の証拠契約がなく、実装可能なのは no-build tombstone に限られる。`drive()` を oracle query と一般化できない。
  - **P5** — `BatchCommitted` 後の abandon は FSM が拒否するため、文面どおり実装不能。
  - **P6** — fixture ledger と 8c CLI は結線されておらず、N8 は別 probe の R=2 direct event。`DW-G04` の既存発火 path ではない。