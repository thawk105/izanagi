## 判定

基準 commit は指定どおり `28ebff456b9f57a927854950b5030fa77aec6529` だった。

結論は二分される。

- cap-lift 固有の topology helper 単体を T-434 の成果として land することは NO-GO。
- しかし「編集 file なし」という全面 NO-GO は強すぎる。既存 production 経路で発火し、受理集合を広げない安全な前提作業として、`s8b_ratified_freeze` の Git trust boundary 共通化・hardening が存在する。

pytest は実行していない。以下は静的検査結果である。

## must-fix

1. **段 2 の helper 合成は、二つの異なる Git truth を混ぜる。**

   - (a) `assert_effective_commit_exact_parent` は環境 allowlist、global/system config 無効化、replace 無効化を使う。一方、再利用予定の `_added_paths` と `_is_none_commit` は ambient `GIT_DIR` などを継承し、`core.useReplaceRefs=false` しか指定しない。しかも直接呼出しでは `_capture_head` の graft・root 検査を通らない。親を正規 repo、diff を別 Git dir の graft 後 graph で検査する経路が残る。
   - (b) [s2-plan.md:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/artifacts/t434-two-stage-binding/s2-plan.md:19)、[s2-plan.md:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/artifacts/t434-two-stage-binding/s2-plan.md:46)、[s8b_ratified_freeze.py:303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/s8b_ratified_freeze.py:303)、[trial_registry.py:942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:942)
   - (c) 放置時: 実際には extra path を持つ `A` が topology を通り、認定記録・受領証を参照する成果物が不正な発効 commit を正本として受理し得る。

2. **D1407 の却下案への直接該当という論証は不正確で、最小単位も `G` 単独ではない。**

   - (a) D1407 には「到達不能と承知で受領証の入口だけを land する」が逐語で存在する。しかし提案 helper は receipt を parse せず caller もないため、字義上は「受領証の入口」ではない。同じ到達不能欠陥型ではある。cap-lift 固有 helper として land すれば、より直接には「`G` が実装一式を導入」と「`G` と `A` は同一 land transaction」に反する。最小単位は単独 `G` ではなく、実装一式を持つ一つの `G` と、人間が作る直子 `A` の atomic transaction である。
   - (b) [D1407:6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/rulings-D1407.md:6)、[D1407:13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/rulings-D1407.md:13)、[D1407:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/rulings-D1407.md:48)、[s2-plan.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/artifacts/t434-two-stage-binding/s2-plan.md:7)、[s2-plan.md:145](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/artifacts/t434-two-stage-binding/s2-plan.md:145)
   - (c) 放置時: helper 先行 land 後の `G/A` が D1407 準拠として台帳へ参照される一方、`G` は実装一式の導入 commit ではなくなり、発効参照の根拠が偽になる。

3. **提案 helper は activation ではなく commit shape しか証明しない。**

   - (a) 署名には measurement HEAD がなく、`A` の発見、`A` が pinned HEAD の祖先であること、`A` の二 blob と HEAD blob の一致がない。従って exact `G` の直子だが main から到達しない dangling `A` も通る。段 2 は不足を認識しているが、提案 API 名と実装位置へ反映していない。
   - (b) [s2-plan.md:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/artifacts/t434-two-stage-binding/s2-plan.md:19)、[s2-plan.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/artifacts/t434-two-stage-binding/s2-plan.md:42)、現行先例 [trial_registry.py:1499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:1499)、[trial_registry.py:1504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:1504)
   - (c) 放置時: main に存在しない `A` を発効根拠として材料レポートや試行台帳が参照し、cap-lift の受理判定だけが真になり得る。

4. **将来の `G` パッケージが、既に裁定済みの設計穴を落としている。**

   - (a) 少なくとも、receipt 無しの literal cap 2、run scope への generation と receipt SHA の封印、Layer 3 generator SHA の互換規則、campaign identity の preimage 循環、実 certified-selection consumer が必要である。現行 completeness は producer 定数を直接読むため、定数だけを変更すると receipt 無し入力も追随する。`_RunScopeBinding` は generation と receipt を持たず、Layer 3 は自身の file hash を記録する一方、再構築比較はそれを正規化しない。また Layer 3 自身が certified-selection consumer 不在を明記する。
   - (b) [prior-design-v3.md:102](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/prior-design-v3.md:102)、[s2-plan.md:153](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/artifacts/t434-two-stage-binding/s2-plan.md:153)、[p3_autonomous_workload_trial.py:477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:477)、[autonomous_trial_completeness.py:2289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/autonomous_trial_completeness.py:2289)、[layer3_report.py:651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/layer3_report.py:651)、[layer3_report.py:689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/layer3_report.py:689)
   - (c) 放置時: receipt 無しの上限超過入力が producer と completeness を通る、異なる generation が同一 scope に混ざる、既存材料レポートが再検証で拒否される、または certified 選択へ到達しない、のいずれかが起きる。

5. **`AI-Agent: none` は人間性の証明ではなく自己申告である。**

   - (a) brief の「人間の commit であり AI は作れない」は機械的には偽である。`_is_none_commit` は message の raw 行と trailer parse だけを見る。provenance checker も `none` 単独なら受理し、実装 path の author 検査から早期 return する。AI が `A` または実装 commit に `AI-Agent: none` を書けば、現行 checker 群だけでは虚偽を検出できない。
   - (b) [brief.md:54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/brief.md:54)、[s8b_ratified_freeze.py:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/s8b_ratified_freeze.py:546)、[check_ai_provenance.py:1434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/tools/check_ai_provenance.py:1434)、[check_ai_provenance.py:1554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/tools/check_ai_provenance.py:1554)
   - (c) 放置時: AI 関与を隠した `A` が上限引き上げの権威参照になり、認定選択・材料レポート・試行台帳が偽の human provenance を保持する。

## nit

1. **段 2 の行番号は stale で、親 brief の方が現物に近い。**

   - (a) `MAX_APPROVED_GENERATIONS = 2` は現物の 144 行で、段 2 の 139 行は `ROOT`。manifest の exact 2 predicate は 771 行、診断文字列 `generations must be the integer 2` 自体は 772 行である。段 2 の 743 行は `_parse_trials` の宣言。従って親の 144 は完全一致、771 は意味的 anchor として一致するが、文字列の物理行は 772。
   - (b) [p3_autonomous_workload_trial.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:139)、[p3_autonomous_workload_trial.py:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:144)、[trial_registry.py:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:743)、[trial_registry.py:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:771)
   - (c) 放置時: 値と受理集合は変わらないが、段 2 の監査参照は定数や predicate ではなく別の宣言行を指す。

2. **「4 述語」は独立保証を一つ多く数えている。**

   - (a) exact parent set `{G}` は非 merge を論理的に含む。実装も root、merge、別親を一つの exact-parent helper で処理するため、独立述語は exact-parent、exact-additions、trailer の三群である。
   - (b) [brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/brief.md:8)、[s2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/artifacts/t434-two-stage-binding/s2-plan.md:28)、[trial_registry.py:1263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:1263)
   - (c) 放置時: 受理集合は変わらないが、変異 matrix と保証一覧が同じ parent guard を二重計上する。

## 受理集合の検算

| 入力 | 現行分岐 | 段 2 推奨後 |
|---|---|---|
| unregistered、明示 opt-in、整数 1 または 2 | `_validate_generation_budget` を通る | 無変更 |
| registered、manifest 2、runtime 2 | manifest predicate と runtime equality を通る | 無変更 |
| registered、manifest 1 または上限超過 | manifest の exact 2 で拒否 | 拒否のまま |
| unregistered、上限超過 | `main`、`run_trial`、`_run_workload` の各入口で拒否 | 拒否のまま |
| 不正 topology の `A` | cap-lift production caller 自体がない | helper を land しなければ変化なし |

従って段 2 の推奨どおり無変更なら、現在受理される 1 世代・2 世代が拒否へ移る経路も、現在拒否される入力が受理へ移る経路もない。conditional helper 単体も production caller がないため、現在の成果物受理集合は動かない。

## NO-GO の両面検算

D1407 の却下案は逐語で存在する。ただし topology helper は「受領証の入口」そのものではなく、同じ到達不能欠陥型である。

cap-lift の意味を実装する単位については、三条件を同時に満たすものはない。

- P6 本体を成功可能にすれば現行の `P6Unavailable` だけの結果集合が変わる。成功不能のままなら実装したことにならない。
- calibration と attestation は現在の production run 入力から発火する面がない。
- receipt 機構は条件 (i) に反する。
- 新 manifest 版を意味あるものにすれば新入力を受理し、拒否 stub なら到達不能である。
- consumer 結線を receipt 無しの現行 `<=2` と同値に置くだけなら、既存 gate の後ろで恒真になる。

一方、全面 NO-GO を崩す実装単位はある。`s8b_ratified_freeze` の Git query を単一の allowlisted、exact-root、graft・replace・shallow 拒否 primitive へ移し、既存 `load_ratified_freeze` production 経路で使用する hardening である。[p3_autonomous_workload_trial.py:4710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:4710) から今日すでに発火し、receipt 入口ではなく、受理集合は同じか狭くなるだけである。

段 2 は cap-lift artifact の不在だけを見て、再利用対象 private helper 自身の trust boundary と既存 production consumer を性質で追わなかったため、この単位を見落とした。

## D841・D1407・D156

narrow helper は receipt ではないため、D841 の「受領証だけ先行」へ字義上は抵触しない。ただし receipt と全 consumer を伴わない以上、D841 が要求する positive control を満たす cap-lift 実装として数えてはならない。

抵触しない最小の発効単位は次である。

- 単一の内容 commit `G`: D156 の四要件、receipt の唯一 parser と sealed verifier、新 manifest 版、producer、journal、全 report 経路、registry acceptance、completeness、Layer 3 と downstream consumer を導入する。
- exact `G` に対する実認定後、人間が直子 `A` を作り、認定記録と receipt の二つだけを regular canonical blob として追加する。
- `G` と `A` を同一 land transaction で取り込む。

topology 各述語は直接 API では負例を作れるため恒真ではない。しかし production caller がない限り全述語が一度も評価されず、cap-lift 保証としては実質恒真表示になる。段 2 は P6 実装を主張せず四コア要件を未実装一覧へ残しているため、D156 を実装したふりにはしていない。

## D882 の予約範囲

段 2 の「無変更」と、上で名指しした s8b Git hardening は次の予約範囲へ触れない。

- 8c 本文の条件 11: [phase3-8c-preregistration.md:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/docs/phase3-8c-preregistration.md:279)、[同:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/docs/phase3-8c-preregistration.md:423)
- 条件 11 evidence contract: [s8c_preregistration_evidence_contract.v1.json:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:437)
- runbook の三つの承認上限主張: [runbook:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/docs/phase3-s8c-autonomous-trial-runbook.md:120)、[同:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/docs/phase3-s8c-autonomous-trial-runbook.md:152)、[同:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/docs/phase3-s8c-autonomous-trial-runbook.md:239)
- frozen hash と g11 bytes: [test_s8c_preregistration_core.py:1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/tests/test_s8c_preregistration_core.py:1195)、[condition-freeze.v1.g11.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g11.json:1)

## 裁定パッケージ候補

本 scope 外として明記すべき層は、A の H 到達性と blob 同一性、receipt 無し literal cap 2 の独立再検査、run scope の generation・receipt SHA 封印、campaign identity preimage、Layer 3 generator 互換規則、実 certified-selection consumer、そして人間 `A` を保証する land authority である。

既存 runbook の予約三箇所は編集せず、新しい manifest 系列の操作記述が必要なら予約文の外側で扱う必要がある。

## 総括

最も重い所見は、段 2 が安全に再利用できるとした二組の Git helper が同じ repository・graph を見ていない点である。これは topology の値そのものを偽陽性にできる。

崩れた親 brief の前提は「既存 exact-parent、exact-additions、`AI-Agent: none` をそのまま組み合わせれば安全な一部品になる」と「`AI-Agent: none` なら AI は `A` を作れない」の二つである。

cap-lift helper 単体の NO-GO は維持すべきだが、「コード変更は一切ない」という段 2 の結論は修正が必要である。既存 production で発火する共有 Git hardening は、受理集合を広げずに今実施できる。