## B1 — 組込み manifest では両ゲートが恒真

- **一次資料:** [tools/codex_reasoning_ab.py:229-270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:229)、[tools/codex_reasoning_ab.py:3017-3042](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:3017)、[tools/codex_reasoning_ab.py:10179-10184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:10179)
- **主張:** 実コードを `python3 -B` で評価し、POS、NEG、manifest union がすべて同じ 11 ID であることを確認した。従って組込み入力では、計画中の `_load_adjudication` の narrowing だけでなく、既存 `_aggregate_verified` の task 別検査も恒真であり、一度も union より狭い受理集合を作らない。§5.3 の「機構は着地」は「コードが存在する」という意味に限られ、現行組込み入力で発火実績があるという意味ではない。
- **成果物影響:** 組込み manifest の `valid`、受理集合、判断台帳は変更前後で同一であり、差が出るのは task ごとの集合が異なる外部 v3 manifest だけである。
- **修正案:** プランの外部 2-task fixture は必須。到達度文にも「組込み manifest 上では恒真、外部の異集合でのみ narrowing が発火」と残す。

## B2 — `_load_adjudication` 負例の帰属は正しいが、reader 方向が片側しかない

- **一次資料:** [s2-plan.md:126-130](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/s2-plan.md:126)、[tools/codex_reasoning_ab.py:9322-9336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9322)、[tools/codex_reasoning_ab.py:9385-9405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9385)、[tools/codex_reasoning_ab.py:11506-11516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:11506)
- **主張:** `alpha-finding` は manifest union 内なので `_validate_verdict_row` では落ちず、parent だけに置けば conservative intersection から消えるため `_aggregate_verified` にも届かない。従ってこの負例が落ちるべき箇所は、新設する `_load_adjudication` の raw-row task 別検査だけであり、帰属は成立する。ただし parent だけの負例では、second-reader の検査だけを削る変異が全テストを通る。
- **成果物影響:** second-reader だけが cross-task ID を出した場合、修正なしでは material report が `valid=True`、`experiment_complete=True` のまま受理され得る。
- **修正案:** `reader = parent / second-reader` の parametrized 負例にする。各ケースで `append_verdicts` が成功したこと、union 内であること、task-specific reason が exact 1 件であることを確認する。

## B3 — 既存 aggregate の task 別検査には負の証明がない

- **一次資料:** [tools/codex_reasoning_ab.py:10175-10184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:10175)、[test_codex_reasoning_ab.py:12094-12138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:12094)、[s2-plan.md:132-141](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/s2-plan.md:132)
- **主張:** 現行の外部 manifest aggregate 正例は beta slot に `beta-finding` を入れるだけである。`_aggregate_verified` の `equivalent not in known_finding_ids` を削除しても、この既存正例と計画中の 3 テストはすべて通り得る。計画の cross-task 負例は `_load_adjudication` 用、aggregate 負例は `oracle_kind` 用なので、既存 equivalent ゲートの「独立 fail-closed」は未検査のままである。
- **成果物影響:** loader を迂回した内部 caller、stub、将来の replay 経路から cross-task finding が渡ると、`valid=True` のまま negative false-finding 台帳や arm 除外判断へ混入し得る。
- **修正案:** `_aggregate_verified` へ外部 2-task manifest を直接渡し、beta verdict に union 内の `alpha-finding` を置く負例を追加する。削除変異で exact reason が消え、必ず赤になるようにする。

## B4 — 新 fixture は scheduleless 迂回か、2-slot schedule 不成立のどちらかになる

- **一次資料:** [s2-plan.md:100-116](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/s2-plan.md:100)、[tools/codex_reasoning_ab.py:9193-9213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9193)、[tools/codex_reasoning_ab.py:11307-11359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:11307)、[test_codex_reasoning_ab.py:9019-9023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:9019)
- **主張:** alpha/beta 各 1 slot の schedule は、各 block が 2 行かつ同一 task であることを要求する `_validate_schedule` に通らない。一方 schedule を packet source から省けば `make_packets` の scheduleless 互換経路を通るだけで、v3 schedule、`_replay_manifest`、`verify`/`aggregate` CLI の実配線を証明しない。既存の外部 replay テストも `_load_adjudication` を stub しているため、`_replay_manifest` から loader への `task_manifest` 転送を消す変異を検出できない。
- **成果物影響:** 正しい外部 manifest の CLI 実行が組込み manifest へフォールバックし、`task_manifest_sha256 mismatch` で常時 `valid=False` になるなど、「内部 unit は通るが実成果物を生成できない」状態を見逃す。
- **修正案:** alpha、beta 各 2 slot、合計 4 slot の paired schedule を作り、schedule descriptor を `make_packets` に含める。その fixture で実 `_load_adjudication` を通したうえ、少なくとも `verify_manifest` または `aggregate_manifest` まで到達する正例を追加する。CLI option の単なる mock forwarding test は代用にならない。

## B5 — oracle_kind の変異帰属と dimension 診断が未閉包

- **一次資料:** [s2-plan.md:24-46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/s2-plan.md:24)、[s2-plan.md:132-141](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/s2-plan.md:132)、[tools/codex_reasoning_ab.py:10154-10164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:10154)
- **主張:** aggregate 負例が「逆値または削除」のどちらか一方では、missing-field rejection を所有できない。例えば `verdict.get("oracle_kind", dimensions["oracle_kind"])` への変異は逆値テストを落とす一方、欠落を受理する。また、計画する dimension join reason の追加行には対応する負例がなく、reason 追加だけを削る変異は赤にならない。
- **成果物影響:** oracle_kind 欠落 verdict が `valid=True` になり得る。dimension reason だけの削除は受理集合を変えないが、failure report から packet/task の参照が失われるため、この部分は nit。
- **修正案:** oracle_kind は `wrong` と `missing` の 2 ケースを parametrized test にする。dimension join は exact reason を契約とするなら malformed-dimensions 負例を足し、契約にしないならプランから「明示的 reason」の実装要求を外す。

## B6 — brief の「coverage 分子が増える」は現行成果物に存在しない

- **一次資料:** [s1-brief.md:87-94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/context/s1-brief.md:87)、[prereg-8.md:25-37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/context/prereg-8.md:25)、[tools/codex_reasoning_ab.py:10243-10252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:10243)、[tools/codex_reasoning_ab.py:10452-10529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:10452)
- **主張:** `_aggregate_verified` には §8 の「一致した oracle finding 数 / oracle finding 総数」を生成する ledger や分母がない。現行コードで task-specific reason が変えるのは `valid`、`experiment_complete` と、無効時に null 化される主台帳であり、brief がいう coverage 分子ではない。
- **成果物影響:** 修正なしでは成果物説明が実在しない値を参照する。実際の差は、one-reader cross-task verdict に対する `valid=False`、`experiment_complete=False`、`primary_judgment_ledger`・`new_finding_ledger`・`decision` の null 化である。
- **修正案:** brief と docs の影響記述を実在する値へ直す。§8 coverage の numerator、denominator、negative-control 除外、false-finding rate の実装は本 wave 外の real な所見として裁定パッケージ候補にする。

## B7 — P1 の分離は成立するが、(b) 完了とは呼べない

- **一次資料:** [prereg-8.md:5-18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/context/prereg-8.md:5)、[prereg-8.md:22-30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/context/prereg-8.md:22)、[prereg-5.2-5.3.md:16-24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/context/prereg-5.2-5.3.md:16)、[prereg-5.2-5.3.md:88-114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/context/prereg-5.2-5.3.md:88)、[D767.md:3-15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/context/D767.md:3)
- **主張:** §8 の逐語は、ledger を「実験開始前に」作ることとその内容を要求しているが、generic consumer の実装前に ledger が存在しなければならないとは書いていない。従って台帳作成と束縛機構の実装は分離できる。ただし wave 後の呼称は、§5.2 では `_load_adjudication` が **部分実装**、§5.3 では **機構は着地**、**task 固有契約は未登録**、**acceptance 未束縛**の併記でなければならない。
- **成果物影響:** 「(b) 完了」または「実装済み」と書くと、存在しない独立 ledger と acceptance を certified report の参照元と誤認させる。routing/fix の選択結果は引き続き `inconclusive` である。
- **修正案:** 閉じていない面として、独立 ledger の作成・凍結、severity・must-fix・根拠 artifact・検出条件・canonical identity の schema、独立 hash 契約、task 固有 acceptance、§8 coverage と negative-control 集計、reader 独立性、組込み manifest の同一集合をすべて名指しする。

## 総括

must-fix は **B2、B3、B4、B5、B6**。

プランの中心述語と cross-task 負例の値選択は正しい。しかし aggregate 側の既存ゲート、second-reader 方向、missing oracle_kind、外部 manifest の replay/CLI 実配線に変異帰属がなく、現状のままでは「unit fixture 上は実装したが、独立防壁または実経路を検査していない」が残る。

pytest は実走していない。実施したのは静的検査と、組込み manifest の集合一致を確認する read-only の Python 評価だけである。