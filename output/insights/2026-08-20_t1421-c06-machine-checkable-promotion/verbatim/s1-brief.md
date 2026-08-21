# [T-1421]/[T-1384] C06 (budget consumer) を machine_checkable へ昇格する
- 目的: `orchestrator/campaign/s8c_budget.py` の条件6 (budget consumer) を D529 手順で machine_checkable へ昇格する
- 状態: 作業中 (段1 brief 完了、段2 へ)
- 最終更新: 2026-08-20
- 基準コミット: 9fb5216624aed75a77ed9dff9760333e2cd2b9bb (worktree: dev-wave-t1421-c06-machine-checkable-promotion、作業ツリー clean)

## 段1 brief

**scope:** D529/D533 手順に従い、以下 4 点を不可分の 1 commit で行う。
1. `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` condition 6 block (line 231-267)
   の `machine_checkable: false` → `true` へ反転 (line ~263)
2. `orchestrator/campaign/s8c_preregistration_evidence.py` の `_MACHINE_EVALUATORS` dict (line 3058-3067)
   へ `6: _evaluate_c06,` を数値順 (5 の次、7 の前) で追加。`_STAGED_EVALUATORS`
   (line 3539、現在 `_MappingProxyType({6: _evaluate_c06})`) から 6 を外し空にする
3. `orchestrator/campaign/s8c_preregistration.py` の `DECIDER_VERSION` (line 51、現在
   `"s8c-decider/v5"`) を v6 へ bump
4. 新世代 (第10世代想定、現行 generation 9 → 10) の condition-freeze record 発行。
   **record の実体 (別ファイルか埋め込み field か) は段2 codex plan (read-only) が
   `9f89da3d`/`73b66eca` の実 diff を読んで file:line で確定すること** — 親は
   generation 機構 (`generation_path()`, `_load_freeze_record`, `MAX_GENERATIONS`,
   `s8c_preregistration.py:1165-1240` 付近) の存在は確認したが、正確な生成手順は未確定。

**確定済みユーザー裁定:** command 引数どおり。D529 (docs/decisions.md:21856) が全体手順の正本。
`orchestrator/tests/test_s8c_preregistration_predicates.py` の
`test_current_contract_keeps_c06_staged_only` (現状 line 3666-3671 相当、fast-forward で
若干ズレる可能性あるため関数名で特定すること) の期待値を新状態に合わせて更新する
(`machine_checkable is True`・`6 in _MACHINE_EVALUATORS`・`_STAGED_EVALUATORS` は空・
`len(MACHINE_CHECKABLE_CONDITION_IDS) == 10`)。

**実装テンプレ (実 commit、段2 codex plan の第一入力):**
- `9f89da3d` — [T-1379] C05→v5昇格 (直近・最も詳細、`git show 9f89da3d` で全文参照)
- `73b66eca` — [T-1355] C07→v4昇格
両方とも「docs/spool worklog fragment 3枚 + s8c_preregistration.py 2行 +
s8c_preregistration_evidence.py 1-2行 + contract JSON 2行 + test 3ファイル改修 +
output/insights/<date>_<slug>/ 一式 (README・mutation-spec/out・verbatim/s1-brief)」という
同一構造。mutation matrix は両方とも baseline PASSED, 4/4 KILLED, SURVIVED 0, MISMATCH 0。

**不変条件:**
- 規律2 (正しさゲートを緩めない): 昇格は「機械検査を可能にする」だけで、`_evaluate_c06` 自体の
  判定ロジックを甘くする変更をしない。SATISFIABLE_CONDITION_IDS は空集合のままであり、C06 昇格後も
  UNSATISFIED か EVIDENCE_UNDEFINED に留まる見込み (memory `s8c-evidence-undefined-is-the-pass-terminal`:
  これは合格終端であり未実装の印ではない — SATISFIED を無理に狙わない)。
- D533: 段階登録の evaluator 本体は今回 scope 外 (既に staged で実装済み)。本体ロジックへ触るのは
  段2/3 が構造的欠陥を発見し段4 で scope 内と裁定した場合のみ
- (P1・攻撃対象) `_evaluate_c06`/`_c06_field_path_verdict` (evidence.py:3358-3477 想定、行番号は
  fast-forward でズレうるので関数名で確認) が negative control
  (`nc_c06_one_arm_reservation_removed`) を正しく検出できるかは、今回の 1-bit 昇格そのものでは
  再検証されない。T-1421 起票時点の「直接実行で構造検査通過を確認済み」という主張を段2 codex が
  再現し、段3 敵対レンズの一方はこの評価器本体の頑健性 (reachability 構造検査の抜け・
  negative control の実効性) を専任で攻撃すること
- (P2・scope 外仮置き) 評価器本体のバグ修正は本 wave の scope 外と仮定。段2/3 が発見したら
  段4 で real/refuted と scope 内外を裁定する
- 兄弟条件 C03/C08 は現時点で `_MACHINE_EVALUATORS` 未登録・staged 未着手 (T-1422 が調査中、
  worktree 起票なし) — 本 wave の影響範囲外、触らない

**衝突確認 (実測済み、2026-08-20):** 全 `.claude/worktrees/*` を `git diff main --stat` で
共有編集面4ファイル (`s8c_preregistration_evidence.py`/`s8c_preregistration.py`/
`s8c_preregistration_evidence_contract.v1.json`/`test_s8c_preregistration_{core,invariant,predicates}.py`)
について走査した (memory `s8c-condition-family-shared-edit-surface` の教訓どおり、command が
名指しした worktree だけでなく全件)。ヒット4件、いずれも非衝突と確認済み:
- `dev-wave-t1337-launcher-timing-proof`: `_evaluate_c03` 本体 + C03 fixture (line ~1634/2916/3032
  相当) のみ。`_MACHINE_EVALUATORS`/`_STAGED_EVALUATORS`/`DECIDER_VERSION`/対象テスト関数は非接触
- `dev-wave-t183-codex-failure-classification` / `humble-questing-lerdorf`: 両方とも
  main に対する固有コミット 0 件 (`git log main..HEAD` 空)。表示された diff は C01 (T-1420 landed
  済み) 由来の main 側変更に対する純粋な遅れで、能動的な編集ではない
- `dev-wave-jobs/t1363-c06-budget-consumer/.../worktree`: detached HEAD、main に対し
  3674 行削除相当の逆行 diff (2026-08-18 時点で停止した古い受入debris、`.claude/worktrees/`
  未登録)。生きた作業ではない — dev-wave 改善候補として下に記録、cleanup は本 wave の scope 外
- ListAgents (21 peer) にも C0x/s8c/budget/decider 名の busy peer なし

**成果物影響 (DW-G05):** 実施しない場合、8c 事前登録は 12 条件中 9 条件 (C06 昇格後は10条件) しか
機械検査できないままで、budget consumer 面 (予算予約・決済・対称停止) の証拠が引き続き人間レビュー
依存に留まり、certified 選択の proof chain における機械保証範囲が広がらない。

**並列分割方針:** 実装差分は小さく (contract 1箇所 + registry 1行 + STAGED除去 + version 1行 +
generation record 発行 + test 更新) 密結合 (D529 により同一commit必須) — 段5 実装単位は分割せず
単一 Codex author 単位とする。

## dev-wave 改善候補 (段8 裁定用、随時追記)
1. **`dev-wave-jobs/t1363-c06-budget-consumer/izanagi-acceptance-reds-cw83yun7/worktree` が
   `.claude/worktrees/` 未登録のまま stale で残存し、`git worktree list` に出続けている。**
   2026-08-18 時点の古い受入debrisで生きた作業ではないが、C0x 系ファイルへの衝突チェック時に
   誤検出候補として毎回引っかかる。cleanup-branches の対象候補として記録 (本 wave では削除しない)。
2. **EnterWorktree の既定 (`fresh`=`origin/<default-branch>` から分岐) が、今回
   実際には stale な commit (`954ae781`、既に main へ吸収済みの旧 worktree HEAD と同一) から
   worktree を作成した。** `main`/`origin/main` 自体は正しく現行 tip (`9fb52166`) を指していたため
   原因未特定。実害は `git merge --ff-only main` で即復旧したが、dev-wave 起動直後に
   `git rev-parse HEAD` と `git rev-parse main` の一致を毎回実測すべきという教訓
   (DW-O20 の check_wave_startup.py --mode fresh が最終的に検出するはずだが、事前に気づけば
   1 手番節約できる)。

## 段2 codex plan (完了、rc=0)
出力: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1421-c06-machine-checkable-promotion/stage2-plan-output.md`
generation record は別ファイル `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g10.json`、
`python3 -m orchestrator.campaign.s8c_preregistration prepare-revision --repo-root . --commit HEAD
--ruling-reference D529 --revision-reason '...'` で発行と判明 (段1で未解決だった論点を解消)。
`_MACHINE_EVALUATORS` は `_evaluate_c06` (evidence.py:3477) より前 (:3058) にあるため単純追加は
import 時 `NameError` になると指摘。

## 段3 敵対相談 (完了、2レンズとも rc=0)
- lensA (sol、正しさ境界・整合性): blocker 0。real は「stale な staged 表現の残存」(minor) と
  「negative-control wrapper 統合方法の未確定」(unclear だが要対応)。他は全て段2プランを裏取りし
  refuted (map移動の必要性・hash値・prepare-revision引数と実行順序・supersedes_sha256の意味・
  D529受理条件の充足を確認)。
- lensB (luna、実効性・regulation-2): blocker 1件「`_MACHINE_EVALUATORS` へ C06 追加で過去 commit の
  reason code が変わる」、major 1件「machine-checkable宣言が実際の検査より強い」、このまま昇格は
  NO と判定。他は refuted (SATISFIED到達不能・P3はC06 predicateを読まない・負対照検出力維持・
  C06が唯一のstaged条件)。

## 段4 親裁定 (完了)
裁定inboxを再走査 (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) — 本wave開始後の新着なし。
T-1202/T-1197 (2026-08-17、decider version bump が並行 wave の凍結世代着地と衝突し land 不能に
なった事例) を教訓として吸収: 段9 直前に main の凍結世代が動いていないか再確認すること。

**lensB blocker (過去commit reason code回帰) を親が直接 `PredicateRegistry.evaluate_all`
(evidence.py:3103-3205) と `_evaluate_undefined` (:3073-3100) を読んで検証し、REFUTED と裁定した。**
理由: dispatch (`evaluate_all`:3159) は評価対象 **commit 自身の contract blob** の
`condition.machine_checkable` で production/staged を振り分ける (現在コードの `_MACHINE_EVALUATORS`
静的メンバーシップだけでは production 経路に入らない)。`_evaluate_undefined` 内の
`number in _MACHINE_EVALUATORS` 分岐 (:3079) による reason 遷移
(`budget-consumer-contract-undefined` → `completion-proof-not-machine-checkable`) は、
現に C05/C07 など既存9条件の昇格でも同じ機構が既に発生させている**既存の意図的挙動**であり
(現在の `_MACHINE_EVALUATORS` に 5・7 が入っているため、それらの昇格前 commit を現行コードで
評価すれば同じ遷移が起きる)、C06 固有の新規回帰ではない。段2プランの
`test_current_repository_gap_reason_snapshot_requires_cross_wave_review` 更新がこの遷移を
意識的に吸収する設計 (テスト名の「cross wave review」どおり)。**lensB の提案する対処
(number==6 分岐を map membership より前に置く) は、C05/C07 の既存挙動と非対称になり過去の昇格を
無断で書き換えることになるため不採用。**

lensB major (reachability検査の甘さ) は段2プラン・lensA・lensB の3者が独立に到達した既知の事実。
`SATISFIABLE_CONDITION_IDS` が空集合 (:3070) であり `evaluate_all` 自身の防御的再チェック
(:3180-3188、`is_satisfied` かつ非allowlistなら強制ERROR) もあるため、本waveでも regulation2
(正しさゲートを緩めない) は侵害されない。lensBの「昇格保留」は少数意見 (段2プラン・lensAは
scope-out採用、親自身の直接検証でも安全と確認) のため不採用。評価器強化は後続waveのbacklogとして
段7で明示的に記録する (D533 の「評価器改善は登録と分離できる」先例どおり)。

lensA の real 所見2件はプランv2へ採用: (1) staged関連コメント・命名 (:3235-3236 等) を
production状態の記述へ更新、(2) `STAGED_NEGATIVE_CONTROL_CASES`/`_negative_control_c06`/
`_BASE_NEGATIVE_CONTROL_CASE`/wrapper再定義を撤去し、そのmutationロジックをmain
`_negative_control_case` 本体 (:1191近辺) へ統合する (統合しないと `AssertionError` になる)。

### プランv2 (段2からの確定差分)
1. `_MACHINE_EVALUATORS`/`MACHINE_CHECKABLE_CONDITION_IDS` の定義文だけを `_evaluate_c06` 定義後へ
   移動する。`_evaluate_undefined`/`PredicateRegistry.evaluate_all` は移動不要 (関数本体内の名前解決は
   モジュールロード完了後に行われるため、定義順に依存しない)。`SATISFIABLE_CONDITION_IDS` も移動不要。
2. `prepare-revision` はコード/契約変更を **未commitのまま** 実行し、生成された g10 record を
   含めて全部を1回のcommitにまとめる (lensA確認済みの実行順序、先にcommitすると履歴検査で失敗)。
3. staged negative-control wrapper を撤去しmain dispatcherへ統合する。
4. stale staged コメント・命名を production 状態の記述へ更新する。
5. reachability検査の甘さは本waveでは修正しない。段7で backlog として明示記録する。

### 変異事前登録 (DW-M01、段4)
C05 (`9f89da3d`)・C07 (`73b66eca`) と同型 (baseline PASSED, 4/4 KILLED, SURVIVED 0, MISMATCH 0) を
テンプレとし、D529 の4点それぞれに1変異を対応させる (各点は独立した meta-test/consistency-check で
守られており、同じ入力を拒否する層が前後に重複しないため単一理由性が成立する)。
- M1: contract JSON の C06 `machine_checkable: true` → `false` へ逆変異。検出層 = 新設する
  machine_checkable 正例テスト (旧 `test_current_contract_keeps_c06_staged_only` の反転後版)。
- M2: `_MACHINE_EVALUATORS` から `6: _evaluate_c06` を除去 (contractはtrueのまま)。検出層 =
  contract⇔registry 双射を要求する invariant/predicate meta-test。
- M3: `DECIDER_VERSION` を v6→v5 へ逆変異 (g10 recordはv6のまま)。検出層 = tip/version 束縛
  一貫性テスト (`test_s8c_preregistration_invariant.py` 系)。
- M4: g10 generation record を欠落/g9のまま に逆変異 (コードはv6のまま)。検出層 = freeze chain
  妥当性検査。
実装後、DW-M07 (fix後anchor) に従い最終commitへ対して anchor 逐語と期待nodeを再検証してから
本走する。

## 段5 実装 (完了、rc=0、未commit)
出力: `stage5-author-output.md`。diff は計画v2と file:line 単位で完全一致 (親が `git diff` で
全ファイル直接確認済み): 契約反転 (:264)、`_MACHINE_EVALUATORS`/`MACHINE_CHECKABLE_CONDITION_IDS`
の `_evaluate_c06` 定義後への移動 + `6:_evaluate_c06` 追加、`_STAGED_EVALUATORS` 空化、stale
コメント更新、`DECIDER_VERSION` v6、g10 record (generation=10, decider=v6, evidence_hash/
protected_hash/supersedes_hash が段2 plan・lensA 独立計算と3者一致)、negative-control wrapper
撤去 (main `_negative_control_case` 本体へ統合)、テスト改名・値更新全項目。

**重要な検証 (親が実施、DW-O06/DW-O18/DW-O26):**
- 直接編集した3テストファイルを `tools/run_tests.py` (計算ノード dispatch) で自分の環境で実走:
  **594 passed, 1 failed** (実装子報告の「6 errors」はサンドボックス固有で私の環境では0件再現 —
  sandboxのread-only `.git/.agents`によるcandidate fixture作成失敗が原因と確認)。残る1件
  `test_current_repository_snapshot_exactly_matches_head` は commit前提のtripwire (既知パターン、
  memory `s8c-evidence-undefined-is-the-pass-terminal` 参照)。
- DW-O26 (consumer test 拡張) に従い `s8c_preregistration_evidence`/`DECIDER_VERSION` を参照する
  8ファイルを追加で焦点走 → **10件の追加red (4 failed + 6 error、test_p3_autonomous_workload_trial.py
  と test_trial_registry.py に集中)。**
- **`git stash` による安全なA/B検証 (2回、100%再現性) で、この10件が私のC06変更に起因すると確定**
  (変更除去時: 680 passed 0 failed。変更復元時: 670 passed, 4 failed, 6 errors、同一10 nodeidが
  毎回同じ)。
- 根本原因を1 ERROR + 1 FAILED を詳細確認して特定: `orchestrator/tests/conftest.py:148` の
  `ratified_enforcement_source` fixture が `contract_loader_binding.capture_contract_loader_binding()`
  を呼び、`CONTRACT_LOADER_RELATIVE_PATHS` (`orchestrator/campaign/s8c_preregistration.py` を含む)
  の **disk bytes が HEAD blob と一致すること** を要求する。エラーメッセージが直接
  `contract-loader-drift: disk bytes が HEAD blob と不一致: orchestrator/campaign/s8c_preregistration.py`
  と明示。**これは `test_current_repository_snapshot_exactly_matches_head` と同型の
  「commit前提のtripwire」であり、単に影響範囲が s8c predicate test 自身を超えて
  p3/trial_registry の acceptance系テストにも及んでいただけ。統合commit後に自然解消する見込み。**
  FAILED側2件 (`assert 0 == 1` payload_bytes空、`CampaignVerifierEpochRejected`) も同根の
  dirty-state検出の下流影響と判断 (直接の「disk≠HEAD」文字列は出ないが、A/B結果の完全再現性・
  campaign verifier由来のreject文言と整合)。
- stashは安全手順 (push -u -m タグ→SHA捕捉→apply→drop) で後始末済み、他セッションのstash entry
  には触れていない。

**段6/段7への申し送り (重要):** 統合commit後、この10件 + `test_current_repository_snapshot_exactly_matches_head`
の計11件を含めて **再実走し全て緑になることを確認してから受入全走へ進む**こと。緑にならなければ
「commit後に解消するpre-commit artifact」という本裁定は誤りだったことになり、実装差分を再検査する。

## 未完の作業と次の一手
1. 段6: 敵対レビュー2本 (reasoning=max、実際の diff を対象。1本は「diffがD529/計画v2と正確に
   一致するか」、もう1本は「他に見落とした consumer/回帰がないか、上記10件red裁定の妥当性」を
   専任で攻撃) → fix (real所見があれば) → 統合commit (親) → **commit後に上記11 nodeidを含む
   再実走で全緑を確認** → 変異matrix (M1-M4本走) → 受入全走
   (`tools/dev_wave_wait.py acceptance` で lease claim 後に投入)。
2. 段7: worklog fragment で T-1421 と T-1384 の両方の carry を解消。insight package・decisions
   fragment (regulation2裁定・lensB blocker refutedの根拠・10 red のcommit-tripwire裁定を記録)・
   failures fragment (reachability検査の甘さをbacklog化)。
3. 段8: 上記「dev-wave改善候補」2件 (t1363 debris worktree残置、EnterWorktree stale base) を裁定。
4. 段9: local main取り込み直前に main の凍結世代が動いていないか再確認 (T-1202/T-1197教訓)。
