単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/s1-brief.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/s1-brief.md` — 親 brief (検査対象。親自身も攻撃対象である)
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/artifacts/t2293-8c-wiring-design/s2-plan.md` — 段 2 の plan (検査対象)
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/refs/decisions-verbatim.md` — D1616 / D1561 / D1190 / D1555 の逐語
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/refs/design-doc-verbatim.md` — `docs/phase3-8c-wiring-design.md` の逐語
5. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2293-8c-wiring-design/refs/t524-ruling-stage4.md` と `refs/t524-ruling-stage6.md` — 稼働中 wave (実験単位 = slot) の設計前提

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-8c-wiring-design` である。コードはすべてこの worktree の中を読む。HEAD は local main `97ee3cd3a`。

## レンズ: 整合と実効性

お前は plan を守る側ではない。**plan と親 brief が現行コードで本当に実行形を持つか**を攻撃する。設計 wave なので実装はしないが、「実装 wave がこの設計どおりに書いたとき、33 の物理 run が本当に claim / layout / WAL / resume gate を通り、formal consumer まで届くか」を file:line で追え。

必ず次を検査せよ。各所見に severity (blocker / must-fix / nit)、file:line、[実測] / [推測] を付けろ。

1. **親 brief の実アンカー表 A1〜A17 の誤り・過大・古い行番号。** 親は現物を読んだと言うが、その一般化 (例: A6「identity が違えば protocol_digest も違う」、A8「同 identity の 2 run 目は claim 以前にここで止まる」、A13「consumer にも producer にも参照が無い」) を独立に反証せよ。
2. **`trial` 接尾辞 (P1) の副作用。** `CampaignConfig.trial` を読む全箇所 (`grep -rn "\.trial\b" orchestrator/campaign/`) を列挙し、identity 以外の用途 (driver 選択、lock 照合、A-1 分岐、site 別 cfg、report / lifecycle への記録、registry の `campaign_id` 再導出) で値の変化が拒否や別挙動を生むかを 1 件ずつ判定せよ。`trial_registry.assert_campaign_binding` が物理 cfg でなく論理 cfg に対して呼ばれる保証がどこにあるか。
3. **P4 の専用 executor の実現性。** 現行 `run_trial` → workload 実行 (`p3_autonomous_workload_trial.py:3780-3905` 付近) の構造で、origin topology mode が generation loop と排他に分岐できる点はどこか。`_assert_fresh_campaign_state`、`exploration_campaign_layout`、`drive` の signature (`layout` 引数)、`_finish_trial` の originless 既定値 (§6.5) との整合。33 run の各 `drive` が返す outcome から result-evidence record を作るまでの材料 (WAL 区間、`build_attempt_id`、execution receipt、trigger binding) が実際に取れるか。
4. **稼働中 wave との食い違い。** t524 の attempt slot (`campaign_id` 1 つ、`replicate_index == 0`、1 unit に final terminal 1 件) と、本案の「1 slot の内側に 33 物理 run」が、t524 の acceptance receipt v5 の全 unit 消費検査・lifecycle の start-once・`_reject_registered_lifecycle_duplicate` と矛盾しないか。t1851 (s8b) の file に触れる必要が本当に無いか。
5. **既定経路の bytes 不変 (§6.5)。** plan が挙げる変更点ごとに、originless 経路で key・bytes・受理集合が動かない根拠が現物にあるか。completeness の exact key gate (`autonomous_trial_completeness.py`) が新 key を拒否する箇所を名指しし、plan の「同じ変更単位で optional 更新」が具体的にどの定数か。
6. **D1555 の shape 不一致 (formal consumer の `_wal_trigger` は root `kind == "TriggerGateBinding"` を要求、production の `wal.log_trigger_binding` は `stage` / `payload` へ書く) を本案が前提にしていないか。** 前提にしているなら、その修理を実装 wave の受入要件に入れる必要がある。
7. **費用・運用の実効性。** 33 run を同一 job 内で直列に回すとき、reservation の残時間検査 (`loop.py:198-207`) と `max_wall_s` の関係、途中 crash 時に §7.2 の tombstone suffix へ落ちる経路が plan にあるか。

## 出力

- 所見表 (severity / 所見 / file:line / 根拠 / 親 brief または plan のどこを直すか)。
- 「plan を作り直すべきか、修正で足りるか」の判定と、修正なら差し替える節の名指し。
- 裁定パッケージ候補 (設計上の択一で、この wave が決めてよくないもの)。
- 各主張に [実測] / [推測]。

## 制約

- 読取専用。pytest の実走は要求しない。静的検査でよい。実測は親が行う。
- 実装・docs 編集・commit をしない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、blocker 件数・must-fix 件数・plan の判定を 8 行以内で書け。
