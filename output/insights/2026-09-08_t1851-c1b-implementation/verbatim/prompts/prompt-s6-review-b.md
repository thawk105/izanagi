単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s4-adjudication.md

## 前提 (read-only)

**書込可能な tmp が無いため pytest 緑を要求しない。静的検査でよい。** テスト実測は親が行う。
**file を書けないので、成果はすべて最終メッセージ本文に全文で書け。** 途中で予算が尽きそうなら、
そこまでの結論を出力形式どおり書いて終われ。無出力が最悪である。

## 必読事項の射影

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review`
(detached HEAD、commit `d52b2f833`) である。すべてこの worktree の中で読む。
**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `<repo>/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md` — **契約の正本**
2. `<repo>/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/plan-v2.md` — 実装 plan
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s4-adjudication.md` — 親の段 4 裁定
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s1-brief.md` — 親 brief

審査対象は commit `d03b26773` と `d52b2f833` の 2 本 (`git log -2 -p` で読める)。変更 file は 9 本。

## レンズ B — 契約への逐条適合と、既存受理集合・consumer の保全

**あなたの役割は「契約が書いた条項と実装が字面で食い違う箇所」と「この変更が repo の他の場所を
壊す箇所」を見つけることである。** 機構が発火するかはレンズ A が担当するので、あなたは
**条文対照と波及**に集中せよ。

次を順に検査せよ。

1. **逐条対照。** 契約 v3.1 の 1.1 / 1.2 / 1.3 / 1.4 / 1.5 / 2 / 3 / 4.1 / 4.2 / 4.3 / 5.1 /
   5.1.1 / 5.3 / 5.4 / 6.1 / 6.2 / 6.3 / 7 / 8 / 9 の**各条項について**、実装のどの file:line が
   それを担っているかを対応づけ、**担い手が無い条項**と**条文と違う実装**を挙げよ。
   特に次を数えて確かめよ。
   - `campaign_record` の **exact 30 key** が `s8b_ratified_freeze._JOURNAL_KEYS["session"]` と
     集合等値か
   - draft の `attempt_binding` が **exact 9 key** で、3 digest の key が **null ではなく欠落**か
   - validated が **exact 12 key** か
   - 3 digest の綴りが `classification_receipt_sha256` / `classification_event_sha256` /
     **`observation_event_sha256`** か。行側の `observation_start_event_sha256` と
     **同名化していない**か (契約 1.3)
   - E2 が exact 4 語で、**v1 の retryable 集合が空のまま**か
   - E1 の枝が契約 4.1 の**順序**どおりか (枝 1 から 7)
   - 契約 1.4 の不変条件
     `len(throughputs) + nonfinite_count + exec_failures == reps_expected` が実装されているか
   - **`assess_session` へ渡す reps が「元の `reps_expected`」であって、落とした本数だけ
     減らしたものでない**か
2. **契約 8 節「採らないもの」の混入。** claim v4 の新設、`_AttemptState` への `mode` 追加、
   core 公開 API 8 surface への capability 伝播が**紛れ込んでいないか。**
3. **契約 9 節「主張しないこと」の逸脱。** 実装や docstring が、契約が「主張しない」と定めたことを
   **主張していないか** (`exec_failures` が rep ごとの実行成否を証明する、権威の無い 6 語が
   帳簿上の位置を保証する、campaign が同じ入力で同じ語を出す、同一 process の module 改変への
   防壁、など)。
4. **pin 閉包の再確認。** 親は段 1 で「新 identifier / path の実装面 hit 0 件」「触る 8 file の
   whole-file sha256 golden 0 件」と測った。**実装後の今も成立するか**を独立に引き直せ。
   `test_official_perf_closure.py` の semantic inventory (`:44` の `_REVIEWED_PERF_FILES`、
   `:531` の AST 走査、`:905` の集合等値 assert) に**新 leaf が入っていないか**、
   `test_reflux_formal_consumer.py` の AST 走査 (`aborted=False` の keyword 呼び出しと
   `OriginSealed(False, ...)` の禁止) に**抵触していないか**を現物で確かめよ。
5. **consumer の波及。** 変更した production file を参照する consumer を**名前の推測でなく
   参照関係で**引け。private symbol の変更は公開 API の consumer 表に出ないので、
   symbol 名で production 全体を grep せよ。特に `record_attempt_terminal` /
   `DomainProfile(` / `_assert_null_matrix` / `_atomic_update*` / transition callable の
   呼出し閉包を**自分で数え直し**、実装子の報告値 (`_atomic_update_locked` 2、`_atomic_update` 7、
   `_atomic_update_with_consumption_marker` 2、transition callable production 7 + test 4 = 11、
   `record_attempt_terminal` production 4 + test 6 = 10) と一致するか確かめよ。
   **一致しない場合は、どちらが正しいかを現物の file:line で示せ。**
6. **既存テストの期待値。** 親が意味変更を許したのは **2 箇所だけ**である
   (`test_s8b_floor_attempt_launcher.py` の `test_v2_profile_is_rejected_before_any_registry_side_effect`、
   `test_attempt_registry_core_s8b_profile.py` の
   `test_v2_profile_is_additive_empty_retryable_and_budgeted_by_cell`)。
   **それ以外に期待値の反転・緩和・skip・削除・golden 更新が無いか**を diff 全体で確かめよ。
7. **新規 test file の登録簿。** `test_s8b_terminal_evidence.py` が新設されたことで、
   file 名を data として持つ登録簿・meta-test・凍結 gate に**登録漏れが生じていないか**を
   repo 全体で引け (親は `test_pytest_collection_config.py` の glob 走査と
   `acceptance_duration_ledger.json` を既知として把握している。**それ以外を探せ**)。

## 出力形式

節見出しはすべて `##` で統一する。所見ごとに次の 5 点を書く。

- (a) 所見の一文要約
- (b) **現物の file:line** (推測でなく読んだ行)
- (c) なぜ契約違反か / 何が壊れるか
- (d) 修正案 (実装しない。方向だけ)
- (e) **重大度** — `blocker` / `must-fix` / `nit`

最後に `## 総括` を置き、次を書く。

- 判定: `yes` (契約 v3.1 に逐条で適合し波及も閉じている) または `no`
- 契約の各条項について「担い手あり / 担い手なし / 条文と相違」の一覧
- 呼出し閉包の**自分の実測値**と、実装子の報告値との一致・不一致
- blocker / must-fix / nit の件数

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- **`IZANAGI_RUN_GROWTH_HELD_TESTS` を設定して hold を解除するな。**
- 実装・編集・commit をしない。
