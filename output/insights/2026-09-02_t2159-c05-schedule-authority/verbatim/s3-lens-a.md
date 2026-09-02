## 所見 1 — `whiteboard=[]` は受理集合の緩和である

**主張:** 新旧の受理集合全体は包含関係ではなく不比較だが、`[]` という従来拒否入力を新たに受理する。しかも production 値を C05 authority に通す目的の例外なので、「述語を通すための受理緩和」に該当する。

**根拠 (file:line):** 現行は `whiteboard` を sequence authority とし、空配列を一律拒否する（`orchestrator/campaign/s8c_schedule.py:106-110,167-207,235-249`）。production の fresh state は `[]`（`orchestrator/campaign/p3_autonomous_workload_trial.py:1707-1709,3810`）。プランは `whiteboard` だけ非退化検査を外して exact `[]` を受理すると明記する（`s2-plan.md:148-154`）。親 brief の絶対規律は受理集合を広げないこと（`brief.md:30`）。

**成果物へどう効くか:** 非空 list/tuple を同時に拒否しても、empty-list slice は `拒否→受理` になる。「単純な上位集合ではない」という説明は、この新規受理を打ち消さない。

**これが正しければプランのどこを変えるか:** `s8c_schedule.validate_authority` の局所例外案は採らない。`whiteboard` を共有 authority に含める設計自体を再裁定し、空状態を表現できる versioned schema、または caller-supplied authority のいずれかへ戻す。

## 所見 2 — loader は production では構造上到達不能のまま

**主張:** §5・schedule artifact・ratified freeze を将来そろえても、現行契約のままでは `_load_s8c_schedule_authority` の受理分岐に production から到達できない。一方、C05 の AST 探索はその死んだ経路を「到達」と数える。

**根拠 (file:line):**

- loader を呼ぶ budget 分岐は `registered-effective and do_build` のみ（`orchestrator/campaign/p3_autonomous_workload_trial.py:4576-4578,4709-4715`）。
- `registered-effective` capability は全12述語が `SATISFIED` の場合だけ発行可能（`orchestrator/campaign/s8c_preregistration.py:1925-1930,1951-1956,1998-2003`）。
- `_evaluate_c05` は全検査を通っても必ず `EVIDENCE_UNDEFINED` を返す（`orchestrator/campaign/s8c_preregistration_evidence.py:2188-2192`）。さらに C10 以外の `SATISFIED` は `ERROR` にされる（同 `:3335,3445-3453`）。
- 到達性探索は非 literal 条件の両 branch を live と扱う（同 `:636-645`）。したがって `c06_budget_enabled` が実際には成立不能でも call graph に入る。
- 親 brief 自身も上流 gate を認識している（`brief.md:39-47`）が、「人が §5 を埋めるまで発火しない」は必要条件を一つだけ抜き出した不十分な表現である。

**成果物へどう効くか:** AST 上の reason code は `schedule-consumer-unreachable` から `completion-proof-not-machine-checkable` へ変えられるが、production の実行可能性は1ビットも変わらない。D1448 の「正式経路を生かす」成果とは言えない。

**これが正しければプランのどこを変えるか:** evaluator/activation/admission を編集しない条件なら、成果を「到達不能な将来用 readiness code」に限定し、D1448 完了や production 配線完了を主張しない。本当に production 到達を成果条件にするなら、禁止面を含む段4裁定へ戻す。

## 所見 3 — C05 evaluator は artifact の中身を一切検証しない

**主張:** `schedule.v1.json` は存在するだけで第1関門を通る。空 bytes、非 JSON、改竄済み digest でも、consumer の関数名と call graph があれば C05 は同じ `completion-proof-not-machine-checkable` へ進む。

**根拠 (file:line):** `_evaluate_c05` は `read_kind("schedule_artifact") is None` だけを調べ、得た bytes を decode・regenerate・verify のいずれにも渡さない（`orchestrator/campaign/s8c_preregistration_evidence.py:2083-2089`）。その後の検査は consumer の関数集合、文字列 literal、call graph だけ（同 `:2091-2186`）。D549 も「artifact/authority の中身の正当性を問わない」と明記する（`docs/decisions.md:22420-22422`）。

**成果物へどう効くか:** runtime loader が強くても所見2のため実行されず、commit evidence 側には「置けば進む」経路だけが残る。これは brief の禁止事項（`brief.md:53-59`）と正面から矛盾する。

**これが正しければプランのどこを変えるか:** evaluator を編集不要とする `s2-plan.md:213-235,299-311` を撤回する。少なくとも corrupt/noncanonical/seed・digest 不一致 artifact mutation を C05 evaluator に掛け、同じ結果になる現状を段4へ提示する。

## 所見 4 — `descriptor_binding` 完全表は共有初期状態の証明にならない

**主張:** six-cell 完全表を単数 `descriptor_binding` に入れる案は、cell ごとに異なる実 binding を一つの表で包み、全 cell に同じ hash を複製するだけである。共有初期状態を証明していない。

**根拠 (file:line):**

- schedule generator は authority 全体から一つの `initial_digest` を作り、それを全6 cell にコピーする（`orchestrator/campaign/s8c_schedule.py:317-339`）。shared verifier もその同一値を比較するだけ（同 `:478-495`）。
- 実行時の `descriptor_binding` は選択された一 cell の `descriptor_record`（`orchestrator/campaign/p3_autonomous_workload_trial.py:2642-2659,3790-3826`）。
- resolver は arm ごとに異なる descriptor bytes を選び、三 arm の content digest が相異なることを要求する（`orchestrator/campaign/s8c_arm_inputs.py:434-478`）。
- プランはこれらを完全表にして単数 field へ入れる（`s2-plan.md:129,156-158`）。

**成果物へどう効くか:** schedule hash と実際に各 trial が消費した binding row の対応が schedule artifact に存在しない。表が自己整合しているだけでも全 cell の shared hash は通る。

**これが正しければプランのどこを変えるか:** cell-specific binding digest を各 schedule cell へ明示して launch binding と照合するか、`descriptor_binding` を shared-initial-state authority から外す versioned redesign が必要。既存単数 field の意味を完全表へ読み替えない。

## 所見 5 — zero reservation で予算保証が恒真化する

**主張:** プランの値域では全 cell の `reserved_bench_s=0` が正例になる。上限も非負なら ledger は `held` となり、bench を開始してから初めて超過が判明する。

**根拠 (file:line):** 数値 validator は有限な「非負」だけを要求し、0を受理する（`orchestrator/campaign/s8c_budget.py:43-49,83-128`）。十分性は予約値の合計が上限以下かだけで判定する（同 `:517-530`）ため、全ゼロは `held`（同 `:533-568`）。`held` 後に run が継続する（`orchestrator/campaign/p3_autonomous_workload_trial.py:4717-4751`）。プランの負例は bool・負・非有限だけで、zero を含まない（`s2-plan.md:266-268`）。

**成果物へどう効くか:** 「予算 consumer がある」という外形は満たしながら、実測前の予約防壁をゼロで無効化できる。正の実測は terminal settlement で落ちるだけで、事前停止にならない。

**これが正しければプランのどこを変えるか:** six-cell reservation は各 cell strict-positive、少なくとも総予約値 strict-positive を要求する。zero reservation が launch 前に `insufficient` へ倒れる負例を追加する。

## 所見 6 — `reserved_bench_s` の出所は §5 に存在しない

**主張:** measurements の「ReservationCell の値も§5未記入欄に対応する」という一般化は根拠不足で、プランは scope 外の preregistration schema を暗黙に新設している。

**根拠 (file:line):**

- §5 の欄名と規範は total、arm、holdout の上限だけを定め、per-cell reservation は定めない（`docs/phase3-8c-preregistration.md:159-165,194-205`、`verbatim-prereg-s5-s6.md:3-13`）。
- parser の値域 validator は反復対比欄にしか存在しない（`orchestrator/campaign/s8c_preregistration.py:948-952`）。
- activation は内容の型ではなく `FILLED` かだけで判断する（同 `:1925-1955`）。
- measurements は `ReservationCell.reserved_bench_s` まで同じ欄に対応すると断定する（`measurements.md:53-57`）。
- プランは undocumented な第四 key として追加する（`s2-plan.md:172-179`）一方、§5 と preregistration module を編集対象外にする（同 `:299-311`）。

**成果物へどう効くか:** 将来の記入者が正本から導出できない hidden schema が production consumer にだけ現れる。値の発明を避けたのではなく、値の置き場所と意味を実装側で発明している。

**これが正しければプランのどこを変えるか:** per-cell reservation を別の明示的な事前登録 field／manifest fieldとして versioned に定義し、activation validator も同じ改訂単位で追加する。禁止面を触らずに済むという判断は撤回して段4へ戻す。

## 所見 7 — schedule/budget 検証の順序が遅すぎる

**主張:** プランは既存 call site を維持するため、registered attempt の予約・分類・lifecycle start、origin 経路では observation 開始の後に schedule と budget を検証する。

**根拠 (file:line):** attempt slot は `:4628-4639`、classification は `:4646-4670`、origin observation/read は `:4671-4678`、lifecycle start は `:4679-4697`。schedule/budget loader と全 cell reservation はその後の `:4709-4727`（すべて `orchestrator/campaign/p3_autonomous_workload_trial.py`）。プランはこの call site を維持する（`s2-plan.md:226-228`）。

**成果物へどう効くか:** §5 や schedule の不正が分かった時点で attempt/lifecycle が既に消費され、origin 経路では observation まで始まっている。「実走前に固定・検証」の失敗境界になっていない。

**これが正しければプランのどこを変えるか:** schedule/§5/ratified freeze の検証と全-cell budget reservation を、attempt classification・observation・lifecycle start より前の preflight へ移す。順序 mutation test も必要。

## 所見 8 — test は両層 stub を概ね避けるが、負例3件は実装削除でも通り得る

**主張:** success-path と C05 mutation は実体を名指ししている。一方、例外の型だけを見る負例は、旧「常に raise」に戻しても通り得る。既存 shape test は loader を完全 stub している。

**根拠 (file:line):** 計画された tests は `s2-plan.md:237-287`。現行 caller test は `_load_s8c_schedule_authority` を lambda へ差し替える（`orchestrator/tests/test_p3_autonomous_workload_trial.py:9024-9055`）。現行 C05 helper は p3 を worktree でなく `git show HEAD` から読む（`orchestrator/tests/test_s8c_preregistration_predicates.py:4036-4069`）。

|計画 test|実装削除でも通り得るか|静的判定|
|---|---:|---|
|`whiteboard=[]` 受理・非空/tuple/mapping 拒否|いいえ|旧 validator は `[]` を拒否し非空を受理する|
|17 key digest＋whiteboard拒否|いいえ|新 fixture `[]` が旧 validator で落ちる|
|loader resolves committed schedule/cells|いいえ|成功を要求する|
|loader uses supplied root|いいえ|成功を要求する|
|rejects worktree/commit drift|**はい**|単なる `pytest.raises` なら無条件 raise でも通る|
|rejects seed/authority drift|**はい**|同上|
|fails closed for §5 status|いいえ|プランは理由文字列 exact 比較を要求|
|rejects budget shape|**はい**|計画文には理由 exact 比較がない|
|prepare with real loader|いいえ|loader と schedule module を stub せず成功を要求|
|C05 positive with real p3/schedule bytes|いいえ|loader 呼出しを消せば `UNSATISFIED` になる|
|p3 の `load_schedule` 除去 mutation|いいえ|実 target の欠落を検出|
|p3 の `consume_schedule` 除去 mutation|いいえ|同上|
|schedule の `consume→verify` 除去 mutation|いいえ|`_live_called_names` が検出|
|既存 `_s8c_budget_test_setup`|**はい**|loader を完全 stub。production 証拠にはならない|

**成果物へどう効くか:** 特定の負例だけを見れば「常に失敗する loader」が緑になり得る。また current helper の `git show HEAD` を残すと、commit 前 test は作業差分を検査しない。

**これが正しければプランのどこを変えるか:** 3負例すべてで exact reason を要求し、同一 fixture の mutation 前成功も先に確認する。C05 helper は production file の worktree bytes を読む。garbage artifact、zero reservation、runtime順序の mutation も追加する。

## 所見 9 — 既存期待値の変更には一件、誤りを隠す向きがある

**主張:** whiteboard 系の期待変更は schema 決定そのものなので、裁定後なら整合する。しかし C05 direct evaluator の期待を `UNSATISFIED` から `EVIDENCE_UNDEFINED` へ変える変更は、production 到達不能を静的 call graph で覆い隠す。

**根拠 (file:line):**

- 現行 fixture は非空 whiteboard（`orchestrator/tests/test_s8c_schedule.py:12-70`、`orchestrator/tests/test_s8c_preregistration_predicates.py:44-102`）。
- 現行 digest test は whiteboard も mutation→digest差を期待する（`orchestrator/tests/test_s8c_schedule.py:199-211`）。プランはこれを拒否期待へ変える（`s2-plan.md:239-244`）。
- 現行 C05 direct test は `UNSATISFIED / schedule-consumer-unreachable`（`orchestrator/tests/test_s8c_preregistration_predicates.py:4075-4078`）。プランは `EVIDENCE_UNDEFINED` へ変える（`s2-plan.md:281-284`）。
- 実 HEAD の通常評価は artifact 不在のため `schedule-schema-absent` であり（`measurements.md:7-24`）、プランの「現行 UNSATISFIED」は synthetic artifact 注入時の反実仮想である（`s2-plan.md:230-233`）。

**成果物へどう効くか:** C05 の期待変更が「production wiring が生きた」証拠として読まれると誤りを隠す。実際に変わるのは synthetic static probe の reason code だけである。

**これが正しければプランのどこを変えるか:** test 名と説明を `counterfactual_static_reachability_with_injected_artifact` 相当にし、production 到達性の証拠に数えない。通常 HEAD の `schedule-schema-absent` 期待は別に維持する。

## 所見 10 — 親 brief / measurements の provisional 裁定は再裁定が必要

**主張:** P1-a は条件付きで成立するが、P1-b、P1-c、P1-d、P1-e の結論はそのまま採用できない。また brief の「現状 raise を固定する test」という実アンカーは事実と異なる。

**根拠 (file:line):**

- **P1-a:** `{"text": LEAKPROOF_CONTEXT}` は単射だが、実 payload は文字列のまま（`orchestrator/campaign/p3_autonomous_workload_trial.py:3988-4005`）。wrapper が実値の exact projection である検査が必要。
- **P1-b:** 所見1のとおり新規受理である（`brief.md:67-69`、`s2-plan.md:146-154`）。
- **P1-c:** 所見4のとおり cell-specific binding を共有表で包む proxy である（`brief.md:70-71`）。
- **P1-d:** parser 再利用は可能だが、budget/master_seed の意味・値域 validator は存在しない（`brief.md:72-73`、`orchestrator/campaign/s8c_preregistration.py:948-952`）。
- **P1-e:** synthetic test が必要という診断は正しいが、artifact 内容と production 動的到達性の mutation が欠ける（`brief.md:74-76`）。
- brief が「現状の raise を固定する test」とする `:9053` は、実際には loader を成功 lambda に置換する monkeypatch である（`brief.md:98`、`orchestrator/tests/test_p3_autonomous_workload_trial.py:9051-9055`）。
- measurements M5 の `reserved_bench_s` まで§5対応値とする一般化には規範上の根拠がない（`measurements.md:53-57`）。

**成果物へどう効くか:** 親の scope 外線引きを前提に実装へ進むと、必要な schema/evaluator 改訂を回避したまま、proxy と synthetic reason change が成果として固定される。

**これが正しければプランのどこを変えるか:** P1-b/P1-c/P1-d と禁止面を段4へ戻す。P1-a は wrapper と実文字列の exact 対応 test を条件に残せる。P1-e は corrupt artifact・dynamic gate・zero reservation・順序 mutation を追加する。

## 総括

**最も重い所見 3 件まで**

- production では loader に構造上到達できないのに、AST evaluator は到達済みと判定する。
- C05 evaluator は schedule artifact の内容を一切検証せず、任意 bytes で構造検査を進められる。
- `whiteboard=[]` は production 値を通すための新規受理であり、絶対規律2に抵触する。

**プランをそのまま実装してよいか:** **だめ**。
禁止面である evaluator/preregistration schema の再裁定なしには、production 保証ではなく到達不能な静的外形しか作れない。受理緩和と undocumented budget schema も未解決である。

**自分が確かめられなかった箇所**

- pytest は実走しておらず、緑とは判定していない。test verdict は静的な削除変異判定である。
- §5 数値、master seed、schedule artifact、active ratified freeze が不在のため production 受理分岐は実走確認できない。
- measurements の evaluator 出力と ratified-freeze 例外は再実走せず、提示値と source の静的整合だけを検査した。