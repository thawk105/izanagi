結論から言うと、推奨は「cell 単位で pre-admission 実行と post-admission critic を分割し、build 経路だけ journal に admission barrier を残す」「critic invalid は従来どおり `role-invalid`」「複数世代は別の機械上限で fail-closed」です。

以下、静的検査のみです。ファイル変更・pytest 実行はしておらず、テスト結果を緑とは判定していません。

## 1. 現行実行順序の正確な地図

略号:

- `P` = [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1)
- `C` = [autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:1)
- `TP` = [test_p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:1)
- `TC` = [test_autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_autonomous_trial_completeness.py:1)

### `run_trial`

1. `P:1831` で開始。
2. generation は `P:1881` で検査。実際の公開経路は `MAX_APPROVED_GENERATIONS=1` に閉じる。
3. launch admission は `P:1901-1945`。
4. build site / coder authority gate は `P:1949-1956`。この時点では `run_root` 未作成。
5. `run_root`、`raw/`、`proposals/`、journal を `P:1975-1981` で作る。
6. transport opt-in 時は `transport-admission` を `P:2000-2003`、その後 `run-start` を `P:2011-2033` で追記。
7. provider 初期化後、sealed scope 内で `_finish_trial` を `P:2076-2105` から呼ぶ。
8. report が返った後、formal lifecycle の terminal status を `P:2106-2111` で `report["status"]` に合わせる。
9. provider close は `P:2119-2121`。

CLI も `P:2173`、公開 `run_trial` も `P:1881`、direct `_run_workload` も `P:1488` で同じ generation validator を通る。

### `_finish_trial`

1. `P:1228` で開始し、launch admission の再導出と sealed scope 一致を `P:1256-1275` で検査。
2. workload 開始前の wall budget は `P:1285-1294`。ここでは `fatal_error` を作り、`supervisor-wall-budget` を journal へ書き、cell を作らず終了する。
3. workload ごとに `_run_workload` を `P:1297-1315` で呼ぶ。
4. `_run_workload` 例外は `P:1316-1350` で `supervisor-error` に変換する。`_partial` の current generation がまだ cell に入っていなければ `P:1331-1338` で復元する。
5. trial `status` は、現状では admission より先に `P:1352-1362` で決まる。

   - 全 requested cell が揃う
   - `fatal_error is None`
   - 全 cell の `stop_reason` が `role-invalid` / `supervisor-error` / `supervisor-wall-budget` 以外

   の場合だけ `complete`。それ以外は `partial`。

6. 全 workload 終了後、全 cell をまとめて `P:1363-1369` で admission finalization する。

   - build: `_finalize_build_cell_admission`
   - no-build: `{"admission_status": "not-applicable"}`

7. report 構築は `P:1370-1412`。
8. `run-finish` を `P:1413-1420` で journal 最終 event として追記。
9. journal hash を `P:1421` で固定。
10. `assert_autonomous_trial_completeness` を `P:1422-1425`。
11. build 時の `assert_campaign_layer3_chain` を、その後の `P:1426-1435`。
12. journal bytes が検査中に変わらなかったことを `P:1436-1441` で再確認。
13. 最後に report を `P:1442` で公開。

したがって現行順は正確には:

```text
全 role 呼び出し
→ trial status 算出
→ 全 cell の _finalize_build_cell_admission
→ run-finish
→ attempt_journal_sha256 固定
→ assert_autonomous_trial_completeness
→ assert_campaign_layer3_chain
→ journal 再 hash
→ report.json
```

### `_run_workload` generation ループ

初期 cell は `P:1516-1525`。`stop_reason` の初期値は `fixed-generation-budget`。`prior_reverse` は cell ごとに `P:1529` で `None` 初期化される。

各 generation は次の順:

1. generation 境界 wall check: `P:1538-1550`。
2. planner payload 構築 `P:1565-1570`、呼び出し `P:1571-1581`。

   - event を roles に格納: `P:1582`
   - invalid: `outcome=planner-invalid`、generation を append、`stop_reason=role-invalid`: `P:1583-1589`

3. coder payload `P:1591-1608`、呼び出し `P:1609-1619`。

   - invalid 処理: `P:1621-1627`

4. machine preview: `P:1629-1636`。
5. auditor:

   - preview reject なら journaled skip: `P:1637-1651`
   - 通常呼び出し: `P:1653-1673`
   - invalid: `P:1674-1680`

6. proposal artifact を `P:1682-1690` で書く。この時点で `prior_critic_reverse` が記録される。
7. harness/drive 呼び出しは `P:1691-1714`。`prior_reverse` は positional argument として `P:1709` で渡る。
8. harness shape / stop reason を `P:1715-1738` で検査し、generation の harness/outcome/metrics を `P:1739-1741` で固定。
9. critic digest / candidate projection は `P:1743-1769`。
10. critic payload は `P:1770-1780`、呼び出しは `P:1781-1791`。
11. critic event を roles に入れ、generation を cell に append: `P:1792-1795`。
12. `critic is None` なら `role-invalid`: `P:1796-1798`。
13. valid critic の `reverse_recommended` を次世代用へ代入: `P:1799`。
14. harness stop が `continue` 以外なら、それを cell `stop_reason` にする: `P:1800-1802`。

この順なので、critic invalid は harness の `converged` 等より優先して `role-invalid` になる。

### 現行 journal 順

`AttemptJournal.append` は `P:515-546`、`seq` は `P:521-523` で一度だけ単調増加する。

transport なし、1 cell、正常完了なら:

```text
seq=1 run-start
seq=2 planner
seq=3 coder
seq=4 auditor
seq=5 critic
seq=6 run-finish
```

`_finalize_build_cell_admission` 自体には journal event がないため、現行 journal だけでは critic と Layer 3 admission の前後関係を観測できない。

### completeness 内部順

`C:928-991` の順は:

1. journal 再読込と hash 一致: `C:933-936`
2. closed event set / `seq=1..N`: `C:937-938`
3. transport / run envelope: `C:939-942`
4. cell `admission_decision` の build/no-build shape: `C:943-971`
5. terminal event projection: `C:972`
6. role event unique/session isolation/state machine: `C:976-984`
7. journal/report role 順一致: `C:985`
8. journal/report 全単射: `C:986-989`
9. workload coverage / complete-partial 再算出: `C:990-991`

`assert_campaign_layer3_chain` は `C:1082-1188`。producer からは completeness の後に呼ばれる。

## 2. critic 後置で壊れるもの

### journal event、`seq`、観測可能性

単純に critic の Python 呼び出しだけを後置しても、承認済み `generations=1` では role event 順は依然 `planner,coder,auditor,critic` のままになり得る。admission event が存在しないので、「本当に admission 後か」を artifact から証明できない。

推奨は build 経路に新 event `critic-admission-barrier` を置くこと。正常 build cell は:

```text
planner → coder → auditor
→ critic-admission-barrier
→ critic
```

となり、barrier 以降の event はすべて `seq` が1増える。no-build は実 Layer 3 admission がないため barrier を出さず、従来の journal role 順を維持する。

### `_ROLE_ORDER` と prefix

現在の `C:52` は:

```python
("planner", "coder", "auditor", "critic")
```

`C:631-639` が受理する role key 集合は厳密に:

```text
{}
{planner}
{planner,coder}
{planner,coder,auditor}
{planner,coder,auditor,critic}
```

であり、`planner+auditor` 等は拒否される。

1 generation なら critic 後置後も最終 report の role key 集合は変わらないため、この prefix を緩める必要はない。

一方、P2 の「複数 generation を先に全部実行し、その後 critic をまとめる」を許すと、journal は:

```text
P1,C1,A1, P2,C2,A2, admission, Crit1,Crit2
```

になり、report scan は `C:732-755` により:

```text
P1,C1,A1,Crit1, P2,C2,A2,Crit2
```

として平坦化される。`C:857-865` の journal/report order check が拒否する。

さらに generation 2 の途中で supervisor error が起きると、generation 1 も critic 未到達の `{P,C,A}` になる。現行 `C:782-843` は「最終 generation より前は全4 role」を要求するため拒否する。この理由から P4 は fail-closed が安全である。

### journal と report の突き合わせ

新 barrier は role attempt ではないので、既存の:

- role-only sequence check: `C:857-865`
- canonical multiset 全単射: `C:986-989`

には混ぜない。

代わりに独立した barrier checker を追加し、次を検査する必要がある。

- build cell の critic event が存在するなら barrier は exactly one
- no-build に barrier は存在しない
- barrier の workload は report cell と一致
- barrier の decision hash は `cells[].admission_decision` の canonical hash と一致
- 全 planner/coder/auditor の `seq` より barrier が後
- 全 critic の `seq` より barrier が前
- barrier があって critic がない状態は、post-admission の `supervisor-error` に限る

### `status=complete/partial`

現状は critic が `_run_workload` 内で終わってから `P:1352-1362` が status を計算する。

critic を後へ出す際、status 計算を critic より前に残すと、invalid critic でも `complete` になる。`C:909-925` が再計算して拒否する。

したがって post-admission critic を全 cell で処理した後にのみ、現行 status 式を評価する必要がある。

### `critic is None → role-invalid`

`_invoke` は provider/parse の通常例外を捕捉し、invalid role event と `None` を返す (`P:994-1019`)。新しい post-admission helper でも:

1. invalid critic event を generation roles に格納
2. `cell["stop_reason"]="role-invalid"`
3. admission decision は削除・巻き戻ししない
4. critic batch を停止
5. trial status を `partial`

とする。

critic event 自体が invalid role を特定するので、新 stop reason `critic-invalid-after-admission` は不要。

### harness stop reason

現行では critic invalid が harness の `converged` / `budget-walltime` 等を上書きする。後置後もこの優先順位を保つ。valid critic の場合だけ、事前に保存した harness stop reason を最終 cell stop reason とする。

### `attempt_journal_sha256`

barrier と critic は必ず `run-finish` より前、したがって `P:1421` の hash 固定より前に完了させる。

順序は変えない:

```text
barrier/critic
→ run-finish
→ hash
→ completeness
→ campaign chain
→ hash 再確認
```

既存の post-verification race 防止 `P:1436-1441` と [TC:1675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_autonomous_trial_completeness.py:1675) は維持する。

### `_partial`

現在 generation は critic 後の `P:1793` で初めて cell に append されるため、それ以前の例外は `_partial["generation"]` から `P:1331-1338` が復元する。

分割後は harness 完了時点で:

1. generation を cell へ append
2. pending critic record を private queue へ追加
3. `_partial["generation"]=None`

とする。

post-admission payload/digest 構築で例外になっても、generation はすでに cell にあり、復元コードが二重 append しない形にする。pending payload を report cell や proposal JSON に一時保存してはならない。

### supervisor-error

分岐を区別する必要がある。

- pre-admission error: critic/barrier なし。現行 `_partial` 復元を維持。
- admission finalizer error:現行同様、positive decision を作れないため report を公開せず fail-closed。`supervisor-error` partial として受理集合を広げない。
- barrier 後、critic 呼び出し前の内部 error: admission decision と barrier は残り、critic なし、`supervisor-error` partial。新 barrier checker はこの形だけを許可。
- provider/parse error: supervisor-error ではなく invalid critic → `role-invalid`。

### wall-budget

- workload 前: `P:1285-1294`。cell も critic も作らない。
- generation 開始前: `P:1538-1550`。その generation の critic は呼ばない。
- generation 実行開始後に時間超過しても、現状は次の generation/workload 境界まで検査しない。admission と critic の間に新しい wall check は足さない。足すと新しい partial topology になる。

既存の問題として、transport 付き generation-boundary wall は `P:1541-1549` で terminal event を書く一方、`fatal_error` を作らない。`C:545-579` は terminal wall event に `fatal_error` を要求するため、full `run_trial` では report 公開不能になる。既存テスト [test_claude_transport.py:2085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_claude_transport.py:2085) は `_run_workload` 単体しか見ていない。これは実在する既存不整合だが、U-8 へ混ぜず別修正に分離すべきである。

### post-admission での digest 再構築

critic block を後へ移すと `require_admitted_campaign` も Layer 3 report 書き込み後に再実行される。

これは静的には安全である。`layer3_report.render` は [layer3_report.py:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/layer3_report.py:570) で report を書くが、`require_admitted_campaign` の admission decision は [artifact_admission.py:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/artifact_admission.py:521) 以降の campaign lock / WAL / provenance から作られ、Layer 3 report 自体を decision preimage に含めない。したがって decision drift や自己参照は生じない。

## 3. 具体的変更案

### P2: cell 単位を推奨

`P:282-303` 付近に private dataclass `_PendingCriticAttempt` を追加する。保持するのは次だけに限定する。

- generation number
- `_common_payload` の immutable copy
- harness outcome の copy
- metric projection
- raw variant (`str | None`)
- reflux flag

critic payloadそのものや admission decision は pre-admission で作らない。

`_run_workload` (`P:1446`) に新しい必須引数 `_pending_critics: list[_PendingCriticAttempt]` を追加し、役割を「planner/coder/auditor/harness まで」に狭める。

- `P:1739-1741` の直後で generation を cell へ append
- `P:1743-1801` の critic block を削除
- pending record を queue へ追加
- harness terminal reason を一旦 cell へ保存
- `prior_reverse` は承認済み1世代では常に `None`

`P:1197-1225` の近傍に次を新設する。

- `_finalize_cell_admission(cell, *, do_build, launch_admission)`
- `_append_critic_admission_barrier(...)`
- `_build_post_admission_critic_payload(...)`
- `_run_post_admission_critics(...)`

`_finish_trial` の `P:1297-1315` 直後を、cell ごとに:

```text
_run_workload(..., _pending_critics=queue)
→ _finalize_cell_admission
→ build かつ queue 非空なら critic-admission-barrier
→ _run_post_admission_critics
→ cells.append(cell)
```

へ変える。

現在の一括 finalization `P:1363-1369` は、pre-admission supervisor-error から復元された「まだ decision がない cell」の fallback にだけ残す。正常 cell をここで再 finalization してはならない。

代案は launch admission と finalizer callback を `_run_workload` へ渡し、同関数内部で admission と critic まで完結させる形。ただし direct `_run_workload` の責務が Layer 3/report orchestration まで膨らみ、`_partial` recovery も複雑になるため非推奨。

trial 全 cell を先に実行してから critic をまとめる案は、journal/report role 順を壊すので却下する。

### P3: `role-invalid` を維持

推奨:

- post-admission `_invoke(role="critic")` が `None` を返したら `role-invalid`
- admission decision は positive のまま
- generation `outcome` は harness outcome のまま
- invalid critic role event が失敗箇所を表す
- status 計算はその後なので `partial`

代案は `critic-invalid-after-admission` を新 stop reason にする形。ただし `C:764-769` の closed stop set、`C:781-811` の state machine、status consumer、report 意味をすべて増やす割に、critic event の `role/status` と情報が重複するため非推奨。

### P4: fail-closed を推奨

既存 `MAX_APPROVED_GENERATIONS=1` だけに依存すると、将来その定数を2へ上げただけで critic reflux が黙って切れる。

`P:145-146` に別の意味上限:

```python
MAX_POST_ADMISSION_CRITIC_GENERATIONS = 1
```

を追加し、共有 validator `P:306-315` で approval 上限とは別理由として検査する。通常の2世代入力は先に D114 approval gate で止まり、境界テストでは `MAX_APPROVED_GENERATIONS` だけを2へ monkeypatch しても新上限が止めることを確認する。

同じ上限を standalone consumer の:

- `C:502-506`
- `C:1097-1098`

にも追随させる。

これにより `MAX_GENERATIONS=10` は絶対 parser 範囲として残るが、post-admission critic feedback capability は1に閉じる。

還流断を明示記録する代案には、少なくとも次が必要になる。

- `prior_critic_reverse_consumed`
- `critic_feedback_delivery = not-consumed-after-cell-admission`
- generation-major ではなく二相 role 順を completeness に実装
- critic k が invalid になった後、すでに実行済みの generation k+1…をどう扱うかの新裁定
- report schema の版上げ
- proposal artifact と report の突き合わせ

planner は前世代 metrics / whiteboard を引き続き見るため、「全還流断」ではなく「critic reverse だけ断」であることも記録しなければならない。scope と report v3 不導入の制約に収まらないため、本 wave では採らない。

### schema と D96

新 journal event を入れるため:

- `P:143` の trial/role schema を `v3 → v4`
- `P:144` の report schema は `v2` のまま

とする。critic payloadへ full `admission_decision` は追加しない。WAL hash 等の新たな recipient disclosureを増やさず、journal barrierで順序だけを証明する。

D96 [docs/decisions.md:4269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/docs/decisions.md:4269) に従い、新しい D の spool fragmentには以下を記録する。

- cell 単位二相順序
- barrier event の意味
- critic invalid の非遡及性
- post-admission critic 上限1
- report v2維持
- trial-wide batch、full decision payload、還流断記録案を却下した理由

## 4. completeness の受理集合変更

### 変更前

受理する:

- schema v3
- journal event が `C:40-48` の既存7種だけ
- generation roles が `_ROLE_ORDER` prefix
- build cell に positive-looking `admission_decision`
- journal/report role attempts が同順かつ全単射
- critic と admission の時間順を示す event がなくてもよい

拒否する:

- admission barrier のような未知 event
- nonprefix roles
- `generations>1`
- invalid critic を持つ `fixed-generation-budget` cell

### 変更後

新たに受理する:

- schema v4
- exact shape の `critic-admission-barrier`
- build admission 後、critic 前という seq 関係
- barrier 後の supervisor error による「barrierあり・criticなし」partial

新たに拒否する:

- schema v3
- build critic event があるのに barrier がない
- barrier が critic より後
- barrier が planner/coder/auditor より前
- duplicate/foreign workload barrier
- barrier decision hash と report decision の不一致
- no-build の barrier
- supervisor-error 以外の barrier-only cell
- `MAX_APPROVED_GENERATIONS` だけを上げて作った複数世代 report

引き続き受理する:

- planner/coder/auditor invalid による prefix partial
- no-build `admission_status=not-applicable`
- pre-admission supervisor-error
- generation 開始前 wall cell
- valid critic を含む fixed/driver-terminal cell

引き続き拒否する:

- `planner+auditor` 等の nonprefix
- role/report 全単射不一致
- seq gap
- hash不一致
- critic invalidなのに cell stop/statusが成功扱い

`test_state_machine_rejects_nonprefix_roles` (`TC:1201-1213`) は期待値を反転しない。`("planner","auditor")` を引き続き拒否し、さらに `("critic",)`、`("planner","critic")` も同じ gate で拒否するパラメータ化へ拡張する。

## 5. 新設・更新すべきテスト

### producer 順序の pin

`TP:1893-1961` の既存 build public-entry test の近傍に `test_build_critic_invocation_occurs_after_cell_admission` を追加する。

- fake `_finalize_build_cell_admission` が `order.append("admission")` して positive decision を設定
- custom critic provider が `order.append("critic")`
- `run_trial(do_build=True)` を通す
- `order == ["admission", "critic"]`
- journal で `auditor.seq < barrier.seq < critic.seq`
- barrier decision hash が report cell decision の canonical hashと一致
- critic invalid版でも admissionが先

内部 callback順と durable journal順の両方を検査する。critic payloadへ admission decisionを追加する必要はない。

### critic invalid

新規 `test_post_admission_invalid_critic_keeps_admission_and_makes_partial`:

- planner/coder/auditor は valid
- finalizer は admitted
- critic responseだけ malformed
- `critic.status == invalid`
- `cell.stop_reason == role-invalid`
- `report.status == partial`
- `admission_decision` が残る
- barrier が invalid critic より前
- harness stop を `converged` にしても `role-invalid` が優先

### completeness barrier 境界

`TC:499` 以降の positive set と `TC:1191` 付近の state-machine negativesに追加する。

- exact barrier positive
- missing barrier reject
- critic-before-barrier reject
- barrier-before-auditor reject
- duplicate barrier reject
- decision hash mismatch reject
- no-build barrier reject
- post-barrier supervisor-error / criticなし positive
- role-invalid planner / barrierなし positive

各負例は event の `seq` と journal hash を再計算し、狙った gate 以外を壊さない。

### `_partial` / supervisor

既存 `TP:2038-2069` と `TC:1035-1111` を拡張する。

- pre-admission preview error: `{planner,coder}` generation が一度だけ復元され、critic/barrierなし
- post-admission critic payload構築 error: generation はすでに cell にあり、二重 appendされない
- admission decision/barrierを残した `supervisor-error` partialが受理される
- journal terminal event は引き続き `run-finish` の直前

### wall-budget

- workload前 wall:既存 `TC:592-606` を維持
- generation開始前 wall: critic providerが未呼び出し、barrierなし
- no-transport full producer pathが partial reportを作ることを追加
- transport付き inner-wall の既存不整合は、別 issueへ切り出す。U-8実装内で期待値を成功へ反転しない

### P4 fail-closed

- `TP:404-407` の境界に、`MAX_APPROVED_GENERATIONS=2` だけを monkeypatchしても新 capability上限が2を拒否するテストを追加
- `TP:1633-1682` の2世代 positive testは、1世代 build positiveへ変更
- `TC:891-939` の旧2世代 state-machine testは、post-admission critic上限による早期拒否テストへ置換
- `TC:859-873` は approval上限とcritic capability上限を別々に pin

### 既存テスト追随

- `TP:706-708`、`TC:40`、`TC:742-760`: schema v4へ更新
- `TP:633-755`: build/no-build別の event順、hash、role countを確認
- `TP:865-948`: critic payload key集合は据え置き、schema値だけv4
- `TP:1138-1303`: critic relation oracleの declassification selectorは増やさない
- direct `_run_workload` の新 queue引数により、`TP:74-76` と [test_claude_transport.py:2086](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_claude_transport.py:2086) を追随
- report schema v2、report top-level key集合 `TP:3110-3116` は変更しない

## 6. 変異事前登録候補

| # | 現行 anchor / 予定位置 | 1行変異 | 期待 kill node |
|---|---|---|---|
| M1 | `P:1297` 直後の新 cell phase | `_run_post_admission_critics` と `_finalize_cell_admission` の呼出し順を交換 | `test_build_critic_invocation_occurs_after_cell_admission` |
| M2 | 現行 `P:1365` 相当の post-finalize位置 | barrier append 1行を削除 | `test_producer_requires_build_admission_barrier_before_critic` |
| M3 | `C:949` 直後に新設する barrier checker | `barrier.seq < critic.seq` を `barrier.seq > critic.seq` に反転 | `test_barrier_rejects_critic_before_admission` |
| M4 | 同 barrier checker | decision SHA 比較を削除 | `test_barrier_rejects_report_decision_hash_mismatch` |
| M5 | 現行 `P:1796-1798` を移した postcritic helper | `critic is None` の `role-invalid` 代入を削除 | `test_post_admission_invalid_critic_keeps_admission_and_makes_partial` |
| M6 | `C:637` | prefix equalityを subset 判定へ緩和 | 既存 `test_state_machine_rejects_nonprefix_roles` |

単一理由性の確認:

- M1/M5 は direct helper testで completeness/chainを介さず、valid generation=1とpositive admissionを与える。前後の別gateに遮られない。
- M2 は missing barrier以外が完全なbuild fixture。closed event set、seq、role全単射、statusは通るため、新barrier必須gateだけがrejectする。
- M3/M4 は `seq` とjournal hashを再計算し、role attempt順とreport全単射を一致させる。後段state machineも通るためbarrier checkerだけがrejectする。
- M6 の fixtureは全role event shape、journal/report順、terminal projectionが有効。prefixを緩めると `C:827-841` の supervisor-error branchまで通るため、現行prefix gateが唯一のreject理由である。

候補から外すもの:

- generation上限行:通常の入力2はD114 approval gateと新critic capability gateの両方に関係し、monkeypatchなしでは後段がmaskされる。
- `AttemptJournal.seq += 1` (`P:521`): journal-sequence、role-bijection、複数テストが同時に落ち、単一kill nodeにならない。
- `_ROLE_ORDER` からcriticを削除: logical-id、prefix、state machine、全単射が同時に壊れる。
- hash固定 `P:1421`: journal-hashとpost-read race検査の複数層が同時に反応し、U-8固有の変異にならない。

## 親 brief の前提への訂正

1. P4の「実装上限10の経路」は通常実行可能な経路ではない。`main`、`run_trial`、direct `_run_workload` の3入口すべてが現状2以上を拒否する。2世代へ到達しているのは `TP:1634` や `TC:894` のように定数をmonkeypatchしたテストだけである。
2. 承認済み `generations=1` で単純に呼出し位置だけを変えても、report rolesとjournal role順は変わらない。したがって「completeness の受理集合が自動的に変わる」は正しくない。順序保証をartifactで検査可能にするには、今回推奨したbarrier event等を意図的に新設する必要がある。
3. `prior_reverse` がcellごとに初期化され、consumerが次generationだけであるというP4の機械的説明は正しい。
4. transport付きinner wall-budgetのterminal projection不整合は親briefが拾っていない既存所見である。

## 総括

- **(a) 推奨案:** cellごとに planner/coder/auditor/harness → Layer 3 admission → build-only journal barrier → critic とし、critic invalidは`role-invalid`、複数世代は別上限1でfail-closedにする。
- **(b) 変更ファイルと概算行数:** producer約140行、completeness約90行、指定2テスト約280行、`test_claude_transport.py`約5行、新D/spool・insight約50行、計およそ565行touch。
- **(c) 最大のリスク:** admission後・critic前のsupervisor failureを、generation重複なし・barrierあり・criticなし・terminal順維持で正しく復元するpartial state。
- **(d) 親briefの誤り:** 通常到達可能な「実装上限10経路」は存在せず、また1世代の単純移動だけではcompleteness受理集合もjournal上の観測可能な順序も変わらない。